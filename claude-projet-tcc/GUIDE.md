# Superviseur TCC dans un projet Claude — mode d'emploi

**Un projet séparé** de votre projet « Note clinique EPFL » : les deux superviseurs (IPB et TCC) ont chacun leur « Document 2 » par défaut ; dans un même projet, l'IA ne saurait pas lequel produire.

1. claude.ai → **Projets** → **Créer un projet** → nom : `Supervision TCC`.
2. **Instructions du projet** → collez **tout** le contenu de `instructions.txt`.
3. **Connaissances du projet** → **+** → **Charger** → les **3 fichiers** du dossier `fichiers/` :
   - `TCC-document-maitre.md` (votre document, inchangé)
   - `10-analyse-ipb.md` (règles générales partagées et notions IPB pour la passerelle)
   - `11-reperes-ipb.md` (votre synthèse du livre IPB, pour la passerelle)
4. Paramètres : mémoire désactivée ou limitée au projet ; recherche web activée (CIM-10).

## Utilisation

- Un patient = une nouvelle conversation dans le projet ; notes anonymisées.
- **Format court** : collez une situation ou posez une question (« Analyse cette situation : … »).
- **Format long** : collez les notes d'entretien en précisant la séance (« Séance 2 : … »).

## Retour sur vos interventions

Notez vos interventions importantes **avec vos mots**, et la réaction du patient. Chaque réponse se termine alors par « Retour sur vos interventions » : ce que vous avez fait, comment ça s'appelle (TCC, IPB ou commun), critique, comment faire, puis votre posture.

## Quand vous mettez le document à jour

Remplacez seulement `TCC-document-maitre.md` dans les Connaissances (supprimer l'ancien, charger le nouveau). Les instructions ne changent pas.

## Confidentialité

Le document maître TCC résume les cours du MAPP et `11-reperes-ipb.md` le livre IPB : ils ne sont pas publiés sur GitHub. Ne partagez pas ce projet.
