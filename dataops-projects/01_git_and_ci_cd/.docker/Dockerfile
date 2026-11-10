# Use an official Ubuntu LTS as base image
FROM ubuntu:24.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# DuckDB CLI version. Check https://github.com/duckdb/duckdb/releases for the latest.
ARG DUCKDB_VERSION=v2.0.0

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and install DuckDB CLI dynamically based on system architecture
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        echo "Installing DuckDB CLI for x86_64 (amd64)"; \
        DUCKDB_ARCH=amd64; \
    elif [ "$ARCH" = "aarch64" ]; then \
        echo "Installing DuckDB CLI for ARM64 (aarch64)"; \
        DUCKDB_ARCH=arm64; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    wget -q "https://github.com/duckdb/duckdb/releases/download/${DUCKDB_VERSION}/duckdb-cli-linux-${DUCKDB_ARCH}.tar.gz" && \
    tar -xzf duckdb-cli-linux-*.tar.gz && \
    chmod +x duckdb && \
    mv duckdb /usr/local/bin/ && \
    rm duckdb-cli-linux-*.tar.gz

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Default command
CMD ["./scripts/analyze_data.sh"]
