#!/usr/bin/env python3
"""Prépare le paquet pour un GPT personnalisé ChatGPT.

Copie les fichiers de règles depuis ../note-clinique-epfl/ dans chatgpt/fichiers/,
vérifie la limite de 8 000 caractères des instructions, et produit note-clinique-gpt.zip.
À relancer après toute modification des règles :  python3 chatgpt/build.py
"""
import pathlib
import shutil
import zipfile

ICI = pathlib.Path(__file__).resolve().parent
SKILL = ICI.parent / "note-clinique-epfl"
FICHIERS = ICI / "fichiers"
LIMITE = 8000  # limite du champ « Instructions » d'un GPT

instructions = (ICI / "instructions.txt").read_text(encoding="utf-8")
assert len(instructions) <= LIMITE, f"instructions.txt : {len(instructions)} caractères (limite {LIMITE})"

if FICHIERS.exists():
    shutil.rmtree(FICHIERS)
FICHIERS.mkdir()
for source in sorted((SKILL / "references").glob("*.md")) + [SKILL / "scripts" / n for n in ("controle.py", "regles.json", "fiche_modele.json", "remplir_releve.py", "releve_modele.json", "releve_positions.json")] + [SKILL / "releve" / "releve_vierge.pdf"]:
    shutil.copy2(source, FICHIERS / source.name)

paquet = ICI / "note-clinique-gpt.zip"
with zipfile.ZipFile(paquet, "w", zipfile.ZIP_DEFLATED) as z:
    for chemin in [ICI / "GUIDE.md", ICI / "instructions.txt"] + sorted(FICHIERS.iterdir()):
        z.write(chemin, chemin.relative_to(ICI))
print(f"instructions.txt : {len(instructions)} / {LIMITE} caractères")
print(f"{len(list(FICHIERS.iterdir()))} fichiers de connaissances")
print(f"Écrit : {paquet}")
