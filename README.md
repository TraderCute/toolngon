# Bot Cược Escape Master Tích Hợp Gemini AI

Đây là một bot tự động chơi game Escape Master, sử dụng AI của Google (Gemini) để phân tích và đưa ra dự đoán phòng cược an toàn nhất.

## Tính năng chính

-   **Phân tích thông minh:** Sử dụng API Gemini để phân tích dữ liệu thống kê 100 ván và lịch sử chi tiết 10 ván gần nhất.
-   **Logic Gấp thếp:** Tự động áp dụng chiến thuật gấp cược khi thua với các hệ số có thể tùy chỉnh.
-   **Quản lý Rủi ro:** Cho phép cài đặt Stop Loss (dừng lỗ) và Take Profit (chốt lời).
-   **Lưu cài đặt:** Tự động lưu và tải lại các thông tin nhạy cảm (`API Key`, `UID`, `Secret Key`) để không phải nhập lại mỗi lần chạy.

## Hướng dẫn cài đặt

Bạn sẽ cần có [Python 3](https://www.python.org/downloads/) được cài đặt trên máy tính.

**1. Clone Repository**
Mở terminal (dòng lệnh) và chạy lệnh sau để tải code về máy:
```bash
git clone https://github.com/TEN_USER_CUA_BAN/gemini-escape-master-bot.git
