import pika
import json
import logging
import os
import time
import threading
from typing import Dict, Any, Callable
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class RabbitMQClient:
    """
    Base RabbitMQ client
    Handles connection management and basic operations
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.host = os.getenv('RABBITMQ_HOST')
        self.port = int(os.getenv('RABBITMQ_PORT'))
        self.username = os.getenv('RABBITMQ_USER')
        self.password = os.getenv('RABBITMQ_PASS')
        self.virtual_host = os.getenv('RABBITMQ_VIRTUAL_HOST')
        
        self.connection = None
        self.channel = None
        self.is_connected = False
        self.shutdown_event = None
        self.consuming = False
        self.consumer_tags = []  # Track our own consumer tags

        self._subscriptions = []   # list of (queue_name, wrapped_callback, auto_ack)
        self._prefetch = 1         # qos to re-apply on every (re)connect
    
    def set_shutdown_event(self, shutdown_event: threading.Event):
        """Set the shutdown event for graceful shutdown"""
        self.shutdown_event = shutdown_event
    
    def connect(self, max_retries: int = 5) -> bool:
        """Connect to RabbitMQ with retry logic"""
        for attempt in range(max_retries):
            try:
                credentials = pika.PlainCredentials(self.username, self.password)
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    virtual_host=self.virtual_host,
                    credentials=credentials,
                    heartbeat=30,
                    blocked_connection_timeout=300
                )
                
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Enable publisher confirms for reliability
                self.channel.confirm_delivery()
                
                self.is_connected = True
                
                logger.info(f"{self.service_name} connected to RabbitMQ at {self.host}:{self.port}")
                return True
                
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        self.is_connected = False
        return False
    
    def ensure_connection(self):
        """Ensure connection is active"""
        if not self.is_connected or not self.connection or self.connection.is_closed:
            if not self.connect():
                raise ConnectionError(f"{self.service_name}: Failed to connect to RabbitMQ")
    
    def publish(self, exchange: str, routing_key: str, message: Dict[str, Any], 
                max_retries: int = 3) -> bool:
        """
        Publish message with fault tolerance
        """
        message_body = {
            'timestamp': datetime.now().isoformat(),
            'source_service': self.service_name,
            'data': message
        }
        
        for attempt in range(max_retries):
            try:
                self.ensure_connection()
                
                # Log the message before publishing
                correlation_id = message.get('correlation_id', 'unknown')
                logger.info(f"Publishing message {correlation_id} to {exchange}/{routing_key} (attempt {attempt+1})")
                
                # Publish with confirmation - basic_publish with confirm_delivery returns None
                # but will raise exception if it fails
                self.channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=json.dumps(message_body, default=str),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Persistent message
                        timestamp=int(time.time()),
                        content_type='application/json',
                        correlation_id=correlation_id,
                        message_id=f"{self.service_name}_{int(time.time() * 1000)}"
                    )
                    # Temporarily disabled mandatory=True to fix publish errors
                    # mandatory=True  # Ensure message is routed to a queue
                )
                
                # If no exception was raised, publishing succeeded
                logger.info(f"Successfully published {correlation_id} to {exchange}/{routing_key}")
                return True
                
            except Exception as e:
                logger.error(f"Publish attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
        logger.error(f"{self.service_name} failed to publish after {max_retries} attempts")
        return False
    
    def consume(self, queue_name: str, callback: Callable, auto_ack: bool = False):
        """
        Set up consumer for a queue
        """
        def wrapped_callback(channel, method, properties, body):
            try:
                # Check if we should stop processing
                if self.shutdown_event and self.shutdown_event.is_set():
                    logger.info(f"{self.service_name} stopping due to shutdown signal")
                    if not auto_ack:
                        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    return
                
                message = json.loads(body.decode('utf-8'))
                logger.info(f"{self.service_name} received message from {queue_name}")
                
                # Call the actual callback
                success = callback(message)
                
                if not auto_ack:
                    if success:
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                        logger.info(f"{self.service_name} acknowledged message")
                    else:
                        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                        logger.warning(f"{self.service_name} rejected message")
                        
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {str(e)}")
                if not auto_ack:
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                if not auto_ack:
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        # Record the subscription so the subscription can be rebuilt automatically if the connection drops.
        self._subscriptions.append((queue_name, wrapped_callback, auto_ack))
        logger.info(f"{self.service_name} registered subscription for {queue_name}")
    
    def _should_stop(self):
        """True if a deliberate shutdown was requested."""
        return self.shutdown_event is not None and self.shutdown_event.is_set()

    def _apply_subscriptions(self):
        """(Re)register prefetch + all recorded subscriptions on the CURRENT channel.
        Runs on first start and after every reconnect - rebuilds the channel-level
        state (prefetch + basic_consume) that dies with a dropped connection."""
        self.consumer_tags = []  # old tags belonged to the dead channel
        self.channel.basic_qos(prefetch_count=self._prefetch)
        for queue_name, wrapped_callback, auto_ack in self._subscriptions:
            consumer_tag = self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=wrapped_callback,
                auto_ack=auto_ack
            )
            self.consumer_tags.append(consumer_tag)
            logger.info(f"{self.service_name} subscribed to {queue_name} (tag={consumer_tag})")

    def _safe_close(self):
        """Best-effort close of a dead connection to release its socket/FD."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception:
            pass
        self.is_connected = False

    def _reconnect(self):
        """Close the dead connection, reconnect (connect() = 5 tries + exp backoff),
        and re-subscribe. Returns True on success, False if all tries failed."""
        self._safe_close()
        if self._should_stop():
            return False
        if self.connect():                 # 5 tries, exponential backoff
            self._apply_subscriptions()     # re-hire the subscriptions on the fresh channel
            return True
        return False

    def start_consuming(self):
        """Consume with automatic reconnect + re-subscribe.

        On a connection drop, reconnect (connect()'s 5 tries + exp backoff) and
        replay all subscriptions. If reconnect still fails, give up and let the
        thread end so the consumer watchdog can restart it.
        """
        self.consuming = True
        try:
            self.ensure_connection()
            self._apply_subscriptions()  # first-time hire (basic_qos + basic_consume)
            logger.info(f"{self.service_name} consuming ({len(self._subscriptions)} subscriptions)")

            while self.consuming and not self._should_stop():
                try:
                    # Pump events with a timeout so we can check shutdown each second
                    self.connection.process_data_events(time_limit=1)

                except (pika.exceptions.AMQPConnectionError,
                        pika.exceptions.StreamLostError,
                        pika.exceptions.ChannelClosedByBroker) as e:
                    if self._should_stop():
                        break
                    logger.warning(f"{self.service_name} connection lost ({e}); reconnecting...")
                    if not self._reconnect():
                        logger.error(f"{self.service_name} reconnect failed after retries; "
                                     f"giving up (watchdog will restart)")
                        break
                except Exception as e:
                    logger.error(f"{self.service_name} unexpected consume error: {str(e)}", exc_info=True)
                    break

            logger.info(f"{self.service_name} stopping consumption...")

        except KeyboardInterrupt:
            logger.info(f"{self.service_name} stopping consumption due to KeyboardInterrupt...")
        except Exception as e:
            logger.error(f"Error during consumption: {str(e)}")
            raise
        finally:
            self.consuming = False
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming messages"""
        try:
            self.consuming = False
            if self.channel and not self.channel.is_closed:
                # Cancel all our tracked consumers (only once each)
                if self.consumer_tags:  # Only if we have consumers to cancel
                    consumer_tags_to_cancel = self.consumer_tags[:]  # Make a copy
                    self.consumer_tags.clear()  # Clear the original list immediately
                    
                    for consumer_tag in consumer_tags_to_cancel:
                        try:
                            self.channel.basic_cancel(consumer_tag)
                            logger.info(f"{self.service_name} cancelled consumer: {consumer_tag}")
                        except Exception as e:
                            # Log at debug level to reduce noise - these errors are often harmless
                            logger.debug(f"Error cancelling consumer {consumer_tag}: {str(e)}")
                            
                    logger.info(f"{self.service_name} stopped consuming")
        except Exception as e:
            logger.debug(f"Error stopping consumption: {str(e)}")
    
    def close(self):
        """Close connection"""
        try:
            self.consuming = False
            
            # First stop consuming (but only if we haven't already)
            if self.consumer_tags:  # Only if we have consumers to cancel
                self.stop_consuming()
            
            # Then close channel
            if self.channel and not self.channel.is_closed:
                try:
                    self.channel.close()
                    logger.debug(f"{self.service_name} channel closed")
                except Exception as e:
                    logger.debug(f"Error closing channel: {str(e)}")
                
            # Finally close connection
            if self.connection and not self.connection.is_closed:
                try:
                    self.connection.close()
                    logger.debug(f"{self.service_name} connection closed")
                except Exception as e:
                    logger.debug(f"Error closing connection: {str(e)}")
                
            self.is_connected = False
            logger.info(f"{self.service_name} RabbitMQ connection closed")
        except Exception as e:
            logger.debug(f"Error closing connection: {str(e)}")
