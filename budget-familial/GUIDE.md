# Installer le copilote budgétaire dans ChatGPT

Durée : 10 minutes, une seule fois, depuis un ordinateur (chatgpt.com). Il faut un abonnement payant (Plus ou Pro) : l'interpréteur de code est indispensable, c'est lui qui fait tous les calculs.

## Ce que vous recevez

| Fichier | Rôle | Où il va |
|---|---|---|
| `instructions.txt` | Le mode d'emploi de l'assistant | à coller dans les **instructions** du projet |
| `fichiers/budget.py` | Le moteur : dédoublonnage, cycles, semaines, enveloppes, projection, tableau | fichiers du projet |
| `fichiers/releves.py` | Lit les relevés PDF PostFinance (extrait de compte, facture de carte), vérifiés au centime | fichiers du projet |
| `fichiers/tableau_modele.html` | Le gabarit du tableau de bord | fichiers du projet |
| `fichiers/categories.json`, `fichiers/regles_commercants.json` | Catégories et commerçants suisses | fichiers du projet |
| `fichiers/methode.md` | Toutes les règles (anti-double-comptage, modes, conseils) | fichiers du projet |
| `contexte-foyer.md` | Votre famille, vos montants, vos décisions (**privé**) | fichiers du projet |
| `tableau-budget.html` | **Votre état** : tout l'historique, à garder | sur votre téléphone ou ordinateur, **pas** dans le projet |

## 1. Créer le projet

1. chatgpt.com → menu de gauche → **Projets** → **Nouveau projet**. Nom : `Budget du foyer`.
2. Ouvrir le projet → **Instructions** (icône ⋯ ou « Ajouter des instructions ») → coller **tout** `instructions.txt`.
3. **Fichiers du projet** → ajouter les 7 fichiers : `budget.py`, `releves.py`, `tableau_modele.html`, `categories.json`, `regles_commercants.json`, `methode.md`, `contexte-foyer.md`.
4. Si l'option existe : mémoire du projet **limitée au projet**.

> Alternative si les fichiers du projet ne sont pas accessibles à l'interpréteur de code : créer un **GPT** (Explorer les GPT → Créer → Configurer), coller les instructions, déposer les 7 fichiers dans **Connaissances** et cocher **Interpréteur de code**. Garder le GPT en « Seulement moi ».

## 2. Confidentialité

- Paramètres → Contrôle des données → **Améliorer le modèle pour tous : désactivé**.
- `contexte-foyer.md` et `tableau-budget.html` contiennent vos données financières : ne les partagez pas et ne les déposez jamais sur GitHub (le dossier `prive/` est exclu du dépôt).
- Recadrez les captures pour ne pas montrer votre IBAN complet.

## 3. Le geste quotidien (tous les 2 à 3 jours)

1. Dans l'application PostFinance, faire les captures :
   - le **compte privé** (liste des mouvements depuis la dernière fois, avec le solde en haut) ;
   - la **carte de crédit** (mouvements, avec le montant comptabilisé et les **réservations**) ;
   - les **ordres en suspens**, s'il y en a.
2. Dans le projet, nouvelle conversation (ou la conversation de la semaine) : joindre **`tableau-budget.html` + les captures**, écrire `maj`. Les captures peuvent se chevaucher, les doublons sont éliminés.
3. Répondre aux questions numérotées (« 1 maison, 2 enfant, 3 ok »). Dire « toujours » pour que l'assistant retienne une habitude (« Migros Lavigny, c'est toujours mon repas de travail »).
4. **Télécharger le nouveau `tableau-budget.html`** et remplacer l'ancien. C'est le seul fichier à conserver. Astuce : le garder dans un dossier iCloud ou Google Drive « Budget », pour l'ouvrir aussi sur le téléphone.

Fiche de salaire : la joindre le jour du salaire avec les captures. L'assistant isole les remboursements, les rappels et les indemnités pour ne pas gonfler le salaire de référence.

## 3 bis. Chaque mois : les relevés PDF

Quand l'extrait du compte privé et la facture de carte de crédit du mois arrivent (application ou e-finance PostFinance → Documents), joignez-les avec le dernier tableau et écrivez `relevés`. Ils sont plus exacts que les captures : ils remplacent les lignes déjà saisies par captures, sans doublon. Ne les mettez pas dans les fichiers du projet.

## 4. Lire le tableau de bord

Ouvrir `tableau-budget.html` dans un navigateur (double-clic). Rien n'est envoyé sur Internet.

- **Aujourd'hui** : cash, dette carte, position nette, reste de la semaine.
- **Frise du cycle** : du salaire à la veille du suivant, semaine par semaine (vert, orange, rouge), avec les échéances.
- **Semaine par semaine** : budget normal, report, disponible, dépensé.
- **Semaine en cours** : chaque poste face à sa cible, avec d'où vient un dépassement.
- **Enveloppes**, **Projection** (prudente et réaliste), **Où part le salaire**, **Où va l'argent** (exceptionnel à part), **Mois normal**, **Alertes**.
- Cliquer sur une barre, une semaine ou une enveloppe affiche les transactions correspondantes : chaque chiffre est traçable.
- Bouton **Vue foyer** : pour montrer le budget à deux, il masque le détail des dépenses personnelles de chacun.

## 5. Phrases utiles

- `maj` (+ captures) : mise à jour complète.
- `bilan` : où on en est, sans nouvelles captures.
- `et si la crèche commence le 1er décembre à 3 jours par semaine ?` : simulation, sans toucher à l'état.
- `et si on active les 500 CHF d’argent personnel pour ma femme dès le salaire de novembre ?`
- `mode récupération de déficit` : plan chiffré pour revenir à zéro sans supprimer le coussin.
- `prévois la visite de ma famille du 15 au 22 décembre, environ 600 CHF`.
- `avance 90 CHF de la semaine prochaine sur celle-ci` (IQOS acheté d'avance).
- `quels abonnements on paie, et combien par an ?`
- `prépare un résumé pour en parler à deux ce soir`.

## 6. Mettre à jour le moteur

Quand `budget.py`, `methode.md` ou les règles changent dans ce dépôt : dans le projet, supprimer l'ancien fichier et déposer le nouveau. Votre `tableau-budget.html` reste valable : l'état est indépendant du moteur.

Vérifier le moteur à tout moment : `python3 budget.py test` (tests de non-régression de la spécification).
