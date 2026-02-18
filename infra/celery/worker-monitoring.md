# Celery Worker Monitoring Guide

This document describes how to monitor Celery workers in the MueJam Library application.

## Monitoring Tools

### 1. Flower - Real-time Monitoring

Flower is a web-based tool for monitoring and administering Celery clusters.

**Installation:**
```bash
pip install flower
```

**Start Flower:**
```bash
celery -A config flower --port=5555
```

**Access:**
- URL: `http://localhost:5555`
- Features:
  - Real-time task monitoring
  - Worker status and statistics
  - Task history and details
  - Task rate limiting
  - Worker pool management

**Configuration:**
```python
# In settings.py or celery.py
FLOWER_PORT = 5555
FLOWER_BASIC_AUTH = ['admin:password']  # Basic authentication
FLOWER_URL_PREFIX = '/flower'  # URL prefix for reverse proxy
```

### 2. Prometheus Metrics

Export Celery metrics to Prometheus for long-term monitoring and alerting.

**Installation:**
```bash
pip install celery-exporter
```

**Start Exporter:**
```bash
celery-exporter --broker-url=redis://localhost:6379/0
```

**Metrics Exposed:**
```
# Queue metrics
celery_queue_length{queue="celery"}
celery_queue_length{queue="priority"}

# Worker metrics
celery_workers_active
celery_workers_total

# Task metrics
celery_tasks_total{state="SUCCESS"}
celery_tasks_total{state="FAILURE"}
celery_tasks_total{state="RETRY"}
celery_task_duration_seconds_bucket
celery_task_duration_seconds_count
celery_task_duration_seconds_sum
```

### 3. Application Performance Monitoring (APM)

Integrate with APM tools for detailed performance insights.

**Sentry Integration:**
```python
# In celery.py
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[CeleryIntegration()],
    traces_sample_rate=0.1,
)
```

**New Relic Integration:**
```python
# In celery.py
import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

# Wrap Celery app
app = newrelic.agent.wrap_background_task(Celery('muejam'))
```

## Key Metrics to Monitor

### Worker Health Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| Active Workers | Number of running workers | < 1 (critical) |
| Worker CPU | CPU utilization per worker | > 90% (warning) |
| Worker Memory | Memory usage per worker | > 85% (warning) |
| Worker Uptime | Time since worker started | < 5min (info) |

### Queue Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| Queue Depth | Pending tasks in queue | > 1000 (warning) |
| Queue Growth Rate | Rate of queue growth | > 10/sec (warning) |
| Task Wait Time | Time tasks spend in queue | > 60s (warning) |
| Dead Letter Queue | Failed tasks | > 100 (warning) |

### Task Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| Task Success Rate | % of successful tasks | < 95% (warning) |
| Task Failure Rate | % of failed tasks | > 5% (warning) |
| Task Duration P95 | 95th percentile duration | > 300s (warning) |
| Task Retry Rate | % of tasks being retried | > 10% (warning) |
| Task Timeout Rate | % of tasks timing out | > 1% (warning) |

## Grafana Dashboards

### Dashboard 1: Worker Overview

**Panels:**
1. Active Workers (gauge)
2. Worker CPU Usage (graph)
3. Worker Memory Usage (graph)
4. Tasks Processed (counter)
5. Task Processing Rate (graph)

**Queries:**
```promql
# Active workers
celery_workers_active

# Worker CPU
rate(process_cpu_seconds_total{job="celery"}[5m]) * 100

# Worker memory
process_resident_memory_bytes{job="celery"}

# Tasks processed
increase(celery_tasks_total[1h])

# Task rate
rate(celery_tasks_total[5m])
```

### Dashboard 2: Queue Monitoring

**Panels:**
1. Queue Depth (graph)
2. Queue Growth Rate (graph)
3. Task Wait Time (graph)
4. Tasks by State (pie chart)

**Queries:**
```promql
# Queue depth
celery_queue_length

# Queue growth rate
deriv(celery_queue_length[5m])

# Task wait time
histogram_quantile(0.95, rate(celery_task_wait_time_seconds_bucket[5m]))

# Tasks by state
sum by (state) (celery_tasks_total)
```

### Dashboard 3: Task Performance

**Panels:**
1. Task Duration P50/P95/P99 (graph)
2. Task Success/Failure Rate (graph)
3. Top Slowest Tasks (table)
4. Task Retry Rate (graph)

**Queries:**
```promql
# Task duration percentiles
histogram_quantile(0.50, rate(celery_task_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(celery_task_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(celery_task_duration_seconds_bucket[5m]))

# Success rate
rate(celery_tasks_total{state="SUCCESS"}[5m]) / rate(celery_tasks_total[5m]) * 100

# Failure rate
rate(celery_tasks_total{state="FAILURE"}[5m]) / rate(celery_tasks_total[5m]) * 100

# Top slowest tasks
topk(10, avg by (task) (celery_task_duration_seconds_sum / celery_task_duration_seconds_count))

# Retry rate
rate(celery_tasks_total{state="RETRY"}[5m]) / rate(celery_tasks_total[5m]) * 100
```

## Alerting Rules

### Critical Alerts

```yaml
groups:
  - name: celery_critical
    rules:
      - alert: CeleryNoWorkersRunning
        expr: celery_workers_active == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "No Celery workers running"
          description: "All Celery workers are down. Background tasks are not being processed."

      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 5000
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Celery queue has large backlog"
          description: "Queue has {{ $value }} pending tasks. Workers may be overwhelmed."

      - alert: CeleryHighFailureRate
        expr: |
          (
            rate(celery_tasks_total{state="FAILURE"}[5m]) 
            / 
            rate(celery_tasks_total[5m])
          ) * 100 > 20
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High task failure rate"
          description: "{{ $value }}% of tasks are failing."
```

### Warning Alerts

```yaml
  - name: celery_warnings
    rules:
      - alert: CeleryWorkerHighCPU
        expr: rate(process_cpu_seconds_total{job="celery"}[5m]) * 100 > 90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery worker high CPU usage"
          description: "Worker {{ $labels.instance }} CPU usage is {{ $value }}%."

      - alert: CeleryWorkerHighMemory
        expr: |
          (
            process_resident_memory_bytes{job="celery"} 
            / 
            process_virtual_memory_max_bytes{job="celery"}
          ) * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery worker high memory usage"
          description: "Worker {{ $labels.instance }} memory usage is {{ $value }}%."

      - alert: CelerySlowTasks
        expr: |
          histogram_quantile(0.95, rate(celery_task_duration_seconds_bucket[5m])) > 300
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Celery tasks running slowly"
          description: "P95 task duration is {{ $value }}s (>5 minutes)."
```

## Logging

### Structured Logging

Configure structured logging for better log analysis.

```python
# In celery.py
from celery.signals import task_prerun, task_postrun, task_failure
import logging
import json

logger = logging.getLogger(__name__)

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    logger.info(json.dumps({
        'event': 'task_started',
        'task_id': task_id,
        'task_name': task.name,
        'args': str(args),
        'kwargs': str(kwargs),
    }))

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, **extra):
    logger.info(json.dumps({
        'event': 'task_completed',
        'task_id': task_id,
        'task_name': task.name,
        'result': str(retval),
    }))

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **extra):
    logger.error(json.dumps({
        'event': 'task_failed',
        'task_id': task_id,
        'task_name': sender.name,
        'exception': str(exception),
        'traceback': str(traceback),
    }))
```

### Log Aggregation

Send logs to centralized logging system (ELK, Loki, CloudWatch).

**Filebeat Configuration:**
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/celery/*.log
  fields:
    service: celery
    environment: production
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "celery-logs-%{+yyyy.MM.dd}"
```

## Health Checks

### Worker Health Check

```python
# In celery.py
from celery import Celery
from celery.app.control import Inspect

def check_worker_health():
    """Check if workers are healthy."""
    inspect = Inspect(app=app)
    
    # Check active workers
    active = inspect.active()
    if not active:
        return False, "No active workers"
    
    # Check registered tasks
    registered = inspect.registered()
    if not registered:
        return False, "No registered tasks"
    
    # Check stats
    stats = inspect.stats()
    if not stats:
        return False, "Cannot get worker stats"
    
    return True, "Workers healthy"
```

### Queue Health Check

```python
def check_queue_health():
    """Check if queue is healthy."""
    from celery import current_app
    
    # Get queue length
    inspect = Inspect(app=current_app)
    reserved = inspect.reserved()
    
    if not reserved:
        return True, "Queue empty"
    
    # Check if queue is too long
    total_tasks = sum(len(tasks) for tasks in reserved.values())
    if total_tasks > 1000:
        return False, f"Queue backlog: {total_tasks} tasks"
    
    return True, f"Queue healthy: {total_tasks} tasks"
```

## Troubleshooting Commands

```bash
# Check worker status
celery -A config inspect active

# Check registered tasks
celery -A config inspect registered

# Check worker stats
celery -A config inspect stats

# Ping workers
celery -A config inspect ping

# Purge queue (DANGEROUS!)
celery -A config purge

# Revoke task
celery -A config revoke <task-id>

# Shutdown worker
celery -A config control shutdown

# Enable/disable events
celery -A config control enable_events
celery -A config control disable_events
```

## Best Practices

1. **Monitor continuously**: Set up dashboards and alerts
2. **Log everything**: Use structured logging for better analysis
3. **Set timeouts**: Prevent tasks from running forever
4. **Use retries**: Configure automatic retries for transient failures
5. **Limit concurrency**: Prevent resource exhaustion
6. **Monitor queue depth**: Alert on growing queues
7. **Track task duration**: Identify slow tasks
8. **Monitor failure rates**: Investigate high failure rates
9. **Use health checks**: Implement liveness and readiness probes
10. **Document runbooks**: Create procedures for common issues
