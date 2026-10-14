#!/usr/bin/env python3
"""Contrôles mécaniques de la note du premier entretien, de la synthèse, des notes de suite et du Document 2.

Trois commandes :
  fiche   FICHE.json                               vérifie la fiche de faits et les décisions (étapes 2-3)
  texte   FICHIER --type note|synthese|suite-courte|suite-transmission|document2 [--fiche F]
                                                   vérifie un texte produit (étape 6, note de suite, ou Document 2)
  nettoie FICHIER [-o SORTIE] [--sans-accents]      rend le texte compatible Latin-1 (étape 6)

Les règles sont dans regles.json, à côté de ce script. Code de sortie 1 s'il reste une erreur.
Aucune dépendance : Python 3 standard.
"""
import argparse
import json
import pathlib
import re
import sys
import unicodedata

ICI = pathlib.Path(__file__).resolve().parent
ETATS = {"PRESENT", "ABSENT", "NON_EXPLORE"}


def charger_regles():
    return json.loads((ICI / "regles.json").read_text(encoding="utf-8"))


def plat(s):
    """Minuscules, sans accents, apostrophes droites, espaces simples : pour comparer."""
    s = s.replace("’", "'").replace("‘", "'").replace(" ", " ").replace(" ", " ")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()


class Rapport:
    def __init__(self):
        self.erreurs, self.avertissements, self.questions, self.attente = [], [], [], []

    def erreur(self, m):
        if m not in self.erreurs:
            self.erreurs.append(m)

    def avert(self, m):
        if m not in self.avertissements:
            self.avertissements.append(m)

    def afficher(self, titre):
        print(f"=== {titre} ===")
        for nom, liste in (("ERREURS (bloquantes)", self.erreurs),
                           ("QUESTIONS BLOQUANTES (à poser avant de rédiger)", self.questions),
                           ("CHAMPS EN ATTENTE (texte produit avec [À COMPLÉTER], question en fin)", self.attente),
                           ("AVERTISSEMENTS (à vérifier)", self.avertissements)):
            if liste:
                print(f"\n{nom} : {len(liste)}")
                for m in liste:
                    print(f"  - {m}")
        ok = not self.erreurs and not self.questions
        print("\nRÉSULTAT :", "CONFORME" if ok else "NON CONFORME")
        return 0 if ok else 1


# ---------------------------------------------------------------- fiche

def etat(fiche, cle):
    v = fiche.get(cle)
    return v.get("etat") if isinstance(v, dict) else None


def controler_fiche(fiche, regles, r, sans_decision=False, note_seule=False):
    # 1. États valides et règle NON_EXPLORE
    for cle, regle in regles["champs"].items():
        if cle.startswith("_"):
            continue
        e = etat(fiche, cle)
        if e is None:
            r.erreur(f"champ absent de la fiche : {cle}")
            continue
        if e not in ETATS:
            r.erreur(f"{cle} : état « {e} » invalide (PRESENT / ABSENT / NON_EXPLORE)")
            continue
        if e == "PRESENT" and not str(fiche[cle].get("valeur", "")).strip():
            r.erreur(f"{cle} : PRESENT mais sans valeur")
        if e != "NON_EXPLORE":
            continue
        if cle == "fin.idees_suicidaires" and (note_seule or etat(fiche, "aigu.idees_suicidaires") != "PRESENT"):
            continue  # seulement exigé si des idées suicidaires étaient présentes au départ
        if regle == "BLOQUANT":
            r.questions.append(cle)
        elif regle == "ATTENTE":
            r.attente.append(cle)

    # 2. Symptômes aigus : temporalité obligatoire, destin dans l'évolution
    symptomes = [s for s in fiche.get("aigu.symptomes", []) if s.get("libelle", "").strip()]
    if not symptomes:
        r.erreur("aigu.symptomes : aucun symptôme renseigné")
    for s in symptomes:
        if not s.get("depuis", "").strip():
            r.questions.append(f"temporalité du symptôme « {s['libelle']} » (aucun symptôme sans ancrage temporel)")
        if not sans_decision and not note_seule and s.get("etat_final") in (None, "", "non_documente"):
            r.avert(f"symptôme « {s['libelle']} » sans destin documenté dans l'évolution")

    # 3. Cohérences de base
    if etat(fiche, "antecedents.premiere_consultation") == "PRESENT" and etat(fiche, "antecedents.suivis") == "PRESENT":
        r.avert("première consultation en milieu psychiatrique ET suivi antérieur : vérifier la compatibilité (consultation généraliste ?)")
    if etat(fiche, "aigu.idees_suicidaires") != etat(fiche, "status.idees_suicidaires") \
            and "NON_EXPLORE" not in (etat(fiche, "aigu.idees_suicidaires"), etat(fiche, "status.idees_suicidaires")):
        r.avert("idées suicidaires : état différent entre plan aigu et status (rapporté ≠ observé ?)")

    # 4. Décisions (étape 3)
    if sans_decision:
        return
    d = fiche.get("decision", {})
    comp = d.get("compartiment", "")
    b = d.get("branches", {})
    table = regles["compartiments"]
    if comp not in table or comp.startswith("_"):
        r.erreur(f"compartiment « {comp} » inconnu : {', '.join(k for k in table if not k.startswith('_'))}")
        return
    c = table[comp]
    chron = b.get("chronique", "")
    if c["chronique"] and chron not in c["chronique"]:
        r.erreur(f"compartiment {comp} : plan chronique branche {c['chronique']} attendue, pas « {chron} »")
    if note_seule:
        controler_diagnostics(d, r)
        return
    if c["diagnostic"] and b.get("diagnostic") not in c["diagnostic"]:
        r.erreur(f"compartiment {comp} : branche diagnostique {c['diagnostic']} attendue, pas {b.get('diagnostic')}")
    supp = b.get("supplementaires", []) or []
    for s in supp:
        if s not in c["supp_permises"]:
            r.erreur(f"compartiment {comp} : paragraphe supplémentaire branche {s} non prévu (permises : {c['supp_permises']})")
    if c["supp_requises_une_de"] and not set(supp) & set(c["supp_requises_une_de"]):
        r.erreur(f"compartiment {comp} : paragraphe supplémentaire requis, branche parmi {c['supp_requises_une_de']}")
    if comp == "personnalite" and b.get("diagnostic") != 4 and 3 not in supp:
        r.erreur("trouble de la personnalité : branche diagnostique 4 (principal) ou supplémentaire 3 (second) requise")
    evo, issue = b.get("evolution"), b.get("issue")
    if c["evolution"] and evo not in c["evolution"]:
        r.erreur(f"compartiment {comp} : évolution branche {c['evolution']} attendue, pas {evo}")
    if c["issue"] and issue not in c["issue"]:
        r.erreur(f"compartiment {comp} : issue branche {c['issue']} attendue, pas {issue}")

    # 5. Couplage évolution -> issue et sources de l'issue
    couplage = regles["couplage_evolution_issue"]
    permis = couplage.get(str(evo))
    if permis and issue not in permis:
        r.erreur(f"couplage : évolution branche {evo} incompatible avec issue branche {issue} (attendu : {permis})")
    persistants = [s["libelle"] for s in symptomes if s.get("etat_final") == "persistant"] + \
                  [e["libelle"] for e in fiche.get("chronique.elements", []) if e.get("libelle", "").strip() and e.get("etat_final") == "persistant"]
    if evo == 2 and not persistants:
        r.erreur("évolution partiellement favorable sans aucun élément « persistant » dans la fiche : changer de branche ou documenter (filtre 3)")
    if evo == 1 and persistants:
        r.avert(f"évolution favorable alors que la fiche note des éléments persistants : {persistants}")
    if issue == 1 and not d.get("indication_psychotherapie"):
        r.erreur("issue branche 1 (psychothérapie indiquée) mais indication_psychotherapie = false")
    if issue == 1 and not persistants:
        r.erreur("indication de psychothérapie sans élément persistant documenté pour la fonder")
    if issue == 2 and (d.get("indication_psychotherapie") or not d.get("souhait_patient")):
        r.erreur("issue branche 2 : souhait du patient SANS indication formelle (vérifier les deux champs)")
    if issue in (1, 2) and not d.get("orientation_realisee"):
        r.erreur("issue branche 1/2 : « Un travail d'orientation a été réalisé » exige orientation_realisee = true")
    if issue == 3 and d.get("indication_psychotherapie"):
        r.erreur("issue branche 3 (absence d'indication) mais indication_psychotherapie = true")

    controler_diagnostics(d, r)


def controler_diagnostics(d, r):
    """Diagnostic provisoire / final, sous-type."""
    prov, fin = d.get("diagnostic_provisoire", {}), d.get("diagnostic_final", {})
    if not fin.get("code") or not fin.get("intitule"):
        r.questions.append("diagnostic final : code et intitulé CIM-10 (vérifiés dans une source officielle)")
    if prov.get("code") and fin.get("code") and prov["code"] != fin["code"] and not d.get("evaluation_poursuivie"):
        r.avert("diagnostic de la note ≠ diagnostic de la synthèse sans évaluation poursuivie : écart temporel ou contradictoire ?")
    if fin.get("code", "").strip().upper() in ("F43.2", "F43.20"):
        r.avert("trouble de l'adaptation en code générique : sous-types examinés (F43.21 à F43.25, F43.28) ?")


# ---------------------------------------------------------------- texte

def detecter_rubriques(lignes, rubriques):
    """Retourne la liste (index_rubrique, numéro_de_ligne) des titres reconnus, dans l'ordre du texte."""
    vus = []
    for n, ligne in enumerate(lignes):
        p = plat(ligne).strip(" :#*-_")
        if not p or len(p) > 60:
            continue
        for i, rub in enumerate(rubriques):
            noms = [plat(rub["nom"])] + [plat(a) for a in rub["alias"]]
            if p in noms:
                vus.append((i, n))
                break
    return vus


def contenu_rubrique(lignes, vus, i):
    for k, (idx, n) in enumerate(vus):
        if idx == i:
            fin = vus[k + 1][1] if k + 1 < len(vus) else len(lignes)
            return "\n".join(lignes[n + 1:fin])
    return ""


def controler_commun(texte, regles, r):
    p = plat(texte)
    for niveau, table in ((r.erreur, regles["interdits"]), (r.avert, regles["avertissements"])):
        for expr, conseil in table.items():
            if not expr.startswith("_") and re.search(r"\b" + re.escape(plat(expr)) + r"\b", p):
                niveau(f"« {expr} » → {conseil}")
    # Résidus du canevas
    residus = {r"\[(?!À COMPLÉTER)": "crochet de canevas", r"[{}]": "accolade de menu", r"…|\.\.\.": "pointillés",
               r"\b(?:il/elle|Il/Elle|le/la|Le/La|lui/elle|désireux/désireuse)\b": "alternative non tranchée",
               r"\(e\)|\(s\)": "accord non tranché", r"\bBranche [0-9A-D]\b": "nom de branche", r"⟨ajout⟩": "marque d'instruction"}
    for motif, nom in residus.items():
        for m in re.finditer(motif, texte):
            extrait = texte[max(0, m.start() - 25):m.end() + 25].replace("\n", " ")
            r.erreur(f"résidu du canevas ({nom}) : « …{extrait}… »")
    for m in re.finditer(r"\[À COMPLÉTER[^\]]*\]", texte):
        r.attente.append(m.group(0))
    # Sigles
    autorises = set(regles["sigles_autorises"])
    diag = set(regles["sigles_diagnostiques"])
    # les lignes de titre en majuscules ne sont pas des sigles
    corps = "\n".join(l for l in texte.splitlines()
                      if sum(c.isupper() for c in l) < 0.6 * max(1, sum(c.isalpha() for c in l)))
    for m in re.finditer(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*\b", corps):
        s = m.group(0)
        if len(re.sub(r"[^A-Z]", "", s)) < 2 or s in autorises or re.fullmatch(r"[A-Z]\d{2}(\.\d+)?", s):
            continue
        if s in diag:
            r.erreur(f"sigle « {s} » : écrire en toutes lettres")
        else:
            r.avert(f"abréviation « {s} » : nom usuel (garder) ou opaque (développer) ?")
    # Phrases très longues
    for phrase in re.split(r"(?<=[.!?])\s+|\n", texte):
        if len(phrase.split()) > 55:
            r.avert(f"phrase de {len(phrase.split())} mots : une information par phrase ? « {phrase[:70]}… »")


def controler_note(texte, regles, fiche, r):
    lignes = texte.splitlines()
    rubriques = regles["rubriques_note"]
    vus = detecter_rubriques(lignes, rubriques)
    presents = [i for i, _ in vus]
    is_ou_geste = fiche is not None and "PRESENT" in (etat(fiche, "aigu.idees_suicidaires"), etat(fiche, "antecedents.geste_suicidaire"))
    for i, rub in enumerate(rubriques):
        oblig = rub["obligatoire"]
        if oblig == "si_idees_ou_geste":
            oblig = is_ou_geste
            if fiche is None:
                r.avert("sans fiche, impossible de savoir si l'évaluation du risque suicidaire est requise")
        if oblig and i not in presents:
            r.erreur(f"rubrique manquante : {rub['nom']}")
    if presents != sorted(presents):
        r.erreur("rubriques dans le désordre : " + " → ".join(rubriques[i]["nom"] for i in presents))
    if len(set(presents)) != len(presents):
        r.erreur("rubrique en double")

    apa = plat(contenu_rubrique(lignes, vus, 1))
    if apa and not apa.startswith("il s'agit d"):
        r.erreur("affection actuelle : la phrase d'ouverture doit commencer par « Il s'agit d'un étudiant / d'une étudiante de … ans »")
    if apa and "sur le plan aigu" not in apa:
        r.erreur("affection actuelle : « Sur le plan aigu » absent")
    if apa and "exclut toute autre symptomatologie aigue" not in apa:
        r.avert("affection actuelle : clôture « exclut toute autre symptomatologie aiguë » absente")
    if fiche is not None:
        chron = fiche.get("decision", {}).get("branches", {}).get("chronique", "")
        if chron == "aucune" and "sur le plan chronique" in apa:
            r.erreur("compartiment sans plan chronique (trouble de l'adaptation seul) mais « Sur le plan chronique » présent")
        if chron in ("A", "B", "C", "D") and "sur le plan chronique" not in apa:
            r.erreur(f"plan chronique branche {chron} attendu mais absent")

    status = plat(contenu_rubrique(lignes, vus, 5))
    if status:
        manquants = [item for item, cles in regles["items_status"].items()
                     if not item.startswith("_") and not any(plat(c) in status for c in cles)]
        if manquants:
            r.erreur("status : items manquants (12 attendus) : " + ", ".join(manquants))
        if "activation" in status:
            r.erreur("status : le niveau d'activation ne figure jamais dans le status")

    diag = plat(contenu_rubrique(lignes, vus, 8))
    if diag and fiche is not None and fiche.get("decision", {}).get("evaluation_poursuivie") \
            and not any(m in diag for m in ("provisoire", "hypothese", "a preciser")):
        r.erreur("diagnostic CIM-10 : l'évaluation se poursuit, le caractère provisoire doit être mentionné")
    if diag and re.search(r"diff[ée]rentiel", diag):
        r.erreur("diagnostic CIM-10 : pas de différentiel dans cette rubrique (il va dans Hypothèses)")
    controler_commun(texte, regles, r)


def controler_synthese(texte, regles, fiche, r):
    paras = [p.strip() for p in re.split(r"\n\s*\n", texte) if p.strip()]
    if not paras:
        r.erreur("texte vide")
        return
    if paras[-1] != "Nous nous tenons à sa disposition.":
        r.erreur("la dernière ligne doit être, seule : « Nous nous tenons à sa disposition. »")
    corps = paras[:-1]
    if not 4 <= len(corps) <= 5:
        r.avert(f"{len(corps)} paragraphes avant la phrase finale (4 attendus, 5 si un second diagnostic est discuté)")
    if not re.match(r"(Le patient|La patiente) a bénéficié d", paras[0]):
        r.erreur("paragraphe 1 : moule « Le patient / La patiente a bénéficié d'une … »")
    p = plat(texte)
    if "sur le plan diagnostique" not in p and "les elements recueillis" not in p:
        r.erreur("paragraphe diagnostique absent (« Sur le plan diagnostique » / « Les éléments recueillis »)")
    if "au cours du suivi" not in p and "le suivi ayant ete interrompu" not in p:
        r.erreur("paragraphe d'évolution absent (« Au cours du suivi » / « Le suivi ayant été interrompu »)")
    if fiche is not None:
        d = fiche.get("decision", {})
        evo, issue = d.get("branches", {}).get("evolution"), d.get("branches", {}).get("issue")
        if evo == 1 and "partiellement favorable" in p:
            r.erreur("fiche : évolution favorable ; texte : partiellement favorable")
        if evo == 2 and "partiellement favorable" not in p and "amelioration partielle" not in p:
            r.erreur("fiche : évolution partiellement favorable ; le texte ne le dit pas")
        if issue == 3 and "orientation" in p:
            r.erreur("absence d'indication : aucune mention d'orientation")
        if "orientation a ete realise" in p and not d.get("orientation_realisee"):
            r.erreur("« travail d'orientation réalisé » alors que la fiche ne le documente pas")
        if etat(fiche, "aigu.idees_suicidaires") == "PRESENT" and "suicidaire" not in p:
            r.erreur("idées suicidaires initialement présentes : passage obligatoire dans l'évolution")
        code = d.get("diagnostic_final", {}).get("code", "")
        if code and code not in texte:
            r.avert(f"code du diagnostic final ({code}) absent du texte")
    controler_commun(texte, regles, r)


def mentionne_idees_suicidaires(texte):
    p = plat(texte)
    return "ideation suicidaire" in p or "idees suicidaires" in p


def controler_suite_courte(texte, regles, fiche, r):
    phrases = [x for x in re.split(r"(?<=[.!?])\s+", texte.strip()) if x.strip()]
    if len(phrases) > 8:
        r.avert(f"note courte de {len(phrases)} phrases : 2 à 6 attendues ; sinon, régime de transmission ?")
    vus = detecter_rubriques(texte.splitlines(), regles["rubriques_suite_transmission"])
    if vus:
        r.erreur("note courte : pas de titres de rubriques (réservés à la note de transmission)")
    if not re.search(r"entretien|ne s'est pas présenté|ne s’est pas présenté", texte, re.I):
        r.avert("note courte : le cadre de l'entretien n'est pas indiqué")
    if fiche is not None and etat(fiche, "aigu.idees_suicidaires") != "PRESENT" and mentionne_idees_suicidaires(texte):
        r.erreur("note courte : idées suicidaires mentionnées alors qu'il n'y en avait pas au départ (règle du 14.10.2026)")
    if fiche is not None and etat(fiche, "aigu.idees_suicidaires") == "PRESENT" and not mentionne_idees_suicidaires(texte):
        r.erreur("note courte : idées suicidaires présentes au départ, réévaluation à mentionner")
    controler_commun(texte, regles, r)


def controler_suite_transmission(texte, regles, fiche, r):
    lignes = texte.splitlines()
    rubriques = regles["rubriques_suite_transmission"]
    vus = detecter_rubriques(lignes, rubriques)
    presents = [i for i, _ in vus]
    for i, rub in enumerate(rubriques):
        if rub["obligatoire"] and i not in presents:
            r.erreur(f"note de transmission : rubrique manquante : {rub['nom']}")
    if presents != sorted(presents):
        r.erreur("note de transmission : rubriques dans le désordre")
    status = contenu_rubrique(lignes, vus, 4)
    if status and not mentionne_idees_suicidaires(status):
        r.erreur("note de transmission : le status mentionne l'idéation suicidaire à chaque entretien")
    comprehension = contenu_rubrique(lignes, vus, 3)
    if comprehension and len(comprehension.split()) < 15:
        r.avert("éléments de compréhension très courts : suffisent-ils pour que le collègue ne reparte pas de zéro ?")
    controler_commun(texte, regles, r)


# ---------------------------------------------------------------- Document 2 (analyse IPB)

PUCE = re.compile(r"^\s*(?:[-•*]|\d+[.)])\s+")


def intitule(ligne):
    """Une ligne courte sans ponctuation finale est un intitulé (sous-titre)."""
    l = ligne.strip()
    if not l or PUCE.match(l) or len(l.split()) > 8 or re.search(r"[.!?…»)\"]$", l):
        return None
    return plat(l.strip("#*_ :").rstrip(":"))


def controler_document2(texte, regles, fiche, r):
    d = regles["document2"]
    if not texte.strip():
        r.erreur("Document 2 vide")
        return
    p = plat(texte)
    for niveau, table in ((r.erreur, d["interdits"]), (r.avert, d["avertissements"])):
        for expr, conseil in table.items():
            if not expr.startswith("_") and re.search(r"\b" + re.escape(plat(expr)) + r"\b", p):
                niveau(f"« {expr} » → {conseil}")
    premier_bloc, puces = None, 0
    for n, ligne in enumerate(texte.splitlines()):
        h = intitule(ligne)
        if h is not None:
            if any(h.startswith(b) for b in d["blocs_autorises"]):
                premier_bloc = n if premier_bloc is None else premier_bloc
            else:
                r.erreur(f"sous-titre « {ligne.strip()} » : le corps est un texte continu ; seuls trois blocs finaux "
                         "(volet psychiatrique, préparation du prochain entretien, réflexivité)")
        elif PUCE.match(ligne) and premier_bloc is None:
            puces += 1
    if puces:
        r.avert(f"{puces} ligne(s) en liste dans le corps : texte continu attendu (listes admises seulement dans les blocs finaux)")
    if re.search(r"\bFDG\b\s*(?:de|=|:|à)?\s*\d", texte) or re.search(r"\bitems?\s+\d+", texte, re.I):
        r.avert("cotation chiffrée (FDG, numéro d'item) : impossible sans verbatim ; écrire le niveau en mots")
    mots = len(texte.split())
    if mots > d["longueur_max_mots"]:
        r.avert(f"{mots} mots : peut-il être lu en entier ? (repère : {d['longueur_max_mots']})")


# ---------------------------------------------------------------- nettoie

def nettoyer(texte, regles, sans_accents=False):
    for a, b in regles["typographie"].items():
        if not a.startswith("_"):
            texte = texte.replace(a, b)
    if sans_accents:
        texte = "".join(c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c))
    restants = sorted({c for c in texte if ord(c) > 255})
    return texte, restants


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fiche")
    f.add_argument("fiche")
    f.add_argument("--sans-decision", action="store_true", help="étape 2 : contrôler les faits seulement, avant les décisions")
    f.add_argument("--note-seule", action="store_true", help="note du premier entretien seule : pas de contrôle évolution / issue")
    t = sub.add_parser("texte")
    t.add_argument("fichier")
    t.add_argument("--type", choices=["note", "synthese", "suite-courte", "suite-transmission", "document2"], required=True)
    t.add_argument("--fiche")
    n = sub.add_parser("nettoie")
    n.add_argument("fichier")
    n.add_argument("-o", "--sortie")
    n.add_argument("--sans-accents", action="store_true", help="seulement si le logiciel de dossier refuse vraiment les accents")
    a = ap.parse_args()
    regles = charger_regles()
    r = Rapport()

    if a.cmd == "fiche":
        fiche = json.loads(pathlib.Path(a.fiche).read_text(encoding="utf-8"))
        controler_fiche(fiche, regles, r, a.sans_decision, a.note_seule)
        sys.exit(r.afficher("CONTRÔLE DE LA FICHE ET DES DÉCISIONS"))

    texte = pathlib.Path(a.fichier).read_text(encoding="utf-8")
    if a.cmd == "nettoie":
        propre, restants = nettoyer(texte, regles, a.sans_accents)
        if a.sortie:
            pathlib.Path(a.sortie).write_text(propre, encoding="latin-1", errors="replace")
            print(f"Écrit en Latin-1 : {a.sortie}")
        else:
            sys.stdout.write(propre)
        if restants:
            print("\nCaractères hors Latin-1 restants : " + " ".join(f"{c!r} (U+{ord(c):04X})" for c in restants), file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    fiche = json.loads(pathlib.Path(a.fiche).read_text(encoding="utf-8")) if a.fiche else None
    {"note": controler_note, "synthese": controler_synthese, "suite-courte": controler_suite_courte,
     "suite-transmission": controler_suite_transmission, "document2": controler_document2}[a.type](texte, regles, fiche, r)
    sys.exit(r.afficher(f"CONTRÔLE DU TEXTE ({a.type})"))


if __name__ == "__main__":
    main()
