<!-- date: 2026-08-06 -->
<!-- source: chat:6f235f14-dfac-4aec-b2a4-c30dee9f17fb · user: tổng hợp các tính năng UX/UI thành file review -->

# Đề xuất Nâng cấp UI/UX (Phase D - Pro Max)

> **Tài liệu tham khảo & Đề xuất tương lai**
> File này tổng hợp các ý tưởng nâng cấp giao diện và trải nghiệm người dùng (UX/UI) nhằm biến web app nội bộ thành một sản phẩm tiệm cận mức độ thương mại (Pro Max).
> Các tính năng này chủ yếu thi công ở Frontend (`web/index.html` và Javascript), ít hoặc không tác động đến kiến trúc Backend hiện tại.

## Nhóm 1: Tính năng Cốt lõi & Khả năng Dùng (Must-have Usability)

| Tính năng | Mô tả | Độ khó |
|-----------|-------|--------|
| **1. Đảo ngược luồng tin nhắn (Newest on top)** | Thay vì cuộn xuống đáy, các câu dịch mới sẽ được chèn lên đầu danh sách (`prepend`). (✅ **Đã triển khai nhanh trên disk**) | Rất Dễ |
| **2. Lưu trữ Lịch sử (Session History)** | Tự động lưu các câu đã dịch vào `localStorage` hoặc `IndexedDB`. Tránh mất dữ liệu khi vô tình F5 (Refresh) trang web. Có thêm thanh Sidebar nhỏ bên trái để xem lại các phiên làm việc cũ. | Trung Bình |
| **3. Chọn Micro Đầu Vào (Device Selection)** | Sử dụng `navigator.mediaDevices.enumerateDevices()` để liệt kê và cho phép người dùng chọn đích danh Micro muốn thu (ví dụ: Mic tai nghe thay vì Mic máy tính). Thêm icon ⚙️ Cài đặt. | Dễ |
| **4. Export / Tải xuống Phiên dịch** | Cung cấp nút 📥 Tải xuống để xuất toàn bộ đoạn hội thoại ra file `.txt`, `.md`, hoặc file phụ đề `.srt` có chứa Timestamp chuẩn xác. Rất hữu ích để làm biên bản họp. | Dễ |
| **5. Phát âm (Text-to-Speech - TTS)** | Tích hợp biểu tượng Loa (🔈). Sử dụng `Web Speech API` có sẵn của trình duyệt để đọc to câu tiếng Nhật hoặc bản dịch tiếng Việt mà không cần gọi API Backend tốn kém. | Dễ |

---

## Nhóm 2: Trải nghiệm Nâng cao & Đa nhiệm (Advanced Multi-tasking)

| Tính năng | Mô tả | Độ khó |
|-----------|-------|--------|
| **6. Picture-in-Picture (PiP) Subtitle** | **Killer Feature:** Tận dụng `Document Picture-in-Picture API` để tách bản dịch tiếng Việt ra một cửa sổ nhỏ nổi trên cùng (Always-on-top). Người dùng có thể vừa họp Zoom/Google Meet vừa xem phụ đề mà không cần chia đôi màn hình. | Trung Bình |
| **7. Chỉnh sửa & Dịch lại (In-place Edit)** | Cho phép click đúp vào câu tiếng Nhật (do ASR nhận diện sai) để tự gõ lại. Bấm Enter để Frontend gọi API `/api/translate` lấy lại bản dịch mới cập nhật trực tiếp vào UI. | Trung Bình |
| **8. Chế độ OBS (Chroma Key Stream Mode)** | Thêm nút Toggle để biến giao diện sang dạng nền Xanh lá (hoặc Đen tuyền), chữ to ở giữa. Phục vụ streamer/Youtuber muốn chèn luồng web này thẳng vào OBS làm phụ đề trực tiếp. | Dễ |
| **9. Cài đặt thành App (PWA)** | Thêm `manifest.json` và Service Worker cơ bản để trình duyệt Chrome/Safari cho phép "Cài đặt ứng dụng". Web app sẽ hoạt động như một Native App độc lập trên máy Mac/Win (có icon riêng, không có thanh địa chỉ). | Dễ |

---

## Nhóm 3: Hiệu ứng Thị giác "Đắt tiền" (Visual Candy)

| Tính năng | Mô tả | Độ khó |
|-----------|-------|--------|
| **10. Sóng âm mượt mà (Smooth Waveform)** | Thay thanh `audio-meter` ngang cứng nhắc bằng thẻ `<canvas>` kết hợp `AnalyserNode`. Vẽ đường sóng âm uốn lượn liên tục giống Siri hoặc trợ lý ảo Google. | Trung Bình |
| **11. Bong bóng Chat (Chat Bubble)** | Đổi các thẻ Card vuông thành bong bóng Chat (như iMessage). Gom nhóm các câu nói liên tục vào chung một khối, ngắt khối khi có khoảng lặng dài. Trực quan hơn nhiều. | Dễ |
| **12. Shimmer & Flash Animations** | Các câu nói đang dở dang (`is_final: false`) sẽ có hiệu ứng chữ mờ dần hoặc bóng loang (shimmer) để báo hiệu hệ thống đang "suy nghĩ". Khi chốt câu, viền chớp sáng (flash) 0.5s. | Dễ |
| **13. Phản hồi VAD trên Meter** | Thanh đo âm thanh thay đổi màu sắc rực rỡ khi vượt ngưỡng VAD (Đang nói) và chuyển xám tĩnh khi dưới ngưỡng (Đang im lặng). | Dễ |

---

## 🚀 Kế hoạch Hành động Đề xuất (Next Steps)

Nếu tiếp tục mở rộng dự án, chúng ta nên chia các đề xuất này làm 2 đợt (Sprints):

1. **Sprint 1 (Tiện ích thiết thực - Must-Haves):** Tập trung vào Nhóm 1 và tính năng số 9 (PWA). Mục tiêu là làm cho tool không thể mất dữ liệu và có thể export ra ngoài.
2. **Sprint 2 (Trải nghiệm Pro - Nice-to-Haves):** Tập trung vào Nhóm 2 (PiP Window rất hữu ích) và Nhóm 3 (Waveform) để tạo độ "Wow" khi trình diễn.
