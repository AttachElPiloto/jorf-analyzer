# Analyse intelligente du Journal Officiel (JORF)

Ce petit outil automatise la lecture du Journal Officiel pour repérer les articles vraiment pertinents sans avoir à tout lire manuellement. Il utilise Gemini Flash-Lite 2.0 pour détecter ceux qui parlent de finances publiques (trésorerie, dettes, immobilisations, etc.).

---

## Pipeline

1. Télécharge automatiquement la dernière archive du JORF.
2. Extrait chaque article au format XML.
3. Envoie les titres + extraits de chaque article du JORF concerné à Gemini.
4. Le modèle répond avec un JSON formaté contenant : 
   - Une liste des notes concernées, vide si aucune ne l'est
   - Un score d'importance pour hiérarchiser les articles
   - Un bref résumé de l'article
   - Un indice permettant de comprendre le texte qui a trigger la détéction du LLM.
5. Enfin, on envoie un mail contenant les articles pertinents à l'adresse souhaitée.

---

## How-to-install

Installe les dépendances nécessaires (Python ≥ 3.8) :

```bash
pip install httpx beautifulsoup4

