resource "aws_ecs_cluster" "this" {
  name = "${var.project_name}-cluster"
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
}

resource "aws_cloudwatch_log_group" "metabase" {
  name              = "/ecs/${var.project_name}-task"
  retention_in_days = 30
}

resource "aws_ecs_task_definition" "metabase" {
  family                   = "${var.project_name}-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.task_execution.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture         = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "metabase"
      image     = var.metabase_image
      essential = true
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
          name          = "metabase-3000-tcp"
          appProtocol   = "http"
        }
      ]
      environment = [
        { name = "MB_DB_TYPE", value = "postgres" },
        { name = "MB_DB_DBNAME", value = var.db_name },
        { name = "MB_DB_HOST", value = aws_db_instance.this.address },
        { name = "MB_DB_PORT", value = "5432" },
        { name = "MB_DB_USER", value = var.db_username },
        { name = "MB_DB_PASS", value = var.db_password },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.metabase.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "metabase" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.metabase.arn
  desired_count   = 1

  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 0
  }

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.metabase.arn
    container_name   = "metabase"
    container_port   = 3000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener.http]
}
