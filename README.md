# Survival Game AI - Nhóm 25
# Giới thiệu
Trò chơi này được thiết kế theo cảm hứng từ game sinh tồn kết hợp hành động tiêu diệt quái vật. Người chơi sẽ nhập vai vào một nhân vật chính và điều khiển anh ta di chuyển trong một bản đồ 2D với góc nhìn từ trên xuống. Nhiệm vụ chính của người chơi là cố gắng sinh tồn trước những đợt tấn công dồn dập và không ngừng nghỉ từ các loại quái vật. Để làm được điều đó, người chơi cần linh hoạt tránh né sự truy đuổi của kẻ thù, tận dụng hệ thống vũ khí có khả năng tấn công tự động để tiêu diệt chúng, đồng thời thu thập các điểm kinh nghiệm rơi ra để thăng cấp. Mỗi lần lên cấp, người chơi sẽ có cơ hội nâng cấp trang bị hiện tại, qua đó tăng khả năng sống sót lâu hơn. Mục tiêu cuối cùng của trò chơi là kéo dài thời gian sinh tồn càng lâu càng tốt và đạt được số điểm cao nhất có thể.

# Các thuật toán sử dụng:
Trí tuệ nhân tạo thông minh
Game tích hợp các thuật toán AI đa dạng để điều khiển các nhân vật hoặc kẻ thù trong môi trường sinh tồn, bao gồm:

# And-Or Search:
Thuật toán sử dụng tìm kiếm đệ quy theo chiều sâu để khám phá cây AND-OR. Nó xử lý chu kỳ bằng cách trả về thất bại nếu trạng thái hiện tại trùng với trạng thái trên đường đi từ gốc, tránh lặp vô hạn, nhưng không kiểm tra trùng lặp trên các đường đi khác để tăng hiệu quả. Thuật toán đảm bảo kết thúc trong không gian trạng thái hữu hạn, vì mọi đường đi sẽ dẫn đến mục tiêu, điểm chết, hoặc trạng thái lặp lại.
AND-OR graphs có thể được khám phá bằng breadth-first hoặc best-first. Hàm heuristic được điều chỉnh để ước lượng chi phí của giải pháp có điều kiện thay vì chuỗi hành động. Một phiên bản tương tự A* tồn tại để tìm giải pháp tối ưu, giữ nguyên khái niệm admissibility, đảm bảo hiệu quả trong việc tìm kiếm đường đi tốt nhất trong không gian trạng thái phức tạp
Trong trò chơi được mô tả, các thực thể (entities) như kẻ thù (zombies, skeletons, ghouls) cần di chuyển từ vị trí hiện tại đến vị trí của người chơi (target). Mỗi loại kẻ thù sử dụng một thuật toán tìm đường khác nhau, được xác định trong file spawner.py qua từ điển ENEMY_TYPE_TO_PATHFIND. Cụ thể, loại kẻ thù STRONG_SKELETON được gán sử dụng lớp AOSearching, tức là thuật toán AND-OR search.
# Backtracking
Thuật toán sử dụng tìm kiếm đệ quy theo chiều sâu, chọn một biến chưa gán, thử từng giá trị trong miền của biến, và gọi đệ quy để mở rộng gán. Nếu giá trị dẫn đến giải pháp, trả về kết quả; nếu thất bại, khôi phục trạng thái và thử giá trị tiếp theo. Nếu không giá trị nào thành công, trả về thất bại. Cây tìm kiếm được minh họa trong bài toán tô màu bản đồ Úc, cho thấy cách gán giá trị từng bước.
Backtracking search giải quyết các bài toán ràng buộc (CSPs) khi lan truyền ràng buộc vẫn để lại biến với nhiều giá trị. Trong CSPs với n biến và miền giá trị kích thước d, tìm kiếm theo chiều sâu thông thường tạo cây tìm kiếm có tất cả gán hoàn chỉnh ở độ sâu n, nhưng nhân tố phân nhánh ở mức đầu là nd, rồi (n-1)d, dẫn đến n!. dn lá, dù chỉ có dn gán hoàn chỉnh, gây lãng phí tài nguyên tính toán nghiêm trọng.
Trong trò chơi, các thực thể kẻ thù (như zombies, skeletons) cần di chuyển từ vị trí hiện tại đến vị trí người chơi (target) trên một bản đồ có các chướng ngại vật (collisions). File spawner.py chỉ định rằng loại kẻ thù WEAK_SKELETON sử dụng lớp BackTrackCSP (xem từ điển ENEMY_TYPE_TO_PATHFIND), tức là thuật toán Backtracking Search được áp dụng để điều hướng cho loại kẻ thù.
Backtracking Search được sử dụng để giải bài toán tìm đường được mô hình hóa như một bài toán ràng buộc (Constraint Satisfaction Problem - CSP), trong đó các biến là các điểm di chuyển (edges) và các ràng buộc đảm bảo đường đi không va chạm với chướng ngại vật và dẫn đến mục tiêu.
# Q-Learning:
Q-Learning là thuật toán RL tập trung vào đánh giá chất lượng cặp trạng thái-hành động Q(s, a), tìm policy tối ưu để tối đa hóa phần thưởng dựa trên Bellman Equation: 
Q(s,a) = R(s,a) + γ∑s’ ​ P(s, a, s′) maxa’​ Q(s′, a′), với R(s,a) là phần thưởng tức thời, γ là hệ số chiết khấu, và maxa’​ Q(s′, a′) là giá trị tối ưu từ trạng thái tiếp theo. Q-Learning cập nhật Q(s′, a′) bằng công thức: Q(s,a) ← (1 − α)Q(s, a) + α(R(s, a) + γ maxa’​ Q(s′, a′)), trong đó α là tỷ lệ học. Agent cân bằng giữa khai thác (chọn hành động tốt nhất) và khám phá (thử ngẫu nhiên) để học hiệu quả.
Thuật toán Q-Learning được ứng dụng trong file pathfind.py thông qua lớp QLearningPathFind, một thành phần tìm đường (pathfinding) cho các thực thể trong trò chơi sinh tồn. Dưới đây là cách thuật toán này được áp dụng vào bài toán tìm đường, dựa trên các tài liệu được cung cấp, đặc biệt là liên kết với file spawner.py và lý thuyết Q-Learning đã tóm tắt trước đó.
Trong trò chơi, các thực thể kẻ thù (như zombies, skeletons, ghouls) cần di chuyển từ vị trí hiện tại đến vị trí của người chơi (target) trên một bản đồ có các chướng ngại vật. File spawner.py chỉ định rằng loại kẻ thù GHOUL sử dụng lớp QLearningPathFind (xem từ điển ENEMY_TYPE_TO_PATHFIND), tức là thuật toán Q-Learning được áp dụng để điều hướng cho loại kẻ thù này.
Q-Learning - thuật toán học tăng cường (reinforcement learning), được sử dụng để giúp kẻ thù học cách chọn hành động tối ưu (hướng di chuyển) dựa trên trạng thái hiện tại và mục tiêu, tối đa hóa phần thưởng tích lũy mà không cần mô hình môi trường đầy đủ.
# BFS
Thuật toán tìm kiếm theo chiều rộng là một phương pháp duyệt và tìm kiếm trên đồ thị, trong đó các đỉnh ở mức nông hơn được ưu tiên khám phá trước khi chuyển sang mức sâu hơn. BFS bắt đầu từ một đỉnh gốc, sau đó mở rộng dần đến các đỉnh kề theo từng mức độ sâu, sử dụng hàng đợi FIFO để đảm bảo thứ tự xử lý.
BFS hoạt động bằng cách khởi tạo từ một đỉnh gốc, thêm đỉnh này vào hàng đợi và đánh dấu là đã thăm, sau đó lặp lại các bước: lấy đỉnh đầu tiên từ hàng đợi, xử lý, rồi thêm các đỉnh kề chưa thăm vào hàng đợi. Quá trình này tiếp tục cho đến khi hàng đợi rỗng hoặc tìm được mục tiêu, đảm bảo các đỉnh ở cùng độ sâu được xử lý trước.
Đối với BFS trong trò chơi này, các thực thể kẻ thù (như zombies, skeletons, ghouls) cần di chuyển từ vị trí hiện tại đến vị trí của người chơi (target) trên một bản đồ có các chướng ngại vật. File spawner.py chỉ định rằng loại kẻ thù WEAK_ZOMBIE có thể sử dụng lớp UninformedPathFind (xem từ điển ENEMY_TYPE_TO_PATHFIND), tức là thuật toán BFS được áp dụng để điều hướng cho loại kẻ thù này.
Thuật toán được sử dụng để tìm đường đi ngắn nhất từ điểm bắt đầu (start) đến điểm đích (end) trong không gian trạng thái được định nghĩa bởi bản đồ điều hướng (nav_map), đảm bảo tránh các chướng ngại vật và phù hợp với các bài toán tìm kiếm không thông tin (uninformed search).
# Thuật toán A*
Thuật toán A* là một phương pháp tìm kiếm có thông tin phổ biến, thuộc nhóm tìm kiếm ưu tiên tốt nhất, sử dụng hàm đánh giá f(n) = g(n) + h(n), trong đó g(n) là chi phí đường đi từ trạng thái ban đầu đến đỉnh n, và h(n) là chi phí ước lượng từ n đến mục tiêu. A* hướng đến việc tìm đường đi tối ưu về chi phí, thường được áp dụng trong các bài toán như tìm đường đi ngắn nhất
Thuật toán hoạt động bằng cách ưu tiên mở rộng đỉnh có giá trị f(n) nhỏ nhất trên tập các đỉnh chưa duyệt, trong đó f(n) = g(n) + h(n) thể hiện chi phí ước lượng của đường đi tốt nhất qua n. Thuật toán đảm bảo tính hiệu quả bằng cách kết hợp thông tin chi phí thực tế và ước lượng, giúp giảm số đỉnh cần khám phá so với các phương pháp không có thông tin
Đối với thuật toán được ứng dụng trong trò chơi, các thực thể kẻ thù (như zombies, skeletons, ghouls) cần di chuyển từ vị trí hiện tại đến vị trí của người chơi (target) trên một bản đồ có các chướng ngại vật. File spawner.py chỉ định rằng loại kẻ thù WEAK_ZOMBIE có thể sử dụng lớp InformedPathFind (xem từ điển ENEMY_TYPE_TO_PATHFIND), tức là thuật toán A* được áp dụng để điều hướng cho loại kẻ thù này. Ngoài ra, tất cả các loại kẻ thù được thêm thành phần InformedPathFind mặc định trong hàm spawn, đảm bảo A* là một lựa chọn phổ biến cho pathfinding.
Mục đích của thuật toán tìm đường đi ngắn nhất từ điểm bắt đầu (start) đến điểm đích (end) trong không gian trạng thái, đảm bảo hiệu quả hơn so với các thuật toán không thông tin như BFS.
# Local Beam Search
Cơ sở lý thuyết chung của thuật toán đã nằm trong chương 1 nên trong phần này sẽ nêu lại ngắn gọn.
Thuật toán này là một phương pháp tìm kiếm thông minh, khác biệt với các thuật toán chỉ giữ một trạng thái duy nhất, khi nó theo dõi đồng k trạng thái trong bộ nhớ thay vì chỉ một. Thuật toán khởi đầu với k trạng thái được tạo ngẫu nhiên, sau đó tại mỗi bước, nó sinh ra tất cả các trạng thái kế tiếp từ các trạng thái hiện tại.
Thuật toán này có khả năng khai thác thông tin giữa các luồng tìm kiếm song song, không giống cách hoạt động độc lập của tìm kiếm khởi động lại ngẫu nhiên. Các trạng thái tạo ra các hậu duệ tốt sẽ hướng dẫn các trạng thái khác tập trung vào khu vực cụ thể nào đó, có thể xem như một tín hiệu rằng khu vực này có tiềm năng cao hơn. Điều này giúp thuật toán nhanh chóng từ bỏ các hướng tìm kiếm kém hiệu quả, tăng cường mức độ cho những nơi có tiến triển lớn qua đó nâng cao hiệu suất tổng thể
Đối với thuật toán được ứng dụng trong trò chơi, các thực thể kẻ thù (như zombies, skeletons, ghouls) cần di chuyển từ vị trí hiện tại đến vị trí của người chơi trên một bản đồ có các chướng ngại vật. File spawner.py chỉ định rằng loại kẻ thù STRONG_ZOMBIE sử dụng lớp LocalPathFind (xem từ điển ENEMY_TYPE_TO_PATHFIND), tức là thuật toán Local Beam Search được áp dụng để điều hướng cho loại kẻ thù này.
Mục đích của thuật toán là giữ một số lượng giới hạn (beam_width) các trạng thái tốt nhất tại mỗi bước, sử dụng heuristic để ưu tiên các trạng thái gần mục tiêu hơn, nhằm tìm đường đi khả thi từ điểm bắt đầu (start) đến điểm đích (end) một cách hiệu quả.

# Đội ngũ phát triển
Nhóm 25 - Trí Tuệ Nhân Tạo

# Thành viên:

+ Nguyễn Trí Lâm - 23110250
+ Trần Bá Thành - 23110320
+ Kinh Văn Việt - 23110363

# Phân công
| Thành viên       | Công việc            |
|------------------|----------------------|
| Nguyến Trí Lâm     | BFS, Backtrack    |
| Trần Bá Thành       | Q - Learning, And - Or search         |
| Kinh Văn Việt         | A*, Beam search       |
