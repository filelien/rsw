# RAXUS — All-in-One Docker Setup

> 🚀 **Single container deployment** - All services running together!

## 🎯 Quick Start

```bash
# 1. Clone and setup
cd raxus
cp .env.example .env

# 2. Start everything in ONE container
make -f Makefile-all-in-one quick-start
```

That's it! 🎉 All services start automatically.

## 📋 Services Included

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 3000 | Next.js UI |
| **Gateway** | 8000 | Main API |
| **Alertmanager** | 8001 | Alert processing |
| **Inventory** | 8002 | Asset management |
| **Notifier** | 8003 | Notifications |
| **TaskManager** | 8004 | Task execution |
| **SLO Engine** | 8005 | SLO monitoring |
| **Rules Engine** | 8006 | Automation rules |
| **Grafana** | 3001 | Dashboards |
| **VictoriaMetrics** | 8428 | Metrics storage |
| **MySQL** | 3306 | Database |
| **Redis** | 6379 | Cache |
| **Vault** | 8200 | Secrets |

## 🔧 Commands

```bash
# Start all services
make -f Makefile-all-in-one up

# View logs
make -f Makefile-all-in-one logs

# Check health
make -f Makefile-all-in-one health

# Stop everything
make -f Makefile-all-in-one down

# Shell into container
make -f Makefile-all-in-one shell-raxus

# Test alerts
make -f Makefile-all-in-one test-alert
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           RAXUS ALL-IN-ONE              │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   Frontend  │  │   7 Microservices│   │
│  │   Next.js   │  │   (FastAPI)     │   │
│  │    :3000    │  │  :8000-8006     │   │
│  └─────────────┘  └─────────────────┘   │
│  ┌─────────────────────────────────────┐│
│  │         Celery Worker               ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

## 🌐 Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **RAXUS UI** | http://localhost:3000 | admin / password |
| **API Docs** | http://localhost:8000/docs | — |
| **Grafana** | http://localhost:3001 | admin / admin |
| **VictoriaMetrics** | http://localhost:8428 | — |
| **Vault** | http://localhost:8200 | Token dans .env |

## 🚀 Benefits

✅ **Single container** - Easy deployment  
✅ **All services** - Complete RAXUS platform  
✅ **Fast startup** - Optimized multi-stage build  
✅ **Health checks** - Automatic monitoring  
✅ **Environment ready** - Pre-configured  

## 📦 vs Multi-Container

| Feature | All-in-One | Multi-Container |
|---------|------------|-----------------|
| **Setup** | 1 command | Multiple services |
| **Memory** | Shared | Isolated |
| **Scaling** | Vertical | Horizontal |
| **Debug** | One container | Service-specific |
| **Production** | Small/medium | Large scale |

## 🔍 Troubleshooting

```bash
# Check all services
make -f Makefile-all-in-one health

# View detailed logs
make -f Makefile-all-in-one logs-raxus

# Restart everything
make -f Makefile-all-in-one down
make -f Makefile-all-in-one up

# Reset database
make -f Makefile-all-in-one reset-db
```

## 🐳 Docker Details

The all-in-one Dockerfile uses:
- **Multi-stage builds** for optimization
- **Alpine Linux** for small size
- **Parallel service startup** 
- **Built-in health checks**
- **Environment variables** configuration

## 📝 Migration from Multi-Container

```bash
# Stop existing services
make down

# Start all-in-one version
make -f Makefile-all-in-one up

# Data is preserved in Docker volumes
```

---

**Ready in ~2 minutes** 🚀
