# 🚀 Déploiement RAXUS sur Render

## 📋 Étapes de déploiement

### 1. Prérequis
- Compte Render (gratuit ou payant)
- Repository GitHub avec le code
- Tous les Dockerfiles individuels prêts

### 2. Configuration Render

#### Option A: Via render.yaml (recommandé)
1. Push le fichier `render.yaml` à la racine du projet
2. Connectez votre compte GitHub à Render
3. Créez un "New Blueprint" depuis le dashboard Render
4. Sélectionnez votre repository GitHub
5. Render détectera automatiquement `render.yaml`

#### Option B: Manuellement
1. Créez chaque service un par un via le dashboard Render

### 3. Services à déployer

| Service | Type | URL |
|---------|------|-----|
| Frontend | Web Service | `raxus-frontend.onrender.com` |
| API Gateway | Web Service | `raxus-api.onrender.com` |
| MySQL | Private Service | `raxus-db` |
| Redis | Redis | `raxus-redis` |
| Alertmanager | Web Service | `raxus-alertmanager.onrender.com` |
| Inventory | Web Service | `raxus-inventory.onrender.com` |
| Notifier | Web Service | `raxus-notifier.onrender.com` |
| TaskManager | Web Service | `raxus-taskmanager.onrender.com` |
| SLO Engine | Web Service | `raxus-slo-engine.onrender.com` |
| Rules Engine | Web Service | `raxus-rules-engine.onrender.com` |

### 4. Variables d'environnement

Dans le dashboard Render, configurez ces variables:

#### Pour le Frontend:
```
NEXT_PUBLIC_API_URL=https://raxus-api.onrender.com
NEXT_PUBLIC_WS_URL=wss://raxus-api.onrender.com
NEXTAUTH_SECRET=votre_secret_ici
NEXTAUTH_URL=https://raxus-frontend.onrender.com
```

#### Pour l'API Gateway:
```
DATABASE_URL=mysql://raxus:password@raxus-db:3306/raxus
REDIS_URL=redis://raxus-redis:6379
SECRET_KEY=votre_secret_ici
ENVIRONMENT=production
```

#### Pour les autres services:
```
DATABASE_URL=mysql://raxus:password@raxus-db:3306/raxus
REDIS_URL=redis://raxus-redis:6379
```

### 5. Dépannage

#### Erreur de build Docker:
- Vérifiez que chaque Dockerfile est valide
- Assurez-vous que les ports sont corrects (Render utilise le port 10000+)
- Vérifiez les chemins des fichiers

#### Erreur de connexion base de données:
- Vérifiez que le service MySQL est démarré
- Confirmez les variables d'environnement DATABASE_URL
- Assurez-vous que les services sont dans le même VPC

#### Erreur Redis:
- Vérifiez que le service Redis est actif
- Confirmez les URLs de connexion

### 6. Monitoring

Une fois déployé:
- Frontend: https://raxus-frontend.onrender.com
- API Docs: https://raxus-api.onrender.com/docs
- Logs disponibles dans le dashboard Render

### 7. Commandes utiles

```bash
# Vérifier les logs d'un service
render logs raxus-frontend

# Redémarrer un service
render restart raxus-api

# Vérifier le statut
render ps
```

### 8. Limites du plan gratuit

- 750 heures/build par mois
- 512MB RAM par service
- Pas de custom domains
- Services endormis après 15min d'inactivité

### 9. Optimisations

Pour le plan gratuit:
- Utilisez des images Docker légères
- Limitez les ressources consommées
- Implémentez des wake-up hooks
- Considérez Render Cron pour éviter l'endormissement

---

## 🎯 Déploiement rapide

1. **Push sur GitHub** avec `render.yaml`
2. **Connectez Render** à GitHub
3. **Create Blueprint** → sélectionnez repo
4. **Deploy** 🚀

Le déploiement prend 5-10 minutes pour tous les services.
