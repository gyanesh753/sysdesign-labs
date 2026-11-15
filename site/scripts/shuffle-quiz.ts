// npm run shuffle-quiz -- ddia/ch03   Shuffle the options of every single/multi question and fix the answer letters.
// Use it once on a newly written quiz: authors tend to put the right answer in the same position every time.
import fs from 'node:fs';
import path from 'node:path';
import { parseDocument } from 'yaml';
import { loadCourse } from '../src/lib/content.ts';

const filter = process.argv[2];
if (!filter) {
  console.error('Say which chapter(s): npm run shuffle-quiz -- ddia/ch03   (a prefix such as "ddia" matches several)');
  process.exit(1);
}
const LETTERS = 'ABCDEF';
const rand = () => Math.random();

for (const ch of loadCourse().books.flatMap((b) => b.chapters)) {
  if (!ch.id.startsWith(filter) || !ch.quiz) continue;
  const file = path.join(ch.dir, 'quiz.yaml');
  const doc = parseDocument(fs.readFileSync(file, 'utf8'));
  const questions: any = doc.get('questions');
  const tally: Record<string, number> = {};
  for (const q of questions.items) {
    const type = q.get('type');
    if (type === 'numeric') continue;
    const options = q.get('options');
    const n = options.items.length;
    const answer = q.get('answer');
    const old: string[] = type === 'single' ? [answer] : answer.items.map((i: any) => i.value ?? i);
    const order = [...Array(n).keys()];
    for (let i = n - 1; i > 0; i--) {
      const j = Math.floor(rand() * (i + 1));
      [order[i], order[j]] = [order[j], order[i]];
    }
    options.items = order.map((i) => options.items[i]);            // new position k holds old option order[k]
    const next = old.map((l) => LETTERS[order.indexOf(LETTERS.indexOf(l))]).sort();
    if (type === 'single') {
      q.set('answer', next[0]);
      tally[next[0]] = (tally[next[0]] ?? 0) + 1;
    } else {
      const seq: any = doc.createNode(next);
      seq.flow = true;
      q.set('answer', seq);
    }
  }
  fs.writeFileSync(file, doc.toString({ lineWidth: 0 }));
  console.log(`${ch.id}: shuffled; single-choice answers now ${Object.entries(tally).sort().map(([l, c]) => `${l}=${c}`).join(' ')}`);
}
