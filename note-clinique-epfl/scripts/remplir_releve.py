#!/usr/bin/env python3
"""Remplit le « Relevé de données UNIL-EPFL » original (2 pages) à partir d'un fichier releve.json.

    python3 remplir_releve.py releve.json -o releve_rempli.pdf [--defauts] [--apercu]

releve.json :
    {"choix":  {"etat_civil": "célibataire", "langue_consultation": "fr", ...},
     "textes": {"nationalite": "suisse et tchèque", "nb_consultations": "4", ...},
     "screening_types": ["TDAH"],                      (seulement si screening = oui)
     "deductions": {"annees_suisse": "arrivée en 2023 pour le bachelor"}}   (facultatif)

--defauts  applique les valeurs par défaut de releve_modele.json aux rubriques absentes, et les liste.
--apercu   produit aussi une image PNG de chaque page (si pdftoppm est disponible), pour la vérification visuelle.

Le PDF original n'est jamais modifié : les réponses sont écrites sur une couche superposée
(encre noire, trait fin, police non grasse). Rien n'est produit s'il reste une erreur.
Dépendances : pypdf (ou PyPDF2) et reportlab.
"""
import argparse
import io
import json
import pathlib
import shutil
import subprocess
import sys

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # environnements plus anciens
    from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

ICI = pathlib.Path(__file__).resolve().parent
VIERGE = ICI.parent / "releve" / "releve_vierge.pdf"
if not VIERGE.exists():  # copie à plat (ex. fichiers d'un GPT dans /mnt/data)
    VIERGE = ICI / "releve_vierge.pdf"
POLICE, TAILLE, TAILLE_MIN = "Helvetica", 10.5, 7.5


def charger(nom):
    return json.loads((ICI / nom).read_text(encoding="utf-8"))


def verifier(data, modele, positions, defauts):
    rub = modele["rubriques"]
    choix, textes = dict(data.get("choix", {})), dict(data.get("textes", {}))
    erreurs, appliques, attente = [], [], []
    for k in list(choix) + list(textes):
        if k not in rub:
            erreurs.append(f"rubrique inconnue : {k}")
    for k, v in choix.items():
        if k in rub and rub[k]["type"] == "choix" and v not in rub[k]["options"]:
            erreurs.append(f"{k} : « {v} » n'est pas une option du formulaire ({' / '.join(rub[k]['options'])})")

    # Calculé : une seule consultation
    nb = str(textes.get("nb_consultations", "")).strip()
    if nb.isdigit():
        calc = "oui" if int(nb) == 1 else "non"
        if choix.get("une_seule_consultation", calc) != calc:
            erreurs.append(f"une_seule_consultation = {choix['une_seule_consultation']} alors que nb_consultations = {nb}")
        choix["une_seule_consultation"] = calc

    # Valeurs par défaut (règles de déduction du clinicien)
    if defauts:
        for k, r in rub.items():
            if r["type"] == "choix" and k not in choix and r.get("defaut") is not None and "condition" not in r:
                choix[k] = r["defaut"]
                appliques.append(f"{k} = {r['defaut']} ({r['regle']})")

    # Conditions
    for k, r in rub.items():
        cond = r.get("condition")
        if not cond:
            continue
        actif = all(choix.get(ck) == cv for ck, cv in cond.items())
        present = k in choix or k in textes
        if present and not actif:
            erreurs.append(f"{k} rempli alors que la condition {cond} n'est pas remplie")
        if actif and not present and k not in ("consultations_anterieures_lieu", "mode_venue_autre"):
            erreurs.append(f"{k} est requis puisque {cond}")
    types = data.get("screening_types", [])
    if types and choix.get("screening") != "oui":
        erreurs.append("types de screening cochés alors que screening ≠ oui")
    if choix.get("screening") == "oui" and not types:
        erreurs.append("screening = oui : cocher au moins un type (TDAH, Prodromes, Asperger, Dys)")
    for ty in types:
        if ty not in positions["cases_screening"]:
            erreurs.append(f"type de screening inconnu : {ty}")

    # Données jamais déduites : laissées vides, signalées
    for k, r in rub.items():
        if r.get("jamais_deduire") and not str(textes.get(k, "")).strip():
            attente.append(k)
    vides = [k for k, r in rub.items() if r["type"] == "choix" and k not in choix and "condition" not in r]
    return choix, textes, types, erreurs, appliques, attente, vides


def ecrire_texte(c, x, y, x_fin, texte):
    taille = TAILLE
    while taille > TAILLE_MIN and stringWidth(texte, POLICE, taille) > x_fin - x - 2:
        taille -= 0.25
    c.setFont(POLICE, taille)
    c.drawString(x + 1, y, texte)
    return stringWidth(texte, POLICE, taille) <= x_fin - x - 2


def produire(choix, textes, types, positions, sortie):
    lecteur = PdfReader(str(VIERGE))
    redacteur = PdfWriter()
    trop_longs = []
    for n, page in enumerate(lecteur.pages, 1):
        largeur, hauteur = float(page.mediabox.width), float(page.mediabox.height)
        tampon = io.BytesIO()
        c = canvas.Canvas(tampon, pagesize=(largeur, hauteur))
        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        for cle, val in choix.items():
            p = positions["choix"][cle][val]
            if p["page"] != n:
                continue
            for x0, y0, x1, y1 in [p["boite"]] + p.get("boites_suivantes", []):
                c.ellipse(x0 - 3, y0 - 2.5, x1 + 3, y1 + 2.5, stroke=1, fill=0)
        for ty in types:
            p = positions["cases_screening"][ty]
            if p["page"] == n:
                x0, y0, x1, y1 = p["boite"]
                c.line(x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5)
                c.line(x0 + 1.5, y1 - 1.5, x1 - 1.5, y0 + 1.5)
        for cle, val in textes.items():
            val = str(val).strip()
            p = positions["textes"][cle]
            if val and p["page"] == n and not ecrire_texte(c, p["x"], p["ligne"], p["x_fin"], val):
                trop_longs.append(cle)
        c.save()
        tampon.seek(0)
        page.merge_page(PdfReader(tampon).pages[0])
        redacteur.add_page(page)
    with open(sortie, "wb") as f:
        redacteur.write(f)
    return trop_longs


def apercu(pdf):
    if not shutil.which("pdftoppm"):
        print("Aperçu : pdftoppm indisponible ; ouvrir le PDF pour la vérification visuelle.")
        return
    base = str(pathlib.Path(pdf).with_suffix(""))
    subprocess.run(["pdftoppm", "-png", "-r", "110", pdf, base + "_page"], check=True)
    print(f"Aperçu : {base}_page-1.png et {base}_page-2.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("releve")
    ap.add_argument("-o", "--sortie", default="releve_rempli.pdf")
    ap.add_argument("--defauts", action="store_true")
    ap.add_argument("--apercu", action="store_true")
    a = ap.parse_args()
    modele, positions = charger("releve_modele.json"), charger("releve_positions.json")
    data = json.loads(pathlib.Path(a.releve).read_text(encoding="utf-8"))
    choix, textes, types, erreurs, appliques, attente, vides = verifier(data, modele, positions, a.defauts)

    print("=== RELEVÉ DE DONNÉES ===")
    if erreurs:
        print(f"\nERREURS ({len(erreurs)}) : rien n'est produit.")
        for e in erreurs:
            print("  - " + e)
        sys.exit(1)
    trop_longs = produire(choix, textes, types, positions, a.sortie)
    print(f"\nPDF écrit : {a.sortie} ({len(choix)} choix entourés, {sum(1 for v in textes.values() if str(v).strip())} textes, {len(types)} case(s) cochée(s))")
    if appliques:
        print(f"\nVALEURS PAR DÉFAUT APPLIQUÉES ({len(appliques)}) : à relire")
        for x in appliques:
            print("  - " + x)
    if data.get("deductions"):
        print("\nDÉDUCTIONS (à relire)")
        for k, v in data["deductions"].items():
            print(f"  - {k} : {v}")
    if vides:
        print(f"\nRUBRIQUES LAISSÉES VIDES ({len(vides)}) : " + ", ".join(vides))
    if attente:
        print("\nEN ATTENTE DE DOCUMENTS (jamais déduites) : " + ", ".join(attente))
    if trop_longs:
        print("\nTEXTES TROP LONGS POUR LA LIGNE (à raccourcir) : " + ", ".join(trop_longs))
    if a.apercu:
        apercu(a.sortie)


if __name__ == "__main__":
    main()
