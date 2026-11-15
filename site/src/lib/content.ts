// Reads the course content from the repo root (one folder per chapter) and validates it.
// Used by the Astro pages and by scripts/check.ts, so there is exactly one definition of "valid".
import fs from 'node:fs';
import path from 'node:path';
import { parse } from 'yaml';
import { z } from 'zod';
import { slug as slugify } from 'github-slugger';
import { chapterSchema, courseSchema, quizSchema, QUIZ_LENGTH } from './schema.ts';
import type { ChapterMeta, Quiz } from './schema.ts';

export const ROOT = path.resolve(process.env.COURSE_ROOT ?? path.join(process.cwd(), '..'));

export type Problem = { file: string; message: string };

export type Chapter = {
  id: string; // "ddia/ch01-tradeoffs"
  book: string;
  slug: string; // "ch01-tradeoffs"
  number: number;
  dir: string;
  meta: ChapterMeta;
  lecture: string | null;
  quiz: Quiz | null;
  project: string | null;
  notes: string | null;
};

export type Accent = { light: string; dark: string };
export type Book = { id: string; title: string; authors: string; blurb?: string; tagline?: string; accent?: Accent; cover: string | null; chapters: Chapter[] };
export type AudioConfig = { voice: string; lang: string; speed: number };
export type CourseData = { title: string; audio: AudioConfig; pronunciations: Record<string, string>; books: Book[]; problems: Problem[] };

const CHAPTER_DIR = /^ch(\d{2})-[a-z0-9-]+$/;

const read = (file: string) => (fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : null);

/** A cover image the owner dropped into site/public/covers/ (not committed). Null means: draw the designed cover. */
function findCover(bookId: string): string | null {
  for (const ext of ['jpg', 'jpeg', 'png', 'webp']) {
    if (fs.existsSync(path.join(ROOT, 'site', 'public', 'covers', `${bookId}.${ext}`))) return `/covers/${bookId}.${ext}`;
  }
  return null;
}
const rel = (file: string) => path.relative(ROOT, file);

function parseYaml<S extends z.ZodType>(file: string, schema: S, problems: Problem[]): z.infer<S> | null {
  const text = read(file);
  if (text === null) return null;
  let raw: unknown;
  try {
    raw = parse(text);
  } catch (e) {
    problems.push({ file: rel(file), message: `YAML syntax error: ${(e as Error).message}` });
    return null;
  }
  const result = schema.safeParse(raw);
  if (!result.success) {
    for (const issue of result.error.issues) {
      const where = issue.path.length ? issue.path.join('.') + ': ' : '';
      problems.push({ file: rel(file), message: where + issue.message });
    }
    return null;
  }
  return result.data;
}

/** Text of every ## and ### heading in a markdown document, ignoring fenced code. */
export function headings(markdown: string): string[] {
  const out: string[] = [];
  let fenced = false;
  for (const line of markdown.split('\n')) {
    if (/^\s*(```|~~~)/.test(line)) fenced = !fenced;
    if (fenced) continue;
    const m = /^#{2,3}\s+(.+?)\s*#*\s*$/.exec(line);
    if (m) out.push(m[1]);
  }
  return out;
}

export const sectionId = (heading: string) => slugify(heading);

const letterIndex = (l: string) => l.charCodeAt(0) - 65;

function validateChapter(ch: Chapter, problems: Problem[]) {
  const at = (name: string) => `${ch.id}/${name}`;
  const ready = ch.meta.status === 'ready';

  if (ready) {
    for (const [name, value] of [['lecture.md', ch.lecture], ['quiz.yaml', ch.quiz], ['project.md', ch.project]] as const) {
      if (value === null && !problems.some((p) => p.file === at(name))) {
        problems.push({ file: at(name), message: 'missing, but chapter.yaml says status: ready' });
      }
    }
    if (!ch.meta.summary) problems.push({ file: at('chapter.yaml'), message: 'summary is required when status is ready' });
    if (ch.meta.objectives.length === 0) problems.push({ file: at('chapter.yaml'), message: 'at least one objective is required when status is ready' });
  }

  const labFiles = new Set(ch.meta.labs.map((l) => l.file));
  for (const lab of ch.meta.labs) {
    if (!fs.existsSync(path.join(ch.dir, lab.file))) problems.push({ file: at('chapter.yaml'), message: `labs: file "${lab.file}" does not exist in this folder` });
    for (const dep of lab.depends_on) {
      if (!labFiles.has(dep)) problems.push({ file: at('chapter.yaml'), message: `labs: "${lab.file}" depends_on "${dep}", which is not a lab in this chapter` });
    }
  }

  if (ch.quiz) {
    const qs = ch.quiz.questions;
    if (ready && qs.length !== QUIZ_LENGTH) problems.push({ file: at('quiz.yaml'), message: `has ${qs.length} questions, a ready chapter needs exactly ${QUIZ_LENGTH}` });
    const seen = new Set<string>();
    const sections = ch.lecture ? new Set(headings(ch.lecture)) : null;
    for (const q of qs) {
      const tag = `question "${q.id}": `;
      if (seen.has(q.id)) problems.push({ file: at('quiz.yaml'), message: tag + 'duplicate id' });
      seen.add(q.id);
      if (q.type !== 'numeric') {
        const answers = q.type === 'single' ? [q.answer] : q.answer;
        for (const a of answers) {
          if (letterIndex(a) >= q.options.length) problems.push({ file: at('quiz.yaml'), message: tag + `answer ${a} but there are only ${q.options.length} options` });
        }
        if (new Set(answers).size !== answers.length) problems.push({ file: at('quiz.yaml'), message: tag + 'answer lists the same letter twice' });
        if (new Set(q.options).size !== q.options.length) problems.push({ file: at('quiz.yaml'), message: tag + 'two options are identical' });
      }
      if (q.section && sections && !sections.has(q.section)) {
        problems.push({ file: at('quiz.yaml'), message: tag + `section "${q.section}" is not a ## or ### heading in lecture.md` });
      }
    }
  }
}

let cache: { at: number; data: CourseData } | null = null;

export function loadCourse(): CourseData {
  // Tiny cache so one page render does not re-read the tree for every helper call; dev reloads still pick up edits.
  if (cache && Date.now() - cache.at < 500) return cache.data;
  const problems: Problem[] = [];
  const course = parseYaml(path.join(ROOT, 'course.yaml'), courseSchema, problems);
  if (!course) {
    if (problems.length === 0) problems.push({ file: 'course.yaml', message: 'missing' });
    return { title: 'Course', audio: { voice: 'bm_george', lang: 'en-gb', speed: 1 }, pronunciations: {}, books: [], problems };
  }

  const books: Book[] = course.books.map((b) => {
    const bookDir = path.join(ROOT, b.id);
    const chapters: Chapter[] = [];
    if (!fs.existsSync(bookDir)) {
      problems.push({ file: 'course.yaml', message: `book "${b.id}" has no folder ${b.id}/` });
      return { ...b, cover: findCover(b.id), chapters };
    }
    for (const name of fs.readdirSync(bookDir).sort()) {
      const dir = path.join(bookDir, name);
      if (!fs.statSync(dir).isDirectory()) continue;
      const m = CHAPTER_DIR.exec(name);
      if (!m) {
        problems.push({ file: `${b.id}/${name}`, message: 'folder name must look like ch03-data-models' });
        continue;
      }
      const meta = parseYaml(path.join(dir, 'chapter.yaml'), chapterSchema, problems) ?? chapterSchema.parse({ title: name.replace(/^ch\d{2}-/, '').replace(/-/g, ' ') });
      const ch: Chapter = {
        id: `${b.id}/${name}`,
        book: b.id,
        slug: name,
        number: Number(m[1]),
        dir,
        meta,
        lecture: read(path.join(dir, 'lecture.md')),
        quiz: parseYaml(path.join(dir, 'quiz.yaml'), quizSchema, problems),
        project: read(path.join(dir, 'project.md')),
        notes: read(path.join(dir, 'NOTES.md')),
      };
      validateChapter(ch, problems);
      chapters.push(ch);
    }
    return { ...b, cover: findCover(b.id), chapters };
  });

  const data = { title: course.title, audio: course.audio, pronunciations: course.pronunciations, books, problems };
  cache = { at: Date.now(), data };
  return data;
}

/** For the site: fail loudly instead of rendering half-valid content. */
export function loadCourseOrThrow(): CourseData {
  const data = loadCourse();
  if (data.problems.length) {
    throw new Error('Course content has problems (run `npm run check`):\n' + data.problems.map((p) => `  ${p.file}: ${p.message}`).join('\n'));
  }
  return data;
}
