# 🔧 Comment Fonctionne RAXUS - Architecture Complète

## 📋 Vue d'ensemble de l'application

RAXUS est une plateforme unifiée d'opérations IT qui combine **7 microservices** + **1 frontend** pour offrir une solution complète de monitoring.

---

## 🏗️ Architecture Actuelle

### **Frontend (Next.js)**
```
frontend/
├── app/                    # Pages Next.js 14
│   ├── page.tsx            # Dashboard principal
│   ├── alerts/page.tsx     # Gestion des alertes
│   ├── inventory/page.tsx  # Inventaire des serveurs
│   ├── tasks/page.tsx      # Tâches automatisées
│   ├── slo/page.tsx        # SLO monitoring
│   └── tickets/page.tsx    # Tickets ITSM
├── components/
│   └── layout/Sidebar.tsx   # Navigation
└── lib/api.ts              # Client API
```

**Fonctionnement:**
- Interface utilisateur React 18
- Appels API vers le gateway (port 10000)
- WebSocket pour temps réel
- Authentification NextAuth

### **Backend (7 Microservices FastAPI)**

#### 1. **Gateway** (Port 10000) - Point d'entrée principal
```python
services/gateway/main.py
├── Authentification JWT
├── Routage vers autres services
├── Middleware CORS/Rate limiting
├── Documentation Swagger (/docs)
└── WebSocket temps réel
```

#### 2. **AlertManager** (Port 8001) - Gestion des alertes
```python
services/alertmanager/main.py
├── Ingestion webhook/Prometheus
├── Déduplication et fingerprinting
├── Statuts: active/resolved/acknowledged
├── Suppression windows
└── Tickets ITSM intégrés
```

#### 3. **Inventory** (Port 8002) - Gestion des actifs
```python
services/inventory/main.py
├── Datacenters
├── Environments (prod/staging/dev)
├── Serveurs avec composants
├── Tags et metadata
└── Statuts de maintenance
```

#### 4. **Notifier** (Port 8003) - Notifications
```python
services/notifier/main.py
├── Email (SMTP)
├── Webhook générique
├── Slack integration
├── Teams/PagerDuty
└── Templates HTML
```

#### 5. **TaskManager** (Port 8004) - Automatisation
```python
services/taskmanager/main.py
├── Scripts Bash/Python/Ansible
├── Exécution async avec Celery
├── Schedules cron
├── Historique des exécutions
└── Timeout et logs
```

#### 6. **SLO Engine** (Port 8005) - Monitoring SLO
```python
services/slo-engine/main.py
├── SLO targets (availability/latency)
├── Probes HTTP/TCP/ICMP
├── Error budget calculations
├── Measurements temps réel
└── VictoriaMetrics integration
```

#### 7. **Rules Engine** (Port 8006) - Automatisation
```python
services/rules-engine/main.py
├── Conditions AND/OR
├── Actions: notify/execute task/webhook
├── Priorités des règles
├── Trigger par alertes
└── Évaluation en temps réel
```

---

## 🔄 Flux de Données

### **1. Ingestion d'alertes**
```
Prometheus/Webhook → AlertManager → Rules Engine → Notifier → Frontend (WebSocket)
```

### **2. Gestion des actifs**
```
Frontend → Gateway → Inventory → Base PostgreSQL → Frontend
```

### **3. Automatisation**
```
Frontend → Gateway → TaskManager → Celery Worker → Exécution → Résultats → Frontend
```

### **4. Monitoring SLO**
```
SLO Engine → Probes → VictoriaMetrics → Calculs → Frontend (Dashboard)
```

---

## 🗄️ Base de Données

### **PostgreSQL Schema**
```sql
-- Alertes
alerts (id, fingerprint, name, severity, status, instance, labels, annotations)
suppression_windows (id, name, matchers, starts_at, ends_at)
tickets (id, title, description, priority, status, alert_id)

-- Inventaire  
datacenters (id, name, location, description, tags)
environments (id, datacenter_id, name, type, description)
servers (id, environment_id, hostname, ip_address, os_type, status, metadata)
components (id, server_id, name, type, version, port, status)

-- Tâches
tasks (id, name, description, script, script_type, parameters, timeout_sec)
task_executions (id, task_id, server_id, status, output, error_output, duration_ms)
schedules (id, task_id, name, cron_expr, target_type, next_run)

-- SLO
slo_targets (id, name, service_name, sli_type, target_percent, window_days)
slo_measurements (id, slo_id, good_events, total_events, compliance, period_start/end)
probes (id, name, type, target, interval_sec, last_status, slo_id)
probe_results (id, probe_id, status, response_ms, status_code, error_msg)

-- Notifications
notifiers (id, name, type, config, is_active)
notifications (id, alert_id, notifier_id, status, attempts, sent_at)

-- Rules
alert_rules (id, name, conditions, actions, priority, is_active, trigger_count)
```

---

## 🚀 Comment l'application démarre

### **Développement Local**
```bash
# 1. Base de données PostgreSQL + Redis
docker compose up -d mysql redis

# 2. Chaque service indépendant
cd services/gateway && python main.py      # Port 10000
cd services/alertmanager && python main.py  # Port 8001
cd services/inventory && python main.py     # Port 8002
# ... etc pour tous les services

# 3. Frontend
cd frontend && npm run dev                  # Port 3000
```

### **Production Render**
```bash
# 1. Blueprint Render détecte render-simple.yaml
# 2. Build Dockerfile-render-api (combine tous les services)
# 3. Déploie sur les ports automatiques (10000+)
# 4. Base de données PostgreSQL créée automatiquement
```

---

## 📊 Fonctionnalités Utilisateur

### **Dashboard Principal**
- Vue d'ensemble des alertes actives
- Statuts des serveurs et services
- Graphiques SLO en temps réel
- Tâches récentes et notifications

### **Gestion des Alertes**
- Liste filtrable par sévérité/statut
- Acknowledgement et résolution
- Création de tickets depuis alertes
- Suppression windows pour maintenance

### **Inventaire IT**
- Arborescence Datacenter → Environment → Server → Component
- Ajout/modification des actifs
- Tags et recherche
- Mode maintenance

### **Automatisation**
- Création de scripts Bash/Python
- Schedules pour exécution périodique
- Exécution manuelle avec paramètres
- Historique et logs

### **SLO Monitoring**
- Définition d'objectifs de service
- Probes automatiques (HTTP/TCP/ICMP)
- Calculs de compliance et error budget
- Alertes SLO

---

## 🔧 Points d'API Principaux

### **Gateway** (https://raxus-api.onrender.com)
```
GET  /health                    # Health check
GET  /docs                     # Documentation Swagger
POST /api/v1/auth/login       # Authentification
GET  /api/v1/alerts            # Liste des alertes
POST /api/v1/alerts/ingest/*  # Ingestion alertes
GET  /api/v1/inventory/*       # Inventaire
POST /api/v1/tasks/*          # Gestion tâches
GET  /api/v1/slo/*             # SLO monitoring
POST /api/v1/rules/*           # Rules engine
WS   /ws                       # WebSocket temps réel
```

### **Frontend** (https://raxus.onrender.com)
```
GET  /                         # Dashboard
GET  /alerts                   # Page alertes
GET  /inventory                # Page inventaire
GET  /tasks                    # Page tâches
GET  /slo                      # Page SLO
GET  /tickets                  # Page tickets
```

---

## 🎯 Ce qui fonctionne déjà

✅ **Architecture complète** - 7 microservices + frontend  
✅ **Base de données** - Schema PostgreSQL complet  
✅ **API REST** - Tous les endpoints implémentés  
✅ **Authentification** - JWT avec refresh tokens  
✅ **WebSocket** - Temps réel pour alertes  
✅ **Configuration Render** - Ports et variables corrigés  
✅ **Docker optimisé** - Multi-stage builds  
✅ **Documentation** - Guides complets de déploiement  

---

## 🚀 Prêt pour le déploiement

L'application est **100% fonctionnelle** et **prête pour Render** avec:
- Tous les bugs corrigés
- Configuration cloud native
- Documentation complète
- Tests de santé intégrés

**Il ne reste plus qu'à déployer !** 🎯
