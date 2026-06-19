# Idempotency-Layer Tests

## Definition

Idempotency tests verify that running the same operation twice produces the same
end state. Required for retry-safe pipelines, event handlers, and migrations.

## Why This Layer Matters Separately

Idempotency bugs hide behind happy-path tests because the second invocation is
rarely exercised explicitly. A handler may insert a duplicate row, publish a
second message, or corrupt accumulated state — all invisible when tests call the
operation only once.

## The Core Pattern

Snapshot state, run the operation, snapshot again, run again, assert the second
snapshot matches the first.

```python
def test_process_twice_same_state():
    state = {"count": 0, "processed_ids": set()}
    handler = MyHandler(state)

    handler.process(event_id="evt-1", payload={"value": 42})
    snapshot_1 = dict(state)

    handler.process(event_id="evt-1", payload={"value": 42})
    snapshot_2 = dict(state)

    assert snapshot_1 == snapshot_2
```

## Identity Key Strategy

Idempotency requires a stable key (`event_id`, `request_id`, content hash).
Operations sharing a key must collapse; operations with distinct keys must not.

```python
def test_same_key_collapses():
    store = InMemoryStore()
    upsert(store, key="k1", value="a")
    upsert(store, key="k1", value="a")
    assert store.count("k1") == 1

def test_different_keys_do_not_collapse():
    store = InMemoryStore()
    upsert(store, key="k1", value="a")
    upsert(store, key="k2", value="b")
    assert store.count_all() == 2
```

## Side-Effect Counting

Assert that side effects (DB inserts, queue publishes, filesystem writes) fire
once, not twice. Use `mock.assert_called_once_with(...)`.

```python
def test_side_effect_fires_once(mocker):
    publish = mocker.patch("mymodule.queue.publish")
    handler = EventHandler(publish=publish)

    handler.handle(event_id="evt-1", data={})
    handler.handle(event_id="evt-1", data={})

    publish.assert_called_once_with(event_id="evt-1", data={})
```

## Partial-Failure Resume

Simulate a crash mid-operation (raise after step N), retry, and assert the end
state matches a clean single-success run. Use a counter and raise-after-N.

```python
def test_resume_after_partial_failure():
    store = InMemoryStore()
    call_count = 0

    def brittle_step():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("simulated crash")

    with pytest.raises(RuntimeError):
        run_pipeline(store, step_fn=brittle_step, event_id="evt-1")

    run_pipeline(store, step_fn=brittle_step, event_id="evt-1")

    assert store.get("evt-1") == expected_final_state()
```

## Database Upserts

Assert `INSERT ... ON CONFLICT DO NOTHING` or `MERGE` semantics. Never use a
bare `INSERT` on idempotent paths.

```python
def test_upsert_no_duplicate_row(db_session):
    record = {"id": "rec-1", "value": 10}
    upsert_record(db_session, record)
    upsert_record(db_session, record)

    rows = db_session.query(MyTable).filter_by(id="rec-1").all()
    assert len(rows) == 1
    assert rows[0].value == 10
```

## Event Handlers

Assert dedup-table writes and that downstream side-effects fire only on first
delivery.

```python
def test_handler_deduplicates(db_session, mocker):
    send_email = mocker.patch("mymodule.send_email")
    handler = OrderHandler(db=db_session, notify=send_email)

    handler.on_event(event_id="order-99", payload={"amount": 50})
    handler.on_event(event_id="order-99", payload={"amount": 50})

    assert db_session.query(DedupeLog).filter_by(event_id="order-99").count() == 1
    send_email.assert_called_once()
```

## Hypothesis Property Form

The formal idempotency invariant: `f(f(state, msg), msg) == f(state, msg)` for
any state and message.

```python
from hypothesis import given, strategies as st

@given(state=st.dictionaries(st.text(), st.integers()), msg=st.text())
def test_handler_idempotent(state, msg):
    once = apply(state.copy(), msg)
    twice = apply(once.copy(), msg)
    assert once == twice
```

## Anti-Patterns

- **Testing only the first invocation.** The bug only appears on the second call.
- **Mocking the dedup mechanism.** If you mock `is_duplicate()` to return `True`,
  idempotency comes from the mock, not the code — the real path is untested.
- **Using `freezegun` improperly across both runs.** If the clock is frozen
  identically for both invocations, timestamp-based dedup keys collide
  artificially. Advance the frozen clock between runs if the real dedup key
  is time-derived; otherwise use an explicit `event_id`.

## Complete Example

```python
# test_order_handler_idempotent.py

def test_order_handler_full_idempotency(db_session, mocker):
    fulfil = mocker.patch("orders.fulfil_order")
    handler = OrderHandler(db=db_session, fulfil=fulfil)
    event = {"event_id": "evt-42", "order_id": "ord-7", "amount": 100}

    # First delivery
    handler.handle(**event)
    row_count_after_first = db_session.query(DedupeLog).count()
    assert row_count_after_first == 1
    fulfil.assert_called_once_with(order_id="ord-7", amount=100)

    # Second delivery (retry / redelivery)
    handler.handle(**event)
    assert db_session.query(DedupeLog).count() == 1  # no new row
    fulfil.assert_called_once()                       # still once
```
