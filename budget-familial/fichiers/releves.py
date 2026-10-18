#!/usr/bin/env python3
"""Lecture des relevés PDF PostFinance (extrait du compte privé, facture de carte de crédit) en lot
d'import pour budget.py : mêmes champs que les captures, mais exacts et complets.

  python3 releves.py RELEVE.pdf [...] -o nouvelles.json      (puis budget.py importer)
  python3 budget.py importer-releve ETAT RELEVE.pdf [...]     (les deux d'un coup)

Contrôle intégré : pour le compte, le solde recalculé doit retomber sur chaque solde imprimé ;
pour la carte, la somme des transactions doit égaler le total de la facture. Sinon : erreur.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

MONTANT = re.compile(r"^-?\d{1,3}(?:[' ]\d{3})*\.\d{2}$")
DATE_COURTE = re.compile(r"^\d\d\.\d\d\.\d\d$")
DATE_DU = re.compile(r"DU (\d\d\.\d\d\.\d{4})")
IBAN = re.compile(r"^CH\d{2}[0-9A-Z]{10,30}$")
DEVISE = re.compile(r"^(EUR|USD|GBP|TND|CAD|JPY|SEK|NOK|DKK|PLN|CZK|HUF|TRY|MAD|AED) (\d[\d' ]*\.\d{2}) AU COURS DE ([\d.]+)")


def montant(txt):
    return round(float(txt.replace("'", "").replace(" ", "")), 2)


def date_courte(s):
    j, m, a = s.split(".")
    return f"20{a}-{m}-{j}"


def date_longue(s):
    j, m, a = s.split(".")
    return f"{a}-{m}-{j}"


def ouvre(chemin):
    try:
        import pdfplumber
    except ImportError:
        sys.exit("ERREUR : pdfplumber est nécessaire pour lire les relevés (pip install pdfplumber).")
    return pdfplumber.open(chemin)


def type_releve(pdf):
    t = pdf.pages[0].extract_text() or ""
    if "Facture de carte de crédit" in t:
        return "carte"
    if "Extrait de compte" in t:
        return "courant"
    return None


# ---------------------------------------------------------------- compte privé

def lignes_page(page):
    """Regroupe les mots par ligne et fusionne les montants à séparateur de milliers (« 8 597.45 »)."""
    mots = page.extract_words(x_tolerance=1.5, keep_blank_chars=False)
    groupes, haut = [], None
    for w in sorted(mots, key=lambda w: w["top"]):
        if haut is None or w["top"] - haut > 2.5:
            groupes.append([])
            haut = w["top"]
        groupes[-1].append(w)
    res = []
    for groupe in groupes:
        ws = sorted(groupe, key=lambda w: w["x0"])
        fus = []
        for w in ws:
            if fus and re.fullmatch(r"\d{1,3}", fus[-1]["text"]) and re.fullmatch(r"\d{3}\.\d{2}", w["text"]) \
                    and w["x0"] - fus[-1]["x1"] < 6:
                fus[-1] = dict(fus[-1], text=fus[-1]["text"] + " " + w["text"], x1=w["x1"])
            else:
                fus.append(dict(w))
        res.append(fus)
    return res


def lit_compte(pdf):
    ops, soldes_imprimes, debut, fin_periode = [], [], None, None
    entete = None
    courant = None
    for page in pdf.pages:
        cols = None
        for ws in lignes_page(page):
            textes = [w["text"] for w in ws]
            if "Texte" in textes and "Crédit" in textes and "Débit" in textes:
                g = {w["text"]: w for w in ws}
                cols = {"texte": g["Texte"]["x0"], "credit": g["Crédit"]["x1"], "debit": g["Débit"]["x1"],
                        "valeur": g["Valeur"]["x0"], "solde": g["Solde"]["x1"]}
                continue
            if "Extrait" in textes and "compte" in textes:
                dates = [t for t in textes if re.fullmatch(r"\d\d\.\d\d\.\d{4}", t)]
                if len(dates) == 2:
                    entete = (date_longue(dates[0]), date_longue(dates[1]))
            if not cols:
                continue
            ligne = " ".join(textes)
            if ligne.startswith("Page ") or re.match(r"^\d{5} FR", ligne) or "Date 01" in ligne:
                continue
            gauche = [w for w in ws if w["x0"] < cols["texte"] - 5]
            centre = [w for w in ws if cols["texte"] - 5 <= w["x0"] < cols["credit"] - 45]
            nums = [w for w in ws if w["x0"] >= cols["credit"] - 45 and MONTANT.match(w["text"])]
            date_b = next((w["text"] for w in gauche if DATE_COURTE.match(w["text"])), None)
            texte = " ".join(w["text"] for w in centre).strip()
            credit = debit = solde = None
            for w in nums:
                dist = {k: abs(w["x1"] - cols[k]) for k in ("credit", "debit", "solde")}
                k = min(dist, key=dist.get)
                if k == "credit":
                    credit = montant(w["text"])
                elif k == "debit":
                    debit = montant(w["text"])
                else:
                    solde = montant(w["text"])
            if date_b:
                courant_date = date_courte(date_b)
                lit_compte.date = courant_date
            if texte.startswith("Total") and not date_b:
                continue
            if texte.startswith("Etat de compte"):
                if debut is None:
                    debut = solde
                else:
                    fin_periode = solde
                continue
            if credit is not None or debit is not None:
                courant = {"comptabilisation": lit_compte.date, "type": texte, "lignes": [],
                           "montant": credit if credit is not None else -debit, "solde": solde}
                ops.append(courant)
            elif courant is not None and texte:
                courant["lignes"].append(texte)
                if solde is not None:
                    courant["solde"] = solde
            elif courant is not None and solde is not None:
                courant["solde"] = solde
    # contrôle par la chaîne des soldes
    s = debut or 0.0
    for o in ops:
        s = round(s + o["montant"], 2)
        if o["solde"] is not None and abs(s - o["solde"]) > 0.01:
            raise ValueError(f"Relevé de compte : solde recalculé {s} ≠ solde imprimé {o['solde']} "
                             f"({o['comptabilisation']} {o['type']}). Lecture à vérifier.")
    if fin_periode is not None and abs(s - fin_periode) > 0.01:
        raise ValueError(f"Relevé de compte : solde final recalculé {s} ≠ état de compte imprimé {fin_periode}.")
    return {"debut": debut, "fin": s, "periode": entete, "ops": ops}


lit_compte.date = None


def decrit_compte(o):
    """Transforme une opération brute en transaction : date d'achat, commerçant, devise, note."""
    L = o["lignes"]
    typ = o["type"]
    tout = " ".join([typ] + L)
    m = DATE_DU.search(tout)
    date = date_longue(m.group(1)) if m else o["comptabilisation"]
    devise = next((DEVISE.match(l) for l in L if DEVISE.match(l)), None)
    marchand, lieu, note = "", "", []
    i_carte = next((i for i, l in enumerate(L) if l.startswith("CARTE N")), None)
    if i_carte is not None:
        reste = L[i_carte + 1:]
        marchand = reste[0] if reste else ""
        lieu = reste[1] if len(reste) > 1 else ""
    elif "TWINT" in typ or not typ:
        reste = []
        for l in L:
            if l.startswith(("COMMUNICATIONS", "REFERENCES")):
                break
            if re.match(r"^(DU )?\d\d\.\d\d\.\d{4}$|^(DEPUIS LE N|DU NUMÉRO MOBILE|POUR NUMÉRO MOBILE|\+\d)", l):
                continue
            reste.append(l.lstrip(", "))
        marchand = reste[0] if reste else ""
        lieu = reste[1] if len(reste) > 1 else ""
    else:
        i_iban = next((i for i, l in enumerate(L) if IBAN.match(l.replace(" ", ""))), None)
        i_ordre = next((i for i, l in enumerate(L) if l.startswith(("DONNEUR D'ORDRE", "EXPÉDITEUR"))), None)
        if i_ordre is not None and i_ordre + 1 < len(L):
            marchand = L[i_ordre + 1]
        elif i_iban is not None and i_iban + 1 < len(L) and not L[i_iban + 1].startswith("REFERENCE"):
            marchand = L[i_iban + 1]
        elif L:
            marchand = L[0]
    if "COMMUNICATIONS:" in L:
        k = L.index("COMMUNICATIONS:")
        if k + 1 < len(L) and not L[k + 1].startswith("REFERENCES"):
            note.append("communication : " + L[k + 1])
    nature = ("Samsung Pay" if "SAMSUNG PAY" in typ else "carte" if (not typ and i_carte is not None) else
              "TWINT" if ("TWINT" in typ or not typ) else
              "en ligne" if "EN LIGNE" in typ else "ordre / débit" if typ.startswith("DÉBIT") else
              "crédit" if typ.startswith("CRÉDIT") else typ.title())
    if "RETRAIT" in tout:
        nature = "retrait d'espèces"
    if "RETOUR DE MARCHANDISE" in typ:
        nature = "retour de marchandise"
    elif "RÉCEPTION D'ARGENT" in typ:
        nature = "TWINT reçu"
    elif "ENVOI D'ARGENT" in typ:
        nature = "TWINT envoyé"
    libelle = " ".join(x for x in (marchand.title() if marchand.isupper() else marchand, lieu.title() if lieu.isupper() else lieu) if x)
    tx = {"date": date, "compte": "courant", "libelle": libelle or typ.title(), "montant": o["montant"],
          "statut": "comptabilise", "type_operation": nature}
    if o["comptabilisation"] != date:
        tx["date_comptable"] = o["comptabilisation"]
    if devise:
        tx["devise_origine"] = devise.group(1)
        tx["montant_devise"] = montant(devise.group(2))
        note.append(f"{devise.group(1)} {devise.group(2)} au cours de {devise.group(3)}, frais inclus")
    if "RETRAIT" in tout:
        tx["libelle"] = "Retrait d'espèces " + (lieu.title() or marchand.title())
    if note:
        tx["note"] = " | ".join(note)
    return tx


# ---------------------------------------------------------------- facture de carte

LIGNE_CARTE = re.compile(r"^(\d\d\.\d\d\.\d\d) (\d\d\.\d\d\.\d\d) (.+?) (-?[\d']+\.\d\d)$")
LIGNE_PAIEMENT = re.compile(r"^(\d\d\.\d\d\.\d\d) (Votre paiement|Paiement|Crédit.*?) (-?[\d']+\.\d\d)$")


def lit_carte(pdf):
    lignes = []
    for page in pdf.pages:
        lignes += [l.strip() for l in (page.extract_text() or "").splitlines()]
    def valeur(etiquette, motif):
        # selon l'extracteur, la valeur est sur la même ligne que l'étiquette, juste avant ou juste après
        for i, l in enumerate(lignes):
            if l.startswith(etiquette):
                for cand in (l[len(etiquette):], lignes[i - 1] if i else "", lignes[i + 1] if i + 1 < len(lignes) else ""):
                    m = re.search(motif, cand)
                    if m:
                        return m
        return None
    m = valeur("Date de la facture", r"(\d\d\.\d\d\.\d\d)")
    date_facture = date_courte(m.group(1)) if m else None
    m = valeur("Période de facturation", r"(\d\d\.\d\d\.\d\d)\s*[–-]\s*(\d\d\.\d\d\.\d\d)")
    periode = (date_courte(m.group(1)), date_courte(m.group(2))) if m else None
    # ligne des totaux : solde précédent, paiements, transactions, nouveau solde, minimum
    tot = None
    for i, l in enumerate(lignes):
        nb = re.findall(r"-?[\d']+\.\d\d", l)
        if len(nb) == 5 and "Solde" not in l:
            tot = [montant(x) for x in nb]
            break
    txs, en_paiements = [], False
    for i, l in enumerate(lignes):
        if l.startswith("Vos paiements"):
            en_paiements = True
        if l.startswith("Transactions "):
            en_paiements = False
        if l.startswith(("Report", "Total")):
            continue
        mp = LIGNE_PAIEMENT.match(l)
        if mp and en_paiements:
            txs.append({"date": date_courte(mp.group(1)), "compte": "carte", "libelle": "Paiement reçu carte de crédit",
                        "montant": -montant(mp.group(3)), "statut": "comptabilise"})
            continue
        mt = LIGNE_CARTE.match(l)
        if not mt:
            continue
        details = mt.group(3)
        devise = re.search(r" (EUR|USD|GBP|TND) ([\d']+\.\d\d)$", details)
        tx = {"date": date_courte(mt.group(2)), "date_comptable": date_courte(mt.group(1)), "compte": "carte",
              "libelle": details[:devise.start()] if devise else details, "montant": -montant(mt.group(4)),
              "statut": "comptabilise"}
        if devise:
            tx["devise_origine"], tx["montant_devise"] = devise.group(1), montant(devise.group(2))
        suivante = lignes[i + 1] if i + 1 < len(lignes) else ""
        if suivante and not LIGNE_CARTE.match(suivante) and not suivante.startswith(("Report", "Total", "¹", "Cours", "Majoration")):
            tx["type_commerce"] = suivante
        frais = [lignes[k] for k in range(i + 1, min(i + 4, len(lignes))) if lignes[k].startswith(("Cours", "Majoration"))]
        if frais:
            tx["note"] = " | ".join(frais)
        txs.append(tx)
    somme = round(-sum(t["montant"] for t in txs if t["libelle"] != "Paiement reçu carte de crédit"), 2)
    if tot and abs(somme - tot[2]) > 0.02:
        raise ValueError(f"Facture de carte : transactions lues {somme} ≠ total imprimé {tot[2]}. Lecture à vérifier.")
    return {"date_facture": date_facture, "periode": periode, "totaux": tot, "transactions": txs}


# ---------------------------------------------------------------- lot

def lot_depuis(chemins):
    lot = {"source": "relevés PDF PostFinance", "origine": "releve", "transactions": [], "soldes": [], "resume": []}
    for c in chemins:
        with ouvre(c) as pdf:
            t = type_releve(pdf)
            if t == "courant":
                r = lit_compte(pdf)
                txs = [decrit_compte(o) for o in r["ops"]]
                lot["transactions"] += txs
                fin = r["periode"][1] if r["periode"] else txs[-1]["date"]
                lot["soldes"].append({"date": fin, "courant": r["fin"], "source": f"extrait de compte {Path(c).name}",
                                      "partiel": True})
                lot["resume"].append(f"Compte privé {r['periode'][0]} → {r['periode'][1]} : {len(txs)} opérations, "
                                     f"solde {r['debut']} → {r['fin']} (chaîne des soldes vérifiée)")
            elif t == "carte":
                r = lit_carte(pdf)
                lot["transactions"] += r["transactions"]
                if r["totaux"]:
                    lot["soldes"].append({"date": r["date_facture"], "carte_comptabilise": r["totaux"][3],
                                          "source": f"facture de carte {Path(c).name}", "partiel": True})
                lot["resume"].append(f"Carte {r['periode'][0]} → {r['periode'][1]} : {len(r['transactions'])} lignes, "
                                     f"total {r['totaux'][2] if r['totaux'] else '?'} (somme vérifiée), "
                                     f"nouveau solde {r['totaux'][3] if r['totaux'] else '?'}")
            else:
                raise ValueError(f"{c} : ni extrait de compte ni facture de carte PostFinance.")
    return lot


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="+")
    ap.add_argument("-o", "--sortie", default="nouvelles.json")
    a = ap.parse_args()
    lot = lot_depuis(a.pdf)
    Path(a.sortie).write_text(json.dumps(lot, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lot["resume"]))
    print(f"{len(lot['transactions'])} transactions → {a.sortie}")


if __name__ == "__main__":
    main()
