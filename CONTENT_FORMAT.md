# Course content format

Every chapter is one folder: `<book>/chNN-slug/`. The site reads these folders directly; nothing is copied.

```
ddia/ch03-data-models/
  chapter.yaml     title, status, objectives, list of labs
  lecture.md       the lecture
  quiz.yaml        10 auto-graded questions
  project.md       the lab brief
  lab1_*.py        lab code, run from this folder
  NOTES.md         your own notes (shown read-only on the site)
```

The book and chapter number come from the folder path, so they are never written in a file.

## Books

Books are listed in `course.yaml` at the repo root, which also holds the site name (`title`). To add a book, add an entry there and a folder with the same `id`.

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Folder name and URL, for example `ddia` |
| `title` | yes | Shown on the shelf, the cover and the book page |
| `authors` | yes | Shown under the title |
| `tagline` | no | One sentence on the book page |
| `accent` | no | The book's colour: `{ light: "#8a2f24", dark: "#e59a86" }`. Used for the drawn cover and for links and buttons on that book's pages |

Covers: the site draws a cover for every book from its title, authors and accent. To use your own image, put it at `site/public/covers/<id>.jpg` (or `.png`, `.webp`). That folder is ignored by git.

## Adding a chapter

1. Copy the four files from `_templates/chapter/` into the chapter folder (each folder already has a `chapter.yaml` with the title and `status: draft`).
2. Write `lecture.md`, `quiz.yaml`, `project.md`, and the lab scripts.
3. List the labs in `chapter.yaml` and set `status: ready`.
4. From `site/`, run `npm run shuffle-quiz -- ddia/ch03` once, so the correct answers are not all in the same position. Then run `npm run check`, then `npm run verify-labs -- ddia/ch03` to run that chapter's labs.
5. Run `npm run audio -- ddia/ch03` to generate the narration, and listen to a section or two.
6. Fact-check the lecture and quiz against the book chapter, then fill in `verified`.

A chapter with `status: draft` shows as "Coming soon", whatever files it has.

## chapter.yaml

| Field | Required | Meaning |
|---|---|---|
| `title` | yes | Chapter title |
| `status` | no | `draft` (default) or `ready` |
| `summary` | when ready | One sentence for the header and home page |
| `objectives` | when ready | List of things the reader can do afterwards |
| `est_minutes` | no | Reading time for the lecture |
| `labs` | no | List of labs, see below |
| `verified` | no | `date` (`"YYYY-MM-DD"`, quoted) and `notes` saying what was checked |

Each lab:

| Field | Required | Meaning |
|---|---|---|
| `file` | yes | Script name in this folder |
| `title` | yes | Shown in the Labs tab |
| `needs_services` | no | `true` if it needs `docker compose up -d`; skipped by the verifier when Docker is down |
| `needs_ollama` | no | `true` if it calls a local model through Ollama; skipped by the verifier when Ollama is not running |
| `depends_on` | no | Lab files in this chapter that must pass first |
| `expect` | no | Strings that must appear in the output for the lab to count as passing |
| `timeout_s` | no | Default 300 |

## lecture.md

Plain Markdown (GitHub flavoured: tables, fenced code with a language, task lists). Start at `##`; use `###` for subsections. Those headings form the "On this page" list and are what quiz questions link back to.

Two extras:

```markdown
:::callout[Title]
An aside in a box. `:::callout[Title]{type=warn}` for a warning.
:::

:::checkpoint[A question?]
The answer, hidden until clicked.
:::
```

A fenced block with language `mermaid` is drawn as a diagram.

### Writing for the ear

Every lecture can be listened to. The narration is built from the same file: headings, paragraphs, list items, callouts and checkpoints are read aloud; code blocks, tables and diagrams are skipped. Two more blocks control the difference between what is seen and what is heard:

```markdown
:::spoken
Heard but not shown. Put it right after a table, formula or diagram to say what it shows.
The thing above it is outlined while this is read.
:::

:::silent
Shown but not read aloud.
:::
```

Rules of thumb: after every table or formula that matters, add a `:::spoken` block of one to three sentences. Write numbers the way you want them read only inside `:::spoken`; ordinary text is read as written.

If the voice mispronounces a term, add it to `pronunciations` in `course.yaml` (for example `HTAP: "H tap"`) instead of changing the lecture.

Write lectures in your own words. The books are the reference for facts and structure, not text to paste in.

## quiz.yaml

A top-level `questions:` list. A ready chapter needs exactly 10.

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique within the quiz; lowercase letters, digits, dashes |
| `type` | yes | `single`, `multi`, or `numeric` |
| `prompt` | yes | Markdown |
| `options` | single, multi | 2 to 6 strings (Markdown) |
| `answer` | yes | `single`: a letter such as `B`. `multi`: a list such as `[A, C]`. `numeric`: a number |
| `tolerance` | numeric only | Accepted distance from `answer`, default 0 |
| `unit` | numeric only | Label shown after the input |
| `explanation` | yes | Shown after checking, right or wrong |
| `section` | no | Exact text of a `##` or `###` heading in `lecture.md`; becomes a "Review" link |

Letters refer to option order: the first option is A. Put any text containing `: ` in double quotes.

## project.md

Plain Markdown, same extras as the lecture. Suggested shape: a goal, one section per lab with the command, "What you should observe", and "Try" tasks, then what to write in `NOTES.md`. State observations as things that can be checked, and only after running the lab yourself.

## Lecture audio

Audio is generated, never written by hand, and it is derived from `lecture.md`:

```bash
cd site
npm run audio                    # every ready chapter
npm run audio -- ddia/ch03       # one chapter
```

- It uses the Kokoro speech model, which runs on your machine. The model files (about 350 MB) live in `.models/kokoro/` and are not committed; the command prints the download lines if they are missing.
- The voice, language and speed are set under `audio` in `course.yaml`.
- Output goes to `site/public/audio/<book>/<chapter>/`: one small `.m4a` per lecture section plus `manifest.json` with the start time of every sentence. These files are committed.
- Only sections whose text changed are regenerated. Each file name contains a hash of its text, so an edited section gets a new file and the old one is deleted.
- Until a chapter has up-to-date audio, the Listen button uses the browser's built-in voice instead. `npm run check` says which chapters are in that state.

## What the checks cover

`npm run check` (in `site/`): YAML syntax, unknown or missing fields, a ready chapter having all its files, exactly 10 questions, unique ids, answers that point at existing options, `section` matching a real heading, lab files existing, `depends_on` naming real labs. The site build runs the same checks and refuses to build if any fail.

`npm run verify-labs`: runs each listed lab from its folder with `.venv/bin/python`, in dependency order, and requires exit code 0 and every `expect` string.

`npm run check` also warns, without failing, when most single-choice answers in a quiz share one letter, and when a chapter's audio is missing or older than its lecture.

Neither can tell whether a lecture is *correct*. That is what the manual fact-check and the `verified` field are for; `npm run check` prints "NOT fact-checked" next to ready chapters without one.
