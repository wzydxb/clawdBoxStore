#!/usr/bin/env node
import { createServer } from 'node:http';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const PORT = Number.parseInt(process.env.OPENCLI_HOST_BRIDGE_PORT || '19826', 10);
const HOST = process.env.OPENCLI_HOST_BRIDGE_HOST || '0.0.0.0';
const TOKEN = process.env.OPENCLI_HOST_BRIDGE_TOKEN || '';
const COMMAND = process.env.OPENCLI_HOST_COMMAND || 'npx';
const PREFIX_ARGS = process.env.OPENCLI_HOST_COMMAND
  ? []
  : ['-y', '@jackwener/opencli'];
const TIMEOUT_MS = Number.parseInt(process.env.OPENCLI_HOST_BRIDGE_TIMEOUT_MS || '60000', 10);

function sendJson(res, status, payload) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(payload));
}

function unauthorized(req, res) {
  sendJson(res, 401, { ok: false, error: 'unauthorized', error_code: 'unauthorized', recoverability: 'operator_action' });
}

function classifyFailure(stderr) {
  const text = String(stderr || '');
  if (/not found|ENOENT|command not found/i.test(text)) {
    return { error_code: 'command_missing', recoverability: 'config_or_install' };
  }
  if (/No supported browser found/i.test(text)) {
    return { error_code: 'browser_unavailable', recoverability: 'install_browser' };
  }
  if (/missing_brave_api_key/i.test(text)) {
    return { error_code: 'missing_brave_api_key', recoverability: 'configure_api_key' };
  }
  if (/timed out|timeout/i.test(text)) {
    return { error_code: 'timeout', recoverability: 'retryable' };
  }
  if (/fetch failed|Extension not connected|host bridge/i.test(text)) {
    return { error_code: 'bridge_unreachable', recoverability: 'retryable' };
  }
  return { error_code: 'upstream_error', recoverability: 'inspect' };
}

const server = createServer(async (req, res) => {
  if (req.url === '/health' && req.method === 'GET') {
    try {
      const { stdout, stderr } = await execFileAsync(COMMAND, [...PREFIX_ARGS, '--version'], {
        timeout: Math.min(TIMEOUT_MS, 15000),
        maxBuffer: 1024 * 1024,
      });
      return sendJson(res, 200, {
        ok: true,
        command: COMMAND,
        prefixArgs: PREFIX_ARGS,
        capability_snapshot: {
          command_resolved: true,
          opencli_version: String(stdout).trim(),
          stderr: String(stderr || ''),
        },
      });
    } catch (err) {
      const stderr = typeof err?.stderr === 'string' ? err.stderr : err?.stderr?.toString?.() ?? err?.message ?? String(err);
      return sendJson(res, 200, {
        ok: false,
        command: COMMAND,
        prefixArgs: PREFIX_ARGS,
        capability_snapshot: {
          command_resolved: false,
        },
        stderr,
        ...classifyFailure(stderr),
      });
    }
  }

  if (req.url !== '/exec' || req.method !== 'POST') {
    return sendJson(res, 404, { ok: false, error: 'not_found' });
  }

  if (TOKEN) {
    const header = req.headers.authorization || '';
    if (header !== `Bearer ${TOKEN}`) {
      return unauthorized(req, res);
    }
  }

  let raw = '';
  for await (const chunk of req) raw += chunk;
  let body;
  try {
    body = raw ? JSON.parse(raw) : {};
  } catch {
    return sendJson(res, 400, { ok: false, error: 'invalid_json' });
  }

  const args = Array.isArray(body.args) ? body.args.filter((v) => typeof v === 'string') : [];
  try {
    const { stdout, stderr } = await execFileAsync(COMMAND, [...PREFIX_ARGS, ...args], {
      timeout: TIMEOUT_MS,
      maxBuffer: 20 * 1024 * 1024,
    });
    const text = String(stdout);
    let json;
    try {
      json = text.trim() ? JSON.parse(text) : undefined;
    } catch {
      json = undefined;
    }
    return sendJson(res, 200, { ok: true, stdout: text, stderr: String(stderr), ...(json !== undefined ? { json } : {}) });
  } catch (err) {
    const stderr = typeof err?.stderr === 'string' ? err.stderr : err?.stderr?.toString?.() ?? err?.message ?? String(err);
    return sendJson(res, 200, {
      ok: false,
      stdout: typeof err?.stdout === 'string' ? err.stdout : err?.stdout?.toString?.() ?? '',
      stderr,
      ...classifyFailure(stderr),
    });
  }
});

server.listen(PORT, HOST, () => {
  process.stdout.write(`opencli-host-bridge listening on http://${HOST}:${PORT}\n`);
});
