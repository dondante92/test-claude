#!/usr/bin/env python3
"""Calcule les positions des rubriques du « Relevé de données UNIL-EPFL » (version LG 06.08.2021).

Outil de maintenance, à relancer seulement si le formulaire change. Il lit les coordonnées
des mots avec pdftotext -bbox-layout (poppler) et écrit scripts/releve_positions.json,
utilisé par remplir_releve.py. Coordonnées PDF : origine en bas à gauche, en points.
"""
import html
import json
import pathlib
import re
import subprocess
import sys

ICI = pathlib.Path(__file__).resolve().parent
VIERGE = ICI.parent.parent / "releve" / "releve_vierge.pdf"
HAUTEUR = 792.0

# (clé, page, y du haut de ligne, options, (x min, x max)) — options : texte exact des mots
CHOIX = [
    ("sexe", 1, 208, ["F", "M"], (95, 140)),
    ("etat_civil", 1, 282, ["célibataire", "marié(e)", "divorcé(e)", "veuf(ve)", "partenarié(e)"], (100, 440)),
    ("enfants", 1, 310, ["oui", "non"], (100, 170)),
    ("langue_consultation", 1, 338, ["fr", "ang", "all", "it", "esp", "autre"], (400, 570)),
    ("echange", 1, 365, ["oui", "non"], (150, 215)),
    ("annees_suisse", 1, 365, ["<1", "1-2", "3-4", ">5", "né CH"], (420, 575)),
    ("situation_economique", 1, 393, ["dépendance parents", "bourse", "activité prof.", "assistanat (assistant-doctorant)"], (160, 580)),
    ("situation_economique+", 1, 412, ["dépendance conjoint"], (45, 155)),
    ("etudes", 1, 439, ["UNIL", "EPFL"], (85, 165)),
    ("niveau_etudes", 1, 467, ["CMS", "EFLE", "bachelor", "master", "doctorat", "MAN"], (160, 485)),
    ("situation_echec", 1, 495, ["oui", "non"], (140, 200)),
    ("echecs_anterieurs", 1, 495, ["oui", "non"], (440, 500)),
    ("deplacement_etudes", 1, 522, ["non", "autre canton", "étranger"], (175, 335)),
    ("mode_venue", 1, 550, ["internet", "SASME (unil)", "SOC (unil)", "Accueil santé (unil)", "SAE (epfl)"], (178, 568)),
    ("mode_venue+", 1, 569, ["Pt santé (epfl)", "prof.", "Ψ pays d’origine", "MT", "pair(e)", "proches (FA, amis)", "autre"], (30, 500)),
    ("mode_rdv", 1, 596, ["réception SASME", "mail UNIL", "mail EPFL", "mail via guichet"], (230, 580)),
    ("consultations_anterieures", 1, 624, ["oui", "non"], (245, 305)),
    ("consultations_anterieures_lieu", 1, 624, ["UNIL", "EPFL", "DP-CHUV", "externe"], (380, 575)),
    ("hospitalisation", 1, 651, ["oui", "non"], (285, 348)),
    ("motif_principal", 1, 679, ["symptômes", "problème relationnel", "études"], (170, 408)),
    ("contexte_etudes", 1, 707, ["début", "fin", "examen", "échec"], (135, 312)),
    ("difficultes_relationnelles", 1, 734, ["familial", "sentimental", "vie sociale", "milieu d’études", "milieu prof."], (175, 536)),
    ("idees_suicidaires", 2, 73, ["scénarisées", "idéation passive", "absentes"], (130, 352)),
    ("tentative_suicide", 2, 73, ["oui", "non"], (522, 578)),
    ("screening", 2, 101, ["oui", "non"], (240, 300)),
    ("symptomes_screening", 2, 129, ["oui", "non"], (210, 270)),
    ("une_seule_consultation", 2, 184, ["oui", "non"], (440, 502)),
    ("raison_une_seule", 2, 212, ["rupture", "problème économique", "pas besoin de plus", "départ campus"], (160, 540)),
    ("raison_une_seule+", 2, 228, ["autre suivi déjà en cours", "bilan somatique d’abord", "arrêt à l’initiative du patient"], (160, 576)),
    ("abus_substances", 2, 409, ["oui", "non"], (183, 243)),
    ("type_travail", 2, 409, ["IP", "IPB", "IPB (en cours)"], (440, 575)),
    ("decision", 2, 437, ["arrêt", "rupture", "transmission DP-CHUV", "transmission privé", "en cours", "urgences"], (90, 550)),
    ("decision+", 2, 455, ["psy. précédent", "poursuite suivi par intervenant(e)", "poursuite chez le généraliste", "départ à"], (90, 572)),
    ("decision++", 2, 472, ["l’étranger", "poursuite chez le psy. étranger", "autre"], (90, 360)),
    ("prescription", 2, 501, ["∅", "somnifère", "benzodiazépine", "neuroleptique", "antidépresseur", "physiothérapie", "autre"], (108, 576)),
    ("certificat_medical", 2, 530, ["oui", "non"], (135, 182)),
    ("demande_certificat", 2, 530, ["oui", "non"], (348, 396)),
    ("attestation_medicale", 2, 530, ["oui", "non"], (525, 574)),
    ("liaison_campus", 2, 558, ["oui", "non"], (502, 562)),
    ("liaison_hors_campus", 2, 586, ["oui", "non"], (209, 270)),
    ("groupe_indication", 2, 613, ["oui", "non"], (276, 337)),
    ("tests_psychologiques", 2, 641, ["oui", "non"], (164, 224)),
    ("adresse_medecine", 2, 669, ["oui", "non"], (371, 431)),
    ("entretien_famille", 2, 696, ["oui", "non"], (231, 292)),
    ("demande_ccf", 2, 724, ["oui", "non"], (190, 250)),
]
# Cases à cocher du screening (le caractère de case suit chaque mot)
CASES = {"TDAH": (353, 100, 362, 111), "Prodromes": (429, 100, 438, 111), "Asperger": (495, 100, 505, 111), "Dys": (536, 100, 546, 111)}
# Zones de texte : (page, x début, y haut, y bas, x fin) d'après les pointillés
TEXTES = {
    "nom": (1, 102, 156, 167, 250), "prenom": (1, 102, 174, 185, 250), "consultant": (1, 336, 156, 166, 575),
    "date_naissance_j": (1, 124, 191, 202, 149), "date_naissance_m": (1, 157, 191, 202, 182), "date_naissance_a": (1, 190, 191, 202, 225),
    "nationalite": (1, 109, 255, 265, 290), "langue_maternelle": (1, 144, 338, 348, 290),
    "faculte_section": (1, 328, 439, 449, 574), "mode_venue_autre": (1, 506, 569, 579, 575),
    "date_premiere_j": (2, 150, 156, 166, 190), "date_premiere_m": (2, 197, 156, 166, 234), "date_premiere_a": (2, 240, 156, 166, 290),
    "date_derniere_j": (2, 449, 156, 166, 487), "date_derniere_m": (2, 493, 156, 166, 530), "date_derniere_a": (2, 537, 156, 166, 575),
    "nb_consultations": (2, 109, 184, 194, 147),
    "diagnostic_principal_axe1": (2, 165, 283, 293, 559), "diagnostic_principal_axe2": (2, 165, 307, 317, 559),
    "comorbidite_axe1": (2, 165, 332, 342, 559), "comorbidite_axe2": (2, 165, 356, 367, 559),
    "code_z": (2, 94, 381, 391, 160),
}


def mots(pdf):
    sortie = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    pages = re.findall(r"<page.*?</page>", sortie, re.S)
    return [[(float(a), float(b), float(c), float(d), html.unescape(w)) for a, b, c, d, w in
             re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', p)] for p in pages]


def trouver(liste, y, texte, xmin, xmax):
    cibles = texte.split(" ")
    ligne = sorted([w for w in liste if abs(w[1] - y) <= 4 and xmin <= w[0] <= xmax], key=lambda w: w[0])
    for i in range(len(ligne) - len(cibles) + 1):
        if [w[4] for w in ligne[i:i + len(cibles)]] == cibles:
            g = ligne[i:i + len(cibles)]
            return [round(g[0][0], 1), round(HAUTEUR - max(w[3] for w in g), 1), round(g[-1][2], 1), round(HAUTEUR - min(w[1] for w in g), 1)]
    sys.exit(f"introuvable : « {texte} » vers y={y}")


def main():
    pages = mots(VIERGE)
    choix = {}
    for cle, page, y, options, (xmin, xmax) in CHOIX:
        base = cle.rstrip("+")
        for o in options:
            choix.setdefault(base, {})[o] = {"page": page, "boite": trouver(pages[page - 1], y, o, xmin, xmax)}
    # Option coupée sur deux lignes : « départ à » + « l’étranger »
    d = choix["decision"]
    d["départ à l’étranger"] = d.pop("départ à") | {"boites_suivantes": [d.pop("l’étranger")["boite"]]}
    cases = {k: {"page": 2, "boite": [x0, HAUTEUR - y1, x1, HAUTEUR - y0]} for k, (x0, y0, x1, y1) in CASES.items()}
    textes = {k: {"page": p, "x": x0, "ligne": round(HAUTEUR - yb + 3.6, 1), "x_fin": x1} for k, (p, x0, yh, yb, x1) in TEXTES.items()}
    sortie = ICI.parent / "releve_positions.json"
    sortie.write_text(json.dumps({"_lisezmoi": "Généré par outils/positions_releve.py depuis releve/releve_vierge.pdf (version LG 06.08.2021). Ne pas modifier à la main.",
                                  "choix": choix, "cases_screening": cases, "textes": textes}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{sum(len(v) for v in choix.values())} options, {len(cases)} cases, {len(textes)} zones de texte → {sortie}")


if __name__ == "__main__":
    main()
