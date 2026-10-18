#!/usr/bin/env python3
"""Moteur du budget familial : état unique, cycles de salaire, semaines avec report, enveloppes,
position nette sans double comptage, projections et tableau de bord HTML.

L'état complet (paramètres, transactions, soldes, salaires, ajustements, prévus, règles du foyer)
vit dans un seul fichier : tableau-budget.html (ou etat.json). Le tableau de bord embarque l'état ;
il suffit donc de garder ce fichier et de le redonner avec les nouvelles captures.

Commandes :
  budget.py init        ETAT_INITIAL.json -o tableau-budget.html
  budget.py importer    ETAT nouvelles.json [-o SORTIE]     transactions et/ou soldes lus sur les captures
  budget.py appliquer   ETAT modifs.json    [-o SORTIE]     corrections, ajustements, prévus, salaires, règles, paramètres
  budget.py rapport     ETAT [--date AAAA-MM-JJ]            les 4 blocs du brief, en texte
  budget.py tableau     ETAT -o tableau-budget.html [--date]
  budget.py exporter    ETAT -o etat.json | transactions.csv
  budget.py test                                            tests de non-régression (spécification § 19)

Conventions : montant en CHF, signé comme sur le relevé (négatif = sortie). Dates AAAA-MM-JJ.
"""
import argparse
import copy
import csv
import datetime as dt
import hashlib
import html as html_mod
import json
import re
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
VERSION = 1
MARQUE_DEBUT = '<script id="etat-budget" type="application/json">'
MARQUE_FIN = "</script>"
STATUTS = {"comptabilise", "reservation", "estimation", "ordre", "annule", "remplace"}
ENVELOPPES_HORS_CONSO = {"flux", "revenu"}

PARAMETRES_DEFAUT = {
    "noms": {"moi": "Moi", "conjoint": "Conjoint·e", "enfant": "Enfant"},
    "budget_jour": 30.0,
    "budget_weekend": 200.0,
    "cibles_semaine": {"courses": 190.0, "perso_moi": 126.0},
    "enveloppe_enfant": 1000.0,
    "coussin_mensuel": 1000.0,
    "coussin_report": True,
    "report_entre_cycles": False,
    "argent_perso_conjoint": {"actif": False, "montant": 500.0},
    "salaire_normalise": 7700.0,
    "prochains_salaires": [],
    "jour_salaire_habituel": 25,
    "frais_change": 0.015,
    "limite_carte": 5000.0,
    "reserve_cible": 1000.0,
    "debut_suivi": None,
    "comptes_liquides": ["courant"],
    "comptes_epargne": [],
    "fixes": [],
    "abonnements_surveilles": [],
}


# ---------------------------------------------------------------- utilitaires

def normalise(texte):
    t = unicodedata.normalize("NFKD", str(texte or "")).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9&+.*' -]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def contient_mot(libelle_norm, mot):
    mot = normalise(mot)
    if not mot:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(mot) + r"(?![a-z0-9])", libelle_norm) is not None


MOTS_VIDES = {"achat", "paiement", "carte", "debit", "card", "twint", "e-commerce", "ecommerce", "pos", "samsung", "pay",
              "service", "shopping", "ligne", "prestation", "fil", "wfs", "sumup", "zettle",
              "cr", "dr", "ch", "sa", "ag", "gmbh", "sarl", "the", "de", "du", "la", "le", "www", "com"}


def cle_commercant(libelle):
    mots = [m for m in re.split(r"[ .*'-]+", normalise(libelle)) if len(m) >= 3 and m not in MOTS_VIDES
            and not m.isdigit()]
    return mots[0] if mots else normalise(libelle)[:8]


def d(s):
    return dt.date.fromisoformat(str(s)[:10])


def chf(x):
    s = f"{abs(x):,.2f}".replace(",", "'")
    return ("−" if x < 0 else "") + s


def arrondi(x):
    return round(float(x) + 0.0, 2)


def ident(tx, n=0):
    base = f"{tx.get('compte')}|{tx.get('date')}|{normalise(tx.get('libelle'))}|{tx.get('montant')}|{n}"
    return "t" + hashlib.sha1(base.encode()).hexdigest()[:10]


def nouvel_id(prefixe, contenu):
    return prefixe + hashlib.sha1((json.dumps(contenu, sort_keys=True, ensure_ascii=False)
                                   + dt.datetime.now().isoformat()).encode()).hexdigest()[:8]


# ---------------------------------------------------------------- état

def etat_vide():
    return {"version": VERSION, "mis_a_jour": None, "parametres": copy.deepcopy(PARAMETRES_DEFAUT),
            "transactions": [], "soldes": [], "salaires": [], "ajustements": [], "prevus": [],
            "regles": [], "journal": []}


def complete_etat(etat):
    base = etat_vide()
    for k, v in base.items():
        etat.setdefault(k, v)
    p = etat["parametres"]
    for k, v in PARAMETRES_DEFAUT.items():
        if k not in p:
            p[k] = copy.deepcopy(v)
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                p[k].setdefault(k2, v2)
    return etat


def charge_etat(chemin):
    chemin = Path(chemin)
    texte = chemin.read_text(encoding="utf-8")
    if chemin.suffix.lower() in (".html", ".htm"):
        i = texte.find(MARQUE_DEBUT)
        if i < 0:
            sys.exit(f"ERREUR : {chemin} ne contient pas d'état de budget.")
        j = texte.find(MARQUE_FIN, i)
        brut = texte[i + len(MARQUE_DEBUT):j]
        brut = brut.replace("<\\/", "</")
        etat = json.loads(brut)
        etat = etat.get("etat", etat)
    else:
        etat = json.loads(texte)
    return complete_etat(etat)


def charge_config():
    cats = json.loads((ICI / "categories.json").read_text(encoding="utf-8"))
    regles = json.loads((ICI / "regles_commercants.json").read_text(encoding="utf-8"))["regles"]
    return cats, regles


def label(texte, noms):
    return texte.replace("{moi}", noms.get("moi", "Moi")).replace("{conjoint}", noms.get("conjoint", "Conjoint·e")) \
        .replace("{enfant}", noms.get("enfant", "Enfant"))


def note_journal(etat, action, detail):
    etat["journal"].append({"quand": dt.datetime.now().isoformat(timespec="seconds"), "action": action,
                            "detail": detail})
    etat["journal"] = etat["journal"][-300:]


# ---------------------------------------------------------------- classement

def sens(tx):
    return "entree" if tx["montant"] > 0 else "sortie"


def regle_correspond(regle, tx, lib):
    si = regle.get("si", {})
    if "compte" in si and si["compte"] != tx.get("compte"):
        return False
    if "sens" in si and si["sens"] != sens(tx):
        return False
    m = abs(tx["montant"])
    if "montant_min" in si and m < si["montant_min"]:
        return False
    if "montant_max" in si and m > si["montant_max"]:
        return False
    if "montant_egal" in si and abs(m - si["montant_egal"]) > 0.01:
        return False
    if "contient" in si and not any(contient_mot(lib, mot) for mot in si["contient"]):
        return False
    if "contient_tous" in si and not all(contient_mot(lib, mot) for mot in si["contient_tous"]):
        return False
    return True


def classe(tx, etat, cats, regles_defaut):
    """Applique : correction manuelle > règle du foyer > règle par défaut > à vérifier."""
    if tx.get("manuel"):
        return tx
    lib = " " + normalise(" ".join(str(tx.get(k) or "") for k in ("libelle", "type_commerce", "type_operation"))) + " "
    choix = None
    for source, regles in (("foyer", etat.get("regles", [])), ("defaut", regles_defaut)):
        for r in sorted(regles, key=lambda r: -r.get("priorite", 50)):
            if r.get("actif", True) and regle_correspond(r, tx, lib):
                choix = (source, r)
                break
        if choix:
            break
    proposee = tx.get("categorie_proposee")  # ce que l'IA a lu / proposé sur la capture
    if choix:
        source, r = choix
        a = r["alors"]
        tx["categorie"] = a["categorie"]
        tx["sous_categorie"] = a.get("sous_categorie", tx.get("sous_categorie"))
        tx["beneficiaire"] = a.get("beneficiaire", tx.get("beneficiaire"))
        tx["enveloppe"] = a.get("enveloppe") or cats["categories"][a["categorie"]]["enveloppe"]
        tx["confiance"] = a.get("confiance", "haute" if source == "foyer" else "moyenne")
        tx["regle"] = r.get("id")
        if a.get("lien"):
            tx["lien"] = a["lien"]
        if a.get("note") and not tx.get("note"):
            tx["note"] = a["note"]
        if proposee and proposee != tx["categorie"] and tx["confiance"] != "haute":
            tx["confiance"] = "basse"
            tx["note"] = (tx.get("note") or "") + f" | IA propose « {proposee} »"
    elif proposee in cats["categories"]:
        tx["categorie"] = proposee
        tx["enveloppe"] = tx.get("enveloppe_proposee") or cats["categories"][proposee]["enveloppe"]
        tx["confiance"] = tx.get("confiance") or "basse"
        tx["regle"] = "ia"
    else:
        tx["categorie"] = "a_verifier"
        tx["enveloppe"] = "a_verifier"
        tx["confiance"] = "basse"
        tx["regle"] = None
    if tx.get("enveloppe_proposee") and tx.get("regle") != "ia":
        tx["enveloppe"] = tx["enveloppe_proposee"]
    p = etat["parametres"]
    if tx["categorie"] == "perso_conjoint" and p["argent_perso_conjoint"]["actif"] and not tx.get("enveloppe_proposee"):
        tx["enveloppe"] = "perso_conjoint"
    return tx


# ---------------------------------------------------------------- import (dédoublonnage)

def prepare(tx, p):
    tx = dict(tx)
    tx["date"] = str(tx["date"])[:10]
    tx.setdefault("compte", "courant")
    tx.setdefault("statut", "comptabilise")
    tx["libelle"] = str(tx.get("libelle", "")).strip()
    devise = (tx.get("devise") or "CHF").upper()
    tx["devise"] = devise
    if devise != "CHF" and tx.get("montant") is None:
        taux = tx.get("taux") or p.get("taux", {}).get(devise)
        if not taux:
            raise ValueError(f"Taux de change manquant pour {tx['libelle']} ({devise})")
        tx["montant"] = arrondi(float(tx["montant_devise"]) * float(taux) * (1 + p["frais_change"]))
        tx["montant"] = -abs(tx["montant"]) if float(tx["montant_devise"]) < 0 or tx.get("sortie", True) else tx["montant"]
        tx["statut"] = "estimation"
        tx["note"] = (tx.get("note") or "") + f" | estimé {tx['montant_devise']} {devise} × {taux} + {p['frais_change']*100:.1f} %"
    tx["montant"] = arrondi(tx["montant"])
    if tx["statut"] not in STATUTS:
        raise ValueError(f"Statut inconnu : {tx['statut']}")
    return tx


def proches(a, b, jours, tolerance):
    if a.get("compte") != b.get("compte"):
        return False
    if abs((d(a["date"]) - d(b["date"])).days) > jours:
        return False
    if cle_commercant(a["libelle"]) != cle_commercant(b["libelle"]):
        return False
    ma, mb = abs(a["montant"]), abs(b["montant"])
    return abs(ma - mb) <= max(0.05, tolerance * max(ma, mb)) and (a["montant"] < 0) == (b["montant"] < 0)


def importe(etat, lot, cats, regles_defaut):
    """lot = {"transactions": [...], "soldes": {...} | [...], "source": "capture du ..."}"""
    p = etat["parametres"]
    rapport = {"ajoutees": [], "doublons": [], "remplacees": [], "a_verifier": [], "soldes": 0, "debut_suivi": None}
    existantes = [t for t in etat["transactions"] if t["statut"] not in ("remplace",)]
    if not existantes and not p.get("debut_suivi") and lot.get("transactions"):
        premiere = min(d(t["date"]) for t in lot["transactions"])
        p["debut_suivi"] = (premiere - dt.timedelta(days=premiere.weekday())).isoformat()
        rapport_debut = p["debut_suivi"]
    else:
        rapport_debut = None
    stock = Counter((t["compte"], t["date"], normalise(t["libelle"]), t["montant"])
                    for t in existantes if t["statut"] in ("comptabilise", "reservation", "estimation", "ordre"))
    vus_lot = Counter()
    for brut in lot.get("transactions", []):
        tx = prepare(brut, p)
        cle = (tx["compte"], tx["date"], normalise(tx["libelle"]), tx["montant"])
        vus_lot[cle] += 1
        # 1. doublon exact (captures qui se chevauchent) : on ne compte que l'excédent
        if vus_lot[cle] <= stock[cle]:
            rapport["doublons"].append(tx)
            continue
        tx["origine"] = lot.get("origine", tx.get("origine", "capture"))
        jumeau = next((t for t in existantes if t["statut"] == "comptabilise" and tx["statut"] == "comptabilise"
                       and t.get("origine", "capture") != tx["origine"] and not t.get("_apparie")
                       and proches(t, tx, 3, 0.0)), None)
        if jumeau is not None:
            # même opération vue sur une capture et sur un relevé : le relevé (officiel) complète la capture
            jumeau["_apparie"] = True
            if tx["origine"] == "releve":
                jumeau.setdefault("historique", []).append({"libelle": jumeau["libelle"], "date": jumeau["date"],
                                                           "origine": jumeau.get("origine", "capture")})
                jumeau.update({k: tx[k] for k in ("libelle", "date", "type_commerce", "type_operation", "date_comptable")
                               if tx.get(k)} | {"origine": "releve"})
            rapport["doublons"].append(tx)
            continue
        # 2. réservation/estimation devenue définitive (ou reprise d'une ancienne capture)
        cible = None
        if tx["statut"] == "comptabilise":
            cands = [t for t in existantes if t["statut"] in ("reservation", "estimation", "ordre") and t.get("lot") != id(lot)
                     and proches(t, tx, 7, 0.15 if t["statut"] != "estimation" else 0.10)]
            if cands:  # la plus proche en montant, puis en date
                cible = min(cands, key=lambda t: (abs(abs(t["montant"]) - abs(tx["montant"])), abs((d(t["date"]) - d(tx["date"])).days)))
        elif tx["statut"] in ("reservation", "estimation"):
            # réservation renvoyée sur une ancienne capture alors qu'elle a déjà été finalisée
            deja = [t for t in existantes if t["statut"] == "comptabilise" and proches(t, tx, 10, 0.15)
                    and any(h.get("statut") == tx["statut"] and abs(abs(h.get("montant", 0)) - abs(tx["montant"])) < 0.01
                            for h in t.get("historique", []))]
            if deja:
                rapport["doublons"].append(tx)
                continue
        if cible is not None:
            cible.setdefault("historique", []).append({k: cible.get(k) for k in ("date", "montant", "statut", "libelle")}
                                                     | {"remplace_le": dt.date.today().isoformat()})
            cible.update({"montant": tx["montant"], "statut": "comptabilise", "date_comptable": tx["date"],
                          "libelle": tx["libelle"] or cible["libelle"]})
            if not cible.get("manuel"):
                classe(cible, etat, cats, regles_defaut)
            rapport["remplacees"].append(cible)
            continue
        # 3. nouvelle transaction
        tx["id"] = ident(tx, vus_lot[cle])
        while any(t["id"] == tx["id"] for t in etat["transactions"]):
            tx["id"] = ident(tx, vus_lot[cle] + 100 + len(etat["transactions"]))
        tx["source"] = lot.get("source", tx.get("source"))
        tx["lot"] = id(lot)
        classe(tx, etat, cats, regles_defaut)
        # un remboursement marchand hérite de la catégorie de l'achat d'origine
        if tx["montant"] > 0 and tx["categorie"] in ("a_verifier", "revenu") and tx.get("sous_categorie") != "salaire":
            origine = [t for t in existantes if t["montant"] < 0 and cle_commercant(t["libelle"]) == cle_commercant(tx["libelle"])
                       and 0 <= (d(tx["date"]) - d(t["date"])).days <= 60]
            if origine:
                o = origine[-1]
                tx.update({"categorie": o["categorie"], "enveloppe": o["enveloppe"], "beneficiaire": o.get("beneficiaire"),
                           "lien": o["id"], "confiance": "moyenne", "note": (tx.get("note") or "") + " | remboursement de l'achat lié"})
        etat["transactions"].append(tx)
        existantes.append(tx)
        rapport["ajoutees"].append(tx)
        if tx["confiance"] == "basse" or tx["enveloppe"] == "a_verifier":
            rapport["a_verifier"].append(tx)
    for t in existantes:
        t.pop("_apparie", None)
        t.pop("lot", None)
    relie_paiements_carte(etat)
    soldes = lot.get("soldes")
    if soldes:
        for s in (soldes if isinstance(soldes, list) else [soldes]):
            s = dict(s)
            s["date"] = str(s["date"])[:10]
            meme = next((x for x in etat["soldes"] if x["date"] == s["date"]), None)
            if meme is not None:
                meme.update(s)
            else:
                etat["soldes"].append(s)
            rapport["soldes"] += 1
        etat["soldes"].sort(key=lambda s: s["date"])
    # salaire reçu sans fiche : événement de salaire estimé
    for tx in rapport["ajoutees"]:
        if tx["categorie"] == "revenu" and tx.get("sous_categorie") == "salaire" and tx["compte"] in p["comptes_liquides"]:
            if not any(abs((d(s["date"]) - d(tx["date"])).days) <= 5 for s in etat["salaires"]):
                etat["salaires"].append({"date": tx["date"], "verse": tx["montant"], "normalise": p["salaire_normalise"],
                                         "remboursements": 0, "variable": 0, "estimation": True,
                                         "note": "Créé depuis le relevé ; préciser avec la fiche de salaire."})
                etat["salaires"].sort(key=lambda s: s["date"])
    rapport["debut_suivi"] = rapport_debut
    note_journal(etat, "importer", {k: len(v) if isinstance(v, list) else v for k, v in rapport.items()})
    return rapport


def relie_paiements_carte(etat):
    """Débit du compte vers la carte ↔ crédit sur la carte, même montant à ±7 jours : deux flux liés."""
    tx = [t for t in etat["transactions"] if t["statut"] == "comptabilise"]
    debits = [t for t in tx if t["compte"] != "carte" and t["montant"] < 0 and t.get("sous_categorie") == "paiement carte"]
    credits = [t for t in tx if t["compte"] == "carte" and t["montant"] > 0 and t["categorie"] == "flux"]
    for db in debits:
        for cr in credits:
            if abs(cr["montant"] + db["montant"]) < 0.01 and abs((d(cr["date"]) - d(db["date"])).days) <= 7:
                db["lien"], cr["lien"] = cr["id"], db["id"]


# ---------------------------------------------------------------- corrections, ajustements, prévus

def corrige(t, c, cats):
    champs = {k: v for k, v in c.items() if k not in ("id", "cherche", "motif", "tous")}
    if "categorie" in champs and champs["categorie"] not in cats["categories"]:
        raise ValueError(f"Catégorie inconnue : {champs['categorie']}")
    if "categorie" in champs and "enveloppe" not in champs:
        champs["enveloppe"] = cats["categories"][champs["categorie"]]["enveloppe"]
    t.setdefault("historique", []).append({k: t.get(k) for k in champs} | {"corrige_le": dt.date.today().isoformat(),
                                                                            "motif": c.get("motif")})
    t.update(champs)
    if any(k in champs for k in ("categorie", "enveloppe", "beneficiaire", "sous_categorie")):
        t["manuel"] = True
        t["confiance"] = "haute"


def applique(etat, modifs, cats, regles_defaut):
    r = Counter()
    for k, v in (modifs.get("parametres") or {}).items():
        etat["parametres"][k] = v
        r["parametres"] += 1
    for regle in modifs.get("regles", []):
        regle.setdefault("id", nouvel_id("r", regle))
        regle.setdefault("priorite", 80)
        etat["regles"] = [x for x in etat["regles"] if x["id"] != regle["id"]] + [regle]
        r["regles"] += 1
    for c in modifs.get("corrections", []):
        cibles = [t for t in etat["transactions"] if t["id"] == c.get("id")]
        if not cibles and c.get("cherche"):
            q = c["cherche"]
            cibles = [t for t in etat["transactions"]
                      if (not q.get("date") or t["date"] == q["date"])
                      and (not q.get("montant") or abs(abs(t["montant"]) - abs(q["montant"])) < 0.01)
                      and (not q.get("libelle") or normalise(q["libelle"]) in normalise(t["libelle"]))]
        if not cibles or (len(cibles) > 1 and not c.get("tous")):
            raise ValueError(f"Correction ambiguë ou introuvable ({len(cibles)} transactions ; ajouter \"tous\": true "
                             f"pour toutes les corriger) : {c}")
        for t in cibles:
            corrige(t, c, cats)
        r["corrections"] += len(cibles)
    for tx in modifs.get("ajouts", []):  # saisie manuelle (ex. cash, achat oublié)
        lot = importe(etat, {"transactions": [tx], "source": "saisie manuelle"}, cats, regles_defaut)
        r["ajouts"] += len(lot["ajoutees"])
    for a in modifs.get("ajustements", []):
        a = dict(a)
        a.setdefault("id", nouvel_id("a", a))
        a["date"] = str(a["date"])[:10]
        etat["ajustements"] = [x for x in etat["ajustements"] if x["id"] != a["id"]] + [a]
        r["ajustements"] += 1
    for pv in modifs.get("prevus", []):
        pv = dict(pv)
        pv.setdefault("id", nouvel_id("p", pv))
        pv.setdefault("statut", "prevu")
        etat["prevus"] = [x for x in etat["prevus"] if x["id"] != pv["id"]] + [pv]
        r["prevus"] += 1
    for s in modifs.get("salaires", []):
        s = dict(s)
        s["date"] = str(s["date"])[:10]
        s.setdefault("remboursements", 0)
        s.setdefault("variable", 0)
        if "normalise" not in s:
            s["normalise"] = arrondi(s["verse"] - s["remboursements"] - s.get("rappels", 0))
        etat["salaires"] = [x for x in etat["salaires"] if abs((d(x["date"]) - d(s["date"])).days) > 5] + [s]
        etat["salaires"].sort(key=lambda x: x["date"])
        r["salaires"] += 1
    for sid in modifs.get("supprimer", []):
        for liste in ("transactions", "ajustements", "prevus", "regles"):
            avant = len(etat[liste])
            etat[liste] = [x for x in etat[liste] if x.get("id") != sid]
            r["suppressions"] += avant - len(etat[liste])
    if modifs.get("reclasser", True):
        for t in etat["transactions"]:
            if not t.get("manuel") and t["statut"] != "remplace":
                classe(t, etat, cats, regles_defaut)
    note_journal(etat, "appliquer", dict(r))
    return dict(r)


# ---------------------------------------------------------------- calculs

def actives(etat):
    return [t for t in etat["transactions"] if t["statut"] in ("comptabilise", "reservation", "estimation")]


def cycles(etat, aujourd_hui):
    p = etat["parametres"]
    dates = sorted({s["date"] for s in etat["salaires"]})
    futurs = sorted(x for x in p.get("prochains_salaires", []) if x > (dates[-1] if dates else "0"))
    res = []
    for i, debut in enumerate(dates):
        if i + 1 < len(dates):
            fin = d(dates[i + 1]) - dt.timedelta(days=1)
        elif futurs:
            fin = d(futurs[0]) - dt.timedelta(days=1)
        else:
            dd = d(debut)
            m, y = (dd.month % 12) + 1, dd.year + (dd.month == 12)
            fin = dt.date(y, m, min(p["jour_salaire_habituel"], 28)) - dt.timedelta(days=1)
        sal = next(s for s in etat["salaires"] if s["date"] == debut)
        res.append({"debut": debut, "fin": fin.isoformat(), "salaire": sal, "estime_fin": i + 1 >= len(dates)})
    return res


def cycle_de(date, liste):
    for c in liste:
        if c["debut"] <= date <= c["fin"]:
            return c["debut"]
    return None


def segments(debut, fin, p):
    segs, jour = [], d(debut)
    fin = d(fin)
    while jour <= fin:
        dim = jour + dt.timedelta(days=6 - jour.weekday())
        f = min(dim, fin)
        n = (f - jour).days + 1
        we = any((jour + dt.timedelta(days=k)).weekday() == 5 for k in range(n)) or \
            (n >= 1 and f.weekday() == 6)
        segs.append({"debut": jour.isoformat(), "fin": f.isoformat(), "jours": n, "weekend": we,
                     "normal": arrondi(p["budget_jour"] * n + (p["budget_weekend"] if we else 0))})
        jour = f + dt.timedelta(days=1)
    return segs


def cible_prorata(cible, jours):
    return arrondi(cible * jours / 7)


def depense(t):
    """Coût économique d'une transaction de consommation (positif = coût)."""
    return -t["montant"]


def calcule(etat, aujourd_hui=None, cats=None):
    cats = cats or charge_config()[0]
    p = etat["parametres"]
    noms = p["noms"]
    auj = aujourd_hui or dt.date.today().isoformat()
    liste = cycles(etat, auj)
    tx = actives(etat)
    for t in tx:
        t["_cycle"] = t.get("cycle_force") or cycle_de(t["date"], liste)
    res = {"aujourd_hui": auj, "noms": noms, "cycles": [], "alertes": [], "a_verifier": []}
    coussin_reporte = 0.0
    report_var = 0.0
    for c in liste:
        cyc = {"debut": c["debut"], "fin": c["fin"], "salaire": c["salaire"], "estime_fin": c["estime_fin"],
               "en_cours": c["debut"] <= auj <= c["fin"], "futur": auj < c["debut"]}
        txc = [t for t in tx if t["_cycle"] == c["debut"]]
        debut_suivi = p.get("debut_suivi")
        ajc = [a for a in etat["ajustements"] if (a.get("cycle") or cycle_de(a["date"], liste)) == c["debut"]
               and not (debut_suivi and (a.get("semaine") or a["date"]) < debut_suivi)]
        # --- semaines
        segs = segments(c["debut"], c["fin"], p)
        report = report_var if p["report_entre_cycles"] else 0.0
        for s in segs:
            sem = [t for t in txc if t["enveloppe"] == "semaine" and s["debut"] <= (t.get("semaine_force") or t["date"]) <= s["fin"]]
            depense_s = sum(depense(t) for t in sem)
            for a in ajc:
                ds = a.get("semaine") or a["date"]
                if s["debut"] <= ds <= s["fin"]:
                    if a["de"] == "semaine":
                        depense_s -= a["montant"]
                    if a["vers"] == "semaine":
                        depense_s += a["montant"]
            par_cat = defaultdict(float)
            for t in sem:
                par_cat[t["categorie"]] += depense(t)
            base = sum(v for k, v in par_cat.items() if cats["categories"].get(k, {}).get("base"))
            we = sum(depense(t) for t in sem if d(t["date"]).weekday() >= 4)
            s.update({"report_entrant": arrondi(report), "disponible": arrondi(s["normal"] + report),
                      "depense": arrondi(depense_s), "base": arrondi(base), "flexible": arrondi(depense_s - base),
                      "dont_weekend": arrondi(we),
                      "par_categorie": {k: arrondi(v) for k, v in sorted(par_cat.items(), key=lambda x: -x[1])},
                      "cibles": {k: cible_prorata(v, s["jours"]) for k, v in p["cibles_semaine"].items()},
                      "en_cours": s["debut"] <= auj <= s["fin"], "futur": auj < s["debut"],
                      "non_suivi": bool(debut_suivi and s["fin"] < debut_suivi),
                      "ids": [t["id"] for t in sem]})
            if s["non_suivi"]:
                # semaine antérieure au début du suivi : pas de données complètes, donc ni solde ni report
                s.update({"report_entrant": 0.0, "disponible": s["normal"], "report_sortant": None})
                continue
            s["report_sortant"] = arrondi(s["disponible"] - s["depense"]) if not s["futur"] else None
            if not s["futur"]:
                report = s["disponible"] - s["depense"]
        report_var = report
        cyc["semaines"] = segs
        normal_total = sum(s["normal"] for s in segs if not s["non_suivi"])
        dep_var = sum(s["depense"] for s in segs if not s["futur"] and not s["non_suivi"])
        # --- enveloppes
        def env_total(nom):
            v = sum(depense(t) for t in txc if t["enveloppe"] == nom)
            for a in ajc:
                if a["vers"] == nom:
                    v += a["montant"]
                if a["de"] == nom:
                    v -= a["montant"]
            return arrondi(v)
        coussin_budget = p["coussin_mensuel"] + (coussin_reporte if p["coussin_report"] else 0)
        env = {
            "semaine": {"budget": arrondi(normal_total), "depense": arrondi(dep_var)},
            "enfant": {"budget": p["enveloppe_enfant"], "depense": env_total("enfant")},
            "coussin": {"budget": arrondi(coussin_budget), "depense": env_total("coussin"),
                        "dont_report": arrondi(coussin_reporte if p["coussin_report"] else 0)},
            "fixes": {"budget": arrondi(sum(f["montant"] for f in p["fixes"] if f.get("actif", True))), "depense": env_total("fixes")},
            "ponctuel": {"budget": arrondi(sum(pv["montant"] for pv in etat["prevus"]
                                                if pv.get("type", "depense") == "depense" and c["debut"] <= pv["echeance"] <= c["fin"])),
                         "depense": env_total("ponctuel")},
        }
        if p["argent_perso_conjoint"]["actif"]:
            env["perso_conjoint"] = {"budget": p["argent_perso_conjoint"]["montant"], "depense": env_total("perso_conjoint")}
        for v in env.values():
            v["reste"] = arrondi(v["budget"] - v["depense"])
        if not cyc["futur"]:
            coussin_reporte = max(0.0, env["coussin"]["reste"]) if c["fin"] < auj else coussin_reporte
        cyc["enveloppes"] = env
        # --- fixes attendus / payés
        fixes_etat = []
        for f in p["fixes"]:
            if not f.get("actif", True):
                continue
            payes = [t for t in txc if t["montant"] < 0 and any(contient_mot(" " + normalise(t["libelle"]) + " ", m) for m in f.get("mots", []))]
            fixes_etat.append({"nom": f["nom"], "montant": f["montant"], "jour": f.get("jour"), "compte": f.get("compte", "courant"),
                               "paye": arrondi(sum(depense(t) for t in payes)), "ids": [t["id"] for t in payes]})
        cyc["fixes"] = fixes_etat
        # --- où va l'argent
        par_cat = defaultdict(float)
        for t in txc:
            if t["enveloppe"] not in ENVELOPPES_HORS_CONSO:
                par_cat[t["categorie"]] += depense(t)
        cyc["par_categorie"] = {k: arrondi(v) for k, v in sorted(par_cat.items(), key=lambda x: -x[1])}
        cyc["consommation"] = arrondi(sum(par_cat.values()))
        revenus = [t for t in txc if t["categorie"] == "revenu"]
        cyc["revenus"] = arrondi(sum(t["montant"] for t in revenus))
        cyc["flux"] = arrondi(sum(t["montant"] for t in txc if t["enveloppe"] == "flux"))
        cyc["ajustements"] = ajc
        cyc["waterfall"] = [
            ("Salaire versé", c["salaire"]["verse"]),
            ("Charges fixes", -env["fixes"]["depense"]),
            ("Ponctuel / prévu", -env["ponctuel"]["depense"]),
            ("Budget semaine", -env["semaine"]["depense"]),
            (label("{enfant}", noms), -env["enfant"]["depense"]),
            ("Coussin", -env["coussin"]["depense"]),
        ] + ([(label("{conjoint} (perso)", noms), -env["perso_conjoint"]["depense"])] if "perso_conjoint" in env else []) + [
            ("Autres revenus", arrondi(cyc["revenus"] - (c["salaire"]["verse"] if any(t.get("sous_categorie") == "salaire" for t in revenus) else 0))),
        ]
        cyc["resultat"] = arrondi(sum(v for _, v in cyc["waterfall"]))
        res["cycles"].append(cyc)
    courant = next((c for c in res["cycles"] if c["en_cours"]), res["cycles"][-1] if res["cycles"] else None)
    res["cycle_courant"] = courant["debut"] if courant else None
    res["position"] = position(etat, auj)
    if courant:
        res["projection"] = projection(etat, courant, res["position"], auj, cats)
        res["semaine_courante"] = explique_semaine(next((s for s in courant["semaines"] if s["en_cours"]),
                                                        [s for s in courant["semaines"] if not s["futur"]][-1]), cats, noms)
    res["normalise"] = normalise_budget(etat)
    res["apprentissage"] = apprentissage(res["cycles"], cats, noms)
    res["alertes"] = alertes(etat, res, auj)
    # seules comptent les transactions d'un cycle suivi (les plus anciennes ne changent plus rien au budget)
    res["a_verifier"] = [t["id"] for t in tx if t.get("_cycle") and (t["enveloppe"] == "a_verifier" or t.get("confiance") == "basse")]
    for t in tx:
        t.pop("_cycle", None)
    return res


def position(etat, auj):
    p = etat["parametres"]
    if not etat["soldes"]:
        return None
    dispo = [x for x in etat["soldes"] if x["date"] <= auj] or etat["soldes"][:1]
    s = {}
    cote_compte = [x for x in dispo if "courant" in x or "comptes" in x]
    cote_carte = [x for x in dispo if "carte_comptabilise" in x]
    if cote_compte:
        sc = cote_compte[-1]
        s.update({k: sc[k] for k in ("courant", "comptes", "epargne", "ordres", "autres_dettes") if k in sc})
        s["date_compte"] = sc["date"]
    if cote_carte:
        sk = cote_carte[-1]  # réservations et paiements en transit vont avec le solde de carte du même instant
        s.update({k: sk.get(k, 0) for k in ("carte_comptabilise", "carte_reservations", "paiements_en_transit")})
        s["date_carte"] = sk["date"]
    s["date"] = max(x for x in (s.get("date_compte"), s.get("date_carte")) if x)
    cash = sum(float(v) for k, v in s.get("comptes", {}).items() if k in p["comptes_liquides"]) if "comptes" in s else float(s.get("courant", 0))
    epargne = sum(float(v) for k, v in s.get("comptes", {}).items() if k in p["comptes_epargne"]) if "comptes" in s else float(s.get("epargne", 0))
    comptab = float(s.get("carte_comptabilise", 0))
    reserv = float(s.get("carte_reservations", 0))
    transit = float(s.get("paiements_en_transit", 0))
    dette = comptab + reserv - transit
    autres = float(s.get("autres_dettes", 0))
    ordres = s.get("ordres", [])
    ordres_carte = sum(float(o["montant"]) for o in ordres if o.get("type") == "paiement_carte")
    ordres_autres = [o for o in ordres if o.get("type") != "paiement_carte"]
    return {"date": s["date"], "date_compte": s.get("date_compte"), "date_carte": s.get("date_carte"), "cash": arrondi(cash), "epargne": arrondi(epargne), "carte_comptabilise": arrondi(comptab),
            "carte_reservations": arrondi(reserv), "paiements_en_transit": arrondi(transit), "dette_carte": arrondi(dette),
            "autres_dettes": arrondi(autres), "nette": arrondi(cash + epargne - dette - autres),
            "ordres_paiement_carte": arrondi(ordres_carte), "ordres_autres": ordres_autres,
            "ordres_autres_total": arrondi(sum(float(o["montant"]) for o in ordres_autres)),
            "utilisation_carte": arrondi(dette / p["limite_carte"]) if p["limite_carte"] else None,
            "age_jours": (d(auj) - d(s["date"])).days}


def projection(etat, cyc, pos, auj, cats):
    """Aujourd'hui → veille du prochain salaire → après ce salaire → fin du cycle suivant. Deux scénarios."""
    p = etat["parametres"]
    if not pos:
        return None
    ref = max(pos["date"], cyc["debut"])
    fin = cyc["fin"]
    jours_restants = max(0, (d(fin) - d(ref)).days)
    # fixes encore à payer dans ce cycle (pas déjà débités ni déjà en ordre)
    ordres_cycle = [o for o in pos["ordres_autres"] if not o.get("date") or o["date"] <= fin]
    ordres_suivants = [o for o in pos["ordres_autres"] if o.get("date") and o["date"] > fin]
    libs_ordres = " ".join(normalise(o.get("libelle", "")) for o in ordres_cycle)
    fixes_restants = []
    for f in cyc["fixes"]:
        if f["paye"] + 0.5 < f["montant"] and not any(contient_mot(" " + libs_ordres + " ", m) for m in
                                                       next((x.get("mots", []) for x in p["fixes"] if x["nom"] == f["nom"]), [])):
            if f.get("jour") is None or cyc["debut"] <= _date_dans_cycle(cyc, f["jour"]) and _date_dans_cycle(cyc, f["jour"]) > pos["date"]:
                fixes_restants.append({"nom": f["nom"], "montant": arrondi(f["montant"] - f["paye"])})
    prevus_restants = [pv for pv in etat["prevus"] if pv.get("statut", "prevu") == "prevu" and pos["date"] < pv["echeance"] <= fin]
    dep_prevues = arrondi(sum(pv["montant"] for pv in prevus_restants if pv.get("type", "depense") == "depense"))
    rev_prevus = arrondi(sum(pv["montant"] for pv in prevus_restants if pv.get("type") == "revenu"))
    env = cyc["enveloppes"]
    reste_var = max(0.0, env["semaine"]["budget"] - env["semaine"]["depense"])
    # Une semaine déjà dépassée n'est pas « rendue » : on ne projette que les jours restants au budget normal
    jours_budget = sum(s["normal"] for s in cyc["semaines"] if s["debut"] > ref) + \
        sum(arrondi(s["normal"] * max(0, (d(s["fin"]) - d(ref)).days) / s["jours"]) for s in cyc["semaines"] if s["debut"] <= ref <= s["fin"])
    base_jour = sum(p["cibles_semaine"].values()) / 7
    variable_realiste = arrondi(min(reste_var, jours_budget) if reste_var > 0 else 0)
    variable_prudent = arrondi(base_jour * jours_restants)
    base = pos["nette"] - sum(float(o["montant"]) for o in ordres_cycle) - sum(f["montant"] for f in fixes_restants) - dep_prevues + rev_prevus
    scen = {}
    # enveloppes flexibles : consommation attendue au prorata des jours restants (pas tout d'un coup)
    jours_cycle = (d(fin) - d(cyc["debut"])).days + 1
    part = jours_restants / jours_cycle if jours_cycle else 0
    # le coussin reporté des cycles précédents est une réserve : on ne projette pas de le dépenser
    coussin_du_cycle = max(0.0, min(env["coussin"]["reste"], p["coussin_mensuel"] - env["coussin"]["depense"]))
    flex_attendu = (max(0.0, env["enfant"]["reste"]) + coussin_du_cycle) * part
    # cycle suivant : budget semaine réel de ses segments, fixes, enveloppes, prévus qui y tombent
    deb_s = (d(fin) + dt.timedelta(days=1)).isoformat()
    fin_s = _fin_suivant(fin, p)
    var_s = sum(s["normal"] for s in segments(deb_s, fin_s, p))
    n = normalise_budget(etat)
    # ordres déjà programmés pour le cycle suivant : seule la part qui dépasse les fixes prévus s'ajoute
    par_fixe, hors_fixes = defaultdict(float), []
    for o in ordres_suivants:
        lib_o = " " + normalise(o.get("libelle", "")) + " "
        f = next((f for f in p["fixes"] if f.get("actif", True) and any(contient_mot(lib_o, m) for m in f.get("mots", []))), None)
        if f:
            par_fixe[f["nom"]] += float(o["montant"])
        else:
            hors_fixes.append(o)
    supplement = sum(max(0.0, v - next(f["montant"] for f in p["fixes"] if f["nom"] == k)) for k, v in par_fixe.items()) + \
        sum(float(o["montant"]) for o in hors_fixes)
    sorties_suivant = supplement + n["fixes"] + n["fixes_temporaires"] + var_s + n["enfant"] + n["coussin"] + n["perso_conjoint"] + sum(
        pv["montant"] for pv in etat["prevus"] if pv.get("statut", "prevu") == "prevu" and pv.get("type", "depense") == "depense"
        and deb_s <= pv["echeance"] <= fin_s)
    for nom, var, flex in (("prudent", variable_prudent, 0.0), ("realiste", variable_realiste, flex_attendu)):
        veille = arrondi(base - var - flex)
        apres = arrondi(veille + p["salaire_normalise"])
        fin_suivant = arrondi(apres - sorties_suivant)
        scen[nom] = {"aujourdhui": pos["nette"], "veille_salaire": veille, "apres_salaire": apres, "fin_cycle_suivant": fin_suivant,
                     "variable": var, "flexible": arrondi(flex)}
    return {"date_ref": ref, "fin_cycle": fin, "jours_restants": jours_restants, "fixes_restants": fixes_restants,
            "ordres": ordres_cycle, "ordres_cycle_suivant": ordres_suivants, "supplement_ordres_suivant": arrondi(supplement),
            "prevus": prevus_restants, "depenses_prevues": dep_prevues,
            "revenus_prevus": rev_prevus, "scenarios": scen, "cycle_suivant": {"debut": deb_s, "fin": fin_s,
            "sorties_prevues": arrondi(sorties_suivant), "budget_semaine": arrondi(var_s)},
            "deficit": arrondi(min(0.0, scen["realiste"]["veille_salaire"]))}


def _date_dans_cycle(cyc, jour):
    deb = d(cyc["debut"])
    cand = deb.replace(day=min(jour, 28))
    if cand < deb:
        m, y = (deb.month % 12) + 1, deb.year + (deb.month == 12)
        cand = dt.date(y, m, min(jour, 28))
    return cand.isoformat()


def _fin_suivant(fin, p):
    f = d(fin) + dt.timedelta(days=1)
    futurs = sorted(x for x in p.get("prochains_salaires", []) if x > f.isoformat())
    if futurs:
        return (d(futurs[0]) - dt.timedelta(days=1)).isoformat()
    m, y = (f.month % 12) + 1, f.year + (f.month == 12)
    return (dt.date(y, m, min(p["jour_salaire_habituel"], 28)) - dt.timedelta(days=1)).isoformat()


def normalise_budget(etat):
    p = etat["parametres"]
    fixes = sum(f["montant"] for f in p["fixes"] if f.get("actif", True) and not f.get("temporaire"))
    temporaires = sum(f["montant"] for f in p["fixes"] if f.get("actif", True) and f.get("temporaire"))
    variable = p["budget_jour"] * 30.4 + p["budget_weekend"] * 4.35
    perso = p["argent_perso_conjoint"]["montant"] if p["argent_perso_conjoint"]["actif"] else 0
    periodiques = sum(pv.get("mensualise", 0) for pv in etat["prevus"])
    sorties = fixes + temporaires + variable + p["enveloppe_enfant"] + p["coussin_mensuel"] + perso + periodiques
    return {"salaire": p["salaire_normalise"], "fixes": arrondi(fixes), "fixes_temporaires": arrondi(temporaires),
            "variable": arrondi(variable), "enfant": p["enveloppe_enfant"], "coussin": p["coussin_mensuel"],
            "perso_conjoint": perso, "periodiques_mensualises": arrondi(periodiques),
            "sorties_cycle_normal": arrondi(sorties),
            "capacite": arrondi(p["salaire_normalise"] - sorties),
            "capacite_sans_temporaires": arrondi(p["salaire_normalise"] - sorties + temporaires),
            "capacite_si_coussin_epargne": arrondi(p["salaire_normalise"] - sorties + p["coussin_mensuel"])}


def explique_semaine(s, cats, noms):
    lignes = []
    for k, v in s["par_categorie"].items():
        cible = s["cibles"].get(k)
        lignes.append({"categorie": k, "label": label(cats["categories"].get(k, {}).get("label", k), noms), "montant": v,
                       "cible": cible, "ecart": arrondi(v - cible) if cible is not None else None,
                       "base": cats["categories"].get(k, {}).get("base", False)})
    for k, c in s["cibles"].items():
        if k not in s["par_categorie"]:
            lignes.append({"categorie": k, "label": label(cats["categories"][k]["label"], noms), "montant": 0.0, "cible": c,
                           "ecart": -c, "base": True})
    ecart_base = sum(l["ecart"] for l in lignes if l["base"] and l["ecart"] is not None)
    depassement = arrondi(s["depense"] - s["disponible"])
    if depassement <= 0:
        verdict = "Dans le budget."
    elif ecart_base > 0.5 * max(depassement, 1):
        verdict = "Dérive des postes de base : à surveiller."
    else:
        verdict = "Semaine chargée par des postes flexibles ; les bases tiennent leur cible."
    return {"semaine": s, "lignes": lignes, "ecart_base": arrondi(ecart_base), "depassement": depassement, "verdict": verdict}


def apprentissage(cycles_calc, cats, noms):
    termines = [c for c in cycles_calc if not c["en_cours"] and not c["futur"]]
    stats = {}
    for k in cats["categories"]:
        vals = [c["par_categorie"].get(k, 0.0) for c in termines]
        if any(vals):
            stats[k] = {"label": label(cats["categories"][k]["label"], noms), "n": len(vals), "mediane": arrondi(statistics.median(vals)),
                        "moyenne": arrondi(statistics.mean(vals)), "max": arrondi(max(vals))}
    return {"cycles_termines": len(termines), "actif": len(termines) >= 3, "stats": stats}


def alertes(etat, res, auj):
    p = etat["parametres"]
    out = []
    tx = actives(etat)
    n_av = sum(1 for t in tx if (t.get("_cycle") or cycle_de(t["date"], cycles(etat, auj)))
               and (t["enveloppe"] == "a_verifier" or t.get("confiance") == "basse"))
    if n_av:
        out.append(("info", f"{n_av} transaction(s) à vérifier avant d'être définitivement affectées."))
    for t in tx:
        if t["statut"] == "reservation" and (d(auj) - d(t["date"])).days > 10:
            out.append(("attention", f"Réservation ancienne ({t['date']}, {t['libelle']}, {chf(t['montant'])}) : vérifier si débitée ou annulée."))
        if t["statut"] == "estimation" and (d(auj) - d(t["date"])).days > 10:
            out.append(("info", f"Montant en devise encore estimé : {t['libelle']} ({t['date']})."))
    # double compte potentiel : même montant, même jour, deux comptes différents (hors flux)
    vus = defaultdict(list)
    for t in tx:
        if t["enveloppe"] not in ENVELOPPES_HORS_CONSO:
            vus[(t["date"], t["montant"])].append(t)
    for (jour, m), ts in vus.items():
        if len({t["compte"] for t in ts}) > 1:
            out.append(("attention", f"Double compte possible le {jour} : {chf(m)} sur {', '.join(sorted({t['compte'] for t in ts}))}."))
    pos = res.get("position")
    if pos:
        if pos["age_jours"] > 4:
            out.append(("info", f"Soldes datés du {pos['date']} ({pos['age_jours']} j) : envoyer une capture des soldes pour une position à jour."))
        if pos["utilisation_carte"] and pos["utilisation_carte"] > 0.8:
            out.append(("attention", f"Carte utilisée à {pos['utilisation_carte']*100:.0f} % de la limite."))
    proj = res.get("projection")
    if proj and proj["scenarios"]["realiste"]["veille_salaire"] < 0:
        out.append(("attention", f"Déficit projeté à la veille du salaire : {chf(proj['scenarios']['realiste']['veille_salaire'])} (scénario réaliste)."))
    for pv in etat["prevus"]:
        if pv.get("statut", "prevu") == "prevu" and auj <= pv["echeance"] <= (d(auj) + dt.timedelta(days=45)).isoformat() and pv["montant"] >= 300:
            out.append(("info", f"Échéance importante : {pv['libelle']} {chf(pv['montant'])} le {pv['echeance']}."))
    for ab in p.get("abonnements_surveilles", []):
        derniers = [t["date"] for t in tx if any(contient_mot(" " + normalise(t["libelle"]) + " ", m) for m in ab.get("mots", []))]
        if derniers and (d(auj) - d(max(derniers))).days > ab.get("periode_jours", 31) + 14:
            out.append(("info", f"Abonnement peut-être inactif ou non vu : {ab['nom']}."))
    cour = next((c for c in res["cycles"] if c["en_cours"]), None)
    if cour:
        for s in cour["semaines"]:
            if not s["futur"] and s["report_sortant"] is not None and s["report_sortant"] < -50:
                out.append(("attention" if s["en_cours"] else "info",
                            f"Semaine du {s['debut']} : dépassement de {chf(-s['report_sortant'])} (reporté sur la suite)."))
    return [{"niveau": n, "texte": t} for n, t in out]


# ---------------------------------------------------------------- sorties

def rapport_texte(etat, res, cats):
    noms = res["noms"]
    L = []
    cyc = next((c for c in res["cycles"] if c["debut"] == res["cycle_courant"]), None)
    if not cyc:
        return "Aucun cycle : ajouter au moins un salaire (fiche ou relevé)."
    L.append(f"CYCLE {cyc['debut']} → {cyc['fin']} (aujourd'hui {res['aujourd_hui']})")
    L.append("\n1. SEMAINE PAR SEMAINE")
    L.append("| Semaine | Normal | Report entrant | Disponible | Dépensé | Solde / report |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for s in cyc["semaines"]:
        if s["non_suivi"]:
            L.append(f"| {s['debut'][5:]}→{s['fin'][5:]} (avant le début du suivi) | {chf(s['normal'])} | | | {chf(s['depense'])} (partiel) | |")
        elif s["futur"]:
            L.append(f"| {s['debut'][5:]}→{s['fin'][5:]} (à venir) | {chf(s['normal'])} | | | | |")
        else:
            L.append(f"| {s['debut'][5:]}→{s['fin'][5:]}{' (en cours)' if s['en_cours'] else ''} | {chf(s['normal'])} | {chf(s['report_entrant'])} | "
                     f"{chf(s['disponible'])} | {chf(s['depense'])} | {chf(s['report_sortant'])} |")
    env = cyc["enveloppes"]
    L.append(f"Autres sorties du cycle : fixes {chf(env['fixes']['depense'])} · {label('{enfant}', noms)} {chf(env['enfant']['depense'])} · "
             f"coussin {chf(env['coussin']['depense'])} · ponctuel {chf(env['ponctuel']['depense'])}.")
    if cyc["ajustements"]:
        for a in cyc["ajustements"]:
            L.append(f"Ajustement : {chf(a['montant'])} de « {a['de']} » vers « {a['vers']} » ({a.get('motif','')}) — le total économique ne change pas.")
    sc = res.get("semaine_courante")
    if sc:
        s = sc["semaine"]
        L.append(f"\n2. SEMAINE {s['debut']} → {s['fin']} : {chf(s['depense'])} pour {chf(s['disponible'])} disponibles")
        L.append("| Catégorie | Montant | Cible | Écart |")
        L.append("|---|---:|---:|---:|")
        for l in sc["lignes"]:
            L.append(f"| {l['label']}{' (base)' if l['base'] else ''} | {chf(l['montant'])} | {chf(l['cible']) if l['cible'] is not None else '—'} | "
                     f"{('+' if (l['ecart'] or 0) > 0 else '') + chf(l['ecart']) if l['ecart'] is not None else '—'} |")
        L.append(f"Bases : {chf(s['base'])} · Flexibles : {chf(s['flexible'])} · dont week-end (ven–dim) : {chf(s['dont_weekend'])}")
        L.append(f"Lecture : {sc['verdict']}")
    pos = res.get("position")
    L.append("\n3. SITUATION GLOBALE")
    if pos:
        L.append(f"Soldes (compte au {pos['date_compte']}, carte au {pos['date_carte']}) : cash {chf(pos['cash'])} · épargne {chf(pos['epargne'])} · carte comptabilisée {chf(pos['carte_comptabilise'])} "
                 f"+ réservations {chf(pos['carte_reservations'])} − paiements en transit {chf(pos['paiements_en_transit'])} = dette carte {chf(pos['dette_carte'])}")
        L.append(f"POSITION NETTE ACTUELLE : {chf(pos['nette'])}")
        if pos["ordres_paiement_carte"]:
            L.append(f"(Ordre de paiement de la carte {chf(pos['ordres_paiement_carte'])} : déjà représenté par la dette carte, non soustrait une 2e fois.)")
    else:
        L.append("Pas de soldes enregistrés : envoyer une capture des soldes (compte + carte + réservations).")
    for k, v in env.items():
        L.append(f"- {label(cats['enveloppes'][k], noms)} : {chf(v['depense'])} / {chf(v['budget'])} → reste {chf(v['reste'])}")
    proj = res.get("projection")
    L.append("\n4. PROJECTION")
    if proj:
        L.append(f"Restant à payer d'ici le {proj['fin_cycle']} : fixes {chf(sum(f['montant'] for f in proj['fixes_restants']))} "
                 f"({', '.join(f['nom'] for f in proj['fixes_restants']) or 'aucun'}) · ordres {chf(sum(float(o['montant']) for o in proj['ordres']))} · "
                 f"prévus {chf(proj['depenses_prevues'])} · revenus attendus {chf(proj['revenus_prevus'])}")
        L.append("| | Aujourd'hui | Veille du salaire | Après salaire | Fin du cycle suivant |")
        L.append("|---|---:|---:|---:|---:|")
        for nom, sc_ in proj["scenarios"].items():
            L.append(f"| {'Prudent' if nom == 'prudent' else 'Réaliste'} | {chf(sc_['aujourdhui'])} | {chf(sc_['veille_salaire'])} | {chf(sc_['apres_salaire'])} | {chf(sc_['fin_cycle_suivant'])} |")
        cs = proj["cycle_suivant"]
        L.append("Prudent = plus aucune dépense flexible, seulement les bases. Réaliste = budget semaine normal restant + enveloppes "
                 f"{label('{enfant}', noms)} et coussin au prorata des jours restants.")
        L.append(f"Cycle suivant ({cs['debut']} → {cs['fin']}) : salaire de planification {chf(etat['parametres']['salaire_normalise'])} − sorties prévues "
                 f"{chf(cs['sorties_prevues'])} (dont budget semaine {chf(cs['budget_semaine'])} ; ordres déjà programmés au-delà des fixes : "
                 f"{chf(proj['supplement_ordres_suivant'])}).")
    n = res["normalise"]
    L.append(f"\nVUE NORMALISÉE (mois sans exceptionnel) : salaire {chf(n['salaire'])} − fixes {chf(n['fixes'])} − crédits temporaires "
             f"{chf(n['fixes_temporaires'])} − variable {chf(n['variable'])} − {label('{enfant}', noms)} {chf(n['enfant'])} − coussin "
             f"{chf(n['coussin'])}{' − ' + label('{conjoint}', noms) + ' ' + chf(n['perso_conjoint']) if n['perso_conjoint'] else ''} "
             f"= {chf(n['capacite'])} ; {chf(n['capacite_sans_temporaires'])} une fois les crédits terminés ; "
             f"{chf(n['capacite_si_coussin_epargne'])} si le coussin n'est pas utilisé.")
    if res["alertes"]:
        L.append("\nALERTES")
        for a in res["alertes"]:
            L.append(f"- [{a['niveau']}] {a['texte']}")
    av = [t for t in etat["transactions"] if t["id"] in res["a_verifier"]]
    if av:
        L.append("\nÀ VÉRIFIER (demander au foyer)")
        for t in av[:30]:
            L.append(f"- {t['id']} · {t['date']} · {t['compte']} · {t['libelle']} · {chf(t['montant'])} → proposé : {t['categorie']} / {t['enveloppe']}"
                     f"{' · ' + t['note'] if t.get('note') else ''}")
    return "\n".join(L)


def tableau_html(etat, res, cats):
    gabarit = (ICI / "tableau_modele.html").read_text(encoding="utf-8")
    donnees = {"etat": etat, "calcul": res, "categories": cats, "genere_le": dt.datetime.now().isoformat(timespec="minutes")}
    brut = json.dumps(donnees, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return gabarit.replace("/*__DONNEES__*/", "").replace("<!--ETAT-->", MARQUE_DEBUT + brut + MARQUE_FIN)


def ecrit(etat, chemin, cats, auj=None):
    chemin = Path(chemin)
    etat["mis_a_jour"] = dt.datetime.now().isoformat(timespec="minutes")
    if chemin.suffix.lower() in (".html", ".htm"):
        res = calcule(etat, auj, cats)
        chemin.write_text(tableau_html(etat, res, cats), encoding="utf-8")
    elif chemin.suffix.lower() == ".csv":
        champs = ["id", "date", "compte", "libelle", "montant", "devise", "montant_devise", "statut", "categorie", "sous_categorie",
                  "beneficiaire", "enveloppe", "confiance", "note"]
        with chemin.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, champs, extrasaction="ignore")
            w.writeheader()
            for t in sorted(etat["transactions"], key=lambda t: t["date"]):
                w.writerow(t)
    else:
        chemin.write_text(json.dumps(etat, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- tests (spécification § 19)

def tests():
    cats, regles = charge_config()
    ok = []

    def base():
        e = etat_vide()
        e["parametres"]["prochains_salaires"] = ["2026-10-23"]
        e["salaires"] = [{"date": "2026-09-25", "verse": 7700, "normalise": 7700, "remboursements": 0, "variable": 0}]
        return e

    def verifie(nom, cond):
        ok.append((nom, bool(cond)))

    # 1. achat carte 100 puis paiement carte 100 → une seule dépense de 100
    e = base()
    importe(e, {"transactions": [
        {"date": "2026-09-28", "compte": "carte", "libelle": "Migros Lausanne", "montant": -100},
        {"date": "2026-10-05", "compte": "courant", "libelle": "Paiement carte de crédit PostFinance Visa", "montant": -100},
        {"date": "2026-10-06", "compte": "carte", "libelle": "Paiement merci", "montant": 100}]}, cats, regles)
    r = calcule(e, "2026-10-10", cats)
    verifie("achat carte + paiement carte = 100 CHF de consommation", r["cycles"][0]["consommation"] == 100)

    # 2. réservation 50 remplacée par débit final 48 → 48
    e = base()
    importe(e, {"transactions": [{"date": "2026-09-28", "compte": "carte", "libelle": "Coop Pronto", "montant": -50, "statut": "reservation"}]}, cats, regles)
    importe(e, {"transactions": [{"date": "2026-09-30", "compte": "carte", "libelle": "COOP PRONTO LAUSANNE", "montant": -48}]}, cats, regles)
    r = calcule(e, "2026-10-10", cats)
    verifie("réservation 50 → débit 48 : 48 CHF", r["cycles"][0]["consommation"] == 48 and len(actives(e)) == 1)

    # 3. achat EUR estimé puis comptabilisé en CHF → une seule dépense
    e = base()
    e["parametres"]["taux"] = {"EUR": 0.94}
    importe(e, {"transactions": [{"date": "2026-10-01", "compte": "carte", "libelle": "Amazon EU", "montant_devise": -130, "devise": "EUR"}]}, cats, regles)
    est = actives(e)[0]["montant"]
    importe(e, {"transactions": [{"date": "2026-10-03", "compte": "carte", "libelle": "AMAZON EU SARL", "montant": -123.40}]}, cats, regles)
    verifie(f"EUR estimé ({est}) puis CHF final : une seule dépense", len(actives(e)) == 1 and actives(e)[0]["montant"] == -123.40
            and actives(e)[0]["historique"][0]["statut"] == "estimation")

    # 4. transfert 800 remboursant une avance : pas de consommation
    e = base()
    importe(e, {"transactions": [{"date": "2026-09-27", "compte": "courant", "libelle": "Virement à M. X (remboursement avance supervision)", "montant": -800,
                                  "categorie_proposee": "flux"}]}, cats, regles)
    applique(e, {"corrections": [{"cherche": {"montant": 800}, "categorie": "flux", "sous_categorie": "remboursement d'avance", "motif": "avance supervision"}]}, cats, regles)
    r = calcule(e, "2026-10-10", cats)
    verifie("800 CHF de remboursement d'avance : 0 consommation", r["cycles"][0]["consommation"] == 0)

    # 5. premier week-end 491.76, 201.76 réalloués à l'enfant : total inchangé
    e = base()
    importe(e, {"transactions": [{"date": "2026-09-26", "compte": "courant", "libelle": "Migros MMM", "montant": -491.76}]}, cats, regles)
    applique(e, {"ajustements": [{"date": "2026-09-26", "montant": 201.76, "de": "semaine", "vers": "enfant", "motif": "dépassement du 1er week-end"}]}, cats, regles)
    r = calcule(e, "2026-10-10", cats)
    c = r["cycles"][0]
    s1 = c["semaines"][0]
    verifie("1er segment : 290 normal, 290 imputés à la semaine", s1["normal"] == 290 and s1["depense"] == 290)
    verifie("enveloppe enfant reçoit 201.76, total économique 491.76",
            c["enveloppes"]["enfant"]["depense"] == 201.76 and c["consommation"] == 491.76)

    # 6. permis 306 prévu reste « ponctuel prévu » même débité avant le cycle
    e = base()
    importe(e, {"transactions": [{"date": "2026-09-20", "compte": "carte", "libelle": "Service de la population permis", "montant": -306}]}, cats, regles)
    applique(e, {"corrections": [{"cherche": {"montant": 306}, "categorie": "ponctuel", "cycle_force": "2026-09-25", "motif": "permis prévu"}]}, cats, regles)
    r = calcule(e, "2026-10-10", cats)
    verifie("permis 306 dans le cycle prévu, enveloppe ponctuel", r["cycles"][0]["enveloppes"]["ponctuel"]["depense"] == 306)

    # 7. ordre après le prochain salaire → cycle suivant
    e = base()
    e["salaires"].append({"date": "2026-10-23", "verse": 7700, "normalise": 7700, "remboursements": 0, "variable": 0})
    e["parametres"]["prochains_salaires"] = ["2026-11-25"]
    importe(e, {"transactions": [{"date": "2026-10-28", "compte": "courant", "libelle": "Romande Energie", "montant": -90}]}, cats, regles)
    r = calcule(e, "2026-10-10", cats)
    verifie("ordre du 28.10 affecté au cycle du 23.10", r["cycles"][1]["consommation"] == 90 and r["cycles"][0]["consommation"] == 0)

    # 8. captures qui se chevauchent : doublons ignorés, deux cafés identiques gardés
    e = base()
    lot = {"transactions": [{"date": "2026-10-01", "compte": "courant", "libelle": "Café X", "montant": -4.5},
                            {"date": "2026-10-01", "compte": "courant", "libelle": "Café X", "montant": -4.5}]}
    importe(e, lot, cats, regles)
    importe(e, lot | {"transactions": lot["transactions"] + [{"date": "2026-10-02", "compte": "courant", "libelle": "Denner", "montant": -10}]}, cats, regles)
    verifie("chevauchement : 2 cafés + 1 Denner = 3 transactions", len(actives(e)) == 3)

    # 9. position nette : ordre de paiement carte non soustrait deux fois
    e = base()
    e["soldes"] = [{"date": "2026-10-06", "courant": 1295.14, "carte_comptabilise": 1898.31, "carte_reservations": 271.39,
                    "ordres": [{"libelle": "Paiement carte", "montant": 1898.31, "type": "paiement_carte"}]}]
    r = calcule(e, "2026-10-06", cats)
    verifie("position nette 1295.14 − 2169.70 = −874.56", r["position"]["nette"] == -874.56)

    # 10. report : semaine dépassée de 80 → la suivante démarre à 330
    e = base()
    e["salaires"] = [{"date": "2026-09-28", "verse": 7700, "normalise": 7700, "remboursements": 0, "variable": 0}]
    importe(e, {"transactions": [{"date": "2026-09-29", "compte": "courant", "libelle": "Migros", "montant": -490}]}, cats, regles)
    r = calcule(e, "2026-10-06", cats)
    verifie("report négatif : 410 − 80 = 330 disponibles", r["cycles"][0]["semaines"][1]["disponible"] == 330)

    # 11. premier import en cours de cycle : semaines antérieures non évaluées, pas de faux report positif
    e = base()
    e["ajustements"] = [{"id": "a1", "date": "2026-09-26", "montant": 201.76, "de": "semaine", "vers": "enfant"}]
    importe(e, {"transactions": [{"date": "2026-10-13", "compte": "carte", "libelle": "Migros", "montant": -100}]}, cats, regles)
    r = calcule(e, "2026-10-14", cats)
    c = r["cycles"][0]
    sem = next(s for s in c["semaines"] if s["en_cours"])
    verifie("début du suivi au 12.10 : semaine en cours sans report fictif", e["parametres"]["debut_suivi"] == "2026-10-12"
            and sem["report_entrant"] == 0 and c["enveloppes"]["enfant"]["depense"] == 0)

    # 12. même achat vu sur une capture puis sur le relevé PDF : une seule transaction, libellé du relevé
    e = base()
    importe(e, {"transactions": [{"date": "2026-10-14", "compte": "courant", "libelle": "Samsung Pay - Migros M St-Paul Lausanne", "montant": -4.20}]}, cats, regles)
    importe(e, {"origine": "releve", "transactions": [{"date": "2026-10-14", "compte": "courant", "libelle": "Migros M St-Paul Lausanne (Ch)", "montant": -4.20},
                                                      {"date": "2026-10-14", "compte": "courant", "libelle": "Migros M St-Paul Lausanne (Ch)", "montant": -4.20}]}, cats, regles)
    verifie("capture puis relevé : la capture est complétée, le 2e achat identique est gardé",
            len(actives(e)) == 2 and all(t.get("origine") == "releve" for t in actives(e)))

    for nom, v in ok:
        print(("OK   " if v else "ÉCHEC ") + nom)
    n_ko = sum(not v for _, v in ok)
    print(f"\n{len(ok) - n_ko}/{len(ok)} tests réussis.")
    return n_ko == 0


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for nom in ("init", "importer", "importer-releve", "appliquer", "rapport", "tableau", "exporter"):
        s = sp.add_parser(nom)
        s.add_argument("etat")
        if nom in ("importer", "appliquer"):
            s.add_argument("fichier")
        if nom == "importer-releve":
            s.add_argument("pdf", nargs="+")
        s.add_argument("-o", "--sortie")
        s.add_argument("--date", help="date de référence (défaut : aujourd'hui)")
    sp.add_parser("test")
    a = ap.parse_args()
    if a.cmd == "test":
        sys.exit(0 if tests() else 1)
    cats, regles = charge_config()
    if a.cmd == "init":
        etat = complete_etat(json.loads(Path(a.etat).read_text(encoding="utf-8")))
        lot = {"transactions": etat.pop("transactions", []), "soldes": None}
        etat["transactions"] = []
        importe(etat, lot, cats, regles) if lot["transactions"] else None
        ecrit(etat, a.sortie or "tableau-budget.html", cats, a.date)
        print(rapport_texte(etat, calcule(etat, a.date, cats), cats))
        return
    etat = charge_etat(a.etat)
    if a.cmd in ("importer", "importer-releve"):
        if a.cmd == "importer-releve":
            sys.path.insert(0, str(ICI))
            import releves
            lot = releves.lot_depuis(a.pdf)
            print("\n".join(lot["resume"]))
        else:
            lot = json.loads(Path(a.fichier).read_text(encoding="utf-8"))
        r = importe(etat, lot, cats, regles)
        if r["debut_suivi"]:
            print(f"Premier import : suivi semaine par semaine à partir du {r['debut_suivi']} (les semaines précédentes ne sont pas évaluées).")
        print(f"Ajoutées : {len(r['ajoutees'])} · doublons ignorés : {len(r['doublons'])} · réservations/estimations finalisées : "
              f"{len(r['remplacees'])} · soldes : {r['soldes']} · à vérifier : {len(r['a_verifier'])}")
        for t in r["doublons"]:
            print(f"  doublon ignoré : {t['date']} {t['libelle']} {chf(t['montant'])}")
        for t in r["remplacees"]:
            print(f"  finalisée : {t['date']} {t['libelle']} → {chf(t['montant'])}")
    elif a.cmd == "appliquer":
        print("Appliqué :", applique(etat, json.loads(Path(a.fichier).read_text(encoding="utf-8")), cats, regles))
    if a.cmd in ("importer", "importer-releve", "appliquer", "tableau", "exporter"):
        sortie = a.sortie or (a.etat if a.cmd != "exporter" else "etat.json")
        if a.cmd == "tableau" and not sortie.endswith((".html", ".htm")):
            sortie = "tableau-budget.html"
        ecrit(etat, sortie, cats, a.date)
        print(f"Écrit : {sortie}")
    if a.cmd in ("importer", "importer-releve", "appliquer", "rapport"):
        print()
        print(rapport_texte(etat, calcule(etat, a.date, cats), cats))


if __name__ == "__main__":
    main()
