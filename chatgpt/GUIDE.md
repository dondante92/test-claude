# Créer le GPT « Note clinique EPFL » dans ChatGPT

Durée : 10 minutes, une seule fois. Il faut un abonnement ChatGPT payant (Plus, Pro…) et un ordinateur : la création d'un GPT ne se fait pas depuis l'application mobile.

## 1. Ouvrir l'éditeur

1. Aller sur **chatgpt.com**.
2. Menu de gauche → **GPTs** (ou « Explorer les GPT ») → **+ Créer** (en haut à droite).
3. Cliquer sur l'onglet **Configurer**. Ne pas utiliser l'onglet « Créer », qui fait discuter avec un assistant.

## 2. Remplir les champs

| Champ | Quoi mettre |
|---|---|
| **Nom** | Note clinique EPFL |
| **Description** | Note du premier entretien et synthèse en 7 étapes, avec contrôles automatiques. |
| **Instructions** | Copier-coller **tout** le contenu de `instructions.txt` |
| **Amorces de conversation** | voir ci-dessous |

Amorces de conversation (une par case) :
- `Voici les notes du premier entretien, fais la note :`
- `Voici les notes des entretiens 1 à 4, fais la note et la synthèse :`
- `Corrige cette note :`
- `Enchaîne`

## 3. Déposer les fichiers

Rubrique **Connaissances** → **Charger des fichiers** → sélectionner **les 12 fichiers** du dossier `fichiers/` :

```
1-comprehension.md      4-canevas-note.md        7-verification.md
2-fiche-faits.md        4-canevas-synthese.md    controle.py
3-decision.md           4-langage.md             regles.json
3-compartiments.md      5-contrebalance.md       fiche_modele.json
```

## 4. Cocher les fonctionnalités

Rubrique **Fonctionnalités** :
- ✅ **Interpréteur de code et analyse de données** : **indispensable**. C'est lui qui exécute le script de contrôle, c'est-à-dire les blocus.
- ✅ **Recherche web** : pour vérifier la CIM-10 à l'étape 3.
- ⬜ Génération d'images : inutile.

## 5. Confidentialité, avant d'enregistrer

- Ouvrir **Paramètres supplémentaires** (en bas de l'onglet Configurer) et **décocher** « Utiliser les données de conversation pour améliorer nos modèles ».
- Dans vos propres réglages ChatGPT : **Paramètres → Contrôle des données → Améliorer le modèle pour tous** → désactiver.
- Toujours anonymiser les notes : ni nom, ni date de naissance, ni détail qui rend la personne reconnaissable. Vérifier ce que le CHUV autorise.

## 6. Enregistrer

Bouton **Créer** (ou « Mettre à jour ») en haut à droite → partage : **Seulement moi**. Pour vos collègues, choisir plus tard « Toute personne disposant du lien ».

## Utilisation

- **Un patient = une nouvelle conversation** avec le GPT.
- Coller les notes en précisant l'entretien (E1, E2…).
- Le GPT s'arrête après la compréhension, après la fiche s'il a des questions, et après la décision. Écrire **« enchaîne »** pour qu'il aille jusqu'au bout.
- À l'étape 6, vous devez voir passer l'exécution du script (« Analyse… »). **Si le GPT dit avoir contrôlé sans montrer le résultat du script, demandez-le-lui** : c'est la garantie que les blocus ont vraiment tourné.

## Mettre à jour les règles

Quand une règle change dans le dossier `note-clinique-epfl/`, régénérer le paquet (`python3 chatgpt/build.py`), puis dans l'éditeur du GPT supprimer l'ancien fichier concerné et charger le nouveau. Si `instructions.txt` a changé, recoller son contenu.

## Ce qui diffère de la version Claude

Rien sur le fond : mêmes étapes, mêmes règles, même script. La qualité de rédaction dépend du modèle utilisé. Comparez sur un même cas fictif.
