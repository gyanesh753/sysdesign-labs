// Server side of lecture audio: where the files live, whether they still match the lecture text,
// and the playlist handed to the browser. Audio is derived data; the lecture is the source of truth.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { ROOT } from './content.ts';
import type { AudioConfig, Chapter } from './content.ts';
import { renderLecture } from './markdown.ts';
import type { NarrationSection } from './markdown.ts';

export const AUDIO_VERSION = 1; // bump to force regeneration of everything

export type ManifestSection = { id: string; title: string; hash: string; file: string; duration: number; starts: number[] };
export type Manifest = { version: number; engine: string; voice: string; lang: string; speed: number; generated: string; sections: ManifestSection[] };

export type PlaylistSection = { id: string; title: string; first: number; count: number; file?: string; duration?: number; starts?: number[] };
export type Playlist = { mode: 'files' | 'speech'; base: string; total: number; minutes: number; sections: PlaylistSection[] };

export const audioDir = (chapterId: string) => path.join(ROOT, 'site', 'public', 'audio', chapterId);

export function sectionHash(section: NarrationSection, cfg: AudioConfig): string {
  const payload = JSON.stringify([AUDIO_VERSION, cfg.voice, cfg.lang, cfg.speed, section.items.map((i) => [i.text, i.gap])]);
  return crypto.createHash('sha1').update(payload).digest('hex').slice(0, 10);
}

export function loadManifest(chapterId: string): Manifest | null {
  try {
    return JSON.parse(fs.readFileSync(path.join(audioDir(chapterId), 'manifest.json'), 'utf8'));
  } catch {
    return null;
  }
}

export type LectureAudio = { html: string; sections: NarrationSection[]; status: 'ok' | 'stale' | 'none'; stale: number; playlist: Playlist };

export async function lectureAudio(ch: Chapter, cfg: AudioConfig, pronunciations: Record<string, string>): Promise<LectureAudio> {
  const { html, sections } = await renderLecture(ch.lecture ?? '', pronunciations);
  const manifest = loadManifest(ch.id);
  const dir = audioDir(ch.id);
  const matched = sections.map((s) => {
    const hash = sectionHash(s, cfg);
    const m = manifest?.sections.find((x) => x.id === s.id && x.hash === hash && x.starts.length === s.items.length);
    return m && fs.existsSync(path.join(dir, m.file)) ? m : null;
  });
  const stale = matched.filter((m) => !m).length;
  const status = !manifest ? 'none' : stale ? 'stale' : 'ok';
  const total = sections.reduce((n, s) => n + s.items.length, 0);
  const words = sections.reduce((n, s) => n + s.items.reduce((w, i) => w + i.text.split(' ').length, 0), 0);
  const seconds = status === 'ok' ? matched.reduce((t, m) => t + m!.duration, 0) : (words / 155) * 60;
  const playlist: Playlist = {
    mode: status === 'ok' ? 'files' : 'speech',
    base: `/audio/${ch.id}/`,
    total,
    minutes: Math.max(1, Math.round(seconds / 60)),
    sections: sections.map((s, k) => {
      const base = { id: s.id, title: s.title, first: s.items[0].i, count: s.items.length };
      const m = matched[k];
      return status === 'ok' && m ? { ...base, file: m.file, duration: m.duration, starts: m.starts } : base;
    }),
  };
  return { html, sections, status, stale, playlist };
}
