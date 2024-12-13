# Define ANSI color codes
YELLOW = \033[1;33m
GREEN = \033[1;32m
RESET = \033[0m

# Target to build the Docker container
.PHONY: build
build:
	@echo "$(YELLOW)Building the Docker container...$(RESET)"
	docker build -t duckdb-data-analysis -f .docker/Dockerfile .
	@echo "$(GREEN)Build completed successfully!$(RESET)"

# Target to run the Docker container
.PHONY: run
run:
	@echo "$(YELLOW)Starting the Docker container...$(RESET)"
	docker run -it --rm duckdb-data-analysis
	@echo "$(GREEN)Program executed successfully!$(RESET)"

# Target to display help
.PHONY: help
help:
	@echo "$(YELLOW)Available commands:$(RESET)"
	@echo "  $(GREEN)make build$(RESET) - Build the Docker container."
	@echo "  $(GREEN)make run$(RESET)   - Start the Docker container and run the program."