/* Simule ChatGPT avec le standard MCP Apps : l'écran est dans une iframe et dialogue par messages. */
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { chromium } = require('playwright-core');
const { demarrer } = require('./client.js');
const EX = path.join(__dirname, '..', '..', 'note-clinique-epfl', 'exemples');
const CHROMIUM = process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
(async () => {
  const { client, fermer } = await demarrer();
  const outils = (await client.listTools()).tools;
  const fiche = outils.find(t => t.name === 'afficher_fiche');
  assert.strictEqual(fiche._meta.ui.resourceUri, 'ui://widget/note-clinique-v2-mcp.html');
  const res = (await client.readResource({ uri: 'ui://widget/note-clinique-v2-mcp.html' })).contents[0];
  assert.strictEqual(res.mimeType, 'text/html;profile=mcp-app');
  console.log('  ok  outil lié à une ressource text/html;profile=mcp-app');
  const f = JSON.parse(fs.readFileSync(path.join(EX, 'fiche_exemple.json'), 'utf8')); delete f.decision;
  const sortie = (await client.callTool({ name: 'afficher_fiche', arguments: { fiche: f, type: 'note' } })).structuredContent;
  await fermer();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mcpapps-'));
  fs.writeFileSync(path.join(dir, 'ecran.html'), res.text);
  fs.writeFileSync(path.join(dir, 'hote.html'), `<!doctype html><meta charset="utf-8"><iframe id="f" src="ecran.html" style="width:760px;height:300px"></iframe><script>
    window.journal = { tailles: [], messages: [] };
    const f = document.getElementById('f');
    addEventListener('message', e => {
      const m = e.data; if (!m || m.jsonrpc !== '2.0') return;
      const repondre = r => f.contentWindow.postMessage({ jsonrpc: '2.0', id: m.id, result: r }, '*');
      if (m.method === 'ui/initialize') repondre({ protocolVersion: '2026-01-26', hostInfo: { name: 'hote-test', version: '1' }, hostCapabilities: {}, hostContext: { theme: 'light' } });
      if (m.method === 'ui/notifications/initialized') f.contentWindow.postMessage({ jsonrpc: '2.0', method: 'ui/notifications/tool-result', params: { content: [], structuredContent: ${JSON.stringify(sortie)} } }, '*');
      if (m.method === 'ui/notifications/size-changed') journal.tailles.push(m.params.height);
      if (m.method === 'ui/message') { journal.messages.push(m.params.content[0].text); repondre({}); }
    });
  </script>`);
  const b = await chromium.launch({ executablePath: CHROMIUM });
  const p = await b.newPage(); const err = []; p.on('pageerror', e => err.push(e.message));
  await p.goto('file://' + path.join(dir, 'hote.html'));
  const ecran = p.frameLocator('#f');
  await ecran.locator('#valider').waitFor();
  console.log('  ok  écran affiché via le standard MCP Apps');
  const tailles = await p.evaluate(() => journal.tailles);
  assert(tailles.length && Math.max(...tailles) > 400, 'hauteur non annoncée : ' + tailles); console.log('  ok  hauteur annoncée à l\'hôte : ' + Math.max(...tailles) + ' px');
  await ecran.locator('#valider').click();
  await p.waitForFunction(() => journal.messages.length > 0);
  assert((await p.evaluate(() => journal.messages[0])).startsWith('FICHE VALIDÉE')); console.log('  ok  « FICHE VALIDÉE » envoyé par ui/message');
  assert(!err.length, err.join());
  await b.close();
  console.log('MCP APPS : tous les tests passent');
})().catch(e => { console.error('ÉCHEC', e); process.exit(1); });
