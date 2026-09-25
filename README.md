# 0-Note · A Programmer's Knowledge Base Constitution

**English | [简体中文](./README.zh-CN.md)**

> A pure-Markdown, tool-agnostic, AI-friendly knowledge management system for programmers.
> It combines PARA (action-oriented categories) + Zettelkasten (atomic notes) + MOC (maps of content) + Johnny.Decimal (numbered locations) + Karpathy-style layering (raw vs. finished material).
> This file is the **single source of rules** for the system: both humans and AI follow it.

Note: note filenames inside this vault are Chinese; this English version is a courtesy translation, the Chinese file remains the authoritative text.

## 1. Directory System (numbers are priorities)

```text
0-Note\
├── 00-索引\   Index layer. One "map" per topic; the entry point for notes (links only, no content)
├── 10-项目\   Project layer. Goal-and-deadline learning; projects are self-contained - finished notes live in the project's own `20-知识\` (containers: `!名词解释\`, `!系统与工具\`)
├── 40-归档\   Archive layer. Finished projects, outdated knowledge (append-only)
├── 50-资源\   Resource layer. Collected material/tools/scripts/images, not yet distilled
├── 90-模板\   Template layer. Unified note skeletons (algorithm / project / system / language)
└── README.md  This file (the constitution)
```

Companion directory outside the repo (optional, **not created yet** - create it yourself if you want one):

- `F:\0-Note-Data\` - a suggested home for Anki decks, xlsx/csv, processing scripts and other raw material, mirroring the vault's subfolder names (e.g. `英语`). Nothing in this repo depends on it

### What 00~90 mean (numbers are both priority and knowledge lifecycle)

> The numeric prefixes carry two meanings: (1) smaller numbers sit closer to the repo core and move more often; (2) each layer is a lifecycle stage. **The same topic moves between layers as its lifecycle position changes.** Examples below are real files from this vault:

| Directory | Meaning | What goes in | Real example in this vault |
|------|------|--------|--------------------|
| **00-索引** | Index layer · one map per topic | Links and routes only; content lives in the project's `20-知识\` | A line in `00-索引/算法.md` like `- [[冒泡算法]] — ...` is the entry to a note |
| **10-项目** | Project layer · goal+deadline learning, self-contained | Project folder (goal, deadline, task list) + the project's `20-知识\` (**the finished notes themselves**, the only home for note bodies) | `10-项目/2026-12-掌握SQLite/` (with `!项目说明.md`) and its `20-知识/SQLite介绍.md` |
| **40-归档** | Archive layer · retired | Finished projects, outdated knowledge (append-only) | `40-归档/CSDN文章/`; a finished `10-项目/` folder moves here wholesale |
| **50-资源** | Resource layer · raw material staging | Unrefined material, images, script tools | `50-资源/图片/`, `50-资源/工具/`, `50-资源/英语/` |
| **90-模板** | Template layer · skeletons | Templates copied when writing new notes (never edited) | `90-模板/20-笔记正文模板.md` |

**One-line mnemonic**: `00 points the way -> 10 starts a project -> 50 stages raw material -> 20-知识 hosts the notes (inside the project) -> 40 seals the past -> 90 provides the format`.

**The numbers name layers, not steps**: knowledge flows raw -> project -> finished -> indexed -> sealed (see section 6), and `50-资源` carries a high number simply because it sits furthest from the core, not because it is low priority.

**This layer is not pushed to the remote**: images and language material stay on this machine (`.gitignore` ignores `50-资源/*` with a small whitelist); only the vault checker, event logs and MOC-referenced docs are committed. A fresh clone therefore has no `50-资源/图片/` or `50-资源/英语/`, and links into them only resolve locally.

## 2. Five Core Rules

### 1. Flow rule (the PARA soul)

Information has a lifecycle; it must flow, **storing without moving is forbidden**:

- New material goes to `50-资源` first, **never straight into Areas**
- To learn something systematically -> create a project folder in `10-项目` (goal + deadline + task list)
- Project folder naming = time-granularity first + `!` prefix for pinned daily items; granularity encodes difficulty: months for beginner topics, quarters for foundations/deployment, years for advanced internals. The exact learning order inside a group lives in the 00-索引 "learning route" index
- Distilled knowledge -> written into the project's own `20-知识/`; finished projects move wholesale into `40-归档`
- **Quarterly review**: anything in Resources untouched for 3+ months gets either distilled into Areas or deleted

### 2. Writing rule (lightweight Zettelkasten)

- One note, one topic (atomicity)
- **Rewrite in your own words** - copy-pasted material is collecting, not learning
- Code is fine, but must come with "why it is written this way" comments
- Notes interlink via `[[wiki-links]]` (clickable in Obsidian, harmless plain text in VS Code)

### 3. Retrieval rule (MOC)

- **Find things via MOC maps, not by digging into folders**
- One MOC per topic (e.g. `00-索引\算法.md`): lists all notes of the topic + recommended order + gaps to fill
- After writing a note, add its line to the matching MOC
- Two link styles: `[[wikilinks]]` for cross-note references inside notes (clickable in Obsidian); relative-path links in MOCs / indexes / README (clickable in VS Code and GitHub). Wikilinks must carry a path when the target filename is not unique, e.g. `[[2026-掌握西班牙语B2/!项目说明|项目说明]]`
- The MOC header stat line (e.g. `> 条目 49 · 覆盖 ...`) ends with **two trailing spaces** - that is a hard line break keeping the stat line apart from the intro blockquote below it. Keep them; do not let a formatter strip them

### 4. Metadata rule (frontmatter)

YAML frontmatter at the top of every note, **at most 8 fields**: `type` (algorithm | project | system | language | tutorial | log | note | concept), `tags`, `status` (todo | learning | done | review), `date`, `difficulty` (1-5, algorithm notes), `source`, `related` (`"[[note]]"`), optional `review` (next review date).

- The two non-obvious `type` values: `note` = in-project daily / list / index notes (e.g. Spanish daily notes, vocabulary lists); `concept` = concept comparison / explanation notes (e.g. CLI-TUI-GUI, editor-compiler-IDE, test fixtures)
- Project `status` rule (the basis of checker A7): a project folder holding any `.md` besides `!项目说明.md` (including `!实施计划.md`) is `learning`; one holding only `!项目说明.md` is `todo`
- Vault checker (A1-A11, exit code 0 = PASS): `cd 50-资源/工具/vault-check && PYTHONIOENCODING=utf-8 python -B check_vault.py`; `--coverage` for per-MOC coverage, `--moc-stats` for entry counts
- **What belongs in the `!名词解释` container (Terminology)** (since 2026-09-23; moved 2026-09-25): cross-cutting, tooling and engineering **term/concept explainers** (e.g. "editor vs compiler vs IDE", "CLI/TUI/GUI", "Node.js/npm/pnpm", "test fixtures") live in `10-项目/!名词解释/20-知识/`; concepts that belong to one discipline stay in that discipline's own project `20-知识/`. How-to steps do not belong here - they go to the matching technical category
- **Teaching workspaces (teach, since 2026-09-24)**: every learning project under `10-项目/` is also a `teach` workspace. State lives in `MISSION.md` (why), `RESOURCES.md` (trusted sources) and `NOTES.md` (preferences); outputs live in `lessons/*.html` (one lesson per file), `reference/*.html` (cheat sheets), `learning-records/*.md` (created lazily) and `GLOSSARY.md` (only terms already mastered). These are **skill protocol files**, so their names stay English (an exception to the Chinese-directory-name rule) and they are exempt from A3 / A5-A6 / A7; checker **A11** guards their completeness instead. The shared stylesheet and quiz widget exist exactly once at `50-资源/工具/teach-assets/` (lessons reference them relatively)
- **Knowledge-type notes must live in a project/container `20-知识/`** (enforced by checker A10, since 2026-09-23; reversed 2026-09-25): a note whose `type` is `algorithm` / `language` / `system` / `concept` / `tutorial` belongs under `10-项目/<project or container>/20-知识/`; the project root only allows `project` (scaffolding), `note` (project-internal daily notes / lists) and `log` (records). If a document genuinely serves one project only, change its `type` to `note` or `log` instead of moving it

### 5. Layering rule (Karpathy style)

- This vault (0-Note) stores **finished text** only: md notes
- Binary material (Anki/xlsx/large images/scripts/docx/pdf) lives outside the repo in `0-Note-Data\` or in `50-资源\` subfolders (`图片\`, `工具\`, `英语\`). Note: `*.sh` / `*.docx` / `*.xlsx` / `*.pptx` / `*.pdf` are listed in `.gitignore`, so these files stay on this machine only and are **never committed**
- **`50-资源` as a whole is not committed** (since 2026-09-23): `.gitignore` ignores `50-资源/*` and whitelists only `工具/vault-check/` (the checker), `记录/`, `Zephyr/`, `工具/Markdown资料收集.md`. Images and language material stay local and never reach the remote or its history
- Knowledge is "compiled" once: raw material -> distill -> finished note inside a project's `20-知识/`; afterwards keep updating the output instead of re-reading raw material

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
- MOC files: `topic.md` (e.g. `算法.md`, `系统.md`)
- Foreign languages split into two MOCs: human languages (English/Spanish) under `外语.md`; programming/markup languages under `编程语言.md`
- No date prefixes on knowledge notes (retrieval relies on MOC and tags, not time)

## 4.5 Notes vs. Logs

Two kinds of text live in this vault - decide before writing:

| Kind | Definition | Filename | Home | frontmatter type |
|---|---|---|---|---|
| **Note** | Distilled knowledge: principles / methods / trade-offs | `topic.md`, no date prefix | the owning project's `20-知识/` | `algorithm` / `system` / `language` / `tutorial` / `note` / `concept` |
| **Log** | Event record: what happened + how it was handled + what to watch | `记录-<event>.md` | `50-资源/记录/` | `log` |

- If an event yields a reusable method, distill that method into a note inside the owning project's `20-知识/` and link it from the log via `related`
- Logs live in the resource layer: subject to the quarterly cleanup (archive/delete after 3 months without reference), never occupying Areas

## 5. AI Collaboration Rules (for AI assistants)

- The vault structure is described by this file; generate new notes from `90-模板` skeletons, with frontmatter
- When writing notes for me: distilled content goes into the owning project's `20-知识/`; raw material into `50-资源`
- Update the relevant MOC link list after every big change
- Respect the flow rule: never dump raw material into Areas

## 6. A Full Example: how one note flows through the system

Following the real note `10-项目/!一天一道算法题/20-知识/冒泡算法.md` (bubble sort):

1. **Stash (50-资源)** - you collect a C bubble-sort snippet, a solution PDF, an animation. Collecting is not learning; no organizing yet.
2. **Distill (the project's `20-知识/`)** - copy `90-模板/20-笔记正文模板.md`, rename to `10-项目/!一天一道算法题/20-知识/冒泡算法.md`, fill the skeleton in your own words with "why" comments, add frontmatter (<= 8 fields). Raw material from step 1 is then deleted or demoted.
3. **Index (00-索引)** - add one line to `00-索引/算法.md`: `- [[冒泡算法]] — ...`. Content lives in the project's `20-知识/`; the index holds a single line. Finding all sorting notes means opening one map.
4. **Project (10-项目)** - if this becomes systematic practice, create `10-项目/2026-10-刷完Hot100/` with goal, deadline, task list; cross-link via `related: [[..]]` so project and index hook into each other.
5. **Archive (40-归档)** - when the project is done, the whole folder moves into `40-归档` (append-only). A single outdated note moves there too, and the index drops its link.

```text
idea/material -> 50-资源 (staging) --\
                                           +-> 10-项目/20-知识 (finished notes) -> 40-归档 (sealed)
templates 90-模板 <-copy- write body -+        ^                          |
                                           \-> 00-索引 (index entry)           <- move when done
```

`00` indexes, `10` charters, `20` hosts, `30` stages, `40` seals, `90` formats - the same knowledge advances 30 -> 20 -> 40 as it matures; `00` always points at it, `90` always teaches how to write it.
