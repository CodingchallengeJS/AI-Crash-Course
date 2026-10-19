# AI Crash Course

Web ôn lý thuyết AI bằng tiếng Việt cho VAIO/IAIO, bám hai đề thi trong `real-test`.

```powershell
npm run dev
```

Mở **http://127.0.0.1:5173**. Không cần `npm install`. Hoặc mở trực tiếp [ai-exam/dist/index.html](ai-exam/dist/index.html).

- 11 bài RL/AI cổ điển dạng bài giảng nhập môn: ví dụ xuyên suốt, giải nghĩa thuật ngữ, trace từng bước, bảng so sánh và mục lục. ML/DL/CV/NLP giữ dạng ôn tập công thức.
- 67 bài học: ML, DL, CV, NLP, AI cổ điển, RL và Training Lab. Có công thức, ví dụ giải, câu tự kiểm tra, ghi chú và code minh họa.
- 30 hồ sơ kiến trúc, sơ đồ khối tương tác và so sánh hai model.
- 176 công thức với KaTeX cục bộ; máy tính Gini/entropy, information gain, linkage, convolution, precision/recall/F1.
- Bản đồ 10 mục [phạm vi IAIO 2026](https://iaio-official.org/competition2026/) ở `#/syllabus`. Bổ sung BFS/DFS/UCS/A*, minimax, CNF/SAT/unification, CSP/forward checking/AC-3, MDP/Bellman/TD/Q-learning, t-SNE và recommender SVD/ALS/NCF.
- 11 bài Training Lab: audit và preprocessing, validation/OOF, LR schedulers, best/last checkpoint và early stopping, hard/soft voting, stacking/EMA/SWA/TTA, pseudo-labeling, augmentation/MixUp/CutMix, AMP/accumulation/clipping và quy trình thí nghiệm.
- Phòng thử `#/workshop`: đồ thị LR tương tác, Q-learning/SARSA, trace queue AC-3, hard/soft voting và early stopping. Chạy cục bộ, không cần AI key.
- Toàn bộ 129 câu: 100 VOAI sơ loại 2025 trong phụ lục công văn 2026 và 29 VAIC 2025. Giữ ảnh, bảng, code và PDF gốc; gắn nhiều chủ đề khi cần.
- Bộ lọc nhiều chủ đề và nguồn; luyện có giải thích, thi thử có giờ, nộp/chấm, khôi phục lượt dở, làm lại câu sai, đánh dấu câu.
- Lộ trình 4 giờ và checklist. Tiến độ lưu trên thiết bị bằng localStorage.
- Tìm kiếm toàn web bằng tiếng Việt/Anh; kết quả chỉ rõ bài và nhảy tới công thức. Dùng ô trang chủ, menu **Tìm kiến thức**, `/` hoặc `Ctrl+K`.
- **Chat popup cạnh bài học**: bấm Hỏi AI, thu gọn/mở lại giữ bản nháp và hội thoại. Chọn “Kèm bài đang đọc”, “Kèm đoạn đã bôi đen” hoặc “Hỏi AI về phần này”; xem trước và bỏ trước khi gửi. Chỉ nội dung được chủ động chọn mới đi cùng câu hỏi tới Google.
- **Gia sư AI** dùng key Google AI Studio do bạn nhập; chọn model từ danh sách Google hoặc nhập ID, chat nhiều lượt, hiển thị LaTeX, dừng và thử lại. Key chỉ giữ trong bộ nhớ tab; hội thoại giữ trong phiên tab. Không tự gửi bài/ảnh đề/ghi chú sang Google.

Lời giải do trang biên soạn, không phải key chính thức. 7 câu có lựa chọn chồng lấn, lỗi cú pháp hoặc thiếu dữ kiện được giải thích riêng và không tính điểm tự động. Model kinh điển được phân biệt với các hướng hiện đại; không gọi chung mọi model là SOTA hiện tại.

Mã web ở `ai-exam/dist`: `content.js` là giáo trình ban đầu, `extension.js` bổ sung AI/RL/training, `workshop.js` chứa bản đồ syllabus và ví dụ tương tác, `models.js` là hồ sơ model, `questions.js` là ngân hàng câu hỏi, `app.js` là tương tác. Mọi font và thư viện hiển thị đều nằm trong dự án; không có runtime CDN.

```powershell
npm run build
```

Lệnh build tạo service worker từ đúng nội dung static. Bản localhost/HTTPS dùng ngoại tuyến sau khi cache tải xong. Mở file trực tiếp vẫn đọc và làm bài được.

Kiểm tra trình duyệt: chạy server cổng 8000 bằng `python -m http.server 8000 --bind 127.0.0.1 --directory ai-exam/dist`, sau đó `npm test`. Kiểm tra cần Python Playwright và Chromium. Trích lại đề cần PyMuPDF, FontTools, Pillow; xem `scripts/extract_exams.py` và `scripts/prepare_questions.py`.

Kiểm tra riêng tìm kiếm/chat: `npm run test:tutor`. Bộ này giả lập Google API, không cần key thật. Hướng dẫn nhập key/chọn model ở [ai-exam/README.md](ai-exam/README.md).

Kiểm tra phần mở rộng: `npm run test:extension`, dùng cùng server cổng 8000. Kiểm công thức, tìm kiếm, code Python hợp lệ về cú pháp, 5 ví dụ tương tác, nghiệm CSP vét cạn và hiển thị mobile. Các đoạn PyTorch là khung minh họa, cần model/loaders và môi trường Python của người học; không chạy Python trong trình duyệt. Bộ đề gốc vẫn 129 câu; không thêm câu tự biên soạn dưới nhãn VOAI/VAIC. Lịch 4 giờ cũ được ghi rõ phạm vi và có lịch bổ sung AI/RL riêng.

Kiểm tra nhập môn/chat popup: npm run test:beginner. Dùng API Google giả lập để kiểm đính kèm theo lựa chọn, không tự gửi ghi chú, giữ URL/bản nháp/hội thoại, mục lục và responsive.
