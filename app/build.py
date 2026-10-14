#!/usr/bin/env python3
"""Assemble l'application en un seul fichier HTML autonome.

Les règles restent écrites une seule fois, dans ../note-clinique-epfl/ :
ce script les injecte dans template.html et produit note-clinique.html.
À relancer après toute modification des règles :  python3 app/build.py
"""
import json
import pathlib
import re

ICI = pathlib.Path(__file__).resolve().parent
SKILL = ICI.parent / "note-clinique-epfl"


def lire(chemin):
    return (SKILL / chemin).read_text(encoding="utf-8")


def base_de_donnees():
    texte = lire("SKILL.md")
    m = re.search(r"## Base de données[^\n]*\n\n(.+?)\n\n", texte, re.S)
    return m.group(1).strip()


donnees = {
    "base": base_de_donnees(),
    "refs": {
        "comprehension": lire("references/1-comprehension.md"),
        "fiche": lire("references/2-fiche-faits.md"),
        "decision": lire("references/3-decision.md"),
        "compartiments": lire("references/3-compartiments.md"),
        "langage": lire("references/4-langage.md"),
        "canevas_note": lire("references/4-canevas-note.md"),
        "canevas_synthese": lire("references/4-canevas-synthese.md"),
        "contrebalance": lire("references/5-contrebalance.md"),
        "verification": lire("references/7-verification.md"),
    },
    "regles": json.loads(lire("scripts/regles.json")),
    "fiche_modele": json.loads(lire("scripts/fiche_modele.json")),
    "demo": {
        "comprehension": lire("exemples/comprehension_exemple.txt"),
        "fiche": json.loads(lire("exemples/fiche_exemple.json")),
        "note": lire("exemples/note_exemple.txt"),
        "synthese": lire("exemples/synthese_exemple.txt"),
    },
}

charge = json.dumps(donnees, ensure_ascii=False).replace("</", "<\\/")
gabarit = (ICI / "template.html").read_text(encoding="utf-8")
assert "/*__DONNEES__*/" in gabarit
sortie = ICI / "note-clinique.html"
controles = (ICI.parent / "partage" / "controles.js").read_text(encoding="utf-8")
assert "/*__CONTROLES__*/" in gabarit
gabarit = gabarit.replace("/*__CONTROLES__*/", controles)
sortie.write_text(gabarit.replace("/*__DONNEES__*/", charge), encoding="utf-8")
print(f"Écrit : {sortie} ({sortie.stat().st_size // 1024} Ko)")
