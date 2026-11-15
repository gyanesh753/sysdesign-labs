# Booktern

Hands-on labs for *Designing Data-Intensive Applications* (2nd ed.) and *AI Engineering* (Chip Huyen).
One folder per chapter. Commit after every lab with a short `NOTES.md` of what you observed.

```
ddia/ch01-tradeoffs ... ch14-ethics      DDIA chapters: lecture, quiz, lab brief and lab scripts for each
aie/ch01-intro ... ch10-architecture-feedback   AI Engineering chapters: lecture, quiz, lab brief and lab scripts for each
capstone/                                 the mini AI knowledge platform that grows each sprint
_templates/NOTES.md                       the template already copied into every chapter folder
_templates/chapter/                       skeleton files for writing a new chapter
site/                                     the Booktern website (shelf, lectures, quizzes, lab checklists)
course.yaml, CONTENT_FORMAT.md            list of books, and the format of each chapter's files
docker-compose.yml                        Postgres, Redpanda (Kafka), S3-compatible store, Toxiproxy
verify_setup.py                           checks everything below
```

## Setup (about 45 minutes, mostly downloads). Written for macOS on Apple Silicon.

Disk: plan for roughly 8 GB free. RAM: 16 GB is comfortable. Stop the containers when you aren't using them.

### Step 1. Install the tools (15 min)

See what you already have:

```bash
git --version; brew --version; uv --version; docker --version; ollama --version
```

Install only what is missing:

- **Git and compilers:** `xcode-select --install`
- **Homebrew:** run the one-line installer from brew.sh, then follow the "Next steps" it prints.
- **uv (Python manager):** `brew install uv`
- **Docker Desktop:** download "Docker Desktop for Mac with Apple silicon" from docker.com/products/docker-desktop, open the .dmg, drag it to Applications, launch it, accept the terms (you can skip signing in), and wait until it says **Engine running**.
- **Ollama:** download from ollama.com/download, open the app once. A menu-bar icon means the server is running.

Set your git identity once (skip if already set):

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Step 2. Create the repo (3 min)

```bash
unzip ~/Downloads/sysdesign-labs-starter.zip -d ~
cd ~/sysdesign-labs
git init -b main
cp .env.example .env
```

`.env` holds local-only passwords and is already in `.gitignore`.

### Step 3. Python environment (5 min)

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
python verify_setup.py python
```

Expect every line to say `[ ok ]`. In every new terminal, run `source .venv/bin/activate` first.

### Step 4. Start the services (10 min, first run downloads images)

```bash
docker compose up -d
docker compose ps
python verify_setup.py services
```

Expect four containers `Up` (Postgres shows `healthy`). Extra manual checks:

```bash
docker exec lab-postgres psql -U lab -d lab -c "select version();"
curl localhost:8474/version
```

Open http://localhost:9001 for the object store's web console (log in with the keys in `.env`).

### Step 5. Local models (10 min, ~2.5 GB download)

Start this while Step 4 is pulling images.

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
ollama run llama3.2:3b "Say hello in five words"
python verify_setup.py ollama
```

Using a hosted model instead? Put its key in `.env` (never in code), for example `ANTHROPIC_API_KEY=...`. Everything still works; the Ollama checks will just show `[warn]`.

### Step 6. Full check and first commit (3 min)

```bash
python verify_setup.py
uv pip freeze > requirements.lock
git add -A
git commit -m "Lab environment ready"
```

Done when `verify_setup.py` ends with **All required checks passed.**

Optional: create an empty repo named `sysdesign-labs` on github.com (private while learning), then copy the two `git remote add ...` / `git push ...` lines GitHub shows you.

## The site

Booktern shows each book as a cover on a shelf. Open a book to see its chapters; each chapter has a lecture you can read or listen to, a 10-question quiz and labs. Progress is remembered in the browser. The site lives in `site/` and needs Node 22.18 or newer.

```bash
cd site
npm install
npm run dev
```

Then open http://127.0.0.1:4321. Other commands, all run from `site/`:

| Do this | Command |
|---|---|
| Validate every chapter's files | `npm run check` |
| Run every lab and check its output | `npm run verify-labs` |
| Run one chapter's labs | `npm run verify-labs -- ddia/ch02` |
| Generate lecture audio (changed sections only) | `npm run audio` |
| Shuffle a new quiz's options | `npm run shuffle-quiz -- ddia/ch03` |
| Build a static copy into `site/dist` | `npm run build` |

All 24 chapters are written: 14 for DDIA and 10 for AI Engineering, each with a lecture, narrated audio, a quiz and labs. To add or change one, see `CONTENT_FORMAT.md`.

Each book gets a cover drawn in its own colour. To show your own cover image instead, put it in `site/public/covers/` named after the book, for example `ddia.jpg`. Images in that folder are not committed.

Seven of the AI Engineering labs call a model running on your machine through Ollama: any chat model for chapters 1, 5 and 9, and `nomic-embed-text` for chapters 3, 6 and 10. They are marked "needs Ollama" on the site, and `npm run verify-labs` skips them when Ollama is not running.

## Daily commands

| Do this | Command |
|---|---|
| New terminal | `cd ~/sysdesign-labs && source .venv/bin/activate` |
| Start services | `docker compose up -d` |
| Stop, keep data | `docker compose stop` |
| Wipe all service data | `docker compose down -v` |
| Watch a service | `docker compose logs -f redpanda` |
| SQL shell | `docker exec -it lab-postgres psql -U lab -d lab` |
| Re-check everything | `python verify_setup.py` |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Cannot connect to the Docker daemon` | Open Docker Desktop and wait for **Engine running**. |
| `port is already allocated` on 5432 | Another Postgres is running. Set `POSTGRES_PORT=5433` in `.env`, then `docker compose up -d`. |
| `no matching manifest for linux/arm64` | Add `platform: linux/amd64` under that service in `docker-compose.yml`. |
| Redpanda keeps restarting | `docker logs lab-redpanda`. Give Docker Desktop at least 4 GB (Settings, Resources). |
| Kafka check fails but the port is open | `docker compose logs redpanda`, and confirm `docker-compose.yml` still advertises `localhost:19092`. |
| S3 check fails with a signature or access error | Make sure `.env` keys match, then `docker compose up -d --force-recreate rustfs`. |
| `hnswlib` fails to build | `xcode-select --install`, then `uv pip install hnswlib`. Only needed from DDIA Ch 4. |
| `ollama pull` says model not found | Browse ollama.com/library, pick a similar small model, and change the names in `verify_setup.py`. |

## Notes on choices

- **RustFS instead of MinIO.** MinIO's community edition stopped publishing Docker images in October 2025 and its repository was archived in April 2026, so the S3-compatible store here is RustFS.
- **Everything binds to 127.0.0.1**, so nothing is reachable from your network.
- **Postgres runs with `wal_level=logical`** so change data capture works later (DDIA Ch 12).
