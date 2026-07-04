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
        
        try:
            self.ensure_connection()
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=wrapped_callback,
                auto_ack=auto_ack
            )
            logger.info(f"{self.service_name} set up consumer for {queue_name}")
            
        except Exception as e:
            logger.error(f"Failed to set up consumer: {str(e)}")
            raise
    
    def start_consuming(self):
        """Start consuming messages (blocking)"""
        try:
            self.ensure_connection()
            logger.info(f"{self.service_name} starting to consume messages...")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info(f"{self.service_name} stopping consumption...")
            self.stop_consuming()
        except Exception as e:
            logger.error(f"Error during consumption: {str(e)}")
            raise
    
    def stop_consuming(self):
        """Stop consuming messages"""
        try:
            if self.channel and not self.channel.is_closed:
                logger.info(f"{self.service_name} stopping message consumption...")
                self.channel.stop_consuming()
                logger.info(f"{self.service_name} stopped consuming")
        except Exception as e:
            logger.error(f"Error stopping consumption: {str(e)}")
    
    def close(self):
        """Close connection"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self.is_connected = False
            logger.info(f"{self.service_name} RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")
