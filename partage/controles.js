/* Contrôles mécaniques de la note et de la synthèse — traduction de
   note-clinique-epfl/scripts/controle.py, mêmes règles (regles.json).
   Partagé par l'application web (app/) et l'app ChatGPT (chatgpt-app/). */
function creerControles(R) {
'use strict';
const cles = o => Object.keys(o || {}).filter(k => !k.startsWith('_'));
const ETATS = ['PRESENT', 'ABSENT', 'NON_EXPLORE'];
const LIB = { patient: 'Patient', motif: 'Motif', cadre: 'Cadre', aigu: 'Plan aigu', psychosocial: 'Contexte', antecedents: 'Antécédents', somatique: 'Somatique', status: 'Status', fin: 'Fin du suivi' };
function libelle(k) { const [a, b] = k.split('.'); return (LIB[a] || a) + (b ? ' › ' + b.replace(/_/g, ' ') : ''); }
const plat = s => String(s ?? '').replace(/[’‘]/g, "'").replace(/[  ]/g, ' ')
  .normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/\s+/g, ' ').trim();
const reEsc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const etat = (f, k) => (f[k] && typeof f[k] === 'object' && !Array.isArray(f[k])) ? f[k].etat : undefined;

function rapport() {
  const r = { erreurs: [], avert: [], questions: [], attente: [] };
  const add = (l, m) => { if (!r[l].includes(m)) r[l].push(m); };
  r.erreur = m => add('erreurs', m); r.av = m => add('avert', m);
  r.q = m => add('questions', m); r.att = m => add('attente', m);
  r.conforme = () => !r.erreurs.length && !r.questions.length;
  return r;
}

function persistants(f) {
  const s = (f['aigu.symptomes'] || []).filter(x => String(x.libelle || '').trim() && x.etat_final === 'persistant').map(x => x.libelle);
  const c = (f['chronique.elements'] || []).filter(x => String(x.libelle || '').trim() && x.etat_final === 'persistant').map(x => x.libelle);
  return s.concat(c);
}

function controlerFiche(f, { sansDecision = false, noteSeule = false } = {}) {
  const r = rapport();
  for (const k of cles(R.champs)) {
    const regle = R.champs[k], e = etat(f, k);
    if (e === undefined) { r.erreur(`champ absent de la fiche : ${k}`); continue; }
    if (!ETATS.includes(e)) { r.erreur(`${k} : état « ${e} » invalide`); continue; }
    if (e === 'PRESENT' && !String(f[k].valeur || '').trim()) r.erreur(`${libelle(k)} : PRÉSENT mais sans valeur`);
    if (e !== 'NON_EXPLORE') continue;
    if (k === 'fin.idees_suicidaires' && (noteSeule || etat(f, 'aigu.idees_suicidaires') !== 'PRESENT')) continue;
    if (regle === 'BLOQUANT') r.q(k); else if (regle === 'ATTENTE') r.att(k);
  }
  const sympt = (f['aigu.symptomes'] || []).filter(s => String(s.libelle || '').trim());
  if (!sympt.length) r.erreur('aucun symptôme aigu renseigné');
  for (const s of sympt) {
    if (!String(s.depuis || '').trim()) r.q(`temporalité du symptôme « ${s.libelle} »`);
    if (!sansDecision && !noteSeule && [undefined, null, '', 'non_documente'].includes(s.etat_final)) r.av(`symptôme « ${s.libelle} » sans destin documenté dans l'évolution`);
  }
  if (etat(f, 'antecedents.premiere_consultation') === 'PRESENT' && etat(f, 'antecedents.suivis') === 'PRESENT')
    r.av('première consultation en milieu psychiatrique ET suivi antérieur : vérifier la compatibilité');
  const ia = etat(f, 'aigu.idees_suicidaires'), is = etat(f, 'status.idees_suicidaires');
  if (ia !== is && ia !== 'NON_EXPLORE' && is !== 'NON_EXPLORE') r.av('idées suicidaires : état différent entre plan aigu et status');
  if (!sansDecision) controlerDecision(f, r, noteSeule);
  return r;
}

function controlerDecision(f, r, noteSeule) {
  const d = f.decision || {}, comp = d.compartiment || '', b = d.branches || {};
  const c = R.compartiments[comp];
  if (!c || comp.startsWith('_')) { r.erreur(`compartiment « ${comp} » inconnu`); return; }
  const chron = b.chronique || '';
  if (c.chronique.length && !c.chronique.includes(chron)) r.erreur(`ce compartiment impose le plan chronique ${c.chronique.join(' ou ')}, pas « ${chron} »`);
  const fin = d.diagnostic_final || {};
  if (!String(fin.code || '').trim() || !String(fin.intitule || '').trim()) r.q('diagnostic : code et intitulé CIM-10');
  const prov = d.diagnostic_provisoire || {};
  if (prov.code && fin.code && prov.code !== fin.code && !d.evaluation_poursuivie) r.av('diagnostic de la note ≠ diagnostic de la synthèse sans évaluation poursuivie : écart temporel ou contradictoire ?');
  if (['F43.2', 'F43.20'].includes(String(fin.code || '').trim().toUpperCase())) r.av("trouble de l'adaptation en code générique : sous-types examinés ?");
  if (noteSeule) return;
  const diag = +b.diagnostic, supp = (b.supplementaires || []).map(Number), evo = +b.evolution, issue = +b.issue;
  if (c.diagnostic.length && !c.diagnostic.includes(diag)) r.erreur(`branche diagnostique attendue : ${c.diagnostic.join(' ou ')} (choisie : ${diag || 'aucune'})`);
  for (const s of supp) if (!c.supp_permises.includes(s)) r.erreur(`paragraphe supplémentaire branche ${s} non prévu pour ce compartiment`);
  if (c.supp_requises_une_de.length && !supp.some(s => c.supp_requises_une_de.includes(s))) r.erreur(`paragraphe supplémentaire requis : branche ${c.supp_requises_une_de.join(' ou ')}`);
  if (comp === 'personnalite' && diag !== 4 && !supp.includes(3)) r.erreur('trouble de la personnalité : branche diagnostique 4 ou supplémentaire 3 requise');
  if (c.evolution.length && !c.evolution.includes(evo)) r.erreur(`branche d'évolution attendue : ${c.evolution.join(' ou ')} (choisie : ${evo || 'aucune'})`);
  if (c.issue.length && !c.issue.includes(issue)) r.erreur(`branche d'issue attendue : ${c.issue.join(' ou ')} (choisie : ${issue || 'aucune'})`);
  const permis = R.couplage_evolution_issue[String(evo)];
  if (permis && !permis.includes(issue)) r.erreur(`couplage : l'évolution ${evo} n'admet que l'issue ${permis.join(' ou ')}`);
  const pers = persistants(f);
  if (evo === 2 && !pers.length) r.erreur('évolution partiellement favorable sans aucun élément « persistant » dans la fiche');
  if (evo === 1 && pers.length) r.av(`évolution favorable alors que la fiche note des éléments persistants : ${pers.join(', ')}`);
  if (issue === 1 && !d.indication_psychotherapie) r.erreur('issue 1 (psychothérapie indiquée) sans indication cochée');
  if (issue === 1 && !pers.length) r.erreur('indication de psychothérapie sans élément persistant documenté');
  if (issue === 2 && (d.indication_psychotherapie || !d.souhait_patient)) r.erreur('issue 2 : souhait du patient SANS indication formelle');
  if ([1, 2].includes(issue) && !d.orientation_realisee) r.erreur('issue 1/2 : « travail d\'orientation réalisé » exige que l\'orientation soit cochée');
  if (issue === 3 && d.indication_psychotherapie) r.erreur('issue 3 (absence d\'indication) alors que l\'indication est cochée');
}

function detecterRubriques(lignes) {
  const vus = [];
  lignes.forEach((l, n) => {
    const p = plat(l).replace(/^[\s:#*_-]+|[\s:#*_-]+$/g, '');
    if (!p || p.length > 60) return;
    R.rubriques_note.forEach((rub, i) => {
      if ([rub.nom, ...rub.alias].map(plat).includes(p) && !vus.some(v => v[1] === n)) vus.push([i, n]);
    });
  });
  return vus;
}
function contenuRubrique(lignes, vus, i) {
  const k = vus.findIndex(v => v[0] === i);
  if (k < 0) return '';
  const fin = k + 1 < vus.length ? vus[k + 1][1] : lignes.length;
  return lignes.slice(vus[k][1] + 1, fin).join('\n');
}

function controlerCommun(texte, r) {
  const p = plat(texte);
  for (const [table, niveau] of [[R.interdits, 'erreur'], [R.avertissements, 'av']])
    for (const e of cles(table))
      if (new RegExp('\\b' + reEsc(plat(e)) + '\\b').test(p)) r[niveau](`« ${e} » → ${table[e]}`);
  const residus = [[/\[(?!À COMPLÉTER)/g, 'crochet de canevas'], [/[{}]/g, 'accolade de menu'], [/…|\.\.\./g, 'pointillés'],
    [/\b(?:il\/elle|Il\/Elle|le\/la|Le\/La|lui\/elle|désireux\/désireuse)\b/g, 'alternative non tranchée'],
    [/\(e\)|\(s\)/g, 'accord non tranché'], [/\bBranche [0-9A-D]\b/g, 'nom de branche'], [/⟨ajout⟩/g, "marque d'instruction"]];
  for (const [re, nom] of residus)
    for (const m of texte.matchAll(re)) r.erreur(`résidu du canevas (${nom}) : « …${texte.slice(Math.max(0, m.index - 25), m.index + m[0].length + 25).replace(/\n/g, ' ')}… »`);
  for (const m of texte.matchAll(/\[À COMPLÉTER[^\]]*\]/g)) r.att(m[0]);
  const corps = texte.split('\n').filter(l => { const lettres = [...l].filter(c => /\p{L}/u.test(c)).length; const maj = [...l].filter(c => /\p{Lu}/u.test(c)).length; return maj < 0.6 * Math.max(1, lettres); }).join('\n');
  for (const m of corps.replace(/\[À COMPLÉTER[^\]]*\]/g, ' ').matchAll(/(?<![\p{L}\d])[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*(?![\p{L}\d])/gu)) {
    const s = m[0];
    if (s.replace(/[^A-Z]/g, '').length < 2 || R.sigles_autorises.includes(s) || /^[A-Z]\d{2}(\.\d+)?$/.test(s)) continue;
    if (R.sigles_diagnostiques.includes(s)) r.erreur(`sigle « ${s} » : écrire en toutes lettres`);
    else r.av(`abréviation « ${s} » : nom usuel (garder) ou opaque (développer) ?`);
  }
  for (const ph of texte.split(/(?<=[.!?])\s+|\n/)) {
    const n = ph.split(/\s+/).filter(Boolean).length;
    if (n > 55) r.av(`phrase de ${n} mots : une information par phrase ? « ${ph.slice(0, 70)}… »`);
  }
}

function controlerNote(texte, f) {
  const r = rapport(), lignes = texte.split('\n'), vus = detecterRubriques(lignes), presents = vus.map(v => v[0]);
  const isOuGeste = f && [etat(f, 'aigu.idees_suicidaires'), etat(f, 'antecedents.geste_suicidaire')].includes('PRESENT');
  R.rubriques_note.forEach((rub, i) => {
    const oblig = rub.obligatoire === 'si_idees_ou_geste' ? isOuGeste : rub.obligatoire;
    if (oblig && !presents.includes(i)) r.erreur(`rubrique manquante : ${rub.nom}`);
  });
  if (presents.join() !== [...presents].sort((a, b) => a - b).join()) r.erreur('rubriques dans le désordre');
  if (new Set(presents).size !== presents.length) r.erreur('rubrique en double');
  const apa = plat(contenuRubrique(lignes, vus, 1));
  if (apa && !apa.startsWith("il s'agit d")) r.erreur("affection actuelle : la phrase d'ouverture doit commencer par « Il s'agit d'un étudiant / d'une étudiante de … ans »");
  if (apa && !apa.includes('sur le plan aigu')) r.erreur('affection actuelle : « Sur le plan aigu » absent');
  if (apa && !apa.includes('exclut toute autre symptomatologie aigue')) r.av('affection actuelle : clôture « exclut toute autre symptomatologie aiguë » absente');
  const chron = f?.decision?.branches?.chronique;
  if (chron === 'aucune' && apa.includes('sur le plan chronique')) r.erreur('compartiment sans plan chronique, mais « Sur le plan chronique » présent');
  if (['A', 'B', 'C', 'D'].includes(chron) && !apa.includes('sur le plan chronique')) r.erreur(`plan chronique branche ${chron} attendu mais absent`);
  const status = plat(contenuRubrique(lignes, vus, 5));
  if (status) {
    const manq = cles(R.items_status).filter(it => !R.items_status[it].some(c => status.includes(plat(c))));
    if (manq.length) r.erreur('status : items manquants : ' + manq.join(', '));
    if (status.includes('activation')) r.erreur("status : le niveau d'activation ne figure jamais dans le status");
  }
  const diag = plat(contenuRubrique(lignes, vus, 8));
  if (diag && f?.decision?.evaluation_poursuivie && !['provisoire', 'hypothese', 'a preciser'].some(m => diag.includes(m))) r.erreur('diagnostic CIM-10 : mentionner le caractère provisoire');
  if (diag && /differentiel/.test(diag)) r.erreur('diagnostic CIM-10 : pas de différentiel dans cette rubrique');
  controlerCommun(texte, r);
  return r;
}

function controlerSynthese(texte, f) {
  const r = rapport(), paras = texte.split(/\n\s*\n/).map(x => x.trim()).filter(Boolean);
  if (!paras.length) { r.erreur('texte vide'); return r; }
  if (paras.at(-1) !== 'Nous nous tenons à sa disposition.') r.erreur('la dernière ligne doit être, seule : « Nous nous tenons à sa disposition. »');
  const corps = paras.slice(0, -1);
  if (corps.length < 4 || corps.length > 5) r.av(`${corps.length} paragraphes avant la phrase finale (4 attendus, 5 si second diagnostic)`);
  if (!/^(Le patient|La patiente) a bénéficié d/.test(paras[0])) r.erreur('paragraphe 1 : moule « Le patient / La patiente a bénéficié d\'une … »');
  const p = plat(texte);
  if (!p.includes('sur le plan diagnostique') && !p.includes('les elements recueillis')) r.erreur('paragraphe diagnostique absent');
  if (!p.includes('au cours du suivi') && !p.includes('le suivi ayant ete interrompu')) r.erreur("paragraphe d'évolution absent");
  if (f?.decision) {
    const d = f.decision, evo = +d.branches?.evolution, issue = +d.branches?.issue;
    if (evo === 1 && p.includes('partiellement favorable')) r.erreur('décision : évolution favorable ; texte : partiellement favorable');
    if (evo === 2 && !p.includes('partiellement favorable') && !p.includes('amelioration partielle')) r.erreur("décision : évolution partiellement favorable ; le texte ne le dit pas");
    if (issue === 3 && p.includes('orientation')) r.erreur("absence d'indication : aucune mention d'orientation");
    if (p.includes('orientation a ete realise') && !d.orientation_realisee) r.erreur("« travail d'orientation réalisé » non documenté");
    if (etat(f, 'aigu.idees_suicidaires') === 'PRESENT' && !p.includes('suicidaire')) r.erreur("idées suicidaires initialement présentes : passage obligatoire dans l'évolution");
    if (d.diagnostic_final?.code && !texte.includes(d.diagnostic_final.code)) r.av(`code du diagnostic final (${d.diagnostic_final.code}) absent du texte`);
  }
  controlerCommun(texte, r);
  return r;
}

function nettoyer(texte, sansAccents = false) {
  for (const a of cles(R.typographie)) texte = texte.split(a).join(R.typographie[a]);
  if (sansAccents) texte = texte.normalize('NFKD').replace(/\p{M}/gu, '');
  return texte;
}

return { cles, ETATS, plat, etat, libelle, controlerFiche, controlerNote, controlerSynthese, nettoyer, persistants };
}
if (typeof module !== 'undefined') module.exports = { creerControles };
