# Arbitrages

Le système applique exactement ce qui est décidé ici. Il y a trois catégories de points :
- **déjà tranchés** par votre version la plus récente (`Document_sans_titre_3`) : rien à faire ;
- **appliqués provisoirement** par moi : à confirmer ou corriger ;
- **ouverts** : votre décision est nécessaire.

Pour changer une règle : modifier `scripts/regles.json` (règles mécaniques) ou le fichier de `references/` concerné (règles de rédaction).

---

## Déjà tranchés par votre dernière version (conservés tels quels)

| Sujet | Anciennes versions | Retenu (dernière version) |
|---|---|---|
| Motif | 2-3 mots, jamais « consulte parce que » | « Le patient / La patiente consulte pour … / dans un contexte de … » |
| Abréviations | « aucun sigle » | Règle nuancée : on développe ce qui est opaque (sigles diagnostiques, filières abrégées), on garde les noms usuels (EPFL, CHUV, instruments, codes) |
| Différentiel | dans la rubrique CIM-10 | dans « Hypothèses », jamais dans la rubrique CIM-10 |
| Niveau d'activation | dans le status | jamais dans le status |
| Information manquante | « ne jamais écrire non mentionné, omettre » | question préalable, ou champ visiblement en attente ; jamais de phrase amputée ni de formulation neutre |
| Correction d'un texte | raccourcir, alléger | règle de non-suppression ; le doute profite au texte soumis |

---

## Appliqués provisoirement : à confirmer

**A1. Status : items non mentionnés.**
Votre note manuscrite dit « si ce n'est pas mentionné, on considère normal, les 12 points toujours ». Votre principe prioritaire dit « le status reflète le tableau, ne pas neutraliser par confort ».
→ **Appliqué** : les 12 items sont toujours rédigés. Un item non mentionné est normal, **sauf** la thymie, l'appétit, le sommeil et l'anxiété, qui reprennent ce que le plan aigu documente. L'idéation suicidaire n'est jamais déduite : non explorée → question bloquante.
☐ OK  ☐ À modifier : …

**A2. « Il/Elle exclut toute autre symptomatologie aiguë. »**
Dernière version : systématique. Version intermédiaire : seulement si réellement exploré.
→ **Appliqué** : systématique, comme dans votre dernière version. Le script avertit seulement si elle manque.
☐ OK  ☐ Seulement si exploré

**A3. Note de fin du premier entretien.**
Votre ajout manuscrit, sans place définie.
→ **Appliqué** : dernière phrase de la rubrique « Hypothèses diagnostiques et suite proposée », avec vos formulations d'adhésion de l'ancienne annexe (acceptation, nuance, ambivalence, indécision, réflexion, refus).
☐ OK  ☐ Rubrique séparée

**A5. Encodage Latin-1.**
Les anciennes versions retiraient tous les accents (« ideation », « therapeutique »). Or le Latin-1 **contient** é, è, à, ç, ô et « ».
→ **Appliqué** : le script garde les accents et remplace seulement ’ “ ” … — – œ et les espaces spéciaux.
☐ **À tester une fois** : coller dans le logiciel du dossier un texte passé par `nettoie`. Si les accents posent vraiment problème, utiliser l'option `--sans-accents`.

**A6. Champs « en attente » ou « omis ».**
Voir la section `champs` de `scripts/regles.json`. Par exemple : faut-il vraiment une question si la fratrie ou le lieu de naissance manquent, ou peut-on les omettre ?
☐ OK tel quel  ☐ Modifications : …

**A7. Relecture « dans une nouvelle conversation ».**
Dans un skill, tout se passe dans la même conversation. La vérification (étape 7) y est donc une étape séparée, après le contrôle automatique.
→ Pour une vraie relecture indépendante : coller la note finale et la fiche dans une nouvelle conversation en demandant seulement l'étape 7.

**A11. La « contrebalance ».**
J'ai compris la confrontation compréhension ↔ note dans les deux sens (votre étape 2). Si vous pensiez aussi à autre chose, comme la règle de non-suppression en contrepoids du filtre de pertinence, à me préciser.
☐ OK  ☐ Préciser : …

**A12. Nouveau compartiment « trouble chronique constitué » (proposé après le premier cas réel).**
Aucun des six compartiments ne couvre un trouble constitué ancien hors personnalité et neurodéveloppement (trichotillomanie, trouble obsessionnel-compulsif, trouble anxieux ancien…).
→ **Ajouté provisoirement** dans `scripts/regles.json` (`trouble_chronique`) : note avec plan chronique branche D ; plan aigu = ce qui a changé récemment ; synthèse branche diagnostique 1. À ne pas écrire : présenter la majoration récente comme le début du trouble.
☐ OK  ☐ À modifier : …

**A13. Nombre de séances.** Passé de « bloquant » à « en attente » : il ne sert qu'à la note de fin et à la synthèse.
☐ OK

---

## Ouverts : votre décision est nécessaire

**A9. Relevé de données et supervision IPB (hors de cette version 1, pour information).**
Le relevé de données **déduit** (« si rien → non »), alors que la note **n'invente jamais**. C'est légitime pour un usage statistique, à condition que ce soit un outil séparé avec ses propres règles. La supervision IPB (Document 2) est un outil pédagogique : un skill à part, avec les textes de référence joints.

---

## Tranchés par vous

| # | Sujet | Décision |
|---|---|---|
| A4 | « stress / fonctionnement / retentissement académique » | « retentissement académique » est gardé (il est dans le répertoire). « stress académique » devient « stress lié aux études ». « fonctionnement académique », « anxiété / pression / épuisement académique » sont interdits (contrôlés par le script). |
| A8 | Notes de suite | Module à part, traité séparément. Le choix entre format court et format de transmission se fera à ce moment-là. |
| A10 | Vérification CIM-10 | Recherche en ligne **obligatoire** pour le code, l'intitulé **et les critères diagnostiques**, avant de retenir tout diagnostic. Sans accès web, le diagnostic reste en attente. |
| A14 | Notes de suite : idées suicidaires (note courte) | Mentionnées seulement s'il y avait des idées suicidaires au départ ou un risque à réévaluer (contrôlé par le script avec la fiche). |
| A15 | Note de transmission : psychodynamique | Juste milieu : les éléments nécessaires à la compréhension, sans formulation psychodynamique complète. Critère : la pertinence pour la continuité du suivi, pour que le collègue ne reparte pas de zéro. Nouvelle rubrique obligatoire « Éléments de compréhension pour la continuité du suivi ». |
| A16 | Note de transmission : forme | Chaque note de suite d'un patient transmis est écrite en régime de transmission. |
| A17 | Interface ChatGPT | Canvas ajouté : le texte final s'ouvre dans un panneau modifiable. |

**Appliqués provisoirement, à confirmer :**
- **A18.** Note de transmission : l'idéation suicidaire est mentionnée au status **à chaque entretien** (votre texte « régime de transmission »), même sans idées suicidaires au départ, parce que le collègue doit connaître le risque. ☐ OK ☐ Même règle que la note courte
- **A19.** Dans les briques de la note courte, « dynamiques relationnelles » est remplacé par « difficultés relationnelles », car vos dernières règles l'interdisent. ☐ OK
- **A20.** Relevé : mode de prise de rendez-vous des étudiants EPFL = « mail EPFL » (votre règle), alors que le formulaire propose aussi « EPFL : mail via guichet ». ☐ OK ☐ mail via guichet
- **A21.** Relevé : l'identité (nom, prénom, date de naissance) reste vide par défaut, on colle l'étiquette, pour ne pas envoyer l'identité à l'IA. ☐ OK ☐ Remplir quand je fournis la photo
- **A22.** Relevé : situation économique d'un étudiant non doctorant laissée vide et demandée si elle n'est pas documentée (pas de « dépendance parents » supposée). ☐ OK

