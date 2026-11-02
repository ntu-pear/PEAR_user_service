from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any, List, Tuple
import json
import logging
import uuid

from ..models.outbox_model import OutboxEvent, OutboxStatus
from ..messaging.producer_manager import get_producer_manager

logger = logging.getLogger(__name__)


class OutboxService:
    """
    Outbox service for reliable message delivery (Outbox pattern)
    """

    def __init__(self):
        self.producer_manager = get_producer_manager()
    
    def create_event(
        self,
        db: Session,
        event_type: str,
        aggregate_id: str,
        payload: Dict[str, Any],
        routing_key: str,
        correlation_id: str,
        created_by: str
    ) -> OutboxEvent:
        """
        Create outbox event within existing database transaction.
        
        Args:
            db: Database session (must be same as business transaction)
            event_type: Type of event (e.g., 'PATIENT_CREATED')
            aggregate_id: Entity ID (e.g., patient ID)
            payload: Event data as dictionary
            routing_key: Message routing key
            correlation_id: Unique ID for tracing and deduplication
            created_by: User who triggered the event
            
        Returns:
            Created OutboxEvent (or existing if duplicate correlation_id)
        """
        try:
            outbox_event = OutboxEvent(
                event_type=event_type,
                aggregate_id=str(aggregate_id),
                routing_key=routing_key,
                correlation_id=correlation_id,
                created_by=created_by
            )
            
            outbox_event.set_payload(payload)
            
            db.add(outbox_event)
            db.flush()  # Get ID without committing
            
            logger.debug(f"Created outbox event: {outbox_event.id} (correlation: {correlation_id})")
            return outbox_event
            
        except IntegrityError as e:
            # Duplicate correlation_id - this is expected for idempotency
            db.rollback()
            existing_event = db.query(OutboxEvent).filter(
                OutboxEvent.correlation_id == correlation_id
            ).first()
            
            if existing_event:
                logger.info(f"Duplicate correlation_id {correlation_id} - returning existing event")
                return existing_event
            else:
                logger.error(f"Integrity error but no existing event found: {str(e)}")
                raise
    
    # TODO: rename id according
    def process_pending_events(self, batch_size: int = 50) -> Tuple[int, int]:
        """
        Process pending outbox events.
        
        Args:
            batch_size: Number of events to process
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        from ..database import SessionLocal
        
        successful = 0
        failed = 0
        
        db = SessionLocal()
        try:
            # Get pending events - ORDERED BY created_at for proper sequencing
            pending_events = db.query(OutboxEvent).filter(
                OutboxEvent.status == OutboxStatus.PENDING
            ).filter(
                OutboxEvent.retry_count < 3
            ).order_by(OutboxEvent.created_at.asc()).limit(batch_size).all()  # ASC for sequential processing
            
            for i, event in enumerate(pending_events, 1):
                logger.info(f"Processing event {i}/{len(pending_events)}: {event.correlation_id[:8]}...")
                
                try:
                    # Publish to message queue
                    payload = event.get_payload()
                    logger.info(f"Publishing event {event.id} (correlation: {event.correlation_id}) to exchange")
                    logger.debug(f"Payload: {payload.get('event_type')} for user {payload.get('user_id')}")
                    
                    success = self.producer_manager.publish(
                        exchange='user.updates',  # Fixed exchange for simplicity
                        routing_key=event.routing_key,
                        message=payload
                    )
                    
                    if success:
                        event.mark_published()
                        successful += 1
                        logger.info(f"Successfully published event {event.id} (correlation: {event.correlation_id})")
                        
                        # Add small delay between messages to ensure proper sequencing
                        if i < len(pending_events):  # Don't delay after the last message
                            import time
                            time.sleep(0.5)
                    else:
                        event.mark_failed("Failed to publish to message queue")
                        failed += 1
                        logger.warning(f"Failed to publish event {event.id} (correlation: {event.correlation_id})")
                
                except Exception as e:
                    event.mark_failed(f"Error: {str(e)}")
                    failed += 1
                    logger.error(f"Error processing event {event.id}: {str(e)}")
            
            # Commit all status updates
            db.commit()
            
            if successful > 0 or failed > 0:
                logger.info(f"Processed {successful + failed} events - Success: {successful}, Failed: {failed}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in process_pending_events: {str(e)}")
        finally:
            db.close()
        
        return successful, failed


    def get_stats(self) -> Dict[str, Any]:
        """Get simple statistics"""
        from ..database import SessionLocal
        
        db = SessionLocal()
        try:
            total = db.query(OutboxEvent).count()
            pending = db.query(OutboxEvent).filter(OutboxEvent.status == OutboxStatus.PENDING).count()
            published = db.query(OutboxEvent).filter(OutboxEvent.status == OutboxStatus.PUBLISHED).count()
            failed = db.query(OutboxEvent).filter(OutboxEvent.status == OutboxStatus.FAILED).count()
            
            return {
                'total': total,
                'pending': pending,
                'published': published,
                'failed': failed
            }
        finally:
            db.close()

    def retry_failed_events(self) -> int:
        """Reset all failed events for retry"""
        from ..database import SessionLocal
        
        db = SessionLocal()
        try:
            failed_events = db.query(OutboxEvent).filter(OutboxEvent.status == OutboxStatus.FAILED).all()
            
            for event in failed_events:
                event.status = OutboxStatus.PENDING
                event.retry_count = 0
                event.error_message = None
            
            db.commit()
            count = len(failed_events)
            logger.info(f"Reset {count} failed events for retry")
            return count
        finally:
            db.close()

def generate_correlation_id() -> str:
    """Generate correlation ID for tracing and deduplication"""
    return str(uuid.uuid4()).upper()


# Singleton instance
_outbox_service = None

def get_outbox_service() -> OutboxService:
    """Get singleton outbox service"""
    global _outbox_service
    if _outbox_service is None:
        _outbox_service = OutboxService()
    return _outbox_service