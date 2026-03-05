import logging
import threading
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

from .drift_consumer import DriftConsumer

logger = logging.getLogger(__name__)

class ConsumerManager:
    """
    Manages multiple RabbitMQ consumers for the patient service
    Allows easy scaling and management of different consumer types
    """
    
    def __init__(self):
        self.consumers = {}
        self.consumer_instances = {}  # Store actual consumer instances
        self.threads = {}
        self.executor = None
        self.running = False
        self.shutdown_event = None
        
    def set_shutdown_event(self, shutdown_event: threading.Event):
        """Set the shutdown event for graceful shutdown"""
        self.shutdown_event = shutdown_event
        
    def register_consumer(self, name: str, consumer_class):
        """Register a consumer class"""
        self.consumers[name] = consumer_class
        logger.info(f"Registered consumer: {name}")
    
    def start_all_consumers(self):
        """Start all registered consumers in separate threads"""
        if self.running:
            logger.warning("Consumers are already running")
            return
        
        if not self.consumers:
            logger.warning("No consumers registered")
            return
        
        self.executor = ThreadPoolExecutor(max_workers=len(self.consumers))
        self.running = True
        
        for name, consumer_class in self.consumers.items():
            future = self.executor.submit(self._run_consumer, name, consumer_class)
            self.threads[name] = future
            logger.info(f"Started consumer thread: {name}")
    
    def start_consumer(self, name: str):
        """Start a specific consumer"""
        if name not in self.consumers:
            logger.error(f"Consumer {name} not registered")
            return False
        
        if name in self.threads and not self.threads[name].done():
            logger.warning(f"Consumer {name} is already running")
            return False
        
        if not self.executor:
            self.executor = ThreadPoolExecutor(max_workers=len(self.consumers))
            self.running = True
        
        consumer_class = self.consumers[name]
        future = self.executor.submit(self._run_consumer, name, consumer_class)
        self.threads[name] = future
        logger.info(f"Started consumer: {name}")
        return True
    
    def stop_consumer(self, name: str):
        """Stop a specific consumer"""
        if name not in self.threads:
            logger.warning(f"Consumer {name} is not running")
            return False
        
        # Stop the consumer instance if it exists
        if name in self.consumer_instances:
            try:
                consumer = self.consumer_instances[name]
                consumer.stop()
                logger.info(f"Sent stop signal to consumer: {name}")
            except Exception as e:
                logger.error(f"Error stopping consumer {name}: {str(e)}")
        
        return True
    
    def stop_all_consumers(self):
        """Stop all running consumers"""
        if not self.running:
            logger.warning("No consumers are running")
            return
        
        logger.info("Stopping all consumers...")
        
        # First, stop all consumer instances gracefully
        for name, consumer in self.consumer_instances.items():
            try:
                logger.info(f"Stopping consumer: {name}")
                consumer.stop()
            except Exception as e:
                logger.error(f"Error stopping consumer {name}: {str(e)}")
        
        # Then shutdown the executor - handle Python version compatibility
        if self.executor:
            logger.info("Shutting down thread executor...")
            try:
                # Try with timeout parameter (Python 3.9+)
                import sys
                if sys.version_info >= (3, 9):
                    self.executor.shutdown(wait=True, timeout=10)
                else:
                    # For older Python versions, just use wait=True
                    self.executor.shutdown(wait=True)
            except TypeError:
                # Fallback for any other issues
                self.executor.shutdown(wait=True)
            logger.info("Thread executor shutdown complete")
        
        # Clear state
        self.consumer_instances.clear()
        self.threads.clear()
        self.running = False
        logger.info("All consumers stopped")
    
    def get_consumer_status(self) -> Dict[str, str]:
        """Get status of all consumers"""
        status = {}
        for name, future in self.threads.items():
            if future.done():
                if future.exception():
                    status[name] = f"Error: {future.exception()}"
                else:
                    status[name] = "Completed"
            else:
                status[name] = "Running"
        
        return status
    
    def _run_consumer(self, name: str, consumer_class):
        """Run a consumer in a separate thread"""
        consumer = None
        try:
            logger.info(f"Starting consumer: {name}")
            consumer = consumer_class()
            
            # Store consumer instance for graceful shutdown
            self.consumer_instances[name] = consumer
            
            # Pass shutdown event to consumer if it supports it
            if hasattr(consumer, 'set_shutdown_event') and self.shutdown_event:
                consumer.set_shutdown_event(self.shutdown_event)
            
            consumer.start_consuming()
            
        except KeyboardInterrupt:
            logger.info(f"Consumer {name} interrupted by user")
        except Exception as e:
            logger.error(f"Consumer {name} failed: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
        finally:
            if consumer:
                try:
                    consumer.close()
                except Exception as e:
                    logger.error(f"Error closing consumer {name}: {str(e)}")
            
            # Remove from instances dict
            if name in self.consumer_instances:
                del self.consumer_instances[name]
                
            logger.info(f"Consumer {name} shutdown complete")


# Pre-configured manager instance
def create_user_consumer_manager() -> ConsumerManager:
    """Create a consumer manager with all user service consumers registered"""
    manager = ConsumerManager()
    
    # Register all available consumers
    manager.register_consumer("drift", DriftConsumer)

    return manager
