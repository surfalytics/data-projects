# Environment Setup Guide

This document walks you through every dependency you need for the **Data Streaming Mastery** course.

## System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| Free disk space | 20 GB | 40 GB |
| CPU cores | 4 | 8 |
| OS | macOS 12+, Windows 10/11, Ubuntu 20.04+ | macOS 14+, Ubuntu 22.04+ |

> The capstone module runs 15+ containers simultaneously. If you only have 8 GB RAM, close other applications and allocate at least 6 GB to Docker.

---

## 1. Docker Desktop

### macOS

```bash
# Option A: Homebrew (recommended)
brew install --cask docker

# Option B: Download the installer
# https://docs.docker.com/desktop/install/mac-install/
```

After installation, open Docker Desktop and go to **Settings > Resources**:
- Memory: **8 GB** (minimum), **12 GB** recommended
- CPUs: **4** minimum
- Disk image size: **60 GB**

### Windows

1. Enable **WSL 2** (Windows Subsystem for Linux):
   ```powershell
   wsl --install
   ```
2. Download and install Docker Desktop from [docker.com](https://docs.docker.com/desktop/install/windows-install/).
3. In Docker Desktop settings, ensure **Use the WSL 2 based engine** is checked.
4. Allocate resources the same way as macOS (Settings > Resources).

### Linux (Ubuntu/Debian)

```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key and repository
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# Allow running Docker without sudo
sudo usermod -aG docker $USER
newgrp docker
```

---

## 2. Python 3.9+

### macOS

```bash
# Homebrew
brew install python@3.11

# Verify
python3 --version   # Should print 3.9 or higher
```

### Windows

Download the installer from [python.org](https://www.python.org/downloads/). During installation, check **Add Python to PATH**.

### Linux

```bash
sudo apt-get install -y python3 python3-pip python3-venv
```

### Virtual Environment

Create a dedicated virtual environment for the course:

```bash
cd data-streaming-mastery
python3 -m venv .venv
source .venv/bin/activate    # macOS / Linux
# .venv\Scripts\activate     # Windows PowerShell

pip install --upgrade pip setuptools wheel
```

Install common course dependencies:

```bash
pip install \
  confluent-kafka==2.3.0 \
  fastavro==1.9.3 \
  requests==2.31.0 \
  faust-streaming==0.11.0 \
  httpx==0.25.2 \
  psycopg2-binary==2.9.9 \
  mysql-connector-python==8.2.0 \
  pydantic==2.5.3
```

---

## 3. Verify Installations

Run each command and confirm the output matches (versions may differ slightly):

```bash
# Docker
docker --version
# Docker version 24.x or higher

docker compose version
# Docker Compose version v2.x

# Python
python3 --version
# Python 3.9+

# Test Docker can pull and run images
docker run --rm hello-world

# Test Docker Compose with the course stack (quick smoke test)
cd data-streaming-mastery
docker compose config --quiet && echo "Compose file is valid"
```

---

## 4. IDE Recommendations

### VS Code (recommended)

Install [Visual Studio Code](https://code.visualstudio.com/) with the following extensions:

| Extension | ID | Purpose |
|---|---|---|
| Python | `ms-python.python` | Python IntelliSense, debugging |
| Docker | `ms-azuretools.vscode-docker` | Dockerfile/Compose syntax and management |
| YAML | `redhat.vscode-yaml` | YAML validation and auto-complete |
| SQL Tools | `mtxr.sqltools` | Run SQL against PostgreSQL/MySQL |
| SQL Tools MySQL | `mtxr.sqltools-driver-mysql` | MySQL driver for SQL Tools |
| SQL Tools PostgreSQL | `mtxr.sqltools-driver-pg` | PostgreSQL driver for SQL Tools |
| REST Client | `humao.rest-client` | Test HTTP APIs (Schema Registry, Connect) |
| Avro Viewer | `ryansmith.avro-viewer` | View Avro schemas |

Recommended `settings.json` additions:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "yaml.schemas": {
    "https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json": "docker-compose*.yml"
  }
}
```

### Alternative IDEs

- **PyCharm Professional** -- native Docker and database tooling
- **IntelliJ IDEA** with the Python and Docker plugins
- **DataGrip** for SQL work alongside any text editor

---

## 5. Troubleshooting

### Docker Memory Issues

**Symptom:** Containers exit with code 137, or `docker compose up` hangs.

```bash
# Check current Docker memory allocation
docker info | grep "Total Memory"

# On macOS/Windows: increase via Docker Desktop > Settings > Resources > Memory
# On Linux: check system memory
free -h
```

Recommended Docker memory settings for this course:

| Modules 01-08 (individual) | Capstone (Module 09) |
|---|---|
| 4 GB | 8-12 GB |

### Port Conflicts

The course uses these ports. Make sure nothing else is listening on them:

| Port | Service |
|------|---------|
| 2181 | ZooKeeper |
| 9092, 9093, 9094 | Kafka brokers |
| 8081 | Schema Registry |
| 8083 | Kafka Connect REST API |
| 8088 | ksqlDB |
| 3306 | MySQL |
| 5432 | PostgreSQL |
| 8080 | Kafka UI |
| 3000 | Grafana |
| 9090 | Prometheus |

Check for conflicts:

```bash
# macOS / Linux
for port in 2181 9092 9093 9094 8081 8083 8088 3306 5432 8080 3000 9090; do
  lsof -i :$port 2>/dev/null && echo "^^^ Port $port is in use"
done
```

To free a port:

```bash
# Find the PID
lsof -ti :8080
# Kill it
kill -9 $(lsof -ti :8080)
```

### Docker Compose Errors

```bash
# Reset everything and start fresh
docker compose down -v --remove-orphans
docker system prune -f
docker compose up -d
```

### Kafka Broker Not Ready

If producers or consumers fail to connect immediately after `docker compose up`:

```bash
# Wait for Kafka to be fully ready
docker compose exec kafka-1 cub kafka-ready -b kafka-1:29092 1 60

# Or use a retry loop
until docker compose exec kafka-1 kafka-topics --bootstrap-server kafka-1:29092 --list 2>/dev/null; do
  echo "Waiting for Kafka..."
  sleep 5
done
```

### Schema Registry 409 Conflict

This happens when you try to register an incompatible schema:

```bash
# Check current compatibility level
curl -s http://localhost:8081/config | jq

# Temporarily set to NONE for development (do not do this in production)
curl -X PUT -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"compatibility": "NONE"}' \
  http://localhost:8081/config
```

### Python Virtual Environment Not Activated

If `pip install` installs packages globally or `import` fails:

```bash
# Make sure you see (.venv) in your shell prompt
which python3
# Should show: /path/to/data-streaming-mastery/.venv/bin/python3

# If not, activate it
source .venv/bin/activate
```

### WSL 2 (Windows) Specific Issues

```powershell
# Ensure WSL 2 is the default
wsl --set-default-version 2

# If Docker fails to start, restart the WSL backend
wsl --shutdown
# Then reopen Docker Desktop
```

---

## Next Steps

Once everything is installed and verified, head back to the [README](README.md) and start with **Module 01: Fundamentals**.
