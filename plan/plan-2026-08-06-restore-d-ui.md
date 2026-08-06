<!-- date: 2026-08-06 -->
<!-- source: chat:restore-d-ui · user: lưu plan và prompt cho gemini 3.1 pro -->
<!-- cursor: .cursor/plans/restore_d-ui_plan_3b93f412.plan.md -->

# Plan: Restore D-UI + khớp plan trên disk

> UI lệch plan D-UI: commit `c0bb784` (UI1–3 + prepend) bị mất khỏi `antigravity/dev` (chỉ còn D-UX Sprint 1 `745d3d7`).  
> Sibling: [`plan-2026-08-06-ui-visual.md`](plan-2026-08-06-ui-visual.md) · [`plan-2026-08-06-ux-interaction.md`](plan-2026-08-06-ux-interaction.md).

## Executor

| | |
|--|--|
| **Agent** | **Antigravity + Gemini 3.1 Pro High** (không Flash) |
| **Task branch** | `ui-visual/dev` → merge `antigravity/dev` (AGENTS §1a) |
| Verify | Cursor / Bugbot sau khi xong |
| Không dùng | Flash / free-claude-code cho task này |

## Chẩn đoán (locked)

| Plan | Disk `antigravity/dev` @ `745d3d7` | `c0bb784` (lost, còn trong git object) |
|------|-----------------------------------|----------------------------------------|
| UI1 cỡ chữ VN | thiếu | `#fontSizeVi` → `--vi-font-size` |
| UI2 Chỉ VI / 1 dòng | thiếu | `#oneLineMode` → `body.one-line-mode` |
| UI3 badge MOCK/offline | partial (WS only) | check `fallback`/`mock` |
| **UI4 newest-on-top** | **`appendChild` → mới dưới đáy** | **`prepend` → mới đầu list** |
| Đánh số `#0` / “0 câu” | bug | silence emit `is_final=false` → UI không `itemCounter++` |

Nhánh: `c0bb784` (D-UI) và `745d3d7` (D-UX) đều fork từ `3393934`; D-UX không kéo D-UI. `origin/ui-visual/dev` = `3393934` (không có UI).

UI4 không có nút riêng: mỗi card mới `prepend` ngay dưới system card “Sẵn sàng”.

## Checklist

- [x] Cherry-pick `c0bb784` lên working tree có D-UX; resolve `web/index.html` **giữ cả** D-UI + UX1–5
- [x] UI4: `jaList.prepend` / `viList.prepend` (không `appendChild`) — bắt buộc, verify 2 câu
- [x] `endpoints.py`: mỗi emit audio từ `pop_utterance` → `is_final=True` (root `#0`)
- [x] UI3: badge đỏ khi ASR fallback/mock **hoặc** MT `FallbackDict`
- [x] Giữ patch MT `sentencepiece` / sticky `load_failed` nếu còn uncommitted — không revert
- [x] Restore / sync `plan/plan-2026-08-06-ui-visual.md`; tick mốc; wiki ngắn
- [x] Commit + push / merge vào `antigravity/dev`; task `ui-visual/dev` đã xóa — disk `antigravity/dev` @ `d9e9b9f` (+ `885c2bc`). Không `master`

## Mốc

- [x] Restore D-UI đóng — ngày: 2026-08-06 · verified Cursor: 2026-08-06 (disk: UI1–4 + is_final trên `antigravity/dev` @ `d9e9b9f`)

## Cắt / không làm

D-UX Sprint 2 (PiP / localStorage / TTS / manifest) · waveform · bubble · shimmer · OBS.

---

## Appendix — Prompt Gemini 3.1 Pro High (copy nguyên khối)

```text
Bạn là lazy senior (ponytail) trên Antigravity với Gemini 3.1 Pro High (không Flash).

TASK: Restore D-UI đã mất + khớp plan trên disk cho Realtime Translate JP To VN.

ĐỌC BẮT BUỘC:
1. AGENTS.md (§0 ponytail, §1a branches, §2 disk wins, §6 errors.log, §7 nếu UI feature).
2. Living plan: plan/plan-2026-08-06-restore-d-ui.md — làm đúng checklist locked.
3. Sibling: plan/plan-2026-08-06-ui-visual.md · plan/plan-2026-08-06-ux-interaction.md.
4. web/index.html (HEAD hiện có D-UX UX1–5; thiếu UI1–3; đang appendChild).
5. local-bridge/app/api/endpoints.py (is_final từ client → card #0 sau silence endpointing).

BRANCH (trước khi sửa):
- checkout/create ui-visual/dev từ antigravity/dev (đã có D-UX Sprint 1).
- Agent name = antigravity.

VẤN ĐỀ:
- Commit c0bb784 (feat: implement D-UI visual features UI1-UI3) bị lệch nhánh — không nằm trên antigravity/dev.
- UI4 newest-on-top claim đã ship nhưng HEAD dùng appendChild (câu mới dưới đáy) — PHẢI prepend.
- Silence endpointing gửi is_final=false → UI itemCounter không tăng → mọi card #0 / “0 câu”.

LÀM (thứ tự):
1) git cherry-pick c0bb784 vào ui-visual/dev. Resolve conflict web/index.html: GIỮ CẢ
   - D-UI: fontSizeVi (--vi-font-size), oneLineMode (body.one-line-mode), warning-badge
   - D-UX: micSelect, Export, dblclick edit JA, Space toggle, WS offline disable mic
   Không xóa UX1–5. Không re-implement D-UI từ đầu nếu cherry-pick đủ.
2) UI4 BẮT BUỘC — trong addTranslationResult:
   jaList.prepend(jaCard); viList.prepend(viCard);
   (không appendChild). Verify: 2 câu → câu mới hơn nằm phía trên, dưới card Hệ thống.
3) endpoints.py: mỗi lần pop_utterance trả audio window (silence/max/flush có audio)
   → TranslationResponse is_final=True. Client is_final chỉ còn cho flush rỗng (resend last).
4) UI3: refreshEngineBadge — badge đỏ nếu asr_engine chứa fallback/mock HOẶC mt_engine là FallbackDict.
   WS offline giữ như D-UX hiện có.
5) Giữ các patch MT nếu đang có (sentencepiece trong requirements, sticky load_failed) — không revert.
6) Sync plan/plan-2026-08-06-ui-visual.md (checklist UI1–4 + UI4 prepend rõ); tick checklist restore plan;
   wiki/index.md + wiki/log.md + wiki/topics/realtime-translate.md ngắn.

GATE / CẤM:
- Không D-UX Sprint 2 (PiP/TTS/PWA/localStorage).
- Không waveform/bubble/shimmer/OBS.
- Không push master.
- Không --force master.

SAU KHI XONG:
1. Tick checklist + mốc trong plan/plan-2026-08-06-restore-d-ui.md.
2. Commit + push origin ui-visual/dev.
3. Merge vào antigravity/dev, push antigravity/dev, xóa ui-visual/dev (local+remote).
4. Trả về: file đổi, cách thử UI1–4 + #1/#2 ở đầu list, SHA branch.

Không tự verified — user chạy Cursor/Bugbot.
```
