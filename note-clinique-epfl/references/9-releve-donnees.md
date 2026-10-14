# Relevé de données UNIL-EPFL

> Vos règles (« Fonction — relevé de données »), réorganisées pour être appliquées par étapes. Les ajouts sont signalés ⟨ajout⟩.
> Le remplissage du PDF est fait par `scripts/remplir_releve.py`, pas par l'IA : l'IA décide des **réponses**, le script les **écrit** sur le formulaire original, toujours au même endroit et de la même manière.

## Principe

Le relevé est la seule fonction où l'on **déduit** : l'objectif est de compléter le maximum de rubriques avec une déduction clinique et administrative raisonnable, sans multiplier les champs vides. C'est l'inverse des notes, où l'on n'invente rien : les deux règles ne se mélangent pas.

Ordre de priorité : **information explicite du dossier → déduction raisonnable → valeur par défaut**. Jamais d'information d'un autre patient ou d'une autre conversation.

## Procédure

1. **Rassembler** ce qui est dans la conversation : notes d'entretien, fiche de faits et décisions validées, note et synthèse. La fiche de faits est la source principale : le relevé reste ainsi cohérent avec la note.
2. **Remplir `releve.json`** (modèle : `scripts/releve_modele.json`, exemple : `exemples/releve_exemple.json`) :
   - `choix` : pour chaque rubrique à choix, **exactement** une des options du formulaire, écrite comme dans `releve_modele.json` ;
   - `textes` : nationalité, langue maternelle, section, nombre de consultations, diagnostics, code Z ;
   - `deductions` : pour chaque réponse **déduite** et non explicite, la raison en quelques mots. Elles seront montrées au clinicien.
   - Ne pas mettre les rubriques qui ont une valeur par défaut, sauf si le dossier dit autre chose : le script les applique.
3. **Lancer** : `python3 scripts/remplir_releve.py releve.json -o releve_rempli.pdf --defauts --apercu`
4. **Corriger** les erreurs signalées (option inexistante, rubrique conditionnelle incohérente) et relancer.
5. **Vérifier visuellement** les deux pages de l'aperçu.
6. **Restituer** le PDF, puis la liste que le script affiche : valeurs par défaut appliquées, déductions, rubriques laissées vides, données en attente de documents. Poser en un seul bloc les questions pour les rubriques vides.

## Identité et dates : jamais déduites

Nom, prénom, date de naissance, date de première consultation, date de dernière consultation : **uniquement** depuis une photographie, un document ou une donnée explicitement fournie. Sinon, laissées vides et signalées « en attente de documents ».

⟨ajout⟩ **Par défaut, l'identité reste vide et on colle l'étiquette** (le formulaire le prévoit : « Etiquette ou remplir »). Cela évite d'envoyer l'identité du patient à l'IA. Ne la remplir que si le clinicien le demande explicitement.

Le champ « Consultant(e) » reçoit le nom du clinicien, donné par lui.

## Règles de déduction (vos règles)

| Rubrique | Règle |
|---|---|
| Nationalité | Nationalité documentée ; sinon origine clairement indiquée (origine polonaise → polonaise). |
| État civil | Aucun mariage mentionné → célibataire. |
| Enfants | Aucun enfant mentionné → non. |
| Langue maternelle | Pays principal où le patient a grandi et fait sa scolarité, si le contexte est clair. |
| Langue de consultation | Langue documentée de l'entretien. |
| Nombre d'années en Suisse | Déduit du parcours académique et des dates d'arrivée (doctorant en dernière année → >5). |
| Situation économique | Doctorant EPFL → assistanat (assistant-doctorant), sauf information contraire. ⟨ajout⟩ Pour les autres étudiants, **seulement si documentée** : sinon laissée vide et demandée, sans supposer « dépendance parents ». |
| Situation d'échec actuelle | Aucune mentionnée → non. |
| Échecs antérieurs | Aucun mentionné → non. |
| Déplacement pour études | Arrivé de l'étranger pour ses études → étranger. |
| Mode de venue | Démarche spontanée sans autre orientation mentionnée → internet. |
| Mode de prise de rendez-vous | Contact spontané avec la consultation EPFL sans autre canal → mail EPFL. |
| Consultations antérieures en psychiatrie | Aucune rapportée → non ; si oui, le lieu quand il est connu. |
| Hospitalisation psychiatrique | Aucune rapportée → non. |
| Idées suicidaires | Aucune rapportée → absentes ; sinon idéation passive ou scénarisées selon leur nature. |
| Tentative de suicide | Aucun antécédent rapporté → non. |
| Abus d'alcool ou de substances | Aucune consommation problématique → non. Une consommation simple n'est pas un abus. |
| Prescription | Aucune prescription dans le cadre de la consultation → ∅. Un traitement des antécédents n'est pas une prescription. |
| Certificat, demande de certificat, attestation, liaison sur et hors campus, groupe d'indication DP, tests psychologiques, adressage en médecine, entretien avec la famille, demande CCF | Non, sauf si **effectivement documenté**. Envisagé n'est pas réalisé. |
| ⟨ajout⟩ Échange en cours | Aucun échange mentionné → non. |
| ⟨ajout⟩ Études | Consultation EPFL → EPFL, sauf étudiant UNIL documenté. |
| ⟨ajout⟩ Niveau d'études | Le niveau actuel : refait la première année après le cours de mise à niveau → bachelor ; en cours de mise à niveau → MAN. |

## Screening : l'exception

Le screening n'est **jamais déduit**. « Oui » seulement si un questionnaire a été **effectivement réalisé pour ce patient** : proposé, discuté ou envisagé ne compte pas. Jamais de PQ-16 ou de dépistage des prodromes par contamination entre dossiers. Si oui : cocher le type (TDAH, Prodromes, Asperger, Dys) et renseigner « avec symptômes » d'après le **résultat documenté**, jamais d'après le tableau clinique.

## Consultations et prise en charge

- Nombre de consultations : entretiens effectivement réalisés. ⟨ajout⟩ « Une seule consultation » est **calculée** par le script (1 → oui, sinon non) ; la raison n'est remplie que si oui.
- Type de travail (IP, IPB, IPB en cours) et décision : ceux qui ont réellement eu lieu.
- Diagnostic CIM-10 : celui retenu dans le dossier, jamais créé pour remplir le formulaire.
- Motif principal, contexte des études, difficultés relationnelles : d'après les éléments cliniques, dans les catégories du formulaire, **un seul choix** par rubrique.

## Ce que garantit le script

- Le PDF original (version LG du 06.08.2021, 2 pages) n'est jamais modifié : les réponses sont superposées.
- Écriture noire, non grasse, taille proche du formulaire, réduite seulement si le texte ne tient pas sur la ligne (sinon signalé « trop long »).
- Choix entourés d'un trait noir fin, centré, sans masquer le texte ; un seul choix par rubrique ; screening coché d'une croix.
- Refus de produire le PDF si une option n'existe pas dans le formulaire ou si une rubrique conditionnelle est incohérente.

## Point à confirmer par vous

⟨ajout⟩ **Mode de prise de rendez-vous** : le formulaire range « mail EPFL » sous « UNIL : » et propose aussi « EPFL : mail via guichet ». Votre règle dit « mail EPFL » ; elle est appliquée telle quelle. Si un étudiant EPFL devait plutôt être « mail via guichet », il suffit de me le dire.
