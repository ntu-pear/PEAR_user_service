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

        self._watchdog_thread = None
        self._watchdog_enabled = False
        self._watchdog_interval = 10       # seconds between health checks
        self._watchdog_max_backoff = 60    # cap on per-consumer restart backoff
        self._watchdog_alert_after = 5     # log an ERROR once after this many consecutive failed restarts
        self._watchdog_stable_after = 30   # seconds alive before a restart counts as success
        self._restart_backoff = {}         # name -> current backoff seconds
        self._next_restart_at = {}         # name -> earliest epoch time to retry
        self._restart_attempts = {}        # name -> consecutive failed restarts
        self._alive_since = {}             # name -> epoch when consumer was first seen alive
        self._alerted = set()              # names already reported as persistently failing

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

        # Start the supervisor that revives any consumer thread that dies
        self._start_watchdog()

    def _start_watchdog(self):
        """Start the supervisor thread that restarts dead consumers."""
        if self._watchdog_enabled:
            return
        self._watchdog_enabled = True
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()
        logger.info("Consumer watchdog started")

    def _watchdog_loop(self):
        """Every interval, restart any consumer whose thread has died (unless we
        are shutting down), with per-consumer exponential backoff.

        It never gives up: a broker that is down for a few minutes looks the same
        as one that is down for longer. After _watchdog_alert_after consecutive
        failures it logs an ERROR once, then keeps retrying at the capped backoff.
        """
        while self._watchdog_enabled:
            time.sleep(self._watchdog_interval)
            if not self._watchdog_enabled:
                break
            if self.shutdown_event and self.shutdown_event.is_set():
                break

            now = time.time()
            for name in list(self.consumers.keys()):
                if not self._watchdog_enabled:
                    break

                future = self.threads.get(name)
                alive = future is not None and not future.done()
                if alive:
                    # Alive, but is it *proven* alive or still failing to connect?
                    first_seen = self._alive_since.setdefault(name, now)
                    if now - first_seen >= self._watchdog_stable_after:
                        # survived the stability window -> forgive past failures
                        if name in self._alerted:
                            logger.info(f"Watchdog: consumer '{name}' recovered")
                        self._restart_backoff.pop(name, None)
                        self._next_restart_at.pop(name, None)
                        self._restart_attempts.pop(name, None)
                        self._alerted.discard(name)
                    continue

                self._alive_since.pop(name, None)

                if now < self._next_restart_at.get(name, 0):
                    continue

                attempts = self._restart_attempts.get(name, 0)
                if attempts >= self._watchdog_alert_after and name not in self._alerted:
                    self._alerted.add(name)
                    logger.error(f"Watchdog: consumer '{name}' still failing after {attempts} "
                                 f"consecutive restarts - RabbitMQ may be down. Will keep "
                                 f"retrying every {self._watchdog_max_backoff}s.")

                self._log_consumer_death(name, future)
                logger.warning(f"Watchdog: consumer '{name}' is not running - restarting "
                               f"(attempt {attempts + 1})")
                self.start_consumer(name)
                self._restart_attempts[name] = attempts + 1

                # schedule next allowed restart with exponential backoff (capped)
                cur = self._restart_backoff.get(name, self._watchdog_interval)
                self._next_restart_at[name] = time.time() + cur
                self._restart_backoff[name] = min(cur * 2, self._watchdog_max_backoff)

        logger.info("Consumer watchdog stopped")

    def _log_consumer_death(self, name, future):
        """Log why a consumer ended, if it raised."""
        try:
            exc = future.exception(timeout=0) if future else None
            if exc:
                logger.error(f"Consumer '{name}' died with exception: {exc}")
        except Exception:
            pass

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

        # Stop the watchdog first so it does not revive consumers we're stopping
        self._watchdog_enabled = False
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=self._watchdog_interval + 2)

        # First, stop all consumer instances gracefully
        for name, consumer in list(self.consumer_instances.items()):
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
        # Clear watchdog bookkeeping so a later start_all_consumers() begins clean
        self._restart_backoff.clear()
        self._next_restart_at.clear()
        self._restart_attempts.clear()
        self._alive_since.clear()
        self._alerted.clear()
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
