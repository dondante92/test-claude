# App ChatGPT « Note clinique EPFL »

Une **app ChatGPT** (Apps SDK d'OpenAI, protocole MCP) : vous travaillez dans ChatGPT comme d'habitude, avec votre abonnement, et des **écrans interactifs s'affichent dans la conversation** :

| Étape | Ce qui s'affiche dans ChatGPT |
|---|---|
| 2 | **La fiche de faits**, modifiable. Le bouton « Valider » reste grisé tant qu'il y a une question bloquante. |
| 3 | **La décision** : diagnostic, compartiment et branches en menus, avec le refus des combinaisons incohérentes. |
| 7 | **Le texte final**, surligné, avec « Copier pour le dossier », les champs à compléter et les questions à choix. |

## Pourquoi c'est plus sûr qu'un GPT personnalisé

| | GPT personnalisé | **Cette app** |
|---|---|---|
| Règles de chaque étape | Lues dans les fichiers, si l'IA y pense | Envoyées par le serveur à chaque étape |
| Contrôles | Script lancé par l'IA, qui peut l'oublier | Faits par le serveur |
| Fiche et décision | Validées en texte | Validées **dans un écran**, bouton bloqué tant que c'est incohérent |
| Texte final | Affiché même s'il a des erreurs | **Refusé par le serveur** tant qu'il a des erreurs |

Une limite reste : ChatGPT pourrait encore écrire du texte libre dans la conversation. Mais **seul le texte affiché dans l'écran « Étape 7 · texte contrôlé » a passé les contrôles**. C'est celui-là qu'on copie dans le dossier.

---

## Installation (environ 20 minutes, une seule fois)

### Ce qu'il faut

- Un abonnement ChatGPT payant (Plus, Pro, Business…) et un **ordinateur**.
- **Node.js** version 18 ou plus : nodejs.org → « LTS » → installer.
- Le code : le dossier complet du dépôt (`chatgpt-app/`, `partage/`, `note-clinique-epfl/`), ou le zip `note-clinique-chatgpt-app.zip`.

### 1. Lancer le serveur sur votre ordinateur

Dans un terminal (Mac : application « Terminal » ; Windows : « PowerShell ») :

```
cd chemin/vers/le-dossier/chatgpt-app
npm install
npm start
```

Le terminal affiche : `Note clinique EPFL : http://localhost:8787/mcp`. **Laisser cette fenêtre ouverte.**

### 2. Rendre le serveur joignable par ChatGPT

ChatGPT ne peut pas atteindre « localhost » : il faut une adresse **https** publique. Le plus simple, gratuit et sans compte, est un tunnel Cloudflare. Dans **un second terminal** :

```
npx cloudflared tunnel --url http://localhost:8787
```

Il affiche une adresse du type `https://mots-au-hasard.trycloudflare.com`. **Votre adresse pour ChatGPT est cette adresse suivie de `/mcp`.**

Si `npx cloudflared` ne fonctionne pas, installer `cloudflared` depuis le site de Cloudflare (developers.cloudflare.com, rubrique « Cloudflare Tunnel ») et lancer la même commande sans `npx`. ngrok fait la même chose (`ngrok http 8787`).

Cette adresse change à chaque relance du tunnel. Pour une adresse fixe, voir « Installation durable » plus bas.

### 3. Activer le mode développeur dans ChatGPT

Sur **chatgpt.com** : **Paramètres** → **Applications et connecteurs** (« Apps & Connectors ») → **Paramètres avancés** → activer **Mode développeur**.

### 4. Ajouter l'app

Toujours dans **Applications et connecteurs** → **Créer** (ou « Ajouter une app / un connecteur ») :

| Champ | Valeur |
|---|---|
| Nom | Note clinique EPFL |
| Description | Note du premier entretien et synthèse en 7 étapes, avec contrôles et écrans. |
| URL du serveur MCP | `https://mots-au-hasard.trycloudflare.com/mcp` |
| Authentification | Aucune |

Cocher « Je fais confiance à cette application », puis **Créer**. ChatGPT doit lister **7 outils** : `demarrer_note_clinique`, `regles_etape`, `afficher_fiche`, `afficher_decision`, `controler_texte`, `afficher_resultat`, `nettoyer_pour_dossier`.

OpenAI déplace parfois ces menus. Si un intitulé diffère, chercher « mode développeur » ou « connecteur » dans l'aide de ChatGPT.

---

## Utilisation

1. Nouvelle conversation. Bouton **+** → **Mode développeur** (ou **Plus**) → choisir **Note clinique EPFL**.
2. Écrire, par exemple : `Utilise Note clinique EPFL. Fais la note du premier entretien : E1 : …` puis coller les notes.
3. ChatGPT écrit la **compréhension** et vous demande si c'est la bonne lecture.
4. **L'écran de la fiche** s'affiche : complétez les cases rouges, puis **Valider la fiche**. Le message part tout seul dans la conversation.
5. **L'écran de la décision** s'affiche, avec la CIM-10 vérifiée en ligne si la recherche web est active : corrigez si besoin, puis **Valider les décisions**.
6. ChatGPT rédige, confronte à la compréhension et fait contrôler par le serveur.
7. **L'écran du résultat** s'affiche : **Copier pour le dossier**. S'il reste des `[À COMPLÉTER]` ou des questions, répondez dans l'écran, puis **Intégrer mes réponses**.

Si un écran ne s'affiche pas (par exemple sur mobile), les outils fonctionnent quand même : ChatGPT donne les questions en texte. Le refus des textes non conformes reste actif.

---

## Installation durable (adresse fixe)

Pour ne pas relancer le tunnel à chaque fois, héberger le serveur :

- **Le mieux pour des données cliniques : un serveur du CHUV ou de l'EPFL**, à demander à l'informatique. Le serveur ne garde rien et n'écrit aucun contenu clinique dans ses journaux, mais il reçoit la fiche et les textes pendant la conversation.
- Sinon, un hébergeur Node.js (Render, Railway, Fly.io…) : déployer le dépôt avec la commande `npm start` dans `chatgpt-app/`. La variable `PORT` est prise en compte.

Puis remplacer l'adresse dans l'app ChatGPT par `https://votre-serveur/mcp`.

## Confidentialité

- Les notes passent par ChatGPT (OpenAI). Désactiver « Améliorer le modèle pour tous » (Paramètres → Contrôle des données) et **anonymiser** : ni nom, ni date de naissance, ni détail identifiant. Vérifier ce que le CHUV autorise.
- Le serveur ne stocke rien et n'enregistre aucun contenu.

## Modifier les règles

Le serveur lit les règles dans `note-clinique-epfl/` et les contrôles dans `partage/controles.js`, les mêmes que le skill Claude et l'application web. Après une modification : relancer `npm start`, puis dans ChatGPT, rouvrir l'app et cliquer sur « Actualiser ».

## Tests

```
cd chatgpt-app
npm test
```

Le test démarre le serveur, appelle les 7 outils comme ChatGPT, puis ouvre les écrans dans Chromium en simulant ChatGPT. Il vérifie notamment :
- âge non exploré → bouton bloqué ;
- évolution favorable avec psychothérapie indiquée → refusé ;
- note fautive → résultat refusé.

Pour le test des écrans, la variable `CHROMIUM_PATH` indique le navigateur à utiliser.
