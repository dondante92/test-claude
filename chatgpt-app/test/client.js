/* Client MCP de test : démarre le serveur sur un port libre et appelle les outils comme ChatGPT. */
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StreamableHTTPClientTransport } = require('@modelcontextprotocol/sdk/client/streamableHttp.js');
const { app } = require('../server.js');
async function demarrer() {
  const http = app.listen(0);
  await new Promise(r => http.once('listening', r));
  const client = new Client({ name: 'test', version: '1.0.0' });
  await client.connect(new StreamableHTTPClientTransport(new URL(`http://localhost:${http.address().port}/mcp`)));
  return { client, fermer: async () => { await client.close(); http.close(); } };
}
module.exports = { demarrer };
