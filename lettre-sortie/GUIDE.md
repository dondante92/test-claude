# « Lettre de sortie EPFL » — correction des résumés d'investigation

Vous collez une lettre déjà écrite. Vous recevez :
1. une **page colorée** : supprimé en rouge barré, ajouté en vert, chaque correction numérotée ;
2. la **lettre corrigée propre**, prête à coller ;
3. le **tableau des raisons** (n°, avant → après, raison, catégorie) ;
4. les **points à vérifier** que l'IA ne peut pas trancher seule (questions à choix multiples).

Les règles viennent de l'analyse de 11 lettres signées (`note-clinique-epfl/references/13-lettre-sortie.md`) et des canevas déjà validés pour la note et la synthèse.

## Option A0 : plugin ChatGPT (les GPT personnalisés ne peuvent plus être créés depuis fin octobre 2026 et s'arrêtent le 11 décembre 2026)

1. ChatGPT → **Plugins** → créer un plugin (Plugin Creator).
2. Joindre **`lettre-sortie-epfl.zip`** (la compétence : `SKILL.md`, `references/`, `scripts/`) et demander de l'utiliser telle quelle, avec l'exécution de code.
3. Test : « exécute python3 scripts/controle.py texte exemple.txt --type lettre » sur une lettre : le résultat du script doit s'afficher.

## Option A : GPT ChatGPT (recommandée : les scripts tournent, la page colorée est un vrai fichier)

1. chatgpt.com → GPTs → **+ Créer** → onglet **Configurer**.
2. **Nom** : Lettre de sortie EPFL. **Instructions** : tout `instructions-gpt.txt`.
3. **Amorces** : `Corrige cette lettre :` · `Voici mes réponses :`
4. **Connaissances** : les 9 fichiers du dossier `fichiers/`.
5. **Fonctionnalités** : ✅ Interpréteur de code (indispensable) · ✅ Recherche web · ✅ Canvas.
6. **Paramètres supplémentaires** : décocher l'amélioration des modèles. Partage : **Seulement moi**.

## Option B : projet Claude

1. claude.ai → Projets → **Créer un projet** : « Lettre de sortie EPFL ».
2. **Instructions du projet** : tout `instructions-claude.txt`.
3. **Fichiers du projet** : les 9 fichiers du dossier `fichiers/`.
4. Activer l'exécution de code si elle est proposée : sinon les contrôles sont faits à la main (Claude le dit) et la page colorée est produite directement en artefact.

## Utilisation

- **Une lettre = une nouvelle conversation.**
- Coller la lettre, de préférence **sans l'en-tête d'identité** (nom, date de naissance, IPP, adresse). Si vous la laissez, elle est retirée de tout ce qui est produit, mais elle a quand même été envoyée au service.
- Le GPT doit montrer le résultat du script (« Analyse… »). S'il dit avoir contrôlé sans le montrer, demandez-le.
- Répondez aux points à vérifier : seule la partie concernée est reprise.

## Mettre à jour

Après une modification des règles : `python3 lettre-sortie/build.py`, puis remplacer les fichiers dans le GPT ou le projet.
