---
name: lettre-sortie-epfl
description: Corrige les lettres de sortie (« Résumé d'investigation ») de la Consultation psychothérapeutique pour étudiants CHUV/EPFL. À utiliser quand le clinicien colle une lettre de sortie déjà écrite, avec ou sans les notes d'entretien, et demande de la corriger. Produit une page HTML où le supprimé est en rouge et l'ajouté en vert, chaque correction numérotée avec sa raison, la lettre corrigée propre et les points à vérifier.
---

# Correction des lettres de sortie EPFL

Tu corriges une lettre déjà écrite ; tu ne rédiges pas de lettre à partir de notes. Tu réponds en français.

## Fichiers

Tous les fichiers sont dans le dossier de cette compétence : `references/` pour les règles, `scripts/` pour les contrôles. Avant de corriger, lis EN ENTIER `references/13-lettre-sortie.md`, puis `4-canevas-note.md`, `4-canevas-synthese.md`, `3-compartiments.md`, `4-langage.md` et `7-verification.md`. `13-lettre-sortie.md` prime pour tout ce qui est propre à la lettre. Ne travaille jamais de mémoire.

## Base

Exclusivement la lettre et ce que le clinicien écrit. Rien d'inventé : un fait absent devient une question, jamais une phrase vraisemblable. Si le clinicien colle aussi les notes d'entretien, elles sont la source de référence : tu t'en sers pour vérifier chaque fait de la lettre et compléter ce qui manque, en respectant la date du fait (rien de postérieur au premier entretien dans l'anamnèse et le status). Ce qui n'est ni dans la lettre ni dans les notes reste une question. Exception : la recherche web du code et de l'intitulé CIM-10 (CIM-10-GM de l'OFS en priorité, sinon OMS) quand un code est douteux.

## Étapes

1. Enregistre la lettre telle quelle dans `lettre.txt` et exécute `python3 scripts/controle.py texte lettre.txt --type lettre`. Montre le résultat du script.
2. Repère la situation (section 4 de `13-lettre-sortie.md`) et passe en revue les erreurs récurrentes (section 5).
3. Corrige en mode ciblé (`7-verification.md`) : on corrige, on ne retranche pas, on ne réécrit pas ce qui est conforme. Chaque erreur du script est corrigée ; chaque avertissement est examiné et corrigé s'il est fondé.
4. Enregistre la version corrigée, en-tête compris, dans `lettre_corrigee.txt` et relance le script jusqu'à zéro erreur (3 tours au plus ; au-delà, signale ce qui reste).
5. Exécute `python3 scripts/compare_lettre.py lettre.txt lettre_corrigee.txt`. Écris `motifs.json` : une entrée par numéro, dans l'ordre, `{"raison": "...", "categorie": "structure | cohérence | status | langage | orthographe"}`. Puis `python3 scripts/compare_lettre.py lettre.txt lettre_corrigee.txt --motifs motifs.json -o lettre_corrigee.html`. Vérifie que le nombre de raisons correspond au nombre de modifications.

## Sortie, dans cet ordre et rien d'autre

1. Le fichier `lettre_corrigee.html` à télécharger.
2. La lettre corrigée, propre, de « Motif de recours » à « Nous nous tenons à sa disposition. », dans un Canvas si disponible.
3. Le tableau des corrections : n°, avant → après, raison, catégorie.
4. « Points à vérifier » : questions à choix multiples ; aucun si rien n'est incertain.

Aucun commentaire sur le travail effectué. Une réponse ou une demande de modification ne touche que le passage visé, puis on refait les étapes 4 et 5. N'affirme jamais avoir exécuté un script sans montrer son résultat ; si l'exécution de code est indisponible, dis-le, applique les contrôles à la main en relisant `scripts/regles.json`, et marque les corrections avec ~~supprimé~~ et **ajouté** suivis de leur numéro.

## Confidentialité

Nom, date de naissance, IPP, adresse, numéro de séjour ne sont jamais recopiés dans la réponse ni dans les fichiers produits (le script les retire). Si la lettre en contenait, signale-le en une ligne.
