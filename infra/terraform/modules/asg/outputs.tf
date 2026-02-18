output "asg_id" {
  description = "ID of the auto-scaling group"
  value       = aws_autoscaling_group.app.id
}

output "asg_name" {
  description = "Name of the auto-scaling group"
  value       = aws_autoscaling_group.app.name
}

output "asg_arn" {
  description = "ARN of the auto-scaling group"
  value       = aws_autoscaling_group.app.arn
}

output "launch_template_id" {
  description = "ID of the launch template"
  value       = aws_launch_template.app.id
}

output "app_security_group_id" {
  description = "ID of the application security group"
  value       = aws_security_group.app.id
}
