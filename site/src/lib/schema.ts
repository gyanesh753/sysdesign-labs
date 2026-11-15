// Schemas for the course content files. Shared by the site and by `npm run check`.
import { z } from 'zod';

export const QUIZ_LENGTH = 10;

const letter = z.string().regex(/^[A-F]$/, 'must be a single letter A-F');

export const courseSchema = z.strictObject({
  title: z.string().min(1),
  books: z
    .array(
      z.strictObject({
        id: z.string().regex(/^[a-z0-9-]+$/),
        title: z.string().min(1),
        authors: z.string().min(1),
        blurb: z.string().optional(),
        tagline: z.string().optional(),
        accent: z.strictObject({ light: z.string().regex(/^#[0-9a-fA-F]{6}$/), dark: z.string().regex(/^#[0-9a-fA-F]{6}$/) }).optional(),
      }),
    )
    .min(1),
  // Voice used by `npm run audio` (Kokoro voice id, language code, speaking speed).
  audio: z.strictObject({ voice: z.string().min(1), lang: z.string().min(1), speed: z.number().positive().default(1) }).default({ voice: 'bm_george', lang: 'en-gb', speed: 1 }),
  // Spoken replacements for words the voice gets wrong, e.g. HTAP: "H tap".
  pronunciations: z.record(z.string(), z.string()).default({}),
});

const labSchema = z.strictObject({
  file: z.string().min(1),
  title: z.string().min(1),
  needs_services: z.boolean().default(false),
  needs_ollama: z.boolean().default(false),
  depends_on: z.array(z.string()).default([]),
  expect: z.array(z.string()).default([]),
  timeout_s: z.number().positive().default(300),
});

export const chapterSchema = z.strictObject({
  title: z.string().min(1),
  status: z.enum(['draft', 'ready']).default('draft'),
  summary: z.string().optional(),
  objectives: z.array(z.string().min(1)).default([]),
  est_minutes: z.number().positive().optional(),
  labs: z.array(labSchema).default([]),
  verified: z
    .strictObject({ date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'use YYYY-MM-DD, in quotes'), notes: z.string().min(1) })
    .optional(),
});

const questionBase = {
  id: z.string().regex(/^[a-z0-9-]+$/, 'lowercase letters, digits and dashes only'),
  prompt: z.string().min(1),
  explanation: z.string().min(1),
  section: z.string().min(1).optional(),
};

export const questionSchema = z.discriminatedUnion('type', [
  z.strictObject({ ...questionBase, type: z.literal('single'), options: z.array(z.string().min(1)).min(2).max(6), answer: letter }),
  z.strictObject({ ...questionBase, type: z.literal('multi'), options: z.array(z.string().min(1)).min(2).max(6), answer: z.array(letter).min(1) }),
  z.strictObject({ ...questionBase, type: z.literal('numeric'), answer: z.number(), tolerance: z.number().nonnegative().default(0), unit: z.string().optional() }),
]);

export const quizSchema = z.strictObject({ questions: z.array(questionSchema).min(1) });

export type Course = z.infer<typeof courseSchema>;
export type ChapterMeta = z.infer<typeof chapterSchema>;
export type Lab = z.infer<typeof labSchema>;
export type Question = z.infer<typeof questionSchema>;
export type Quiz = z.infer<typeof quizSchema>;
