#!/usr/bin/env python3
"""Assemble la skill Claude « budget-foyer » (zip à installer dans Paramètres → Capacités → Skills).

  python3 claude/build.py [-o budget-foyer.zip]

Le moteur et les règles viennent de ../fichiers/ : une seule source pour ChatGPT et pour Claude.
"""
import argparse
import zipfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
FICHIERS = ICI.parent / "fichiers"
CONTENU = {
    "budget-foyer/SKILL.md": ICI / "SKILL.md",
    "budget-foyer/references/methode.md": FICHIERS / "methode.md",
    **{f"budget-foyer/scripts/{n}": FICHIERS / n for n in
       ("budget.py", "releves.py", "tableau_modele.html", "categories.json", "regles_commercants.json")},
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--sortie", default=str(ICI / "budget-foyer.zip"))
    a = ap.parse_args()
    with zipfile.ZipFile(a.sortie, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in CONTENU.items():
            z.write(src, arc)
    print(f"{a.sortie} : {len(CONTENU)} fichiers")


if __name__ == "__main__":
    main()
