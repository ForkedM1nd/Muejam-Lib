# Celery Worker Autoscaling Configuration

This document describes the autoscaling strategies for Celery workers in the MueJam Library application.

## Overview

Celery workers can be scaled horizontally to handle varying workloads. This configuration supports:
- **Manual scaling**: Adjust worker count manually
- **Metric-based autoscaling**: Scale based on queue depth, CPU, memory
- **Time-based scaling**: Scale up during peak hours
- **Event-driven scaling**: Scale based on specific events

## Autoscaling Strategies

### 1. Queue Depth-Based Autoscaling

Scale workers based on the number of pending tasks in the queue.

**Metrics:**
- Queue depth (number of pending tasks)
- Task processing rate
- Average task duration

**Thresholds:**
```yaml
scale_up:
  queue_depth: 100  # Scale up if queue has >100 tasks
  wait_time: 60s    # Wait 60s before scaling up

scale_down:
  queue_depth: 10   # Scale down if queue has <10 tasks
  wait_time: 300s   # Wait 5min before scaling down
```

**Implementation (Kubernetes KEDA):**
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: celery-worker-scaler
  namespace: muejam
spec:
  scaleTargetRef:
    name: celery-worker
  minReplicaCount: 2
  maxReplicaCount: 20
  pollingInterval: 30
  cooldownPeriod: 300
  triggers:
  - type: redis
    metadata:
      address: redis:6379
      listName: celery
      listLength: "50"
      databaseIndex: "0"
```

### 2. CPU/Memory-Based Autoscaling

Scale based on resource utilization.

**Thresholds:**
```yaml
cpu:
  target_utilization: 70%
  scale_up_threshold: 80%
  scale_down_threshold: 30%

memory:
  target_utilization: 80%
  scale_up_threshold: 85%
  scale_down_threshold: 40%
```

**Implementation (Kubernetes HPA):**
See `celery-worker-deployment.yaml` for HPA configuration.

### 3. Time-Based Scaling

Scale workers based on time of day to handle predictable traffic patterns.

**Schedule:**
```yaml
peak_hours:
  - time: "08:00-18:00"
    timezone: "UTC"
    min_replicas: 5
    max_replicas: 20

off_peak:
  - time: "18:00-08:00"
    timezone: "UTC"
    min_replicas: 2
    max_replicas: 10

weekend:
  - days: ["Saturday", "Sunday"]
    min_replicas: 2
    max_replicas: 8
```

**Implementation (Kubernetes CronJob):**
```yaml
# Scale up for peak hours
apiVersion: batch/v1
kind: CronJob
metadata:
  name: celery-scale-up
spec:
  schedule: "0 8 * * 1-5"  # 8 AM Mon-Fri
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: kubectl
            image: bitnami/kubectl:latest
            command:
            - kubectl
            - scale
            - deployment/celery-worker
            - --replicas=5
          restartPolicy: OnFailure

# Scale down for off-peak
apiVersion: batch/v1
kind: CronJob
metadata:
  name: celery-scale-down
spec:
  schedule: "0 18 * * 1-5"  # 6 PM Mon-Fri
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: kubectl
            image: bitnami/kubectl:latest
            command:
            - kubectl
            - scale
            - deployment/celery-worker
            - --replicas=2
          restartPolicy: OnFailure
```

### 4. Celery Built-in Autoscaling

Celery has built-in autoscaling for worker processes (not pods/containers).

**Configuration:**
```bash
# Start worker with autoscaling
celery -A config worker --autoscale=10,3 --loglevel=info

# Parameters:
# --autoscale=MAX,MIN
# MAX: Maximum number of worker processes
# MIN: Minimum number of worker processes
```

**How it works:**
- Monitors queue depth and task processing rate
- Spawns new worker processes when queue grows
- Terminates idle worker processes when queue shrinks
- Operates within a single container/pod

**Recommended settings:**
```python
# In celery.py or settings.py
CELERYD_AUTOSCALE = (10, 3)  # (max, min)
CELERYD_PREFETCH_MULTIPLIER = 1  # Fetch one task at a time
CELERYD_MAX_TASKS_PER_CHILD = 1000  # Restart worker after 1000 tasks
```

## Monitoring Metrics

### Key Metrics to Monitor

1. **Queue Metrics:**
   - Queue depth (pending tasks)
   - Task processing rate (tasks/second)
   - Task wait time (time in queue)
   - Task failure rate

2. **Worker Metrics:**
   - Active workers
   - Idle workers
   - Worker CPU utilization
   - Worker memory utilization
   - Tasks processed per worker

3. **Task Metrics:**
   - Task duration (P50, P95, P99)
   - Task success rate
   - Task retry rate
   - Task timeout rate

### Prometheus Queries

```promql
# Queue depth
celery_queue_length{queue="celery"}

# Task processing rate
rate(celery_tasks_total[5m])

# Active workers
celery_workers_active

# Task duration P95
histogram_quantile(0.95, rate(celery_task_duration_seconds_bucket[5m]))

# Task failure rate
rate(celery_tasks_failed_total[5m]) / rate(celery_tasks_total[5m])
```

## Scaling Policies

### Scale Up Policy

**Trigger conditions (any):**
- Queue depth > 100 tasks for 60 seconds
- CPU utilization > 80% for 2 minutes
- Memory utilization > 85% for 2 minutes
- Task wait time > 30 seconds

**Action:**
- Add 2 workers (or 50% of current, whichever is greater)
- Maximum: 20 workers
- Cooldown: 60 seconds

### Scale Down Policy

**Trigger conditions (all):**
- Queue depth < 10 tasks for 5 minutes
- CPU utilization < 30% for 5 minutes
- Memory utilization < 40% for 5 minutes
- No tasks processed in last 2 minutes

**Action:**
- Remove 1 worker (or 25% of current, whichever is less)
- Minimum: 2 workers
- Cooldown: 300 seconds (5 minutes)

### Safety Limits

```yaml
limits:
  min_workers: 2        # Always keep at least 2 workers
  max_workers: 20       # Never exceed 20 workers
  scale_up_max: 5       # Add max 5 workers at once
  scale_down_max: 2     # Remove max 2 workers at once
  cooldown_up: 60s      # Wait 60s between scale-ups
  cooldown_down: 300s   # Wait 5min between scale-downs
```

## Task Prioritization

Configure task priorities to ensure critical tasks are processed first.

**Priority Levels:**
```python
# In tasks.py
from celery import Task

class HighPriorityTask(Task):
    priority = 9  # Highest priority

class MediumPriorityTask(Task):
    priority = 5  # Medium priority

class LowPriorityTask(Task):
    priority = 1  # Lowest priority

# Usage
@app.task(base=HighPriorityTask)
def critical_task():
    pass

@app.task(base=MediumPriorityTask)
def normal_task():
    pass

@app.task(base=LowPriorityTask)
def background_task():
    pass
```

## Worker Pools

Celery supports different worker pool implementations:

### 1. Prefork Pool (Default)
- Uses multiprocessing
- Good for CPU-bound tasks
- Recommended for most use cases

```bash
celery -A config worker --pool=prefork --concurrency=4
```

### 2. Gevent Pool
- Uses greenlets (lightweight threads)
- Good for I/O-bound tasks
- Higher concurrency with less memory

```bash
celery -A config worker --pool=gevent --concurrency=100
```

### 3. Solo Pool
- Single process, no concurrency
- Good for debugging
- Not recommended for production

```bash
celery -A config worker --pool=solo
```

**Recommendation:**
- Use **prefork** for general-purpose tasks
- Use **gevent** for I/O-heavy tasks (API calls, database queries)
- Consider separate worker pools for different task types

## Deployment Checklist

- [ ] Configure broker (Redis/RabbitMQ)
- [ ] Configure result backend
- [ ] Set up worker deployment (Docker/K8s/systemd)
- [ ] Configure autoscaling (HPA/KEDA)
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure alerting (Alertmanager)
- [ ] Set up Flower for monitoring
- [ ] Test scaling behavior
- [ ] Document runbooks
- [ ] Train team on operations

## Troubleshooting

### Workers not scaling up

**Check:**
1. Verify autoscaler is running
2. Check metrics are being collected
3. Verify thresholds are configured correctly
4. Check resource limits (CPU/memory quotas)
5. Review autoscaler logs

### Workers scaling too aggressively

**Solutions:**
1. Increase cooldown periods
2. Adjust thresholds (higher for scale-up, lower for scale-down)
3. Add stabilization windows
4. Review task processing patterns

### Tasks timing out

**Solutions:**
1. Increase task timeout: `task_time_limit = 300`
2. Add more workers
3. Optimize task code
4. Split long-running tasks into smaller chunks

### Memory leaks

**Solutions:**
1. Set `CELERYD_MAX_TASKS_PER_CHILD` to restart workers periodically
2. Monitor memory usage per worker
3. Profile task code for memory leaks
4. Use memory limits to prevent OOM

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [KEDA](https://keda.sh/)
- [Flower Monitoring](https://flower.readthedocs.io/)
