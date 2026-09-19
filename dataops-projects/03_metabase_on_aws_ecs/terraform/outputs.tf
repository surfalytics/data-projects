output "alb_dns_name" {
  description = "URL to reach Metabase through the load balancer"
  value       = "http://${aws_lb.this.dns_name}"
}

output "rds_endpoint" {
  description = "RDS Postgres endpoint address"
  value       = aws_db_instance.this.address
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.this.name
}
