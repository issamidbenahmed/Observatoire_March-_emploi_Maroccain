# 🎯 Observatoire du Marché de l'Emploi IT au Maroc

Un système complet de scraping, d'analyse et de visualisation du marché de l'emploi technologique au Maroc. Ce projet permet de suivre en temps réel les tendances du marché, la répartition géographique des offres et l'évolution des compétences demandées.

## 📋 Aperçu du Projet

L'Observatoire collecte des données depuis plusieurs plateformes d'emploi (Rekrute, etc.), les traite pour extraire les technologies clés et les localisations, puis les présente via un dashboard interactif.

### Fonctionnalités Clés
- **Collecte Automatisée** : Scraper basé sur Playwright avec gestion intelligente des anti-scraping.
- **Analyse Géographique** : Carte interactive du Maroc affichant la densité des offres par ville.
- **Tendances Technologiques** : Visualisation des technologies les plus demandées (React, Python, Cloud, etc.).
- **Analyse Historique** : Suivi de l'évolution des offres dans le temps.
- **Export de Données** : Possibilité d'exporter les offres filtrées au format CSV.

## 🚀 Architecture Technique

### Backend
- **Framework** : Flask (Python)
- **Base de données** : MySQL
- **Scraping** : Playwright & Playwright-Stealth
- **Traitement** : Pandas, NumPy, Regex pour l'extraction de compétences
- **Planification** : Flask-APScheduler pour l'automatisation horaire

### Frontend
- **Framework** : React 19 avec Vite
- **Styling** : Tailwind CSS (Design Moderne)
- **Visualisation** : Recharts, React Simple Maps
- **Animations** : Framer Motion
- **Icônes** : Lucide React

## ⚙️ Installation et Configuration

### 1. Prérequis
- Python 3.9+
- Node.js 18+
- MySQL : XAMPP ...

### 2. Configuration de la Base de Données
Créez une base de données nommée `observatoire_emploi` dans votre serveur MySQL :
```sql
CREATE DATABASE observatoire_emploi;
```

### 3. Installation du Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

Configurez vos accès MySQL dans `backend/config.py`.

### 4. Installation du Frontend
```bash
cd frontend
npm install
```

## 🎮 Exécution

### Lancer l'Application
1. **Démarrer le Backend** :
   ```bash
   cd backend
   python app.py
   ```
   *L'API sera accessible sur http://localhost:5000*

2. **Démarrer le Frontend** :
   ```bash
   cd frontend
   npm run dev
   ```
   *Le dashboard sera accessible sur http://localhost:5173*

### Automatisation du Scraping
Le scraper est configuré pour s'exécuter automatiquement toutes les heures au démarrage du serveur Flask. Pour un lancement manuel :
```bash
cd backend
python scraper/run_scrapers.py
```

## 📊 Endpoints API Principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/jobs` | GET | Liste des offres avec filtres complexes |
| `/api/stats/global` | GET | Indicateurs clés de performance |
| `/api/stats/technologies` | GET | Fréquence des technologies demandées |
| `/api/stats/regions` | GET | Distribution géographique |
| `/api/stats/historical` | GET | Évolution chronologique des offres |

---
**Owner**
- ID BEN AHMED Aissam

