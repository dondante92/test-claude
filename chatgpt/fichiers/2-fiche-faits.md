# Étape 2 — Fiche de faits

> But : séparer **ce qui est établi** de **ce qui est rédigé**. Tout ce que les textes diront vient de cette fiche, et rien d'autre.
> Modèle complet : `scripts/fiche_modele.json`. Règles par champ : `scripts/regles.json` (section `champs`), qui fait foi.

## Ce que l'étape produit

À partir des notes dictées **et** de la compréhension validée (étape 1), remplir la fiche :

1. **Pour le clinicien** : un tableau lisible, à valider ou corriger.

   | Champ | État | Fait (ses mots) | Source |
   |---|---|---|---|
   | Âge | PRÉSENT | 22 ans | E1 |
   | Idées suicidaires | NON EXPLORÉ | — | — |

2. **Pour le contrôle** : le fichier `fiche.json` (même contenu). Enregistrer aussi les notes brutes du clinicien, telles quelles, dans `notes.txt`, puis lancer :
   `python3 scripts/controle.py fiche fiche.json --sans-decision --notes notes.txt` (les décisions viennent à l'étape 3)

3. **Les questions** que le script renvoie, en un seul bloc :
   - **questions bloquantes** : à poser **avant** toute rédaction ;
   - **champs en attente** : le texte sera produit avec `[À COMPLÉTER : …]` visible, et la question sera posée en fin de réponse.

## Balayage des symptômes (avant de remplir, puis par le script)

Erreur récurrente : un symptôme aigu écrit dans les notes n'arrive pas dans la fiche, donc ni dans le plan aigu, ni dans le status, ni dans le diagnostic.

1. **Avant de remplir** : relire les notes **ligne par ligne** et relever chaque mention de symptôme, même isolée, même en abrégé, même au milieu d'une phrase sur autre chose (« mange moins », « fume des joints pour se calmer », « n'arrive plus à suivre en cours »). Domaines à passer en revue : humeur, intérêt et plaisir, anxiété, sommeil, appétit et poids, énergie, concentration, irritabilité, idées de mort, auto-agressivité, consommations, plaintes somatiques, symptômes psychotiques, (hypo)manie, retrait social, alimentation, obsessions, trauma, dissociation.
2. **Chaque mention reçoit une place** : `aigu.symptomes` (avec datation), `chronique.elements`, un champ du status, ou **`aigu.ecartes`** avec la raison (« stress » = mot du patient pour le facteur de crise). Une mention niée (« pas d'idées noires ») est un ABSENT, pas un oubli.
3. **Le script vérifie** (`--notes`) : tout domaine nommé dans les notes, hors négation, et absent de la fiche est une **erreur**. Corriger la fiche, jamais le lexique pour faire taire l'erreur. Un mot manqué par le script peut être ajouté à `lexique_symptomes` dans `regles.json`.

## Les trois états

| État | Sens | Exemple |
|---|---|---|
| **PRÉSENT** | Le fait est dans les notes | « difficultés d'endormissement depuis un mois » |
| **ABSENT** | Exploré et négatif | « pas d'idées suicidaires » est écrit dans les notes |
| **NON EXPLORÉ** | Rien dans les notes | les notes ne parlent pas de l'appétit |

**ABSENT et NON EXPLORÉ ne se confondent jamais.** C'est la distinction qui empêche à la fois d'inventer un négatif et de laisser un trou silencieux.

## Ce qui arrive à un champ NON EXPLORÉ

| Règle | Effet | Champs (voir `regles.json`) |
|---|---|---|
| **BLOQUANT** | Question avant rédaction | genre, âge, cursus, mode d'arrivée, motif, cadre, nombre de séances, idées suicidaires (plan aigu, status, et en fin de suivi si présentes au départ), diagnostic final |
| **ATTENTE** | `[À COMPLÉTER : …]` dans le texte + question en fin | facteur de crise, retentissement, lieu de naissance et de croissance, fratrie, relations familiales, social, sentimental, chaîne des antécédents, participation |
| **OMIS** | L'emplacement disparaît, la phrase est réécrite sans lui | origine, arrivée en Suisse, délimitation, mesures, logement, financier, anamnèse somatique |
| **NORMAL** | Valeur normale du répertoire | items du status : tenue, attitude, vigilance, contact, discours, pensée, substances |
| **DERIVE_AIGU** | Reprend ce que le plan aigu documente, sinon normal | thymie, appétit, sommeil, anxiété du status |

## Règles reprises de votre texte (mot pour mot)

▸ QUESTIONS PRÉALABLES — avant de produire, pas après Certains champs conditionnent une phrase entière du moule : l'âge, l'origine ou le parcours, le cursus exact, le mode d'arrivée à la consultation, le nombre de séances, le cadre de l'intervention. Quand l'un d'eux manque et n'est pas trouvable dans la conversation, deux conduites, jamais une troisième :
· poser la question avant de produire le texte ;
· ou produire le texte en laissant le champ visiblement en attente, signalé comme tel. IL EST INTERDIT de rédiger une phrase amputée qui masque le manque. IL EST INTERDIT, lorsqu'une alternative du moule ne peut pas être tranchée (prend contact de lui-même / est adressé par), de fabriquer une troisième formulation neutre qui évite de choisir. On demande. Les autres manques sont relevés dans le bloc de questions final.

▸ TEMPORALITÉ DES DONNÉES — La note documente l'état du patient au moment du premier entretien. Ce qui compte est la date du fait, pas celle où il a été appris. Exclu : ce qui est survenu après. Inclus, même rapporté plus tard : antécédents, biographie, contexte, fonctionnement habituel, éléments chroniques, symptômes déjà présents mais non encore rapportés.

## Règles de remplissage

- **La colonne Source est obligatoire** (E1, E2, …). Elle sert à la règle de temporalité : un fait survenu après E1 n'entre pas dans la note, mais un fait ancien appris en E3 y entre.
- **Les mots du clinicien, pas une reformulation.** La fiche n'est pas un texte : on n'y « améliore » rien. Ne jamais convertir les propos en critères plus précis qu'ils ne l'étaient.
- **Chaque symptôme aigu a sa datation** (`depuis`) **et son destin** (`etat_final` : amendé, atténué, persistant, stable, majoré). C'est la table de correspondance : elle garantit qu'aucun symptôme ne disparaît sans destin dans l'évolution, et qu'on n'écrit jamais « persistance de X » sans X.
- **Status** : seulement ce qui a été observé au premier entretien. L'observé se distingue du rapporté.
- **Aucune donnée identifiante** : ni nom, ni date de naissance, ni tiers identifiable.
