// Manual MCP client using stdio directly (no SDK)
// This demonstrates the raw JSON-RPC protocol communication

import { type ChildProcess, spawn } from "node:child_process";
import { createInterface } from "node:readline";

interface JsonRpcMessage {
	jsonrpc: "2.0";
	id?: string | number;
	method?: string;
	params?: unknown;
	result?: unknown;
	error?: {
		code: number;
		message: string;
		data?: unknown;
	};
}

class ManualMcpClient {
	private serverProcess: ChildProcess;
	private messageId = 1;
	private pendingRequests = new Map<
		string | number,
		(response: JsonRpcMessage) => void
	>();

	constructor() {
		// Start the MCP server process
		this.serverProcess = spawn("node", ["dist/index.js"], {
			stdio: ["pipe", "pipe", "pipe"],
		});

		// Set up readline to read server responses line by line
		if (this.serverProcess.stdout) {
			const rl = createInterface({
				input: this.serverProcess.stdout,
			});

			rl.on("line", (line) => {
				try {
					const message: JsonRpcMessage = JSON.parse(line);
					this.handleServerMessage(message);
				} catch (error) {
					console.error("Failed to parse server message:", line, error);
				}
			});
		}

		// Handle server errors
		this.serverProcess.stderr?.on("data", (data: Buffer) => {
			console.error("Server stderr:", data.toString());
		});

		this.serverProcess.on("exit", (code: number | null) => {
			console.log(`Server process exited with code ${code}`);
		});
	}

	private handleServerMessage(message: JsonRpcMessage) {
		console.log("← Received from server:", JSON.stringify(message, null, 2));

		// Handle responses to our requests
		if (message.id !== undefined && this.pendingRequests.has(message.id)) {
			const resolver = this.pendingRequests.get(message.id);
			if (resolver) {
				this.pendingRequests.delete(message.id);
				resolver(message);
			}
		}
	}

	private sendMessage(message: JsonRpcMessage): Promise<JsonRpcMessage> {
		const messageStr = JSON.stringify(message);
		console.log("→ Sending to server:", messageStr);

		this.serverProcess.stdin?.write(`${messageStr}\n`);

		// If this is a request (has an id), wait for response
		if (message.id !== undefined) {
			return new Promise((resolve) => {
				if (message.id !== undefined) {
					this.pendingRequests.set(message.id, resolve);
				}
			});
		}

		return Promise.resolve(message);
	}

	private getNextId(): number {
		return this.messageId++;
	}

	async initialize(): Promise<JsonRpcMessage> {
		const initMessage: JsonRpcMessage = {
			jsonrpc: "2.0",
			method: "initialize",
			params: {
				protocolVersion: "2025-03-26",
				capabilities: {},
				clientInfo: {
					name: "manual-debug-client",
					version: "1.0.0",
				},
			},
			id: this.getNextId(),
		};

		const response = await this.sendMessage(initMessage);

		// Send initialized notification
		const initializedNotification: JsonRpcMessage = {
			jsonrpc: "2.0",
			method: "notifications/initialized",
		};

		await this.sendMessage(initializedNotification);

		return response;
	}

	async ping(): Promise<JsonRpcMessage> {
		const pingMessage: JsonRpcMessage = {
			jsonrpc: "2.0",
			method: "ping",
			id: this.getNextId(),
		};

		return this.sendMessage(pingMessage);
	}

	async introspectSchema(): Promise<JsonRpcMessage> {
		const introspectMessage: JsonRpcMessage = {
			jsonrpc: "2.0",
			method: "tools/call",
			params: {
				name: "introspect-schema",
				arguments: {},
			},
			id: this.getNextId(),
		};

		return this.sendMessage(introspectMessage);
	}

	async listTools(): Promise<JsonRpcMessage> {
		const listToolsMessage: JsonRpcMessage = {
			jsonrpc: "2.0",
			method: "tools/list",
			params: {},
			id: this.getNextId(),
		};

		return this.sendMessage(listToolsMessage);
	}

	async close() {
		this.serverProcess.kill();
	}
}

// Main execution
async function main() {
	console.log("🚀 Starting manual MCP client...");

	const client = new ManualMcpClient();

	try {
		// Wait a bit for the server to start
		await new Promise((resolve) => setTimeout(resolve, 1000));

		console.log("\n📋 Step 1: Initialize connection");
		const initResponse = await client.initialize();
		console.log("✅ Initialization complete");

		console.log("\n📋 Step 2: Ping server");
		const pingResponse = await client.ping();
		console.log("✅ Ping successful");

		console.log("\n📋 Step 3: List available tools");
		const toolsResponse = await client.listTools();
		console.log("✅ Tools listed");

		console.log("\n📋 Step 4: Call introspect-schema tool");
		const schemaResponse = await client.introspectSchema();
		console.log("✅ Schema introspection complete");

		console.log("\n🎉 All operations completed successfully!");
	} catch (error) {
		console.error("❌ Error:", error);
	} finally {
		console.log("\n🔚 Closing client...");
		client.close();
	}
}

main().catch(console.error);
