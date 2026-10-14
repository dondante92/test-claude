/* Ouvre l'écran dans Chromium en simulant ChatGPT (window.openai) et vérifie les blocus. */
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { chromium } = require('playwright-core');
const { demarrer } = require('./client.js');
const EX = path.join(__dirname, '..', '..', 'note-clinique-epfl', 'exemples');
const lire = n => fs.readFileSync(path.join(EX, n), 'utf8');
const CAPTURES = process.env.CAPTURES || os.tmpdir();
const CHROMIUM = process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
(async () => {
  const { client, fermer } = await demarrer();
  const html = (await client.readResource({ uri: 'ui://widget/note-clinique-v2.html' })).contents[0].text;
  const fichier = path.join(os.tmpdir(), 'ecran-note-clinique.html'); fs.writeFileSync(fichier, html);
  const fiche = JSON.parse(lire('fiche_exemple.json')); const decision = fiche.decision; delete fiche.decision;
  const sortie = async (name, args) => (await client.callTool({ name, arguments: args })).structuredContent;
  const vues = {
    fiche: await sortie('afficher_fiche', { fiche, type: 'les_deux' }),
    decision: await sortie('afficher_decision', { fiche: { ...fiche, decision }, type: 'les_deux' }),
    resultat: await sortie('afficher_resultat', { type: 'les_deux', fiche: { ...fiche, decision }, note: lire('note_exemple.txt').replace('elle est célibataire depuis la rupture', '[À COMPLÉTER : situation sentimentale]'), synthese: lire('synthese_exemple.txt'), mode: 'génération', incertains: [{ question: 'Thymie observée ?', options: ['abaissée', 'neutre'] }] }),
    refus: await sortie('afficher_resultat', { type: 'note', fiche: { ...fiche, decision }, note: lire('note_avec_erreurs.txt') }),
  };
  await fermer();
  const b = await chromium.launch({ executablePath: CHROMIUM });
  const ok = m => console.log('  ok  ' + m);
  async function ouvrir(vue) {
    const p = await b.newPage({ viewport: { width: 760, height: 900 } });
    const erreurs = []; p.on('pageerror', e => erreurs.push(e.message));
    await p.addInitScript(o => { window.__messages = []; window.openai = { toolOutput: o, theme: 'light', widgetState: null, setWidgetState: s => { window.openai.widgetState = s; }, sendFollowUpMessage: ({ prompt }) => window.__messages.push(prompt) }; }, vues[vue]);
    await p.goto('file://' + fichier);
    return { p, erreurs };
  }
  let { p, erreurs } = await ouvrir('fiche');
  assert(!(await p.isDisabled('#valider'))); ok('fiche : validation possible');
  await p.selectOption('select[data-k="patient.age"]', 'NON_EXPLORE');
  assert(await p.isDisabled('#valider')); ok('fiche : âge non exploré → bouton bloqué');
  await p.selectOption('select[data-k="patient.age"]', 'PRESENT'); await p.click('#valider');
  const m1 = await p.evaluate(() => window.__messages[0]);
  assert(m1.startsWith('FICHE VALIDÉE') && m1.includes('"patient.age"')); ok('fiche : message « FICHE VALIDÉE » envoyé à ChatGPT');
  await p.screenshot({ path: path.join(CAPTURES, 'ecran-fiche.png') });
  assert(!erreurs.length, erreurs.join()); await p.close();

  ({ p, erreurs } = await ouvrir('decision'));
  assert(!(await p.isDisabled('#valider'))); ok('décision : cohérente');
  await p.selectOption('#evo', '1');
  assert(await p.isDisabled('#valider')); ok('décision : évolution 1 + issue 1 → bouton bloqué');
  await p.selectOption('#evo', '2'); await p.click('#valider');
  assert((await p.evaluate(() => window.__messages[0])).startsWith('DÉCISION VALIDÉE')); ok('décision : message envoyé');
  await p.screenshot({ path: path.join(CAPTURES, 'ecran-decision.png'), fullPage: true });
  assert(!erreurs.length, erreurs.join()); await p.close();

  ({ p, erreurs } = await ouvrir('resultat'));
  assert((await p.textContent('mark')).includes('À COMPLÉTER')); ok('résultat : champ en attente surligné');
  await p.fill('[data-ac="0"]', 'célibataire'); await p.check('input[name=q0][value="neutre"]'); await p.click('#repondre');
  const m3 = await p.evaluate(() => window.__messages[0]);
  assert(m3.startsWith('RÉPONSES DU CLINICIEN') && m3.includes('célibataire') && m3.includes('neutre')); ok('résultat : réponses envoyées');
  await p.screenshot({ path: path.join(CAPTURES, 'ecran-resultat.png'), fullPage: true });
  assert(!erreurs.length, erreurs.join()); await p.close();

  ({ p, erreurs } = await ouvrir('refus'));
  assert((await p.textContent('h2')).includes('refusé')); ok('refus : texte non affiché, erreurs listées');
  assert(!erreurs.length, erreurs.join()); await p.close();
  await b.close();
  console.log('ÉCRAN : tous les tests passent (captures dans ' + CAPTURES + ')');
})().catch(e => { console.error('ÉCHEC', e); process.exit(1); });
