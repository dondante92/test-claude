/* App ChatGPT « Note clinique EPFL » — serveur MCP (Apps SDK).

   ChatGPT appelle ces outils pendant la conversation. Les règles viennent de
   ../note-clinique-epfl/ et les contrôles de ../partage/controles.js : une seule
   source pour le skill Claude, l'application web et cette app.

   Le serveur ne stocke rien et ne journalise aucun contenu clinique. */
'use strict';
const fs = require('fs');
const path = require('path');
const express = require('express');
const { McpServer } = require('@modelcontextprotocol/sdk/server/mcp.js');
const { StreamableHTTPServerTransport } = require('@modelcontextprotocol/sdk/server/streamableHttp.js');
const { z } = require('zod');
const { creerControles } = require('../partage/controles.js');
const { verifierReleve } = require('../partage/releve.js');
const { PDFDocument, StandardFonts, rgb } = require('pdf-lib');
const crypto = require('crypto');

const RACINE = path.join(__dirname, '..');
const SKILL = path.join(RACINE, 'note-clinique-epfl');
const lire = p => fs.readFileSync(path.join(SKILL, p), 'utf8');

const R = JSON.parse(lire('scripts/regles.json'));
const MODELE = JSON.parse(lire('scripts/fiche_modele.json'));
const C = creerControles(R);
const RELEVE_MODELE = JSON.parse(lire('scripts/releve_modele.json'));
const RELEVE_POSITIONS = JSON.parse(lire('scripts/releve_positions.json'));
const RELEVE_VIERGE = fs.readFileSync(path.join(SKILL, 'releve', 'releve_vierge.pdf'));
const REFS = {
  1: ['1-comprehension.md'],
  2: ['2-fiche-faits.md'],
  3: ['3-decision.md', '3-compartiments.md'],
  4: ['4-langage.md'],
  5: ['5-contrebalance.md'],
  7: ['7-verification.md'],
};
const ref = n => lire('references/' + n);
const BASE = lire('SKILL.md').match(/## Base de données[^\n]*\n\n([\s\S]+?)\n\n/)[1].trim();
const TITRES_COMP = { adaptation_seul: "TROUBLE DE L'ADAPTATION SEUL", code_z: 'CODE Z', adaptation_traits: "TROUBLE DE L'ADAPTATION AVEC ACCENTUATION", personnalite: 'TROUBLE DE LA PERSONNALITÉ RETENU', neurodev: 'HYPOTHÈSE NEURODÉVELOPPEMENTALE', non_conclusif: 'SITUATION NON CONCLUSIVE', trouble_chronique: 'TROUBLE CHRONIQUE CONSTITUÉ' };
const blocCompartiment = comp => '▸ ' + (ref('3-compartiments.md').split('▸ ').slice(1).find(b => b.startsWith(TITRES_COMP[comp] || '§')) || '(compartiment inconnu)')
  + "\nRÈGLE TRANSVERSALE DU STATUS — il ne contient jamais d'élément orientant vers un diagnostic non retenu, et contient ce que le diagnostic retenu implique.";

/* ---- Interface affichée dans ChatGPT ---- */
const WIDGET_URI = 'ui://widget/note-clinique-v2.html';            // ancien format ChatGPT (skybridge)
const WIDGET_URI_MCP = 'ui://widget/note-clinique-v2-mcp.html';    // standard MCP Apps
const WIDGET = fs.readFileSync(path.join(__dirname, 'widget.html'), 'utf8')
  .replace('/*__CONTROLES__*/', () => fs.readFileSync(path.join(RACINE, 'partage', 'controles.js'), 'utf8'))
  .replace('/*__REGLES__*/', () => JSON.stringify(R).replace(/</g, '\\u003c'));
const avecEcran = (enCours, fait) => ({
  'openai/outputTemplate': WIDGET_URI,
  'openai/toolInvocation/invoking': enCours,
  'openai/toolInvocation/invoked': fait,
  'openai/widgetAccessible': true,
  ui: { resourceUri: WIDGET_URI_MCP },
});
const LECTURE = { readOnlyHint: true, destructiveHint: false, openWorldHint: false };

/* ---- Utilitaires ---- */
const TYPE = z.enum(['note', 'synthese', 'les_deux']).describe("note = note du premier entretien ; synthese = synthèse ; les_deux = note et synthèse");
const DEMANDE = z.enum(['note', 'synthese', 'les_deux', 'suite', 'releve', 'analyse', 'redaction_analyse']).describe("note, synthese, les_deux : procédure en 7 étapes ; suite : note de suite (courte ou transmission) ; releve : relevé de données UNIL-EPFL ; analyse : Document 2 (analyse IPB d'une séance) ; redaction_analyse : G1/G2, Document 3 (présentation supervisable) ou courrier d'adressage");
const FICHE = z.record(z.string(), z.any()).describe('Fiche de faits : même structure que fiche_modele.json (champ → {etat, valeur, source} ; listes aigu.symptomes, chronique.elements, instruments ; bloc decision).');
const texte = t => ({ content: [{ type: 'text', text: t }] });
function completerFiche(f) {
  const out = {};
  for (const k of Object.keys(MODELE)) {
    if (k.startsWith('_') || k === 'decision') continue;
    out[k] = f[k] ?? (Array.isArray(MODELE[k]) ? [] : { etat: 'NON_EXPLORE', valeur: '', source: '' });
  }
  if (f.decision) out.decision = f.decision;
  return out;
}
const resumeRapport = r => ({ erreurs: r.erreurs, questions: r.questions.map(q => (R.champs[q] ? C.libelle(q) : q)), attente: r.attente.map(q => (R.champs[q] ? C.libelle(q) : q)), avertissements: r.avert, conforme: r.conforme() });

const PROCEDURE = `PROCÉDURE NOTE CLINIQUE EPFL — 7 étapes. Suis-la strictement, sans sauter d'étape.

1. COMPRÉHENSION DE LA SITUATION : règles ci-dessous. Écris un bloc de prose continue, sans diagnostic. Montre-le au clinicien et demande s'il valide la lecture du cas. ARRÊT.
2. FICHE DE FAITS : appelle regles_etape(2), remplis la fiche (trois états PRESENT / ABSENT / NON_EXPLORE, rien d'inventé), puis appelle afficher_fiche. Le clinicien complète et valide DANS L'ÉCRAN. ARRÊT jusqu'au message « FICHE VALIDÉE ».
3. DÉCISION : appelle regles_etape(3). Vérifie par recherche web (CIM-10-GM de l'OFS, sinon CIM-10 de l'OMS) le code, l'intitulé et les critères. Remplis le bloc decision et appelle afficher_decision. ARRÊT jusqu'au message « DÉCISION VALIDÉE ».
4. RÉDACTION : appelle regles_etape(4, compartiment, type) et rédige sur le canevas, uniquement avec les faits de la fiche validée et les branches validées.
5. CONTREBALANCE : appelle regles_etape(5) ; confronte la note à la compréhension dans les deux sens ; corrige les écarts sans toucher au reste.
6. CONTRÔLE : appelle controler_texte pour chaque texte. Corrige uniquement les passages visés et rappelle controler_texte, jusqu'à zéro erreur (3 tours au plus).
7. VÉRIFICATION : appelle regles_etape(7), puis afficher_resultat. Cet outil REFUSE un texte qui ne passe pas le contrôle.

Le texte final n'est JAMAIS donné en texte libre dans la conversation : il est présenté uniquement par afficher_resultat.
Pour une note de suite ou le relevé de données, appelle demarrer_note_clinique avec type = suite ou releve.
Si le clinicien écrit « enchaîne », continue sans t'arrêter aux étapes 1, mais les écrans des étapes 2 et 3 restent obligatoires s'il reste une question bloquante ou une incohérence.

BASE DE DONNÉES — ${BASE}`;

/* ---- Outils ---- */
/* ---- Relevé de données : PDF écrit sur le formulaire original, gardé 15 minutes en mémoire ---- */
const PDFS = new Map();
const DUREE_PDF = 15 * 60 * 1000;
function garderPdf(octets) {
  const id = crypto.randomBytes(18).toString('base64url');
  PDFS.set(id, octets);
  setTimeout(() => PDFS.delete(id), DUREE_PDF).unref();
  return id;
}
async function produireReleve({ choix, textes, types }) {
  const doc = await PDFDocument.load(RELEVE_VIERGE);
  const police = await doc.embedFont(StandardFonts.Helvetica);
  const pages = doc.getPages(), noir = rgb(0, 0, 0), tropLongs = [];
  for (const [cle, val] of Object.entries(choix)) {
    const p = RELEVE_POSITIONS.choix[cle][val];
    for (const [x0, y0, x1, y1] of [p.boite, ...(p.boites_suivantes || [])]) {
      pages[p.page - 1].drawEllipse({ x: (x0 + x1) / 2, y: (y0 + y1) / 2, xScale: (x1 - x0) / 2 + 3, yScale: (y1 - y0) / 2 + 2.5, borderColor: noir, borderWidth: 0.8 });
    }
  }
  for (const ty of types) {
    const p = RELEVE_POSITIONS.cases_screening[ty], [x0, y0, x1, y1] = p.boite, pg = pages[p.page - 1];
    pg.drawLine({ start: { x: x0 + 1.5, y: y0 + 1.5 }, end: { x: x1 - 1.5, y: y1 - 1.5 }, thickness: 0.8, color: noir });
    pg.drawLine({ start: { x: x0 + 1.5, y: y1 - 1.5 }, end: { x: x1 - 1.5, y: y0 + 1.5 }, thickness: 0.8, color: noir });
  }
  for (const [cle, brut] of Object.entries(textes)) {
    const val = C.nettoyer(String(brut ?? '').trim());
    if (!val) continue;
    const p = RELEVE_POSITIONS.textes[cle], place = p.x_fin - p.x - 2;
    let taille = 10.5;
    while (taille > 7.5 && police.widthOfTextAtSize(val, taille) > place) taille -= 0.25;
    if (police.widthOfTextAtSize(val, taille) > place) tropLongs.push(cle);
    pages[p.page - 1].drawText(val, { x: p.x + 1, y: p.ligne, size: taille, font: police, color: noir });
  }
  return { octets: Buffer.from(await doc.save()), tropLongs };
}

function creerServeur(baseUrl = '') {
  const s = new McpServer({ name: 'note-clinique-epfl', version: '1.0.0' });

  s.registerResource('ecran-note-clinique', WIDGET_URI, { title: 'Note clinique EPFL', mimeType: 'text/html+skybridge' }, async () => ({
    contents: [{ uri: WIDGET_URI, mimeType: 'text/html+skybridge', text: WIDGET, _meta: { 'openai/widgetDescription': 'Fiche de faits, décision ou texte final de la note clinique, avec contrôles.', 'openai/widgetPrefersBorder': true, 'openai/widgetCSP': { connect_domains: [], resource_domains: [] } } }],
  }));
  s.registerResource('ecran-note-clinique-mcp', WIDGET_URI_MCP, { title: 'Note clinique EPFL', mimeType: 'text/html;profile=mcp-app' }, async () => ({
    contents: [{ uri: WIDGET_URI_MCP, mimeType: 'text/html;profile=mcp-app', text: WIDGET, _meta: { ui: { prefersBorder: true, csp: { connectDomains: [], resourceDomains: [] } } } }],
  }));

  s.registerTool('demarrer_note_clinique', {
    title: 'Démarrer une note clinique',
    description: "À appeler EN PREMIER dès que le clinicien demande, pour la Consultation psychothérapeutique pour étudiants (CHUV/EPFL) : une note du premier entretien, une synthèse, la correction d'une note, une note de suite (courte ou de transmission), le relevé de données, l'analyse IPB d'une séance (Document 2, aussi quand le clinicien écrit « analyse ») ou un bilan G1/G2, un Document 3, un courrier. Renvoie la procédure et les règles à suivre.",
    inputSchema: { type: DEMANDE },
    annotations: LECTURE,
  }, async ({ type }) => {
    if (type === 'suite') return texte(`PROCÉDURE NOTE DE SUITE. Pas de procédure en 7 étapes. Note courte par défaut ; note de transmission si le clinicien a écrit « transmission » pour ce patient (cela vaut pour toutes ses notes de suite). Appuie-toi sur la compréhension et la fiche déjà validées dans la conversation, mises à jour avec cet entretien. Rédige selon les règles ci-dessous, contrôle avec controler_texte (type suite-courte ou suite-transmission) jusqu'à zéro erreur, puis présente la note UNIQUEMENT avec afficher_note_de_suite. Ne donne pas la note en texte libre.\n\nBASE DE DONNÉES — ${BASE}\n\n=== RÈGLES DES NOTES DE SUITE ===\n${ref('8-notes-de-suite.md')}\n\n=== RÈGLES DE LANGAGE ===\n${ref('4-langage.md')}`);
    if (type === 'releve') return texte(`PROCÉDURE RELEVÉ DE DONNÉES. Lis les règles ci-dessous. Construis l'objet releve {choix, textes, screening_types, deductions} à partir de la conversation (fiche et décisions validées en priorité) : pour chaque rubrique à choix, exactement une option du modèle ; n'inclus pas les rubriques qui ont une valeur par défaut, sauf si le dossier dit autre chose ; pour chaque réponse déduite, sa raison dans deductions. Identité et dates : seulement si fournies explicitement (par défaut vides : étiquette). Puis appelle preparer_releve : il refuse les incohérences, applique les valeurs par défaut, écrit le PDF original et l'affiche au clinicien.\n\n=== RÈGLES DU RELEVÉ ===\n${ref('9-releve-donnees.md')}\n\n=== MODÈLE DES RUBRIQUES (options exactes, valeurs par défaut) ===\n${JSON.stringify(RELEVE_MODELE.rubriques)}`);
    if (type === 'analyse') return texte(`PROCÉDURE ANALYSE IPB (DOCUMENT 2). Pas de procédure en 7 étapes : suis l'algorithme du document ci-dessous (étapes 0 à 11). Étapes 1 à 3 silencieuses ; questions seulement si nécessaires (défaut : zéro), en choix multiples, avant de rédiger. Le Document 2 est privé, pour le thérapeute : jamais une note de dossier. Avant de le donner, appelle controler_texte (type document2) et corrige les erreurs ; examine les avertissements. Puis présente-le au clinicien (dans un Canvas si disponible), suivi au plus de quelques lignes de points à signaler (relecture). Le référentiel détaillé du livre (fichier 11-reperes-ipb.md) n'est pas disponible dans cette app : appuie-toi sur les repères du document ci-dessous et sur tes connaissances de ces méthodes, sans citer de chiffres ni de grilles que tu n'as pas.\n\nBASE DE DONNÉES — ${BASE}\n\n=== DOCUMENT MAÎTRE : RÈGLES D'ANALYSE ===\n${ref('10-analyse-ipb.md')}`);
    if (type === 'redaction_analyse') return texte(`PROCÉDURE RÉDACTIONS LIÉES À L'ANALYSE (G1/G2, Document 3, courriers). Seulement sur demande explicite, à partir des Documents 2 validés dans la conversation. Pour une note de suite ou de 4e entretien, appelle plutôt demarrer_note_clinique(type suite).\n\n=== RÈGLES ===\n${ref('12-redactions-analyse.md')}\n\n=== RÈGLES TRANSVERSALES (rappel) ===\n${ref('10-analyse-ipb.md').split('## Règles transversales')[1].split('## Grille de relecture')[0]}`);
    return texte(`${PROCEDURE}\n\nTEXTE DEMANDÉ : ${type}\n\n=== RÈGLES DE L'ÉTAPE 1 ===\n${ref('1-comprehension.md')}`);
  });

  s.registerTool('regles_etape', {
    title: "Règles d'une étape",
    description: "Renvoie le texte exact des règles d'une étape (1 à 7). À appeler au début de chaque étape : ne jamais rédiger de mémoire. Pour l'étape 4, préciser le compartiment validé et le type de texte.",
    inputSchema: { etape: z.number().int().min(1).max(7), compartiment: z.string().optional(), type: TYPE.optional() },
    annotations: LECTURE,
  }, async ({ etape, compartiment, type }) => {
    if (etape === 6) return texte('Étape 6 : appelle controler_texte pour chaque texte, corrige uniquement les passages visés, recommence jusqu\'à zéro erreur (3 tours au plus).');
    let t = (REFS[etape] || []).map(ref).join('\n\n');
    if (etape === 2) t += '\n\nMODÈLE DE FICHE (JSON, sans le bloc decision) :\n' + JSON.stringify(completerFiche({}), null, 1) + '\n\nRÈGLE QUAND UN CHAMP EST NON_EXPLORE :\n' + JSON.stringify(R.champs, null, 1);
    if (etape === 3) t += '\n\nCOMPARTIMENTS (clés à utiliser) : ' + C.cles(R.compartiments).join(', ') + '\nTABLE EXÉCUTABLE :\n' + JSON.stringify({ compartiments: R.compartiments, couplage_evolution_issue: R.couplage_evolution_issue }) + '\n\nMODÈLE DU BLOC decision :\n' + JSON.stringify(MODELE.decision);
    if (etape === 4) {
      if (!compartiment) return texte("Précise le compartiment validé à l'étape 3 (paramètre compartiment).");
      t += '\n\nCOMPARTIMENT IMPOSÉ :\n' + blocCompartiment(compartiment) + '\n\nRÈGLE PAR CHAMP NON_EXPLORE (ATTENTE = écrire [À COMPLÉTER : ce qui manque] ; OMIS = supprimer l\'emplacement ; NORMAL = valeur normale ; DERIVE_AIGU = reprendre le plan aigu, sinon normal) :\n' + JSON.stringify(R.champs);
      if (type !== 'synthese') t += '\n\n=== CANEVAS DE LA NOTE ===\nChaque titre de rubrique seul sur sa ligne, en majuscules.\n' + ref('4-canevas-note.md');
      if (type !== 'note') t += '\n\n=== CANEVAS DE LA SYNTHÈSE ===\nSans titres ; quatre paragraphes (cinq si second diagnostic), puis « Nous nous tenons à sa disposition. » seul.\n' + ref('4-canevas-synthese.md');
    }
    return texte(`=== RÈGLES DE L'ÉTAPE ${etape} ===\n${t}`);
  });

  s.registerTool('afficher_fiche', {
    title: 'Afficher la fiche de faits',
    description: "Étape 2. Affiche la fiche de faits dans un écran modifiable, avec les questions bloquantes. Le clinicien la complète et la valide dans l'écran ; attendre son message « FICHE VALIDÉE » avant l'étape 3.",
    inputSchema: { fiche: FICHE, type: TYPE },
    annotations: LECTURE,
    _meta: avecEcran('Préparation de la fiche…', 'Fiche affichée'),
  }, async ({ fiche, type }) => {
    const f = completerFiche(fiche); delete f.decision;
    const r = C.controlerFiche(f, { sansDecision: true });
    const res = resumeRapport(r);
    return {
      structuredContent: { vue: 'fiche', type, fiche: f, rapport: res },
      content: [{ type: 'text', text: `Fiche affichée. ${res.questions.length} question(s) bloquante(s)${res.questions.length ? ' : ' + res.questions.join(' ; ') : ''}. Le clinicien complète et valide dans l'écran. ATTENDS son message « FICHE VALIDÉE » ; ne passe pas à l'étape 3 avant.` }],
    };
  });

  s.registerTool('afficher_decision', {
    title: 'Afficher la décision',
    description: "Étape 3. Affiche la proposition de diagnostic, compartiment et branches dans un écran ; le contrôle refuse les combinaisons incohérentes. Attendre le message « DÉCISION VALIDÉE » avant l'étape 4.",
    inputSchema: {
      fiche: FICHE.describe('Fiche validée, avec le bloc decision rempli.'), type: TYPE,
      arguments: z.record(z.string(), z.string()).optional().describe('Arguments de chaque proposition'),
      hypotheses_a_explorer: z.array(z.string()).optional(),
      verification_cim: z.object({ effectuee: z.boolean(), sources: z.array(z.string()).optional(), criteres: z.array(z.object({ critere: z.string(), faits: z.string(), rempli: z.string() })).optional(), resume: z.string().optional() }).optional(),
    },
    annotations: LECTURE,
    _meta: avecEcran('Préparation de la décision…', 'Décision affichée'),
  }, async ({ fiche, type, arguments: args, hypotheses_a_explorer, verification_cim }) => {
    const f = completerFiche(fiche);
    f.decision = Object.assign(JSON.parse(JSON.stringify(MODELE.decision)), fiche.decision || {});
    f.decision.branches = Object.assign({ chronique: 'aucune', diagnostic: 0, supplementaires: [], evolution: 0, issue: 0 }, fiche.decision?.branches || {});
    const res = resumeRapport(C.controlerFiche(f, { noteSeule: type === 'note' }));
    return {
      structuredContent: { vue: 'decision', type, fiche: f, rapport: res, arguments: args || {}, hypotheses_a_explorer: hypotheses_a_explorer || [], verification_cim: verification_cim || { effectuee: false } },
      content: [{ type: 'text', text: `Décision affichée (${res.conforme ? 'cohérente' : 'refusée : ' + res.erreurs.concat(res.questions).join(' ; ')}). Le clinicien la corrige et la valide dans l'écran. ATTENDS son message « DÉCISION VALIDÉE » ; ne passe pas à l'étape 4 avant.` }],
    };
  });

  s.registerTool('controler_texte', {
    title: 'Contrôler un texte',
    description: "Contrôle mécanique d'un texte : note ou synthèse (étape 6), note de suite, ou Document 2 (analyse IPB : formules interdites, sous-titres dans le corps, différentiels sans arguments, contre-transfert, cotations chiffrées, longueur). Renvoie les erreurs à corriger.",
    inputSchema: { type: z.enum(['note', 'synthese', 'suite-courte', 'suite-transmission', 'document2']), texte: z.string(), fiche: FICHE.optional().describe('Fiche validée (avec le bloc decision pour la note et la synthèse)') },
    annotations: LECTURE,
  }, async ({ type, texte: t, fiche }) => {
    const r = { note: C.controlerNote, synthese: C.controlerSynthese, 'suite-courte': C.controlerSuiteCourte, 'suite-transmission': C.controlerSuiteTransmission, document2: C.controlerDocument2 }[type](t, fiche || null);
    const res = resumeRapport(r);
    const suite = { document2: 'présente le Document 2 au clinicien (Canvas si disponible) ; examine d\'abord chaque avertissement.', 'suite-courte': 'présente la note avec afficher_note_de_suite.', 'suite-transmission': 'présente la note avec afficher_note_de_suite.' }[type] || 'passe à l\'étape 7 (regles_etape(7), puis afficher_resultat).';
    const consigne = res.erreurs.length ? 'Corrige UNIQUEMENT les passages visés (le reste mot pour mot), puis rappelle controler_texte.' : 'Aucune erreur : ' + suite;
    return texte(JSON.stringify(res, null, 1) + '\n\n' + consigne);
  });

  s.registerTool('afficher_resultat', {
    title: 'Afficher le résultat',
    description: "Étape 7. Présente le texte final dans un écran (copie pour le dossier, champs à compléter, questions). REFUSE les textes qui ne passent pas le contrôle ou une fiche non validée.",
    inputSchema: {
      type: TYPE, fiche: FICHE.describe('Fiche validée avec le bloc decision'),
      note: z.string().optional(), synthese: z.string().optional(), mode: z.string().optional(),
      anomalies: z.object({ langage: z.array(z.string()).optional(), coherence: z.array(z.string()).optional() }).optional(),
      incertains: z.array(z.object({ question: z.string(), options: z.array(z.string()).optional() })).optional(),
      signalement: z.array(z.string()).optional(),
    },
    annotations: LECTURE,
    _meta: avecEcran('Contrôle final…', 'Résultat affiché'),
  }, async (a) => {
    const blocages = [];
    const rf = C.controlerFiche(a.fiche, { noteSeule: a.type === 'note' });
    if (!rf.conforme()) blocages.push(...rf.erreurs.map(e => 'Fiche : ' + e), ...rf.questions.map(q => 'Fiche : à renseigner : ' + (R.champs[q] ? C.libelle(q) : q)));
    const textes = {};
    for (const t of ['note', 'synthese']) {
      const voulu = t === 'note' ? a.type !== 'synthese' : a.type !== 'note';
      if (!voulu) continue;
      if (!a[t]?.trim()) { blocages.push(`${t === 'note' ? 'Note' : 'Synthèse'} manquante`); continue; }
      const r = t === 'note' ? C.controlerNote(a[t], a.fiche) : C.controlerSynthese(a[t], a.fiche);
      blocages.push(...r.erreurs.map(e => `${t === 'note' ? 'Note' : 'Synthèse'} : ${e}`));
      textes[t] = { texte: a[t].trim(), avertissements: r.avert };
    }
    if (blocages.length) return {
      structuredContent: { vue: 'refus', blocages },
      content: [{ type: 'text', text: 'REFUSÉ : le contrôle a trouvé des erreurs. Corrige-les (controler_texte), puis rappelle afficher_resultat. Ne donne pas le texte en clair dans la conversation.\n- ' + blocages.join('\n- ') }],
    };
    return {
      structuredContent: { vue: 'resultat', type: a.type, textes, mode: a.mode || '', anomalies: a.anomalies || {}, incertains: a.incertains || [], signalement: a.signalement || [] },
      content: [{ type: 'text', text: "Résultat affiché et contrôlé. Le clinicien peut copier le texte pour le dossier, compléter les champs en attente et répondre aux questions dans l'écran. Ne recopie pas le texte dans la conversation." }],
    };
  });

  s.registerTool('afficher_note_de_suite', {
    title: 'Afficher la note de suite',
    description: "Présente une note de suite (courte ou de transmission) dans un écran, avec « Copier pour le dossier ». REFUSE une note qui ne passe pas le contrôle.",
    inputSchema: { regime: z.enum(['suite-courte', 'suite-transmission']), texte: z.string(), fiche: FICHE.optional(), incertains: z.array(z.object({ question: z.string(), options: z.array(z.string()).optional() })).optional() },
    annotations: LECTURE,
    _meta: avecEcran('Contrôle de la note de suite…', 'Note de suite affichée'),
  }, async ({ regime, texte: t, fiche, incertains }) => {
    const r = regime === 'suite-courte' ? C.controlerSuiteCourte(t, fiche || null) : C.controlerSuiteTransmission(t);
    if (r.erreurs.length) return {
      structuredContent: { vue: 'refus', blocages: r.erreurs },
      content: [{ type: 'text', text: 'REFUSÉ : corrige ces erreurs (controler_texte), puis rappelle afficher_note_de_suite. Ne donne pas la note en clair.\n- ' + r.erreurs.join('\n- ') }],
    };
    return {
      structuredContent: { vue: 'resultat', type: regime, textes: { [regime]: { texte: t.trim(), avertissements: r.avert } }, mode: '', anomalies: {}, incertains: incertains || [], signalement: [] },
      content: [{ type: 'text', text: 'Note de suite affichée et contrôlée. Ne la recopie pas dans la conversation.' }],
    };
  });

  s.registerTool('preparer_releve', {
    title: 'Préparer le relevé de données',
    description: "Relevé de données UNIL-EPFL : vérifie les réponses, applique les valeurs par défaut du clinicien, écrit le PDF original (2 pages) et l'affiche avec un lien de téléchargement valable 15 minutes. REFUSE les options inexistantes et les rubriques incohérentes.",
    inputSchema: {
      releve: z.object({
        choix: z.record(z.string(), z.string()).optional().describe('rubrique → option exacte du formulaire'),
        textes: z.record(z.string(), z.string()).optional().describe('rubrique → texte'),
        screening_types: z.array(z.string()).optional(),
        deductions: z.record(z.string(), z.string()).optional().describe('rubrique → raison de la déduction'),
      }),
    },
    annotations: LECTURE,
    _meta: avecEcran('Remplissage du relevé…', 'Relevé prêt'),
  }, async ({ releve }) => {
    const v = verifierReleve(releve, RELEVE_MODELE, RELEVE_POSITIONS, true);
    if (v.erreurs.length) return {
      structuredContent: { vue: 'refus', blocages: v.erreurs },
      content: [{ type: 'text', text: 'REFUSÉ : corrige ces points dans releve, puis rappelle preparer_releve.\n- ' + v.erreurs.join('\n- ') }],
    };
    const { octets, tropLongs } = await produireReleve(v);
    const lien = `${baseUrl}/releve/${garderPdf(octets)}.pdf`;
    const reponses = Object.entries(v.choix).map(([k, val]) => [k, val]).concat(Object.entries(v.textes).filter(([, val]) => String(val).trim()));
    return {
      structuredContent: { vue: 'releve', lien, reponses, appliques: v.appliques, deductions: releve.deductions || {}, vides: v.vides, attente: v.attente, tropLongs, types: v.types },
      content: [{ type: 'text', text: `Relevé prêt (lien valable 15 minutes, affiché dans l'écran). Rubriques laissées vides : ${v.vides.join(', ') || 'aucune'}. En attente de documents : ${v.attente.join(', ') || 'rien'}. Pose en un seul bloc les questions pour les rubriques vides.` }],
    };
  });

  s.registerTool('nettoyer_pour_dossier', {
    title: 'Nettoyer pour le dossier',
    description: 'Rend un texte compatible Latin-1 pour le logiciel du dossier (apostrophes, guillemets, tirets, points de suspension ; accents conservés).',
    inputSchema: { texte: z.string() },
    annotations: LECTURE,
  }, async ({ texte: t }) => texte(C.nettoyer(t)));

  return s;
}

/* ---- Serveur HTTP (sans état) ---- */
const app = express();
app.use(express.json({ limit: '2mb' }));
app.post('/mcp', async (req, res) => {
  // Journal minimal pour le diagnostic : nom de la méthode et de l'outil, jamais le contenu.
  const b = req.body || {};
  for (const m of Array.isArray(b) ? b : [b]) if (m && m.method) console.log('MCP', m.method, m.params && (m.params.name || m.params.uri) || '');
  const hote = req.get('x-forwarded-host') || req.get('host');
  const proto = req.get('x-forwarded-proto') || req.protocol;
  const serveur = creerServeur(`${proto}://${hote}`);
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined, enableJsonResponse: true });
  res.on('close', () => { transport.close(); serveur.close(); });
  try {
    await serveur.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (e) {
    console.error('Erreur MCP :', e.message);
    if (!res.headersSent) res.status(500).json({ jsonrpc: '2.0', error: { code: -32603, message: 'Erreur interne' }, id: null });
  }
});
app.all('/mcp', (req, res) => res.status(405).json({ jsonrpc: '2.0', error: { code: -32000, message: 'Méthode non autorisée' }, id: null }));
app.get('/releve/:id.pdf', (req, res) => {
  const octets = PDFS.get(req.params.id);
  if (!octets) return res.status(404).type('text').send('Lien expiré (15 minutes) : redemandez le relevé dans ChatGPT.');
  res.set({ 'Content-Type': 'application/pdf', 'Content-Disposition': 'attachment; filename="releve_donnees.pdf"', 'Cache-Control': 'no-store' }).send(octets);
});
app.get('/', (req, res) => res.type('text').send('Note clinique EPFL : serveur actif. Adresse à donner à ChatGPT : <cette adresse>/mcp'));

if (require.main === module) {
  const PORT = Number(process.env.PORT) || 8787;
  app.listen(PORT, () => console.log(`Note clinique EPFL : http://localhost:${PORT}/mcp`));
}
module.exports = { app, creerServeur };
