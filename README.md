# 0-Note · A Programmer's Knowledge Base Constitution

**English | [简体中文](./README.zh-CN.md)**

> A pure-Markdown, tool-agnostic, AI-friendly knowledge management system for programmers.
> It combines PARA (action-oriented categories) + Zettelkasten (atomic notes) + MOC (maps of content) + Johnny.Decimal (numbered locations) + Karpathy-style layering (raw vs. finished material).
> This file is the **single source of rules** for the system: both humans and AI follow it.

Note: note filenames inside this vault are Chinese; this English version is a courtesy translation, the Chinese file remains the authoritative text.

## 1. Directory System (numbers are priorities)

```text
0-Note\
├── 00-索引\    Index entry layer: holds the root index `00-索引.md` (one global page: every project's name / status / knowledge count / entry)
├── 10-项目\    Project layer. Projects are self-contained - plan, raw material, knowledge and templates live in one folder (containers: `!名词解释\`, `!系统与工具\`)
├── 40-归档\    Archive layer. Finished projects, outdated knowledge (append-only)
├── 50-资源\    Resource layer. Collected material/tools/scripts/images, not yet distilled
├── 90-模板\    Template layer. Global note skeletons
└── README.md  This file (the constitution)
```

> **Why the root index sits inside a folder:** `00-索引/00-索引.md` is a directory *on purpose*. Windows Explorer always sorts folders before files and offers no option to mix them, so a top-level `00-索引.md` file would always sink below `10-项目\`, `40-归档\`, `50-资源\` and `90-模板\`. Keeping the vault's entry point as a folder whose name starts with `00-` puts it first in every default view, on any machine. Do not "optimise" this back into a top-level single file.

Companion directory outside the repo (optional, **not created yet** - create it yourself if you want one):

- `F:\0-Note-Data\` - a suggested home for Anki decks, xlsx/csv, processing scripts and other raw material, mirroring the vault's subfolder names (e.g. `英语`). Nothing in this repo depends on it

### What 00~90 mean (numbers are both priority and knowledge lifecycle)

> The numeric prefixes carry two meanings: (1) smaller numbers sit closer to the repo core and move more often; (2) each layer is a lifecycle stage. **The same topic moves between layers as its lifecycle position changes.** Examples below are real files from this vault (the archive layer is currently empty, so that row shows the shape instead):

| Directory | Meaning | What goes in | Real example in this vault |
|------|------|--------|--------------------|
| **00-索引** | Index entry layer · holds the root index `00-索引/00-索引.md` | Links and routes only: one line per directory under `10-项目/` (name / status / knowledge count / entry); content lives in the owner's `20-知识\` | the `## 项目清单` table of the root index |
| **10-项目** | Project layer · self-contained, goal+deadline | Project folder (`!项目说明.md`, `00-索引.md`, optional `!实施计划.md` / `90-模板\`) + the project's `20-知识\` (**the finished notes themselves**, the only home for note bodies) | `10-项目/2026-12-掌握SQLite/00-索引.md` and its `20-知识/SQLite介绍.md` |
| **40-归档** | Archive layer · retired | Finished projects and outdated knowledge, moved in wholesale (append-only) | currently empty (no project has met the four criteria yet); once archived it looks like `40-归档/2026-10-掌握Markdown/`, with its notes travelling along under `20-知识/` |
| **50-资源** | Resource layer · raw material staging | Unrefined material, images, script tools | `50-资源/图片/`, `50-资源/工具/`, `50-资源/英语/` |
| **90-模板** | Template layer · skeletons | Templates copied when writing new notes (never edited) | `90-模板/20-笔记正文模板.md` |

**One-line mnemonic**: `00 points the way -> 10 starts a project -> 50 stages raw material -> 20-知识 hosts the notes (inside the project) -> 40 seals the past -> 90 provides the format`.

**The numbers name layers, not steps**: knowledge flows raw -> project -> finished -> indexed -> sealed (see section 6), and `50-资源` carries a high number simply because it sits furthest from the core, not because it is low priority.

**This layer is not pushed to the remote**: images and language material stay on this machine (`.gitignore` ignores `50-资源/*` with a small whitelist); only the vault checker, event logs and index-referenced docs are committed. A fresh clone therefore has no `50-资源/图片/` or `50-资源/英语/`, and links into them only resolve locally.

### Archive criteria (four mechanical conditions, checked by A12)

A project moves wholesale into `40-归档/` only when all four hold:

1. `!项目说明.md` has `status: done` in its frontmatter
2. The 「出口」or「验收」section has no unchecked item (`- [ ]`)
3. The body has a 「复盘」section (retrospective)
4. The 「任务清单」section has no unchecked item

- **Location mirrors status, it never defines it.** The criteria read `status` and the checkboxes - never the folder path. Do not move a project just to tidy up
- **A full pass only produces a hint**: the checker prints `可归档:<project>` in its own `[提示]` block and never as a FAIL; doing the move stays a human decision
- **A missing section counts as "not satisfied"**: with no 「出口/验收」or「任务清单」section there is nothing to verify, so no hint is printed (a false hint costs more than a missed one)
- **The reverse is a hard error (A12)**: a project sitting under `40-归档/` (a folder holding `!项目说明.md`) must keep a line in the root `00-索引/00-索引.md`; an archived project that vanished from the index is a file nobody can find again. Keep the line - tick its `## 计划与进度` entry and set its `## 项目清单` status to `归档`

## 2. Five Core Rules

### 1. Flow rule (the PARA soul)

Information has a lifecycle; it must flow, **storing without moving is forbidden**:

- New material goes to `50-资源` first, **never straight into a project's `20-知识/`**
- To learn something systematically -> create a project folder in `10-项目` (goal + deadline + task list)
- Project folder naming = time-granularity first + `!` prefix for pinned daily items; granularity encodes difficulty: months for beginner topics, quarters for foundations/deployment, years for advanced internals. The exact learning order inside a group lives in the root `00-索引/00-索引.md` "learning route" section
- Distilled knowledge -> written into the owning project's `20-知识/`; a project meeting all four archive criteria moves wholesale into `40-归档`
- **Quarterly review**: anything in `50-资源` untouched for 3+ months gets either distilled into the owning project's `20-知识/` or deleted

### 2. Writing rule (lightweight Zettelkasten)

- One note, one topic (atomicity)
- **Rewrite in your own words** - copy-pasted material is collecting, not learning
- Code is fine, but must come with "why it is written this way" comments
- Notes interlink via `[[wiki-links]]` (clickable in Obsidian, harmless plain text in VS Code)

### 3. Retrieval rule (index pages)

- **Find things via index pages, not by digging into folders**
- Two levels: the root `00-索引/00-索引.md` lists every project (one global page); each project's `00-索引.md` lists that project's notes + recommended order + gaps to fill
- After writing a note, add its line to the owning project's `00-索引.md`; add a line to the root page whenever a project is created
- **Two link styles (dual track)**: `[[wikilinks]]` for cross-note references inside note bodies (clickable in Obsidian); relative-path links in index pages / README (clickable in VS Code and GitHub). Wikilinks must carry a path when the target filename is not unique, e.g. `[[2026-掌握西班牙语B2/!项目说明|项目说明]]`
- The stat line of an index page (`> 本项目知识 12 篇 · 状态 learning · 覆盖 12/12(100%)`) must sit inside the first 8 lines - that is where checker A9 reads it, and A9 verifies its counts and status against the real files
- The two containers (`!名词解释` / `!系统与工具`) are **not projects and are never archived**: the human-facing status reads **`常驻`** in both the root index and the container's own stat line. A container has no `!项目说明.md` (so A9 checks no status for it), while frontmatter `status` may only take one of the four machine values (A5) - hence a container index page keeps `done` in its frontmatter and never `常驻`

### 4. Metadata rule (frontmatter)

YAML frontmatter at the top of every note, **at most 8 fields**: `type` (algorithm | project | system | language | tutorial | log | note | concept), `tags`, `status` (todo | learning | done | review), `date`, `difficulty` (1-5, algorithm notes), `source`, `related` (`"[[note]]"`), optional `review` (next review date).

- The two non-obvious `type` values: `note` = in-project daily / list / index notes (e.g. Spanish daily notes, vocabulary lists); `concept` = concept comparison / explanation notes (e.g. CLI-TUI-GUI, editor-compiler-IDE, test fixtures)
- Project `status` rule (the basis of checker A7): a project folder holding any `.md` besides `!项目说明.md` and `00-索引.md` (including `!实施计划.md`) is `learning`; one holding only those two is `todo`
- Vault checker (A1-A14, exit code 0 = PASS): `cd 50-资源/工具/vault-check && PYTHONIOENCODING=utf-8 python -B check_vault.py`; `--json` for machine-readable output. The two hint channels (archive-ready projects, root index not yet created) print their own `[提示]` block and never count as FAIL. The legacy `--coverage` / `--moc-stats` switches were removed on 2026-09-25 together with the five legacy MOC files (the `00-索引/` directory name now holds the root index page): per-index coverage is the stats line at the top of each `00-索引.md`, kept in sync by A9
- **What belongs in the `!名词解释` container (Terminology)** (since 2026-09-23; moved 2026-09-25): cross-cutting, tooling and engineering **term/concept explainers** (e.g. "editor vs compiler vs IDE", "CLI/TUI/GUI", "Node.js/npm/pnpm", "test fixtures") live in `10-项目/!名词解释/20-知识/`; concepts that belong to one discipline stay in that discipline's own project `20-知识/`. How-to steps do not belong here - they go to the matching technical category
- **Teaching workspaces (teach, since 2026-09-24)**: every learning project under `10-项目/` is also a `teach` workspace. State lives in `MISSION.md` (why), `RESOURCES.md` (trusted sources) and `NOTES.md` (preferences); outputs live in `lessons/*.html` (one lesson per file), `reference/*.html` (cheat sheets), `learning-records/*.md` (created lazily) and `GLOSSARY.md` (only terms already mastered). These are **skill protocol files**, so their names stay English (an exception to the Chinese-directory-name rule) and they are exempt from A3 / A5-A6 / A7; checker **A11** guards their completeness instead. The shared stylesheet and quiz widget exist exactly once at `50-资源/工具/teach-assets/` (lessons reference them relatively)
- **Knowledge-type notes must live in a project/container `20-知识/`** (enforced by checker A10, since 2026-09-23; reversed 2026-09-25): a note whose `type` is `algorithm` / `language` / `system` / `concept` / `tutorial` belongs under `10-项目/<project or container>/20-知识/`; the project root only allows `project` (scaffolding), `note` (project-internal daily notes / lists) and `log` (records). If a document genuinely serves one project only, change its `type` to `note` or `log` instead of moving it

### 5. Layering rule (Karpathy style)

- This vault (0-Note) stores **finished text** only: md notes
- Binary material (Anki/xlsx/large images/scripts/docx/pdf) lives outside the repo in `0-Note-Data\` or in `50-资源\` subfolders (`图片\`, `工具\`, `英语\`). Note: `*.sh` / `*.docx` / `*.xlsx` / `*.pptx` / `*.pdf` are listed in `.gitignore`, so these files stay on this machine only and are **never committed**
- **`50-资源` as a whole is not committed** (since 2026-09-23): `.gitignore` ignores `50-资源/*` and whitelists only `工具/vault-check/` (the checker), `记录/`, `Zephyr/`, `工具/Markdown资料收集.md`. Images and language material stay local and never reach the remote or its history
- Knowledge is "compiled" once: raw material -> distill -> finished note inside the owning project's `20-知识/`; afterwards keep updating the output instead of re-reading raw material

## 3. How to Write a Note (four skeletons)

Copy the matching skeleton from `90-模板\` (currently one shared body template serves all four scenarios; the essential sections differ):

| Scenario | Skeleton | Essential sections |
|------|------|---------|
| An algorithm problem | `20-笔记正文模板.md` | problem -> intuition & trial -> core idea -> code -> complexity -> similar problems -> review log |
| An open-source / own project | `20-笔记正文模板.md` | what it solves -> architecture -> run it -> core mechanism -> **decisions & trade-offs** -> what I can reuse -> retrospective |
| A system / middleware | `20-笔记正文模板.md` | one-sentence essence -> what it solves -> core concepts -> architecture -> **trade-offs** -> bottlenecks -> interview angles |
| A language / technology | `20-笔记正文模板.md` | positioning -> environment cheatsheet -> core mental models -> syntax diff table -> pitfalls & best practices -> snippets |

> For how each layer's templates fit together and a full project lifecycle, see `90-模板/90-模板总览与生命周期.md`.

## 4. Naming Conventions

- Note files: `topic.md` (Chinese fine, short and searchable)
- Project folders: `{granularity}-{name}` (e.g. `2026-10-刷完Hot100/`); pinned standing items take a `!` prefix, e.g. `!一天一道算法题/`
- Index pages: the root one at `00-索引/00-索引.md` (inside a folder, see section 1), one per project/container (e.g. `10-项目/!一天一道算法题/00-索引.md`)
- Natural languages (English/Spanish) each live in their own learning project; notes about programming/markup languages stay in the project that produced them (there is no global language index any more)
- No date prefixes on knowledge notes (retrieval relies on the index page and tags, not time)

## 4.5 Notes vs. Logs

Two kinds of text live in this vault - decide before writing:

| Kind | Definition | Filename | Home | frontmatter type |
|---|---|---|---|---|
| **Note** | Distilled knowledge: principles / methods / trade-offs | `topic.md`, no date prefix | the owning project's `20-知识/` | `algorithm` / `system` / `language` / `tutorial` / `note` / `concept` |
| **Log** | Event record: what happened + how it was handled + what to watch | `记录-<event>.md` | `50-资源/记录/` | `log` |

- If an event yields a reusable method, distill that method into a note inside the owning project's `20-知识/` and link it from the log via `related`
- Logs live in the resource layer: subject to the quarterly cleanup (archive/delete after 3 months without reference), never occupying a project's `20-知识/`

## 5. AI Collaboration Rules (for AI assistants)

- The vault structure is described by this file; generate new notes from `90-模板` skeletons, with frontmatter
- When writing notes for me: distilled content goes into the owning project's `20-知识/`; raw material into `50-资源`
- Update the owning project's `00-索引.md` after every big change, and the root `00-索引/00-索引.md` whenever projects are added, renamed or archived
- Respect the flow rule: never dump raw material into a project's `20-知识/`
- Move a project into `40-归档/` only after all four archive criteria hold; never move it to "tidy up"

## 6. A Full Example: how one note flows through the system

Following the real note `10-项目/!一天一道算法题/20-知识/冒泡算法.md` (bubble sort):

1. **Stash (50-资源)** - you collect a C bubble-sort snippet, a solution PDF, an animation. Collecting is not learning; no organizing yet.
2. **Distill (the project's `20-知识/`)** - copy `90-模板/20-笔记正文模板.md`, rename to `10-项目/!一天一道算法题/20-知识/冒泡算法.md`, fill the skeleton in your own words with "why" comments, add frontmatter (<= 8 fields). Raw material from step 1 is then deleted or demoted.
3. **Index (the project's `00-索引.md`)** - add one line to `10-项目/!一天一道算法题/00-索引.md`: `- [冒泡算法](<20-知识/冒泡算法.md>) — ...`. Content lives in the project's `20-知识/`; the index holds a single line. Finding all sorting notes means opening one page.
4. **Project (10-项目)** - if this becomes systematic practice, create `10-项目/2026-10-刷完Hot100/` with goal, deadline, task list; cross-link via `related: [[..]]` so project and note hook into each other, then add the project's line to the root `00-索引/00-索引.md`.
5. **Archive (40-归档)** - once the project meets the four archive criteria the checker hints `可归档:<project>`; the whole folder then moves into `40-归档` (append-only) while keeping its line in the root `00-索引/00-索引.md`. A single note that only ever served one project is not moved alone - it is retyped as `note` / `log` instead.

```text
idea/material -> 50-资源 (staging) -----\
                                        +-> 10-项目/<项目>/20-知识 (finished notes) -> 40-归档 (sealed) <- move when done
templates 90-模板 <-copy- write body----+                  ^
                                        \-> 00-索引/00-索引.md (root) + <项目>/00-索引.md (project index pages)
```

`00` indexes, `10` charters, `20` hosts, `40` seals, `50` stages, `90` formats - the same knowledge advances `50 -> 20 -> 40` as it matures; `00` always points at it, `90` always teaches how to write it.
