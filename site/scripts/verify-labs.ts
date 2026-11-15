// npm run verify-labs [-- ddia/ch01-tradeoffs]: run every lab listed in chapter.yaml and check its output.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { loadCourse, ROOT } from '../src/lib/content.ts';

const filter = process.argv[2];
const venvPython = path.join(ROOT, '.venv', 'bin', 'python');
const python = fs.existsSync(venvPython) ? venvPython : 'python3';

function servicesUp(): boolean {
  const r = spawnSync('docker', ['compose', 'ps', '--status', 'running', '-q'], { cwd: ROOT, encoding: 'utf8' });
  return r.status === 0 && r.stdout.trim().length > 0;
}
let services: boolean | null = null;
const ollamaUp = () => spawnSync('curl', ['-s', '-m', '2', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:11434/api/tags'], { encoding: 'utf8' }).stdout === '200';
let ollama: boolean | null = null;

let failed = 0;
let ran = 0;
let skipped = 0;
const course = loadCourse();
for (const ch of course.books.flatMap((b) => b.chapters)) {
  if (filter && !ch.id.startsWith(filter)) continue;
  if (!ch.meta.labs.length) continue;
  console.log(`\n${ch.id}`);
  const state = new Map<string, 'pass' | 'fail' | 'skip'>();
  const pending = [...ch.meta.labs];
  while (pending.length) {
    // Next lab whose dependencies have all been handled (falls back to file order on a cycle).
    const i = Math.max(0, pending.findIndex((l) => l.depends_on.every((d) => state.has(d))));
    const lab = pending.splice(i, 1)[0];
    const blocked = lab.depends_on.find((d) => state.get(d) !== 'pass');
    if (blocked) {
      state.set(lab.file, 'skip');
      skipped++;
      console.log(`  skip  ${lab.file}  (needs ${blocked}, which did not pass)`);
      continue;
    }
    if (lab.needs_services && !(services ??= servicesUp())) {
      state.set(lab.file, 'skip');
      skipped++;
      console.log(`  skip  ${lab.file}  (needs Docker services: docker compose up -d)`);
      continue;
    }
    if (lab.needs_ollama && !(ollama ??= ollamaUp())) {
      state.set(lab.file, 'skip');
      skipped++;
      console.log(`  skip  ${lab.file}  (needs Ollama running: open the Ollama app)`);
      continue;
    }
    const t = Date.now();
    const r = spawnSync(python, [lab.file], { cwd: ch.dir, encoding: 'utf8', timeout: lab.timeout_s * 1000, maxBuffer: 64 * 1024 * 1024 });
    const secs = ((Date.now() - t) / 1000).toFixed(1);
    const out = (r.stdout ?? '') + (r.stderr ?? '');
    const missing = lab.expect.filter((e) => !out.includes(e));
    ran++;
    if (r.status === 0 && missing.length === 0) {
      state.set(lab.file, 'pass');
      console.log(`  pass  ${lab.file}  (${secs}s)`);
    } else {
      state.set(lab.file, 'fail');
      failed++;
      const why = r.error ? String(r.error.message) : r.status !== 0 ? `exit code ${r.status}` : `output is missing: ${missing.map((m) => JSON.stringify(m)).join(', ')}`;
      console.log(`  FAIL  ${lab.file}  (${secs}s) ${why}`);
      console.log(out.trim().split('\n').slice(-8).map((l) => '        ' + l).join('\n'));
    }
  }
}
console.log(`\n${ran - failed} passed, ${failed} failed, ${skipped} skipped.`);
process.exit(failed ? 1 : 0);
