#!/usr/bin/env python3
"""Compare une lettre et sa version corrigée : page HTML colorée, modifications numérotées.

  python3 compare_lettre.py lettre.txt lettre_corrigee.txt
      liste les modifications numérotées (pour écrire motifs.json)
  python3 compare_lettre.py lettre.txt lettre_corrigee.txt --motifs motifs.json -o lettre_corrigee.html
      produit la page : supprimé en rouge barré, ajouté en vert, numéro renvoyant au tableau des raisons

motifs.json : liste de raisons dans l'ordre des numéros, chaque élément étant une chaîne
ou {"raison": "...", "categorie": "structure | cohérence | status | langage | orthographe"}.
L'identité (en-tête, pieds de page) est retirée avant comparaison et n'apparaît jamais dans la page.
Aucune dépendance : Python 3 standard.
"""
import argparse
import difflib
import html
import json
import pathlib
import re
import sys

DEBUT = re.compile(r"^\s*Motif de recours\s*$", re.M)
PARASITES = re.compile(r"Centre hospitalier universitaire vaudois|^\s*PC\d|Document archivé automatiquement"
                       r"|La présence des noms des signataires|^\s*\S.*\s\d+/\d+\s*$|^\s*\d{2}\.\d{2}\.\d{4}\s*$")


def anonymiser(texte):
    """Garde le corps de la lettre, de « Motif de recours » à « Nous nous tenons à sa disposition. »."""
    m = DEBUT.search(texte)
    if m:
        texte = texte[m.start():]
    fin = texte.find("Nous nous tenons")
    if fin >= 0:
        texte = texte[:texte.find("\n", fin) if "\n" in texte[fin:] else len(texte)]
    lignes = [l.strip() for l in texte.splitlines() if not PARASITES.search(l)]
    texte = "\n".join(lignes)
    texte = re.sub(r"[^\n,]+, \d{2}\.\d{2}\.\d{4}, IPP: ?\d+[^\n]*", "[identité]", texte)
    return re.sub(r"\n{3,}", "\n\n", texte).strip()


def jetons(texte):
    """Mots, espaces et ponctuation, en gardant les sauts de ligne."""
    return re.findall(r"\n|[^\S\n]+|\w+(?:['’.]\w+)*|[^\w\s]", texte)


def modifications(avant, apres):
    a, b = jetons(avant), jetons(apres)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    blocs = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        ancien, nouveau = "".join(a[i1:i2]), "".join(b[j1:j2])
        # un seul espace inchangé entre deux modifications ne les sépare pas : une modification = une correction
        colle = op == "equal" and i2 - i1 == 1 and not ancien.strip() and ancien != "\n"
        if blocs and blocs[-1][0] != "equal" and (op != "equal" or colle):
            blocs[-1] = ("replace", blocs[-1][1] + ancien, blocs[-1][2] + nouveau)
        else:
            blocs.append((op, ancien, nouveau))
    return blocs


def court(s, n=80):
    s = s.replace("\n", " ⏎ ").strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def page(blocs, motifs):
    corps, lignes_tableau, num = [], [], 0
    for op, ancien, nouveau in blocs:
        if op == "equal":
            corps.append(html.escape(ancien))
            continue
        num += 1
        m = motifs[num - 1] if num - 1 < len(motifs) else {}
        m = {"raison": m} if isinstance(m, str) else m
        corps.append(f'<span class="mod" id="m{num}">')
        if ancien.strip():
            corps.append(f"<del>{html.escape(ancien)}</del>")
        if nouveau.strip():
            corps.append(f"<ins>{html.escape(nouveau)}</ins>")
        corps.append(f'<a class="n" href="#r{num}">{num}</a></span>')
        lignes_tableau.append(
            f'<tr id="r{num}"><td><a href="#m{num}">{num}</a></td><td><del>{html.escape(court(ancien, 120))}</del></td>'
            f'<td><ins>{html.escape(court(nouveau, 120))}</ins></td><td>{html.escape(m.get("raison", ""))}</td>'
            f'<td>{html.escape(m.get("categorie", ""))}</td></tr>')
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lettre corrigée</title>
<style>
:root {{ --fond:#fff; --texte:#1d1d1f; --suppr:#b3261e; --suppr-fond:#fde7e5; --ajout:#11632f; --ajout-fond:#dcf5e3; --bord:#d9d9de; }}
@media (prefers-color-scheme: dark) {{ :root {{ --fond:#1b1b1d; --texte:#ececf0; --suppr:#ff8a80; --suppr-fond:#4a1f1c;
  --ajout:#7ee2a0; --ajout-fond:#173a24; --bord:#3a3a40; }} }}
body {{ background:var(--fond); color:var(--texte); font:15px/1.6 system-ui, sans-serif; max-width:860px; margin:0 auto; padding:24px 16px; }}
.lettre {{ white-space:pre-wrap; border:1px solid var(--bord); border-radius:8px; padding:20px; }}
del {{ color:var(--suppr); background:var(--suppr-fond); text-decoration:line-through; }}
ins {{ color:var(--ajout); background:var(--ajout-fond); text-decoration:none; }}
a.n {{ font-size:11px; vertical-align:super; margin-left:2px; color:inherit; font-weight:600; }}
table {{ border-collapse:collapse; width:100%; margin-top:24px; font-size:14px; }}
td, th {{ border:1px solid var(--bord); padding:6px 8px; vertical-align:top; text-align:left; }}
.legende {{ font-size:13px; margin-bottom:12px; }}
@media print {{ a.n {{ color:#000; }} }}
</style></head><body>
<h1>Lettre corrigée</h1>
<p class="legende"><del>supprimé</del> · <ins>ajouté</ins> · le numéro renvoie à la raison. {num} modification(s).</p>
<div class="lettre">{"".join(corps)}</div>
<h2>Raisons des corrections</h2>
<table><tr><th>N°</th><th>Avant</th><th>Après</th><th>Raison</th><th>Catégorie</th></tr>
{"".join(lignes_tableau)}
</table></body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("avant")
    ap.add_argument("apres")
    ap.add_argument("--motifs", help="JSON : une raison par modification, dans l'ordre des numéros")
    ap.add_argument("-o", "--sortie", help="page HTML à écrire")
    a = ap.parse_args()
    avant = anonymiser(pathlib.Path(a.avant).read_text(encoding="utf-8"))
    apres = anonymiser(pathlib.Path(a.apres).read_text(encoding="utf-8"))
    blocs = modifications(avant, apres)
    mods = [b for b in blocs if b[0] != "equal"]
    for n, (_, ancien, nouveau) in enumerate(mods, 1):
        print(f"{n}. « {court(ancien)} » → « {court(nouveau)} »")
    motifs = json.loads(pathlib.Path(a.motifs).read_text(encoding="utf-8")) if a.motifs else []
    if a.motifs and len(motifs) != len(mods):
        print(f"\nATTENTION : {len(mods)} modifications, {len(motifs)} raisons dans {a.motifs}", file=sys.stderr)
    if a.sortie:
        pathlib.Path(a.sortie).write_text(page(blocs, motifs), encoding="utf-8")
        print(f"\nÉcrit : {a.sortie}")


if __name__ == "__main__":
    main()
