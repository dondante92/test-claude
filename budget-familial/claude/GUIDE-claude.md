# Installer le copilote budgétaire dans Claude

Même moteur, mêmes règles, même tableau que la version ChatGPT : vous pouvez passer de l'un à l'autre avec le même `tableau-budget-….html`. Durée : 10 minutes, depuis un ordinateur (claude.ai). Il faut un abonnement payant (Pro ou Max).

## Ce que vous recevez

| Fichier | Rôle | Où il va |
|---|---|---|
| `budget-foyer.zip` | La **skill** : le moteur, le lecteur de relevés, le tableau, la méthode | Paramètres → Capacités → Skills |
| `instructions-projet.txt` | La manière de travailler | Instructions du projet |
| `contexte-foyer.md` | Votre famille, vos montants, vos décisions (**privé**) | Connaissances du projet |
| `tableau-budget-AAAA-MM-JJ.html` | **Votre état** : tout l'historique | chez vous (Drive), joint à chaque mise à jour |

## 1. Activer l'exécution de code

claude.ai → **Paramètres** → **Capacités** → activer **Exécution de code et création de fichiers**. C'est elle qui fait tourner le moteur.

## 2. Installer la skill

Toujours dans **Paramètres → Capacités → Skills** : **Importer une skill** → choisir `budget-foyer.zip` (ne pas le décompresser). Vérifier qu'elle est **activée**.

## 3. Créer le projet

1. Menu de gauche → **Projets** → **Créer un projet**. Nom : `Budget du foyer`.
2. **Instructions du projet** (« Définir les instructions ») : coller tout `instructions-projet.txt`.
3. **Connaissances du projet** (+) : ajouter `contexte-foyer.md`. Rien d'autre : les relevés et les captures ne vont pas ici, ils s'importent dans le tableau.

## 4. Premier test

Dans le projet, nouvelle conversation : `Lance le test du moteur budget-foyer.` → il doit répondre « 13/13 tests réussis ». Puis joindre le dernier `tableau-budget-….html` et écrire `bilan`.

## 5. Au quotidien

- **Tous les 2 à 3 jours** : joindre le dernier tableau + les captures PostFinance (compte, carte, soldes, ordres en suspens) → `maj`. Claude pose ses questions sous forme de choix ; répondre d'un clic ou librement. Télécharger le nouveau tableau et le ranger dans Drive.
- **Chaque mois** : joindre l'extrait du compte privé et la facture de carte (PDF) → `relevés`. Ils remplacent les captures sans doublon.
- **Le jour du salaire** : joindre la fiche de salaire → `bilan du cycle`.
- **Questions libres** : « pourquoi cette semaine est haute ? », « est-ce que je peux acheter… ? », « et si la crèche commence le 1er décembre ? », « résumé pour le couple ».

## 6. Améliorer l'outil au fur et à mesure

- **Une habitude** (« Migros Lavigny, c'est toujours mon repas ») ou un **paramètre** (budget jour, enveloppe, charges fixes) : dites-le simplement, Claude l'enregistre dans le tableau. Rien à réinstaller.
- **Une nouvelle fonction** (graphique, calcul, alerte) : demandez-la. Claude modifie une copie de la skill, lance les tests, et vous rend un nouveau `budget-foyer.zip` : Paramètres → Capacités → Skills → remplacer l'ancienne. Votre tableau reste compatible.

## Confidentialité

Gardez le projet privé (non partagé). `contexte-foyer.md` et le tableau contiennent vos données financières : ne les publiez pas. Recadrez les captures pour ne pas montrer l'IBAN complet.
