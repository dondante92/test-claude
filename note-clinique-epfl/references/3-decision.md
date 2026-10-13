# Étape 3 — Décision : diagnostic, compartiment, branches

> Le diagnostic commande le contenu. Les décisions se prennent **ici, une fois, avant d'écrire** : à l'étape 4, l'IA ne choisit plus de branche.
> Texte de référence : `3-compartiments.md` (votre section VIII, mot pour mot). Version exécutable : `scripts/regles.json` (sections `compartiments` et `couplage_evolution_issue`).

## Ce que l'étape produit

Une proposition, que le clinicien **valide ou corrige** :

| Décision | Proposition | Arguments (renvoi à la fiche) |
|---|---|---|
| Diagnostic de la note (provisoire) | intitulé + code | … |
| Diagnostic de la synthèse (final) | intitulé + code, sous-type examiné | … |
| Compartiment | un parmi les six ci-dessous | … |
| Plan chronique | aucune / A / B / C / D | … |
| Branche diagnostique, paragraphes supplémentaires | … | … |
| Branche d'évolution | … | symptômes persistants / amendés de la fiche |
| Branche d'issue | … | indication, souhait, orientation réalisée |

Puis on remplit `decision` dans `fiche.json` et on relance `python3 scripts/controle.py fiche fiche.json`. **Une combinaison incohérente est refusée avant la rédaction.**

## Les six compartiments

| Compartiment (`regles.json`) | Plan chronique | Branche diagnostique | Supplémentaire | Évolution | Issue |
|---|---|---|---|---|---|
| `adaptation_seul` : trouble de l'adaptation seul | **aucun** | 2 ou 3 | (1, 6) | selon fiche | selon couplage |
| `code_z` : code Z ou difficulté circonscrite | A | 5 (ou 6) | (1, 6) | 6 | 3 ou 5 |
| `adaptation_traits` : avec accentuation de traits | B, sans nommer le registre | 2 ou 3 | **2**, registre nommé | 2 | fondée sur les difficultés persistantes (1, 7) |
| `personnalite` : trouble de la personnalité | B, portant les critères | 4 si principal | **3** si second | 2 | — |
| `neurodev` : hypothèse neurodéveloppementale | C, plaintes formulées seulement | selon tableau | **4** si écartée, **5** si poursuivie | selon fiche | selon couplage |
| `non_conclusif` : non conclusive ou interrompue | seulement si éléments durables | 6 ou 7 | — | 7 | 6 |

## Couplage évolution → issue (votre section VII, paragraphe 3)

| Évolution | Issue compatible |
|---|---|
| 1 favorable : symptômes amendés, fonctionnement repris | pas d'indication formelle (± souhait du patient) : 2, 3, 4, 5 |
| 2 partiellement favorable : symptomatologie résiduelle | psychothérapie indiquée : 1 |
| 4 défavorable, 5 absence d'amélioration | poursuite du suivi : 7 |
| 6 code Z | pas d'indication ± proposition ciblée : 3, 5 |
| 7 interruption | 6 |

Contrôles ajoutés par le script, tous issus de vos règles :
- évolution 2 sans aucun élément `persistant` dans la fiche → refusée (filtre 3 : « on n'invente pas Y ») ;
- issue 1 sans élément persistant ou sans `indication_psychotherapie` → refusée ;
- issue 2 = souhait **sans** indication formelle ;
- issue 1 ou 2 → `orientation_realisee` doit être vrai (« ne pas mentionner un acte qui n'a pas été réalisé ») ;
- issue 3 → aucune mention d'orientation ;
- trouble de l'adaptation en code générique → rappel : sous-types examinés ?

## Diagnostic de la note et diagnostic de la synthèse (votre texte)

DIAGNOSTIC DE LA NOTE ET DIAGNOSTIC DE LA SYNTHÈSE — Le diagnostic de la note est celui du premier entretien ; celui de la synthèse est celui du terme de l'évaluation. Ils peuvent différer, et cet écart est légitime : il traduit le travail de l'investigation, pas une incohérence. Quand l'évaluation se poursuit au-delà du premier entretien, la mention du caractère provisoire est obligatoire dans la note — le diagnostic n'y figure jamais comme une conclusion. La structure de la note suit le diagnostic final (compartiment), tandis que sa rubrique diagnostique porte le diagnostic provisoire. Ces deux exigences ne s'opposent pas : le compartiment détermine ce qui est développé, la rubrique enregistre où en était le raisonnement. Un écart entre les deux diagnostics est vérifié avant restitution : est-il temporel — l'évaluation a précisé le tableau — ou contradictoire ? S'il est contradictoire, il est signalé.

## Code CIM-10

Code et intitulé vérifiés dans une source officielle (CIM-10-GM de l'OFS en priorité, sinon navigateur OMS). Si l'IA n'a pas accès au web, elle propose et **le clinicien confirme le code** : elle ne le présente jamais comme vérifié.
