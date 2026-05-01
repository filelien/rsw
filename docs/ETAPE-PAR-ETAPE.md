# 🎯 ÉTAPE PAR ÉTAPE - Déploiement RAXUS sur Render

## 📋 CE QUE VOUS AVEZ BESOIN

✅ Repository GitHub: `filelien/rsw` (déjà fait)  
✅ Fichier `render-simple.yaml` (déjà configuré)  
✅ Compte Render (à créer)  

---

## 🚀 ÉTAPE 1: INSCRIPTION RENDER (2 minutes)

### 1.1 Allez sur render.com
```
https://render.com
```

### 1.2 Créez votre compte
- **Sign up** (en haut à droite)
- Choisissez **"Continue with GitHub"**
- Autorisez Render à accéder à vos repos GitHub

### 1.3 Vérifiez l'email
- Ouvrez l'email de Render
- Cliquez sur le lien de vérification

---

## 🔗 ÉTAPE 2: CONNECTER LE REPOSITORY (3 minutes)

### 2.1 Tableau de bord Render
- Après connexion, vous êtes sur le dashboard
- Cliquez sur **"New +"** (en haut à gauche)

### 2.2 Choisissez "Blueprint"
- Dans le menu, cliquez **"Blueprint"**
- Blueprint = déploiement automatique depuis GitHub

### 2.3 Sélectionnez le repository
- Cherchez `filelien/rsw` dans la liste
- Cliquez **"Connect"**

### 2.4 Render détecte automatiquement
Render verra `render-simple.yaml` et montrera:
```
✅ 3 services détectés:
- Web Service: raxus (Frontend)
- Web Service: raxus-api (API)
- PostgreSQL: raxus-db (Database)
```

---

## ⚙️ ÉTAPE 3: CONFIGURATION (2 minutes)

### 3.1 Vérifiez la configuration
Render montrera la configuration automatique:

**Service Frontend:**
- Name: `raxus`
- Type: `Web Service`
- Dockerfile: `./frontend/Dockerfile`
- Domain: `raxus.onrender.com`

**Service API:**
- Name: `raxus-api`
- Type: `Web Service`
- Dockerfile: `./Dockerfile-render-api`
- Domain: `raxus-api.onrender.com`

**Database:**
- Name: `raxus-db`
- Type: `PostgreSQL`
- Plan: Free

### 3.2 Variables d'environnement
Render configure automatiquement:
```bash
DATABASE_URL=postgresql://... (généré)
SECRET_KEY=... (généré)
NEXTAUTH_SECRET=... (généré)
```

---

## 🚀 ÉTAPE 4: DÉPLOIEMENT (5-10 minutes)

### 4.1 Lancez le déploiement
- Cliquez **"Create Blueprint"** (bouton en bas)
- Puis **"Deploy"**

### 4.2 Suivez la progression
Vous verrez:
```
🔍 Analyzing repository...
📦 Building Docker images...
🚀 Creating services...
⏳ Deploying frontend...
⏳ Deploying API...
🗄️ Setting up database...
✅ Deployment complete!
```

### 4.3 Pendant le déploiement
- **Ne fermez pas** la page
- Le build prend 5-10 minutes
- Vous pouvez voir les logs en temps réel

---

## ✅ ÉTAPE 5: VÉRIFICATION (2 minutes)

### 5.1 Une fois le déploiement terminé
Render montrera:
```
✅ raxus - https://raxus.onrender.com
✅ raxus-api - https://raxus-api.onrender.com
✅ raxus-db - PostgreSQL database
```

### 5.2 Testez les URLs
Ouvrez dans votre navigateur:

1. **Frontend**: `https://raxus.onrender.com`
   - Devrait afficher l'interface RAXUS
   - Vérifiez que la page charge

2. **API Docs**: `https://raxus-api.onrender.com/docs`
   - Devrait afficher la documentation Swagger
   - Testez l'endpoint `/health`

3. **Health Check**: `https://raxus-api.onrender.com/health`
   - Devrait retourner `{"status": "healthy"}`

---

## 🛠️ ÉTAPE 6: DÉPANNAGE (si nécessaire)

### 6.1 Si un service ne démarre pas
1. **Allez sur le dashboard Render**
2. **Cliquez sur le service** (ex: raxus-api)
3. **Onglet "Logs"** pour voir les erreurs
4. **Onglet "Events"** pour les événements

### 6.2 Erreurs communes
```
❌ "Port not available"
→ Solution: Render utilise le port 10000+, pas 3000/8000

❌ "Database connection failed"
→ Solution: Vérifiez DATABASE_URL dans Environment

❌ "Build failed"
→ Solution: Vérifiez le Dockerfile
```

### 6.3 Redémarrer un service
- Dashboard → Service → **"Manual Deploy"**
- Ou **"Restart"** pour redémarrer

---

## 🎉 ÉTAPE 7: UTILISATION

### 7.1 Votre RAXUS est en production!
- **URL principale**: `https://raxus.onrender.com`
- **API**: `https://raxus-api.onrender.com`
- **Documentation**: `https://raxus-api.onrender.com/docs`

### 7.2 Fonctionnalités disponibles
- ✅ Dashboard de monitoring
- ✅ Gestion des alertes
- ✅ Inventaire des serveurs
- ✅ Automatisation des tâches
- ✅ SLO monitoring

---

## 📊 ÉTAPE 8: MONITORING

### 8.1 Dans le dashboard Render
- **Metrics**: CPU, mémoire, réseau
- **Logs**: En temps réel
- **Health checks**: Automatiques
- **Alertes**: Par email

### 8.2 Plan gratuit limitations
- **Endormissement**: Après 15min d'inactivité
- **Ressources**: 512MB RAM par service
- **Build**: 750 heures/mois

---

## 🚀 RÉSUMÉ RAPIDE

1. **Inscription** → render.com → GitHub
2. **New Blueprint** → Sélectionnez `filelien/rsw`
3. **Deploy** → Attendez 5-10 minutes
4. **Testez** → `https://raxus.onrender.com`
5. **🎉 C'est fini !**

---

## 💡 CONSEILS PRO

- **UptimeRobot**: Configurez pour éviter l'endormissement gratuit
- **Custom domain**: Ajoutez votre domaine dans Settings
- **Backups**: Render backup automatique la DB
- **Scaling**: Upgrade vers plan payant si besoin

---

**🎯 Votre RAXUS est maintenant déployé et accessible !**

Temps total: **15-20 minutes** maximum 🚀
