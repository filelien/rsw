# 🚀 Déploiement RAXUS sur Render - Guide Complet Étape par Étape

## 📋 Prérequis Vérifiés ✅

Avant de commencer, vérifions que tout est prêt:

### ✅ **Repository GitHub Prêt**
- URL: https://github.com/filelien/rsw
- `render-simple.yaml` présent et configuré
- Tous les fichiers corrigés (ports, PostgreSQL, dépendances)

### ✅ **Configuration Render Optimisée**
- Frontend: Next.js avec port correct
- API: FastAPI sur port 10000+
- Base: PostgreSQL native
- Health checks configurés

---

## 🎯 ÉTAPE 1: Connexion à Render (2 minutes)

### 1.1 Créer/Connecter compte Render
```bash
# Allez sur
https://render.com
```

1. **Sign up** (si nouveau compte)
2. **Continue with GitHub** 
3. **Autorisez** l'accès à vos repositories
4. **Sélectionnez** `filelien/rsw` dans la liste

### 1.2 Vérification
- ✅ Repository visible dans dashboard Render
- ✅ `render-simple.yaml` détecté automatiquement

---

## 🔧 ÉTAPE 2: Configuration Blueprint (3 minutes)

### 2.1 Créer le Blueprint
1. Dans dashboard Render, cliquez **"New +"**
2. Sélectionnez **"Blueprint"**
3. Cherchez et sélectionnez `filelien/rsw`

### 2.2 Render Analyse Automatiquement
Render montrera:
```
🔍 Services détectés:
✅ Web Service: raxus (Frontend Next.js)
   - Dockerfile: ./frontend/Dockerfile
   - Port: 3000 (automatique)
   - Health check: /

✅ Web Service: raxus-api (API FastAPI)
   - Dockerfile: ./Dockerfile-render-api
   - Port: 10000 (Render compatible)
   - Health check: /health

✅ PostgreSQL: raxus-db (Base de données)
   - Plan: Free
   - Backup automatique
```

### 2.3 Variables d'Environnement
Render configure automatiquement:
```bash
# Base de données
DATABASE_URL=postgresql://raxus:xxx@xxx:5432/raxus

# Sécurité
SECRET_KEY=xxx (généré automatiquement)
NEXTAUTH_SECRET=xxx (généré automatiquement)

# URLs de service
NEXT_PUBLIC_API_URL=https://raxus.onrender.com
NEXTAUTH_URL=https://raxus.onrender.com
```

---

## 🚀 ÉTAPE 3: Lancement du Déploiement (5-10 minutes)

### 3.1 Démarrer le Blueprint
1. Vérifiez la configuration affichée
2. Cliquez **"Create Blueprint"**
3. Cliquez **"Deploy"**

### 3.2 Suivre la Progression
Render montrera en temps réel:
```
🔍 Analyzing repository...
📦 Building Docker images...
   → Frontend: Node.js build en cours...
   → API: Python dependencies install...
🚀 Creating services...
   → PostgreSQL database initializing...
   → Frontend container starting...
   → API container starting...
⏳ Deploying services...
   → Health checks en cours...
✅ Deployment complete!
```

### 3.3 Pendant le Déploiement
- **NE PAS FERMER** la page
- Le build prend 5-10 minutes
- Vous pouvez voir les logs en direct
- En cas d'erreur, Render montrera les logs détaillés

---

## ✅ ÉTAPE 4: Vérification Post-Déploiement (2 minutes)

### 4.1 URLs de Production
Une fois le déploiement terminé, Render affichera:
```
✅ raxus - https://raxus.onrender.com
✅ raxus-api - https://raxus-api.onrender.com  
✅ raxus-db - PostgreSQL database
```

### 4.2 Tests de Validation
Ouvrez dans votre navigateur:

#### **Test 1: Frontend**
```bash
https://raxus.onrender.com
# Expected: Interface RAXUS qui charge
# Vérifiez: Dashboard, menu de navigation
```

#### **Test 2: API Documentation**
```bash
https://raxus-api.onrender.com/docs
# Expected: Swagger UI avec tous les endpoints
# Testez: GET /health → {"status": "healthy"}
```

#### **Test 3: Health Check**
```bash
curl https://raxus-api.onrender.com/health
# Expected: 
{
  "status": "healthy",
  "services": ["gateway", "alertmanager", "inventory", "notifier", "taskmanager", "slo-engine", "rules-engine"]
}
```

---

## 🛠️ ÉTAPE 5: Configuration Additionnelle (Optionnel)

### 5.1 Variables d'Environnement Supplémentaires
Dans Render Dashboard → Service → Environment:

```bash
# Pour les notifications email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre@email.com
SMTP_PASSWORD=votre_app_password

# Pour Slack (optionnel)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

### 5.2 Domaine Personnalisé (Optionnel)
1. **Settings** → **Custom Domains**
2. Ajoutez votre domaine: `raxus.votre-domaine.com`
3. Configurez DNS selon instructions Render

---

## 📊 ÉTAPE 6: Monitoring et Maintenance

### 6.1 Dashboard Render
- **Metrics**: CPU, mémoire, réseau en temps réel
- **Logs**: Logs de tous les services consultables
- **Health Checks**: Vérification automatique toutes les 30s
- **Events**: Historique des déploiements et redémarrages

### 6.2 Commandes Utiles (via Render CLI)
```bash
# Si vous avez Render CLI installé
render logs raxus-api          # Voir logs API
render restart raxus-api       # Redémarrer API
render ps                      # Voir statut services
```

---

## 🎯 Résultat Final Attendu

### **URLs Disponibles**
| Service | URL | Fonction |
|---------|-----|----------|
| **Application** | https://raxus.onrender.com | Interface utilisateur complète |
| **API Docs** | https://raxus-api.onrender.com/docs | Documentation Swagger |
| **API Health** | https://raxus-api.onrender.com/health | Vérification santé |

### **Fonctionnalités Opérationnelles**
- ✅ **Dashboard** temps réel avec alertes
- ✅ **Inventaire** des serveurs et composants  
- ✅ **Gestion des alertes** avec ack/resolution
- ✅ **Automatisation** avec scripts et schedules
- ✅ **SLO monitoring** avec probes
- ✅ **Notifications** email/webhook/Slack
- ✅ **Tickets ITSM** intégrés

### **Performance**
- **Démarrage**: 5-10 minutes
- **Uptime**: 99.9% (plan gratuit)
- **Scaling**: Automatique selon besoins
- **Backup**: Quotidien base de données

---

## 🚨 Dépannage Rapide

### **Si le build échoue:**
1. **Vérifiez les logs** dans Render dashboard
2. **Causes communes**:
   - Erreur Dockerfile (déjà corrigé)
   - Dépendance manquante (déjà corrigé)
   - Port incorrect (déjà corrigé)

### **Si l'API ne répond pas:**
```bash
# Vérifier health check
curl https://raxus-api.onrender.com/health

# Vérifier logs dans dashboard Render
# Redémarrer le service si nécessaire
```

### **Si le frontend ne charge pas:**
1. Vérifiez que l'API fonctionne
2. Vérifiez NEXT_PUBLIC_API_URL dans Environment
3. Clear cache navigateur

---

## 🎉 Succès !

Votre RAXUS est maintenant en production sur Render !

### **Prochaines Étapes Optionnelles:**
1. **Configurer les notifications** email/Slack
2. **Ajouter votre domaine personnalisé**
3. **Importer vos données d'inventaire**
4. **Créer vos premières règles d'automatisation**
5. **Configurer les SLO pour vos services critiques**

---

## 📞 Support

- **Documentation complète**: `DEPLOYMENT-GUIDE.md`
- **Guide étape par étape**: `ETAPE-PAR-ETAPE.md`
- **Rapport d'analyse**: `CODE-ANALYSIS-REPORT.md`
- **Fonctionnement**: `APPLICATION-FUNCTIONING.md`

---

**🚀 Votre plateforme RAXUS est maintenant déployée et opérationnelle !**

Temps total estimé: **15-20 minutes** maximum ✨
