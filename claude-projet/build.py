#!/usr/bin/env python3
"""Prépare le paquet pour un projet Claude (claude.ai → Projets).

Copie les règles depuis ../note-clinique-epfl/ dans livrables/claude-projet/ et produit
livrables/note-clinique-claude-projet.zip. À relancer après toute modification des règles :
    python3 claude-projet/build.py
Le dossier livrables/ n'est pas publié sur GitHub : il peut contenir 11-reperes-ipb.md (privé).
"""
import pathlib
import shutil
import zipfile

ICI = pathlib.Path(__file__).resolve().parent
SKILL = ICI.parent / "note-clinique-epfl"
SORTIE = ICI.parent / "livrables" / "claude-projet"

if SORTIE.exists():
    shutil.rmtree(SORTIE)
SORTIE.mkdir(parents=True)
sources = sorted((SKILL / "references").glob("*.md")) + [SKILL / "scripts" / n for n in (
    "controle.py", "regles.json", "fiche_modele.json", "remplir_releve.py", "releve_modele.json", "releve_positions.json")] + [
    SKILL / "releve" / "releve_vierge.pdf"]
for source in sources:
    shutil.copy2(source, SORTIE / source.name)
for n in ("instructions.txt", "GUIDE.md"):
    shutil.copy2(ICI / n, SORTIE.parent / f"claude-projet-{n}")

paquet = SORTIE.parent / "note-clinique-claude-projet.zip"
with zipfile.ZipFile(paquet, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(ICI / "GUIDE.md", "GUIDE.md")
    z.write(ICI / "instructions.txt", "instructions.txt")
    for chemin in sorted(SORTIE.iterdir()):
        z.write(chemin, "fichiers/" + chemin.name)
prive = (SORTIE / "11-reperes-ipb.md").exists()
print(f"{len(list(SORTIE.iterdir()))} fichiers de connaissances" + ("" if prive else " (11-reperes-ipb.md absent : fichier privé non fourni)"))
print(f"Écrit : {paquet}")
