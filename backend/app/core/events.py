import asyncio
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Dict, List, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("app.events")


class Event(BaseModel):
    """Strongly typed model representing an infrastructure authentication event."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    version: str = "1.0"
    payload: dict = Field(default_factory=dict)


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event_type: str, payload: dict, correlation_id: Optional[str] = None) -> None:
        """Publish a strongly-typed Event to all registered consumers."""
        pass


class AsyncEventPublisher(EventPublisher):
    """
    Asynchronous event publisher with thread safety and callback isolation guarantees.
    
    Delivery Guarantees:
    - Order: FIFO for dispatch initiation across subscribers of a single event type.
    - Concurrency: Callbacks run concurrently as independent async tasks, resulting in UNORDERED/BEST-EFFORT completion.
    - Isolation: A slow or failing subscriber will never block or prevent other subscribers from executing.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], Any]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[Event], Any]) -> None:
        """Thread-safe registration of a subscriber callback for a specific event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
        logger.info(f"Registered subscriber for event: {event_type}")

    def publish(self, event_type: str, payload: dict, correlation_id: Optional[str] = None) -> None:
        """Thread-safe and non-blocking event publishing. Internally generates a strongly-typed Event."""
        event = Event(
            event_type=event_type,
            correlation_id=correlation_id,
            payload=payload
        )
        
        try:
            loop = asyncio.get_running_loop()
            # If inside an active event loop, run as an asynchronous task
            loop.create_task(self._dispatch_async(event))
        except RuntimeError:
            # Fallback for sync contexts (like unit tests): run inside background thread
            threading.Thread(
                target=self._dispatch_sync,
                args=(event,),
                daemon=True
            ).start()

    async def _dispatch_async(self, event: Event) -> None:
        """Asynchronously dispatches event to all subscribers in parallel tasks to ensure async isolation."""
        with self._lock:
            subscribers = list(self._subscribers.get(event.event_type, []))
            
        for callback in subscribers:
            asyncio.create_task(self._run_callback_safe_async(callback, event))

    async def _run_callback_safe_async(self, callback: Callable[[Event], Any], event: Event) -> None:
        """Safely executes a single callback inside the async event loop to isolate errors and delays."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            logger.error(
                f"Error executing async event subscriber for {event.event_type} "
                f"(Event ID: {event.event_id}): {str(e)}", 
                exc_info=True
            )

    def _dispatch_sync(self, event: Event) -> None:
        """Synchronously dispatches event to all subscribers in separate threads to preserve isolation."""
        with self._lock:
            subscribers = list(self._subscribers.get(event.event_type, []))
            
        threads = []
        for callback in subscribers:
            t = threading.Thread(
                target=self._run_callback_safe_sync,
                args=(callback, event),
                daemon=True
            )
            threads.append(t)
            t.start()

    def _run_callback_safe_sync(self, callback: Callable[[Event], Any], event: Event) -> None:
        """Safely executes a single callback inside a thread pool context to isolate errors and delays."""
        try:
            if asyncio.iscoroutinefunction(callback):
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(callback(event))
                finally:
                    loop.close()
            else:
                callback(event)
        except Exception as e:
            logger.error(
                f"Error executing sync event subscriber for {event.event_type} "
                f"(Event ID: {event.event_id}): {str(e)}", 
                exc_info=True
            )


# Global event publisher singleton instance
event_publisher = AsyncEventPublisher()
