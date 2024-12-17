# Use an official Ubuntu as base image
FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    sqlite3 \
    ca-certificates \
    libc6 \
    && rm -rf /var/lib/apt/lists/*

# Download and install DuckDB CLI dynamically based on system architecture
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        echo "Installing DuckDB CLI for x86_64 (amd64)"; \
        wget https://github.com/duckdb/duckdb/releases/download/v1.1.3/duckdb_cli-linux-amd64.zip; \
    elif [ "$ARCH" = "aarch64" ]; then \
        echo "Installing DuckDB CLI for ARM64 (aarch64)"; \
        wget https://github.com/duckdb/duckdb/releases/download/v1.1.3/duckdb_cli-linux-aarch64.zip; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    unzip duckdb_cli-linux-*.zip && \
    chmod +x duckdb && \
    mv duckdb /usr/local/bin/ && \
    rm duckdb_cli-linux-*.zip

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Default command
CMD ["./scripts/analyze_data.sh"]
