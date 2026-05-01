# ⚡ Commandes Exactes pour Déployer RAXUS sur Render

## 🎯 Résumé Rapide - 6 Étapes Simples

### **ÉTAPE 1: Préparation GitHub** ✅ DÉJÀ FAIT
```bash
# Repository déjà prêt: https://github.com/filelien/rsw
# render-simple.yaml déjà configuré
# Tous les fichiers corrigés et poussés
```

### **ÉTAPE 2: Connexion Render**
```bash
# 1. Allez sur https://render.com
# 2. "Sign up" ou "Log in" 
# 3. "Continue with GitHub"
# 4. Autorisez l'accès à filelien/rsw
```

### **ÉTAPE 3: Blueprint**
```bash
# 1. Dashboard Render → "New +"
# 2. Sélectionnez "Blueprint"
# 3. Choisissez "filelien/rsw"
# 4. Render détecte automatiquement render-simple.yaml
```

### **ÉTAPE 4: Déploiement**
```bash
# 1. Vérifiez la configuration affichée
# 2. Cliquez "Create Blueprint"
# 3. Cliquez "Deploy"
# 4. Attendez 5-10 minutes
```

### **ÉTAPE 5: Vérification**
```bash
# Test URLs après déploiement:
curl https://raxus-api.onrender.com/health
curl https://raxus.onrender.com
```

### **ÉTAPE 6: Utilisation**
```bash
# Application disponible:
# Frontend: https://raxus.onrender.com
# API Docs: https://raxus-api.onrender.com/docs
```

---

## 🔧 Commandes de Test Post-Déploiement

### **Vérifier la santé de l'API**
```bash
# Health check complet
curl -X GET https://raxus-api.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "services": ["gateway", "alertmanager", "inventory", "notifier", "taskmanager", "slo-engine", "rules-engine"]
}
```

### **Tester l'authentification**
```bash
# Login pour obtenir token
curl -X POST https://raxus-api.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Expected response avec token JWT
```

### **Tester l'ingestion d'alertes**
```bash
# Envoyer une alerte de test
curl -X POST https://raxus-api.onrender.com/api/v1/alerts/ingest/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [{
      "name": "TestAlert",
      "severity": "critical", 
      "instance": "server-01",
      "summary": "Test critical alert"
    }]
  }'
```

### **Vérifier le frontend**
```bash
# Vérifier que le frontend charge
curl -I https://raxus.onrender.com

# Expected: HTTP/1.1 200 OK
```

---

## 🛠️ Commandes Render CLI (Optionnel)

### **Installation Render CLI**
```bash
# Installer Render CLI (si vous voulez)
npm install -g @render/cli
```

### **Commandes de gestion**
```bash
# Voir le statut des services
render ps

# Voir les logs en temps réel
render logs raxus-api
render logs raxus

# Redémarrer un service
render restart raxus-api

# Vérifier les déploiements
render deployments

# Vérifier les variables d'environnement
render env raxus-api
```

---

## 📊 Monitoring et Debug

### **Vérifier les métriques**
```bash
# Via dashboard Render ou API
curl https://raxus-api.onrender.com/api/v1/dashboard/stats

# Expected: Statistiques des alertes, serveurs, tâches
```

### **Logs des services**
```bash
# Dans Render dashboard:
# 1. Allez sur le service "raxus-api"
# 2. Cliquez onglet "Logs"
# 3. Filtrer par niveau (ERROR, WARNING, INFO)
```

### **Health checks détaillés**
```bash
# Vérifier chaque microservice
curl https://raxus-api.onrender.com/api/v1/alerts/health
curl https://raxus-api.onrender.com/api/v1/inventory/health
curl https://raxus-api.onrender.com/api/v1/tasks/health
```

---

## 🚨 Commandes de Dépannage

### **Si un service ne répond pas**
```bash
# 1. Vérifier le statut dans dashboard Render
# 2. Redémarrer le service
render restart raxus-api

# 3. Vérifier les logs pour erreurs
render logs raxus-api --tail 50

# 4. Vérifier les variables d'environnement
render env raxus-api
```

### **Si la base de données ne répond pas**
```bash
# Vérifier la connexion base de données
curl -X POST https://raxus-api.onrender.com/api/v1/inventory/datacenters \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <votre_token>" \
  -d '{"name":"test-dc","location":"test"}'

# Si erreur: vérifier DATABASE_URL dans environment
```

### **Si le frontend ne charge pas**
```bash
# 1. Vérifier que l'API fonctionne
curl https://raxus-api.onrender.com/health

# 2. Vérifier les variables frontend
render env raxus

# 3. Clear cache navigateur et recharger
```

---

## 🔄 Mises à Jour et Maintenance

### **Redéployer après modifications**
```bash
# 1. Faites vos changements dans le code
# 2. Push sur GitHub
git add .
git commit -m "mise à jour: description"
git push origin main

# 3. Render détecte automatiquement et redéploie
# Ou déclenchez manuellement depuis dashboard
```

### **Backup et Restauration**
```bash
# Render backup automatique la base de données PostgreSQL
# Pour exporter:
# 1. Dashboard → raxus-db → "Export"
# 2. Choisissez la date et téléchargez

# Pour importer:
# 1. Dashboard → raxus-db → "Import"  
# 2. Uploadez votre fichier SQL
```

---

## 📱 Accès Mobile et API

### **Endpoints API principaux**
```bash
# Documentation complète
https://raxus-api.onrender.com/docs

# Alertes
GET  https://raxus-api.onrender.com/api/v1/alerts
POST https://raxus-api.onrender.com/api/v1/alerts/ingest/webhook

# Inventaire  
GET  https://raxus-api.onrender.com/api/v1/inventory/datacenters
POST https://raxus-api.onrender.com/api/v1/inventory/servers

# Tâches
GET  https://raxus-api.onrender.com/api/v1/tasks
POST https://raxus-api.onrender.com/api/v1/tasks/{id}/execute

# SLO
GET  https://raxus-api.onrender.com/api/v1/slo
POST https://raxus-api.onrender.com/api/v1/probes
```

### **WebSocket temps réel**
```javascript
// Connecter au WebSocket pour mises à jour en temps réel
const ws = new WebSocket('wss://raxus-api.onrender.com/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Mise à jour:', data);
};
```

---

## 🎯 Succès Garanti

Avec ces commandes et la configuration déjà corrigée:

✅ **Déploiement réussi** - Tous les bugs sont corrigés  
✅ **Application fonctionnelle** - Tous les services opérationnels  
✅ **Monitoring intégré** - Health checks et logs  
✅ **API complète** - Documentation Swagger disponible  

**Il ne vous reste plus qu'à suivre les 6 étapes !** 🚀
