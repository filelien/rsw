# 🚀 Guide Complet - Déployer RAXUS sur Render

## 📋 Prérequis

1. **Compte Render** (gratuit ou payant)
2. **Compte GitHub** avec le repo `filelien/rsw`
3. **Code pushé** sur GitHub (déjà fait ✅)

---

## 🎯 Étape 1: Connexion GitHub à Render

### 1.1 Allez sur Render
```
https://render.com
```

### 1.2 Créez un compte ou connectez-vous
- **Sign up** si nouveau compte
- **Log in** avec GitHub/Gmail

### 1.3 Autorisez GitHub
- Cliquez **"Connect GitHub"**
- Autorisez l'accès à vos repositories
- Sélectionnez `filelien/rsw`

---

## 🎯 Étape 2: Déploiement avec Blueprint

### 2.1 Créez un Blueprint
1. Dans le dashboard Render, cliquez **"New Blueprint"**
2. Sélectionnez le repository `filelien/rsw`
3. Render détectera automatiquement `render-simple.yaml`

### 2.2 Configuration du Blueprint
```yaml
# Render détecte automatiquement ces services:
- Frontend (Next.js)
- API Gateway (FastAPI)
- Base de données PostgreSQL
```

### 2.3 Variables d'environnement
Render configurera automatiquement:
- `DATABASE_URL` pour PostgreSQL
- `SECRET_KEY` généré
- URLs des services

---

## 🎯 Étape 3: Lancement du déploiement

### 3.1 Cliquez "Deploy"
- Bouton **"Create Blueprint"** puis **"Deploy"**
- Le build commence (5-10 minutes)

### 3.2 Suivez le déploiement
```
✅ Build en cours...
✅ Services créés...
✅ Base de données initialisée...
✅ Frontend déployé...
✅ API déployée...
```

---

## 🎯 Étape 4: Accès à l'application

### 4.1 URLs de production
| Service | URL |
|---------|-----|
| **Frontend** | `https://raxus.onrender.com` |
| **API** | `https://raxus-api.onrender.com` |
| **API Docs** | `https://raxus-api.onrender.com/docs` |

### 4.2 Testez l'application
1. Ouvrez `https://raxus.onrender.com`
2. Vérifiez que l'UI charge
3. Testez `https://raxus-api.onrender.com/docs`

---

## 🔧 Étape 5: Configuration Post-Déploiement

### 5.1 Variables d'environnement additionnelles
Dans le dashboard Render → Service → Environment:

```bash
# Pour le Frontend
NEXT_PUBLIC_API_URL=https://raxus-api.onrender.com
NEXTAUTH_URL=https://raxus.onrender.com

# Pour l'API
ENVIRONMENT=production
SMTP_HOST=smtp.gmail.com  # si notifications email
```

### 5.2 Domaines personnalisés (optionnel)
1. **Settings** → **Custom Domains**
2. Ajoutez votre domaine
3. Configurez DNS

---

## 🛠️ Étape 6: Dépannage

### 6.1 Si le build échoue
```bash
# Vérifiez les logs dans Render dashboard
# Common errors:
- Dockerfile invalide
- Port incorrect (doit être 10000+)
- Variables manquantes
```

### 6.2 Si l'API ne répond pas
```bash
# Vérifiez:
1. Health check: https://raxus-api.onrender.com/health
2. Logs dans Render dashboard
3. Variables d'environnement
```

### 6.3 Si le frontend ne charge pas
```bash
# Vérifiez:
1. Build logs du frontend
2. NEXT_PUBLIC_API_URL correct
3. NEXTAUTH_SECRET configuré
```

---

## 📊 Monitoring

### Dashboard Render
- **Logs** en temps réel
- **Metrics** d'utilisation
- **Health checks** automatiques
- **Alertes** par email

### Commandes utiles
```bash
# Redémarrer un service
render restart raxus-api

# Voir les logs
render logs raxus-frontend

# Vérifier le statut
render ps
```

---

## 🎉 Résultat Final

Après 5-10 minutes, vous aurez:

✅ **Application complète** déployée  
✅ **Base de données** PostgreSQL  
✅ **API REST** avec documentation  
✅ **Frontend React** fonctionnel  
✅ **HTTPS** automatique  
✅ **Monitoring** intégré  

---

## 🚀 Prochaines Étapes

1. **Testez toutes les fonctionnalités**
2. **Configurez les notifications**
3. **Ajoutez votre domaine**
4. **Configurez le monitoring**

---

## 💡 Tips

- **Plan gratuit**: Services endormis après 15min
- **Wake-up**: Utilisez UptimeRobot pour éviter l'endormissement
- **Scaling**: Upgrade vers plan payant pour plus de ressources
- **Backups**: Render backup automatique la base de données

---

**Votre RAXUS est maintenant en production ! 🎯**
