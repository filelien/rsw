# ─── RAXUS ALL-IN-ONE DOCKERFILE ─────────────────────────────────────
# Multi-stage build for Node.js frontend + Python microservices

# ─── BASE NODE IMAGE ─────────────────────────────────────────────────────
FROM node:20-alpine AS node-base
WORKDIR /app

# ─── BASE PYTHON IMAGE ───────────────────────────────────────────────────
FROM python:3.12-slim AS python-base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc curl && rm -rf /var/lib/apt/lists/*

# ─── FRONTEND BUILD ───────────────────────────────────────────────────────
FROM node-base AS frontend-builder
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# ─── PYTHON SERVICES DEPENDENCIES ─────────────────────────────────────────
FROM python-base AS python-deps
COPY services/gateway/requirements.txt ./gateway/
COPY services/alertmanager/requirements.txt ./alertmanager/
COPY services/inventory/requirements.txt ./inventory/
COPY services/notifier/requirements.txt ./notifier/
COPY services/taskmanager/requirements.txt ./taskmanager/
COPY services/slo-engine/requirements.txt ./slo-engine/
COPY services/rules-engine/requirements.txt ./rules-engine/

RUN pip install --no-cache-dir -r gateway/requirements.txt && \
    pip install --no-cache-dir -r alertmanager/requirements.txt && \
    pip install --no-cache-dir -r inventory/requirements.txt && \
    pip install --no-cache-dir -r notifier/requirements.txt && \
    pip install --no-cache-dir -r taskmanager/requirements.txt && \
    pip install --no-cache-dir -r slo-engine/requirements.txt && \
    pip install --no-cache-dir -r rules-engine/requirements.txt

# ─── FINAL ALL-IN-ONE IMAGE ───────────────────────────────────────────────
FROM python-base AS raxus-all-in-one

# Install Node.js for frontend
RUN apk add --no-cache nodejs npm

# Copy Python dependencies
COPY --from=python-deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy frontend build
COPY --from=frontend-builder /app/.next/standalone ./
COPY --from=frontend-builder /app/.next/static ./.next/static
COPY --from=frontend-builder /app/public ./public
COPY --from=frontend-builder /app/node_modules ./node_modules

# Copy all Python services
COPY services/gateway/ ./gateway/
COPY services/alertmanager/ ./alertmanager/
COPY services/inventory/ ./inventory/
COPY services/notifier/ ./notifier/
COPY services/taskmanager/ ./taskmanager/
COPY services/slo-engine/ ./slo-engine/
COPY services/rules-engine/ ./rules-engine/

# Copy infrastructure configs
COPY infra/ ./infra/

# Create startup script
RUN cat > /app/start-all.sh << 'EOF'
#!/bin/sh
echo "🚀 Starting RAXUS All-in-One Platform..."

# Set environment variables
export ENVIRONMENT=${ENVIRONMENT:-development}
export DATABASE_URL=${DATABASE_URL:-mysql+aiomysql://raxus:raxus_pass@localhost:3306/raxus}
export REDIS_URL=${REDIS_URL:-redis://:raxus_redis@localhost:6379/0}
export SECRET_KEY=${SECRET_KEY:-supersecret-change-in-prod}
export VAULT_URL=${VAULT_URL:-http://localhost:8200}
export VAULT_TOKEN=${VAULT_TOKEN:-raxus-vault-token}

# Function to start a service in background
start_service() {
    echo "📡 Starting $1 on port $2..."
    cd $1
    python main.py &
    cd ..
}

# Start all Python microservices
start_service "gateway" "8000"
start_service "alertmanager" "8001" 
start_service "inventory" "8002"
start_service "notifier" "8003"
start_service "taskmanager" "8004"
start_service "slo-engine" "8005"
start_service "rules-engine" "8006"

# Start Celery worker
echo "🔄 Starting Celery worker..."
cd taskmanager
celery -A app.celery_app worker --loglevel=info --concurrency=4 &
cd ..

# Start frontend
echo "🎨 Starting Next.js frontend on port 3000..."
NODE_ENV=production node server.js

# Wait for all background processes
wait
EOF

RUN chmod +x /app/start-all.sh

# Expose all ports
EXPOSE 3000 8000 8001 8002 8003 8004 8005 8006

# Health check
RUN cat > /app/health-check.sh << 'EOF'
#!/bin/sh
echo "🔍 Checking RAXUS services health..."
curl -f http://localhost:3000 > /dev/null 2>&1 && echo "✅ Frontend OK" || echo "❌ Frontend DOWN"
curl -f http://localhost:8000/health > /dev/null 2>&1 && echo "✅ Gateway OK" || echo "❌ Gateway DOWN"
curl -f http://localhost:8001/health > /dev/null 2>&1 && echo "✅ Alertmanager OK" || echo "❌ Alertmanager DOWN"
curl -f http://localhost:8002/health > /dev/null 2>&1 && echo "✅ Inventory OK" || echo "❌ Inventory DOWN"
curl -f http://localhost:8003/health > /dev/null 2>&1 && echo "✅ Notifier OK" || echo "❌ Notifier DOWN"
curl -f http://localhost:8004/health > /dev/null 2>&1 && echo "✅ TaskManager OK" || echo "❌ TaskManager DOWN"
curl -f http://localhost:8005/health > /dev/null 2>&1 && echo "✅ SLO Engine OK" || echo "❌ SLO Engine DOWN"
curl -f http://localhost:8006/health > /dev/null 2>&1 && echo "✅ Rules Engine OK" || echo "❌ Rules Engine DOWN"
EOF

RUN chmod +x /app/health-check.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/health-check.sh

# Start all services
CMD ["/app/start-all.sh"]
