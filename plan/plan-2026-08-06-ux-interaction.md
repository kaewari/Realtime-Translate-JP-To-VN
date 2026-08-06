<!-- date: 2026-08-06 -->
<!-- source: chat:phase-d-ux · user: lưu 2 plan UI/UX + prompt Gemini -->
<!-- updated: 2026-08-06 — Sprint 2 verified Cursor @ 0593932; plan D-UX closed -->

# Plan D-UX — Interaction / usability (JP→VN Studio)

> Tách từ `plan/plan-2026-08-06-ui-ux-enhancements.md` + ROI bổ sung.  
> Sibling UI: [`plan/plan-2026-08-06-ui-visual.md`](plan-2026-08-06-ui-visual.md) · restore: [`plan/plan-2026-08-06-restore-d-ui.md`](plan-2026-08-06-restore-d-ui.md) (**code done** @ `d9e9b9f`).  
> Visual thuần (cỡ chữ, 1-dòng, badge) → D-UI — **không làm lại trong Sprint 2**.

## Executor

| | |
|--|--|
| **Agent** | **Antigravity + Gemini 3.1 Pro High** (không Flash) |
| **Task branches** | Sprint 1: `ux-core/dev` ✅ · Sprint 2: `ux-pip/dev` → merge `antigravity/dev` ✅ |
| Verify | Cursor / Bugbot sau mỗi sprint |

## Sprint 1 — Ship trước (DONE)

| ID | Mục | Status |
|----|-----|--------|
| UX1 | Chọn micro (`enumerateDevices` + settings) | [x] |
| UX2 | Export `.txt` / `.md` (`.srt` nếu có timestamp) | [x] |
| UX3 | Double-click/sửa JA → POST `/api/translate` cập nhật VI | [x] |
| UX4 | Phím Space toggle mic (không khi đang gõ input) | [x] |
| UX5 | WS reconnect rõ + disable mic khi offline | [x] |

**GATE:** Giữ nguyên UX1–5 trên disk. Không rewrite Sprint 1.

## Sprint 2 — Ship sau (DONE)

| ID | Mục | Status |
|----|-----|--------|
| UX6 | Document PiP — cửa sổ phụ đề VN | [x] |
| UX7 | localStorage restore transcript sau F5 (không sidebar đa phiên) | [x] |
| UX8 | TTS Web Speech — nút loa trên card **VI** | [x] |
| UX9 | `manifest.json` + icon (không Service Worker offline ASR) | [x] |

### Disk baseline (verified Cursor 2026-08-06)

- Branch: `antigravity/dev` @ `0593932` (`059393246a763d331049189879b8c32ae269e3c2`) — commit: *D-UX Sprint 2: PiP, localStorage, TTS, manifest*.
- Evidence:
  - **UX6:** `documentPictureInPicture` + `#btnPip` + `pipContainer` cập nhật VI mới nhất.
  - **UX7:** `localStorage` keys `rt_ja` / `rt_vi` / `rt_count` — save/restore + clear.
  - **UX8:** `.speak-btn` → `speechSynthesis` `lang=vi-VN` (+ `cancel()` trước speak).
  - **UX9:** `web/manifest.json` + `web/icon.svg` + `<link rel="manifest">`; **không** Service Worker.

### Checklist Sprint 2

- [x] Checkout/create `ux-pip/dev` từ `antigravity/dev` (đã có S1 + D-UI).
- [x] UX6: Document Picture-in-Picture — cửa sổ nhỏ hiện dòng VI mới nhất; fallback note nếu browser không hỗ trợ.
- [x] UX7: `localStorage` — lưu/restore transcript session sau F5; không sidebar đa phiên.
- [x] UX8: nút loa trên card VI → `speechSynthesis` `lang=vi-VN` (hoặc `vi`).
- [x] UX9: `web/manifest.json` + icon cơ bản + link từ `index.html`; **không** Service Worker cache ASR.
- [x] `walkthrough.md` + `README.md` ngắn (AGENTS §7).
- [x] Tick UX6–9 + mốc Sprint 2; wiki ngắn.
- [x] Commit + push `ux-pip/dev`; merge `antigravity/dev`; xóa task branch. Không `master`.

## Cắt

OBS · waveform · chat bubble · shimmer · VAD màu · glossary UI · cloud sync · onboarding tour · Service Worker offline ASR · redo D-UI / UX1–5.

## Phụ thuộc

- ASR model upgrade = plan riêng.  
- Utterance-end + D-UI restore đã xong trên `antigravity/dev` — Sprint 2 bắt từ HEAD đó.

## Mốc

- [x] Sprint 1 đóng — ngày: 2026-08-06 · verified Cursor: 2026-08-06 (disk UX1–5; fix export `\\n`→newline; walkthrough dedupe; SHA `745d3d7` + verify patch)
- [x] Sprint 2 đóng — ngày: 2026-08-06 · verified Cursor: 2026-08-06 (disk UX6–9; TTS `cancel()`; walkthrough/README/wiki; SHA `0593932`)
- [x] Plan D-UX đóng — verified Cursor: 2026-08-06 @ `0593932`

---

## Appendix — Prompt Gemini (D-UX Sprint 1)

```text
Bạn là lazy senior (ponytail) trên Antigravity với Gemini 3.1 Pro High. Làm Plan D-UX Sprint 1 cho Realtime Translate JP To VN.

Đọc: AGENTS.md (§0, §1a, §2, §7 nếu UI feature mới); plan/plan-2026-08-06-ux-interaction.md; web/index.html; local-bridge /api/translate.

GATE: Chỉ Sprint 1 (UX1–UX5). Không PiP/TTS/PWA/localStorage (Sprint 2). Không D-UI visual (cỡ chữ/1-dòng — plan ui-visual). Không OBS/waveform/bubble.

Branch: checkout/create ux-core/dev. Agent = antigravity.

LÀM:
UX1: enumerateDevices audioinput + UI chọn mic; getUserMedia dùng deviceId đã chọn.
UX2: nút Export — tải .txt và/hoặc .md từ transcript JA+VI hiện có (timestamp nếu đã có trên card).
UX3: sửa JA trên card (dblclick hoặc edit) → fetch POST /api/translate → cập nhật VI cùng card.
UX4: phím Space toggle start/stop mic; bỏ qua khi focus input/textarea.
UX5: khi WS đóng/mất — status rõ + không cho thu âm / dừng recording; reconnect như hiện có nhưng UX rõ hơn.

Ponytail: ít file; chủ yếu web/index.html. Update walkthrough.md + README ngắn nếu feature user-facing (AGENTS §7).

SAU: tick UX1–UX5; wiki ngắn; commit+push ux-core/dev; merge antigravity/dev; xóa ux-core/dev. Không master.
Trả về: file đổi + cách thử từng UX1–5.
```

## Appendix — Prompt Gemini (D-UX Sprint 2) — copy nguyên khối

```text
Bạn là lazy senior (ponytail) trên Antigravity với Gemini 3.1 Pro High (không Flash).

TASK: Plan D-UX Sprint 2 (UX6–UX9) cho Realtime Translate JP To VN.

ĐỌC BẮT BUỘC:
1. AGENTS.md (§0 ponytail, §1a branches, §2 disk wins, §6 errors.log, §7 feature docs).
2. Living plan: plan/plan-2026-08-06-ux-interaction.md — chỉ Sprint 2 ACTIVE.
3. Sibling (ĐỌC, không làm): plan/plan-2026-08-06-ui-visual.md · plan/plan-2026-08-06-restore-d-ui.md (D-UI đã trên antigravity/dev @ d9e9b9f).
4. web/index.html (HEAD đã có UX1–5 + UI1–4 prepend + fontSizeVi/oneLineMode — GIỮ NGUYÊN).

BRANCH (trước khi sửa):
- checkout/create ux-pip/dev từ antigravity/dev (đã có D-UX S1 + D-UI).
- Agent name = antigravity.

BASELINE DISK (đừng phá):
- Sprint 1: micSelect, Export, dblclick edit JA → /api/translate, Space toggle, WS offline disable mic.
- D-UI: #fontSizeVi, #oneLineMode, prepend (không đổi lại appendChild), badge MOCK/offline.
- endpoints.py is_final=True trên silence emit — không đụng bridge trừ khi bắt buộc (không cần cho Sprint 2).

LÀM (thứ tự, hẹp):
1) UX6 Document Picture-in-Picture:
   - Khi có dòng VI mới (final), cập nhật cửa sổ PiP nhỏ hiện text VI mới nhất.
   - Dùng documentPictureInPicture nếu có; nếu browser không hỗ trợ → nút disabled + note ngắn (không polyfill nặng).
2) UX7 localStorage:
   - Một key (vd. jpvn-transcript-v1) lưu danh sách card JA+VI hiện có.
   - Restore sau F5 vào đúng list (giữ newest-on-top / prepend semantics).
   - Không sidebar đa phiên / không cloud sync.
3) UX8 TTS:
   - Nút loa trên card VI → speechSynthesis speak text VI, lang vi-VN (fallback vi).
   - Stop/cancel utterance trước khi speak mới nếu đang nói.
4) UX9 PWA lite:
   - web/manifest.json + icon cơ bản; <link rel="manifest"> trong index.html.
   - KHÔNG Service Worker; KHÔNG cache offline ASR/models.

Ponytail: ít file (chủ yếu web/index.html + manifest/icon). Không abstraction mới. Update walkthrough.md + README ngắn (AGENTS §7).

GATE / CẤM:
- Không redo UX1–5.
- Không D-UI restore / không đổi cỡ chữ / 1-dòng / badge / prepend→append.
- Không OBS / waveform / bubble / shimmer / VAD màu / glossary UI / onboarding.
- Không push master. Không --force master.

SAU KHI XONG:
1. Tick UX6–UX9 + checklist Sprint 2 + mốc trong plan/plan-2026-08-06-ux-interaction.md.
2. Wiki ngắn: wiki/index.md + wiki/log.md + wiki/topics/realtime-translate.md.
3. Commit + push origin ux-pip/dev.
4. Merge vào antigravity/dev, push antigravity/dev, xóa ux-pip/dev (local+remote).
5. Trả về: file đổi, cách thử UX6–9, SHA branch.

Không tự verified — user chạy Cursor/Bugbot.
```
