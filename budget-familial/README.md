# Copilote budgétaire du foyer (ChatGPT)

Assistant ChatGPT qui lit les captures PostFinance (compte et carte de crédit), élimine les doublons, suit le budget **par cycle de salaire et semaine par semaine avec report**, sépare nature / bénéficiaire / enveloppe, calcule la position nette **sans double comptage** (carte, réservations, ordres), projette jusqu'au salaire suivant (scénarios prudent et réaliste) et produit un **tableau de bord HTML interactif** qui contient aussi tout l'historique.

- Installation et utilisation : [GUIDE.md](GUIDE.md)
- Instructions à coller dans le projet : [instructions.txt](instructions.txt)
- Fichiers à déposer dans le projet : [fichiers/](fichiers/)
- Tests : `python3 fichiers/budget.py test`

Les données personnelles (contexte du foyer, état initial, fiches de salaire) vivent dans `prive/`, exclu du dépôt.
