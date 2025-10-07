# Analyse intelligente du Journal Officiel (JORF)

Ce petit outil automatise la lecture du Journal Officiel pour repérer les articles vraiment pertinents sans avoir à tout lire manuellement. Il utilise Gemini Flash-Lite 2.0 pour détecter les articles liés à au moins l’une des notes suivantes : 

- Note 8 – Immobilisations financières
- Note 11 – Dettes financières
- Note 14 – Autres passifs 
- Note 15 – Trésorerie  
- Note 16 – Comptes de régularisation
- Note 20 – Charges et produits financiers  
  
---

<h1 align=center>Exemple d'analyze :</h1>
<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fefaf1;">
<h2 style='color:#000091;margin-top:5px'>Articles pertinents (JORF_20251003)</h2><ul><li style='margin-bottom:10px;'><strong>Arrêté du 29 septembre 2025 portant ouverture de crédits de fonds de concours ( 85%)</strong><br><em>Résumé:</em> L'arrêté du 29 septembre 2025 ouvre des crédits de fonds de concours pour l'année 2025, d'un montant total de 47,9 millions d'euros en autorisations d'engagement et de 49,3 millions d'euros en crédits de paiement, répartis entre différents programmes budgétaires.<br><br><em>Indice:</em> L'arrêté ouvre des crédits budgétaires, affectant les passifs de l'État.<br><em>Notes:</em> [14]<br><em>Montant:</em> 47.9 M€<br><a href='https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000052345414'>Voir l'article </a></li><li style='margin-bottom:10px;'><strong>Délibération n° 2025/CA/26 du 29 septembre 2025 relative à la mise en place d'un dispositif d'avances exceptionnelles aux exploitants en grande difficulté financière en 2025 (Centre national du cinéma et de l'image animée) ( 70%)</strong><br><em>Résumé:</em> Le CNC met en place un dispositif d'avances remboursables exceptionnelles pour les exploitants de cinéma en difficulté financière, basées sur le compte automatique exploitation cinéma et tenant compte de leur passif, endettement et trésorerie. Les demandes sont examinées par un comité d'experts.<br><br><em>Indice:</em> L'article décrit un dispositif d'avances exceptionnelles, impactant les passifs (14) et la trésorerie (15) des exploitants de cinéma.<br><em>Notes:</em> [14, 15]<br><em>Montant:</em> <br><a href='https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000052345421'>Voir l'article </a></li><li style='margin-bottom:10px;'><strong>Situation mensuelle de l'Etat (août 2025) ( 70%)</strong><br><em>Résumé:</em> Le document est un rapport mensuel sur la situation financière de l'État, sans mention de montants spécifiques.<br><br><em>Indice:</em> Le document présente la situation mensuelle de l'État, incluant des informations sur la dette et la trésorerie.<br><em>Notes:</em> [11, 15]<br><em>Montant:</em> <br><a href='https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000052345793'>Voir l'article </a></li><li style='margin-bottom:10px;'><strong>Arrêté du 30 septembre 2025 modifiant la liste des spécialités pharmaceutiques remboursables aux assurés sociaux ( 60%)</strong><br><em>Résumé:</em> L'arrêté modifie la liste des spécialités pharmaceutiques remboursables aux assurés sociaux, ajoutant de nouveaux médicaments et précisant les indications thérapeutiques.<br><br><em>Indice:</em> L'arrêté modifie la liste des spécialités pharmaceutiques remboursables, impactant les passifs de l'État.<br><em>Notes:</em> [14]<br><em>Montant:</em> <br><a href='https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000052345331'>Voir l'article </a></li></ul><h2 style='color:orange;'>Articles protégés</h2><ul><li style='margin-bottom:10px;'><strong>Décret du 2 octobre 2025 portant naturalisation, réintégration, mention d'enfants mineurs bénéficiant de l'effet collectif attaché à l'acquisition de la nationalité française par leurs parents, francisation de noms et de prénoms et libération de l'allégeance française (Accès protégé)</strong> — <a href='https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000052345665'>Voir l'article</a></li><li style='margin-bottom:10px;'><strong>Demandes de changement de nom (Accès protégé textes 72 à 80)</strong> — <a href='https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000052345798'>Voir l'article</a></li>
</div>

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

Installe les dépendances nécessaires 
```bash
pip install httpx beautifulsoup4
```
puis, 
en adaptant last_done.txt si besoin
```bash
python ./main.py
```

