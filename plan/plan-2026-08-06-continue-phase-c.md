<!-- date: 2026-08-06 -->
<!-- source: chat:continue-phase-c · user: lưu plan này (Continue Phase C verify + close) -->
<!-- cursor: .cursor/plans/continue_phase_c_79d27586.plan.md -->

# Plan: Continue Phase C — verify + close mlx-whisper

> Bản lưu của Cursor plan **Continue Phase C**.  
> Living checklist / số đo / mốc: cập nhật in-place tại [`plan/plan-2026-08-06-phase4-latency.md`](plan-2026-08-06-phase4-latency.md).  
> Phase A/B: [`plan/plan-2026-08-06-bugfix-phase-a-b.md`](plan-2026-08-06-bugfix-phase-a-b.md).

## Overview

Hoàn thiện Phase C trên disk: cài `mlx-whisper`, đo latency thật, khóa claim (không tin `~63ms` cũ), sync living plan C + wiki. Phase B deferred.

## Gate

- **A done** trên disk (đã xác nhận).  
- **B không chặn C** (nới so với gate cũ A+B+Bugbot B).

## Todos

- [x] `pip install -r requirements.txt`; `import mlx_whisper` OK
- [x] `python3 benchmark_asr.py` — ghi load / engine / avg ms vào living plan C
- [x] unittest xanh không `ImportError` mlx; badge `/api/status` hiện mlx
- [x] Retick living plan C + wiki ingest với số đo thật

## Steps

1. **Cài deps** — `cd local-bridge && python3 -m pip install -r requirements.txt && python3 -c "import mlx_whisper; print('ok')"`. Pip fail → `WARNING:bridge:` trong `errors.log`, dừng, không claim latency.
2. **Đo** — `python3 benchmark_asr.py` (warmup + 5× noise 2s @16k). Mục tiêu &lt; 1–2s. Nếu &gt;2s: một bước model nhỏ hơn (`whisper-base-mlx` / tiny) — không song song whisper.cpp.
3. **Smoke** — `python3 -m unittest tests.test_pipeline`; giữ Phase A contracts (`to_thread`, `is_final`, sample_rate, `load_failed`).
4. **Sync** — điền bảng Số đo + tick mốc trong living [`plan-2026-08-06-phase4-latency.md`](plan-2026-08-06-phase4-latency.md); wiki topic / index / log.

## Out of scope

Phase B; whisper.cpp path thứ hai; extension/ipad/iphone/macos-bridge-app.

## Executor

Antigravity + Gemini 3.1 Pro High, hoặc Cursor. Không Flash / free-claude-code.

## Handoff prompt

Copy từ appendix trong [`plan-2026-08-06-phase4-latency.md`](plan-2026-08-06-phase4-latency.md) (Continue C).
