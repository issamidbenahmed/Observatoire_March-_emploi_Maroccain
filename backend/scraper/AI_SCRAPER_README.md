# 🤖 Deep AI Scraper - Guide d'utilisation

## 📋 Prérequis

### 1. Installer Ollama
```bash
# Télécharger depuis https://ollama.ai
# Ou si déjà installé, vérifier:
ollama --version
```

### 2. Télécharger un modèle
```bash
# Recommandé pour l'extraction (rapide et précis):
ollama pull llama3.2:latest

# Alternatives:
ollama pull mistral
ollama pull codellama
```

### 3. Lancer Ollama
```bash
ollama serve
```

### 4. Installer les dépendances Python
```bash
cd backend/scraper
pip install -r requirements_ai.txt
playwright install chromium
```

## 🚀 Utilisation

### Étape 1: Lancer le scraping AI
```bash
cd backend/scraper
python ai_deep_scraper.py
```

**Ce que fait le script:**
- ✅ Scrape Rekrute.com page par page
- ✅ Extrait chaque offre avec Ollama (AI)
- ✅ Parse intelligemment: dates, villes, technologies, compétences
- ✅ Sauvegarde en JSON au fur et à mesure
- ✅ Gère les erreurs et continue

**Durée estimée:** 2-3 heures pour 1000 offres (avec Ollama local)

### Étape 2: Importer dans la BD
```bash
cd backend/scraper
python import_ai_data.py ai_scraped_jobs_YYYYMMDD_HHMMSS.json
```

## 🎯 Avantages du Scraper AI

### vs Scraper classique:
| Critère | Classique | AI |
|---------|-----------|-----|
| **Dates** | Parsing regex fragile | ✅ Compréhension contextuelle |
| **Villes** | Sélecteurs CSS | ✅ Extraction intelligente |
| **Technologies** | Liste prédéfinie | ✅ Détection automatique |
| **Compétences** | Regex basique | ✅ Extraction sémantique |
| **Robustesse** | Casse si HTML change | ✅ S'adapte au contenu |

### Données extraites:
```json
{
  "title": "Développeur Full Stack",
  "company": "TechCorp Maroc",
  "location": "Casablanca",
  "date_posted": "2024-12-20",
  "technologies": ["React", "Node.js", "MongoDB", "Docker"],
  "skills": ["Travail d'équipe", "Agile", "Problem solving"],
  "contract_type": "CDI",
  "experience_required": "3 ans",
  "salary": "15000-20000 MAD",
  "description_summary": "Poste de développeur full stack..."
}
```

## ⚙️ Configuration

### Modifier le modèle Ollama
Dans `ai_deep_scraper.py`:
```python
OLLAMA_MODEL = "llama3.2:latest"  # Changer ici
```

### Ajuster le nombre de pages
```python
for page_num in range(1, 51):  # Modifier 51 pour plus/moins de pages
```

### Limiter les offres par page (pour test)
```python
for idx, job_url in enumerate(job_links[:10], 1):  # Modifier 10
```

## 🐛 Dépannage

### Ollama ne répond pas
```bash
# Vérifier qu'Ollama tourne:
curl http://localhost:11434/api/tags

# Relancer si nécessaire:
ollama serve
```

### Extraction JSON échoue
- Le modèle peut parfois ne pas retourner du JSON valide
- Le script réessaie automatiquement
- Vérifier les logs pour voir les réponses

### Trop lent
- Utiliser un modèle plus petit: `ollama pull llama3.2:1b`
- Réduire le nombre d'offres par page
- Augmenter le timeout

## 📊 Monitoring

Le script affiche en temps réel:
```
📄 Page 5/50...
  Trouvé 20 offres
    [1/20] Extraction AI...
      ✅ Développeur Full Stack - React/Node.js
    [2/20] Extraction AI...
      ✅ Data Scientist - Python/TensorFlow
```

Sauvegardes automatiques toutes les 5 pages !

## 🎯 Prochaines étapes

1. **Tester** avec 1-2 pages d'abord
2. **Vérifier** la qualité des données dans le JSON
3. **Lancer** le scraping complet
4. **Importer** dans la BD
5. **Vérifier** le dashboard avec les nouvelles données

## 💡 Tips

- Lancer le scraping la nuit (long)
- Garder Ollama ouvert pendant tout le processus
- Les fichiers JSON sont sauvegardés même en cas d'erreur
- Vous pouvez relancer l'import plusieurs fois (détecte les doublons)
