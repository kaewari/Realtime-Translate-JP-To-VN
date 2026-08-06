<!-- date: 2026-08-06 -->
<!-- source: chat:phase-d-ux · user: lưu 2 plan UI/UX + prompt Gemini -->

# Plan D-UX — Interaction / usability (JP→VN Studio)

> Tách từ `plan/plan-2026-08-06-ui-ux-enhancements.md` + ROI bổ sung.  
> Sibling UI: [`plan/plan-2026-08-06-ui-visual.md`](plan-2026-08-06-ui-visual.md).  
> Visual thuần (cỡ chữ, 1-dòng, badge) → D-UI.

## Executor

| | |
|--|--|
| **Agent** | **Antigravity + Gemini 3.1 Pro High** (không Flash) |
| **Task branches** | Sprint 1: `ux-core/dev` · Sprint 2: `ux-pip/dev` → merge `antigravity/dev` |
| Verify | Cursor / Bugbot sau mỗi sprint |

## Sprint 1 — Ship trước

| ID | Mục | Status |
|----|-----|--------|
| UX1 | Chọn micro (`enumerateDevices` + settings) | [x] |
| UX2 | Export `.txt` / `.md` (`.srt` nếu có timestamp) | [x] |
| UX3 | Double-click/sửa JA → POST `/api/translate` cập nhật VI | [x] |
| UX4 | Phím Space toggle mic (không khi đang gõ input) | [x] |
| UX5 | WS reconnect rõ + disable mic khi offline | [x] |

## Sprint 2 — Ship sau

| ID | Mục | Status |
|----|-----|--------|
| UX6 | Document PiP — cửa sổ phụ đề VN | [ ] |
| UX7 | localStorage restore transcript sau F5 (không sidebar đa phiên) | [ ] |
| UX8 | TTS Web Speech — nút loa trên card **VI** | [ ] |
| UX9 | `manifest.json` + icon (không Service Worker offline ASR) | [ ] |

## Cắt

OBS · waveform · chat bubble · shimmer · VAD màu · glossary UI · cloud sync · onboarding tour.

## Phụ thuộc

- ASR model upgrade = plan riêng.  
- Utterance-end nên xanh trước UX6 PiP.

## Mốc

- [x] Sprint 1 đóng — ngày: 2026-08-06 · verified Cursor: 2026-08-06 (disk UX1–5; fix export `\\n`→newline; walkthrough dedupe; SHA `745d3d7` + verify patch)
- [ ] Sprint 2 đóng — ngày: ____  
- [ ] Plan D-UX đóng — verified: ____

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

## Appendix — Prompt Gemini (D-UX Sprint 2)

```text
Bạn là lazy senior (ponytail) trên Antigravity với Gemini 3.1 Pro High. Làm Plan D-UX Sprint 2.

Đọc: AGENTS.md; plan/plan-2026-08-06-ux-interaction.md; web/index.html.
GATE: Sprint 1 đã tick. Branch: ux-pip/dev → antigravity/dev.

LÀM hẹp:
UX6: Document Picture-in-Picture — cửa sổ nhỏ hiện dòng VI mới nhất (fallback: bỏ qua nếu browser không hỗ trợ, ghi note).
UX7: localStorage lưu/restore transcript session (một key; không sidebar đa phiên).
UX8: nút loa trên card VI → speechSynthesis tiếng Việt.
UX9: manifest.json + icon cơ bản; KHÔNG service worker cache ASR.

Không OBS/waveform. Commit+push ux-pip/dev; merge antigravity/dev; xóa task branch. Tick Sprint 2 trên plan.
```
