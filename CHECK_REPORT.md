# Kiểm tra bản khôi phục theo báo cáo — 05/11/2026

Giao diện đã được đưa về bố cục trong ảnh báo cáo. RAG trở lại luồng PDF → chia
đoạn → embedding tiếng Việt → FAISS → trả lời theo nguồn. Số đo cũ vẫn thuộc
đúng source và lượt chạy của chúng; không đổi thành kết quả bản khôi phục.

## Source và những phần đã sửa

- Base Git trước sửa: `78b118f1bca7988970abf3d1627d144716aa0846`. Graph đã chạy các lượt cuối: `9df445c208d40dc57c00`. Commit xuất bản cuối xem release lock, không tự suy đoán tại đây.
- Model trả lời giữ `openai/gpt-oss-20b`. Checkpoint embedding `VoVanPhuc/sup-SimCSE-VietNamese-phobert-base` khóa revision `608779b86741a8acd8c8d38132974ff04086b138`; dùng PyVi, mean pooling, vector chuẩn hóa và FAISS IndexFlatL2. Khoảng cách nhỏ hơn là gần hơn, không phải xác suất đúng.
- PDF 6 trang giữ SHA-256 `91c16764898a88f26bb73706d1188afd3e3631f8a462c08fd76130a64ebc736a`. Lock requirements hiện tại: `5923a9ef5dbdc61f4a9d38a51b03ba993931a50d2bd6d6ba6c4bd5477271de92`. Source/asset hash nằm trong `docs/RESTORED_RUNTIME_IDENTITY.json`.
- Chunk 1000 ký tự, overlap 180, top-k 6 được chọn sau các lần so sánh. Bản 500/50/top-2 được chạy lại chỉ đủ span 6/25; bản được chọn đủ 25/25. Bộ 27 câu đã dùng để sửa/chọn tham số nên kết quả này không độc lập và không phải độ đúng của 25 đáp án model.
- Frontend khôi phục theo ảnh, logo lấy từ ảnh báo cáo. Chưa tìm thấy HTML gốc trong các nguồn đã kiểm tra; không nhận là sao chép nguyên source frontend cũ. Không hardcode câu trả lời lịch sử.
- Model dùng tool calling cho mode auto. Với câu trả lời dựa nguồn, model chọn mã quote; server giải mã về đoạn gốc, kiểm tra source ID và quote trước khi trả về. Có nguồn/quote khớp chưa thay thế đánh giá nội dung.

## Đã chạy gì

Unit nhẹ: **67 đạt, 2 bỏ qua**, tổng 69 ca, 12.810 giây. Đây là kiểm tra cơ chế/unit/API, không gọi provider. Hai ca bỏ qua và các lần thiếu RAM được giữ đúng trạng thái. UI có 12/12 kiểm tra Chrome dùng fixture trình duyệt cho bước gửi/nhận, không dùng làm điểm model thật.

Retrieval production dùng embedding thật trong máy và FAISS, không fixture và không Groq/Tavily. Chi tiết chunk theo thứ hạng, trang, nội dung, điểm và reference ở `evidence/restored_20261105/faiss_final_production_retrieval/`. Giữ cả các cấu hình chưa đạt trong thư mục comparison.

## Cuộc trò chuyện thật, một phiên ba câu

Chỉ dùng lượt `live_conversation_2026-11-05T16-33-55-604Z` với đúng ba trace bên dưới; không chọn câu trả lời từ các lần thử khác. Cả ba HTTP 200/status ok, lần lượt qua RAG, hội thoại và web. Đây là hoàn tất kỹ thuật, chưa phải ba điểm nội dung đạt.

| Câu | Nhánh | Latency trình duyệt | Input / output token | Trace |
|---|---|---:|---:|---|
| 1 | rag | 8,183 s | 4.788 / 523 | `27807932154845fe8051681e33affcdb` |
| 2 | answer | 3,307 s | 571 / 102 | `f1b58d16d65e4ccb90ff050ff8ea1b6c` |
| 3 | web | 11,239 s | 3.435 / 909 | `7738a52e3aa84b25882590fd6df1c2ba` |

Tổng token của riêng lượt UI: input 8.794, output 1.534, tổng 10.328; usage đầy đủ 3/3 request. Ảnh và raw response tại `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T16-33-55-604Z/`.

## RAG thật, một lượt đủ 13 câu

Gồm 8 câu cũ, `new_01`, `new_03`, `new_06` và hai câu ngoài PDF. Các request đều
`mode:rag`, cache tắt; concurrency 1, delay 45 giây, index FAISS đã chuẩn bị
trước. Benchmark không gửi request warm-up; đây không phải phép đo cold-start.
Đáp án tham chiếu chỉ nằm ở bản ghi đánh giá, không gửi vào payload cho model.

Hoàn tất kỹ thuật **13/13**; có 10 phản hồi trả lời,
3 từ chối và 0 lỗi kỹ thuật. Latency của riêng lượt này:
mean 5,433 s, p50 5,197 s,
p95 9,687 s, percentile nearest-rank. Tổng token:
input 54.420, output 4.582,
tổng 59.002; usage đầy đủ 13/13.

| ID | HTTP / trạng thái | Latency HTTP | Input / output token | Source entries | Trace |
|---|---|---:|---:|---:|---|
| rag_01 | 200 / ok | 6,118 s | 4.121 / 384 | 5 | `e1cd5f85f20b483eb41b5ecaf776820a` |
| rag_02 | 200 / ok | 3,812 s | 4.329 / 267 | 2 | `2363c9048cef4c7a89720b7c9069f1d3` |
| rag_03 | 200 / ok | 5,014 s | 4.217 / 221 | 1 | `7b6bd4a474214d17b8bca4fec345ad95` |
| rag_04 | 200 / ok | 3,409 s | 4.231 / 303 | 3 | `4556234cc8684418b947b05b72c33aa9` |
| rag_05 | 200 / ok | 9,687 s | 3.913 / 607 | 1 | `3dd2705dd7f34389bd3af41b6de07044` |
| rag_06 | 200 / refused | 6,223 s | 4.301 / 379 | 0 | `830204d891c747a4b102626c615b08a7` |
| rag_07 | 200 / ok | 6,917 s | 4.300 / 313 | 1 | `d5462bb3eba84692b0fc33313223de89` |
| rag_08 | 200 / ok | 5,903 s | 4.138 / 520 | 2 | `e84f6db4c1284db2bc2d187a149c2cb8` |
| new_01 | 200 / ok | 5,337 s | 3.951 / 300 | 1 | `b084742ba7cc456194c555c867b52688` |
| new_03 | 200 / ok | 4,577 s | 4.471 / 400 | 1 | `471704d92db64f15a187f748b68fc7ff` |
| new_06 | 200 / ok | 5,156 s | 4.149 / 494 | 1 | `143acd72b5dd417786530632ab488061` |
| negative_01 | 200 / refused | 3,273 s | 4.249 / 200 | 0 | `47fde85fe49b46afbffa7754d82a41c8` |
| negative_02 | 200 / refused | 5,197 s | 4.050 / 194 | 0 | `8e284ebc05f14b60bcff7a5eca28cd25` |

Raw results, reference, context truy xuất, output model, trace và CSV nằm tại
`evidence/restored_20261105/faiss_live_final_13/`. Thiếu usage để null hoặc trống; không ghi 0 để thay
cho dữ liệu chưa có. Không cộng latency của lượt UI vào lượt RAG này.

## Nội dung còn cần đối chiếu

- HTTP 200, trạng thái `ok` và quote khớp nguồn chỉ xác nhận một phần cơ chế; không đủ để chấm đáp án đúng.
- Bộ 27 câu retrieval đã dùng để sửa và chọn tham số. Kết quả 25/25 đủ span không phải đánh giá độc lập hoặc answer accuracy.
- `rag_06` vẫn từ chối dù retrieval có các span tham chiếu. Tìm được đoạn và tạo được câu trả lời là hai bước khác nhau.
- Các câu `rag_05`, `rag_07`, `new_03` có câu trả lời phù hợp tham chiếu nhưng quote chưa trực tiếp hoặc chưa đầy đủ cho ý được nêu. `rag_01` chỉ được audit là phần lớn có căn cứ, còn rút gọn bước giải thích và quote chưa trọn. Đây là đối chiếu của Codex, không phải điểm người thật.
- Không tự điền điểm người chấm cho lượt mới. RAG 96/104 và web 20/32 chỉ thuộc các phản hồi lịch sử đã được chấm.
- Hai ca unit nặng bị bỏ qua trong lượt kiểm tra nhẹ do điều kiện tài nguyên. Không tính chúng là đạt; giữ log của các lần thiếu RAM.
- FAISS/top-k mới có thể gửi ngữ cảnh dài hơn bản cũ. Không dùng latency hoặc token của BM25 để mô tả bản khôi phục.

Audit riêng nếu đã có:

- `evidence/restored_20261105/faiss_live_final_13/content_audit.csv`
- `evidence/restored_20261105/faiss_live_final_13/content_audit.json`

Đối chiếu dưới đây do Codex thực hiện trên toàn bộ response, tham chiếu và
context đã lưu của đúng lượt 13 câu. Không xem đây là điểm người thật, đánh giá
độc lập hoặc xác nhận lâm sàng:

| ID | Nội dung đối chiếu | Citation | Nhận xét |
|---|---|---|---|
| rag_01 | Phần lớn có căn cứ | Một phần | Đúng tác dụng giảm căng thẳng/nhịp tim/huyết áp. Câu trả lời rút gọn bước não gửi thông điệp đến toàn cơ thể; các quote bị lặp và có đoạn câu chưa hoàn chỉnh. |
| rag_02 | Có căn cứ đối chiếu | Trực tiếp | Vị trí hai tay khớp trang 2; có trích nguyên câu hỗ trợ trực tiếp. |
| rag_03 | Có căn cứ đối chiếu | Trực tiếp | Giữ đúng 3–10 lần, không đổi đơn vị; quote trang 2 có đủ con số. |
| rag_04 | Có căn cứ đối chiếu | Trực tiếp | Giữ 4/7/8 là số đếm, không tự đổi sang giây; ba quote trang 3 tương ứng từng bước. |
| rag_05 | Có căn cứ đối chiếu | Chưa đủ hỗ trợ ý trả lời | Đáp án nằm ngửa/co đầu gối khớp tham chiếu, nhưng quote được chọn kết thúc ở bất kỳ vị trí; chưa trực tiếp chứng minh tư thế khi mới tập. |
| rag_06 | Từ chối chưa phù hợp | Không có | Model báo thiếu thông tin dù ngữ cảnh đã truy xuất có 3–5 phút. Hoàn tất kỹ thuật và retrieval tìm đúng đoạn không đồng nghĩa trả lời đúng. |
| rag_07 | Có căn cứ đối chiếu | Chưa đủ hỗ trợ ý trả lời | Đáp án nâng đầu sau cùng khớp tham chiếu; quote dừng ở bằng cách lăn, thiếu phần nâng đầu ở dòng tiếp theo. |
| rag_08 | Có căn cứ đối chiếu | Có quote trực tiếp, còn đoạn thừa | Đúng 10–20 phút, có một quote trực tiếp; quote bổ sung chỉ nêu bài tập mất vài phút nên không cần thiết. |
| new_01 | Có căn cứ đối chiếu | Trực tiếp | Mặc quần áo thoải mái, khớp nguyên văn trang 2. |
| new_03 | Có căn cứ đối chiếu | Quote chưa trọn | Đáp án giữ ngực không di chuyển đúng tham chiếu. Quote dừng ở Giữ nguyên vị trí của, thiếu từ ngực nằm ở phần kế tiếp. |
| new_06 | Có căn cứ đối chiếu | Trực tiếp | Nhắm mắt, khớp câu trích trực tiếp trang 5. |
| negative_01 | Từ chối phù hợp ngoài PDF | Không áp dụng | PDF không có dân số Việt Nam 2026; model từ chối, không đưa số liệu. |
| negative_02 | Từ chối phù hợp ngoài PDF | Không áp dụng | PDF không có học phí đại học năm 2026; model từ chối, không bịa số liệu. |

## Giữ các lần chưa đạt

- `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T13-28-10-364Z/`: 3 request đã ghi; status `ok, ok, refused`; giữ riêng để đối chiếu quá trình sửa.
- `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T13-35-23-475Z/`: 3 request đã ghi; status `ok, ok, refused`; giữ riêng để đối chiếu quá trình sửa.
- `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T15-55-34-553Z/`: 3 request đã ghi; status `error, ok, ok`; giữ riêng để đối chiếu quá trình sửa.
- `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T16-08-17-665Z/`: 3 request đã ghi; status `ok, ok, refused`; giữ riêng để đối chiếu quá trình sửa.
- `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T16-23-31-466Z/`: 3 request đã ghi; status `error, ok, error`; giữ riêng để đối chiếu quá trình sửa.
- `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T16-29-08-998Z/`: 3 request đã ghi; status `error, ok, error`; giữ riêng để đối chiếu quá trình sửa.
- `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T16-33-55-604Z/`: 3 request đã ghi; status `ok, ok, ok`; lượt UI cuối được chọn.

Trace tổng của ngày chạy nằm tại `evidence/restored_20261105/server_traces_all.jsonl`, gồm cả live,
fixture, lỗi và từ chối theo đúng suite/graph của từng dòng. Không xóa lần thất
bại để chỉ giữ kết quả sau sửa. `TRACE_SELECTION.json` mô tả cách lọc ngày theo
giờ Việt Nam; `INDEX_SHA256.json` đối chiếu byte các tệp được tuyển chọn.

## Lệnh tái lập

Tạo môi trường bằng requirements khóa, tự cấu hình `.env` trên máy chạy; không
đưa `.env`, API key, `.venv`, hồ sơ Chromium hoặc cache model vào Git/gói nộp.
Không đổi model và không thêm dịch vụ trả phí. Cần đủ RAM cho checkpoint; chạy
API và kiểm tra embedding lần lượt để tránh nạp hai bản model cùng lúc.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe start_api.py
```

Khi `/health` báo index ready, mở terminal khác để chạy một bộ mới; đổi tên thư
mục output nếu đã có kết quả để giữ các lượt riêng biệt:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.run_rag_live --base-url http://127.0.0.1:8000 --prepare-index --trace-file .cache/request_traces.jsonl --delay 45 --output ..\rag_live_recheck_moi --ids rag_01 rag_02 rag_03 rag_04 rag_05 rag_06 rag_07 rag_08 new_01 new_03 new_06 negative_01 negative_02
node .\evidence\restored_20261105\ui_restore\capture_live_conversation.cjs --run-live http://127.0.0.1:8000/
```

Kết quả trả lời thật cần API key/quota hợp lệ của dịch vụ hiện có. Nếu không
chạy được, giữ lỗi và dữ liệu còn thiếu; không dùng fixture hoặc đáp án tham
chiếu làm câu trả lời thật. Báo cáo Word/PDF cuối và hồ sơ chỉnh sửa văn bản được
bàn giao riêng sau khi khóa commit; không đưa bản nháp đầy đủ vào code Git.
