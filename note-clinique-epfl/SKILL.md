---
name: note-clinique-epfl
description: Rédige et contrôle la note du premier entretien, les notes de suite (courtes ou de transmission), la synthèse-discussion, le relevé de données UNIL-EPFL et l'analyse IPB des séances (Document 2, G1/G2, Document 3) de la Consultation psychothérapeutique pour étudiants (CHUV/EPFL), à partir de notes d'entretien dictées. Procède en 7 étapes avec points de validation par le clinicien et contrôles automatiques. À utiliser quand le clinicien transmet des notes d'entretien, demande une note de premier entretien, une synthèse, un résumé d'investigation, la correction d'une note ou d'une synthèse existante, ou une analyse psychodynamique d'une séance.
---

# Note du premier entretien et synthèse — procédure en 7 étapes

## Principe

Deux forces, reliées par une contrebalance :

- **Comprendre** (liberté) : la compréhension de la situation gouverne le **contenu**.
- **Conformer** (contrainte) : le canevas du compartiment gouverne la **forme**.
- **La contrebalance** vérifie, dans les deux sens, que la note dit la même chose que la compréhension. On change de registre, pas de contenu.

Chaque règle ne se charge **qu'à l'étape où elle sert**. Ne pas lire les fichiers d'une étape avant d'y être.

## Base de données (texte du clinicien)

Exclusivement le contenu de cette conversation. Lire l'intégralité de la conversation depuis son début avant toute rédaction, et la relire après chaque ajout. Rien d'extérieur, rien d'inventé, rien d'ignoré. Un élément absent de la conversation n'existe pas. LES NOTES DICTÉES SONT GROSSIÈRES — Le matériel transmis est incomplet par nature. La fonction ne comble pas les manques, elle les relève. Une information nécessaire et absente donne lieu à une question, jamais à une reconstruction ni à un contournement.

Seule exception : la recherche en ligne du code, de l'intitulé et des critères diagnostiques CIM-10 (étape 3), qui est obligatoire.

Une conversation = un seul patient. Aucune donnée identifiante dans la fiche ni dans les textes.

## Les étapes

| # | Étape | Charger | Produit | Arrêt ? |
|---|---|---|---|---|
| 1 | **Compréhension de la situation** | `references/1-comprehension.md` | Bloc de prose continue, sans diagnostic | **OUI** : le clinicien valide la lecture du cas |
| 2 | **Fiche de faits** | `references/2-fiche-faits.md` | Tableau + `fiche.json` + questions (`controle.py fiche fiche.json --sans-decision`) | **OUI si questions bloquantes** |
| 3 | **Décision** | `references/3-decision.md`, `references/3-compartiments.md` | Critères CIM-10 vérifiés en ligne, diagnostics, compartiment, branches | **OUI** : le clinicien valide |
| 4 | **Rédaction sur canevas** | `references/4-langage.md`, `references/4-canevas-note.md`, `references/4-canevas-synthese.md` | Note et/ou synthèse | non |
| 5 | **Contrebalance** | `references/5-contrebalance.md` | Corrections, écarts signalés | non |
| 6 | **Contrôle automatique** | (script) | Rapport du script | non : boucle de correction |
| 7 | **Vérification et sortie** | `references/7-verification.md` | Réponse finale selon le contrat de sortie | — |

### Points d'arrêt

Aux étapes marquées **OUI**, montrer le résultat et **attendre la réponse du clinicien**. Si le clinicien écrit « enchaîne » (ou l'a demandé au départ), continuer sans s'arrêter, sauf s'il reste une **question bloquante** : celle-ci arrête toujours.

### Étape 4 : ce que la rédaction n'a pas le droit de faire

- utiliser un fait qui n'est pas dans la fiche validée ;
- choisir une autre branche que celle de l'étape 3 ;
- charger ou utiliser les branches des autres compartiments ;
- combler un champ NON EXPLORÉ autrement que par sa règle (bloquant, attente, omis, normal, dérivé de l'aigu).

Ordre de travail dans chaque rubrique : ouvrir le canevas, parcourir ses emplacements dans l'ordre, placer le fait de la fiche, puis relire la rubrique entière comme un texte (`4-langage.md`, « la rubrique comme unité »).

### Étape 6 : contrôle automatique

Enregistrer chaque texte dans un fichier, puis :

```
python3 scripts/controle.py texte note.txt --type note --fiche fiche.json
python3 scripts/controle.py texte synthese.txt --type synthese --fiche fiche.json
```

- **Erreur** → corriger le passage visé seulement (verrouillage), puis relancer. Au plus 3 tours ; au-delà, signaler ce qui reste.
- **Avertissement** → examiner ; corriger s'il est fondé, sinon le laisser.
- Le texte final est ensuite nettoyé pour le dossier : `python3 scripts/controle.py nettoie note.txt -o note_dossier.txt` (accents conservés, apostrophes, tirets et points de suspension rendus compatibles Latin-1).

Si l'exécution de code n'est pas disponible, appliquer les mêmes contrôles à la main en lisant `scripts/regles.json`, et le dire dans la sortie.

## Notes de suite (entretiens 2, 3, 4…)

Pas de procédure en 7 étapes. Charger `references/8-notes-de-suite.md` et `references/4-langage.md`. Note courte par défaut ; note de transmission si le clinicien a écrit « transmission » pour ce patient (vaut pour toutes ses notes de suite). S'appuyer sur la compréhension et la fiche déjà validées, mises à jour avec l'entretien. Contrôle : `python3 scripts/controle.py texte suite.txt --type suite-courte` (ou `suite-transmission`) `--fiche fiche.json`, jusqu'à zéro erreur.

## Relevé de données UNIL-EPFL

Quand le clinicien demande le relevé : charger `references/9-releve-donnees.md`, remplir `releve.json` (modèle `scripts/releve_modele.json`) à partir de la conversation, puis `python3 scripts/remplir_releve.py releve.json -o releve_rempli.pdf --defauts --apercu`. Corriger les erreurs, vérifier l'aperçu des deux pages, restituer le PDF avec la liste des défauts, déductions, rubriques vides et documents en attente.

## Analyse IPB — Document 2 (séances 1 à 4)

Quand le clinicien demande l'analyse (« analyse », « Document 2 ») ou envoie les notes d'une séance 2 ou plus sans autre demande : pas de procédure en 7 étapes. Charger `references/10-analyse-ipb.md` en entier et suivre son algorithme ; ouvrir `references/11-reperes-ipb.md` (fichier privé, s'il est présent) seulement pour la section utile. Contrôle : `python3 scripts/controle.py texte doc2.txt --type document2`, jusqu'à zéro erreur. G1/G2, Document 3 et courriers, seulement sur demande : `references/12-redactions-analyse.md`. Le Document 2 n'est jamais une note de dossier.

## Mode correction (un texte existe déjà)

Quand le clinicien soumet une note ou une synthèse à corriger : faire quand même les étapes 1 et 2 (sans elles, la correction n'a pas de repère), puis 5, 6 et 7. La règle de non-suppression et le verrouillage (`7-verification.md`) s'appliquent : on corrige, on ne retranche pas, et on ne réécrit pas ce qui est conforme.

## Sortie

Le contrat de sortie est à la fin de `references/7-verification.md`. Il commence toujours par la compréhension de la situation. Aucun commentaire sur le travail effectué.
