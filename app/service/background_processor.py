import asyncio
import logging
import signal
from datetime import datetime
from typing import Optional

from .outbox_service import get_outbox_service

logger = logging.getLogger(__name__)

class OutboxProcessor:
    """Background processor for outbox events"""
    
    def __init__(self, poll_interval: int = 2, batch_size: int = 10):
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.outbox_service = get_outbox_service()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Simple stats
        self.stats = {
            'total_processed': 0,
            'total_successful': 0,
            'total_failed': 0,
            'last_run': None,
            'status': 'stopped'
        }
    
    async def start(self):
        """Start the processor"""
        if self._running:
            logger.warning("Processor already running")
            return
        
        self._running = True
        self.stats['status'] = 'running'
        logger.info(f"Starting outbox processor (poll_interval={self.poll_interval}s, batch_size={self.batch_size})")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start processing loop
        self._task = asyncio.create_task(self._process_loop())
        
        try:
            await self._task
        except asyncio.CancelledError:
            logger.info("Processor cancelled")
        except Exception as e:
            logger.error(f"Processor error: {str(e)}")
        finally:
            self._running = False
            self.stats['status'] = 'stopped'

    async def stop(self):
        """Stop the processor"""
        if not self._running:
            return
        
        logger.info("Stopping processor...")
        self._running = False
        self.stats['status'] = 'stopping'
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, stopping processor...")
        self._running = False

    async def _process_loop(self):
        """Main processing loop"""
        while self._running:
            try:
                # Process events in thread pool to avoid blocking
                successful, failed = await asyncio.to_thread(
                    self.outbox_service.process_pending_events,
                    self.batch_size
                )
                
                # Update stats
                self.stats['total_processed'] += successful + failed
                self.stats['total_successful'] += successful
                self.stats['total_failed'] += failed
                self.stats['last_run'] = datetime.now().isoformat()
                
                if successful > 0 or failed > 0:
                    logger.info(f"Processed {successful + failed} events - Success: {successful}, Failed: {failed}")
                
                # Wait for next cycle
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}")
                await asyncio.sleep(min(self.poll_interval, 30))  # Back off on errors      
    
    def get_stats(self) -> dict:
        """Get processor statistics"""
        return self.stats.copy()
    
    def is_running(self) -> bool:
        """Check if processor is running"""
        return self._running
    

# Global processor instance
_processor: Optional[OutboxProcessor] = None


def get_processor() -> OutboxProcessor:
    """Get or create processor instance"""
    global _processor
    if _processor is None:
        _processor = OutboxProcessor()
    return _processor


# FastAPI lifespan integration
async def outbox_lifespan(app):
    """FastAPI lifespan context manager for outbox processor"""
    processor = get_processor()
    
    # Start processor
    processor_task = asyncio.create_task(processor.start())
    
    try:
        yield
    finally:
        # Stop processor
        await processor.stop()
        if not processor_task.done():
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                pass


# CLI for standalone running
async def run_standalone():
    """Run processor as standalone service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Outbox Processor")
    parser.add_argument("--poll-interval", type=int, default=10, help="Poll interval in seconds")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    processor = OutboxProcessor(
        poll_interval=args.poll_interval,
        batch_size=args.batch_size
    )
    
    try:
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(run_standalone())   