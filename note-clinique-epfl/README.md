# note-clinique-epfl

Skill Claude pour rédiger et contrôler la **note du premier entretien** et la **synthèse-discussion** de la Consultation psychothérapeutique pour étudiants (CHUV/EPFL).

Version 1, construite à partir de `Document_sans_titre_3` (la version la plus récente). Le contenu clinique est **repris mot pour mot**. Ce qui change, c'est l'organisation : 7 étapes, des points de validation, et des contrôles faits par un script plutôt que par l'IA.

## Pourquoi cette organisation

Dans la version « fonction unique », toutes les règles étaient chargées en même temps et l'IA décidait des faits, du diagnostic, de la structure et des mots en un seul passage. Les blocus étaient des consignes qu'elle **disait** avoir appliquées.

Ici :
- **la compréhension de la situation** vient en premier et gouverne le contenu ;
- **la fiche de faits** fixe ce qui est établi (présent / absent / non exploré) ;
- **les décisions** (diagnostic, compartiment, branches) sont prises avant d'écrire, et vérifiées ;
- **la rédaction** ne fait que mettre en forme sur le canevas du compartiment choisi ;
- **la contrebalance** confronte la note à la compréhension, dans les deux sens ;
- **le script** vérifie mécaniquement ce qui peut l'être : il ne se trompe pas et ne fait pas semblant.

```
1 Compréhension ──► 2 Fiche de faits ──► 3 Décision ──► 4 Rédaction ──► 5 Contrebalance ──► 6 Script ──► 7 Vérification
   (vous validez)      (questions)          (vous validez)    (canevas)        (2 sens)            (boucle)
```

## Contenu

| Fichier | Rôle |
|---|---|
| `SKILL.md` | Le chef d'orchestre : les 7 étapes, ce qui se charge à chacune, les arrêts |
| `references/1-comprehension.md` | Votre étape « compréhension de la situation » |
| `references/2-fiche-faits.md` | La fiche de faits et les trois états |
| `references/3-decision.md`, `3-compartiments.md` | Compartiments, branches, couplage évolution → issue |
| `references/4-langage.md` | Langage, quatre filtres, deux registres |
| `references/4-canevas-note.md`, `4-canevas-synthese.md` | Vos canevas |
| `references/5-contrebalance.md` | Confrontation compréhension ↔ note, traçabilité |
| `references/7-verification.md` | Modes, non-suppression, verrouillage, vérification, contrat de sortie |
| `scripts/controle.py` | Le contrôle automatique (Python standard, sans installation) |
| `scripts/regles.json` | **Toutes les règles mécaniques, modifiables sans programmer** |
| `scripts/fiche_modele.json` | Fiche vierge |
| `exemples/` | Un cas **entièrement fictif** : fiche, note et synthèse conformes, et une note volontairement fautive |
| `ARBITRAGES.md` | Ce qui est tranché, ce qui est appliqué provisoirement, ce qui reste à décider |

## Installation dans Claude (claude.ai)

1. Compresser le dossier `note-clinique-epfl` en `.zip`.
2. Dans Claude : **Paramètres → Capacités → Skills → Importer**, puis choisir le zip. L'exécution de code doit être activée pour que le script tourne.
3. Ouvrir **une conversation par patient** et y coller les notes d'entretien.

## Utilisation

- « Voici les notes des entretiens 1 à 4, fais la note et la synthèse » → l'IA s'arrête après la compréhension, puis après la fiche (questions), puis après la décision.
- « … enchaîne » → elle va jusqu'au bout, sauf s'il reste une question bloquante.
- « Corrige cette note » → mode correction : compréhension et fiche d'abord, puis correction sans retrancher.

Tester le script à la main :

```
python3 scripts/controle.py fiche exemples/fiche_exemple.json
python3 scripts/controle.py texte exemples/note_exemple.txt --type note --fiche exemples/fiche_exemple.json
python3 scripts/controle.py texte exemples/note_avec_erreurs.txt --type note --fiche exemples/fiche_exemple.json
python3 scripts/controle.py nettoie exemples/note_exemple.txt -o note_dossier.txt
```

## Faire évoluer le système sans le refaire dériver

1. Une erreur récurrente dans une note → d'abord se demander si elle peut être **détectée par le script**. Si oui, l'ajouter à `regles.json` (une ligne).
2. Sinon, corriger la règle **dans le fichier de l'étape concernée**, pas dans un bloc « règles supplémentaires » en fin de document.
3. Ajouter le cas à `exemples/` (fictif) et vérifier que les anciens cas passent toujours.

## Limites

- Le système ne remplace ni le jugement clinique ni la supervision. La qualité de la compréhension (étape 1) dépend de vos notes dictées, et c'est vous qui la validez.
- Le script vérifie la forme (rubriques, items, mots, sigles, résidus de canevas, cohérence des décisions). Le sens se vérifie aux étapes 5 et 7.
- **Confidentialité** : ne jamais mettre de données de patients dans ce dossier ni dans un dépôt. Vérifier les règles du CHUV sur l'usage d'outils d'IA avec des données cliniques, et anonymiser.

## Hors de cette version

Notes de suite, relevé de données, supervision IPB (Document 2), tableau de suivi. Voir `ARBITRAGES.md` (A8, A9).
