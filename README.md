# AI-DevOps-Assistant  
One-command starter: LocalAI + FastAPI + Postgres, Docker-Compose, Terraform (Hetzner), GitHub-Actions CI, Prometheus/Grafana monitoring, FinOps cost-checker.

## Quick start
```bash
# клонируй
git clone https://github.com/mrukhin/ai-devops-assistant.git
cd ai-devops-assistant

# подними стек
make up          # = docker compose up -d
make logs        # посмотреть логи
make down        # выключить| File                       | Purpose                                                                     |
| -------------------------- | --------------------------------------------------------------------------- |
| `docker-compose.yml`       | LocalAI (OpenAI-compatible API), FastAPI app, Postgres, Prometheus, Grafana |
| `Makefile`                 | короткие команды вместо длинных docker-compose                              |
| `terraform/`               | код для VPS в Hetzner (~5 \$/мес)                                           |
| `.github/workflows/ci.yml` | линтер + сборка + деплой на VPS                                             |
| `scripts/finops.py`        | считает счет за облако и советует, где срезать                              |
---

### 2. docker-compose.yml (Create new file → имя файла: `docker-compose.yml`)
```yaml
version: "3.9"
services:
  localai:
    image: localai/localai:latest
    ports: ["8080:8080"]
    environment:
      - MODELS_PATH=/models
    volumes:
      - ./models:/models
    command: ["/usr/bin/localai" ]

  app:
    build: ./app
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/aiapp
    depends_on: [db]

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: aiapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - db_data:/var/lib/postgresql/data

  prometheus:
    image: prom/prometheus
    ports: ["9090:9090"]
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports: ["3000:3000"]
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  db_data:
  grafana_data:.PHONY: up down logs ps clean

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v --remove-orphansfrom fastapi import FastAPI
import os

app = FastAPI(title="AI-DevOps demo")

@app.get("/")
def root():
    return {"message": "AI-DevOps assistant is running"}

@app.get("/health")
def health():
    return {"status": "ok"}FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]fastapi==0.110
uvicorn[standard]==0.27global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['app:8000']#!/usr/bin/env python3
"""
Простейший FinOps-чекер для Hetzner:
считает стоимость VPS из terraform.tfvars и печатает советы.
"""
import json, sys, pathlib

TFVARS = pathlib.Path(__file__).parent.parent / "terraform" / "terraform.tfvars"
PRICE_MAP = {"cx11": 2.96, "cx21": 5.93}   # €/мес (2025)

def main():
    if not TFVARS.exists():
        print("Файл terraform.tfvars не найден — пропускаем.")
        return
    data = TFVARS.read_text()
    server_type = "cx11"  # парсим грубо
    for line in data.splitlines():
        if "server_type" in line:
            server_type = line.split("=")[-1].strip().strip('"')
    cost = PRICE_MAP.get(server_type, 3)
    print(f"Текущая VPS: {server_type} ≈ {cost} €/мес.")
    print("Совет: перейди на cx11 если нагрузка < 20 % CPU.")
    return cost

if __name__ == "__main__":
    main()terraform {
  required_providers {
    hcloud = { source = "hetznercloud/hcloud", version = "~> 1.45" }
  }
}

variable "hcloud_token" {}        # экспортируй TF_VAR_hcloud_token
variable "server_type" { default = "cx11" }
variable "location"    { default = "nbg1" }   # Нюрнберг

resource "hcloud_server" "node" {
  name        = "ai-devops"
  image       = "ubuntu-22.04"
  server_type = var.server_type
  location    = var.location

  user_data = <<-EOF
    #!/bin/bash
    apt-get update && apt-get install -y docker.io docker-compose-v2
    usermod -aG docker ubuntu
  EOF
}

output "ipv4" { value = hcloud_server.node.ipv4_address }server_type = "cx11"
location    = "nbg1" name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: '3.11' }
    - run: pip install flake8
    - run: flake8 app --max-line-length=88

  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - run: docker compose build
A[LocalAI API] -->|served by| B(FastAPI app)
    B -->|uses| C[(Postgres)]
    B -->|metrics| D(Prometheus)
    D -->|graphs| E(Grafana)
    F(User) -->|queries| A
    F -->|dashboard| E   ```
