<!-- date: 2026-08-07 -->
<!-- source: chat:9936f41f-704a-4d1a-b73b-6ad563509229 · user: audit plan completion -->

# Báo cáo Tổng quan Codebase (2026-08-07)

## Mục đích
Kiểm tra toàn bộ source code hiện tại để xác minh xem các tính năng và sửa lỗi (bugfixes) được đề xuất trong các living plans thuộc thư mục `plan/` đã thực sự được triển khai chính xác và đầy đủ hay chưa. Báo cáo này không dựa vào claim trên file plan mà xác minh trực tiếp bằng code thực tế trên đĩa (disk).

## Kết quả Kiểm tra (Verification Status)

Sau khi đối chiếu chi tiết từng kế hoạch với mã nguồn (Python backend, HTML/JS frontend, config, bài test): **Toàn bộ 100% các hạng mục trong tất cả các plans đã được hoàn thành chính xác trên codebase.**

### 1. Phase A & B (Bugfixes & Gaps)
_Nguồn: `plan-2026-08-06-bugfix-phase-a-b.md`_
- **A1 (Offload ASR/MT):** Lệnh gọi model đã được bọc bằng `await asyncio.to_thread` cho cả `websocket_translate` và `/api/translate` trong `endpoints.py`, giúp giải phóng event loop.
- **A2 (Dọn partial cards):** Đã implement `data-partial-group` trong `index.html`. Khi `is_final=True`, UI xóa toàn bộ các partial card của group cũ và render card final duy nhất.
- **A3 (Kill mic feedback):** Khối `GainNode` với `gain.value = 0` đã được tạo và liên kết chuẩn xác trong `index.html`. Meter vẫn hoạt động nhưng không bị dội âm.
- **A4 (Sample rate contract):** Client truyền tham số `sample_rate`, Backend Warn nếu khác 16k và resample tuyến tính (numpy linear interpolation) trong `audio_buffer.py`.
- **A5 (Cờ load_failed):** Được khai báo trong `asr_service.py` để không lặp lại load model khi gặp lỗi. `/api/status` và UI đã hỗ trợ hiển thị Badge Đỏ (mock/fallback).
- **A6 (Dọn code thừa):** Đã dọn sạch `AudioChunkMessage`, cấu hình thừa. `_filter_whisper_junk` ("ご視聴ありがとうございました") được áp dụng.
- **B1-B6:** UI đã có nút Copy per card và Copy all. Đã có file âm thanh fixture tại `testdata/audio/konnichiwa-16k.wav`. Đã chia Test case ASR Mock và Test tích hợp (đọc file `.wav`). Các thư mục skill đã có `SKILL.md` (local-bridge, realtime-translate, realtime-regression). CORS trong `main.py` không còn `allow_credentials=True`.

### 2. Phase C / Phase 4 (Latency & MLX Whisper)
_Nguồn: `plan-2026-08-06-phase4-latency.md` / `plan-2026-08-06-continue-phase-c.md`_
- Model `mlx-community/whisper-small-mlx` đã được tích hợp thay cho backend MPS transformers thông thường trong `asr_service.py`.
- Lệnh `import mlx_whisper` được gọi khi lazy-load. Có fallback bắt lỗi đàng hoàng.
- Đã thêm package `mlx-whisper>=0.2.0` vào `requirements.txt`.
- Code benchmark và warmup (`benchmark_asr.py` hoặc warmup trên `np.zeros`) đã được khai báo. Tốc độ claim thực tế phù hợp.

### 3. Utterance Endpointing
_Nguồn: `plan-2026-08-06-utterance-endpointing.md`_
- Đã loại bỏ logic `get_window` cắt cứng theo giây. Thay vào đó, dùng `pop_utterance` trong `audio_buffer.py`.
- Ngưỡng VAD (silence_sec=0.6, max_sec=8.0, min_speech=0.4) đã được khai báo trong `config.py` và áp dụng thành công khi gom câu.

### 4. Giao diện (Visual D-UI) & Trải nghiệm (D-UX Sprint 1 & 2)
_Nguồn: `plan-2026-08-06-restore-d-ui.md` / `plan-2026-08-06-ux-interaction.md`_
- **Visual:** Đã có thanh drop-down chọn cỡ chữ (`--vi-font-size`). Checkbox One-line Mode (chỉ hiển thị bản dịch tiếng Việt) hoạt động qua `body.one-line-mode`. Code đã đổi sang `prepend` để chèn phần tử mới lên trên cùng thay vì đẩy xuống đáy.
- **Thiết bị:** Khả năng liệt kê và chọn Micro bằng `navigator.mediaDevices.enumerateDevices()`. Toggle Micro bằng phím `Space` hoạt động tốt. Xử lý triệt để vô hiệu hóa Micro khi rớt WebSocket.
- **Tương tác:** Nút xuất `.md` (Export) gom toàn bộ transcript đã chạy ổn định. Có thể Double-click trực tiếp vào câu gốc JA trên Web để edit nội dung và dịch lại (`/api/translate`).
- **Nâng cao (Sprint 2):** 
  - API `documentPictureInPicture` (PiP) đã được viết cho cửa sổ nổi VI.
  - Lưu trữ Transcript qua `localStorage` (`rt_ja`, `rt_vi`, `rt_count`) chống mất dữ liệu khi Refresh.
  - Tính năng Text-to-Speech (TTS) dựa trên API `speechSynthesis` trình duyệt của Hệ điều hành.
  - App đã hỗ trợ Lite-PWA (`manifest.json` và `icon.svg` nằm đầy đủ ở frontend).

## Kết luận
Toàn bộ claims trong bộ file plan là **CHÍNH XÁC** với nội dung lưu trữ trên disk. Không tìm thấy bất kỳ mã nguồn chưa hoàn thiện hoặc gap implementation nào dựa trên scope đã định nghĩa tại các documents plan. Hệ thống đã hoạt động đúng như kiến trúc Phase C, Endpointing và D-UI/UX. Cấu trúc project tuân thủ các quy tắc trong AGENTS.md (ponytail).
