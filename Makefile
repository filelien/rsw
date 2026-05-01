.PHONY: up down build logs ps clean reset seed

# Start all services
up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d --build

# Start without rebuild
start:
	docker compose up -d

# Stop all
down:
	docker compose down

# Build all images
build:
	docker compose build --parallel

# View logs
logs:
	docker compose logs -f

logs-gateway:
	docker compose logs -f gateway

logs-alertmanager:
	docker compose logs -f alertmanager

# Status
ps:
	docker compose ps

# Clean everything (data included)
clean:
	docker compose down -v --remove-orphans
	docker system prune -f

# Reset DB only
reset-db:
	docker compose stop mysql
	docker compose rm -f mysql
	docker volume rm raxus_mysql_data 2>/dev/null || true
	docker compose up -d mysql

# Shell into service
shell-gateway:
	docker compose exec gateway bash

shell-mysql:
	docker compose exec mysql mysql -u raxus -praxus_pass raxus

# Send test alert (Prometheus format)
test-alert:
	curl -X POST http://localhost:8000/api/v1/alerts/ingest/prometheus \
	  -H "Content-Type: application/json" \
	  -d '{"version":"4","status":"firing","alerts":[{"status":"firing","labels":{"alertname":"TestAlert","severity":"critical","instance":"server-01","job":"node"},"annotations":{"summary":"Test critical alert from RAXUS","description":"This is a test"}}]}'

# Test webhook
test-webhook:
	curl -X POST http://localhost:8000/api/v1/alerts/ingest/webhook \
	  -H "Content-Type: application/json" \
	  -d '{"alerts":[{"name":"HighCPU","severity":"major","instance":"web-01","summary":"CPU above 90%","value":92.5,"threshold":90}]}'

# API docs
docs:
	@echo "Gateway API docs: http://localhost:8000/docs"
	@echo "Grafana: http://localhost:3001"
	@echo "RAXUS UI: http://localhost:3000"

# Health check all services
health:
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@curl -s http://localhost:8001/health | python3 -m json.tool
	@curl -s http://localhost:8002/health | python3 -m json.tool
	@curl -s http://localhost:8003/health | python3 -m json.tool
	@curl -s http://localhost:8004/health | python3 -m json.tool
	@curl -s http://localhost:8005/health | python3 -m json.tool
	@curl -s http://localhost:8006/health | python3 -m json.tool
