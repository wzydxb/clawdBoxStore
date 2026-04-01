#!/usr/bin/env node
import { createServer } from 'node:http';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const execFileAsync = promisify(execFile);
const PORT = Number.parseInt(process.env.VIDEO_SYNTH_BRIDGE_PORT || '19827', 10);
const HOST = process.env.VIDEO_SYNTH_BRIDGE_HOST || '0.0.0.0';
const TOKEN = process.env.VIDEO_SYNTH_BRIDGE_TOKEN || '';
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const CONTAINER_CLAWBOX_ROOT = process.env.VIDEO_SYNTH_CONTAINER_ROOT || '/home/node/.clawbox';
const HOST_CLAWBOX_ROOT = process.env.CLAWBOX_HOST_OPENCLAW_DIR || path.resolve(SCRIPT_DIR, '../clawbox-data');
const PLAY_BASE_URL = (process.env.VIDEO_SYNTH_PLAY_BASE_URL || 'http://127.0.0.1:18789').replace(/\/$/, '');
const VIDEO_WIDTH = 1080;
const VIDEO_HEIGHT = 1920;
const FPS = 30;
const MIN_SEGMENT_SECONDS = 2.2;
const SEGMENT_PADDING_SECONDS = 0.35;
const SEGMENT_DIR = 'segments';
const YTDLP_COMMAND = process.env.YTDLP_COMMAND || path.resolve(os.homedir(), 'Library/Python/3.9/bin/yt-dlp');
const FONT_CANDIDATES = [
  '/System/Library/Fonts/PingFang.ttc',
  '/System/Library/Fonts/Hiragino Sans GB.ttc',
  '/System/Library/Fonts/STHeiti Medium.ttc',
  '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
  '/Library/Fonts/Arial Unicode.ttf',
];
const BG_COLORS = ['#0B1020', '#10243B', '#1A1F36', '#1D3557', '#22304A', '#1F2937', '#132A13'];
const TITLE_MAP = {
  opening_hook: '开场钩子',
  market_overview: '市场热度',
  answer_common_questions: '回答核心问题',
  three_paths: '三条落地路径',
  pitfalls: '必须避开的坑',
  cost_summary: '成本总结',
  closing: '收尾总结',
};

function sendJson(res, status, payload) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(payload));
}

function mapContainerPathToHost(filePath) {
  if (typeof filePath !== 'string' || !filePath.trim()) {
    return null;
  }
  const normalized = path.resolve(filePath.trim());
  if (!normalized.startsWith(CONTAINER_CLAWBOX_ROOT)) {
    return normalized;
  }
  const relativePath = path.relative(CONTAINER_CLAWBOX_ROOT, normalized);
  return path.join(HOST_CLAWBOX_ROOT, relativePath);
}

function repairLikelyJsonStringIssues(text) {
  let out = '';
  let inString = false;
  let escaping = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (!inString) {
      if (ch === '"') inString = true;
      out += ch;
      continue;
    }
    if (escaping) {
      out += ch;
      escaping = false;
      continue;
    }
    if (ch === '\\') {
      out += ch;
      escaping = true;
      continue;
    }
    if (ch === '"') {
      let j = i + 1;
      while (j < text.length && /\s/.test(text[j])) j += 1;
      const next = text[j] || '';
      if (next && ![',', '}', ']', ':'].includes(next)) {
        out += '\\"';
        continue;
      }
      inString = false;
      out += ch;
      continue;
    }
    out += ch;
  }
  return out;
}

function parsePossiblyBrokenJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return JSON.parse(repairLikelyJsonStringIssues(text));
  }
}

function isFormalProductionPackage(pkg) {
  return pkg && typeof pkg === 'object' && !Array.isArray(pkg)
    && (Array.isArray(pkg.voiceover_blocks) || Array.isArray(pkg.scene_beats) || Array.isArray(pkg.asset_requirements));
}

function resolveProductionPackage(rawPackage) {
  if (typeof rawPackage === 'string') {
    const trimmed = rawPackage.trim();
    if (!trimmed) return {};
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      const parsed = parsePossiblyBrokenJson(trimmed);
      if (!isFormalProductionPackage(parsed)) {
        throw new Error('video_synth requires a formal production_package, not a script-only payload');
      }
      return parsed;
    }
    const mappedPath = mapContainerPathToHost(trimmed);
    const parsed = parsePossiblyBrokenJson(readFileSync(mappedPath, 'utf8'));
    if (!isFormalProductionPackage(parsed)) {
      throw new Error('video_synth requires a formal production_package file');
    }
    return parsed;
  }
  if (rawPackage && typeof rawPackage === 'object' && !Array.isArray(rawPackage)) {
    if (typeof rawPackage.path === 'string' && rawPackage.path.trim()) {
      const mappedPath = mapContainerPathToHost(rawPackage.path);
      const parsed = parsePossiblyBrokenJson(readFileSync(mappedPath, 'utf8'));
      if (!isFormalProductionPackage(parsed)) {
        throw new Error('video_synth requires a formal production_package file');
      }
      return parsed;
    }
    if (!isFormalProductionPackage(rawPackage)) {
      throw new Error('video_synth requires a formal production_package, not a script-only payload');
    }
    return rawPackage;
  }
  return {};
}

function resolveOutputDir(rawOutputDir) {
  if (typeof rawOutputDir !== 'string' || !rawOutputDir.trim()) {
    return mkdtempSync(path.join(os.tmpdir(), 'video-synth-'));
  }
  const mappedPath = mapContainerPathToHost(rawOutputDir);
  return path.resolve(mappedPath);
}

function ensureCleanDir(dirPath) {
  rmSync(dirPath, { recursive: true, force: true });
  mkdirSync(dirPath, { recursive: true });
}

function chooseFontFile() {
  for (const candidate of FONT_CANDIDATES) {
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  return null;
}

function safeText(value) {
  return String(value || '')
    .replace(/\r\n?/g, '\n')
    .replace(/\t/g, ' ')
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')
    .trim();
}

function computeDisplayWidth(text) {
  let width = 0;
  for (const char of text) {
    width += /[\u0000-\u00ff]/.test(char) ? 0.6 : 1;
  }
  return width;
}

function wrapText(text, maxWidth, maxLines) {
  const normalized = safeText(text).replace(/\n{2,}/g, '\n');
  if (!normalized) return '';
  const lines = [];
  let current = '';
  for (const sourceLine of normalized.split('\n')) {
    if (!sourceLine.trim()) {
      if (current.trim()) {
        lines.push(current.trim());
        current = '';
      }
      continue;
    }
    for (const char of sourceLine) {
      const next = current + char;
      if (computeDisplayWidth(next) > maxWidth && current.trim()) {
        lines.push(current.trim());
        current = char;
        if (lines.length >= maxLines) {
          break;
        }
      } else {
        current = next;
      }
    }
    if (lines.length >= maxLines) {
      break;
    }
    if (current.trim()) {
      lines.push(current.trim());
      current = '';
    }
  }
  if (current.trim() && lines.length < maxLines) {
    lines.push(current.trim());
  }
  const clipped = lines.slice(0, maxLines);
  if (lines.length > maxLines && clipped.length > 0) {
    clipped[clipped.length - 1] = `${clipped[clipped.length - 1].replace(/[。！？!?,，、；;：:\s]+$/g, '')}…`;
  }
  return clipped.join('\n');
}

function splitIntoSentences(text) {
  const normalized = safeText(text).replace(/\n+/g, ' ');
  if (!normalized) return [];
  const parts = normalized.match(/[^。！？!?；;]+[。！？!?；;]?/g);
  return (parts || [normalized]).map((part) => safeText(part)).filter(Boolean);
}

function splitScriptIntoSegments(text) {
  const paragraphs = safeText(text).split(/\n\s*\n+/).map((part) => safeText(part)).filter(Boolean);
  const segments = [];
  for (const paragraph of paragraphs) {
    const sentences = splitIntoSentences(paragraph);
    let bucket = '';
    for (const sentence of sentences) {
      const proposal = bucket ? `${bucket} ${sentence}` : sentence;
      if (proposal.length > 90 && bucket) {
        segments.push(bucket.trim());
        bucket = sentence;
      } else {
        bucket = proposal;
      }
    }
    if (bucket.trim()) {
      segments.push(bucket.trim());
    }
  }
  return segments.length > 0 ? segments : [safeText(text) || '这是自动生成的视频内容'];
}

function pickVoiceoverBlock(pkg) {
  const blocks = Array.isArray(pkg.voiceover_blocks) ? pkg.voiceover_blocks.filter((entry) => safeText(entry?.text)) : [];
  if (blocks.length === 0) {
    return { title: 'fallback', text: '这是自动生成的视频内容' };
  }
  const titledBlocks = blocks.filter((entry) => safeText(entry?.title));
  if (titledBlocks.length > 0) {
    const preferred = ['6-8min_script', '3min_script', '60s_script'];
    for (const title of preferred) {
      const match = titledBlocks.find((entry) => safeText(entry?.title) === title);
      if (match) return { title: safeText(match.title), text: safeText(match.text) };
    }
    return { title: safeText(titledBlocks[0].title) || 'voiceover', text: safeText(titledBlocks[0].text) };
  }
  return {
    title: 'voiceover',
    text: blocks.map((entry) => safeText(entry.text)).filter(Boolean).join('\n\n'),
  };
}

function normalizeSceneBeats(pkg) {
  const beats = Array.isArray(pkg.scene_beats) ? pkg.scene_beats : [];
  if (beats.length === 0) {
    return [{ name: 'main', duration_seconds: 1, description: '核心内容' }];
  }
  return beats.map((beat, index) => ({
    name: safeText(beat?.name) || `scene_${index + 1}`,
    duration_seconds: Number.isFinite(Number(beat?.duration_seconds)) ? Number(beat.duration_seconds) : 1,
    description: safeText(beat?.description),
  }));
}

function normalizeAssetRequirements(pkg) {
  return Array.isArray(pkg.asset_requirements) ? pkg.asset_requirements.map((asset, index) => ({
    index,
    type: safeText(asset?.type) || 'clip',
    source: safeText(asset?.source),
    keyword: safeText(asset?.keyword),
    start_time: Number.isFinite(Number(asset?.start_time)) ? Number(asset.start_time) : 0,
    end_time: Number.isFinite(Number(asset?.end_time)) ? Number(asset.end_time) : 0,
    desc: safeText(asset?.desc),
  })) : [];
}

async function ensureSourceVideo(asset, assetsDir) {
  if (!asset.source) return null;
  const sourceId = asset.source.replace(/[^0-9A-Za-z_-]/g, '');
  if (!sourceId) return null;
  const outTemplate = path.join(assetsDir, `${sourceId}.%(ext)s`);
  await execFileAsync(YTDLP_COMMAND, [
    '--no-warnings',
    '--no-playlist',
    '--merge-output-format', 'mp4',
    '-f', 'bv*+ba/b',
    '-o', outTemplate,
    `https://www.bilibili.com/video/${asset.source}`,
  ], { timeout: 10 * 60 * 1000, maxBuffer: 20 * 1024 * 1024 });
  const candidates = ['mp4', 'mkv', 'webm', 'flv'].map((ext) => path.join(assetsDir, `${sourceId}.${ext}`));
  return candidates.find((candidate) => existsSync(candidate)) || null;
}

async function getVideoDurationSeconds(filePath) {
  const { stdout } = await execFileAsync('ffprobe', [
    '-v', 'error',
    '-show_entries', 'format=duration',
    '-of', 'default=noprint_wrappers=1:nokey=1',
    filePath,
  ]);
  const parsed = Number.parseFloat(String(stdout).trim());
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

async function clipSourceVideo(sourcePath, outputPath, startTime, endTime) {
  const sourceDuration = await getVideoDurationSeconds(sourcePath);
  const safeStart = Math.max(0, Math.min(startTime, Math.max(0, sourceDuration - 2)));
  const safeEnd = Math.max(safeStart + 2, Math.min(endTime, sourceDuration));
  const duration = Math.max(Math.min(safeEnd - safeStart, sourceDuration - safeStart), 2);
  if (!Number.isFinite(duration) || duration <= 0 || safeStart >= sourceDuration) {
    throw new Error('invalid clip range');
  }
  await execFileAsync('ffmpeg', [
    '-y',
    '-ss', String(safeStart),
    '-t', String(duration),
    '-i', sourcePath,
    // Keep the full frame and pad into the target canvas instead of cropping source content.
    '-vf', `scale=${VIDEO_WIDTH}:${VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad=${VIDEO_WIDTH}:${VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black`,
    '-r', String(FPS),
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-ar', '44100',
    '-ac', '2',
    outputPath,
  ], { timeout: 10 * 60 * 1000, maxBuffer: 20 * 1024 * 1024 });
  return await getVideoDurationSeconds(outputPath);
}

async function prepareAssetClips(pkg, outputDir) {
  const assets = normalizeAssetRequirements(pkg);
  if (assets.length === 0) return [];
  const assetsDir = path.join(outputDir, 'asset-sources');
  const clipsDir = path.join(outputDir, 'asset-clips');
  mkdirSync(assetsDir, { recursive: true });
  mkdirSync(clipsDir, { recursive: true });
  const prepared = [];
  for (const asset of assets) {
    if (asset.type !== 'clip' || !asset.source) continue;
    try {
      const sourcePath = await ensureSourceVideo(asset, assetsDir);
      if (!sourcePath) continue;
      const clipPath = path.join(clipsDir, `asset-${String(asset.index + 1).padStart(2, '0')}.mp4`);
      const clipDuration = await clipSourceVideo(sourcePath, clipPath, asset.start_time, asset.end_time > asset.start_time ? asset.end_time : asset.start_time + 6);
      prepared.push({ ...asset, clipPath, clipDuration });
    } catch {
      // keep best-effort behavior
    }
  }
  return prepared;
}

function assignBeatIndex(index, total, beats) {
  const totalWeight = beats.reduce((sum, beat) => sum + Math.max(1, beat.duration_seconds || 1), 0);
  const midpoint = (index + 0.5) / total;
  let cumulative = 0;
  for (let i = 0; i < beats.length; i += 1) {
    cumulative += Math.max(1, beats[i].duration_seconds || 1) / totalWeight;
    if (midpoint <= cumulative || i === beats.length - 1) {
      return i;
    }
  }
  return beats.length - 1;
}

function buildSceneTitle(pkg, beat, index) {
  if (index === 0 && safeText(pkg.cover_text)) {
    return safeText(pkg.cover_text);
  }
  return TITLE_MAP[beat.name] || safeText(beat.description) || beat.name || `场景 ${index + 1}`;
}

function buildSceneKicker(pkg, beat, index) {
  if (index === 0 && safeText(pkg.publish_metadata?.title)) {
    return safeText(pkg.publish_metadata.title);
  }
  return safeText(beat.description) || safeText(pkg.evidence_summary) || '真实内容合成';
}

function buildSceneBody(pkg, beat, segmentText) {
  const summary = safeText(pkg.evidence_summary);
  if (beat.name === 'opening_hook') {
    return [summary, safeText(segmentText)].filter(Boolean).join('\n\n');
  }
  if (beat.name === 'market_overview') {
    return [safeText(beat.description), summary].filter(Boolean).join('\n\n');
  }
  if (beat.name === 'pitfalls' && Array.isArray(pkg.risk_flags) && pkg.risk_flags.length > 0) {
    return pkg.risk_flags.map((flag) => `• ${safeText(flag)}`).join('\n');
  }
  if (beat.name === 'closing' && safeText(pkg.publish_metadata?.description)) {
    return safeText(pkg.publish_metadata.description);
  }
  return safeText(segmentText);
}

async function getAudioDurationSeconds(filePath) {
  const { stdout } = await execFileAsync('ffprobe', [
    '-v', 'error',
    '-show_entries', 'format=duration',
    '-of', 'default=noprint_wrappers=1:nokey=1',
    filePath,
  ]);
  const parsed = Number.parseFloat(String(stdout).trim());
  return Number.isFinite(parsed) && parsed > 0 ? parsed : MIN_SEGMENT_SECONDS;
}

async function synthesizeSegmentAudio(outputDir, index, text) {
  const baseName = `segment-${String(index + 1).padStart(2, '0')}`;
  const aiffPath = path.join(outputDir, `${baseName}.aiff`);
  const wavPath = path.join(outputDir, `${baseName}.wav`);
  await execFileAsync('say', ['-o', aiffPath, safeText(text)]);
  await execFileAsync('ffmpeg', ['-y', '-i', aiffPath, wavPath]);
  const duration = Math.max(await getAudioDurationSeconds(wavPath) + SEGMENT_PADDING_SECONDS, MIN_SEGMENT_SECONDS);
  return { aiffPath, wavPath, duration, baseName };
}

async function renderSegmentCard(outputDir, segment, index, total, fontFile) {
  const imagePath = path.join(outputDir, `${segment.baseName}.png`);
  const pythonScript = `
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, textwrap, random
WIDTH = ${VIDEO_WIDTH}
HEIGHT = ${VIDEO_HEIGHT}
BG = ${JSON.stringify(BG_COLORS[index % BG_COLORS.length])}
TITLE = ${JSON.stringify(wrapText(segment.title, 16, 3))}
KICKER = ${JSON.stringify(wrapText(segment.kicker, 28, 2))}
BODY = ${JSON.stringify(wrapText(segment.body, 26, 12))}
SUB = ${JSON.stringify(wrapText(segment.subtitle, 24, 6))}
INDEX = ${JSON.stringify(`${index + 1}/${total}`)}
FONT_FILE = ${JSON.stringify(fontFile)}
OUT = ${JSON.stringify(imagePath)}
BEAT = ${JSON.stringify(segment.beat_name)}
SEED = ${index + 1}
random.seed(SEED)

def make_font(size):
    return ImageFont.truetype(FONT_FILE, size=size)

def rgba(hexv, a=255):
    hexv = hexv.lstrip('#')
    return tuple(int(hexv[i:i+2], 16) for i in (0,2,4)) + (a,)

img = Image.new('RGBA', (WIDTH, HEIGHT), rgba(BG))
draw = ImageDraw.Draw(img, 'RGBA')

# layered background
for y in range(HEIGHT):
    ratio = y / max(1, HEIGHT - 1)
    shade = int(18 + 40 * ratio)
    draw.line((0, y, WIDTH, y), fill=(shade, shade + 10, shade + 28, 255))
for _ in range(18):
    cx = random.randint(0, WIDTH)
    cy = random.randint(0, HEIGHT)
    r = random.randint(90, 240)
    glow = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
    gdraw = ImageDraw.Draw(glow, 'RGBA')
    gdraw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(255,255,255,18))
    glow = glow.filter(ImageFilter.GaussianBlur(32))
    img.alpha_composite(glow)
for x in range(0, WIDTH, 48):
    draw.line((x, 0, x, HEIGHT), fill=(255,255,255,10), width=1)
for y in range(0, HEIGHT, 48):
    draw.line((0, y, WIDTH, y), fill=(255,255,255,8), width=1)

title_font = make_font(64)
kicker_font = make_font(28)
body_font = make_font(34)
sub_font = make_font(30)
small_font = make_font(24)
index_font = make_font(28)

# hero shells
hero = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
hdraw = ImageDraw.Draw(hero, 'RGBA')
hdraw.rounded_rectangle((46, 70, 1034, 340), radius=34, fill=(8,10,20,140), outline=(255,255,255,24), width=2)
hdraw.rounded_rectangle((48, 1480, 1032, 1832), radius=28, fill=(6,8,15,180), outline=(255,255,255,28), width=2)
img.alpha_composite(hero)

# beat-specific generated visuals
body_lines = [line for line in BODY.split('\\n') if line.strip()]
sub_lines = [line for line in SUB.split('\\n') if line.strip()]

def pill(x, y, text, color):
    bbox = draw.textbbox((x, y), text, font=small_font)
    pad = 18
    draw.rounded_rectangle((bbox[0]-pad, bbox[1]-10, bbox[2]+pad, bbox[3]+10), radius=18, fill=color)
    draw.text((x, y), text, font=small_font, fill=(255,255,255,255))

def metric_card(x, y, w, h, label, value, accent):
    draw.rounded_rectangle((x,y,x+w,y+h), radius=24, fill=(12,16,28,170), outline=accent, width=2)
    draw.text((x+24, y+18), label, font=small_font, fill=(210,220,255,220))
    draw.text((x+24, y+56), value, font=make_font(40), fill=(255,255,255,255))

def path_card(x, y, w, h, title, bullets, accent):
    draw.rounded_rectangle((x,y,x+w,y+h), radius=28, fill=(10,14,24,180), outline=accent, width=3)
    draw.ellipse((x+24,y+24,x+86,y+86), fill=accent)
    draw.text((x+110, y+28), title, font=make_font(34), fill=(255,255,255,255))
    offset = y + 106
    for bullet in bullets[:4]:
        bullet = bullet.strip()
        if not bullet:
            continue
        wrapped = textwrap.wrap(bullet, width=14)[:2]
        draw.ellipse((x+34, offset+12, x+46, offset+24), fill=accent)
        draw.text((x+64, offset), '\\n'.join(wrapped), font=small_font, fill=(232,236,255,240), spacing=8)
        offset += 64

def warning_card(x, y, w, h, text, accent):
    draw.rounded_rectangle((x,y,x+w,y+h), radius=26, fill=(24,12,12,185), outline=accent, width=3)
    tri = [(x+34,y+34),(x+66,y+96),(x+2,y+96)]
    draw.polygon(tri, fill=accent)
    draw.text((x+96,y+28), text, font=small_font, fill=(255,240,240,255), spacing=8)

if BEAT == 'opening_hook':
    ring = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
    rdraw = ImageDraw.Draw(ring, 'RGBA')
    rdraw.ellipse((640, 360, 990, 710), outline=(255,209,102,120), width=18)
    rdraw.ellipse((684, 404, 946, 666), outline=(255,255,255,80), width=10)
    img.alpha_composite(ring.filter(ImageFilter.GaussianBlur(1)))
    pill(86, 398, '真实需求', (39, 174, 96, 210))
    pill(86, 454, '不吹不卖课', (239, 68, 68, 210))
    pill(86, 510, '讲落地路径', (59, 130, 246, 210))
elif BEAT == 'market_overview':
    metric_card(70, 410, 270, 150, '核心热度', '已验证', (255,209,102,255))
    metric_card(360, 410, 270, 150, '用户关心', '高频出现', (59,130,246,255))
    metric_card(650, 410, 360, 150, '内容价值', '可直接照抄', (34,197,94,255))
    points = [(96, 980), (220, 900), (356, 860), (520, 720), (686, 650), (860, 560), (980, 500)]
    draw.line(points, fill=(255,209,102,255), width=10)
    for px, py in points:
        draw.ellipse((px-12, py-12, px+12, py+12), fill=(255,255,255,255))
        draw.ellipse((px-24, py-24, px+24, py+24), outline=(255,209,102,120), width=4)
elif BEAT == 'answer_common_questions':
    qs = [
        '这个值不值得去？',
        '第一次怎么开始？',
        '最容易踩哪些坑？',
        '怎样最省时间？',
    ]
    positions = [(70, 400), (560, 400), (70, 760), (560, 760)]
    for i, (qx, qy) in enumerate(positions):
        draw.rounded_rectangle((qx, qy, qx+450, qy+280), radius=30, fill=(10,14,24,178), outline=(96,165,250,160), width=2)
        draw.ellipse((qx+28,qy+24,qx+96,qy+92), fill=(59,130,246,240))
        draw.text((qx+48, qy+36), str(i+1), font=make_font(32), fill=(255,255,255,255))
        draw.text((qx+124, qy+34), '\\n'.join(textwrap.wrap(qs[i], width=10)), font=make_font(34), fill=(255,255,255,255), spacing=8)
        if i < len(body_lines):
            draw.text((qx+36, qy+128), '\\n'.join(textwrap.wrap(body_lines[i], width=17)[:4]), font=small_font, fill=(220,228,255,230), spacing=8)
elif BEAT == 'three_paths':
    bullets = body_lines if body_lines else sub_lines
    path_card(56, 430, 300, 760, '路径 01', bullets[0:4], (56,189,248,255))
    path_card(390, 430, 300, 760, '路径 02', bullets[4:8], (34,197,94,255))
    path_card(724, 430, 300, 760, '路径 03', bullets[8:12], (255,209,102,255))
    draw.line((206, 1240, 206, 1390), fill=(56,189,248,120), width=8)
    draw.line((540, 1240, 540, 1390), fill=(34,197,94,120), width=8)
    draw.line((874, 1240, 874, 1390), fill=(255,209,102,120), width=8)
elif BEAT == 'pitfalls':
    warnings = body_lines if body_lines else [SUB]
    warning_card(70, 430, 940, 180, warnings[0] if len(warnings) > 0 else '别照着平台默认推荐走', (248,113,113,255))
    warning_card(70, 660, 940, 180, warnings[1] if len(warnings) > 1 else '关键节点要提前准备', (251,191,36,255))
    warning_card(70, 890, 940, 180, warnings[2] if len(warnings) > 2 else '别把路线和节奏走反了', (249,115,22,255))
elif BEAT == 'cost_summary':
    metric_card(72, 440, 300, 170, '部署门槛', '普通电脑', (34,197,94,255))
    metric_card(390, 440, 300, 170, 'GPU 需求', '不需要', (56,189,248,255))
    metric_card(708, 440, 300, 170, '试错成本', '几百块', (255,209,102,255))
    draw.rounded_rectangle((80, 760, 1000, 1050), radius=28, fill=(10,14,24,180), outline=(255,255,255,34), width=2)
    draw.text((118, 802), '\\n'.join(body_lines[:6] or sub_lines[:6]), font=body_font, fill=(255,255,255,235), spacing=12)
else:
    draw.rounded_rectangle((72, 420, 1008, 1260), radius=34, fill=(10,14,24,168), outline=(255,255,255,34), width=2)
    draw.text((110, 470), '\\n'.join(body_lines[:10] or sub_lines[:10]), font=body_font, fill=(255,255,255,238), spacing=18)
    for i in range(3):
        x = 90 + i * 300
        draw.rounded_rectangle((x, 1280, x+250, 1430), radius=22, fill=(255,255,255,18), outline=(255,255,255,30), width=2)
        draw.text((x+24, 1310), f'要点 {i+1}', font=make_font(28), fill=(255,209,102,255))

# global text overlay
shadow = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
sdraw = ImageDraw.Draw(shadow, 'RGBA')
sdraw.text((84, 122), KICKER, font=kicker_font, fill=(0,0,0,120))
sdraw.text((84, 172), TITLE, font=title_font, fill=(0,0,0,160), spacing=12)
shadow = shadow.filter(ImageFilter.GaussianBlur(4))
img.alpha_composite(shadow)
draw.text((82, 120), KICKER, font=kicker_font, fill=(255, 209, 102, 255))
draw.text((82, 170), TITLE, font=title_font, fill=(255,255,255,255), spacing=12)
draw.text((WIDTH - 150, 118), INDEX, font=index_font, fill=(184,192,255,255))
draw.text((72, 1560), SUB, font=sub_font, fill=(255,255,255,255), spacing=12)
img = img.convert('RGB')
img.save(OUT, 'PNG')
`;
  await execFileAsync('python3', ['-c', pythonScript]);
  return imagePath;
}

async function renderSegmentClip(outputDir, segment) {
  const clipPath = path.join(outputDir, `${segment.baseName}.mp4`);
  if (segment.assetClipPath && existsSync(segment.assetClipPath)) {
    await execFileAsync('ffmpeg', [
      '-y',
      '-stream_loop', '-1',
      '-i', segment.assetClipPath,
      '-t', segment.duration.toFixed(3),
      '-vf', `fps=${FPS},scale=${VIDEO_WIDTH}:${VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad=${VIDEO_WIDTH}:${VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black`,
      '-c:v', 'libx264',
      '-preset', 'veryfast',
      '-pix_fmt', 'yuv420p',
      ...(segment.useOriginalAudio ? ['-c:a', 'aac', '-ar', '44100', '-ac', '2'] : ['-an']),
      clipPath,
    ], { timeout: 10 * 60 * 1000, maxBuffer: 20 * 1024 * 1024 });
    return clipPath;
  }
  await execFileAsync('ffmpeg', [
    '-y',
    '-loop', '1',
    '-i', segment.cardPath,
    '-t', segment.duration.toFixed(3),
    '-vf', `scale=${VIDEO_WIDTH}:${VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad=${VIDEO_WIDTH}:${VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,fps=${FPS}`,
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-pix_fmt', 'yuv420p',
    clipPath,
  ]);
  return clipPath;
}

function formatSrtTime(seconds) {
  const totalMs = Math.max(0, Math.round(seconds * 1000));
  const hours = Math.floor(totalMs / 3600000);
  const minutes = Math.floor((totalMs % 3600000) / 60000);
  const secs = Math.floor((totalMs % 60000) / 1000);
  const ms = totalMs % 1000;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
}

function formatAssTime(seconds) {
  const totalCs = Math.max(0, Math.round(seconds * 100));
  const hours = Math.floor(totalCs / 360000);
  const minutes = Math.floor((totalCs % 360000) / 6000);
  const secs = Math.floor((totalCs % 6000) / 100);
  const cs = totalCs % 100;
  return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(cs).padStart(2, '0')}`;
}

function buildSubtitleArtifacts(outputDir, segments, fontName) {
  let currentTime = 0;
  const srtLines = [];
  const assEvents = [];
  segments.forEach((segment, index) => {
    const start = currentTime;
    const end = currentTime + segment.duration;
    const subtitleText = wrapText(segment.subtitle, 22, 6);
    srtLines.push(String(index + 1));
    srtLines.push(`${formatSrtTime(start)} --> ${formatSrtTime(end)}`);
    srtLines.push(subtitleText);
    srtLines.push('');
    assEvents.push(`Dialogue: 0,${formatAssTime(start)},${formatAssTime(end)},Default,,0,0,0,,${subtitleText.replace(/\n/g, '\\N').replace(/\{/g, '(').replace(/\}/g, ')')}`);
    currentTime = end;
  });

  const srtPath = path.join(outputDir, 'subtitles.srt');
  writeFileSync(srtPath, srtLines.join('\n'), 'utf8');

  const assPath = path.join(outputDir, 'subtitles.ass');
  const ass = `[Script Info]\nScriptType: v4.00+\nPlayResX: ${VIDEO_WIDTH}\nPlayResY: ${VIDEO_HEIGHT}\n\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,${fontName},18,&H00FFFFFF,&H000000FF,&H00101010,&H64000000,0,0,0,0,100,100,0,0,1,1,0,2,40,40,60,1\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n${assEvents.join('\n')}\n`;
  writeFileSync(assPath, ass, 'utf8');

  return { srtPath, assPath, duration: currentTime };
}

async function concatAudio(outputDir, filePaths, outputPath) {
  const listPath = path.join(outputDir, 'audio-concat.txt');
  writeFileSync(listPath, filePaths.map((filePath) => `file '${filePath}'`).join('\n'), 'utf8');
  await execFileAsync('ffmpeg', [
    '-y',
    '-f', 'concat',
    '-safe', '0',
    '-i', listPath,
    '-c:a', 'pcm_s16le',
    outputPath,
  ]);
}

async function renderFinalVideo(outputDir, segments, audioPath, _subtitlePath, totalDuration) {
  const concatList = path.join(outputDir, 'video-concat.txt');
  const lines = [];
  segments.forEach((segment) => {
    lines.push(`file '${segment.clipPath}'`);
    lines.push(`duration ${segment.duration.toFixed(3)}`);
  });
  lines.push(`file '${segments[segments.length - 1].clipPath}'`);
  writeFileSync(concatList, lines.join('\n'), 'utf8');
  const stitchedPath = path.join(outputDir, 'stitched.mp4');
  await execFileAsync('ffmpeg', [
    '-y',
    '-f', 'concat',
    '-safe', '0',
    '-i', concatList,
    '-fps_mode', 'vfr',
    '-pix_fmt', 'yuv420p',
    stitchedPath,
  ]);

  const finalPath = path.join(outputDir, 'video.mp4');
  const ffmpegArgs = [
    '-y',
    '-i', path.basename(stitchedPath),
    ...(audioPath ? ['-i', path.basename(audioPath)] : []),
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-pix_fmt', 'yuv420p',
    ...(audioPath ? ['-c:a', 'aac'] : ['-c:a', 'copy']),
    '-shortest',
    '-t', totalDuration.toFixed(3),
    path.basename(finalPath),
  ];
  await execFileAsync('ffmpeg', ffmpegArgs, { cwd: outputDir });
  return finalPath;
}

function buildWorkspaceLinks(rawOutputDir, fileName) {
  if (typeof rawOutputDir !== 'string' || !rawOutputDir.trim()) {
    return {};
  }
  const normalized = path.resolve(rawOutputDir.trim());
  if (!normalized.startsWith(CONTAINER_CLAWBOX_ROOT)) {
    return {};
  }
  const relativePath = path.relative(CONTAINER_CLAWBOX_ROOT, normalized);
  const parts = relativePath.split(path.sep).filter(Boolean);
  const workspacePart = parts[0] || '';
  if (!workspacePart.startsWith('workspace-')) {
    return {};
  }
  const agentId = workspacePart.slice('workspace-'.length);
  const remainder = parts.slice(1).concat(fileName).map(encodeURIComponent).join('/');
  const routePath = `/workspace-file/${encodeURIComponent(agentId)}/${remainder}`;
  return {
    play_url: `${PLAY_BASE_URL}${routePath}`,
    download_url: `${PLAY_BASE_URL}${routePath}`,
    route_path: routePath,
    agent_id: agentId,
  };
}

function toContainerArtifactPath(rawOutputDir, hostPath, fileName) {
  if (typeof rawOutputDir === 'string' && rawOutputDir.trim()) {
    return path.join(path.resolve(rawOutputDir.trim()), fileName);
  }
  return hostPath;
}

async function synthesize(body) {
  const pkg = resolveProductionPackage(body?.production_package);
  const outputDir = resolveOutputDir(body?.output_dir);
  const rawOutputDir = typeof body?.output_dir === 'string' ? body.output_dir.trim() : '';
  ensureCleanDir(outputDir);
  const segmentsDir = path.join(outputDir, SEGMENT_DIR);
  mkdirSync(segmentsDir, { recursive: true });

  const fontFile = chooseFontFile();
  if (!fontFile) {
    throw new Error('No supported font file found for video synthesis');
  }

  const voiceBlock = pickVoiceoverBlock(pkg);
  const scriptSegments = splitScriptIntoSegments(voiceBlock.text);
  const beats = normalizeSceneBeats(pkg);
  const assetClips = await prepareAssetClips(pkg, outputDir);
  const originalAudioFirst = safeText(pkg?.render_policy?.audio_mode || '') === 'original_audio_first' || assetClips.length > 0;

  const renderedSegments = [];
  for (let index = 0; index < scriptSegments.length; index += 1) {
    const segmentText = scriptSegments[index];
    const beat = beats[assignBeatIndex(index, scriptSegments.length, beats)];
    const chosenAsset = assetClips[index % Math.max(assetClips.length, 1)] || null;
    const audio = originalAudioFirst && chosenAsset
      ? { aiffPath: null, wavPath: null, duration: Math.max(chosenAsset.clipDuration || MIN_SEGMENT_SECONDS, MIN_SEGMENT_SECONDS), baseName: `segment-${String(index + 1).padStart(2, '0')}` }
      : await synthesizeSegmentAudio(segmentsDir, index, segmentText);
    const rendered = {
      index,
      beat_name: beat.name,
      title: buildSceneTitle(pkg, beat, index),
      kicker: buildSceneKicker(pkg, beat, index),
      body: buildSceneBody(pkg, beat, segmentText),
      subtitle: segmentText,
      duration: audio.duration,
      wavPath: audio.wavPath,
      aiffPath: audio.aiffPath,
      baseName: audio.baseName,
      assetClipPath: chosenAsset?.clipPath || null,
      useOriginalAudio: Boolean(originalAudioFirst && chosenAsset),
    };
    rendered.cardPath = await renderSegmentCard(segmentsDir, rendered, index, scriptSegments.length, fontFile);
    rendered.clipPath = await renderSegmentClip(segmentsDir, rendered);
    renderedSegments.push(rendered);
  }

  const voicePathHost = path.join(outputDir, 'voice.wav');
  const syntheticAudioSegments = renderedSegments.map((segment) => segment.wavPath).filter(Boolean);
  if (syntheticAudioSegments.length > 0) {
    await concatAudio(outputDir, syntheticAudioSegments, voicePathHost);
  }

  const subtitleArtifacts = buildSubtitleArtifacts(outputDir, renderedSegments, path.basename(fontFile, path.extname(fontFile)) || 'PingFang');
  const audioInputPath = syntheticAudioSegments.length > 0 ? voicePathHost : null;
  const videoPathHost = await renderFinalVideo(outputDir, renderedSegments, audioInputPath, subtitleArtifacts.assPath, subtitleArtifacts.duration);

  const reportPathHost = path.join(outputDir, 'render_report.json');
  const links = buildWorkspaceLinks(rawOutputDir, 'video.mp4');
  const report = {
    selected_voiceover_title: voiceBlock.title,
    segment_count: renderedSegments.length,
    asset_clip_count: assetClips.length,
    duration_seconds: subtitleArtifacts.duration,
    scenes: renderedSegments.map((segment) => ({
      index: segment.index,
      beat_name: segment.beat_name,
      title: segment.title,
      duration_seconds: segment.duration,
    })),
    ...links,
  };
  writeFileSync(reportPathHost, JSON.stringify(report, null, 2), 'utf8');

  return {
    ok: true,
    stdout: JSON.stringify({
      video_path: toContainerArtifactPath(rawOutputDir, videoPathHost, 'video.mp4'),
      host_video_path: videoPathHost,
      audio_path: toContainerArtifactPath(rawOutputDir, voicePathHost, 'voice.wav'),
      host_audio_path: voicePathHost,
      subtitle_path: toContainerArtifactPath(rawOutputDir, subtitleArtifacts.assPath, 'subtitles.ass'),
      host_subtitle_path: subtitleArtifacts.assPath,
      subtitle_srt_path: toContainerArtifactPath(rawOutputDir, subtitleArtifacts.srtPath, 'subtitles.srt'),
      host_subtitle_srt_path: subtitleArtifacts.srtPath,
      report_path: toContainerArtifactPath(rawOutputDir, reportPathHost, 'render_report.json'),
      host_report_path: reportPathHost,
      output_dir: rawOutputDir || outputDir,
      host_output_dir: outputDir,
      selected_voiceover_title: voiceBlock.title,
      scene_count: renderedSegments.length,
      duration_seconds: subtitleArtifacts.duration,
      ...links,
      ready_for_publish: true,
    }),
    stderr: '',
    json: {
      video_path: toContainerArtifactPath(rawOutputDir, videoPathHost, 'video.mp4'),
      host_video_path: videoPathHost,
      audio_path: toContainerArtifactPath(rawOutputDir, voicePathHost, 'voice.wav'),
      host_audio_path: voicePathHost,
      subtitle_path: toContainerArtifactPath(rawOutputDir, subtitleArtifacts.assPath, 'subtitles.ass'),
      host_subtitle_path: subtitleArtifacts.assPath,
      subtitle_srt_path: toContainerArtifactPath(rawOutputDir, subtitleArtifacts.srtPath, 'subtitles.srt'),
      host_subtitle_srt_path: subtitleArtifacts.srtPath,
      report_path: toContainerArtifactPath(rawOutputDir, reportPathHost, 'render_report.json'),
      host_report_path: reportPathHost,
      output_dir: rawOutputDir || outputDir,
      host_output_dir: outputDir,
      selected_voiceover_title: voiceBlock.title,
      scene_count: renderedSegments.length,
      duration_seconds: subtitleArtifacts.duration,
      ...links,
      ready_for_publish: true,
    },
  };
}

const server = createServer(async (req, res) => {
  if (req.url === '/health' && req.method === 'GET') {
    return sendJson(res, 200, { ok: true, service: 'video-synth-bridge' });
  }
  if (TOKEN) {
    const header = req.headers.authorization || '';
    if (header !== `Bearer ${TOKEN}`) {
      return sendJson(res, 401, { ok: false, error: 'unauthorized' });
    }
  }
  let raw = '';
  for await (const chunk of req) raw += chunk;
  let body = {};
  try {
    body = raw ? JSON.parse(raw) : {};
  } catch {
    return sendJson(res, 400, { ok: false, error: 'invalid_json' });
  }
  try {
    if (req.url === '/render' && req.method === 'POST') {
      return sendJson(res, 200, await synthesize(body));
    }
    if (req.url === '/status' && req.method === 'POST') {
      return sendJson(res, 200, { ok: true, stdout: JSON.stringify({ status: 'ok', job_id: body?.job_id || '' }), stderr: '', json: { status: 'ok', job_id: body?.job_id || '' } });
    }
    return sendJson(res, 404, { ok: false, error: 'not_found' });
  } catch (err) {
    return sendJson(res, 200, { ok: false, stdout: '', stderr: err?.message || String(err) });
  }
});

server.listen(PORT, HOST, () => {
  process.stdout.write(`video-synth-bridge listening on http://${HOST}:${PORT}\n`);
});
