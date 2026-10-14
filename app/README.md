# Application « Note clinique EPFL »

Une page web autonome (`note-clinique.html`, un seul fichier) qui applique le skill `note-clinique-epfl` avec **l'IA de votre choix** : Claude, OpenAI, ou un modèle installé sur votre ordinateur.

## Démarrer en 1 minute

1. Télécharger `note-clinique.html` et l'ouvrir par double-clic (Chrome, Edge, Firefox ou Safari).
2. Sans rien régler, la page est en **mode démo** : écrire n'importe quoi dans « Notes dictées », cliquer sur **Lancer** et suivre le parcours sur un cas fictif.
3. Pour un vrai cas : **Réglages IA**, choisir le fournisseur, coller la clé d'API, enregistrer.

## Ce que fait la page

```
Notes dictées
   │
   ▼
1 Compréhension ─── vous validez (ou corrigez le texte)
2 Fiche de faits ── tableau modifiable ; le bouton « Valider » reste grisé tant qu'il y a une question bloquante
3 Décision ──────── diagnostic, compartiment, branches en menus ; une combinaison incohérente est refusée
4 Rédaction ─────── sur le canevas du compartiment choisi
5 Contrebalance ─── tableau compréhension ↔ note
6 Contrôle ──────── vérification automatique ; si erreur, l'IA corrige le passage visé (3 tours au plus)
7 Résultat ──────── texte final, [À COMPLÉTER] surlignés à remplir, questions à choix, « Copier pour le dossier »
```

- **L'IA ne voit, à chaque étape, que les règles de cette étape.**
- **Les contrôles ne sont pas faits par l'IA** : ils sont programmés dans la page (mêmes règles que `scripts/regles.json`). Ils ne varient donc pas d'un fournisseur à l'autre.
- Cocher « Enchaîner les étapes » fait tout d'un coup, sauf s'il reste une question bloquante.
- « Copier pour le dossier » rend le texte compatible Latin-1 en gardant les accents.

## Fournisseurs

| Fournisseur | Ce qu'il faut | Remarques |
|---|---|---|
| **Claude** | Une clé d'API (console.anthropic.com) | Modèle par défaut `claude-sonnet-5-5`, modifiable. Option « Recherche web » : l'IA vérifie code, intitulé et critères CIM-10 en ligne à l'étape 3. |
| **OpenAI** | Une clé d'API (platform.openai.com) et le nom exact d'un modèle de votre compte | Pas de recherche web : la CIM-10 est à confirmer par vous (la page l'affiche). |
| **Modèle local** | Ollama ou LM Studio installé, et un modèle téléchargé | **Rien ne quitte l'ordinateur.** Pour Ollama, lancer le serveur avec `OLLAMA_ORIGINS=*` pour autoriser la page. La qualité dépend fortement du modèle choisi. |

Changer de fournisseur ne change rien d'autre : mêmes étapes, mêmes règles, mêmes contrôles.

## Confidentialité, à lire avant un vrai cas

- La page **n'enregistre rien** : les notes et les textes disparaissent à la fermeture. Seuls les réglages sont gardés, et la clé seulement si vous cochez « Mémoriser ».
- Avec Claude ou OpenAI, **les notes sont envoyées à ce fournisseur** (serveurs hors de Suisse). Anonymiser : ni nom, ni date de naissance, ni détail qui rend la personne reconnaissable. Vérifier ce que le CHUV autorise.
- Le modèle local est la seule option où aucune donnée ne sort.
- Garder la clé d'API pour soi : quiconque l'a peut l'utiliser à vos frais.

## Coût indicatif

Un dossier complet fait 7 à 10 appels à l'IA. Le coût dépend du modèle choisi : consulter la page de tarifs du fournisseur. Le journal des appels (en bas à gauche) liste chaque appel et la taille des réponses, sans leur contenu.

## Modifier les règles

Les règles ne sont pas écrites dans la page : elles viennent du dossier `note-clinique-epfl/`.

1. Modifier le fichier concerné (`references/…` ou `scripts/regles.json`).
2. Régénérer la page : `python3 app/build.py`.
3. Tester en mode démo.

Le skill Claude et l'application restent ainsi toujours identiques.
