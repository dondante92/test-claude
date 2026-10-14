/* Relevé de données UNIL-EPFL : vérification et application des valeurs par défaut.
   Traduction de note-clinique-epfl/scripts/remplir_releve.py (fonction verifier), mêmes fichiers
   releve_modele.json et releve_positions.json. Utilisé par l'app ChatGPT. */
'use strict';

function verifierReleve(data, modele, positions, defauts = true) {
  const rub = modele.rubriques;
  const choix = { ...(data.choix || {}) }, textes = { ...(data.textes || {}) };
  const erreurs = [], appliques = [], attente = [];
  for (const k of [...Object.keys(choix), ...Object.keys(textes)]) if (!rub[k]) erreurs.push(`rubrique inconnue : ${k}`);
  for (const [k, v] of Object.entries(choix)) {
    if (rub[k] && rub[k].type === 'choix' && !rub[k].options.includes(v)) erreurs.push(`${k} : « ${v} » n'est pas une option du formulaire (${rub[k].options.join(' / ')})`);
  }
  const nb = String(textes.nb_consultations ?? '').trim();
  if (/^\d+$/.test(nb)) {
    const calc = Number(nb) === 1 ? 'oui' : 'non';
    if ((choix.une_seule_consultation ?? calc) !== calc) erreurs.push(`une_seule_consultation = ${choix.une_seule_consultation} alors que nb_consultations = ${nb}`);
    choix.une_seule_consultation = calc;
  }
  if (defauts) {
    for (const [k, r] of Object.entries(rub)) {
      if (r.type === 'choix' && !(k in choix) && r.defaut != null && !r.condition) { choix[k] = r.defaut; appliques.push(`${k} = ${r.defaut} (${r.regle})`); }
    }
  }
  for (const [k, r] of Object.entries(rub)) {
    if (!r.condition) continue;
    const actif = Object.entries(r.condition).every(([ck, cv]) => choix[ck] === cv);
    const present = k in choix || k in textes;
    if (present && !actif) erreurs.push(`${k} rempli alors que la condition ${JSON.stringify(r.condition)} n'est pas remplie`);
    if (actif && !present && !['consultations_anterieures_lieu', 'mode_venue_autre'].includes(k)) erreurs.push(`${k} est requis puisque ${JSON.stringify(r.condition)}`);
  }
  const types = data.screening_types || [];
  if (types.length && choix.screening !== 'oui') erreurs.push('types de screening cochés alors que screening ≠ oui');
  if (choix.screening === 'oui' && !types.length) erreurs.push('screening = oui : cocher au moins un type (TDAH, Prodromes, Asperger, Dys)');
  for (const ty of types) if (!positions.cases_screening[ty]) erreurs.push(`type de screening inconnu : ${ty}`);
  for (const [k, r] of Object.entries(rub)) if (r.jamais_deduire && !String(textes[k] ?? '').trim()) attente.push(k);
  const vides = Object.entries(rub).filter(([k, r]) => r.type === 'choix' && !(k in choix) && !r.condition).map(([k]) => k);
  return { choix, textes, types, erreurs, appliques, attente, vides };
}

module.exports = { verifierReleve };
