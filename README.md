# rsw

# RAXUS — Unified IT Operations Platform

> Observabilité · Automatisation · Sécurité · Analytics · SLO · ITSM

RAXUS est une plateforme complète de gestion des opérations IT inspirée des meilleures fonctionnalités de Splunk, Datadog, Oracle OEM, IBM QRadar, Dynatrace, ServiceNow, et plus encore.

---

## 🚀 Démarrage rapide

### Prérequis
- Docker Desktop ou Docker Engine 24+
- Docker Compose v2+
- 4 GB RAM minimum (8 GB recommandé)
- WSL2 (Windows) ou Linux/macOS

### Installation

```bash
# 1. Cloner ou décompresser le projet
cd raxus

# 2. Copier le fichier d'environnement
cp .env.example .env

# 3. Éditer les variables (optionnel pour le dev)
nano .env

# 4. Démarrer tout
make up
# ou
docker compose up -d --build
```

### Accès

| Service | URL | Credentials |
|---------|-----|-------------|
| **RAXUS UI** | http://localhost:3000 | admin / password |
| **API Docs** | http://localhost:8000/docs | — |
| **Grafana** | http://localhost:3001 | admin / admin |
| **VictoriaMetrics** | http://localhost:8428 | — |
| **Vault** | http://localhost:8200 | Token dans .env |

---

## 🏗️ Architecture

```
raxus/
├── services/
│   ├── gateway/        ← API Gateway FastAPI (port 8000)
│   ├── alertmanager/   ← Ingestion & gestion alertes (port 8001)
│   ├── inventory/      ← Datacenters, servers, composants (port 8002)
│   ├── notifier/       ← Email, Webhook, Slack (port 8003)
│   ├── taskmanager/    ← Scripts, schedules, Celery (port 8004)
│   ├── slo-engine/     ← SLO, SLI, probes HTTP (port 8005)
│   └── rules-engine/   ← Évaluateur de règles (port 8006)
├── frontend/           ← Next.js 14 + React 18 (port 3000)
├── infra/
│   ├── mysql/          ← Schema SQL complet
│   ├── nginx/          ← Reverse proxy
│   ├── grafana/        ← Dashboards & datasources
│   └── loki/           ← Centralisation des logs
└── docker-compose.yml
```

---

## 📡 API — Exemples d'utilisation

### Authentification
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Créer une clé API
curl -X POST "http://localhost:8000/api/v1/auth/api-keys?name=monitoring" \
  -H "Authorization: Bearer <token>"
```

### Ingestion d'alertes

```bash
# Format Prometheus Alertmanager
curl -X POST http://localhost:8000/api/v1/alerts/ingest/prometheus \
  -H "Content-Type: application/json" \
  -d '{
    "version": "4",
    "status": "firing",
    "alerts": [{
      "status": "firing",
      "labels": {
        "alertname": "HighCPU",
        "severity": "critical",
        "instance": "web-01",
        "job": "node_exporter"
      },
      "annotations": {
        "summary": "CPU > 95% depuis 5min",
        "description": "Serveur web-01 surchargé"
      }
    }]
  }'

# Format Webhook générique
curl -X POST http://localhost:8000/api/v1/alerts/ingest/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [{
      "name": "DiskFull",
      "severity": "major",
      "instance": "db-01",
      "summary": "Disque /data à 95%",
      "value": 95,
      "threshold": 90
    }]
  }'
```

### Inventory
```bash
# Créer un datacenter
curl -X POST http://localhost:8000/api/v1/inventory/datacenters \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"DC-Paris-01","location":"Paris, France"}'

# Créer un serveur
curl -X POST http://localhost:8000/api/v1/inventory/servers \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"environment_id":"<env-id>","hostname":"web-01","ip_address":"192.168.1.10","os_type":"Ubuntu","cpu_cores":8,"ram_gb":32}'
```

### Règles d'automatisation
```bash
curl -X POST http://localhost:8000/api/v1/rules \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Critical Alert → Slack",
    "conditions": {
      "match": "all",
      "rules": [{"field":"severity","operator":"eq","value":"critical"}]
    },
    "actions": {
      "list": [{"type":"webhook","url":"https://hooks.slack.com/..."}]
    },
    "priority": 10
  }'
```

### SLO
```bash
curl -X POST http://localhost:8000/api/v1/slo \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"API Availability","service_name":"api-gateway","sli_type":"availability","target_percent":99.9,"window_days":30}'
```

---

## 🔧 Commandes utiles

```bash
make up          # Démarrer tout
make down        # Arrêter tout
make logs        # Voir les logs
make health      # Checker tous les services
make test-alert  # Envoyer une alerte de test
make shell-mysql # Shell MySQL
make clean       # Tout supprimer (données incluses)
```

---

## 🔗 Intégration Prometheus

Ajouter dans votre `prometheus.yml` :

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

# Ou pointer directement vers RAXUS :
# webhook_url: 'http://raxus:8000/api/v1/alerts/ingest/prometheus'
```

---

## 📊 Fonctionnalités

| Module | Fonctionnalités |
|--------|----------------|
| **Alertes** | Ingestion webhook/Prometheus, déduplication, fingerprinting, ACK, résolution, suppression windows |
| **Inventaire** | Datacenters, environments, serveurs, composants, tags, metadata |
| **Tasks** | Scripts Bash/Python/Ansible, exécution async, Celery, schedules cron, historique |
| **SLO** | SLO targets, SLI, error budget, probes HTTP/TCP/ICMP, résultats temps réel |
| **Règles** | Évaluateur conditions AND/OR, actions (notify/task/webhook), priorités |
| **Notifications** | Email (SMTP), Webhook, Slack, Teams, PagerDuty, templates HTML |
| **Tickets** | ITSM complet, priorités, statuts, commentaires, lien avec alertes |
| **Dashboard** | Vue temps réel, charts, top issues, timeline 7j, WebSocket |
| **Auth** | JWT, refresh tokens, API keys, RBAC (admin/operator/viewer) |
| **Logs** | Centralisation Loki, Grafana, VictoriaMetrics |

---

## 🛡️ Sécurité

- JWT tokens avec expiration configurable
- API Keys hashées SHA-256
- RBAC : admin / operator / viewer
- Secrets via HashiCorp Vault
- Rate limiting (configurable dans gateway)
- CORS configuré par environnement

---

## 📝 Crédits

RAXUS est inspiré par : Splunk, Datadog, Oracle OEM, IBM QRadar, Dynatrace, Microsoft Sentinel, Elastic, ManageEngine, SolarWinds, ServiceNow.

**Version** : 1.0.0 | **License** : MIT
