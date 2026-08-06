<!-- date: 2026-08-06 -->
<!-- source: chat:phase-d-ui · user: lưu 2 plan UI/UX + prompt Gemini -->
<!-- updated: 2026-08-06 — restored onto antigravity/dev @ d9e9b9f (was lost; via restore-d-ui) -->

# Plan D-UI — Visual / layout (JP→VN Studio)

> Tách từ `plan/plan-2026-08-06-ui-ux-enhancements.md` (đề xuất Pro Max — tham khảo; sprint theo file này).  
> Sibling UX: [`plan-2026-08-06-ux-interaction.md`](plan-2026-08-06-ux-interaction.md).  
> **Restore:** [`plan-2026-08-06-restore-d-ui.md`](plan-2026-08-06-restore-d-ui.md) — **đóng** trên `antigravity/dev` @ `d9e9b9f`.

## Executor

| | |
|--|--|
| **Agent** | **Antigravity + Gemini 3.1 Pro High** (không Flash) |
| **Task branch** | `ui-visual/dev` → merge `antigravity/dev` (AGENTS §1a) |
| **Skill** | Đọc `skills/frontend-design/SKILL.md` nếu có; tránh AI-slop. Ponytail thắng. |
| Verify | Cursor / Bugbot sau restore |

## Giữ / làm

| ID | Mục | Status |
|----|-----|--------|
| UI1 | Cỡ chữ VN (S/M/L) — CSS var `--vi-font-size` trên `.card-text.vi` | [x] restore `c0bb784` |
| UI2 | Chế độ 1 dòng VI (`body.one-line-mode`, ẩn cột JA) | [x] restore `c0bb784` |
| UI3 | Badge đỏ `fallback`/`mock` ASR **hoặc** MT `FallbackDict` / WS offline | [x] restore `c0bb784` + fix MT check |
| UI4 | Newest-on-top — `jaList.prepend` / `viList.prepend` | [x] Đã sử dụng prepend đúng yêu cầu |

File chính: [`web/index.html`](../web/index.html).

## Cắt

Waveform · chat bubble · shimmer/flash · VAD màu meter · OBS chroma · theme store.

## Out of scope

Mic, export, edit, hotkeys, PiP, TTS, PWA, localStorage → D-UX.

## Mốc

- [x] D-UI trên `antigravity/dev` — ngày: 2026-08-06 · verified Cursor: 2026-08-06  
  (SHA `885c2bc` UI1–3 + `d9e9b9f` UI4 prepend / is_final / MT badge — restore plan đóng)

---

## Appendix — Prompt Gemini

Dùng prompt đầy đủ trong [`plan-2026-08-06-restore-d-ui.md`](plan-2026-08-06-restore-d-ui.md) (Appendix — cherry-pick + UI4 prepend + `is_final`).
