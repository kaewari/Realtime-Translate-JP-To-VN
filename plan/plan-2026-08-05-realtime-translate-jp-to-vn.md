# Plan: Realtime dịch Nhật sang tiếng Việt

> **Cập nhật 2026-08-06** — scaffold structure theo tree YouTube JP Caption Studio: backend = `local-bridge/` (thay `app/backend`), UI sẽ đặt dưới `web/` (TBD). Chi tiết tree ở section "Cấu trúc thư mục" bên dưới.

## Cấu hình máy (đã kiểm tra 2026-08-05)
- Máy: MacBook Pro – Chip Apple M5 Pro (15 core CPU)
- RAM: 24 GB (unified memory)
- GPU: Apple GPU M5 Pro (Metal 4) – **không có NVIDIA CUDA**
- Hệ điều hành: macOS 27.0
- Python: 3.10.6 (đã cài, khuyên dùng venv riêng cho dự án)
- ffmpeg: 8.1.2 (đã cài qua Homebrew tại /opt/homebrew/bin/ffmpeg)

### Hệ quả cho plan
- **Không dùng được CUDA** → các lựa chọn tăng tốc là: Apple Metal (MPS), CoreML, hoặc CPU + quantization (int8).
- **faster-whisper (CTranslate2) chỉ chạy CPU trên Mac** → dùng được nhưng không tối ưu nhất.
- **Ưu tiên ASR: whisper.cpp (Metal) hoặc mlx-whisper (MLX)** – tối ưu riêng cho Apple Silicon, rất nhanh.
- 24GB RAM đủ để chạy song song: model ASR cỡ `small`/`medium` + model dịch nhỏ–vừa.
- ffmpeg đã sẵn sàng cho việc xử lý audio.

## Mục tiêu
- Xây dựng hệ thống dịch theo thời gian thực từ âm thanh tiếng Nhật sang tiếng Việt.
- Ưu tiên độ trễ thấp, nhưng chấp nhận mức “near real-time” thay vì tuyệt đối real-time.
- Dùng các giải pháp mã nguồn mở có sẵn trên GitHub làm nền tảng.

## Nguồn tham khảo tốt
- OpenAI Whisper: nền tảng ASR mạnh, hỗ trợ nhận diện và dịch bằng mô hình Whisper.
- whisper.cpp (ggerganov): bản C/C++ của Whisper, chạy qua **Metal** – rất nhanh trên Mac M5 Pro.
- mlx-whisper / ml-explore/mlx-audio: tối ưu cho Apple Silicon bằng MLX.
- faster-whisper: bản triển khai nhanh hơn Whisper gốc (chạy CPU trên Mac, không dùng Metal).
- WhisperLive / Whisper-Streaming: các repo phổ biến cho mô hình streaming và gần realtime.
- Hugging Face Transformers: dùng cho translation model như MarianMT, M2M100, NLLB.

## Kiến trúc đề xuất

### 1. Thu âm và chia luồng
- Thu âm từ micro bằng Python (sounddevice / PyAudio / pyaudio)
- Chia thành các chunk ngắn, ví dụ 1–2 giây
- Dùng VAD (Voice Activity Detection) để bỏ phần im lặng

### 2. Speech recognition
- Trên Mac M5 Pro (không CUDA), dùng một trong hai:
  - **whisper.cpp** (`ggerganov/whisper.cpp`) – chạy qua Metal, nhanh và nhẹ, có sẵn server streaming.
  - **mlx-whisper** (`ml-explore/mlx-audio`) – tối ưu riêng cho Apple Silicon bằng MLX.
- Model khuyên dùng: `small` hoặc `medium` (cân bằng tốc độ/độ chính xác cho tiếng Nhật). `large-v3` vẫn chạy được với 24GB RAM nhưng chậm hơn theo chunk.
- Cấu hình:
  - device: `metal` (whisper.cpp) hoặc mặc định MLX (mlx-whisper)
  - language: `ja`
- Mỗi chunk được chuyển thành text tạm thời

### 3. Translation
- Sau khi có text ASR, chuyển sang tiếng Việt bằng một mô hình dịch:
  - **Helsinki-NLP/opus-mt-ja-vi** (MarianMT) – nhỏ, chuyên cho Nhật→Việt, ưu tiên MVP.
  - **facebook/m2m100_418M** hoặc **NLLB-200-distilled-600M** – mạnh hơn, cần nhiều RAM hơn.
- Chạy qua PyTorch với backend **MPS** (`torch.backends.mps`) nếu được, hoặc CPU nếu cần ổn định hơn.
- Nếu cần đơn giản nhất, có thể dùng API dịch như OpenAI/DeepL, nhưng ưu tiên local-first cho kiểm soát chi phí

### 4. Gộp và hiển thị kết quả
- Dùng buffer để nối câu ngắn thành câu dài hơn
- Tránh hiện quá nhiều text rời rạc
- Gửi kết quả ra UI qua WebSocket hoặc SSE

### 5. UI
- MVP có thể là web app đơn giản:
  - nút Start/Stop
  - vùng hiển thị text Nhật
  - vùng hiển thị bản dịch tiếng Việt
- Có thể dùng React/Next.js hoặc plain HTML/JS

## Đề xuất stack (cho máy hiện tại)
- Backend: Python + FastAPI + WebSocket
- ASR: whisper.cpp (Metal) hoặc mlx-whisper – ưu tiên cho Apple Silicon
- Translation: Hugging Face Transformers (`opus-mt-ja-vi` trước, nâng cấp M2M100/NLLB sau) + MPS
- Audio: sounddevice (thu micro), ffmpeg (đã cài – xử lý/convert audio)
- Frontend: React hoặc Next.js (có thể bắt đầu bằng HTML/JS đơn giản)
- Môi trường: Python venv riêng (Python 3.10.6 đã có sẵn)
- Deployment: local desktop first, sau đó Docker hoặc cloud

## Kế hoạch triển khai

### Phase 1 – PoC nhanh (3–5 ngày)
- Tạo `local-bridge/` (backend Python: FastAPI + WebSocket) nhận micro input
- Chạy Whisper trên audio chunk ngắn
- In ra text tiếng Nhật và bản dịch tiếng Việt
- Không cần tối ưu quá nhiều về độ trễ

### Phase 2 – Near real-time (5–7 ngày)
- Tối ưu chunking và buffering
- Dùng VAD để loại khoảng lặng
- Giảm độ trễ bằng cách xử lý từng chunk thay vì toàn bộ file
- Cải thiện logic gộp câu

### Phase 3 – UI và trải nghiệm người dùng (3–4 ngày)
- Tạo giao diện web hiển thị text và bản dịch
- Thêm nút start/stop, clear transcript, copy text
- Hiển thị timestamp cho từng câu

### Phase 4 – Tối ưu hiệu năng (1–2 tuần)
- Tận dụng Metal: dùng whisper.cpp với backend Metal hoặc MLX (không dùng CUDA trên Mac)
- Dùng quantization/int8 để giảm RAM/CPU khi cần
- Cân nhắc ONNX Runtime (CoreML/CPU) nếu cần chạy gọn hơn
- Nếu cần, dùng model nhỏ hơn để đổi lại giữa tốc độ và độ chính xác

## Mốc thành công MVP
- Có thể thu âm giọng nói tiếng Nhật từ micro
- Có thể nhận diện text tiếng Nhật trong vòng vài giây
- Có thể dịch sang tiếng Việt và hiển thị trên UI
- Chấp nhận độ chính xác chưa tối ưu ở bước đầu

## Rủi ro và cách giảm thiểu
- Độ trễ cao: dùng smaller model + chunk ngắn + VAD
- Độ chính xác kém: dùng model lớn hơn hoặc fine-tune trên dữ liệu Nhật-Việt
- Cấu hình môi trường phức tạp: ưu tiên Docker và requirements rõ ràng
- Tốn RAM/VRAM: dùng quantized model và giảm batch size

## Cấu trúc thư mục (đã scaffold 2026-08-06 — theo tree YouTube JP Caption Studio)

- extension/              # (TBD) Chrome extension — background/, content/, injected/, popup/, sidepanel/, shared/, styles/, Scripts/
- local-bridge/           # Backend Python (FastAPI + WebSocket): app/ (api/, core/, schemas/, services/, utils/, main.py), data/dict/, scripts/, tests/, bin/, errors.log
- macos-bridge-app/       # (TBD) macOS bridge app — Sources/
- ipad-app/               # (TBD) iPad app — Views/, Services/, Models/, Resources/, Scripts/
- iphone-app/             # (TBD) iPhone app — Views/, Services/, Models/, Resources/, Scripts/
- data/                   # config/ (config máy), dict/, subtitles/ (runtime)
- scripts/                # (TBD) scripts tiện ích
- testdata/               # fixture test / golden audio
- tools/ime-switch/       # (TBD) IME switch cho input tiếng Nhật
- web/saved-items/        # (TBD) web app lưu bản dịch
- skills/                 # 5 skill: ponytail, codegraph, realtime-translate, local-bridge, realtime-regression
- wiki/                   # LLM wiki (Karpathy): index.md, log.md, topics/, upstream/
- plan/ review/           # plan/review file (bất biến; wiki = tổng hợp sống)

Ghi chú: models ASR/MT sẽ ở `local-bridge/data/models/` (bootstrap download, gitignored — chưa tạo dir cho tới khi bootstrap cần).

## Khuyến nghị triển khai ban đầu
- Bắt đầu bằng mô hình ASR: whisper.cpp (Metal) hoặc mlx-whisper – tối ưu cho Mac M5 Pro
- Translation: `Helsinki-NLP/opus-mt-ja-vi` (nhỏ, nhanh, đủ cho MVP)
- Không nên bắt đầu bằng full stack quá phức tạp
- Ưu tiên build một phiên bản chạy local trước, rồi mới nâng cấp sang production

## Gợi ý ưu tiên
1. Xây dựng backend chạy được trên máy local
2. Đảm bảo ASR tiếng Nhật hoạt động ổn trước
3. Thêm translation sau
4. Mới tối ưu latency ở bước sau
