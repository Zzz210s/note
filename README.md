# 0-Note · A Programmer's Knowledge Base Constitution

**English | [简体中文](./README.zh-CN.md)**

> A pure-Markdown, tool-agnostic, AI-friendly knowledge management system for programmers.
> It combines PARA (action-oriented categories) + Zettelkasten (atomic notes) + MOC (maps of content) + Johnny.Decimal (numbered locations) + Karpathy-style layering (raw vs. finished material).
> This file is the **single source of rules** for the system: both humans and AI follow it.

Note: note filenames inside this vault are Chinese; this English version is a courtesy translation, the Chinese file remains the authoritative text.

## 1. Directory System (numbers are priorities)

```
0-Note\
├── 00-MOC\         Index layer. One "map" per topic; the entry point for notes (links only, no content)
├── 10-Projects\    Project layer. Goal-and-deadline learning (e.g. "finish Hot100 in 14 days")
├── 20-Areas\       Area layer. Long-term maintained knowledge fields (01-Algorithms / 02-Languages / 03-DevTools / 04-Systems / 05-Networking / 06-Web / 07-ForeignLanguages)
├── 30-Resources\   Resource layer. Collected material/tools/scripts/images, not yet distilled
├── 40-Archive\     Archive layer. Finished projects, outdated knowledge (append-only)
├── 90-Templates\   Template layer. Unified note skeletons (algorithm / project / system / language)
└── README.md       This file (the constitution)
```

Companion directory outside the repo (binary material, not in git):
- `F:\0-Note-Data\` - Anki decks, xlsx/csv, processing scripts and other raw material, mirroring subfolder names such as English / Español

### What 00~90 mean (numbers are both priority and knowledge lifecycle)

> The numeric prefixes carry two meanings: (1) smaller numbers sit closer to the repo core and move more often; (2) each layer is a lifecycle stage. **The same topic moves between layers as its lifecycle position changes.** Examples below are real files from this vault:

| Directory | Meaning | What goes in | Real example in this vault |
|------|------|--------|--------------------|
| **00-MOC** | Index layer · one map per topic | Links and routes only; content lives in 20-Areas | A line in `00-MOC/算法.md` like `- [[冒泡算法]] — ...` is the entry to a note |
| **10-Projects** | Project layer · goal+deadline learning | Project folders (goal, deadline, task list) | Currently empty; planned e.g. `10-Projects/Hot100-2026Q4\` |
| **20-Areas** | Area layer · long-term fields | **The finished notes themselves** (the only home for note bodies) | `20-Areas/01-算法/冒泡算法.md` (a full note) |
| **30-Resources** | Resource layer · raw material staging | Unrefined material, images, script tools | `30-Resources/image/`, `30-Resources/tools/` |
| **40-Archive** | Archive layer · retired | Finished projects, outdated knowledge (append-only) | Currently empty; e.g. a finished `10-Projects\` folder moves here wholesale |
| **90-Templates** | Template layer · skeletons | Templates copied when writing new notes (never edited) | `90-Templates/20-笔记正文模板.md` |

**One-line mnemonic**: `00 points the way -> 10 starts a project -> 20 hosts the notes -> 30 stages raw material -> 40 seals the past -> 90 provides the format`.

**Why is 30 after 20?** 30-Resources is "not yet distilled material", 20-Areas is "distilled output" - material flows from the edge (30) toward the core (20), matching the PARA direction.

## 2. Five Core Rules

### 1. Flow rule (the PARA soul)
Information has a lifecycle; it must flow, **storing without moving is forbidden**:

- New material goes to `30-Resources` first, **never straight into Areas**
- To learn something systematically -> create a project folder in `10-Projects` (goal + deadline + task list)
- Project folder naming = time-granularity first + `!` prefix for pinned daily items; granularity encodes difficulty: months for beginner topics, quarters for foundations/deployment, years for advanced internals. The exact learning order inside a group lives in the 00-MOC "learning route" index
- Distilled knowledge -> written into `20-Areas`; finished projects move wholesale into `40-Archive`
- **Quarterly review**: anything in Resources untouched for 3+ months gets either distilled into Areas or deleted

### 2. Writing rule (lightweight Zettelkasten)
- One note, one topic (atomicity)
- **Rewrite in your own words** - copy-pasted material is collecting, not learning
- Code is fine, but must come with "why it is written this way" comments
- Notes interlink via `[[wiki-links]]` (clickable in Obsidian, harmless plain text in VS Code)

### 3. Retrieval rule (MOC)
- **Find things via MOC maps, not by digging into folders**
- One MOC per topic (e.g. `00-MOC\算法.md`): lists all notes of the topic + recommended order + gaps to fill
- After writing a note, add its line to the matching MOC

### 4. Metadata rule (frontmatter)
YAML frontmatter at the top of every note, **at most 8 fields**: `type` (algorithm | project | system | language | tutorial), `tags`, `status` (todo | learning | done | review), `date`, `difficulty` (1-5, algorithm notes), `source`, `related` (`"[[note]]"`), optional `review` (next review date).

### 5. Layering rule (Karpathy style)
- This vault (0-Note) stores **finished text** only: md notes
- Binary material (Anki/xlsx/large images/scripts/docx/pdf) lives outside the repo in `0-Note-Data\` or in `30-Resources\` subfolders (`image\`, `tools\`, `English\` / `Español\`)
- Knowledge is "compiled" once: raw material -> distill -> finished Areas note; afterwards keep updating the output instead of re-reading raw material

## 3. How to Write a Note (four skeletons)

Copy the matching skeleton from `90-Templates\` (currently one shared body template serves all four scenarios; the essential sections differ):

| Scenario | Skeleton | Essential sections |
|------|------|---------|
| An algorithm problem | `20-笔记正文模板.md` | problem -> intuition & trial -> core idea -> code -> complexity -> similar problems -> review log |
| An open-source / own project | `20-笔记正文模板.md` | what it solves -> architecture -> run it -> core mechanism -> **decisions & trade-offs** -> what I can reuse -> retrospective |
| A system / middleware | `20-笔记正文模板.md` | one-sentence essence -> what it solves -> core concepts -> architecture -> **trade-offs** -> bottlenecks -> interview angles |
| A language / technology | `20-笔记正文模板.md` | positioning -> environment cheatsheet -> core mental models -> syntax diff table -> pitfalls & best practices -> snippets |

> For how each layer's templates fit together and a full project lifecycle, see `90-Templates/90-模板总览与生命周期.md`.

## 4. Naming Conventions

- Note files: `topic.md` (Chinese fine, short and searchable)
- Project folders: `goal-deadline` (e.g. `Hot100-2026Q4\`)
- MOC files: `topic.md` (e.g. `算法.md`, `系统.md`)
- Foreign languages split into two MOCs: human languages (English/Spanish) under `外语.md`; programming/markup languages under `编程语言.md`
- No date prefixes on knowledge notes (retrieval relies on MOC and tags, not time)

## 4.5 Notes vs. Logs

Two kinds of text live in this vault - decide before writing:

| Kind | Definition | Filename | Home | frontmatter type |
|---|---|---|---|---|
| **Note** | Distilled knowledge: principles / methods / trade-offs | `topic.md`, no date prefix | matching `20-Areas` category | `algorithm` / `system` / `language` / `tutorial` |
| **Log** | Event record: what happened + how it was handled + what to watch | `记录-<event>.md` | `30-Resources/logs/` | `log` |

- If an event yields a reusable method, distill that method into a 20-Areas note and link it from the log via `related`
- Logs live in the resource layer: subject to the quarterly cleanup (archive/delete after 3 months without reference), never occupying Areas

## 5. AI Collaboration Rules (for AI assistants)

- The vault structure is described by this file; generate new notes from `90-Templates` skeletons, with frontmatter
- When writing notes for me: distilled content goes into the matching `20-Areas` category; raw material into `30-Resources`
- Update the relevant MOC link list after every big change
- Respect the flow rule: never dump raw material into Areas

## 6. A Full Example: how one note flows through the system

Following the real note `20-Areas/01-算法/冒泡算法.md` (bubble sort):

1. **Stash (30-Resources)** - you collect a C bubble-sort snippet, a solution PDF, an animation. Collecting is not learning; no organizing yet.
2. **Distill (20-Areas)** - copy `90-Templates/20-笔记正文模板.md`, rename to `20-Areas/01-算法/冒泡算法.md`, fill the skeleton in your own words with "why" comments, add frontmatter (<= 8 fields). Raw material from step 1 is then deleted or demoted.
3. **Index (00-MOC)** - add one line to `00-MOC/算法.md`: `- [[冒泡算法]] — ...`. Content lives in 20-Areas; the MOC holds a single line. Finding all sorting notes means opening one map.
4. **Project (10-Projects)** - if this becomes systematic practice, create `10-Projects/2026-10-刷完Hot100/` with goal, deadline, task list; cross-link via `related: [[..]]` so project and area layers hook into each other.
5. **Archive (40-Archive)** - when the project is done, the whole folder moves into `40-Archive` (append-only). A single outdated note moves there too, and the MOC drops its link.

```
idea/material -> 30-Resources (staging) --\
                                           +-> 20-Areas (finished notes) -> 40-Archive (sealed)
templates 90-Templates <-copy- write body -+        ^                          |
                                           \-> 00-MOC (index entry)           <- move when done
```

`00` indexes, `10` charters, `20` hosts, `30` stages, `40` seals, `90` formats - the same knowledge advances 30 -> 20 -> 40 as it matures; `00` always points at it, `90` always teaches how to write it.
