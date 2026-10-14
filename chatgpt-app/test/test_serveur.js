const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { demarrer } = require('./client.js');
const EX = path.join(__dirname, '..', '..', 'note-clinique-epfl', 'exemples');
const lire = n => fs.readFileSync(path.join(EX, n), 'utf8');
(async () => {
  const { client, fermer } = await demarrer();
  const ok = m => console.log('  ok  ' + m);
  const outils = (await client.listTools()).tools;
  assert.deepStrictEqual(outils.map(t => t.name).sort(), ['afficher_decision', 'afficher_fiche', 'afficher_resultat', 'controler_texte', 'demarrer_note_clinique', 'nettoyer_pour_dossier', 'regles_etape']);
  assert(outils.every(t => t.annotations?.readOnlyHint === true)); ok('7 outils, tous en lecture seule');
  const ecran = outils.filter(t => t._meta?.['openai/outputTemplate']).map(t => t.name).sort();
  assert.deepStrictEqual(ecran, ['afficher_decision', 'afficher_fiche', 'afficher_resultat']); ok('3 outils avec écran');
  const res = await client.readResource({ uri: 'ui://widget/note-clinique-v2.html' });
  assert.strictEqual(res.contents[0].mimeType, 'text/html+skybridge');
  assert(!res.contents[0].text.includes('/*__')); ok('écran servi en text/html+skybridge, gabarit complet');

  const appel = (name, args) => client.callTool({ name, arguments: args });
  const t1 = await appel('demarrer_note_clinique', { type: 'les_deux' });
  assert(t1.content[0].text.includes('ÉTAPE 1') && t1.content[0].text.includes('COMPRÉHENSION')); ok('démarrer : procédure + règles étape 1');
  const t4 = await appel('regles_etape', { etape: 4, compartiment: 'adaptation_seul', type: 'les_deux' });
  assert(t4.content[0].text.includes("TROUBLE DE L'ADAPTATION SEUL") && t4.content[0].text.includes('CANEVAS DE LA SYNTHÈSE')); ok('règles étape 4 : compartiment imposé + canevas');

  const fiche = JSON.parse(lire('fiche_exemple.json')); const decision = fiche.decision; delete fiche.decision;
  let r = await appel('afficher_fiche', { fiche, type: 'les_deux' });
  assert.strictEqual(r.structuredContent.vue, 'fiche'); assert(r.structuredContent.rapport.conforme); ok('fiche conforme');
  const sansAge = JSON.parse(JSON.stringify(fiche)); sansAge['patient.age'].etat = 'NON_EXPLORE';
  r = await appel('afficher_fiche', { fiche: sansAge, type: 'les_deux' });
  assert(!r.structuredContent.rapport.conforme && r.content[0].text.includes('question(s) bloquante')); ok('âge non exploré → question bloquante');

  r = await appel('afficher_decision', { fiche: { ...fiche, decision }, type: 'les_deux' });
  assert(r.structuredContent.rapport.conforme); ok('décision cohérente acceptée');
  const mauvaise = JSON.parse(JSON.stringify(decision)); mauvaise.branches.evolution = 1;
  r = await appel('afficher_decision', { fiche: { ...fiche, decision: mauvaise }, type: 'les_deux' });
  assert(!r.structuredContent.rapport.conforme && r.content[0].text.includes('refusée')); ok('évolution favorable + psychothérapie indiquée → refusée');

  const ficheD = { ...fiche, decision };
  r = await appel('controler_texte', { type: 'note', texte: lire('note_avec_erreurs.txt'), fiche: ficheD });
  assert(JSON.parse(r.content[0].text.split('\n\n')[0]).erreurs.length > 10); ok('note fautive : erreurs détectées');
  r = await appel('afficher_resultat', { type: 'les_deux', fiche: ficheD, note: lire('note_avec_erreurs.txt'), synthese: lire('synthese_exemple.txt') });
  assert.strictEqual(r.structuredContent.vue, 'refus'); ok('résultat avec note fautive → REFUSÉ');
  r = await appel('afficher_resultat', { type: 'les_deux', fiche: ficheD, note: lire('note_exemple.txt'), synthese: lire('synthese_exemple.txt'), mode: 'génération', incertains: [{ question: 'Q ?', options: ['a', 'b'] }] });
  assert.strictEqual(r.structuredContent.vue, 'resultat'); ok('résultat conforme → affiché');
  r = await appel('nettoyer_pour_dossier', { texte: 'L’anamnèse — négative…' });
  assert.strictEqual(r.content[0].text, "L'anamnèse - négative..."); ok('nettoyage Latin-1, accents conservés');
  await fermer();
  console.log('SERVEUR : tous les tests passent');
})().catch(e => { console.error('ÉCHEC', e); process.exit(1); });
