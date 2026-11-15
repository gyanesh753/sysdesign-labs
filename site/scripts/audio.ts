// npm run audio [-- ddia/ch02] [-- --force]: generate lecture audio for ready chapters with Kokoro.
// Only sections whose text (or the voice settings) changed are regenerated.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { loadCourse, ROOT } from '../src/lib/content.ts';
import { renderLecture } from '../src/lib/markdown.ts';
import { audioDir, loadManifest, sectionHash, AUDIO_VERSION } from '../src/lib/audio.ts';
import type { Manifest, ManifestSection } from '../src/lib/audio.ts';

const args = process.argv.slice(2);
const force = args.includes('--force');
const filter = args.find((a) => !a.startsWith('--'));
const BITRATE = 32000;

const course = loadCourse();
if (course.problems.length) {
  console.error('Fix the content problems first: npm run check');
  process.exit(1);
}
const modelDir = path.join(ROOT, '.models', 'kokoro');
const model = path.join(modelDir, 'kokoro-v1.0.onnx');
const voices = path.join(modelDir, 'voices-v1.0.bin');
if (!fs.existsSync(model) || !fs.existsSync(voices)) {
  const url = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0';
  console.error(`Kokoro model files are missing. Download them once (about 350 MB):\n  mkdir -p ${modelDir} && cd ${modelDir}\n  curl -LO ${url}/kokoro-v1.0.onnx\n  curl -LO ${url}/voices-v1.0.bin`);
  process.exit(1);
}
const has = (cmd: string) => spawnSync('which', [cmd]).status === 0;
const encoder = has('afconvert') ? 'afconvert' : has('ffmpeg') ? 'ffmpeg' : null;
if (!encoder) {
  console.error('Need afconvert (built into macOS) or ffmpeg to encode the audio.');
  process.exit(1);
}
if (!has('uv')) {
  console.error('Need uv to run the speech model: brew install uv');
  process.exit(1);
}

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'lecture-audio-'));
type Planned = { chapterId: string; sections: { id: string; title: string; hash: string; keep?: ManifestSection; wav?: string; key: string }[] };
const plans: Planned[] = [];
const jobs: { key: string; wav: string; items: { text: string; gap: number }[] }[] = [];

for (const ch of course.books.flatMap((b) => b.chapters)) {
  if (ch.meta.status !== 'ready' || !ch.lecture) continue;
  if (filter && !ch.id.startsWith(filter)) continue;
  const { sections } = await renderLecture(ch.lecture, course.pronunciations);
  const manifest = loadManifest(ch.id);
  const plan: Planned = { chapterId: ch.id, sections: [] };
  for (const s of sections) {
    const hash = sectionHash(s, course.audio);
    const key = `${ch.id}#${s.id}`;
    const keep = force ? undefined : manifest?.sections.find((x) => x.id === s.id && x.hash === hash && fs.existsSync(path.join(audioDir(ch.id), x.file)));
    if (keep) plan.sections.push({ id: s.id, title: s.title, hash, keep, key });
    else {
      const wav = path.join(tmp, `${jobs.length}.wav`);
      jobs.push({ key, wav, items: s.items.map((i) => ({ text: i.text, gap: i.gap })) });
      plan.sections.push({ id: s.id, title: s.title, hash, wav, key });
    }
  }
  plans.push(plan);
}

let results: Record<string, { duration: number; starts: number[] }> = {};
if (jobs.length) {
  console.log(`Generating ${jobs.length} section${jobs.length > 1 ? 's' : ''} with voice ${course.audio.voice} ...`);
  const jobFile = path.join(tmp, 'job.json');
  const resultFile = path.join(tmp, 'result.json');
  fs.writeFileSync(jobFile, JSON.stringify({ model, voices, voice: course.audio.voice, lang: course.audio.lang, speed: course.audio.speed, result: resultFile, sections: jobs }));
  const script = path.join(ROOT, 'site', 'scripts', 'tts_kokoro.py');
  const run = spawnSync('uv', ['run', '-q', '--python', '3.12', '--with', 'kokoro-onnx', '--with', 'soundfile', 'python', '-I', script, jobFile], { stdio: ['ignore', 'inherit', 'inherit'] });
  if (run.status !== 0 || !fs.existsSync(resultFile)) {
    console.error('Speech synthesis failed; nothing was changed.');
    process.exit(1);
  }
  results = JSON.parse(fs.readFileSync(resultFile, 'utf8'));
}

for (const plan of plans) {
  const dir = audioDir(plan.chapterId);
  fs.mkdirSync(dir, { recursive: true });
  const sections: ManifestSection[] = [];
  let made = 0;
  for (const s of plan.sections) {
    if (s.keep) {
      sections.push(s.keep);
      continue;
    }
    const file = `${s.id}.${s.hash}.m4a`;
    const out = path.join(dir, file);
    const enc =
      encoder === 'afconvert'
        ? spawnSync('afconvert', ['-f', 'm4af', '-d', 'aac', '-b', String(BITRATE), '-c', '1', s.wav!, out])
        : spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', s.wav!, '-ac', '1', '-c:a', 'aac', '-b:a', `${BITRATE / 1000}k`, out]);
    if (enc.status !== 0) {
      console.error(`Encoding failed for ${s.key}: ${enc.stderr}`);
      process.exit(1);
    }
    sections.push({ id: s.id, title: s.title, hash: s.hash, file, ...results[s.key] });
    made++;
  }
  const manifest: Manifest = { version: AUDIO_VERSION, engine: 'kokoro-onnx v1.0', voice: course.audio.voice, lang: course.audio.lang, speed: course.audio.speed, generated: new Date().toISOString().slice(0, 10), sections };
  fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(manifest, null, 1) + '\n');
  const wanted = new Set(sections.map((s) => s.file));
  let removed = 0;
  for (const f of fs.readdirSync(dir)) {
    if (f.endsWith('.m4a') && !wanted.has(f)) {
      fs.unlinkSync(path.join(dir, f));
      removed++;
    }
  }
  const seconds = sections.reduce((t, s) => t + s.duration, 0);
  const bytes = sections.reduce((t, s) => t + fs.statSync(path.join(dir, s.file)).size, 0);
  console.log(`${plan.chapterId}: ${sections.length} sections, ${(seconds / 60).toFixed(1)} min, ${(bytes / 1e6).toFixed(1)} MB  (${made} generated, ${sections.length - made} unchanged, ${removed} old files removed)`);
}
fs.rmSync(tmp, { recursive: true, force: true });
if (!plans.length) console.log('No ready chapters matched.');
