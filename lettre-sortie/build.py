#!/usr/bin/env python3
"""Prépare les fichiers du GPT et du projet Claude « Lettre de sortie EPFL ».

Copie les règles depuis ../note-clinique-epfl/ dans lettre-sortie/fichiers/ et produit lettre-sortie.zip.
À relancer après toute modification des règles :  python3 lettre-sortie/build.py
"""
import pathlib
import shutil
import zipfile

ICI = pathlib.Path(__file__).resolve().parent
SKILL = ICI.parent / "note-clinique-epfl"
FICHIERS = ICI / "fichiers"
LIMITE = 8000  # champ « Instructions » d'un GPT

for nom in ("instructions-gpt.txt", "instructions-claude.txt"):
    n = len((ICI / nom).read_text(encoding="utf-8"))
    assert n <= LIMITE, f"{nom} : {n} caractères (limite {LIMITE})"
    print(f"{nom} : {n} / {LIMITE} caractères")

REFERENCES = ["13-lettre-sortie.md", "4-canevas-note.md", "4-canevas-synthese.md", "3-compartiments.md",
              "4-langage.md", "7-verification.md"]
SCRIPTS = ["controle.py", "regles.json", "compare_lettre.py"]

if FICHIERS.exists():
    shutil.rmtree(FICHIERS)
FICHIERS.mkdir()
for source in [SKILL / "references" / n for n in REFERENCES] + [SKILL / "scripts" / n for n in SCRIPTS]:
    shutil.copy2(source, FICHIERS / source.name)

paquet = ICI / "lettre-sortie.zip"
with zipfile.ZipFile(paquet, "w", zipfile.ZIP_DEFLATED) as z:
    for chemin in [ICI / "GUIDE.md", ICI / "instructions-gpt.txt", ICI / "instructions-claude.txt"] + sorted(FICHIERS.iterdir()):
        z.write(chemin, chemin.relative_to(ICI))
print(f"{len(list(FICHIERS.iterdir()))} fichiers de règles")

# Compétence (skill) pour un plugin ChatGPT ou Claude : SKILL.md + references/ + scripts/
competence = ICI / "lettre-sortie-epfl.zip"
with zipfile.ZipFile(competence, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(ICI / "SKILL.md", "lettre-sortie-epfl/SKILL.md")
    for n in REFERENCES:
        z.write(FICHIERS / n, f"lettre-sortie-epfl/references/{n}")
    for n in SCRIPTS:
        z.write(FICHIERS / n, f"lettre-sortie-epfl/scripts/{n}")
print(f"Écrit : {competence}")
print(f"Écrit : {paquet}")
