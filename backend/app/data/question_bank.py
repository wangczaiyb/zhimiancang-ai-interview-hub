"""结构化面试题库种子数据（纯数据，不依赖 ORM 模型）。

字段说明：
  job_category   适用岗位大类，与 Job.category 对齐；"通用" 表示跨岗位通用
  question_type  PROFESSIONAL 专业题 / GENERAL 通用题 / STRESS 压力题
  skill_name     考察技能（通用题为"综合素养"）
  stage          面试阶段（专业基础 / 深度探究 / 项目深挖 / 系统设计 / 综合素养 / 压力应对）
  difficulty     EASY / MEDIUM / HARD
  text           题干
  reference_points  参考答案要点（逐题复盘时与候选人作答对照）
  hints          临场答题提示
  time_limit_sec 逐题建议限时（秒）

配比设计参考：专业题 : 通用题 : 压力题 = 5 : 3 : 2（可在组卷引擎按面试模式覆盖）。
"""

QUESTION_BANK_SEED = [
    # ================= === 后端开发 · Java 与并发 === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Java并发",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请结合底层机制说明 Java 中 volatile 关键字的作用原理。它能保证原子性吗？为什么？",
        "reference_points": [
            "可见性：写操作刷新主内存、读操作从主内存加载，依赖内存屏障（StoreLoad 等）禁止指令重排",
            "有序性：通过插入内存屏障建立 happens-before 关系，典型如双重检查锁单例必须加 volatile",
            "不保证原子性：i++ 是读-改-写三步，需用 AtomicInteger/synchronized/LongAdder",
            "适用场景：状态标志位、DCL 单例；不适用：计数、复合条件判断"
        ],
        "hints": "先讲内存模型与屏障，再明确区分可见性与原子性，最后给出适用场景"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Java并发",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "请聊聊 AQS 的核心设计思想。ReentrantLock 公平锁与非公平锁在实现上有什么区别，为什么默认选择非公平？",
        "reference_points": [
            "核心三要素：volatile int state 表示同步状态、CLH 变体的 FIFO 双向等待队列、模板方法式的 tryAcquire/tryRelease 由子类实现",
            "获取失败后通过 LockSupport.park 挂起线程，前驱节点出队或被唤醒后重试",
            "非公平锁在 tryAcquire 时先直接 CAS 抢一次，不检查队列；公平锁需 hasQueuedPredecessors 判断",
            "非公平性能更优：省去线程唤醒与上下文切换的窗口期，吞吐显著更高，代价是可能的队列饥饿"
        ],
        "hints": "建议画出 state + 队列的结构，再对比两种锁的源码分支差异"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Java并发",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "ThreadPoolExecutor 有哪些核心参数？生产环境中你如何确定线程池大小，为什么阿里规约禁止用 Executors 直接创建？",
        "reference_points": [
            "七大参数：corePoolSize、maximumPoolSize、keepAliveTime、unit、workQueue、threadFactory、RejectedExecutionHandler",
            "执行顺序：核心线程 → 队列 → 非核心线程 → 拒绝策略，注意与直觉不同的地方是先入队再扩容",
            "容量估算：CPU 密集型 N+1，IO 密集型 N×(1+等待时间/计算时间)，最终以压测 TP99 与 CPU 利用率校准",
            "Executors 风险：newFixedThreadPool/newSingleThreadExecutor 用无界 LinkedBlockingQueue 导致 OOM；newCachedThreadPool 允许 Integer.MAX_VALUE 线程数"
        ],
        "hints": "结合一个你实际调过的线程池参数与被压测出来的数据来说明"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Java并发",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "synchronized 的锁升级过程是怎样的？偏向锁、轻量级锁、重量级锁各自的适用场景与撤销代价是什么？",
        "reference_points": [
            "对象头 Mark Word 存储锁状态，升级路径：无锁 → 偏向锁 → 轻量级锁 → 重量级锁",
            "偏向锁：只有一个线程访问，记录线程 ID，再次进入只需比较，无 CAS 开销；批量重撤销/单线程撤销",
            "轻量级锁：多线程交替执行（无真正竞争），CAS 将 Mark Word 复制到栈帧 Lock Record，自旋尝试",
            "重量级锁：自旋超过阈值或竞争明显，膨胀为 monitor，依赖操作系统 mutex，线程阻塞唤醒代价高",
            "撤销代价：偏向锁撤销需要等到安全点（STW），因此在高并发交替竞争场景反而可能关闭偏向锁"
        ],
        "hints": "重点说清 CAS、自旋与内核态阻塞三者的成本梯度"
    },

    # ================= === 后端开发 · MySQL === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "MySQL",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "InnoDB 的聚簇索引与二级索引在底层组织上有什么区别？为什么通常建议使用自增主键？",
        "reference_points": [
            "B+ 树：叶子节点存数据、非叶子只存键，叶子间双向链表相连，层数即 IO 次数（3 层可支撑两千万行）",
            "聚簇索引叶子存整行数据，二级索引叶子存主键值，因此二级索引查询非覆盖字段需要回表",
            "覆盖索引（Using index）可避免回表；最左前缀决定联合索引可用性",
            "自增主键顺序追加，页分裂少、碎片低；UUID 随机插入导致频繁页分裂与写放大"
        ],
        "hints": "可以用一张 EXPLAIN 结果或一条真实慢 SQL 来佐证"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "MySQL",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "请说明 MySQL 的 MVCC 是如何实现的？在可重复读隔离级别下它能否完全解决幻读？",
        "reference_points": [
            "隐藏字段 trx_id、roll_pointer + undo log 版本链 + ReadView（m_ids/min_trx_id/max_trx_id/creator_trx_id）",
            "ReadView 生成时机：RC 每条语句生成一次，RR 事务首次快照读生成后复用",
            "RR 下快照读通过 MVCC 避免幻读，但当前读（for update / update）需要 Next-Key Lock（记录锁 + 间隙锁）来防止插入",
            "经典反例：事务 A 快照读 → 事务 B 插入并提交 → 事务 A 执行 update 命中新行后再快照读，会看到该行，说明并非绝对无幻读"
        ],
        "hints": "把快照读与当前读分开讨论，这是本题的关键区分点"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "MySQL",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "redo log、undo log、binlog 三者分别解决什么问题？两阶段提交为什么是必要的？",
        "reference_points": [
            "redo log：InnoDB 独有，WAL + 环形持久化，保证崩溃恢复与事务持久性（crash-safe）",
            "undo log：记录逻辑反向操作，支撑回滚与 MVCC 版本链",
            "binlog：Server 层归档日志，追加写，用于主从复制与数据恢复/闪回",
            "两阶段提交（prepare → 写 binlog → commit）保证 redo 与 binlog 逻辑一致，否则主从或恢复出的数据会不一致",
            "commit crash 时的恢复规则：redo 已 prepare 且 binlog 完整则提交，binlog 不完整则回滚"
        ],
        "hints": "从“如果只写一个日志会怎样”的角度反证两阶段提交的必要性"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "MySQL",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "订单表数据量增长到十亿级，你会如何做分库分表？请说明分片键选择、扩容迁移与非分片键查询的处理方案。",
        "reference_points": [
            "先评估垂直拆（按业务域）与水平拆（按行），并确认是否可用冷热分离/归档替代",
            "分片键选择：优先高频查询维度（如 user_id 保证“我的订单”单库查询），兼顾数据均匀与热点",
            "路由算法：取模（扩容需全量迁移）、范围（易热点）、一致性哈希/基因法（把 user_id 后几位嵌入 order_id 实现双维度路由）",
            "跨分片查询：异构索引表（ES / TiDB / 宽表）、全局二级索引、或走离线数仓",
            "扩容迁移：双写 + 全量刷 + 数据校验 + 灰度切读，中间件如 ShardingSphere 或自研路由层"
        ],
        "hints": "务必提到分布式 ID、跨库事务与分页排序这三类衍生难题"
    },

    # ================= === 后端开发 · Redis === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Redis",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "在高并发项目中你如何用 Redis 优化性能？缓存与数据库的一致性如何保障？",
        "reference_points": [
            "典型用法：热点数据缓存、分布式会话、计数器/排行榜（ZSet）、分布式锁、库存预扣（Lua 原子）",
            "一致性主流方案是 Cache Aside：读时回填，写时先更新 DB 再删除缓存",
            "为什么删不是更新：并发写导致旧值覆盖新值；且更新缓存浪费算力于低频使用字段",
            "延迟双删 / Canal 订阅 binlog 异步失效，把不一致窗口收敛到毫秒级",
            "兜底：缓存设置合理 TTL、关键读走 DB 强一致或加版本号校验"
        ],
        "hints": "结合量化数据说明收益（如 DB QPS 从 8000 降到 600）"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Redis",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "缓存穿透、击穿、雪崩分别怎么产生？互斥锁与逻辑过期在防击穿上各有什么取舍？",
        "reference_points": [
            "穿透（查不存在的 key）：布隆过滤器拦截 + 空值缓存（短 TTL）+ 参数校验",
            "击穿（热 key 过期瞬间高并发）：互斥锁重建 or 逻辑过期异步重建 or 热点 key 永不过期 + 后台刷新",
            "雪崩（大批 key 同时过期 / 实例宕机）：TTL 加随机抖动、多级缓存、集群高可用、熔断降级与限流",
            "互斥锁：一致性强，但其他线程等待甚至自旋，吞吐下降，存在死锁与超时风险",
            "逻辑过期：无阻塞高吞吐，但会短暂返回旧值，适合对一致性不敏感的热点榜单/详情"
        ],
        "hints": "对比时给出你自己的选型判断，而不是罗列两种方案"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Redis",
        "stage": "专业基础", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "Redis 常见的五种数据结构各自的底层编码与典型应用场景是什么？",
        "reference_points": [
            "String（int/sds/embstr）：计数、缓存对象、分布式锁、Session",
            "List（quicklist/listpack）：简单消息队列、最新动态列表、LRU 列表",
            "Hash（listpack/hashtable）：对象字段级更新（用户信息、商品库存明细）",
            "Set（intset/hashtable）：去重、共同好友交并差、抽奖防重复",
            "ZSet（listpack/skiplist）：排行榜、延迟队列、带权重的滑动窗口限流"
        ],
        "hints": "每种给一个真实业务例子比背名字更有说服力"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Redis",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Redis 是单线程的，为什么还能支撑十万级 QPS？Redis 6.0 引入多线程又是如何解决瓶颈的？",
        "reference_points": [
            "纯内存操作 + 单线程避免锁竞争与上下文切换 + IO 多路复用（epoll）支撑海量连接",
            "渐进式 rehash、ziplist/listpack 紧凑编码、跳跃表等结构设计降低开销",
            "真正瓶颈是网络 IO 与内存带宽，而非 CPU 计算，因此单线程命令执行不是问题",
            "6.0 多线程只用于网络数据的读写与协议解析，命令执行仍是单线程，因此无需加锁且保持语义不变",
            "大 key、热 key、慢命令（KEYS、SORT）才是生产事故主因，应使用 SCAN、拆分与本地缓存"
        ],
        "hints": "强调“执行单线程、网络多线程”这一关键区分"
    },

    # ================= === 后端开发 · 分布式与消息队列 === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Kafka",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "消息队列如何保证消息不丢失、不重复消费、顺序消费？请结合你实际用过的 MQ 说明。",
        "reference_points": [
            "不丢失三段保障：生产端（同步发送 + acks=all + 重试）、Broker（副本机制 min.insync.replicas + 持久化刷盘）、消费端（手动提交 offset）",
            "不重复：MQ 只能保证 at-least-once，需消费端幂等（唯一业务键 + 去重表/Redis SETNX/状态机乐观锁）",
            "顺序：同一业务键路由到同一分区（Kafka key / RocketMQ MessageQueueSelector），且消费者单线程处理该分区",
            "分区再均衡、消费者故障会打破顺序，需要业务层版本号或时间戳兜底",
            "积压处理：扩分区 + 扩消费者、临时转储到更大 topic 旁路消费、跳过非关键消息"
        ],
        "hints": "以“三段式”结构作答，最后补一个你处理过的积压案例"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "分布式事务",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "请对比 2PC、TCC、本地消息表与事务消息（RocketMQ）四种分布式事务方案，说明各自适用场景。",
        "reference_points": [
            "2PC：强一致但同步阻塞、协调者单点、资源长期锁定，适合数据库层面的 XA 短事务",
            "TCC：Try/Confirm/Cancel 业务侵入大，需处理空回滚、悬挂、幂等，适合资金等强一致高价值场景",
            "本地消息表：业务与消息同库事务落表，定时投递 + 消费幂等，实现简单、最终一致，适合大多数解耦场景",
            "RocketMQ 事务消息：半消息 + 本地事务 + 回查，免去自建消息表，适合已有 MQ 体系",
            "选型判断维度：一致性要求、性能吞吐、开发成本、是否需要人工补偿与对账"
        ],
        "hints": "先给结论（多数场景选最终一致），再解释为什么不选强一致"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "分布式锁",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Redis 分布式锁有哪些坑？Redlock 与 Zookeeper 方案如何取舍？锁续期你怎么做？",
        "reference_points": [
            "基础实现：SET key val NX PX ttl，释放用 Lua 判断持有者后删除（避免误删他人锁）",
            "核心风险：业务超时导致锁提前释放 → 需要看门狗续期（Redisson 默认 30s，每 10s 续）",
            "GC 停顿 / 网络分区导致锁失效后两个线程同时持写，Redis 主从异步复制还会在故障切换时丢锁",
            "Redlock：向多数独立节点加锁，需处理时钟漂移；Martin Kleppmann 与 antirez 的争议值得点出",
            "ZK 方案：临时顺序节点 + watch 前驱，天然会话绑定更安全但吞吐低于 Redis；对一致性要求极高选 ZK/etcd，追求性能选 Redis + 业务幂等兜底"
        ],
        "hints": "务必提到“锁不是正确性的全部，业务侧仍需幂等/版本号兜底”"
    },

    # ================= === 后端开发 · JVM 与框架 === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "JVM",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "JVM 如何判断对象可以被回收？G1 与 CMS 的区别是什么，你实际做过哪些调优？",
        "reference_points": [
            "可达性分析（GC Roots：栈帧引用、静态变量、常量、JNI），而非引用计数（无法解决循环引用）",
            "引用分级：强/软/弱/虚，决定回收时机与缓存策略",
            "CMS：标记清除、并发标记有浮动垃圾与内存碎片；G1：Region 化 + 可预测停顿模型 + 优先回收垃圾最多区域",
            "调优思路：先看 GC 日志与监控定位问题（频繁 Full GC / 长停顿），再调堆分代、元空间、GC 算法与业务对象生命周期",
            "常见根因：大对象直入老年代、缓存无界增长、内存泄漏（ThreadLocal 未清理、静态集合）"
        ],
        "hints": "调优题一定要给“现象 → 定位手段 → 参数改动 → 效果数据”的闭环"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Boot",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Spring Boot 的自动装配原理是什么？Starter 是如何生效的？循环依赖 Spring 怎么解决？",
        "reference_points": [
            "@SpringBootApplication 聚合 @EnableAutoConfiguration，通过 @Import(AutoConfigurationImportSelector) 加载候选配置",
            "Spring Boot 2.7+ 读取 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports（旧版为 spring.factories），配合 @Conditional 系列条件装配",
            "Starter 只做依赖聚合 + 自动配置，配置项通过 @ConfigurationProperties 暴露",
            "循环依赖：三级缓存（singletonObjects / earlySingletonObjects / singletonFactories），提前暴露代理对象解决 setter/字段注入的循环",
            "构造器注入的循环依赖无法解决；Boot 2.6+ 默认禁止循环依赖，应通过重构（拆分职责、@Lazy）解决"
        ],
        "hints": "先讲装配链路，再落到你写过的自定义 Starter 实践"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Boot",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你的接口如何做到幂等？请给出至少两种不同强度的实现方案与适用边界。",
        "reference_points": [
            "天然幂等（查询、状态置为固定值）优先设计成幂等，避免额外开销",
            "Token 机制：先申请幂等号，Redis SETNX + 过期，处理前删除，适合前端重复提交",
            "数据库唯一索引/业务单号约束：最强兜底，插入冲突即视为重复",
            "乐观锁版本号 / 状态机流转（只允许 PENDING→SUCCESS），适合扣减与状态推进",
            "分布式锁 + 去重表：适合外部回调（支付/物流）乱序与重试场景，需考虑回调重试上限与人工对账"
        ],
        "hints": "结合一个真实重复请求事故讲清“为什么这一种方案够用”"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Netty",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Netty 的线程模型是怎样的？如何解决粘包半包？什么是零拷贝，Netty 提供了哪些零拷贝能力？",
        "reference_points": [
            "主从 Reactor：bossGroup 接受连接，workerGroup 处理 IO，业务耗时操作投递到独立业务线程池避免阻塞 EventLoop",
            "一个 Channel 绑定固定 EventLoop，天然串行化避免并发问题；但 Handler 内不可做阻塞调用",
            "粘包半包：定长、分隔符（DelimiterBasedFrameDecoder）、消息头长度字段（LengthFieldBasedFrameDecoder，最常用）",
            "Netty 零拷贝：堆外直接内存、CompositeByteBuf 逻辑合并、slice 共享缓冲区、FileRegion transferTo 文件传输",
            "心跳与空闲检测用 IdleStateHandler，断线重连与写高水位背压需自行处理"
        ],
        "hints": "强调“避免阻塞 EventLoop”这一最容易踩的生产坑"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Elasticsearch",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "ES 的倒排索引原理是什么？为什么深分页性能差，如何正确分页？",
        "reference_points": [
            "分词 → Term Dictionary（FST 前缀树压缩常驻内存）→ Posting List（DocID 列表，Roaring Bitmap 压缩）",
            "写入：buffer + translog，refresh 生成 segment 近实时可见（1s），merge 合并小段，flush 落盘",
            "深分页 from=10000 需各分片取 10010 条汇总排序，协调节点内存与网络放大严重",
            "方案：search_after（游标式，适合翻页）、scroll（适合导出）、限制最大页数 + 业务侧引导筛选",
            "keyword 精确匹配不分词，text 分词；相关性打分 BM25，聚合用 doc_values"
        ],
        "hints": "把“为什么各分片都要取够数据”讲清楚，是本题核心"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Cloud",
        "stage": "系统设计", "difficulty": "MEDIUM", "time_limit_sec": 240,
        "text": "微服务之间调用如何保证高可用？请说明超时、重试、熔断、降级、限流各自解决什么问题。",
        "reference_points": [
            "超时：所有远程调用必须显式设置连接与读取超时，且上游超时应大于下游总耗时",
            "重试：只对幂等接口重试，配合退避（指数 + 抖动）与重试预算，避免重试风暴放大故障",
            "熔断：错误率/慢调用比例超阈值时打开，半开试探恢复，防止级联雪崩",
            "降级：返回兜底数据/缓存/默认值，核心链路优先保障，非核心功能先牺牲",
            "限流：令牌桶/漏桶/滑动窗口，入口按 QPS、资源按并发线程数，配合热点参数与队列排队",
            "还需考虑：线程池/信号量隔离、多活与故障转移、全链路压测与预案演练"
        ],
        "hints": "用一次真实故障的时间线串起这些机制最有说服力"
    },

    # ================= === 前端开发 === =================
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Vue3",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Vue3 的响应式原理相比 Vue2 有什么变化？ref 与 reactive 的底层差异是什么？",
        "reference_points": [
            "Vue2 用 Object.defineProperty 逐层劫持，无法感知新增/删除属性与数组下标变更，需 $set/$delete",
            "Vue3 用 Proxy + Reflect，可拦截 13 种操作，支持动态属性、数组与 Map/Set，且惰性递归（访问时才 deep reactive）",
            "effect 依赖收集：track 建立 target→key→dep 映射，trigger 精确派发，配合 scheduler 实现异步批量更新",
            "reactive 只能作用于对象，解构会丢失响应式；ref 通过 .value 包装，可用于任意类型，模板中自动解包",
            "toRefs / storeToRefs 用于保持解构后的响应式；shallowRef 适合大数据量列表与实例对象"
        ],
        "hints": "顺带提一下 watchEffect 与 computed 的缓存差异会加分"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Vue3",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Vue3 的编译优化有哪些？diff 过程中的最长递增子序列算法解决了什么问题？",
        "reference_points": [
            "静态提升（hoistStatic）：静态节点只创建一次，复用 DOM 与 vnode",
            "PatchFlags：编译期标注动态部分（text/class/props），运行时只比对标记，跳过静态内容",
            "Block Tree：把动态节点收集到动态子树数组，跳过整棵静态子树的遍历",
            "事件缓存（cacheHandlers）、预字符串化（static content 合并）",
            "diff 采用异构比较；对于乱序子节点用 getSequence 求最长递增子序列，只移动不在 LIS 上的节点，最小化 DOM 移动次数"
        ],
        "hints": "LIS 部分说明“为什么是移动最少”即可，不必手写完整代码"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Vue3",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你如何设计一个大型 Vue 项目的状态管理与请求层？请说明分层与踩过的坑。",
        "reference_points": [
            "Pinia 按业务域拆分 store，避免巨型 store；持久化按需（token/user）而非全量",
            "统一 axios 实例：请求拦截注入 token，响应拦截解包 {code,message,data} 并统一错误提示与 401 跳登录",
            "竞态处理：AbortController / 请求序号丢弃过期响应；重复提交用 loading 或幂等 token",
            "大列表性能：虚拟滚动、分页 vs 无限滚动取舍、组件 keep-alive 与路由懒加载",
            "权限：路由 meta + 全局守卫 + 后端二次校验，前端按钮级权限用指令或 composable"
        ],
        "hints": "挑一个真实线上问题（如竞态导致数据错乱）展开讲"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "TypeScript",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "TypeScript 中 interface 与 type 有什么区别？什么是协变与逆变，为什么它们对类型安全重要？",
        "reference_points": [
            "interface 可声明合并、可 extends，适合对外 API 契约；type 支持联合/交叉/条件/映射类型与工具类型",
            "type 可给原始类型/元组/函数签名起别名，interface 不能表达联合类型",
            "协变：子类型关系在容器上保持（Dog→Animal 则 Dog[]→Animal[]），数组协变在运行时可能不安全",
            "逆变：函数参数位置逆变，(Animal)=>void 可赋给 (Dog)=>void；strictFunctionTypes 才会检查",
            "结构化类型（鸭子类型）意味着只要形状匹配即可赋值，配合 unknown 与类型守卫收窄避免 any 扩散"
        ],
        "hints": "落到“为什么项目里要开 strict 并禁 any”的工程实践"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Node.js",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Node.js 的事件循环有哪些阶段？setImmediate 与 setTimeout(fn,0) 谁先执行？如何避免阻塞事件循环？",
        "reference_points": [
            "阶段：timers → pending callbacks → idle/prepare → poll（IO 与回调）→ check（setImmediate）→ close callbacks",
            "微任务队列 process.nextTick 优先于 Promise 微任务，在每个宏任务后清空",
            "模块顶层两者顺序不确定（受启动耗时影响，poll 是否已过期）；在 IO 回调内 setImmediate 一定先于 setTimeout(0)",
            "阻塞规避：CPU 密集任务拆分/worker_threads/子进程；大 JSON 与同步 fs API 是常见元凶",
            "背压与内存：stream pipeline、避免无限并发（p-limit）、监控 event loop delay 与堆使用"
        ],
        "hints": "把“IO 回调内”这个确定顺序的场景说清，最能体现真实理解"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "CSS",
        "stage": "专业基础", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "请说明 BFC 的形成条件与应用场景，以及 flex 布局中常见的溢出问题如何解决。",
        "reference_points": [
            "BFC 触发：float 非 none、position absolute/fixed、display flow-root/inline-block/flex/grid/table-cell、overflow 非 visible",
            "应用：清除浮动（父元素高度塌陷）、自适应两栏布局（左侧固定右侧 flow-root 不重叠）、外边距合并隔离",
            "flex 溢出根因：flex-shrink 默认 1 但 min-width/min-height 默认为 auto 导致无法收缩到内容以下",
            "解决：给可收缩项设置 min-width:0 或 overflow:hidden，长文本用 text-overflow/word-break",
            "响应式：clamp()、容器查询（@container）、grid auto-fit minmax 减少断点数量"
        ],
        "hints": "min-width:0 这个点几乎必问，务必答到"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "前端工程化",
        "stage": "系统设计", "difficulty": "MEDIUM", "time_limit_sec": 240,
        "text": "如果让你负责一个前端项目的性能优化，你会怎么建立指标体系并落地？",
        "reference_points": [
            "指标先行：Core Web Vitals（LCP/INP/CLS）+ 首屏 TTFB + JS 错误率，用 RUM 采集真实用户数据而非只看 Lighthouse",
            "加载：路由与组件级代码分割、预加载关键资源、HTTP 缓存 + 内容哈希、CDN、图片格式与尺寸适配、tree-shaking 与依赖替换",
            "渲染：骨架屏、虚拟列表、避免布局抖动（预留尺寸）、长任务拆分（scheduler.yield / requestIdleCallback）",
            "构建：Vite 预构建与持久化缓存、产物体积分析、按需引入组件库、Gzip/Brotli",
            "防劣化：CI 中设置体积与性能预算门禁、灰度发布与回滚、监控告警闭环"
        ],
        "hints": "给出一个“优化前后具体数字”的案例，说服力最强"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "浏览器原理",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "从输入 URL 到页面展示经历了什么？其中哪些环节最容易成为性能瓶颈？",
        "reference_points": [
            "DNS（缓存层级）→ TCP/TLS（RTT 次数）→ 请求 → 响应 → 解析 HTML 构建 DOM、CSSOM 阻塞渲染",
            "脚本阻塞解析：defer 保持顺序延后执行、async 就绪即执行；关键 CSS 内联，preconnect 提前握手",
            "渲染流水线：layout（几何）→ paint（像素）→ composite（图层合成），transform/opacity 只走合成不触发重排",
            "瓶颈常在：串行请求瀑布（先 JS 再接口）、未压缩大资源、首屏同步 JS 体积、字体闪烁、图片未预留尺寸导致 CLS",
            "安全与跨域：同源策略与 CORS 预检、SameSite Cookie、CSRF/XSS 防护"
        ],
        "hints": "不要背链路，重点说清“哪个环节你能优化、怎么优化”"
    },

    # ================= === 人工智能 / 大模型应用 === =================
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "LLM应用",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你在做 LLM 应用时如何降低幻觉并保证输出可控？请给出体系化的做法。",
        "reference_points": [
            "检索增强（RAG）：给模型可引用的事实来源，并在 prompt 中要求“仅基于给定资料作答，无法回答时明确说明”",
            "结构化约束：few-shot 示例 + JSON Schema/Pydantic 校验 + response_format 强制 JSON，失败重试或降级",
            "任务拆解：把复杂问题拆成多步（规划-执行-校验），让每步上下文更短更聚焦",
            "生成后校验：规则校验 + 小模型/LLM 自评 + 关键事实回查检索结果，不通过则重生成",
            "温度与截断：事实型任务用低温度；控制上下文长度避免“中间遗忘”（lost in the middle），关键信息前置或复述"
        ],
        "hints": "务必提到“校验不通过怎么办”，这是工程成熟度的体现"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "RAG",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "设计一个企业知识库问答系统，你会如何在检索质量与生成成本之间取得平衡？",
        "reference_points": [
            "文档处理：按语义/结构分块（标题层级、代码块完整），重叠窗口，元数据（来源、时间、权限）随块存储",
            "混合检索：向量（语义）+ BM25（关键词/专有名词）召回，再用 rerank 模型精排，显著优于纯向量",
            "查询改写：多查询、HyDE、意图路由（不同库/不同工具），追问澄清歧义问题",
            "上下文压缩与引用：只送相关段落，输出带来源引用便于人工核查，命中不足时拒答",
            "成本控制：小模型做改写/分类、大模型只做最终生成；语义缓存高频问答；离线评测集 + 线上指标（命中率、拒答率、满意度）持续迭代"
        ],
        "hints": "强调评测集与指标体系，没有度量就无法优化"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "LangChain",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你如何评估一个 LLM 应用的效果？没有标注数据时怎么办？",
        "reference_points": [
            "分层评估：端到端业务指标（完成率、人工接管率）+ 中间环节指标（检索命中率、工具调用成功率、格式合法率）",
            "离线评测集：从真实日志抽样构建 golden set，覆盖典型与边界问题，版本化并回归跑",
            "无标注时：LLM-as-judge（需校验裁判与人工一致性）、规则可判定项优先（是否含引用、是否越界承诺）、A/B 对比新旧 prompt",
            "人工评估：小规模双盲打分，定义清晰评分标准（准确性/完整性/安全性）",
            "线上：灰度 + 用户反馈（点赞点踩）+ 抽样人审，建立坏例回流机制持续补充评测集"
        ],
        "hints": "把“坏例如何回流到评测集”说清楚，这是闭环关键"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "深度学习",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Transformer 的自注意力机制是如何计算的？为什么要引入多头与位置编码？",
        "reference_points": [
            "QKV 线性投影，Attention = softmax(QKᵀ/√d)V；√d 缩放防止点积过大导致梯度消失",
            "因果掩码（decoder）保证只看历史 token；复杂度 O(n²d) 是长序列瓶颈",
            "多头：在不同子空间分别关注（语法、指代、位置模式），拼接后投影，增强表达力",
            "位置编码：注意力本身对顺序置换不变，需注入位置信息（正弦、可学习、RoPE、ALiBi）",
            "工程细节：残差连接 + LayerNorm 稳定深层训练，FFN 提供非线性，KV Cache 降低推理成本"
        ],
        "hints": "能说出 KV Cache 或长上下文优化手段会明显加分"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "Python",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "Python 的 GIL 对多线程有什么影响？CPU 密集与 IO 密集分别该怎么选并发模型？",
        "reference_points": [
            "GIL 使同一进程内仅一个线程执行字节码，CPU 密集多线程无加速甚至更慢（切换开销）",
            "IO 密集仍适用多线程/协程：等待时释放 GIL，网络请求由 C 层扩展并发",
            "CPU 密集：multiprocessing 多进程绕过 GIL，或下沉到 NumPy/C/Rust 扩展、Cython",
            "高并发 IO：asyncio 单线程事件循环 + await，代价是必须全链路异步（同步库会阻塞整个 loop）",
            "选型判断：并发量与内存开销（线程 ~MB 栈 vs 协程 ~KB）、第三方库是否有异步版本、调试复杂度"
        ],
        "hints": "点出“混用同步库会卡死事件循环”这个高频事故"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "FastAPI",
        "stage": "专业基础", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "FastAPI 为什么快？它的 async 端点与 sync 端点在运行时有什么区别？",
        "reference_points": [
            "ASGI 异步框架（非 WSGI 阻塞模型），Starlette 路由 + Pydantic 校验 + 自动生成 OpenAPI",
            "async def 端点跑在事件循环；def 端点会被丢到线程池（anyio）执行，避免阻塞 loop",
            "因此调用阻塞库（requests、同步 DB 驱动）时应该用 def，或改用异步客户端",
            "依赖注入系统（Depends）可复用鉴权与 DB 会话；yield 依赖负责资源释放",
            "性能还依赖 uvicorn worker 数量、连接池、序列化开销与响应模型（response_model 过滤字段）"
        ],
        "hints": "把“def 会走线程池”这个反直觉点讲清楚"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "数据工程",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "模型上线后发现效果明显低于离线评估，你会如何排查？",
        "reference_points": [
            "先确认是否训练/服务偏斜（training-serving skew）：特征口径、缺失值填充、预处理顺序、分词与截断长度是否一致",
            "数据分布漂移：线上输入分布、语种、长度、领域是否变化；对比离线评测集是否代表真实流量",
            "标签泄漏：离线指标虚高（使用了未来信息或目标本身），需按时间切分重跑",
            "工程链路：缓存命中旧结果、超时降级走了兜底模型、prompt 版本未同步、并发导致上下文串扰",
            "定位手段：同一条样本双端对比中间产物（检索结果、prompt、原始输出），建立可观测日志与影子流量回放"
        ],
        "hints": "给出“逐环节对齐中间产物”的方法论比猜原因更重要"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "Prompt工程",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请谈谈你迭代 prompt 的方法。如何判断一次 prompt 改动是真正的改进？",
        "reference_points": [
            "结构化模板：角色 + 任务 + 输入边界 + 输出格式 + 拒答规则 + few-shot，各部分独立可替换",
            "改动必须可归因：一次只改一个变量，保留基线版本与变更说明（prompt 版本化，像代码一样管理）",
            "判定依据是评测集指标（准确率/格式合法率/拒答正确率），而不是“看起来更顺”，并关注统计显著性",
            "针对性修补坏例：把典型坏例转成 few-shot 或显式规则，警惕规则膨胀互相冲突导致整体退化",
            "成本与稳定性：token 数、时延、模型版本升级后的回归；关键业务保留人工兜底"
        ],
        "hints": "强调“版本化 + 回归评测”，这是从玄学到工程的分水岭"
    },

    # ================= === 大数据 === =================
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Spark",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Spark 的 shuffle 发生在什么时候？数据倾斜你如何定位与解决？",
        "reference_points": [
            "宽依赖触发 stage 划分与 shuffle（groupByKey/reduceByKey/join/partitionBy），HashAggregate 等也伴随 shuffle",
            "定位：Spark UI 看单个 task 处理数据量与耗时长尾，某些 partition 远大于其余",
            "热点 key 加盐打散：给 key 拼随机前缀做两阶段聚合（局部聚合 + 去前缀全局聚合）",
            "大表 join 小表广播（broadcast join）避免 shuffle；skew join hint 自动拆分热点",
            "其他：过滤无效 key（null/默认值单独处理）、提高并行度、AQE 自适应分区合并、内存与序列化（Kryo）调优"
        ],
        "hints": "一定说清“两阶段聚合”的具体做法，这是高频追问点"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Flink",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Flink 的 exactly-once 是如何实现的？事件时间与窗口延迟怎么处理？",
        "reference_points": [
            "Checkpoint：Chandy-Lamport 变体的异步屏障快照（Barrier），源端注入 barrier，算端对齐后快照状态，全局一致",
            "端到端精确一次还需源可重放（Kafka offset）+ 支持两阶段提交的 Sink（Checkpoint 时 pre-commit，完成后 commit）",
            "反压会影响 barrier 对齐时间，可用 unaligned checkpoint 缓解",
            "事件时间 + Watermark（乱序程度、idle 检测）驱动窗口触发；allowedLateness 容忍迟到，side output 收集超期数据",
            "状态管理：RocksDB 增量 checkpoint、TTL 清理、大状态需预分区与本地恢复"
        ],
        "hints": "把“barrier 对齐”与“两阶段提交”两层讲清，缺一层就不是端到端"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Hive",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "Hive 中小文件过多会带来什么问题？如何治理？",
        "reference_points": [
            "NameNode 元数据压力（每文件约 150B 内存）、大量 Map task 启动开销、随机 IO 拉低吞吐",
            "根因：动态分区插入、粒度过细、频繁小批量写入、未合并的中间结果",
            "治理：merge 参数（merge.inputfiles / mapreduce.merge）、合理分区与分桶、定期 compaction",
            "写入侧控制并发与文件大小，采用 ORC/Parquet 列存 + 压缩（Zstd/Snappy）",
            "架构侧：湖仓格式（Hudi/Iceberg）支持小文件自动合并与增量读写"
        ],
        "hints": "结合“你治理过多少表、效果数字”回答最有说服力"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "SQL",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请用 SQL 求“每个部门薪资前三的员工”，并说明窗口函数与普通 group by 的差异。",
        "reference_points": [
            "ROW_NUMBER()/RANK()/DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC)，外层过滤 rn<=3",
            "三者差异：并列第一时 ROW_NUMBER 强制唯一、RANK 跳号、DENSE_RANK 不跳号，需按业务口径选择",
            "窗口函数保留明细行并可做累计/移动/同比环比（LAG/LEAD/SUM OVER），group by 会压缩行数",
            "性能：分区字段与排序字段决定数据重分布代价，尽量先过滤再开窗、避免全表开窗",
            "NULL 与重复值处理、边界（并列超过 3 人是否都要）需与需求方确认"
        ],
        "hints": "口述 SQL 时保持语法完整，并主动说明并列取法与业务确认"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "数据仓库",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "设计一个支撑 BI 报表与自助取数的数据仓库分层，你会如何建模并保证数据质量？",
        "reference_points": [
            "分层：ODS（贴源）→ DWD（明细事实，清洗标准化）→ DWS（轻度汇总主题宽表）→ ADS（应用层指标），维度表独立",
            "建模：维度建模（星型/雪花），缓慢变化维处理（拉链表/快照），一致性维度与指标口径字典",
            "质量：主键唯一、非空、枚举、波动率、跨表一致性校验，规则前置到调度并阻断下游",
            "血缘与元数据：字段级血缘、任务依赖、指标定义可追溯，变更走评审与影响分析",
            "成本与时效：分区裁剪、增量计算（分区覆盖/merge）、冷热分层、SLA 分级保障核心报表"
        ],
        "hints": "强调“口径统一与指标字典”，这是数仓治理的真正难点"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "数据清洗",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "上游数据源突然变更字段导致下游报表错误，你如何建立防御机制？",
        "reference_points": [
            "契约化：与上游约定 Schema 契约与变更通知流程，接入层做 schema registry 校验",
            "防御式解析：字段缺失/类型异常不静默填默认值，显式标记并进入隔离区（dead letter）",
            "监控：行数、空值率、枚举分布、指标波动率的多维告警，异常自动阻断下游任务",
            "可回滚：数据版本化（分区快照 / 时间旅行），支持按天重跑与幂等覆盖",
            "流程：灰度接入新字段、双跑对比、变更评审与影响面评估，事后复盘补充校验规则"
        ],
        "hints": "把“发现—阻断—回滚—复盘”的闭环讲完整"
    },

    # ================= === 运维 / 云原生 === =================
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "Kubernetes",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Pod 一直处于 Pending 或 CrashLoopBackOff，你的排查思路是什么？",
        "reference_points": [
            "Pending：kubectl describe 看 Events —— 资源不足、节点选择器/亲和性不满足、PVC 未绑定、污点容忍、配额限制",
            "CrashLoopBackOff：kubectl logs --previous 看崩溃前日志，多为启动报错、配置/环境变量缺失、依赖不可达、探针失败",
            "OOMKilled（exit 137）：limits 过低或内存泄漏，需看 GC/堆监控而非盲目调大",
            "探针设计：startupProbe 保护慢启动，readiness 控制流量接入，liveness 只用于真正不可恢复场景（配错会放大故障）",
            "镜像拉取失败（ImagePullBackOff）：镜像地址/凭证/网络；节点层面看 kubelet 日志与磁盘压力驱逐"
        ],
        "hints": "按“事件 → 日志 → 退出码 → 资源配置”的顺序说，体现体系化"
    },
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "Docker",
        "stage": "专业基础", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "如何把一个 Python 服务的镜像做小做安全？请给出具体手段。",
        "reference_points": [
            "多阶段构建：builder 装编译依赖与 wheel，runtime 只拷贝产物，基础镜像用 slim/distroless/alpine（注意 musl 兼容）",
            "层顺序：变动少的（依赖清单）在前，源码在后，最大化构建缓存",
            ".dockerignore 排除 .git、tests、node_modules、本地 venv；pip 用 --no-cache-dir",
            "安全：非 root 用户运行、只读文件系统、固定基础镜像 digest、镜像扫描（Trivy）与最小依赖、不泄露密钥（用 secret 挂载）",
            "体积排查：docker history 看单层大小，常见元凶是 apt 缓存未清理、编译工具链残留、日志文件写入镜像层"
        ],
        "hints": "说一个“从 X GB 压到 Y MB”的真实数字最有效"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Prometheus",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "为一个 50 个微服务的系统设计监控告警体系，你会怎么设计指标与告警规则以避免告警风暴？",
        "reference_points": [
            "分层指标：USE（资源利用率/饱和度/错误）看基础设施，RED（请求量/错误/时延）看服务，业务指标看转化",
            "时延用直方图 + histogram_quantile 聚合，禁止对平均值求平均；区分 P50/P95/P99",
            "告警降噪：只对用户可感知症状告警（SLO 错误预算燃尽），把原因类指标作为排查上下文；分级（page/ticket）",
            "风暴治理：告警聚合与抑制（inhibition）、静默窗口、依赖拓扑关联（同一根因只发一条）、限流与去重",
            "配套：结构化日志 + traceId 打通链路追踪、Dashboard 模板化、值班与复盘机制、定期告警有效性评审"
        ],
        "hints": "强调“告警必须可执行”，每条告警都对应一个处置动作"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Linux",
        "stage": "深度探究", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "一台服务器 CPU 使用率 100%，你如何定位到具体代码？",
        "reference_points": [
            "top 看是 us（用户态）还是 sy（内核态）/wa（等待 IO）/si（软中断），不同占比指向完全不同的原因",
            "us 高：top -H 找高 CPU 线程 → 转十六进制线程号 → jstack/async-profiler 火焰图定位方法栈",
            "sy 高：频繁上下文切换/系统调用，用 vmstat cs、perf stat 看；si 高多为网络包量或中断不均",
            "wa 高：iostat -x 看 util 与 await，pidstat 定位进程，常见于大量小文件 IO 或刷盘",
            "其他：load 高但 CPU 低多为 D 状态进程（NFS/IO 阻塞）；用 perf top 看热点函数，注意容器内 CPU 配额（cgroup throttling）导致的限流"
        ],
        "hints": "先分类（us/sy/wa/si）再定位，展示的是排查思路而非命令背诵"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Go",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Go 的 goroutine 调度模型是什么？channel 与 mutex 你如何选择？常见并发 bug 有哪些？",
        "reference_points": [
            "GMP 模型：G（协程，栈可增长，初始 2KB 左右）、M（OS 线程）、P（逻辑处理器，持有本地运行队列），work stealing 均衡负载",
            "系统调用阻塞时 M 与 P 解绑（hand off），避免整个 P 的队列饿死；GOMAXPROCS 控制并行度",
            "channel 用于传递所有权与协调（生产者消费者、扇入扇出、超时控制）；mutex 用于保护共享状态，语义更直接",
            "常见 bug：goroutine 泄漏（无人接收的 channel 发送、未关闭的 range）、数据竞争（go run -race 检测）、闭包捕获循环变量、WaitGroup Add 位置错误",
            "规范：谁写谁关、通过 context 传递取消与超时、避免无缓冲 channel 死锁、defer unlock 成对"
        ],
        "hints": "提到 go test -race 与 goroutine 泄漏排查（pprof goroutine profile）"
    },
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "CI/CD",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你们的发布流程是怎样的？如何做到可快速回滚且风险可控？",
        "reference_points": [
            "流水线：lint + 单测 → 构建镜像（固定版本与 digest）→ 集成/契约测试 → 安全与镜像扫描 → 预发验证 → 分批发布",
            "发布策略：滚动（默认）、蓝绿（快速切换与回退）、金丝雀/灰度（按流量比例 + 指标自动判定推进或回滚）",
            "可回滚：保留上一版本镜像与配置、迁移脚本向前兼容（expand-contract 模式，避免不可逆 DDL）、一键回滚演练",
            "风险隔离：特性开关（feature flag）让部署与发布解耦，配置变更同样纳入审计与回滚",
            "度量：变更失败率、恢复时长（MTTR）、部署频率、前置时长（DORA 四指标）驱动流程改进"
        ],
        "hints": "务必提到数据库变更兼容性，这是回滚最容易失手的环节"
    },

    # ================= === 质量保障 === =================
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "测试设计",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "给你一个“优惠券发放”功能，你会如何设计测试用例？",
        "reference_points": [
            "先明确规则与边界：领取次数上限、库存、有效期、叠加互斥、适用商品范围、退款后是否返还",
            "正常路径 + 边界（0/1/上限/上限+1、有效期前后 1 秒、跨天跨时区）+ 异常（重复领取、并发抢券、库存不足、参数篡改）",
            "并发与幂等：多线程同时领取不超发、重复请求不重复发放，验证分布式锁与唯一约束",
            "资金与对账：金额计算精度（分为单位）、优惠后价格与订单一致、异常回滚不产生脏数据",
            "非功能：接口性能与限流、日志与监控可定位、灰度与回滚验证；用等价类/边界值/判定表组织，避免用例重复"
        ],
        "hints": "展示“先问清规则再设计用例”的习惯，比罗列用例更高分"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "Pytest",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "接口自动化测试如何做到稳定可维护？你如何处理测试数据与环境依赖？",
        "reference_points": [
            "分层：断言层薄、封装层（client + builder）厚，用例只描述业务意图，避免复制粘贴",
            "fixture 管理前置条件与清理，function/module 作用域合理选择；参数化覆盖多组数据",
            "数据自治：每个用例自己造数（工厂 + 唯一标识），不依赖执行顺序与共享脏数据，用后清理",
            "不稳定根因：等待策略（禁止 sleep，用轮询/条件等待）、时间与时区、随机种子、外部依赖未 mock",
            "契约与 mock：下游用契约测试或录制回放；断言避免全字段快照，只断言业务关键字段；失败保留请求响应日志与 traceId"
        ],
        "hints": "重点讲“用例之间零依赖”，这是自动化能否长期跑下去的关键"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "Selenium",
        "stage": "深度探究", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "UI 自动化测试维护成本高、稳定性差，你认为应该怎么定位它的价值边界？",
        "reference_points": [
            "测试金字塔：大量单测 + 适量接口/契约测试 + 极少量关键路径 E2E，UI 层只覆盖核心链路（登录、下单、支付）",
            "稳定性手段：显式条件等待、Page Object 封装、稳定选择器（data-testid 而非 XPath 层级）、失败自动重试 + 截图/视频/DOM 留档",
            "定位价值：跨浏览器兼容、真实用户旅程回归、发布前冒烟门禁；不适合穷举业务分支",
            "反模式：用 UI 自动化验证细节逻辑、用例互相依赖、断言脆弱（文案/样式）、无人维护的僵尸用例",
            "度量：误报率、执行时长、缺陷发现数；长期发现不了 bug 的套件应精简或下线"
        ],
        "hints": "能主动说出“哪些不该做 UI 自动化”体现判断力"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "性能测试",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "一次全链路压测你如何组织？如何保证压测数据不污染生产？",
        "reference_points": [
            "目标先行：明确 SLO（TPS、P99、成功率）与容量水位，选择基准/阶梯/尖峰/浸泡（长稳）场景",
            "链路建模：按线上流量比例构造场景与参数化数据，避免只压单接口导致结论失真",
            "数据隔离：影子表/影子库 + 压测标透传（网关到 DB），MQ 与缓存走影子 topic/key，禁止写真实业务表",
            "风险控制：限流熔断规则临时调整需评估、避开业务高峰、准备一键停止与降级预案、通知相关方",
            "结果分析：定位瓶颈（应用 CPU/GC、DB 慢查询与连接池、下游依赖、网络与带宽），给出容量结论与优化项，优化后回归验证"
        ],
        "hints": "强调“压测标全链路透传”，这是不污染生产的唯一可靠做法"
    },

    # ================= === 客户端 === =================
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Android",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Android 内存泄漏常见原因有哪些？你如何定位与治理？",
        "reference_points": [
            "典型泄漏：Activity/Context 被静态集合或单例持有、非静态内部类持有外部 Activity、Handler/匿名监听未反注册、未关闭的 Cursor/IO",
            "生命周期：配置变更（旋转）导致重建，ViewModel 与 onRetainNonConfigurationInstance 用于跨重建保存",
            "定位：LeakCanary 自动检测并输出引用链，配合 Profiler 看堆增长与 GC 后是否回落",
            "治理：用 Application Context、弱引用 + 生命周期感知（lifecycleScope 自动取消协程）、统一注册/注销封装",
            "大图与列表：图片采样与复用池、RecyclerView 复用与 DiffUtil、避免主线程 IO 与过度绘制"
        ],
        "hints": "给出“引用链怎么读”的具体例子最加分"
    },
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Flutter",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "Flutter 的三棵树（Widget/Element/RenderObject）分别做什么？setState 之后发生了什么？",
        "reference_points": [
            "Widget 是不可变配置（重建廉价）、Element 管理生命周期与位置、RenderObject 负责布局绘制（昂贵，尽量复用）",
            "setState 标记 Element dirty → 帧回调 build 新 Widget 子树 → Element 按 runtimeType 与 key 决定复用或重建 → 脏化 RenderObject 重新 layout/paint/composite",
            "key 的作用：在列表顺序变化时正确复用状态（ValueKey/ObjectKey/GlobalKey 慎用）",
            "性能优化：拆分小 Widget 缩小重建范围、const 构造、列表用 ListView.builder、避免 build 中做耗时计算与新建对象",
            "RepaintBoundary 隔离重绘区域；isolate 处理 CPU 密集任务避免掉帧"
        ],
        "hints": "把“为什么 Widget 可以随便重建”讲清楚"
    },
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Kotlin",
        "stage": "深度探究", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Kotlin 协程与线程有什么本质区别？结构化并发解决了什么问题？",
        "reference_points": [
            "协程是运行在线程上的轻量任务，挂起（suspend）不阻塞线程，切换成本远低于线程；百万协程可跑在少量线程上",
            "Dispatchers：Main/IO/Default/Unconfined，挂起函数本身不切线程，需显式 withContext",
            "结构化并发：协程必须挂在 CoroutineScope 下，作用域结束自动取消所有子任务，避免“泄漏的异步任务”",
            "SupervisorJob 让兄弟任务失败互不影响；coroutineScope 保证内部子任务全部完成才返回",
            "取消是协作式的：需检查 isActive 或响应 CancellationException，finally 中用 withContext(NonCancellable) 做清理"
        ],
        "hints": "提到“挂起函数不自动切线程”这个高频误解"
    },

    # ================= === 系统底层 / C++ === =================
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "C++",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请说明 C++ 的内存分区与 RAII 思想，以及移动语义解决了什么问题。",
        "reference_points": [
            "分区：栈（自动、局部对象）、堆（new/make_unique）、全局/静态区、常量区、内存映射区；泄漏与越界多发生在堆与栈帧外访问",
            "RAII：资源生命周期绑定对象作用域，析构自动释放，配合 unique_ptr/shared_ptr/lock_guard 消除手动释放",
            "shared_ptr 计数非线程安全（控制块原子、引用计数本身需注意循环引用，用 weak_ptr 打破）",
            "移动语义：右值引用避免深拷贝（vector 扩容、返回大对象），std::move 只是转为左值为右值，真正的收益在移动构造/赋值实现",
            "被移动后对象处于有效但未指定状态，只能重新赋值或析构；完美转发（forward）保留值类别"
        ],
        "hints": "结合一次真实性能改进（拷贝转移动后的耗时变化）说明"
    },
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "Raft",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Raft 如何选出 Leader 并保证日志一致？为什么已提交的日志一定被后续所有 Leader 包含？",
        "reference_points": [
            "三种角色与任期（term）单调递增；Follower 选举超时未收到心跳则自增 term 转 Candidate 发起投票",
            "一票一任期 + 多数派（quorum）当选，随机超时打散降低选票分裂",
            "日志复制：Leader 追加并并行发送 AppendEntries，多数派确认后提交（推进 commitIndex）再应用到状态机",
            "安全性三条：选举限制（只有日志足够新的节点能当选）、Leader 唯一写入口、只提交当前任期的日志（间接提交需再提交一条当前任期日志）",
            "多数派交集非空 → 已提交日志必然存在于任何新 Leader 的日志中；日志匹配特性保证一致性"
        ],
        "hints": "能讲清“多数派相交”这一不变量，说明真正理解了安全性"
    },
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "网络",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "TCP 三次握手为什么不能是两次？TIME_WAIT 过多怎么处理？",
        "reference_points": [
            "两次握手无法让服务端确认客户端的初始序列号，历史重复 SYN 会建立无效连接并浪费资源；同时双方需确认彼此的 ISN",
            "TIME_WAIT 是主动关闭方等待 2MSL，保证最后 ACK 可达且让旧报文在网络中消亡",
            "过多成因：短连接频繁主动关闭（客户端或未启用 keep-alive 的服务端），排查调用方而非盲目调参",
            "缓解：连接池与长连接复用、调 tcp_tw_reuse（客户端侧）、合理 backlog 与 accept 模型、负载均衡层保持长连接",
            "注意 tcp_abort_on_overflow 等参数会引入错误，SYN flood 场景应关注 syncookies 而非随意调整"
        ],
        "hints": "先讲协议正确性，再讲工程处置，顺序不要颠倒"
    },

    # ================= === 信息安全 === =================
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "Web安全",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "XSS、CSRF、SQL 注入、SSRF 分别如何防御？请说明为什么“转义输出”比“过滤输入”更可靠。",
        "reference_points": [
            "XSS：按上下文输出编码（HTML/属性/JS/URL）、CSP 白名单、HttpOnly Cookie、富文本用成熟净化库并服务端二次校验",
            "CSRF：SameSite Cookie + 一次性 CSRF Token / 自定义请求头校验，关键操作二次确认；不依赖 Referer 单独判断",
            "SQL 注入：参数化查询（预编译）为根本，最小权限账号、ORM 而非拼接、WAF 只是纵深防御",
            "SSRF：出网白名单 + 禁止内网与云元数据地址、禁用重定向跟随、独立低权限代理出网",
            "过滤输入易被绕过（编码、上下文差异、协议特性），且破坏正常业务；输出编码在危险发生点做防护，语义明确"
        ],
        "hints": "每类给一个“最核心的一条措施”，别平铺罗列"
    },
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "权限治理",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "如何系统性发现越权访问（水平/垂直）漏洞？你在项目中怎么建立防护？",
        "reference_points": [
            "水平越权：资源 ID 可枚举 + 未校验归属；垂直越权：前端隐藏入口但后端未鉴权",
            "排查方法：用低权限账号携带高权限/他人资源 ID 重放请求；对 ID 做遍历与差集比对；网关日志审计无鉴权调用的接口清单",
            "防护：所有数据访问统一走带 owner 条件的仓储层（默认过滤而非逐接口记得加），接口级权限注解 + 资源级二次校验",
            "ID 设计：对外用不可枚举的 UUID/雪花 ID 或加签 ID，降低探测面（但不能替代鉴权）",
            "工程保障：鉴权中间件统一兜底、契约测试覆盖未授权用例、上线前权限矩阵评审、定期红队扫描"
        ],
        "hints": "强调“默认安全（fail-closed）”的架构性防护，而不是靠人记得写判断"
    },
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "数据合规",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "处理用户简历、手机号等个人信息，你在脱敏、加密与留存策略上会怎么做？",
        "reference_points": [
            "分级分类：识别敏感字段（身份证、手机号、住址、薪资），按等级确定加密与访问控制强度",
            "存储：可逆需求用字段级加密（KMS 托管密钥、密钥与数据分离），仅需比对用 HMAC/哈希加盐索引",
            "展示与日志：默认掩码（138****8000）、导出与查询留痕、日志与埋点禁止明文 PII，测试环境用合成数据",
            "访问控制：最小权限 + 二次授权、按用途授权（企业仅在候选人授权后可见联系方式）、可撤回同意",
            "留存与销毁：明确保留期限与到期删除/匿名化，支持用户导出与注销（被遗忘权），备份同样纳入删除策略"
        ],
        "hints": "结合“授权可见 + 可撤回”的业务流程讲，比只讲算法更专业"
    },

    # ================= === 通用题（跨岗位） === =================
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 120,
        "text": "请用两分钟介绍你自己，重点说明与目标岗位最相关的一段经历。",
        "reference_points": [
            "结构清晰：现状/背景 → 与岗位最相关的一段经历 → 可量化的成果 → 为什么匹配这个岗位",
            "围绕岗位 JD 的能力关键词组织内容，而不是流水账式罗列课程与社团",
            "成果量化：做了什么、指标变化多少、自己承担的具体角色",
            "控制在 2 分钟内，结尾主动把话题引向自己最能证明能力的项目"
        ],
        "hints": "提前准备一个 30 秒版本和 2 分钟版本，切忌背诵感"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 240,
        "text": "介绍一个你最有成就感的项目，说明你负责的部分、遇到的最大困难以及最终结果。",
        "reference_points": [
            "用 STAR：情境（业务目标与约束）→ 任务（你的职责边界）→ 行动（关键技术/方案选择与取舍）→ 结果（量化收益）",
            "困难要具体到“卡在哪一步、试了哪些路、为什么最终选它”，体现真实参与",
            "主动说明自己的不足与返工，比只讲成功更可信",
            "结果给出可核查的数字（性能提升、耗时下降、用户量），并说明数据如何统计得到",
            "准备好被追问细节：某个参数为什么这么设、某段代码谁写的、下一步会怎么改"
        ],
        "hints": "面试官考察的是深度与真实性，宁可讲小切口也不要讲宏大空话"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "项目中你与同事（或上下游）产生过技术分歧吗？你是怎么推动达成一致的？",
        "reference_points": [
            "选真实冲突，先客观复述双方立场与各自合理性，不贬低对方",
            "关键动作：回到共同目标与判断标准（数据、用户体验、维护成本），把“我觉得”变成“我们验证一下”",
            "推动方式：小范围实验/压测数据、书面方案对比、拉相关方评审、必要时向上升级但不越级对抗",
            "结果与关系维护：即使最终采纳对方方案也全力执行，事后复盘沉淀规范",
            "体现成熟度：能承认自己判断失误，并说明从中学到了什么"
        ],
        "hints": "考察协作与情绪管理，避免把自己塑造成“一直正确”的人"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "说一次你失败或犯错的经历，你事后如何复盘，改变了什么？",
        "reference_points": [
            "选真实且有代价的失败，明确自己应承担的责任部分，不甩锅给环境或他人",
            "说清后果（延期、返工、线上问题）与当时为什么判断失误（信息不足、侥幸心理、未验证假设）",
            "复盘落到机制：加了什么检查清单、自动化校验、评审环节，让同类问题不再依赖个人细心",
            "展示改变已被验证：后续同类任务的具体做法与结果",
            "态度：坦然但不自我贬低，聚焦成长"
        ],
        "hints": "这题最忌“我的缺点是太追求完美”式伪失败"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 120,
        "text": "近期你在主动学习什么？通过什么方式学，怎么确认自己真的学会了？",
        "reference_points": [
            "有具体在学的技术/领域与明确动机（岗位需要或项目卡点），不是泛泛而谈“看书”",
            "学习路径：官方文档/源码 → 动手做小项目 → 输出（笔记、分享、博客）→ 反馈修正",
            "检验标准：能否不查资料实现、能否讲给别人听、能否处理异常与边界场景",
            "把学习成果与实际产出关联（用新学的技术解决了什么问题）",
            "体现持续性与方法，而非一次性的突击"
        ],
        "hints": "举一个“学到能上手”的具体证据，比列书单有效"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "你的职业规划是什么？为什么选择我们这个岗位？",
        "reference_points": [
            "短期（1-2 年）能力目标具体可验证（如独立负责某类模块/打通某条链路），不喊“成为专家”的空口号",
            "中长期方向与岗位成长路径一致，说明你了解这个岗位实际做什么",
            "选择理由落到该业务/技术栈/团队特点的具体事实（产品形态、技术挑战、岗位要求），而非“公司很大很有名”",
            "诚实说明自身与要求的差距及补齐计划，展现自我认知",
            "避免暴露“只把这里当跳板”或“完全不了解岗位”的信号"
        ],
        "hints": "提前研究岗位 JD 与公司产品，把理由说具体"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "如果同时有多个任务且截止时间冲突，你如何安排？",
        "reference_points": [
            "先澄清：任务目标、真实截止时间、可交付的最小范围与依赖关系，避免按表面要求硬扛",
            "排序依据：影响面 × 紧急度 × 阻塞他人程度，优先做会阻塞他人的事",
            "主动沟通：及早暴露风险与取舍，向上申请调整范围或时间，而不是最后一刻才说做不完",
            "执行手段：拆分与并行、降低非关键任务标准、争取资源或复用已有方案、设置中间检查点",
            "复盘：识别为什么会出现冲突（估算偏差、需求变更），改进后续排期方式"
        ],
        "hints": "核心是“及时沟通取舍”，不是“我能加班全做完”"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "你觉得自己最大的优势与最需要改进的地方分别是什么？",
        "reference_points": [
            "优势要有证据支撑（具体事例或他人反馈），并与岗位核心要求相关",
            "不足要真实、可控、且已在改进：说明它带来的具体困扰与正在采取的措施、初步效果",
            "避免套路化缺点（过于追求完美、工作太投入），也避免暴露岗位致命短板（如后端岗说自己逻辑差）",
            "展现自我认知的客观性：能区分“能力不足”与“经验不足”",
            "语气平稳，不过度自夸也不自我贬损"
        ],
        "hints": "面试官会追问举例，准备好支撑材料"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 120,
        "text": "你如何快速上手一个不熟悉的技术栈或一个陌生的大型项目？",
        "reference_points": [
            "先建立地图：读文档/架构说明、跑通本地环境、看部署与调用链路，再挑一条最简单的业务链路端到端追代码",
            "动手优先：用一个小需求或修 bug 作为切入点，通过改动验证理解，而不是只读代码",
            "善用资源：问对人（先查再问，带着自己的假设问）、看提交历史与 issue 理解设计动机",
            "输出结构化笔记与疑问清单，及时与导师/同事对齐认知偏差",
            "识别风险区：先改影响面小的地方，理解测试与发布流程后再动核心逻辑"
        ],
        "hints": "给一个真实的上手案例和时间线"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "你在团队中通常扮演什么角色？举一个你主动补位的例子。",
        "reference_points": [
            "自我定位清晰（推动者/执行者/协调者/技术攻坚），并说明这种定位的适用与不适用场景",
            "补位例子要有具体情境：谁不在、风险是什么、你做了什么超出职责的事、结果如何",
            "说明补位的边界：临时补位同时推动长期机制（文档、规范、交接），不鼓励常态化越位",
            "体现对他人贡献的认可，不抢功",
            "主动补位与“不守边界”的区别在于是否沟通对齐"
        ],
        "hints": "考察责任心与协作意识，避免只讲个人技术贡献"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "如果入职后发现岗位内容与你的预期不一致，你会怎么办？",
        "reference_points": [
            "先核实与理解：确认岗位真实职责、团队目标与自己预期的差距来源（信息不对称还是临时安排）",
            "主动沟通：与主管对齐期望与成长路径，争取能发挥所长的切入点，而不是消极等待或私下抱怨",
            "寻找价值：即使偏基础的 work 也能找到改进空间（自动化、规范化、沉淀文档）",
            "设定观察期与判断标准，若长期确实不匹配再理性决策，避免情绪化离职",
            "体现成熟度：不承诺“完全无所谓”，也不表现出只挑活干"
        ],
        "hints": "考察稳定性与沟通成熟度，诚实且积极的答案最优"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 60,
        "text": "你有什么想问我们的？",
        "reference_points": [
            "准备 2-3 个有信息量的问题：团队当前最大的技术/业务挑战、这个岗位前三个月的成功标准、代码评审与成长机制",
            "避免只问薪资福利与不加班（可留到 HR 环节），也不要问官网能查到的基础信息",
            "可基于面试过程中的具体回答追问，体现你在认真听",
            "问题反映你的关注层次：技术挑战与成长 > 流程制度 > 待遇",
            "结尾简短表达对岗位的兴趣与匹配点"
        ],
        "hints": "这是最后的加分机会，千万不要说“没有问题”"
    },

    # ================= === 压力题 === =================
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "你简历上这个项目看起来很简单，说实话我认为它的技术含量不高，你怎么看？",
        "reference_points": [
            "先稳定情绪，不辩解不贬低面试官：认可对方视角的合理性（规模/复杂度确实有限）",
            "用事实补充深度：具体说清难点在哪、自己做过哪些超出表面的优化与权衡",
            "诚实承认边界：如果是校园项目，坦率说明约束条件，并指出若在生产环境会怎么改",
            "把话题引向能力迁移：从这段经历中提炼的可复用方法（排查思路、性能分析、协作）",
            "结尾保持自信而不自负，语气平稳、不攻击问题本身"
        ],
        "hints": "考察情绪管理与自我认知，切忌慌乱或反击"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "刚才那道题你答了五分钟还是没说到关键点，是不是这块基础其实没掌握？",
        "reference_points": [
            "不被标签带情绪：先明确回应“我理解你的顾虑”，再请求用 60 秒重新组织核心结论",
            "立刻给出结构化答案：先结论、再依据、最后边界，展示你能抓住重点",
            "诚实区分：是“知道但表达绕了”还是“确实不熟”，后者要坦承并给出补学计划",
            "把压力转为行动：主动提出可以现场写伪代码或举一个实际案例来证明",
            "全程保持语速平稳，不重复解释自己为什么慢"
        ],
        "hints": "关键动作是“重新组织并给出结论”，不是继续解释"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 120,
        "text": "线上系统在你负责期间出了严重故障造成资损，你现在第一件要做的事是什么？后续怎么处理？",
        "reference_points": [
            "第一优先级是止血恢复：按预案降级/回滚/切流，控制影响面，同时同步相关方与升级通报",
            "保护现场与证据：保留日志、监控快照、变更记录，不在恢复前破坏性排查",
            "恢复后做时间线复盘：故障引入点、发现耗时、处置耗时、影响量化（订单/金额/用户数）",
            "根因用“五个为什么”追到机制层面，改进项分短期修复与长期防御（校验、灰度、监控、演练）",
            "责任态度：不推诿，明确自己该承担的部分，同时避免个人英雄主义，推动系统性改进与对账补偿"
        ],
        "hints": "顺序错了会严重扣分：先止血，再定责，最后复盘改进"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 90,
        "text": "我现在告诉你，你的表现排在今天所有候选人最后，你还有什么想说的？",
        "reference_points": [
            "不被激将、不自我否定：可以先说“这个反馈我记下了”，再问清具体是哪些环节未达预期",
            "把焦点从情绪转到信息：主动请求指出短板，展现可教练性（coachability）",
            "对确实薄弱的环节给出具体补强动作与时间，而不是空喊“我会努力”",
            "重申与岗位最相关的一两个证据，不纠缠、不哀求",
            "结尾体面：无论结果如何都感谢反馈，保持职业感"
        ],
        "hints": "这题没有标准答案，考察的是被否定时的反应模式"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 120,
        "text": "假设你写的方案被架构师全盘否定，而会后你发现他的方案有明显性能隐患，你会怎么做？",
        "reference_points": [
            "先反思：自己的方案被否是否因为考虑不周，架构师可能有你不知道的约束（成本、团队、历史包袱）",
            "用证据而非观点沟通：做一个最小可复现的压测或数据推演，量化隐患与影响面",
            "私下、对事不对人地提出：给出“隐患 + 数据 + 备选缓解方案”，而不是“你错了”",
            "尊重决策权：若对方仍坚持，执行并留痕（书面记录风险与假设），同时设置监控验证",
            "长期机制：推动方案评审模板纳入性能与容量评估项，让风险在评审阶段暴露"
        ],
        "hints": "考察向上沟通与职业成熟度，“越级告状”和“沉默执行”都是低分答案"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "请用 30 秒说服我，为什么我们要录用一个在这轮面试中暴露出这么多问题的候选人？",
        "reference_points": [
            "30 秒内必须有结构：一句定位（我带来的核心价值）+ 两个证据 + 一个短板与补强计划",
            "直面问题不回避：把暴露的短板归因为经验/训练量而非能力上限，并给出可验证的改进路径",
            "强调可迁移性与成长速度：举一个“从零到能用”的真实时间线作为证据",
            "与岗位需求绑定：说明团队当前最需要什么，你恰好能提供什么（哪怕需要一点时间）",
            "语气坚定、简洁，不乞求也不过度承诺"
        ],
        "hints": "计时压力题，超时会直接扣分，务必练到 30 秒内说完"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "你只有五分钟时间向 CEO 汇报一个他完全不关心细节的技术风险，你会怎么说？",
        "reference_points": [
            "结论先行：一句话说清风险是什么、对业务的影响（钱/用户/合规）、需要他做什么决策",
            "用业务语言翻译技术：不说“缓存击穿”，说“大促期间有 30% 概率下单失败，影响约 XX 万元 GMV”",
            "给选项而非开放问题：方案 A/B 的投入、收益、剩余风险与建议，明确所需资源与时间",
            "量化不确定性：概率、影响范围、最坏情况与兜底措施",
            "严格控制时间，留出 1 分钟给提问，准备一页纸或一个数字支撑"
        ],
        "hints": "考察信息压缩与向上沟通，切忌陷入技术细节"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "如果入职三个月你负责的需求连续延期两次，主管开始不信任你，你会怎么做？",
        "reference_points": [
            "先自省归因：延期是估算偏差、需求变更、依赖阻塞还是能力短板，用数据还原事实",
            "主动沟通而非等待：向主管同步根因与改进计划，明确可验证的小目标重建信任",
            "改进动作具体化：拆分任务粒度、每日/每两天同步进度、风险提前暴露、把不确定项先做技术验证",
            "寻求反馈与帮助：结对、请同事评审估算，避免独自硬扛再次失手",
            "用连续的小兑现重建信用，同时管理承诺范围（不轻易答应做不到的时间）"
        ],
        "hints": "核心是“主动 + 可验证的小承诺”，不是表忠心"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "现场写一段代码：给一个可能为 null 的嵌套对象链取值，并说明你会如何避免 NPE 在项目中反复出现。",
        "reference_points": [
            "局部处理：Optional 链式 orElse/orElseThrow、Kotlin 安全调用 ?. 与 ?:、Java 判空提前返回",
            "边界处校验：外部输入/反序列化在入口做校验（Bean Validation、schema 校验），内部信任契约",
            "数据模型设计：用空对象模式（Null Object）、默认值集合（Collections.emptyList）替代 null 返回",
            "工程手段：@NonNull/@Nullable 注解 + 静态检查（NullAway/ErrorProne/IDE 检查）、单测覆盖空值分支",
            "监控兜底：全局异常处理与告警，把重复出现的 NPE 当作设计缺陷治理而非逐处补 if"
        ],
        "hints": "先给出可运行代码，再上升到机制，展示工程视野"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "我打断你一下：你说的这些我在你简历里找不到任何支撑，你是不是在编？",
        "reference_points": [
            "保持镇定，不慌不怒：先确认对方具体指哪一部分，避免笼统辩解",
            "给出可核查的证据：仓库链接、部署地址、监控截图、数据口径、可联系的同事/导师",
            "若确实表述夸大，立刻承认并纠正范围（“这里准确说法是……”），诚实比面子重要",
            "不攻击面试官的质疑，主动提出可现场演示或补充材料",
            "把话题拉回能力本身：用一两个可当场验证的问题重新建立信任"
        ],
        "hints": "这题考察诚信与情绪，含糊其辞或过度激动都会出局"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "客户在大群里公开投诉你负责的模块有严重问题，措辞很难听，你的前 30 分钟做什么？",
        "reference_points": [
            "先处理事实与影响，不处理情绪：不在群里对线，第一时间私聊/电话承接并确认具体问题与影响范围",
            "公开回应简短专业：感谢反馈 + 已定位中 + 明确下次同步时间，把沟通引导到可控渠道",
            "内部快速拉通：确认是否真为缺陷、能否回滚/降级、给出临时方案与预计恢复时间",
            "按约定时间同步进展，即使未解决也保持节奏，避免信息真空放大不满",
            "事后复盘：把客户诉求转成需求或缺陷单，补充监控与用例，避免同类问题复发"
        ],
        "hints": "考察情绪管理与对外沟通，切忌“先自证清白”"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "接下来请连续回答三个问题，每个不超过 20 秒，第一题：你最近一次被人指出错误是什么时候？",
        "reference_points": [
            "高压快节奏下先给答案再补上下文，不要开场铺垫或请求思考时间过长",
            "选真实具体的事件（时间、场景、谁指出、错在哪），拒绝泛泛而谈",
            "第二句说明你当时的反应与后续动作（是否当场承认、如何修正）",
            "第三句给改变：加了什么检查机制，之后是否再犯",
            "全程保持节奏与眼神稳定，答完即停，不拖长解释"
        ],
        "hints": "这题真正考的是节奏控制与简洁表达，内容真实即可"
    }
]
