# 📄 Analyse intelligente du Journal Officiel (JORF)

Ce petit outil automatise la lecture du Journal Officiel pour repérer les articles vraiment pertinents… sans avoir à tout lire manuellement. Il utilise un LLM pour détecter ceux qui parlent de finances publiques (trésorerie, dettes, immobilisations, etc.).

---

## ⚙️ Ce que fait le script

1. Télécharge automatiquement la dernière archive du JORF.
2. Extrait chaque article au format XML.
3. Envoie les titres + extraits au modèle Gemini Flash Lite (API Google).
4. Le modèle répond avec :
   - Une **liste de notes** comptables concernées (8, 11, 14, 15, 16 ou 20).
   - Un **score d’importance** (entre 0 et 100).
5. Si l’article est jugé pertinent :
   - On l’ajoute dans un fichier trié.

---

## 📦 Installation

Installe les dépendances nécessaires (Python ≥ 3.8 recommandé) :

```bash
pip install httpx beautifulsoup4 torch
