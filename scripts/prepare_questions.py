import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path('.tools').resolve()))
import pymupdf

# Each answer is an authored solution, not an official answer key.
# ! marks an item excluded from automatic scoring because its wording/options are ambiguous.
DATA='''
VOAI|1|A|DL|dl-normalization|Vị trí Batch Normalization|Cấu hình thông dụng là Linear/Conv → BatchNorm → ReLU. Có kiến trúc dùng vị trí khác, nên đây là lựa chọn phổ biến trong đề.
VOAI|2|B|CV|cv-convolution|Tham số học của convolution|Weights của bộ lọc được học qua backprop; input size, stride, padding là siêu tham số.
VOAI|3|B|DL|dl-training|Loss không giảm: kiểm tra gì trước?|Kiểm tra pipeline, nhãn, loss, gradient và optimizer trước khi tùy tiện tăng độ sâu hoặc LR lên100 lần.
VOAI|4|B|NLP,DL|nlp-llm-systems|Chi phí fine-tune toàn bộ GPT|Cập nhật toàn bộ weights, gradients và optimizer states của LLM đòi nhiều compute/memory. PEFT/LoRA có thể giảm phần trainable.
VOAI|5|B|CV|dl-training|Trích feature từ ResNet-50|Lấy activation gần cuối, thường avgpool rồi flatten thành vector2048, trước classification head.
VOAI|6|!AC|NLP,DL|dl-activation|BoW + PyTorch: chọn output và loss|A hợp lệ: 1 logit + BCEWithLogitsLoss, nhãn float. C cũng hợp lệ: 2 logits + CrossEntropyLoss, nhãn class index. Đề yêu cầu một đáp án nhưng cả hai cách đều đúng; không chấm tự động.
VOAI|7|B|ML|ml-svm|So sánh SVM và k-NN|Kernel SVM có giai đoạn tối ưu có thể đắt. k-NN chủ yếu lưu dữ liệu, không fit weights theo một quy trình tối ưu rõ ràng; cả hai có bản hồi quy.
VOAI|8|A|ML|ml-svm|SVM phi tuyến lúc inference|Cần cùng biến đổi đặc trưng/kernel và preprocessing đã dùng trong train. Không đổi kernel khi predict.
VOAI|9|D|CV|dl-training|Ý nghĩa pretrained=True|Nạp weights đã học trên ImageNet, dùng cho transfer learning/feature extraction. API mới thường dùng weights=... thay pretrained=True.
VOAI|10|C|CV|cv-iou|Tính NMS với ba bounding boxes|B1 có score0.95. B2 nằm trong B1 nên IoU=80²/100²=0.64>0.40: loại B2. B3 không giao B1 nên giữ. Kết quả B1 và B3.
VOAI|11|A|ML|ml-foundations|Pandas: lấy năm dòng đầu|df.head() mặc định trả5 dòng đầu. df.take nhận danh sách chỉ số, không tương đương take(5).
VOAI|12|D|ML|ml-ensemble|Thuật toán dựa trên bagging|Random Forest dùng bootstrap và ngẫu nhiên tập con đặc trưng. XGBoost thuộc boosting.
VOAI|13|!|ML|ml-generalization|Giảm ảnh hưởng nhiễu và ngoại lệ|Câu quá rộng: PCA có thể lọc nhiễu ở các hướng phương sai nhỏ; regularization hạn chế fit nhiễu nhưng không phải robust outlier treatment nói chung. Không có lựa chọn luôn đúng; cần phân biệt denoising, regularization và robust loss.
VOAI|14|!|NLP|nlp-preprocessing|Thứ tự preprocessing văn bản|Normalize → tokenize là hợp lý. POS thường thực hiện trên từ chưa stemming; một pipeline khác có thể stemming trước. Thứ tự POS/stemming phụ thuộc thiết kế; không có một đáp án phổ quát nên bỏ chấm tự động.
VOAI|15|B|DL|dl-optimizers|Adaptive learning rate|AdaGrad/RMSProp/Adam điều chỉnh bước cập nhật theo từng tham số qua thống kê gradient.
VOAI|16|D|NLP|nlp-llm-systems|Chain-of-Thought|Gợi mô hình tạo các bước trung gian khi giải. Nó có thể giúp một số task nhưng không bảo đảm lời giải đúng.
VOAI|17|C|ML|ml-knn|Trọng số đặc trưng trong k-NN|Điều chỉnh đóng góp của từng thuộc tính trong metric, chẳng hạn d²=Σwⱼ(xⱼ−zⱼ)². Khác với cân trọng số bỏ phiếu theo khoảng cách hàng xóm.
VOAI|18|B|ML|ml-kmeans|Cập nhật ba tâm K-means|Lấy trung bình từng tọa độ: C1=(3,3), C2=(4,4), C3=(6,6).
VOAI|19|C|NLP|nlp-word2vec|Nguồn học vector GloVe|GloVe dùng ma trận đồng xuất hiện toàn cục và weighted least squares trên log counts.
VOAI|20|A|NLP|nlp-bert|Đầu vào BERT|Thông dụng gồm input_ids, attention_mask và token_type_ids. Một số biến thể không dùng token_type_ids; văn bản thô cần tokenizer trước.
VOAI|21|D|NLP|nlp-gpt|Sinh câu trả lời dựa trên đoạn văn|Trong các lựa chọn của đề, instruction-tuned GPT-3.5/GPT-4 cùng prompt chứa context phù hợp hơn cho QA sinh văn bản. Đây là so sánh trong đề, không khẳng định model mới nhất hiện nay.
VOAI|22|B|DL|dl-normalization|Dropout làm validation giảm mạnh|Thử giảm xác suất dropout để giảm regularization quá mức; kiểm tra eval mode trước khi đánh giá.
VOAI|23|B|NLP|nlp-bert|Cải thiện hiểu ngữ cảnh|BERT dùng contextual embeddings và attention. BoW/TF-IDF/one-hot không mô hình hóa ngữ cảnh linh hoạt như vậy.
VOAI|24|B|ML|ml-knn|Định nghĩa dự đoán 1-NN|Tìm (a*,y*)=argmin d(x,a) trong tập train, rồi trả NHÃN y*. Không đo khoảng cách với y và không trả a*.
VOAI|25|C|ML|ml-knn|k-NN đa lớp: q=(6,2,6)|Bình phương khoảng cách: S7=2, S8=5, S5=25, S1=52, S6=30, S4=30, S2=51, S3=52. Ba gần nhất S7,S8,S5 có2 Xanh lá và1 Xanh dương → Xanh lá.
VOAI|26|C|CV|cv-convolution|Feature map phát hiện cạnh|Bản đồ thể hiện cả các nét ngang và dọc sáng rõ, phù hợp cross directional edges, hơn là chỉ cạnh ngang hay color blobs.
VOAI|27|A|CV|cv-convolution|Output Conv2D: same, stride2|Keras mặc định NHWC. Input(1,32,32,3), filters32, same,stride2 → (1,ceil32/2,ceil32/2,32)=(1,16,16,32).
VOAI|28|D|NLP|nlp-word2vec|Mục đích negative sampling|Thay full-vocabulary objective bằng số nhỏ bài toán nhị phân, giảm chi phí với vocabulary lớn.
VOAI|29|D|DL|dl-optimizers|Adam bị plateau|Giảm LR/scheduler hoặc thử optimizer khác sau khi kiểm tra pipeline. Không cần reset toàn bộ model ngay.
VOAI|30|C|DL|dl-contrastive|Self-supervised learning|Augmentation và contrastive loss là cách phổ biến để tự tạo positive pairs. Không phải mọi self-supervised method đều contrastive: MLM cũng là self-supervised.
VOAI|31|A|ML|ml-knn|Vì sao k-NN cần scaling?|Tránh feature thang đo lớn chi phối khoảng cách. Scaling không nhất thiết đưa dữ liệu về[0,1]; standardization có thể âm hoặc lớn hơn1.
VOAI|32|C|CV|cv-pooling|Tính Average Pooling|Cửa sổ đầu3×3 có tổng10+20+30+50+60+70+90+100+110=540. Trung bình540/9=60. Stride2 quyết định vị trí cửa sổ tiếp theo.
VOAI|33|A|CV|dl-training|Lấy feature với fc=Identity|model.fc đã thay bằng Identity nên model(x) chạy toàn backbone, avgpool, flatten và trả B×2048. Gọi riêng avgpool(x) trên ảnh thô không đúng.
VOAI|34|B|CV|dl-training|Giới hạn của transfer learning|Fine-tuning không bảo đảm loại bỏ hoàn toàn domain shift từ ảnh tự nhiên sang ảnh viễn thám. Số tham số cập nhật chỉ giảm nếu freeze một phần.
VOAI|35|B|CV|cv-convolution|Kích thước convolution không padding|Mỗi trục cho floor((m−k)/2)+1 và floor((n−k)/2)+1. Phải có floor và +1.
VOAI|36|C|CV|cv-classification|Head của ViT classification|Biểu diễn CLS/pooling đưa qua classifier tuyến tính/MLP để tạo logits; softmax đổi sang xác suất. Khi dùng CE trong PyTorch, không cần softmax thủ công.
VOAI|37|C|ML|ml-tree|Tính entropy Passed|Có4 mẫu T và2 mẫu F. H=−(4/6)log₂(4/6)−(2/6)log₂(2/6)≈0.9183, gần0.92.
VOAI|38|C|DL,CV|dl-activation|Tính cross-entropy bằng ln|Nhãn[0,1], p=[.3,.7]: CE=−ln(.7)≈0.356675 →0.357.
VOAI|39|A|CV|dl-training|Tăng tốc inference|Trong các lựa chọn, chuyển sang backbone nhỏ hơn như MobileNet có thể giảm latency; cần kiểm tra accuracy và benchmark trên thiết bị đích.
VOAI|40|A|DL|dl-training|Shuffle giữa các epoch|Xáo trộn thứ tự train giúp mini-batch bớt phụ thuộc thứ tự cố định. Với dữ liệu chuỗi có trạng thái cần xử lý riêng.
VOAI|41|D|NLP|nlp-word2vec|Chọn mẫu âm SGNS|Lấy ngẫu nhiên từ vocabulary theo noise distribution, thường unigram mũ3/4, không phải chỉ lấy từ gần nghĩa.
VOAI|42|A|ML|ml-kmeans|Chọn trong 50 lần chạy K-means|Cùng dữ liệu và K, chọn kết quả có mean squared distance/inertia nhỏ nhất trong các nghiệm hội tụ.
VOAI|43|B|CV,DL|cv-convolution|Trainable parameters và FLOPs ResNet|Mỗi conv512→512,k3 có512²·9=2,359,296 weights. Hai conv:4,718,592≈4.7M. MACs=49·4,718,592=231,211,008; FLOPs≈462,422,016≈0.46G.
VOAI|44|D|DL|dl-optimizers|AdaGrad, RMSProp, Adam|Chúng dùng thống kê gradient để điều chỉnh learning rate hiệu dụng theo từng tham số.
VOAI|45|B|DL|dl-optimizers|Mini-batch quá nhỏ|Gradient estimate nhiễu hơn nên loss/updates có thể dao động. Không suy tuyệt đối rằng batch nhỏ luôn làm generalization kém.
VOAI|46|C|ML|ml-tree|Chống overfit decision tree|Giới hạn depth, tăng min leaf samples và pruning đều giảm complexity. Ép mọi lá thuần có thể làm cây quá sâu.
VOAI|47|B|DL|dl-mlp|Tính đầu ra nơ-ron|Weighted sum=1·4+4·8+3·5=51. Activation tuyến tính hệ số3 →153.
VOAI|48|D|DL|dl-backprop|Gradient tại gốc tọa độ|f=2x²−3y²+4y+10 ⇒ ∇f=(4x,−6y+4). Tại(0,0) được(0,4).
VOAI|49|D|DL|dl-activation|Lớp hiếm không được dự đoán|Weighted loss tăng đóng góp lớp hiếm; cũng có thể xem sampling và threshold. Không xóa lớp hiếm khỏi bài toán.
VOAI|50|C|CV|dl-training|Fine-tune MobileNetV2 với ít dữ liệu|Bắt đầu freeze các tầng đầu/backbone và train head giúp tận dụng feature pretrained, giảm số weights cần cập nhật.
VOAI|51|D|DL|dl-training|Xử lý GPU OOM|Giảm micro-batch và dùng gradient accumulation để giữ effective batch; có thể thêm mixed precision/checkpointing.
VOAI|52|D|ML|ml-foundations|Thuật toán unsupervised|K-means không cần nhãn. Decision tree, Ridge và Naive Bayes trong lựa chọn đều học supervised.
VOAI|53|D|ML|ml-knn|k-NN làm task nào?|Classification lấy vote; regression lấy trung bình/trọng số target của hàng xóm.
VOAI|54|D|DL,CV|cv-pooling|Mục đích augmentation|Cải thiện generalization bằng biến đổi bảo toàn nhãn; không tự giảm số tham số hay đảm bảo train nhanh hơn.
VOAI|55|B|NLP|nlp-preprocessing|Output BertTokenizer|encode_plus trả input_ids, attention_mask và có thể token_type_ids tùy cấu hình. Tokenizer hỗ trợ batch qua giao diện phù hợp.
VOAI|56|B|DL|dl-backprop|Khởi tạo mọi weights bằng0|Các nơ-ron cùng tầng đối xứng, nhận gradient giống nhau và không học các feature khác nhau. Bias bằng0 thường vẫn hợp lý nếu weights ngẫu nhiên.
VOAI|57|A|CV|cv-detection|Vai trò anchors trong SSD|Default boxes định nghĩa trước scales/aspect ratios; head học offsets và class scores tương ứng.
VOAI|58|A|ML,CV|ml-evaluation|Đọc hai confusion matrices|Train đúng1810/1864≈97.1%; test đúng285/400=71.25%. Khoảng cách lớn gợi ý overfitting; cũng nên kiểm tra shift/leakage, không thể quy mọi chênh lệch cho một nguyên nhân duy nhất.
VOAI|59|C|ML|ml-tree|Ý nghĩa entropy cao|Các lớp phân bố tương đối đều nên nút kém thuần. Entropy0 khi chỉ có một lớp.
VOAI|60|B|DL,CV|cv-pooling|Thêm Gaussian noise khi train|Học bất biến với nhiễu nhỏ, cải thiện robustness/generalization nếu cường độ phù hợp; không bảo đảm accuracy luôn tăng.
VOAI|61|D|DL|dl-generative|GAN tạo toàn ảnh xám|Mất cân bằng G/D hoặc huấn luyện bất ổn là lời giải thích phù hợp nhất trong các lựa chọn; cần kiểm tra preprocessing/activation và sample diversity để chẩn đoán thật.
VOAI|62|A|NLP|nlp-bert|Từ khóa tốt nhưng ngữ cảnh kém|Dùng contextual encoder như BERT để biểu diễn token theo ngữ cảnh và quan hệ giữa tokens.
VOAI|63|B|DL|ml-generalization|Giảm overfitting mạng sâu|Dropout/weight decay regularize model. Đồng thời theo dõi validation và cân nhắc early stopping/augmentation.
VOAI|64|A|DL|ml-generalization|Train tăng, validation dao động|Phần overfitting trongA hợp lý nhất. Tuy nhiên chỉ shuffle validation không sửa được overfitting; cần kiểm tra tập validation đủ lớn, representative và eval mode.
VOAI|65|B|NLP|nlp-bert|Fine-tune BERT classification|Thêm/thay task head phân loại trên biểu diễn[CLS] và cập nhật head/encoder phù hợp; không bắt buộc train tokenizer mới.
VOAI|66|A|DL|dl-optimizers|Learning rate quá cao|Update có thể vượt qua vùng tối ưu, dao động hoặc phân kỳ.
VOAI|67|!BD|ML|ml-foundations|Validation và test khác nhau thế nào?|B chính xác về vai trò chọn siêu tham số vs đánh giá cuối. D cũng mô tả thời điểm dùng thường gặp. Các lựa chọn chồng lấn nên bỏ chấm tự động; test không được dùng để tune.
VOAI|68|D|ML|ml-ensemble|Hàm hồi quy Random Forest|Lấy trung bình dự đoán các cây: y(x)=1/R·Σgᵢ(x). Không lấy max hay cộng mà không chia R.
VOAI|69|C|NLP|nlp-word2vec|Tải Word2Vec pretrained|KeyedVectors.load_word2vec_format(path) đọc định dạng Word2Vec; binary=True nếu file ở định dạng nhị phân tương ứng.
VOAI|70|A|DL|dl-activation|Đầu vào CrossEntropyLoss|Đưa raw logits làm đối số đầu. Loss đã kết hợp log-softmax với NLL; không softmax hai lần.
VOAI|71|A|DL|ml-generalization|Train loss giảm, val loss tăng|Dấu hiệu overfitting điển hình. Theo dõi checkpoint tốt nhất trên validation và regularize.
VOAI|72|D|CV|cv-segmentation|Loss cho segmentation lệch lớp|Dice trực tiếp tối ưu overlap; Focal giảm trọng số easy negatives. Có thể dùng CE có trọng số hoặc CE+Dice tùy dữ liệu.
VOAI|73|D|CV,DL|cv-classification|Đọc code identity block ResNet|Dòng21 Add([X_shortcut,X]) thực hiện residual sum. Dòng8 chỉ lưu shortcut. Cách gọi ba cặp Conv–BN–ReLU trongD hơi giản lược: ReLU cuối nằm sau phép cộng.
VOAI|74|B|NLP,DL|dl-attention|Attention làm gì?|Tạo biểu diễn bằng tổng có trọng số của các value theo độ tương hợp Q–K. Position encoding đảm nhiệm thông tin thứ tự riêng.
VOAI|75|B|CV|cv-segmentation|Nối skip U-Net theo trục nào?|Concat theo channel: NHWC dùng axis=−1, NCHW dùng dim=1. Nối batch không hợp nhất feature cùng mẫu.
VOAI|76|B|NLP|nlp-gpt|Khái niệm LLM|Trong các lựa chọn, mô hình DL train trên nhiều văn bản với next-token objective là mô tả đúng cho causal LLM phổ biến; phạm vi language model rộng hơn có cả masked models.
VOAI|77|B|CV,DL|dl-diffusion|Stable Diffusion thuộc họ nào?|Latent diffusion: khử nhiễu trong latent và decode ra ảnh. Có autoencoder bên trong nhưng framework sinh là diffusion.
VOAI|78|A|DL|ml-generalization|Metric cho early stopping|Theo dõi validation loss/accuracy hoặc metric phù hợp task, với patience. Không dùng test để quyết định thời điểm dừng.
VOAI|79|B|DL|dl-training|Chuyển model lên GPU|model.to('cuda'), rồi chuyển input/target đến cùng device. Cần CUDA khả dụng.
VOAI|80|D|ML|ml-linear|Tính MSE tám mẫu|Bình phương sai số:9,4,25,4,1,4,9,4. Tổng60, chia8 được7.5.
VOAI|81|D|NLP|nlp-llm-systems|Vai trò LangChain|Orchestrate model calls, retrieval, tools và agent workflows. Không phải một model ngôn ngữ.
VOAI|82|!|ML|ml-logistic|Thuộc tính weights LogisticRegression|Tên đúng trong scikit-learn là model.coef_ (có underscore cuối). Đề in model.coef không có underscore, nên không có lựa chọn đúng theo API. D có thể là ý định của người ra đề nhưng không nên học cú pháp sai.
VOAI|83|B|ML,CV|ml-density|Tính silhouette trên ảnh vệ tinh|a=.35; b=min(.60,.45)=.45. s=(.45−.35)/.45=2/9≈.222. Không lấy trung bình .60 và .45.
VOAI|84|D|DL|dl-backprop|Khởi tạo không phù hợp|Scale weights có thể làm gradient mất hoặc nổ qua các layers. Xavier/He là các chiến lược thường dùng.
VOAI|85|B|ML,CV|ml-evaluation|Metric ảnh mất cân bằng|Macro-F1 trung bình đều F1 từng lớp, làm rõ chất lượng lớp hiếm. AUC cũng hữu ích tùy setup nhưngB là lựa chọn trực tiếp nhất.
VOAI|86|B|CV|dl-training|Bước triển khai model|Trong lựa chọn, export ONNX/TensorRT hợp lý cho deployment. Thực tế còn cần test representative, latency, memory và kiểm tra accuracy sau chuyển đổi.
VOAI|87|C|CV|dl-training|Ảnh hỏng trong dataset|Catch lỗi decode/load, ghi nhận và bỏ qua/quarantine ảnh hỏng có kiểm soát; không bỏ toàn thư mục hoặc che giấu tỷ lệ lỗi lớn.
VOAI|88|C|DL|dl-normalization|Cú pháp dropout PyTorch|nn.Dropout(p=.5) tạo module dropout. nn.Dropout2d dành cho channel-wise dropout của feature maps, không phải thay thế chung.
VOAI|89|C|ML|ml-evaluation|Không bỏ sót gói tin đe dọa|Recall=TP/(TP+FN); ưu tiên giảm FN. Vẫn phải cân nhắc false positives khi chọn ngưỡng triển khai.
VOAI|90|B|ML|ml-tree|Model ít nhạy scaling|Decision tree dùng thứ tự/ngưỡng từng feature; chuẩn hóa đơn điệu tăng không đổi các phép chia tương ứng, bỏ qua sai số số học.
VOAI|91|C|NLP|nlp-word2vec|Mục tiêu CBOW|Dùng các từ context để dự đoán từ trung tâm. Skip-gram làm chiều ngược lại.
VOAI|92|C|DL,CV|dl-contrastive|Mục tiêu contrastive learning|Kéo hai views cùng ảnh gần, tách views của ảnh khác; không kéo mọi mẫu về một điểm.
VOAI|93|D|DL|dl-optimizers|SGD và mini-batch|SGD theo định nghĩa nghiêm dùng một mẫu/update; mini-batch dùng nhóm mẫu. Thực tế tên SGD optimizer còn được dùng khi batch>1.
VOAI|94|D|NLP,ML|ml-knn|Cosine similarity giữa word vectors|cos(w1,w2)≈.9833; cos(w1,w3)≈.8391; cos(w1,w4)≈.1234. w2 gần nhất theo cosine. Cần normalize bằng cả hai norm.
VOAI|95|D|DL|dl-generative|Hai mạng của GAN|Generator tạo mẫu; discriminator phân biệt real/fake. Không phải detector/segmentor hay encoder/decoder theo định nghĩa GAN.
VOAI|96|!|ML|ml-generalization|Nguyên nhân overfitting|Nhiễu dữ liệu (D) là nguyên nhân có thể; model không phù hợp/quá linh hoạt (A) cũng có thể. Các lựa chọn rộng và không loại trừ nhau, nên không có đáp án đơn duy nhất được suy ra chắc chắn.
VOAI|97|C|DL|dl-generative|Autoencoder cho ảnh mờ|Latent quá nhỏ hoặc regularization quá mạnh làm mất chi tiết; reconstruction MSE cũng có xu hướng trung bình hóa các kết quả có thể.
VOAI|98|B|NLP,CV|dl-diffusion|Khả năng DALL·E|Text-to-image: sinh ảnh từ mô tả. Không cần giả định mọi phiên bản DALL·E có cùng architecture.
VOAI|99|C|NLP|nlp-preprocessing|Mục đích bỏ stopwords|Trong pipeline truyền thống, giảm feature ít thông tin, tập trung từ nội dung. Không nên áp tùy tiện với pretrained Transformer hay bỏ từ phủ định quan trọng.
VOAI|100|D|ML|ml-svm|Tính nhãn SVM|Điểm index0=(1,2): wᵀx+b=2·1−3·2+1=−3, sign=−1.
VAIC|1|A|ML|ml-linear|Đa cộng tuyến hoàn hảo|Các feature tương quan±1 nên phụ thuộc affine hoàn hảo. Một cột X1 cùng intercept biểu diễn thông tin tuyến tính của cả ba;A là lựa chọn đơn giản nhất, không phảiD hay Ridge nhiều biến.
VAIC|2|C|ML|ml-tree|Training accuracy của cây mèo|Nhánh Coloured=No chứa1Cat,3NotCat nên đoán NotCat và sai1 mẫu. Các nhánh còn lại phân loại đúng4 mẫu. Tổng7/8=87.5%.
VAIC|3|C|ML|ml-evaluation|Test accuracy của cây mèo|Mẫu(No,Yes,Yes) có nhãnCat nhưng vào lá đa sốNotCat. Ba mẫu khác đúng, nên3/4=75%.
VAIC|4|B|ML|ml-generalization|Nhận xét train–test gap|Train87.5%,test75% gợi ý overfitting, làB trong các lựa chọn. Chỉ4 test samples nên đây là dấu hiệu yếu, chưa chứng minh chắc nguyên nhân.
VAIC|5|B|ML|ml-generalization|Ba fold nhưng không refit|Giữ nguyên cây: đúng7 train+3 test=10/12=83.33%. Đó không phải cross-validation độc lập đúng chuẩn vì không huấn luyện lại trên từng fold.
VAIC|6|C|CV|cv-convolution|Độ phức tạp convolution|Một channel input: M output filters × khoảngWH vị trí ×d² phép nhân mỗi vị trí →O(MWHd²). Nhiều channels phải nhân thêmCin.
VAIC|7|C|DL|dl-activation|Activation output classification|Sigmoid cho nhãn0/1; tanh có thể dùng khi mã hóa nhãn−1/+1. C là tốt nhất trong các lựa chọn, nhưng thực hành phải chọn activation cùng loss phù hợp.
VAIC|8|A|DL|dl-activation|Thiết kế hàm chặn[-1,1]|max(−1,min(1,x)): chặn trên tại1 rồi chặn dưới tại−1. Đây là hardtanh.
VAIC|9|A|CV|cv-detection|Anchors Faster R-CNN|Box tham chiếu trải trên feature map với nhiều scales/aspect ratios. RPN học objectness và offsets từ các anchors này.
VAIC|10|A|CV|cv-iou|Vì sao GIoU hữu ích khi box không giao?|Thành phần phạt dựa trên enclosing box còn phụ thuộc hình học khi IoU=0, tạo tín hiệu gradient hữu ích. Không bảo đảm luôn giảm L2 giữa tâm nhưC.
VAIC|11|D|CV|cv-segmentation|Mask R-CNN thêm gì?|Thêm mask head song song và thay RoIPool bằng RoIAlign; vẫn giữ proposals, class và box regression.
VAIC|12|B|CV|cv-segmentation|Vai trò skip U-Net|Hợp nhất high-resolution encoder features với decoder để phục hồi chi tiết vị trí. Không chỉ là identity residual nhằm tối ưu sâu.
VAIC|13|A|NLP|nlp-word2vec|Mục tiêu SGNS|Binary logistic discrimination giữa cặp target-context thật và noise pairs. Không phải exact full-vocabulary softmax hay MLM.
VAIC|14|B|ML,DL|dl-mlp|Tổ hợp lồi của điểm perceptron dương|wᵀ(Σαᵢxᵢ)+b=Σαᵢ(wᵀxᵢ+b)>0 khi αᵢ>0,tổng1 và mọi logits dương. Không thể đổi sang âm.
VAIC|15|B|ML,DL|dl-mlp|Lấy thêm điểm âm trên đoạn thẳng?|Nếu hai đầu đã phân loại âm đúng thì cả đoạn thẳng cũng âm theo tính lồi của nửa không gian. Các điểm đó không tạo ràng buộc lỗi mới; nên ưu tiên thông tin ngoài vùng đã biết.
VAIC|16|B|NLP|nlp-word2vec|Phân phối noise của Word2Vec|Unigram raised to a power, thường3/4, cân bằng tương đối tần suất phổ biến và hiếm.
VAIC|17|B|CV|cv-map|COCO mAP và định vị chính xác|B giữ AP tốt ở các ngưỡng IoU cao theo xu hướng đề mô tả, nên được lợi khi average .50:.05:.95. Không chỉ dùngAP50 hay trung bình hai đầu.
VAIC|18|A|NLP,ML|ml-pca|Giảm chiều embedding cho Seq2Seq|Giảm quá mạnh mất capacity/thông tin; giảm vừa phải có thể regularize và tăng tốc. PCA không tự có nghĩa xóa toàn bộ position information.
VAIC|19|C|CV|cv-classification|ViT tạo image tokens|Chia patch không chồng lắp, flatten, linear projection, thêm positional information. Bản gốc không cần SIFT hay CNN backbone.
VAIC|20|C|DL|dl-attention|Chia√dk trong attention|Dot product có variance tăng theo dk; chia√dk giúp tránh softmax bão hòa và ổn định gradient. Đề in thiếu biểu thức chia nhưng đây là mục tiêu chuẩn.
VAIC|21|D|CV,DL|cv-pooling|Trộn nhãn MixUp|Cùng hệ sốλ như trộn ảnh: ỹ=λyᵢ+(1−λ)yⱼ, tạo soft labels từ hai one-hot vectors.
VAIC|22|B|DL|dl-optimizers|AdamW và learning rate|B là mệnh đề đúng nhất: Adam+L2 đi qua adaptive moments. A,C sai vì AdamW chuẩn vẫn co theo(1−ηλ); muốn giữ shrinkage khi đổiη phải chỉnhλ đểηλ không đổi. Đáp án này là lời giải biên soạn, không phải key chính thức.
VAIC|23|D|NLP|nlp-word2vec|Ý tưởng GloVe|Weighted least-squares trên log co-occurrence counts toàn cục, có biases và weighting function.
VAIC|24|E|NLP|nlp-bert|Pretraining BERT gốc|BERT gốc dùng MLM+NSP. B ghi SOP (ALBERT) nên sai; các phương án khác cũng không phải cặp mục tiêu gốc →E.
VAIC|25|A|CV|cv-segmentation|Loss segmentation lệch pixel|Dice/IoU-style loss trực tiếp tối ưu overlap, thường hữu ích cho foreground hiếm. Không bảo đảm luôn hơn mọi weighted CE ở mọi dataset.
VAIC|26|B|DL|dl-contrastive|Giảm temperature InfoNCE|Softmax sắc hơn, negative có similarity cao chiếm trọng số tương đối lớn hơn; gradient không giữ nguyên nhưD.
VAIC|27|B|NLP,ML|ml-evaluation|Metric văn bản mất cân bằng|Macro-F1 cân đều các lớp và làm rõ chất lượng lớp thiểu số. Micro-F1 của single-label multiclass đầy đủ bằng accuracy.
VAIC|28|C|NLP|nlp-bert|Kiến trúc BERT|Transformer encoder-only với bidirectional self-attention. Không phải causal decoder, encoder–decoder hay RNN.
VAIC|29|!|ML|ml-bayes|Lỗi Bayes của mixture|Dữ kiện chỉ cho max trên(x,y) của posterior từng nguồn, chưa đủ xác định expectation hay sự xung đột giữa các nguồn. 25% là cận dưới từ0.5·0.1+0.25·0.4+0.25·0.4; chỉ là đáp án dự kiến nếu thêm giả định phù hợp. Không chấm tự động để tránh học sai.
'''
rows={}
for row in DATA.strip().splitlines():
 source,num,answer,topics,lesson,title,explanation=row.split('|')
 rows[(source,int(num))]=dict(answer=list(answer.replace('!','')),scorable='!' not in answer,topics=topics.split(','),lesson=lesson,title=title,explanation=explanation)
raw=json.loads(Path('exam-extracted/questions-raw.json').read_text(encoding='utf-8'))
for q in raw:
 q.update(rows[(q['source'],q['number'])])
 q['options']=list('ABCD' if q['source']=='VOAI' or q['number'] in [6,7,8,16,29] else 'AB' if q['number'] in [14,15] else 'ABCDE')
 q['raw']=re.sub(r'Mã đề 006\s*Trang \d+/16','',q['raw']).replace('sE','sử').replace('thE','thử').replace('xE','xử').replace('cEa','cửa').replace('Ð','Đ')
 q['context']=[]
 if q['source']=='VAIC' and 2<=q['number']<=5:q['context']=['exams/vaic-context-train.webp','exams/vaic-context-tree.webp']
doc=pymupdf.open('real-test/VAIC 2025.pdf')
for pi,name,top,bottom in [(1,'train',170,780),(2,'tree',40,500)]:
 doc[pi].get_pixmap(matrix=pymupdf.Matrix(1.6,1.6),clip=pymupdf.Rect(40,top,doc[pi].rect.width-35,bottom)).pil_save('ai-exam/dist/exams/vaic-context-'+name+'.webp',format='WEBP',quality=87)
# Remove the large trailing blank area from the final VOAI question.
doc=pymupdf.open('real-test/CV gui cac so GDDT_Olympic Tri tue nhan tao.pdf');pg=doc[17]
# Use the extracted question position instead of a guessed top coordinate.
q100=next(q for q in raw if q['id']=='voai-100')
from PIL import Image
im=Image.open('ai-exam/dist/'+q100['images'][0])
# Restore the correct extraction top, then crop after the last answer row.
starts=[l for b in pg.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] if any('T55' in s['text'] for s in l['spans'])]
if starts:
 top=starts[0]['bbox'][1]-3
 pg.get_pixmap(matrix=pymupdf.Matrix(1.65,1.65),clip=pymupdf.Rect(35,top,pg.rect.width-30,310)).pil_save('ai-exam/dist/exams/voai-100-18.webp',format='WEBP',quality=87)
Path('ai-exam/dist/questions.js').write_text('const QUESTIONS='+json.dumps(raw,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
print(f'{len(raw)} questions, {sum(q["scorable"] for q in raw)} scored; all have explanations and original crops')
