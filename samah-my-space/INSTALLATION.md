# Installer « My space » sur le compte Claude de Samah

Trois fichiers :
- `my-space.html` : l'application (interface en anglais).
- `project-instructions.md` : les instructions à coller dans son projet Claude, pour qu'elle puisse aussi agir depuis une conversation.
- ce guide.

## Avant de commencer
- Samah a un compte **Claude Pro**.
- Elle utilise **claude.ai dans un navigateur** (ordinateur ou téléphone) pour l'installation. Sur l'application mobile Claude, l'enregistrement des données n'est pas garanti.

## Étapes

1. **Créer le projet.** Sur claude.ai : Projets → Nouveau projet → nom « My space ».

2. **Publier l'application depuis son compte.** Dans une nouvelle conversation de ce projet, elle joint `my-space.html` et envoie :
   > Publish this file exactly as it is as an artifact, with the capabilities db, sample, user and downloads. Do not change the code.

   C'est cette étape qui fait d'elle la **propriétaire**. Elle a alors accès à tout, y compris l'assistant intégré.
   *Si son Claude répond qu'il ne peut pas publier avec ces capacités* : l'ouvrir depuis Claude Code sur le web (claude.ai/code, inclus dans Pro), puis faire la même demande. C'est ainsi que l'artefact actuel a été créé. Il faut que ce soit son compte qui publie, pas le tien.

3. **Ouvrir l'artefact** à partir du lien donné. Au premier « Sort it », Claude demande l'autorisation d'utiliser son compte : elle choisit **Allow**.

4. **Brancher les conversations.** Elle copie le lien de l'artefact, ouvre `project-instructions.md`, remplace `PASTE-THE-LINK-HERE` par ce lien, puis colle le tout dans Projet → Instructions.

5. **Personnaliser.** Dans l'application : roue dentée → *What the assistant should know about me* (horaires, jours à l'UNIL, moments de la journée où elle est disponible). Les zones protégées sont *Studies* et *Me* par défaut.

6. **Sur son téléphone.** Elle ouvre le lien dans le navigateur, connectée à son compte, puis l'ajoute à l'écran d'accueil (Partager → Sur l'écran d'accueil).

## Tester avant l'usage quotidien (5 minutes)
- **Quick add** : coller *« Buy milk and nappies, I already sent the university email, review my UNIL notes on Thursday, and I need to think about organising the entrance. »* → Sort it. On attend 2 achats, 1 chose déjà faite, 1 révision prévue jeudi (pas une date limite) et 1 idée dans *Keep in mind*.
- **Conversation** : dans une nouvelle conversation du projet, écrire *« Add: call the paediatrician tomorrow »*, puis vérifier dans l'application (onglet Today de demain, ou Plans → Joud).
- **Fermer et rouvrir** : ce qui a été coché doit rester coché.

## À savoir
- Les données de ton artefact actuel ne passent pas automatiquement chez elle. Elles ne contiennent que des tâches d'essai, donc on repart de zéro. Si besoin : *Settings → Download a copy* sur un compte, puis *Import a copy* sur l'autre.
- La tâche programmée qui triait ses notes toutes les heures sur ton compte n'est plus utile : en tant que propriétaire, l'assistant répond directement chez elle. Une note que l'assistant ne peut pas trier reste enregistrée sous *Saved, not sorted yet*. Elle peut aussi demander à Claude dans le projet : *« Sort my saved notes »*.
- Pas de notifications sur le téléphone : un artefact ne peut pas en envoyer. Les vrais rappels (rendez-vous) vont dans le calendrier du téléphone.
