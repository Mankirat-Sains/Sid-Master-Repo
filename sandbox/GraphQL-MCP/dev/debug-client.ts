// Small debug client to test a few specific interactions

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
	command: "node",
	args: ["dist/index.js"],
});

const client = new Client({
	name: "debug-client",
	version: "1.0.0",
});

await client.connect(transport);

// Call introspect-schema with undefined argument
const result = await client.callTool({
	name: "introspect-schema",
	arguments: {},
});

console.log(result);
