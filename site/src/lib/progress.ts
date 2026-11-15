// Browser-only progress store. Everything lives in localStorage under one key.
const KEY = 'sysdesign-labs-progress-v1';

export type ChapterProgress = {
  lectureRead?: boolean;
  quizBest?: number;
  quizLast?: number;
  quizMissed?: string[];
  listenAt?: number;
  labs?: Record<string, boolean>;
};
export type Progress = Record<string, ChapterProgress>;

export function loadAll(): Progress {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) ?? '{}');
    return v && typeof v === 'object' ? v : {};
  } catch {
    return {};
  }
}

function saveAll(p: Progress) {
  try {
    localStorage.setItem(KEY, JSON.stringify(p));
  } catch {
    /* private mode or storage full: progress just is not remembered */
  }
}

export const getChapter = (id: string): ChapterProgress => loadAll()[id] ?? {};

export function updateChapter(id: string, patch: (c: ChapterProgress) => void): ChapterProgress {
  const all = loadAll();
  const c = (all[id] ??= {});
  patch(c);
  saveAll(all);
  return c;
}

export const exportJson = () => JSON.stringify({ version: 1, exported: new Date().toISOString(), progress: loadAll() }, null, 2);

export function importJson(text: string) {
  const v = JSON.parse(text);
  if (!v || typeof v.progress !== 'object' || v.progress === null) throw new Error('Not a progress export file');
  saveAll(v.progress);
}

export const labsDone = (c: ChapterProgress, files: string[]) => files.filter((f) => c.labs?.[f]).length;

export const PASS_MARK = 7;

/** What a reader should do next in a chapter, or null when it is complete. */
export function nextStep(c: ChapterProgress, labFiles: string[]): { hash: string; label: string } | null {
  if (!c.lectureRead) return (c.listenAt ?? 0) > 0 ? { hash: '#lecture', label: 'Keep listening' } : { hash: '', label: 'Read the lecture' };
  if ((c.quizBest ?? 0) < PASS_MARK) return { hash: '#quiz', label: 'Take the quiz' };
  if (labsDone(c, labFiles) < labFiles.length) return { hash: '#labs', label: 'Run the labs' };
  return null;
}

export const hasStarted = (c: ChapterProgress) => !!(c.lectureRead || c.quizBest !== undefined || (c.listenAt ?? 0) > 0 || Object.values(c.labs ?? {}).some(Boolean));
