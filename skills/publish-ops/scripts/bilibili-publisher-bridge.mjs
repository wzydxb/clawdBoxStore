#!/usr/bin/env node
import { createServer } from 'node:http';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { existsSync, mkdirSync, readFileSync, writeFileSync, createWriteStream, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const execFileAsync = promisify(execFile);
const PORT = Number.parseInt(process.env.BILIBILI_PUBLISHER_BRIDGE_PORT || '19828', 10);
const HOST = process.env.BILIBILI_PUBLISHER_BRIDGE_HOST || '0.0.0.0';
const TOKEN = process.env.BILIBILI_PUBLISHER_BRIDGE_TOKEN || '';
const OPENCLI_COMMAND = process.env.OPENCLI_HOST_COMMAND || 'npx';
const OPENCLI_PREFIX_ARGS = process.env.OPENCLI_HOST_COMMAND ? [] : ['-y', '@jackwener/opencli'];
const PYTHON_COMMAND = process.env.BILIBILI_PUBLISHER_PYTHON || 'python3';
const TIMEOUT_MS = Number.parseInt(process.env.BILIBILI_PUBLISHER_BRIDGE_TIMEOUT_MS || '120000', 10);
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const PY_HELPER = path.resolve(SCRIPT_DIR, './bilibili_api_ops.py');
const HOST_CLAWBOX_ROOT = process.env.CLAWBOX_HOST_OPENCLAW_DIR || path.resolve(SCRIPT_DIR, '../clawbox-data');
const CONTAINER_CLAWBOX_ROOT = process.env.BILIBILI_PUBLISHER_CONTAINER_ROOT || '/home/node/.clawbox';
const STATE_DIR = path.resolve(SCRIPT_DIR, '../clawbox-data/workspace/.clawbox');
const STATE_FILE = path.join(STATE_DIR, 'bilibili-ops.json');
const PIPELINE_LEDGER_FILE = path.join(STATE_DIR, 'pipeline-ledger.json');
const DEFAULT_INTERVAL_MS = 120000;
const MIN_PUBLISH_VIDEO_BYTES = 5 * 1024 * 1024;
const MIN_PUBLISH_DURATION_SECONDS = 20;
const MIN_PUBLISH_SCENE_COUNT = 3;

const jobs = new Map();
const timers = new Map();

function sendJson(res, status, payload) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(payload));
}

function checkAuth(req, res) {
  if (!TOKEN) return true;
  const header = req.headers.authorization || '';
  if (header !== `Bearer ${TOKEN}`) {
    sendJson(res, 401, { ok: false, error: 'unauthorized' });
    return false;
  }
  return true;
}

function mapContainerPathToHost(filePath) {
  if (typeof filePath !== 'string' || !filePath.trim()) {
    return '';
  }
  const normalized = path.resolve(filePath.trim());
  if (!normalized.startsWith(CONTAINER_CLAWBOX_ROOT)) {
    return normalized;
  }
  const relativePath = path.relative(CONTAINER_CLAWBOX_ROOT, normalized);
  return path.join(HOST_CLAWBOX_ROOT, relativePath);
}

function normalizeLegacyVideoPath(filePath) {
  if (typeof filePath !== 'string' || !filePath.trim()) return '';
  const trimmed = filePath.trim();
  if (!/output\.mp4$/.test(trimmed)) return trimmed;
  const candidate = trimmed.replace(/output\.mp4$/, 'video.mp4');
  return candidate;
}

async function downloadFile(url, targetPath) {
  const res = await fetch(url);
  if (!res.ok || !res.body) {
    throw new Error(`download failed: ${res.status}`);
  }
  await new Promise((resolve, reject) => {
    const stream = createWriteStream(targetPath);
    res.body.pipeTo(new WritableStream({
      write(chunk) {
        return new Promise((res2, rej2) => stream.write(Buffer.from(chunk), (err) => err ? rej2(err) : res2()));
      },
      close() {
        stream.end(() => resolve());
      },
      abort(err) {
        stream.destroy(err);
        reject(err);
      }
    })).catch(reject);
  });
}

function assessVideoForPublish(payload, videoPath) {
  const reportPath = mapContainerPathToHost('/home/node/.clawbox/workspace-content-strategist-1/render/render_report.json');
  const result = {
    ok: true,
    reasons: [],
    size_bytes: 0,
    duration_seconds: 0,
    scene_count: 0,
  };
  try {
    if (!videoPath || !existsSync(videoPath)) {
      result.ok = false;
      result.reasons.push('video_missing');
      return result;
    }
    result.size_bytes = statSync(videoPath).size;
    if (result.size_bytes < MIN_PUBLISH_VIDEO_BYTES) {
      result.ok = false;
      result.reasons.push('video_too_small');
    }
    if (reportPath && existsSync(reportPath)) {
      const report = JSON.parse(readFileSync(reportPath, 'utf8'));
      result.duration_seconds = Number(report?.duration_seconds) || 0;
      result.scene_count = Number(report?.segment_count || report?.scene_count) || 0;
      if (result.duration_seconds < MIN_PUBLISH_DURATION_SECONDS) {
        result.ok = false;
        result.reasons.push('duration_too_short');
      }
      if (result.scene_count < MIN_PUBLISH_SCENE_COUNT) {
        result.ok = false;
        result.reasons.push('scene_count_too_low');
      }
    }
    return result;
  } catch {
    result.ok = false;
    result.reasons.push('quality_check_failed');
    return result;
  }
}

async function ensureHostVideoPath(payload) {
  const rawVideoPath = normalizeLegacyVideoPath(String(payload?.video_path || '').trim());
  const mapped = mapContainerPathToHost(rawVideoPath);
  if (mapped && existsSync(mapped)) {
    return mapped;
  }
  const fallbackUrl = String(payload?.download_url || payload?.play_url || '').trim();
  if (!fallbackUrl) {
    return mapped;
  }
  const downloadsDir = path.join(STATE_DIR, 'published-videos');
  mkdirSync(downloadsDir, { recursive: true });
  const fileName = `${Date.now()}-video.mp4`;
  const targetPath = path.join(downloadsDir, fileName);
  try {
    await downloadFile(fallbackUrl, targetPath);
    return targetPath;
  } catch {
    return mapped;
  }
}

async function normalizeVideoForBilibili(inputPath) {
  if (!inputPath || !existsSync(inputPath)) {
    return inputPath;
  }
  const normalizedDir = path.join(STATE_DIR, 'normalized-videos');
  mkdirSync(normalizedDir, { recursive: true });
  const normalizedPath = path.join(normalizedDir, `${Date.now()}-bilibili.mp4`);
  try {
    await execFileAsync('ffmpeg', [
      '-y',
      '-i', inputPath,
      '-c:v', 'libx264',
      '-preset', 'medium',
      '-profile:v', 'high',
      '-level', '4.0',
      '-pix_fmt', 'yuv420p',
      '-r', '25',
      '-g', '50',
      '-movflags', '+faststart',
      '-c:a', 'aac',
      '-b:a', '128k',
      '-ar', '44100',
      '-ac', '2',
      normalizedPath,
    ], {
      timeout: TIMEOUT_MS,
      maxBuffer: 20 * 1024 * 1024,
    });
    return normalizedPath;
  } catch {
    return inputPath;
  }
}

function readState() {
  if (!existsSync(STATE_FILE)) {
    return { jobs: [] };
  }
  try {
    const parsed = JSON.parse(readFileSync(STATE_FILE, 'utf8'));
    return parsed && typeof parsed === 'object' && Array.isArray(parsed.jobs) ? parsed : { jobs: [] };
  } catch {
    return { jobs: [] };
  }
}

function writeState() {
  mkdirSync(STATE_DIR, { recursive: true });
  writeFileSync(STATE_FILE, JSON.stringify({ jobs: Array.from(jobs.values()) }, null, 2), 'utf8');
}

function readPipelineLedger() {
  if (!existsSync(PIPELINE_LEDGER_FILE)) {
    return { runs: [] };
  }
  try {
    const parsed = JSON.parse(readFileSync(PIPELINE_LEDGER_FILE, 'utf8'));
    return parsed && typeof parsed === 'object' && Array.isArray(parsed.runs) ? parsed : { runs: [] };
  } catch {
    return { runs: [] };
  }
}

function updatePipelineLedger(runId, patch) {
  if (!runId) return;
  const ledger = readPipelineLedger();
  const runs = Array.isArray(ledger.runs) ? ledger.runs : [];
  const idx = runs.findIndex((item) => item && item.run_id === runId);
  const next = {
    ...(idx >= 0 ? runs[idx] : { run_id: runId }),
    ...patch,
    updated_at: Date.now(),
  };
  if (idx >= 0) runs[idx] = next;
  else runs.push(next);
  mkdirSync(STATE_DIR, { recursive: true });
  writeFileSync(PIPELINE_LEDGER_FILE, JSON.stringify({ runs }, null, 2), 'utf8');
}

function enrichPayloadFromWorkspace(payload) {
  const enriched = { ...(payload || {}) };
  const workspaceDir = path.resolve(SCRIPT_DIR, '../clawbox-data/workspace-content-strategist-1');
  const pkgPath = path.join(workspaceDir, 'production_package.json');
  const executionPath = path.join(workspaceDir, 'execution.json');
  const renderReportPath = path.join(workspaceDir, 'render', 'render_report.json');
  if (existsSync(pkgPath)) {
    try {
      const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
      const metadata = pkg?.publish_metadata || {};
      if (!enriched.run_id) enriched.run_id = metadata.run_id || '';
      if (!enriched.topic_input) enriched.topic_input = metadata.title || pkg?.cover_text || '';
      if (!enriched.title) enriched.title = metadata.title || (Array.isArray(metadata.title_candidates) ? metadata.title_candidates[0] : '') || '';
      if (!enriched.reply_template) enriched.reply_template = metadata.reply_template || '';
      if (!enriched.video_path) enriched.video_path = '/home/node/.clawbox/workspace-content-strategist-1/render/video.mp4';
      enriched.video_path = normalizeLegacyVideoPath(String(enriched.video_path || ''));
    } catch {
      // ignore parse errors
    }
  }
  if (existsSync(executionPath)) {
    try {
      const execution = JSON.parse(readFileSync(executionPath, 'utf8'));
      if (!enriched.run_id) enriched.run_id = execution?.run_id || '';
      if (!enriched.video_path && execution?.render?.video_path) enriched.video_path = execution.render.video_path;
      enriched.video_path = normalizeLegacyVideoPath(String(enriched.video_path || ''));
    } catch {
      // ignore parse errors
    }
  }
  if (existsSync(renderReportPath)) {
    try {
      const report = JSON.parse(readFileSync(renderReportPath, 'utf8'));
      if (!enriched.video_path && report?.video_path) enriched.video_path = report.video_path;
      if (!enriched.play_url && report?.play_url) enriched.play_url = report.play_url;
      if (!enriched.download_url && report?.download_url) enriched.download_url = report.download_url;
    } catch {
      // ignore parse errors
    }
  }
  return enriched;
}

async function runOpencli(args) {
  try {
    const { stdout, stderr } = await execFileAsync(OPENCLI_COMMAND, [...OPENCLI_PREFIX_ARGS, ...args], {
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
    return { ok: true, stdout: text, stderr: String(stderr), ...(json !== undefined ? { json } : {}) };
  } catch (err) {
    return {
      ok: false,
      stdout: typeof err?.stdout === 'string' ? err.stdout : err?.stdout?.toString?.() ?? '',
      stderr: typeof err?.stderr === 'string' ? err.stderr : err?.stderr?.toString?.() ?? err?.message ?? String(err),
    };
  }
}

function buildResult(json) {
  return { ok: true, stdout: JSON.stringify(json), stderr: '', json };
}

function defaultReplyTemplate() {
  return '收到，这里先自动回复确认一下，后面我会继续更新。';
}

function cleanPythonStderr(stderr) {
  return String(stderr || '')
    .split('\n')
    .filter((line) => !/urllib3.*NotOpenSSLWarning|warnings\.warn\(/.test(line))
    .join('\n')
    .trim();
}

async function runPythonHelper(args) {
  try {
    const { stdout, stderr } = await execFileAsync(PYTHON_COMMAND, [PY_HELPER, ...args], {
      timeout: TIMEOUT_MS,
      maxBuffer: 20 * 1024 * 1024,
    });
    const text = String(stdout || '').trim();
    let json;
    try {
      json = text ? JSON.parse(text) : undefined;
    } catch {
      const start = Math.max(text.lastIndexOf('\n{'), text.lastIndexOf('\r{'));
      const candidate = start >= 0 ? text.slice(start + 1).trim() : text.slice(text.indexOf('{')).trim();
      try {
        json = candidate ? JSON.parse(candidate) : undefined;
      } catch {
        json = undefined;
      }
    }
    return { ok: true, stdout: text, stderr: cleanPythonStderr(stderr), ...(json !== undefined ? { json } : {}) };
  } catch (err) {
    return {
      ok: false,
      stdout: typeof err?.stdout === 'string' ? err.stdout : err?.stdout?.toString?.() ?? '',
      stderr: cleanPythonStderr(typeof err?.stderr === 'string' ? err.stderr : err?.stderr?.toString?.() ?? err?.message ?? String(err)),
    };
  }
}

function jobKey(input) {
  const aid = String(input?.aid || '').trim();
  const bvid = String(input?.bvid || '').trim();
  return aid ? `video:${aid}` : bvid ? `video:${bvid}` : '';
}

function normalizeJob(input) {
  const key = jobKey(input);
  if (!key) {
    throw new Error('missing aid_or_bvid');
  }
  const generatedRunId = `autofill-${Date.now()}`;
  return {
    key,
    platform: 'bilibili',
    target_type: 'video',
    aid: input?.aid ? String(input.aid).trim() : '',
    bvid: input?.bvid ? String(input.bvid).trim() : '',
    title: input?.title ? String(input.title).trim() : '',
    video_path: input?.video_path ? String(input.video_path).trim() : '',
    interval_ms: Math.max(Number(input?.interval_ms) || DEFAULT_INTERVAL_MS, 10000),
    limit: Math.max(Number(input?.limit) || 10, 1),
    sort: String(input?.sort || 'new').trim() || 'new',
    reply_template: String(input?.reply_template || defaultReplyTemplate()).trim() || defaultReplyTemplate(),
    enabled: input?.enabled !== false,
    seen_comment_ids: Array.isArray(input?.seen_comment_ids) ? input.seen_comment_ids.map((v) => String(v)) : [],
    last_checked_at: Number(input?.last_checked_at) || 0,
    last_reply_at: Number(input?.last_reply_at) || 0,
    last_replied_comment_id: input?.last_replied_comment_id ? String(input.last_replied_comment_id) : '',
    last_error: input?.last_error ? String(input.last_error) : '',
    running: false,
    run_id: input?.run_id ? String(input.run_id) : generatedRunId,
    publish_status: input?.publish_status ? String(input.publish_status) : '',
    comment_count: Number(input?.comment_count) || 0,
    reply_count: Number(input?.reply_count) || 0,
  };
}

function scheduleJob(job) {
  const existing = timers.get(job.key);
  if (existing) clearInterval(existing);
  if (!job.enabled) return;
  const timer = setInterval(() => {
    void operateJob(job.key);
  }, job.interval_ms);
  timer.unref?.();
  timers.set(job.key, timer);
}

function upsertJob(input) {
  const key = jobKey(input);
  const next = normalizeJob({ ...(jobs.get(key) || {}), ...input });
  jobs.set(next.key, next);
  scheduleJob(next);
  writeState();
  return next;
}

async function monitorVideo(payload) {
  const limit = String(payload?.limit || 10);
  const sort = String(payload?.sort || 'new');
  const args = ['monitor', '--limit', limit, '--sort', sort];
  if (payload?.aid) args.push('--aid', String(payload.aid));
  else if (payload?.bvid) args.push('--bvid', String(payload.bvid));
  return await runPythonHelper(args);
}

async function replyToComment(payload) {
  const root = String(payload?.root || payload?.comment_id || '').trim();
  const parent = String(payload?.parent || root).trim();
  const text = String(payload?.reply_text || payload?.text || '').trim();
  const args = ['reply', '--root', root, '--parent', parent, '--text', text];
  if (payload?.aid) args.push('--aid', String(payload.aid));
  else if (payload?.bvid) args.push('--bvid', String(payload.bvid));
  return await runPythonHelper(args);
}

async function operateJob(jobId) {
  const job = jobs.get(jobId);
  if (!job || !job.enabled || job.running) {
    return { ok: false, skipped: true };
  }
  job.running = true;
  try {
    const monitorResult = await monitorVideo(job);
    const comments = Array.isArray(monitorResult.json?.comments) ? monitorResult.json.comments : [];
    const unseen = comments.filter((comment) => !job.seen_comment_ids.includes(String(comment.comment_id || '')));
    let replyResult = null;
    let pickedComment = null;
    if (unseen.length > 0) {
      pickedComment = unseen[0];
      replyResult = await replyToComment({
        aid: job.aid || pickedComment.oid,
        bvid: job.bvid,
        root: pickedComment.root || pickedComment.comment_id,
        parent: pickedComment.parent || pickedComment.root || pickedComment.comment_id,
        reply_text: job.reply_template,
      });
      if (replyResult.ok && replyResult.json?.ok) {
        job.last_reply_at = Date.now();
        job.last_replied_comment_id = String(pickedComment.comment_id || '');
        job.reply_count += 1;
      }
    }
    for (const comment of comments) {
      const id = String(comment.comment_id || '').trim();
      if (id && !job.seen_comment_ids.includes(id)) {
        job.seen_comment_ids.push(id);
      }
    }
    job.comment_count = comments.length;
    job.last_checked_at = Date.now();
    job.last_error = replyResult && (!replyResult.ok || !replyResult.json?.ok)
      ? String(replyResult.json?.response?.message || replyResult.stderr || 'reply failed')
      : monitorResult.ok && monitorResult.json?.ok
        ? ''
        : String(monitorResult.json?.response?.message || monitorResult.stderr || 'monitor failed');
    writeState();
    return { ok: true, monitor: monitorResult, picked_comment: pickedComment, reply: replyResult, job };
  } finally {
    job.running = false;
    writeState();
  }
}

function loadJobsFromState() {
  const state = readState();
  for (const rawJob of state.jobs || []) {
    try {
      const job = normalizeJob(rawJob);
      jobs.set(job.key, job);
      scheduleJob(job);
    } catch {
      // ignore stale dynamic-era jobs
    }
  }
}

loadJobsFromState();

const server = createServer(async (req, res) => {
  if (req.url === '/health' && req.method === 'GET') {
    return sendJson(res, 200, { ok: true, service: 'bilibili-publisher-bridge', jobs: Array.from(jobs.keys()) });
  }

  if (!checkAuth(req, res)) return;

  let raw = '';
  for await (const chunk of req) raw += chunk;
  let body = {};
  try {
    body = raw ? JSON.parse(raw) : {};
  } catch {
    return sendJson(res, 400, { ok: false, error: 'invalid_json' });
  }

  if (req.url === '/publish' && req.method === 'POST') {
    const payload = enrichPayloadFromWorkspace(body?.payload ?? body);
    const sourceVideoPath = await ensureHostVideoPath(payload);
    const quality = assessVideoForPublish(payload, sourceVideoPath);
    if (!quality.ok) {
      updatePipelineLedger(String(payload?.run_id || ''), {
        topic_input: payload?.topic_input || payload?.title || '',
        phase2_status: 'publish_blocked',
        phase2_last_error: quality.reasons.join(','),
        artifacts: { video_path: String(sourceVideoPath || payload?.video_path || '') },
      });
      return sendJson(res, 200, buildResult({
        phase: 'publish_execute',
        platform: 'bilibili',
        payload,
        publish_blocked: true,
        quality,
      }));
    }
    const videoPath = await normalizeVideoForBilibili(sourceVideoPath);
    const tags = Array.isArray(payload?.tags) ? payload.tags.map((tag) => String(tag).trim()).filter(Boolean).join(',') : '';
    const videoPublish = await runPythonHelper([
      'publish',
      '--video-path', videoPath,
      '--title', String(payload?.title || '').trim(),
      '--description', String(payload?.description || '').trim(),
      ...(tags ? ['--tags', tags] : []),
      ...(payload?.tid ? ['--tid', String(payload.tid)] : []),
    ]);

    const publishOk = videoPublish.ok && videoPublish.json?.ok && videoPublish.json?.result?.code === 0;
    const aid = publishOk ? String(videoPublish.json.result?.data?.aid || '') : '';
    const bvid = publishOk ? String(videoPublish.json.result?.data?.bvid || '') : '';
    const job = publishOk ? upsertJob({
      run_id: payload?.run_id,
      aid,
      bvid,
      title: payload?.title,
      video_path: String(payload?.video_path || '').trim(),
      interval_ms: payload?.interval_ms,
      limit: payload?.limit,
      sort: payload?.sort,
      reply_template: payload?.reply_template,
      enabled: true,
      publish_status: 'published',
    }) : null;
    updatePipelineLedger(String(payload?.run_id || ''), {
      topic_input: payload?.topic_input || payload?.title || '',
      phase2_status: publishOk ? 'published' : 'publish_failed',
      degraded_mode: false,
      phase2_identity: publishOk ? { aid, bvid } : null,
      phase2_last_error: publishOk ? '' : String(videoPublish.stderr || 'publish failed'),
      artifacts: {
        video_path: String(payload?.video_path || '').trim(),
      },
    });
    return sendJson(res, 200, buildResult({
      phase: 'publish_execute',
      platform: 'bilibili',
      payload,
      video_publish: videoPublish,
      publish_identity: publishOk ? { aid, bvid, url: `https://www.bilibili.com/video/${bvid}` } : null,
      auto_monitor_job: job
    }));
  }

  if (req.url === '/monitor' && req.method === 'POST') {
    const payload = enrichPayloadFromWorkspace(body?.payload ?? body);
    const result = await monitorVideo(payload);
    return sendJson(res, 200, buildResult({ phase: 'comment_ingest', platform: 'bilibili', payload, monitor: result }));
  }

  if (req.url === '/reply' && req.method === 'POST') {
    const payload = enrichPayloadFromWorkspace(body?.payload ?? body);
    const result = await replyToComment(payload);
    return sendJson(res, 200, buildResult({ phase: 'comment_reply', platform: 'bilibili', payload, reply: result }));
  }

  if (req.url === '/operate' && req.method === 'POST') {
    const payload = enrichPayloadFromWorkspace(body?.payload ?? body);
    const job = upsertJob({
      run_id: payload?.run_id,
      aid: payload?.aid,
      bvid: payload?.bvid || payload?.video_id,
      title: payload?.title,
      video_path: payload?.video_path,
      interval_ms: payload?.interval_ms,
      limit: payload?.limit,
      sort: payload?.sort,
      reply_template: payload?.reply_template,
      enabled: payload?.enabled !== false,
      publish_status: payload?.publish_status || 'published',
    });
    const result = await operateJob(job.key);
    updatePipelineLedger(String(payload?.run_id || job.run_id || ''), {
      topic_input: payload?.topic_input || job.title || '',
      phase2_status: result?.reply?.ok || result?.monitor?.ok ? 'monitoring' : 'monitor_failed',
      phase2_identity: { aid: job.aid, bvid: job.bvid },
      phase2_monitor: {
        comment_count: job.comment_count,
        reply_count: job.reply_count,
        last_checked_at: job.last_checked_at,
        last_replied_comment_id: job.last_replied_comment_id,
      },
      phase2_last_error: job.last_error || '',
    });
    return sendJson(res, 200, buildResult({ phase: 'publish_monitor_reply', platform: 'bilibili', payload, job, ...result }));
  }

  if (req.url === '/jobs' && req.method === 'GET') {
    return sendJson(res, 200, { ok: true, jobs: Array.from(jobs.values()) });
  }

  return sendJson(res, 404, { ok: false, error: 'not_found' });
});

server.listen(PORT, HOST, () => {
  process.stdout.write(`bilibili-publisher-bridge listening on http://${HOST}:${PORT}\n`);
});
