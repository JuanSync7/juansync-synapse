# Boundary Reference: Queue / Worker / Messaging

Loaded at `[DETECT]` when the module category is queue, worker, or messaging. Use to classify functions as `boundary-runtime`, `boundary-logical`, or `internal`, and to drive lifecycle/risk decisions.

## Detection signals

- **Runtime tier (boundary-runtime):**
  - `@celery.task`, `@celery.shared_task` decorators.
  - Temporal: `@activity.defn`, `@workflow.defn`, `Worker.run`, `Client.start_workflow`.
  - Kafka: `kafka.KafkaProducer`, `kafka.KafkaConsumer`, `confluent_kafka.Producer/Consumer`.
  - RabbitMQ/AMQP: `pika.BlockingConnection`, `aio_pika.connect`, `channel.basic_publish/basic_consume`.
  - AWS SQS: `boto3.client('sqs')` with `send_message`, `receive_message`, `delete_message`.
  - Redis Streams / pub-sub: `redis.Redis().xadd`, `xread`, `xreadgroup`, `publish`, `subscribe`.
  - `asyncio.Queue` only when it crosses a process boundary (multiprocessing, IPC); otherwise treat as internal.
- **Logical tier (boundary-logical):**
  - Functions exported via `__all__` from `tasks/`, `workers/`, `workflows/`, `consumers/`, `producers/`, `jobs/` packages whose body invokes any runtime-tier signal.
  - Thin wrappers that enqueue or dispatch to a runtime-tier client (e.g. `def submit_job(payload): producer.send(...)`).
- **Internal:**
  - Message serializers (`to_dict`, `from_json`), schema validators, dispatch tables, payload normalizers, retry-policy calculators — classify as `internal`, not boundaries.

## Lifecycle pattern decision rules

- **Default → `ephemeral-container`:** Testcontainers or docker-compose-managed broker (RabbitMQ, Kafka, Redis, LocalStack-SQS) spun up per test session. Workers run in-process against the real broker.
- **`ephemeral-container` configuration must:**
  - assign random ports (avoid collisions in parallel CI),
  - isolate per test session (unique queue/topic/stream names),
  - tear down on exit (fixture finalizer or context manager),
  - never reuse a shared broker across CI runs.
- **Temporal:** prefer `temporalio.testing.WorkflowEnvironment` (time-skipping, in-process) over a full container — it executes real workflow/activity code with deterministic replay. Document the choice in the strategy file.
- **Celery:** `task_always_eager=True` is acceptable only for narrow logic-only cases (no broker semantics under test). For routing, retries, ack semantics — use a real broker container.
- **Never recommend in-memory shims** (`fakeredis` for Streams, `moto` for SQS ordering, custom dict-backed queues) as the default. Message ordering, redelivery, visibility timeouts, and at-least-once semantics often diverge from real brokers; bugs slip through.

## Risk weight

- `external_dependency_risk = 3` (moderate-high). Justification: message ordering, redelivery, dead-letter routing, consumer-group rebalancing, and ack/nack semantics are common bug sources that only surface against real brokers.

## Common over-mock anti-patterns to flag

- Mocking the producer's `send`/`publish` and asserting on call args — misses serialization errors and broker-side validation (topic existence, ACL, message size).
- Mocking the consumer's poll loop or `for msg in consumer` — execution semantics (offset commits, rebalances, timeouts) never tested.
- Mocking `asyncio.Queue` for in-process queues — usually internal plumbing; surface as `over_mocking_warning` and recommend testing the surrounding logic instead.
- Patching Celery's `apply_async` — hides routing keys, queue selection, and serializer config.
- Stubbing Temporal activities with `unittest.mock` instead of `WorkflowEnvironment.mock_activity` — bypasses determinism checks.

## Out-of-scope

- Cross-region replication, partition rebalancing under load, broker failover — soak/chaos territory, not unit/integration classification.
- Throughput and latency benchmarks — performance suite, not test-evaluate scope.
- Schema-registry compatibility evolution — separate contract-testing concern.
