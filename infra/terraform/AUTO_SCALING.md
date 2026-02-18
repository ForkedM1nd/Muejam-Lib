# Auto-Scaling Configuration

This document describes the auto-scaling configuration for the MueJam Library platform.

## Overview

The platform uses AWS Auto Scaling Groups (ASG) with CPU-based scaling policies to automatically adjust capacity based on demand. This ensures the platform can handle traffic spikes while minimizing costs during low-traffic periods.

## Configuration

### Capacity Settings

- **Minimum instances**: 2
  - Ensures high availability with redundancy
  - Allows zero-downtime deployments
  - Distributes load across multiple availability zones

- **Maximum instances**: 10
  - Supports up to 10,000 concurrent users
  - Prevents runaway scaling costs
  - Provides sufficient capacity for traffic spikes

- **Desired capacity**: 2
  - Starting point for normal operations
  - Auto-scaling adjusts this based on metrics

### Scaling Policies

#### Scale Up Policy

Triggers when CPU utilization is high:

- **Metric**: Average CPU Utilization
- **Threshold**: 70%
- **Evaluation periods**: 2 consecutive periods
- **Period duration**: 2 minutes (120 seconds)
- **Action**: Add 2 instances
- **Cooldown**: 5 minutes

**Behavior**: When average CPU exceeds 70% for 4 minutes (2 periods × 2 minutes), the ASG adds 2 new instances. After scaling, it waits 5 minutes before evaluating again.

#### Scale Down Policy

Triggers when CPU utilization is low:

- **Metric**: Average CPU Utilization
- **Threshold**: 30%
- **Evaluation periods**: 2 consecutive periods
- **Period duration**: 2 minutes (120 seconds)
- **Action**: Remove 1 instance
- **Cooldown**: 5 minutes

**Behavior**: When average CPU falls below 30% for 4 minutes, the ASG removes 1 instance. After scaling, it waits 5 minutes before evaluating again.

### Why These Settings?

**70% scale-up threshold**:
- Provides headroom before instances become overloaded
- Allows time for new instances to launch and warm up
- Prevents performance degradation during traffic spikes

**30% scale-down threshold**:
- Ensures instances are well-utilized before scaling down
- Prevents frequent scaling oscillations
- Maintains buffer capacity for sudden traffic increases

**2-minute evaluation periods**:
- Filters out temporary CPU spikes
- Ensures sustained load before scaling
- Reduces unnecessary scaling actions

**5-minute cooldown**:
- Allows new instances to fully initialize
- Prevents rapid scaling oscillations
- Gives time for metrics to stabilize

**Add 2, remove 1**:
- Scales up aggressively to handle traffic spikes quickly
- Scales down conservatively to avoid capacity issues
- Asymmetric scaling prevents oscillation

## Health Checks

The Auto Scaling Group uses ELB (Elastic Load Balancer) health checks:

- **Type**: ELB health check
- **Grace period**: 300 seconds (5 minutes)
- **Endpoint**: `/health`
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Healthy threshold**: 2 consecutive successes
- **Unhealthy threshold**: 3 consecutive failures

### Health Check Behavior

1. New instances have a 5-minute grace period before health checks begin
2. ALB checks `/health` endpoint every 30 seconds
3. Instance must respond with HTTP 200 within 5 seconds
4. After 2 consecutive successful checks, instance is marked healthy
5. After 3 consecutive failed checks, instance is marked unhealthy
6. Unhealthy instances are automatically terminated and replaced

## Instance Lifecycle

### Launch Process

1. **Launch**: ASG creates new EC2 instance from launch template
2. **Initialize**: User data script runs to set up application
3. **Grace period**: 5-minute grace period before health checks
4. **Health checks**: ALB begins checking `/health` endpoint
5. **In service**: After 2 successful health checks, instance receives traffic
6. **Warm-up**: Application warms up caches and connections

Total time from launch to serving traffic: ~6-8 minutes

### Termination Process

1. **Deregister**: Instance is removed from ALB target group
2. **Drain**: Existing connections have 60 seconds to complete
3. **Terminate**: Instance is shut down after drain period
4. **Cleanup**: AWS cleans up resources

## Monitoring

### CloudWatch Metrics

The ASG publishes these metrics to CloudWatch:

- `GroupDesiredCapacity`: Target number of instances
- `GroupInServiceInstances`: Number of healthy instances
- `GroupPendingInstances`: Number of instances launching
- `GroupTerminatingInstances`: Number of instances terminating
- `GroupTotalInstances`: Total number of instances
- `GroupMinSize`: Minimum capacity
- `GroupMaxSize`: Maximum capacity

### CloudWatch Alarms

Two alarms monitor CPU and trigger scaling:

1. **muejam-{environment}-cpu-high**
   - Triggers scale-up policy
   - Monitors average CPU across all instances
   - Alerts when CPU > 70% for 4 minutes

2. **muejam-{environment}-cpu-low**
   - Triggers scale-down policy
   - Monitors average CPU across all instances
   - Alerts when CPU < 30% for 4 minutes

## Testing Auto-Scaling

### Load Testing

To test auto-scaling behavior:

1. **Generate load**: Use load testing tools (Apache Bench, Locust, k6)
2. **Monitor metrics**: Watch CloudWatch metrics and alarms
3. **Observe scaling**: Verify instances are added when CPU exceeds 70%
4. **Reduce load**: Stop load generation
5. **Observe scale-down**: Verify instances are removed when CPU drops below 30%

### Example Load Test

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Generate load (adjust -n and -c based on your needs)
ab -n 100000 -c 100 https://your-alb-dns-name/v1/stories/

# Monitor in another terminal
watch -n 5 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names muejam-production-asg \
  --query "AutoScalingGroups[0].[DesiredCapacity,Instances[*].InstanceId]"'
```

## Troubleshooting

### Instances not scaling up

**Symptoms**: CPU is high but no new instances are launched

**Possible causes**:
1. Maximum capacity reached (10 instances)
2. Cooldown period still active
3. CloudWatch alarm not in ALARM state
4. Insufficient EC2 capacity in region/AZ

**Solutions**:
1. Check current instance count vs max capacity
2. Wait for cooldown period to expire
3. Check CloudWatch alarm state in AWS console
4. Try different instance type or region

### Instances not scaling down

**Symptoms**: CPU is low but instances are not terminated

**Possible causes**:
1. Minimum capacity reached (2 instances)
2. Cooldown period still active
3. CloudWatch alarm not in ALARM state
4. Scale-in protection enabled on instances

**Solutions**:
1. Check current instance count vs min capacity
2. Wait for cooldown period to expire
3. Check CloudWatch alarm state
4. Verify scale-in protection is disabled

### Instances failing health checks

**Symptoms**: Instances are launched but immediately terminated

**Possible causes**:
1. Application not starting correctly
2. `/health` endpoint not responding
3. Security group blocking ALB traffic
4. Application listening on wrong port

**Solutions**:
1. Check application logs on instance
2. SSH to instance and test `/health` endpoint locally
3. Verify security group allows traffic from ALB on port 8000
4. Verify application is listening on port 8000

### Rapid scaling oscillations

**Symptoms**: Instances are repeatedly added and removed

**Possible causes**:
1. Thresholds too close together
2. Cooldown period too short
3. Application has high startup CPU usage

**Solutions**:
1. Increase gap between scale-up and scale-down thresholds
2. Increase cooldown period
3. Optimize application startup to reduce CPU usage
4. Increase grace period for new instances

## Cost Optimization

### Strategies

1. **Right-size instances**: Use appropriate instance type for workload
2. **Spot instances**: Use spot instances for non-critical workloads
3. **Reserved instances**: Purchase reserved instances for baseline capacity
4. **Scheduled scaling**: Pre-scale for known traffic patterns
5. **Aggressive scale-down**: Reduce scale-down threshold if traffic is predictable

### Cost Monitoring

Monitor costs in AWS Cost Explorer:
- Filter by Auto Scaling Group tag
- Track EC2 instance hours
- Compare costs across different instance types
- Set up billing alerts for unexpected costs

## Advanced Configuration

### Scheduled Scaling

For predictable traffic patterns, configure scheduled scaling:

```hcl
resource "aws_autoscaling_schedule" "scale_up_morning" {
  scheduled_action_name  = "scale-up-morning"
  min_size               = 4
  max_size               = 10
  desired_capacity       = 4
  recurrence             = "0 8 * * MON-FRI"  # 8 AM weekdays
  autoscaling_group_name = aws_autoscaling_group.app.name
}

resource "aws_autoscaling_schedule" "scale_down_evening" {
  scheduled_action_name  = "scale-down-evening"
  min_size               = 2
  max_size               = 10
  desired_capacity       = 2
  recurrence             = "0 20 * * *"  # 8 PM daily
  autoscaling_group_name = aws_autoscaling_group.app.name
}
```

### Target Tracking Scaling

Alternative to step scaling, use target tracking:

```hcl
resource "aws_autoscaling_policy" "target_tracking" {
  name                   = "target-tracking-policy"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}
```

### Multiple Metrics

Scale based on multiple metrics (CPU, memory, request count):

```hcl
resource "aws_autoscaling_policy" "multi_metric" {
  name                   = "multi-metric-policy"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    customized_metric_specification {
      metric_dimension {
        name  = "AutoScalingGroupName"
        value = aws_autoscaling_group.app.name
      }
      metric_name = "RequestCountPerTarget"
      namespace   = "AWS/ApplicationELB"
      statistic   = "Average"
    }
    target_value = 1000.0
  }
}
```

## Best Practices

1. **Monitor continuously**: Set up CloudWatch dashboards for ASG metrics
2. **Test regularly**: Perform load tests to verify scaling behavior
3. **Tune thresholds**: Adjust based on actual traffic patterns
4. **Use multiple AZs**: Distribute instances across availability zones
5. **Implement graceful shutdown**: Handle SIGTERM for clean shutdowns
6. **Warm up caches**: Pre-warm caches on new instances
7. **Log scaling events**: Track when and why scaling occurs
8. **Set up alerts**: Alert on scaling failures or capacity issues
9. **Review costs**: Regularly review and optimize instance costs
10. **Document changes**: Keep this document updated with configuration changes

## References

- [AWS Auto Scaling Documentation](https://docs.aws.amazon.com/autoscaling/)
- [CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [Target Tracking Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html)
- [Terraform AWS ASG](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_group)
