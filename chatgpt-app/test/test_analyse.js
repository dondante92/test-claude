/* Analyse IPB (Document 2) et rédactions liées dans l'app : procédure, contrôle. */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { demarrer } = require('./client.js');
const EX = path.join(__dirname, '..', '..', 'note-clinique-epfl', 'exemples');
const lire = n => fs.readFileSync(path.join(EX, n), 'utf8');
(async () => {
  const { client, fermer } = await demarrer();
  const ok = m => console.log('  ok  ' + m);
  const appel = (name, args) => client.callTool({ name, arguments: args });
  const resultat = r => JSON.parse(r.content[0].text.split('\n\n')[0]);
  try {
    let r = await appel('demarrer_note_clinique', { type: 'analyse' });
    let t = r.content[0].text;
    assert(t.includes('PROCÉDURE ANALYSE IPB') && t.includes('Garde-fous propres à l\'IA') && t.includes('Grille de relecture finale')); ok('démarrer : procédure du Document 2 avec le document maître');
    r = await appel('demarrer_note_clinique', { type: 'redaction_analyse' });
    t = r.content[0].text;
    assert(t.includes('G2') && t.includes('Document 3') && t.includes('Profondeur sans longueur')); ok('démarrer : rédactions G1/G2, Document 3, courriers');
    r = await appel('controler_texte', { type: 'document2', texte: lire('document2_exemple.txt') });
    assert.strictEqual(resultat(r).conforme, true); assert(r.content[0].text.includes('présente le Document 2')); ok('Document 2 conforme');
    r = await appel('controler_texte', { type: 'document2', texte: lire('document2_avec_erreurs.txt') });
    const res = resultat(r);
    assert.strictEqual(res.conforme, false); assert.strictEqual(res.erreurs.length, 4); assert.strictEqual(res.avertissements.length, 5);
    ok('Document 2 fautif : 4 erreurs, 5 avertissements (formules, sous-titre, TDAH, contre-transfert, FDG…)');
  } finally { await fermer(); }
})().catch(e => { console.error('ÉCHEC', e); process.exit(1); });
