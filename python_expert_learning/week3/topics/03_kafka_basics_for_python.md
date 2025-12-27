# Topic 3: Kafka Basics for Python (Mental Model)

## 🎯 What you’ll learn

- Topics, partitions, producers, consumers
- Offsets and delivery semantics (at-least-once vs exactly-once-ish)
- The #1 rule: **idempotent consumers**

## 1) Core concepts

- **Topic**: named stream of events
- **Partition**: ordered log shard within a topic
- **Producer**: writes events to a topic
- **Consumer**: reads events from a topic
- **Consumer group**: multiple consumers share work (each partition owned by one consumer at a time)

## 2) Offsets (your position in the log)

A consumer reads messages sequentially and tracks “how far it got”:

- If you commit offset *after* processing: you might reprocess on crash (at-least-once)
- If you commit offset *before* processing: you might lose messages on crash (at-most-once)

Most systems choose **at-least-once** + idempotent processing.

## 3) Idempotency (survive retries)

Your consumer should be safe if it processes the same event twice.

Common technique:

- Every event has an `event_id`
- Maintain a “processed ids” store (DB table / Redis set with TTL)
- If already processed: skip

## 4) Partitions and ordering

Kafka only guarantees ordering **within a partition**.

If you need per-user ordering, choose a partition key like `user_id` so all that user’s events land in the same partition.

## ✅ Next: Hands-on exercise

Do: `python_expert_learning/week3/exercises/03_event_bus_kafka_like.py`


