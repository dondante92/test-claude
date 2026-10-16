# Note clinique EPFL dans un projet Claude — mode d'emploi

Il faut un abonnement Claude payant (Pro ou plus) pour les projets. Tout se fait sur **claude.ai**, sur ordinateur.

## Vous avez déjà un projet (premier modèle installé)

1. Ouvrez votre projet.
2. **Instructions** (à droite, « Instructions du projet ») → **effacez tout** → collez **tout** le contenu de `instructions.txt`.
3. **Connaissances du projet** (« Project knowledge ») → **supprimez les anciens fichiers** → cliquez **+** → **Charger** → sélectionnez **tous les fichiers** du dossier `fichiers/` (21 fichiers).
4. C'est tout.

## Vous partez de zéro

1. claude.ai → **Projets** → **Créer un projet** → nom : `Note clinique EPFL`.
2. Puis les étapes 2 et 3 ci-dessus.

## Réglages (une seule fois)

Paramètres (en bas à gauche) :
- **Fonctionnalités / Capacités** → activez **la recherche web** (vérification CIM-10) et, si elle existe, **l'exécution de code** (pour lancer les scripts de contrôle).
- **Confidentialité** → vérifiez que vos conversations ne servent pas à entraîner les modèles.
- **Mémoire** : si elle est activée, désactivez-la, ou limitez-la au projet. Sinon, des éléments d'un patient peuvent ressortir chez un autre.

## Utilisation

- **Un patient = une nouvelle conversation dans le projet.** Notes anonymisées (code patient, jamais le nom).
- Commencez par une de ces phrases :
  - `Voici les notes du premier entretien, fais la note :`
  - `Note de suite :` (ajoutez `transmission` une fois pour un patient que vous transmettez)
  - `Relevé de données`
  - `Analyse (Document 2), séance n° :`
  - `G1/G2`, `Document 3`, `Courrier d'adressage`
- `Enchaîne` : il continue sans s'arrêter, sauf question bloquante.
- `Formation` (ou `pas à pas`) : pour l'analyse, il explique les sigles et le livre à partir du cas, avance axe par axe et vous laisse essayer avant de donner sa lecture ; le Document 2 vient à la fin.

## Ce qui aide le plus l'analyse (dans vos notes)

- Marquez **(S)** ce que le patient a dit spontanément et **(Q)** ce qui répond à une de vos questions.
- Trois à cinq phrases du patient mot pour mot.
- Vos interventions importantes, et sa réaction immédiate.
- Une ligne sur ce que vous avez ressenti.
- Son âge.
- Ce que vous n'écrivez pas (le risque suicidaire par exemple) est lu comme exploré sans élément notable, pas comme oublié.

## Mettre à jour le projet après une modification des règles

Remplacez seulement les fichiers indiqués dans le message de mise à jour : dans « Connaissances du projet », supprimez l'ancien fichier (même nom), puis chargez le nouveau. Si `instructions.txt` a changé : effacez les instructions du projet et collez le nouveau texte en entier. Les conversations déjà ouvertes gardent l'ancienne version : ouvrez une nouvelle conversation.

## Ce qui change par rapport à ChatGPT

- Les **contrôles automatiques** ne tournent que si l'exécution de code est activée et peut lire les fichiers. Sinon, Claude applique les règles à la main **et doit le dire**. Si vous voulez les scripts à coup sûr, installez aussi le **skill** (`note-clinique-epfl.zip`) : Paramètres → Fonctionnalités → Skills → Charger.
- Le **relevé PDF** demande l'exécution de code. Sans elle, Claude donne un tableau à reporter à la main ; l'app ChatGPT, elle, produit toujours le PDF.

## Confidentialité

`11-reperes-ipb.md` est votre synthèse du livre IPB : il n'est **pas** publié sur GitHub. Ne partagez pas ce projet tant qu'il le contient.
