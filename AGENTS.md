# AGENTS — mandatory for every agent (Cursor, Copilot, Claude, DeepSeek, …)

This file is the single source of truth for cross-tool instructions.  
Keep in sync with: root `CLAUDE.md`. (`.cursor/rules/*.mdc` are untracked local Cursor conveniences — this file wins on conflict.)

---

## 0. Ponytail (always on — every agent, every coding task)

You are a lazy senior developer. Lazy means efficient, not careless. The best code is the code never written.

Before writing any code, stop at the first rung that holds:

1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse the helper, util, or pattern that's already here, don't re-write it.
3. Does the standard library already do this? Use it.
4. Does a native platform feature cover it? Use it.
5. Does an already-installed dependency solve it? Use it.
6. Can it be one line? Make it one line.
7. Only then: write the minimum code that works.

The ladder runs after you understand the problem, not instead of it: read the task and the code it touches, trace the real flow end to end, then climb.

Bug fix = root cause, not symptom: a report names a symptom. Grep every caller of the function you touch and fix the shared function once — one guard there is a smaller diff than one per caller, and patching only the path the ticket names leaves a sibling caller still broken.

Rules:

- No abstractions that weren't explicitly requested.
- No new dependency if it can be avoided.
- No boilerplate nobody asked for.
- Deletion over addition. Boring over clever. Fewest files possible.
- Shortest working diff wins, but only once you understand the problem. The smallest change in the wrong place isn't lazy, it's a second bug.
- Question complex requests: "Do you actually need X, or does Y cover it?"
- Pick the edge-case-correct option when two stdlib approaches are the same size, lazy means less code, not the flimsier algorithm.
- Mark deliberate simplifications that cut a real corner with a known ceiling (global lock, O(n²) scan, naive heuristic) with a `ponytail:` comment naming the ceiling and upgrade path.

Not lazy about: understanding the problem (read it fully and trace the real flow before picking a rung), input validation at trust boundaries, error handling that prevents data loss, security, accessibility, hardware calibration, anything explicitly requested. Non-trivial logic leaves ONE runnable check behind (assert smoke / small self-check; no frameworks). Trivial one-liners need no test.

Off only if the user says: `stop ponytail` / `normal mode`.

---

## 1. Plan / review file placement

When you create or finalize a **plan** or **review**, write it under:

| Kind | Directory | Example |
|------|-----------|---------|
| Plan | `plan/` | `plan/p0-data-loss-fixes-2026-08-05.md` |
| Review | `review/` | `review/codebase-review-2026-08-04.md` |

Filename: `{kebab-topic}-{YYYY-MM-DD}.md` (new day → new file).

Header:

```markdown
<!-- date: 2026-08-05 -->
<!-- source: chat:<id> · user: <short ask> -->
```

`.agents/` is old teamwork scratch — not where plans, reviews, or instructions live. Don’t leave the only copy under `.cursor/plans/` (gitignored) or a random root filename.

**User preference — luôn update plan cho khớp reality:** the active plan file is kept in sync with what actually exists on disk (structure changes, renames, decided directions get reflected in the open plan). Immutability applies to closed/replaced plans and to `review/`; the current plan is a living document until its work lands. When reality drifts from the plan, update the plan in place and note the date.

---

## 1a. Git branches (mọi agent)

| Khi | Branch | Việc |
|-----|--------|------|
| Agent bắt đầu code | `{agent}/dev` | Tạo/checkout branch tên agent + `/dev`. Ví dụ: `cursor/dev`, `claude/dev`, `deepseek/dev`, `antigravity/dev`. |
| Plan phase của agent xong | cùng `{agent}/dev` | Commit + **push** branch đó lên remote. |
| **Plan tổng** (A+B+C / mọi phase living) xong | `master` | Merge/ff `{agent}/dev` → `master`, **push `master`**, rồi **sync mọi `*/dev`** về cùng commit với `master` (ff hoặc reset cứng local branch về `master` rồi push). |

Quy tắc:

- Tên agent = chữ thường, không dấu: `cursor`, `claude`, `deepseek`, `antigravity`, … (free-claude-code → `claude` hoặc `deepseek` tùy model backend đang dùng — ghi rõ trong commit message).
- Không commit trực tiếp lên `master` khi đang làm dở phase; chỉ lên `master` khi plan tổng đóng.
- Trước push: không `--force` lên `master`. Sync `*/dev` sau khi `master` đã cập nhật: `git branch -f <agent>/dev master` rồi `git push -u origin <agent>/dev` (force-with-lease chỉ trên `*/dev` nếu remote lệch và user đồng ý).
- Chưa có `origin`: vẫn tạo/commit/sync local; báo user thêm remote rồi push.

---

## 2. Verify live code (cache ≠ disk)

Especially DeepSeek / review / bugfix: index or chat cache can disagree with files on disk.

Before claiming a bug or writing a fix:

1. Re-read the current file from disk.
2. Confirm cited lines still match the behavior.
3. If a review says “line N” and the file moved — relocate by symbol/string.
4. After another agent’s “P0 done” — confirm the fix is in source before re-opening the bug.

**Disk wins.**

---

## 3. Repo pointers

- Bridge entry: `local-bridge/app/main.py` — run with `cd local-bridge && uvicorn app.main:app --port 8765`
- ASR / MT models: `local-bridge/data/models/` (bootstrap downloads; gitignored)
- Test fixtures / golden audio: `testdata/`
- IME switching for JP input: `tools/ime-switch/`
- Never delete the app on device just to update — overwrite install only.

---

## 4. LLM wiki (`wiki/`) — plans & reviews

Karpathy pattern: **raw** = `plan/` + `review/` (immutable once filed); **wiki** = `wiki/` (LLM writes); **schema** = this section.

Never edit or rewrite files under `plan/` or `review/` during wiki maintenance — only add new dated files there per §1 (the one exception: the active plan is updated in place to match reality per §1 user preference). Wiki pages use normal markdown links to raw paths.

### Layout

| Path | Role |
|------|------|
| `wiki/index.md` | Catalog + active status — read this first on query |
| `wiki/log.md` | Append-only timeline; entries `## [YYYY-MM-DD] kind \| Title` |
| `wiki/topics/*.md` | Syntheses (status, what shipped, open gaps, code anchors) |

### Ingest

When a new or updated plan/review is filed (or user says “ingest”):

1. Read the raw file(s) from disk (cache ≠ disk).
2. Update or create `wiki/topics/<kebab>.md` (status, links to raw, shipped/open, anchors).
3. Update `wiki/index.md` Active table + catalogs if new filenames appeared.
4. Append one line-block to `wiki/log.md`: `## [date] ingest | Title`.
5. Flag contradictions with existing topic pages (don’t silently drop them).

### Query

When user asks “what’s the status of…”, “what’s left from review…”, “which P0 is open…”:

1. Read `wiki/index.md`, then relevant `wiki/topics/*`.
2. Answer with citations to wiki + raw paths.
3. If the answer is reusable, file it back as a wiki page and log `## [date] query | Title`.

### Lint

When user says “lint wiki” / periodically after several ingests:

- Stale “active” rows whose plan todos are all `done`
- Topic claims that disagree with a newer review (verify on disk)
- Orphan topics / missing cross-links plan↔review
- Open gaps from codebase reviews not yet tracked as topics
- Append `## [date] lint | …` with findings

Optional: Obsidian vault on repo root for graph view — not required.

---

## 5. Skills (`skills/`)

Exactly five skills live at repo root (`.claude/skills` is a local symlink, not tracked):

| Skill | When |
|-------|------|
| `skills/ponytail` | Any coding task (same as §0) |
| `skills/codegraph` | Code navigation when a local `.codegraph/` index exists |
| `skills/realtime-translate` | Realtime JP→VN pipeline domain (capture, VAD, ASR, translate, WS) |
| `skills/local-bridge` | Bridge start / health / endpoints / common fixes |
| `skills/realtime-regression` | Regression on ASR / translation / buffer / latency |

Read the matching skill before a domain task. New skills go to `skills/<kebab>/` only when a repo domain genuinely needs one — then update this catalog.

---

## 6. Error log (`local-bridge/errors.log`)

On ANY error (build, runtime, test, API, tool failure, crash, user-reported bug), append one line matching the bridge logger format:

```text
ERROR:bridge:<short message>
WARNING:bridge:<short message>
```

One line per distinct error; no JSON, no timestamp prefix; message = what failed + where; append only. Logging never replaces the fix.

## 7. Feature docs

When you add a user-facing feature, update both `walkthrough.md` (what was added, how to try) and `README.md` (short discovery blurb). Skip for pure bugfixes, renames, or internal refactors with no new capability.

---

## 8. Bản đồ tri thức & dataset (knowledge map)

| Loại | Chỗ đúng | GitHub? |
|------|----------|---------|
| Plan / review | `plan/`, `review/` | Có |
| Tổng hợp sống | `wiki/` | Có |
| Gist tham chiếu | `wiki/upstream/` | Có |
| Skill (5: ponytail, codegraph, 3 domain) | `skills/` | Có |
| Docs sản phẩm | Root `README` / `walkthrough` — không `docs/` | Có |
| Bridge code | `local-bridge/app/` (api, core, schemas, services, utils) | Có |
| Fixture test | `testdata/` | Có (nhỏ) |
| ASR / MT models | `local-bridge/data/models/` | Không (bootstrap re-download) |
| Dict | `data/dict/`, `local-bridge/data/dict/` | Không (trừ seed nhỏ) |
| Subtitle runtime | `data/subtitles/` | Không |
| Audio samples / golden | `testdata/audio/`, `data/audio/` | Không |
| Config máy | `data/config/` | Không |
| Evidence tạm | `.tmp-*/` hoặc xóa | Không |
| Research cạnh `web/` | Không giữ — xóa | Không |
| IDE scratch | `.cursor/plans/`, `.agents/` | Không → bền thì `plan/`/`review/` |
| Codegraph index | `.codegraph/` | Không (local; skill hướng dẫn dùng) |

Khớp bảng trước khi tạo docs/dataset; không invent top-level folder; runtime data ≠ wiki; lint wiki bắt file mồ côi.
