// npm run check: validate every chapter's files against the content format.
import { loadCourse } from '../src/lib/content.ts';
import { lectureAudio } from '../src/lib/audio.ts';

const course = loadCourse();
const chapters = course.books.flatMap((b) => b.chapters);
const ready = chapters.filter((c) => c.meta.status === 'ready');

const warnings: string[] = [];
for (const book of course.books) {
  console.log(`\n${book.title}`);
  for (const c of book.chapters) {
    const bad = course.problems.filter((p) => p.file.startsWith(c.id + '/')).length;
    let audio = '';
    // Authors tend to put the right answer in the same position. Warn when one letter dominates.
    const singles = (c.quiz?.questions ?? []).filter((q) => q.type === 'single').map((q) => q.answer as string);
    const top = Math.max(0, ...['A', 'B', 'C', 'D', 'E', 'F'].map((l) => singles.filter((a) => a === l).length));
    if (singles.length >= 5 && top / singles.length > 0.6) warnings.push(`${c.id}: ${top} of ${singles.length} single-choice answers are the same letter. Run: npm run shuffle-quiz -- ${c.id}`);
    if (!bad && c.meta.status === 'ready' && c.lecture) {
      const a = await lectureAudio(c, course.audio, course.pronunciations);
      audio = a.status === 'ok' ? `, audio ${a.playlist.minutes} min` : a.status === 'stale' ? ', audio STALE' : ', no audio';
      if (a.status === 'stale') warnings.push(`${c.id}: ${a.stale} of ${a.sections.length} audio sections no longer match the lecture. Run: npm run audio -- ${c.id}`);
      if (a.status === 'none') warnings.push(`${c.id}: no generated audio, the site will use the browser voice. Run: npm run audio -- ${c.id}`);
    }
    const state = bad ? `${bad} problem${bad > 1 ? 's' : ''}` : c.meta.status === 'ready' ? 'ready' : 'draft';
    const extra = c.meta.status === 'ready' ? `  quiz ${c.quiz?.questions.length ?? 0}q, labs ${c.meta.labs.length}${c.meta.verified ? `, checked ${c.meta.verified.date}` : ', NOT fact-checked'}${audio}` : '';
    console.log(`  ${bad ? 'x' : c.meta.status === 'ready' ? '+' : '.'} ${c.slug.padEnd(30)} ${state}${extra}`);
  }
}

if (course.problems.length) {
  console.error(`\n${course.problems.length} problem${course.problems.length > 1 ? 's' : ''}:`);
  for (const p of course.problems) console.error(`  ${p.file}: ${p.message}`);
  process.exit(1);
}
if (warnings.length) console.log('\nWarnings (not errors):\n' + warnings.map((w) => '  ' + w).join('\n'));
console.log(`\nOK: ${ready.length} ready, ${chapters.length - ready.length} draft, no problems.`);
