#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer } from "node:http";
import { appendFileSync } from "node:fs";

const DEBUG = process.env.CHANNEL_DEBUG === "1";
const LOG_FILE = "/tmp/herokid-channel.log";
function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  if (DEBUG) appendFileSync(LOG_FILE, line);
  process.stderr.write(line);
}

// --- Configuration ---
const PORT = parseInt(process.env.CHANNEL_PORT || "9999", 10);
const TOKEN = process.env.CHANNEL_TOKEN || null;
const SERVER_NAME = "herokid";

// --- MCP Server (stdio, channel capability) ---
const mcp = new Server(
  { name: SERVER_NAME, version: "1.0.0" },
  {
    capabilities: {
      experimental: { "claude/channel": {} },
    },
    instructions: [
      "You receive real-time notifications from local processes via the herokid channel.",
      "Each message has a type (e.g. task-complete, manual, alert) and content.",
      "When you receive a task-complete notification, read the referenced output file and act on the results.",
      "When you receive a manual message, treat it as a user request.",
    ].join(" "),
  }
);

// Track message count for status checks
let messageCount = 0;
let lastMessage = null;

// --- HTTP Listener (accepts POST /push) ---
const http = createServer((req, res) => {
  // Health check
  if (req.method === "GET" && req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", messages: messageCount, last: lastMessage }));
    return;
  }

  // Only accept POST /push
  if (req.method !== "POST" || req.url !== "/push") {
    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "POST /push or GET /health only" }));
    return;
  }

  // Optional bearer token auth
  if (TOKEN) {
    const auth = req.headers.authorization || "";
    if (auth !== `Bearer ${TOKEN}`) {
      res.writeHead(401, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "unauthorized" }));
      return;
    }
  }

  let body = "";
  req.on("data", (chunk) => (body += chunk));
  req.on("end", async () => {
    try {
      const data = JSON.parse(body);
      const content = data.content;

      if (!content) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "missing required field: content" }));
        return;
      }

      // Build meta object — keys must be identifiers (letters, digits, underscores)
      const meta = {};
      if (data.type) meta.type = String(data.type);
      if (data.source) meta.source = String(data.source);
      if (data.meta && typeof data.meta === "object") {
        for (const [k, v] of Object.entries(data.meta)) {
          if (/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(k)) {
            meta[k] = String(v);
          }
        }
      }

      // Push to Claude Code session via MCP channel notification
      try {
        log(`Sending notification: ${JSON.stringify({ content, meta })}`);
        await mcp.notification({
          method: "notifications/claude/channel",
          params: { content, meta },
        });
        log(`Notification sent successfully`);
      } catch (notifErr) {
        log(`Notification FAILED: ${notifErr.message}\n${notifErr.stack}`);
      }

      messageCount++;
      lastMessage = { type: data.type || "unknown", time: new Date().toISOString() };

      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok: true, messages: messageCount }));
    } catch (err) {
      log(`Parse error: ${err.message}`);
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "invalid JSON" }));
    }
  });
});

// --- Graceful shutdown ---
function shutdown(signal) {
  log(`Shutting down (${signal})`);
  http.close();
  process.exit(0);
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGHUP", () => shutdown("SIGHUP"));

// Exit when parent (Claude Code) closes stdin
process.stdin.on("end", () => shutdown("stdin-closed"));
process.stdin.on("close", () => shutdown("stdin-closed"));

// --- Kill orphan on startup ---
async function killOrphan() {
  const { execSync } = await import("node:child_process");
  try {
    const out = execSync(`lsof -ti :${PORT}`, { encoding: "utf8" }).trim();
    if (out) {
      const pids = out.split("\n").map(p => p.trim()).filter(Boolean);
      for (const pid of pids) {
        if (pid !== String(process.pid)) {
          process.kill(Number(pid), "SIGTERM");
          log(`Killed orphan process on port ${PORT} (PID ${pid})`);
        }
      }
      // Brief wait for port to free up
      await new Promise(r => setTimeout(r, 500));
    }
  } catch {
    // No process on port — good
  }
}

// --- Startup ---
async function main() {
  // Kill any orphan from a previous session
  await killOrphan();

  // Start HTTP listener (bind to localhost only)
  http.listen(PORT, "127.0.0.1", () => {
    log(`HTTP listener on http://127.0.0.1:${PORT}`);
  });

  // Connect MCP over stdio
  const transport = new StdioServerTransport();
  await mcp.connect(transport);
  log(`MCP channel connected`);
}

main().catch((err) => {
  log(`Fatal: ${err.message}`);
  process.exit(1);
});
