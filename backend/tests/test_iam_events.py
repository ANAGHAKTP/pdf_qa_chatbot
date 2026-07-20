import pytest
import asyncio
import time
import threading
from app.core.events import AsyncEventPublisher, Event


@pytest.mark.anyio
async def test_event_subscriber_registration():
    publisher = AsyncEventPublisher()
    calls = []

    def callback(event: Event):
        calls.append(event)

    publisher.subscribe("TEST_EVENT", callback)
    publisher.publish("TEST_EVENT", {"val": 42}, correlation_id="corr-999")

    # Wait briefly for execution
    await asyncio.sleep(0.1)

    assert len(calls) == 1
    assert isinstance(calls[0], Event)
    assert calls[0].event_type == "TEST_EVENT"
    assert calls[0].correlation_id == "corr-999"
    assert calls[0].payload["val"] == 42
    assert calls[0].event_id is not None
    assert calls[0].timestamp is not None


@pytest.mark.anyio
async def test_event_publishing_is_non_blocking():
    publisher = AsyncEventPublisher()
    timing = []

    async def slow_callback(event: Event):
        await asyncio.sleep(0.5)
        timing.append("slow_done")

    publisher.subscribe("SLOW_EVENT", slow_callback)
    
    start_time = time.time()
    publisher.publish("SLOW_EVENT", {})
    end_time = time.time()

    duration = end_time - start_time
    assert duration < 0.1
    assert len(timing) == 0

    await asyncio.sleep(0.6)
    assert len(timing) == 1
    assert timing[0] == "slow_done"


@pytest.mark.anyio
async def test_event_subscriber_exception_isolation():
    publisher = AsyncEventPublisher()
    calls = []

    def failing_callback(event: Event):
        raise ValueError("Simulated subscriber exception")

    def succeeding_callback(event: Event):
        calls.append(event)

    publisher.subscribe("ISOLATION_EVENT", failing_callback)
    publisher.subscribe("ISOLATION_EVENT", succeeding_callback)

    publisher.publish("ISOLATION_EVENT", {"ok": True})
    await asyncio.sleep(0.1)

    # Second callback must still execute successfully despite the first failing
    assert len(calls) == 1
    assert calls[0].payload["ok"] is True


@pytest.mark.anyio
async def test_slow_subscriber_isolation():
    publisher = AsyncEventPublisher()
    execution_order = []

    async def slow_callback(event: Event):
        await asyncio.sleep(0.3)
        execution_order.append("slow")

    async def fast_callback(event: Event):
        execution_order.append("fast")

    # Register slow callback first
    publisher.subscribe("MIXED_SPEED_EVENT", slow_callback)
    publisher.subscribe("MIXED_SPEED_EVENT", fast_callback)

    publisher.publish("MIXED_SPEED_EVENT", {})
    
    # Wait long enough for fast, but not long enough for slow
    await asyncio.sleep(0.1)
    
    # Fast must have executed, completely unblocked by the slow subscriber
    assert "fast" in execution_order
    assert "slow" not in execution_order

    # Wait for slow to finish
    await asyncio.sleep(0.3)
    assert "slow" in execution_order


def test_publisher_thread_safety():
    publisher = AsyncEventPublisher()
    results = []

    def subscriber_callback(event: Event):
        results.append(event.payload["index"])

    # Concurrently subscribe from multiple threads
    threads = []
    for i in range(50):
        t = threading.Thread(
            target=publisher.subscribe,
            args=("THREAD_EVENT", subscriber_callback)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify all 50 subscribers registered without dictionary corruption
    with publisher._lock:
        assert len(publisher._subscribers["THREAD_EVENT"]) == 50

    # Concurrently publish from multiple threads
    pub_threads = []
    for i in range(10):
        t = threading.Thread(
            target=publisher.publish,
            args=("THREAD_EVENT", {"index": i})
        )
        pub_threads.append(t)
        t.start()

    for t in pub_threads:
        t.join()

    # Wait dynamically for up to 3.0 seconds for background threads to write their results
    start_time = time.time()
    while len(results) < 500 and (time.time() - start_time) < 3.0:
        time.sleep(0.05)
    
    # Each of the 10 publishes triggered 50 subscriber calls -> 500 total executions
    assert len(results) == 500
