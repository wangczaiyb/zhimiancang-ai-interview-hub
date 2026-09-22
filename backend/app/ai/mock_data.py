import random
from typing import Dict, Any, List

MOCK_RESUME_PARSED = {
    "education": [
        {
            "school": "北京航空航天大学",
            "major": "计算机科学与技术",
            "degree": "本科",
            "start_date": "2020-09",
            "end_date": "2024-06"
        }
    ],
    "work_experience": [
        {
            "company": "字节跳动",
            "title": "后端开发实习生",
            "description": "参与电商营销平台核心业务开发，负责优惠券中台与秒杀限流服务重构，优化 Redis 缓存与 MySQL 索引。",
            "start_date": "2023-07",
            "end_date": "2024-02"
        }
    ],
    "projects": [
        {
            "name": "高并发电商秒杀与订单中心",
            "role": "核心开发",
            "description": "基于 Spring Boot + Redis + RocketMQ 构建高并发秒杀系统，设计分布式锁与双写一致性保障，支撑单机 5000+ QPS。",
            "technologies": "Java, Spring Boot, Redis, MySQL, RocketMQ",
            "start_date": "2023-09",
            "end_date": "2023-12"
        },
        {
            "name": "企业级微服务权限治理中台",
            "role": "项目负责人",
            "description": "采用 Spring Cloud Alibaba + Gateway + Spring Security 实现细粒度 RBAC 权限控制与动态路由，集成 JWT 与 Redis 令牌黑名单。",
            "technologies": "Spring Cloud, Nacos, Sentinel, Redis, JWT",
            "start_date": "2023-02",
            "end_date": "2023-06"
        }
    ],
    "skills": [
        {"skill_name": "Java", "level": "熟练", "evidence": "熟练掌握 JVM 内存模型、垃圾回收与并发编程"},
        {"skill_name": "Spring Boot", "level": "熟练", "evidence": "深入理解自动装配原理与微服务架构开发"},
        {"skill_name": "MySQL", "level": "熟练", "evidence": "精通 InnoDB 存储引擎、B+树索引优化及事务隔离"},
        {"skill_name": "Redis", "level": "熟练", "evidence": "熟练掌握五大基础数据结构、缓存穿透/击穿/雪崩解决方案与 Redisson 分布式锁"},
        {"skill_name": "计算机网络", "level": "熟练", "evidence": "深入理解 TCP/IP 三次握手四次挥手及 HTTP/HTTPS 协议机制"}
    ],
    "certificates": ["全国计算机等级考试四级", "CET-6 (580分)"],
    "warnings": []
}

MOCK_JD_PARSED = {
    "title": "Java高级后端开发工程师",
    "category": "后端开发",
    "city": "北京",
    "salary_min": 20,
    "salary_max": 35,
    "education": "本科及以上",
    "experience": "1-3年",
    "type": "全职",
    "description": "我们正在寻找一位对高并发、分布式架构有深厚热情与工程实践的后端工程师，负责核心业务中台建设。",
    "duties": "1. 负责核心业务微服务的架构设计、研发与性能调优；\n2. 解决大流量、高并发场景下的可用性与一致性挑战；\n3. 参与关键技术预研与攻关，推动工程效能提升。",
    "requirements": "1. 统招本科及以上学历，计算机相关专业，1-3年 Java 后端研发经验；\n2. 深入理解 Java 基础、JVM 原理、多线程与并发编程；\n3. 熟练掌握 Spring Boot/Cloud 生态与主流持久层框架；\n4. 熟练掌握 MySQL 调优及 Redis 缓存架构设计。",
    "bonus": "具备大厂高并发架构经验或开源项目核心贡献者优先。",
    "skills": [
        {"skill_name": "Java", "level": "熟练", "required": True},
        {"skill_name": "Spring Boot", "level": "熟练", "required": True},
        {"skill_name": "Redis", "level": "熟练", "required": True},
        {"skill_name": "MySQL", "level": "熟练", "required": True},
        {"skill_name": "分布式系统", "level": "熟悉", "required": False}
    ],
    "competencies": [
        {"competency_name": "专业基础", "weight": 30.0, "required_score": 80.0},
        {"competency_name": "项目经验", "weight": 25.0, "required_score": 75.0},
        {"competency_name": "系统设计", "weight": 20.0, "required_score": 75.0},
        {"competency_name": "沟通表达", "weight": 15.0, "required_score": 80.0},
        {"competency_name": "综合素质", "weight": 10.0, "required_score": 80.0}
    ]
}

INTERVIEW_QUESTION_POOL = [
    {
        "skill_name": "Redis",
        "stage": "专业基础",
        "difficulty": "MEDIUM",
        "question": "请详细介绍一下在你的高并发项目中，如何利用 Redis 优化系统性能？在高并发读写下又是如何保障缓存与数据库一致性的？"
    },
    {
        "skill_name": "Redis",
        "stage": "深度探究",
        "difficulty": "HARD",
        "question": "如果在突发极端流量下，热点 Key 发生失效导致‘缓存击穿’，你会采取什么具体方案来防范？互斥锁与逻辑过期在实践中各有什么优劣取舍？"
    },
    {
        "skill_name": "Java并发",
        "stage": "专业基础",
        "difficulty": "MEDIUM",
        "question": "请结合底层源码或内存屏障，聊聊 Java 中 volatile 关键字的作用原理？它能保证线程安全原子性吗，为什么？"
    },
    {
        "skill_name": "MySQL",
        "stage": "专业基础",
        "difficulty": "MEDIUM",
        "question": "在 MySQL InnoDB 中，聚集索引与非聚集索引的底层组织方式有什么区别？为什么我们通常建议使用自增主键？"
    },
    {
        "skill_name": "项目经验",
        "stage": "项目深挖",
        "difficulty": "MEDIUM",
        "question": "请挑选你简历中印象最深的一个项目，详细讲讲你在其中负责的核心模块设计、遇到的最棘手技术难题以及最终的解决思路和量化收益。"
    },
    {
        "skill_name": "系统设计",
        "stage": "系统设计",
        "difficulty": "HARD",
        "question": "如果让你设计一个能够支撑千万级日活的分布式全局唯一发号器（如雪花算法或号段模式），你会如何设计并规避时钟回拨与单点瓶颈？"
    }
]

def generate_mock_evaluation(question_text: str, answer_text: str, seq: int) -> Dict[str, Any]:
    ans = (answer_text or "").strip()
    ans_lower = ans.lower()

    # 1. Detect negative, perfunctory, or trivial answers
    negative_patterns = ["不知道", "没用过", "随便", "不会", "不懂", "不清楚", "没接触过", "跳过", "没做过"]
    is_negative = any(p in ans for p in negative_patterns)
    is_very_short = len(ans) < 12

    # 2. Detect technical depth keywords
    high_tech_keywords = [
        "canal", "binlog", "双删", "延迟双删", "最终一致性", "强一致性", "分布式锁", "redlock",
        "互斥锁", "逻辑过期", "缓存击穿", "缓存穿透", "缓存雪崩", "布隆过滤器", "caffeine",
        "volatile", "内存屏障", "指令重排", "happens-before", "cas", "aqs", "synchronized",
        "聚簇索引", "非聚簇索引", "b+树", "回表", "覆盖索引", "最左前缀", "mvcc", "undo log", "redo log",
        "分库分表", "雪花算法", "时钟回拨", "rocketmq", "kafka", "死信队列", "幂等", "分布式事务", "2pc", "tcc", "seata"
    ]
    matched_tech = [kw for kw in high_tech_keywords if kw in ans_lower]

    if is_negative or (is_very_short and len(matched_tech) == 0):
        # Poor / perfunctory answer
        prof = round(random.uniform(36.0, 48.0), 1)
        rel = round(random.uniform(40.0, 52.0), 1)
        comp = round(random.uniform(30.0, 42.0), 1)
        logic = round(random.uniform(40.0, 50.0), 1)
        depth = round(random.uniform(25.0, 38.0), 1)
        comm = round(random.uniform(45.0, 55.0), 1)
        total_score = round(prof * 0.30 + rel * 0.20 + comp * 0.15 + logic * 0.15 + depth * 0.15 + comm * 0.05, 1)
        action = "SIMPLIFY"
        evidence = ["候选人如实阐释了当前在相关技术点上的储备现状，未给出具体的系统性方案与原理解释"]
        weaknesses = ["对所提核心技术的基础原理、工作机制及生产实践缺乏了解与积累"]
        missing = ["核心基础概念定义", "典型应用场景与基本数据流向", "主流开源中间件实践认知"]
        suggestions = ["建议针对所涉技术模块进行系统性的基础知识补强，从官方文档与基础 API 使用开始深入构建技术栈"]
    elif len(matched_tech) >= 2 or len(ans) >= 60:
        # High quality technical answer
        prof = round(random.uniform(86.0, 93.0), 1)
        rel = round(random.uniform(88.0, 95.0), 1)
        comp = round(random.uniform(82.0, 90.0), 1)
        logic = round(random.uniform(84.0, 92.0), 1)
        depth = round(random.uniform(85.0, 92.0), 1)
        comm = round(random.uniform(84.0, 90.0), 1)
        total_score = round(prof * 0.30 + rel * 0.20 + comp * 0.15 + logic * 0.15 + depth * 0.15 + comm * 0.05, 1)
        action = "DEEP" if seq < 5 else "FINISH"
        matched_str = "、".join(matched_tech[:3]) if matched_tech else "相关核心架构"
        evidence = [
            f"候选人准确阐述了以【{matched_str}】为代表的核心设计思想，具备出色的高并发架构把控力",
            "逻辑清晰条理分明，能结合数据一致性与工程痛点给出切实落地方案"
        ]
        weaknesses = [
            "在极端网络抖动、分布式长事务及节点脑裂场景下的容灾降级与监控告警需进一步细化"
        ]
        missing = [
            "大规模微服务链路中压测 QPS 数据指标佐证",
            "生产级兜底回滚方案的极端容错演练"
        ]
        suggestions = [
            "可结合具体的线上业务压测指标（如 TP99、RT、QPS）量化阐述方案带来的性能增益",
            "面试时可主动对比业界同类技术（如 Redis Redlock vs Zookeeper 分布式锁）的优劣选型取舍"
        ]
    else:
        # Standard/moderate answer
        prof = round(random.uniform(72.0, 80.0), 1)
        rel = round(random.uniform(74.0, 82.0), 1)
        comp = round(random.uniform(68.0, 76.0), 1)
        logic = round(random.uniform(70.0, 78.0), 1)
        depth = round(random.uniform(66.0, 75.0), 1)
        comm = round(random.uniform(75.0, 82.0), 1)
        total_score = round(prof * 0.30 + rel * 0.20 + comp * 0.15 + logic * 0.15 + depth * 0.15 + comm * 0.05, 1)
        action = "FOLLOW_UP" if seq < 5 else "FINISH"
        evidence = [
            "候选人对提问所涉及的技术概念有一定认知，能够完成基本场景的技术表述"
        ]
        weaknesses = [
            "回答偏向基础用法，对底层运行机理与高并发边界条件探讨较浅"
        ]
        missing = [
            "并发安全机制的底层实现原理",
            "性能调优与故障排查思路"
        ]
        suggestions = [
            "建议多结合具体项目场景中的线上踩坑经验展开，增强回答的工程实践深度"
        ]

    return {
        "score": total_score,
        "dimensions": {
            "professional": prof,
            "relevance": rel,
            "completeness": comp,
            "logic": logic,
            "depth": depth,
            "communication": comm
        },
        "evidence": evidence,
        "weaknesses": weaknesses,
        "missing_knowledge": missing,
        "suggestions": suggestions,
        "next_action": action
    }

def generate_adaptive_mock_question(
    job_title: str, seq: int = 1, last_question: str = None, last_answer: str = None, last_score: float = None
) -> Dict[str, Any]:
    if seq == 1 or not last_question or not last_answer:
        return {
            "question": "请详细介绍一下在你的高并发项目中，如何利用 Redis 优化系统性能？在高并发读写下又是如何保障缓存与数据库一致性的？",
            "skill_name": "Redis缓存架构",
            "stage": "专业基础",
            "difficulty": "MEDIUM",
            "hints": "回答时请阐明核心原理，并结合实际项目取舍进行展开说明"
        }

    ans = (last_answer or "").strip()
    ans_lower = ans.lower()
    negative_patterns = ["不知道", "没用过", "随便", "不会", "不懂", "不清楚", "没接触过", "跳过", "没做过"]
    is_negative = any(p in ans for p in negative_patterns)
    is_very_short = len(ans) < 12
    is_poor = is_negative or (is_very_short and not any(k in ans_lower for k in ["redis", "mysql", "lock", "锁", "java"])) or (last_score is not None and last_score < 65)

    lq = last_question or ""

    if is_poor:
        if "redis" in lq.lower() or "缓存" in lq:
            return {
                "question": "注意到上一题你对高并发缓存与数据一致性方案不太熟悉，那么我们从基础切入：请简述 Redis 常见的 5 种基本数据结构（String、List、Hash、Set、ZSet）各自的底层特点与典型应用场景？在日常项目中你最常用哪一种？",
                "skill_name": "Redis核心基础",
                "stage": "基础诊断",
                "difficulty": "EASY",
                "hints": "可以挑选你最熟悉的一到两种数据结构，结合具体业务需求（如计数器、会话共享）展开说明"
            }
        elif "volatile" in lq or "并发" in lq or "线程" in lq:
            return {
                "question": "既然对底层的内存屏障机制不太熟悉，我们换个基础角度：请说说 Java 中创建多线程的几种方式？以及在生产环境中为什么阿里规约明确禁止使用 Executors 直接创建线程池？",
                "skill_name": "Java多线程基础",
                "stage": "基础诊断",
                "difficulty": "EASY",
                "hints": "重点说明固定线程池与可缓存线程池可能引发的 OOM 隐患及 ThreadPoolExecutor 的核心参数"
            }
        elif "索引" in lq or "mysql" in lq.lower():
            return {
                "question": "我们回到数据库基础：在日常编写 SQL 查询时，你通常使用什么工具（如 EXPLAIN）来分析慢 SQL？其中哪些关键指标（如 type、key、rows）最能直接反映索引命中情况？",
                "skill_name": "MySQL慢查分析基础",
                "stage": "基础诊断",
                "difficulty": "EASY",
                "hints": "结合具体日常排查经验说明 EXPLAIN 执行计划中的常见字段含义"
            }
        else:
            return {
                "question": "我们换个更贴近日常业务开发的角度：在你的实际项目开发中，最常处理的业务场景是什么？在实现核心业务接口时，你通常遵循怎样的分层规范（Controller-Service-DAO）与统一异常拦截？",
                "skill_name": "工程规范与业务开发",
                "stage": "基础素养",
                "difficulty": "EASY",
                "hints": "结合日常代码规范与实战项目进行说明"
            }

    # If answer is deep / technical
    if any(k in ans_lower for k in ["canal", "binlog", "双删", "延迟双删", "最终一致性", "分布式锁", "redlock"]) or (last_score is not None and last_score >= 80 and "redis" in lq.lower()):
        return {
            "question": "针对你在上题中提到的 Canal 监听 Binlog 延迟双删方案，在极端网络抖动或 Binlog 消费延迟时，如何处理脏读时间窗口？如果在高吞吐场景下数据库发生主从同步延迟，双删的延迟时间该如何科学动态评估？能否结合分布式锁或版本号机制进行深度展开？",
            "skill_name": "Redis高并发架构与容灾",
            "stage": "深度探究",
            "difficulty": "HARD",
            "hints": "建议结合主从延迟监控、MQ 削峰重试与降级兜底方案深入分析"
        }

    if any(k in ans_lower for k in ["击穿", "穿透", "雪崩", "布隆过滤器", "互斥锁", "逻辑过期"]):
        return {
            "question": "你在刚才的回答中准确提到了防范策略。如果系统面对数十万级瞬时突发流量，互斥锁方案可能导致大量请求线程阻塞在后台，你如何通过逻辑过期配合异步刷新或者多级缓存（本地 Caffeine + 远程 Redis）进一步压降单节点延迟？",
            "skill_name": "多级缓存架构设计",
            "stage": "系统设计",
            "difficulty": "HARD",
            "hints": "结合缓存击穿与本地缓存一致性广播机制展开说明"
        }

    if any(k in ans_lower for k in ["volatile", "aqs", "cas", "synchronized", "内存屏障", "happens-before"]):
        return {
            "question": "既然对底层内存可见性有深入理解，请进一步谈谈 JMM 内存模型中的 Happens-Before 原则？在 AQS（AbstractQueuedSynchronizer）的设计中，又是如何利用 CAS 与 volatile state 巧妙实现独占锁与共享锁同步状态流转的？",
            "skill_name": "JMM与AQS底层架构",
            "stage": "源码深度探究",
            "difficulty": "HARD",
            "hints": "可结合 ReentrantLock 或 Semaphore 内部 Sync 实现进行剖析"
        }

    if any(k in ans_lower for k in ["b+树", "聚簇", "非聚簇", "自增", "回表", "覆盖索引"]):
        return {
            "question": "你对 InnoDB 聚簇索引的组织形式理解很扎实。请进一步分析：在亿级数据量的大表历史归档或深分页（如 LIMIT 10000000, 20）场景下，B+ 树多次回表会造成极高磁盘 I/O，你会采取哪些具体的架构级重构（如子查询延迟关联、基于自增游标或搜索引擎分流）进行彻底根治？",
            "skill_name": "海量数据深分页与存储优化",
            "stage": "高并发海量存储",
            "difficulty": "HARD",
            "hints": "对比延迟关联索引覆盖与基于业务时间游标的方案优劣"
        }

    if seq == 2:
        return {
            "question": "请结合底层源码或内存屏障，聊聊 Java 中 volatile 关键字的作用原理？它能保证线程安全原子性吗，为什么？",
            "skill_name": "Java并发",
            "stage": "专业基础",
            "difficulty": "MEDIUM",
            "hints": "从可见性、有序性及 CPU 指令重排角度切入分析"
        }
    elif seq == 3:
        return {
            "question": "在 MySQL InnoDB 中，聚集索引与非聚集索引的底层组织方式有什么区别？为什么我们通常建议使用自增主键？",
            "skill_name": "MySQL",
            "stage": "专业基础",
            "difficulty": "MEDIUM",
            "hints": "结合 B+ 树页分裂与聚集索引叶子节点结构说明"
        }
    elif seq == 4:
        return {
            "question": "请挑选你简历中印象最深的一个项目，详细讲讲你在其中负责的核心模块设计、遇到的最棘手技术难题以及最终的解决思路和量化收益。",
            "skill_name": "项目经验",
            "stage": "项目深挖",
            "difficulty": "MEDIUM",
            "hints": "建议按照 STAR 法则（情境、任务、行动、结果）进行阐述"
        }
    else:
        return {
            "question": "如果让你设计一个能够支撑千万级日活的分布式全局唯一发号器（如雪花算法或号段模式），你会如何设计并规避时钟回拨与单点瓶颈？",
            "skill_name": "系统设计",
            "stage": "系统设计",
            "difficulty": "HARD",
            "hints": "从算法位分布、WorkerID 分配、时钟同步容错等关键维度分析"
        }

def generate_mock_report(interview_id: int, total_questions: int, scores: List[float] = None) -> Dict[str, Any]:
    avg_score = round(sum(scores) / len(scores), 1) if scores else 82.5
    perf = "表现优异" if avg_score >= 85 else ("表现良好" if avg_score >= 75 else "需继续提升")

    dim_scores = {
        "专业基础": round(random.uniform(82.0, 87.0), 1),
        "项目经验": round(random.uniform(80.0, 86.0), 1),
        "系统设计": round(random.uniform(74.0, 80.0), 1),
        "沟通表达": round(random.uniform(84.0, 89.0), 1),
        "综合素质": round(random.uniform(80.0, 85.0), 1)
    }

    strengths = [
        "Redis 基础扎实：清晰掌握常见数据结构及应用场景，能准确分析缓存穿透与击穿的本质区别",
        "表达逻辑清晰流畅：回答问题分点展开，层次分明，具有良好的技术沟通与表达习惯",
        "项目经历具备真实度：能结合秒杀中台与限流场景讲述工程落地实践，思路严谨"
    ]

    weaknesses = [
        "分布式架构深挖尚需深入：面对复杂分布式事务（如两阶段提交与 TCC）与缓存双写极端异常处理时思考深度略显不足",
        "高并发生产压测经验可更具体：缺乏在极限压力下数据库连接池与慢查询定位的具体量化案例"
    ]

    suggestions = [
        "深入精进 Redis 高级进阶：建议重点复习 Redisson 分布式锁 Watch Dog 续期机制与 Redis 主从复制原理",
        "扩充系统设计实战：建议练习千万级高并发秒杀发号器与分布式链路追踪（SkyWalking/OpenTelemetry）的整体设计思路"
    ]

    summary = f"综合评分 {avg_score} 分，整体技术基本功扎实，具有较强的工程思维与实操能力。在基础组件（Redis、MySQL、Java 并发）方面表现稳定，建议针对高并发极限容灾与分布式架构设计持续深化训练。"

    return {
        "total_score": avg_score,
        "performance_level": perf,
        "dimension_scores": dim_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "summary": summary
    }

def generate_mock_learning_tasks() -> List[Dict[str, Any]]:
    return [
        {
            "title": "夯实 Java 并发与 JVM 底层基础",
            "competency_name": "Java",
            "stage": "第一阶段 · 基础夯实",
            "priority": "HIGH",
            "reason": "面试高频考察 JMM、锁机制与 GC 调优，是岗位 JD 的核心要求",
            "action_type": "READING"
        },
        {
            "title": "精读 Redis 分布式锁与 Redisson 源码实现",
            "competency_name": "Redis",
            "stage": "第一阶段 · 基础夯实",
            "priority": "HIGH",
            "reason": "在面试中针对缓存击穿与分布式锁细节仍有提升空间",
            "action_type": "INTERVIEW_PRACTICE"
        },
        {
            "title": "MySQL 深入调优：慢查询日志排查与执行计划全解",
            "competency_name": "MySQL",
            "stage": "第二阶段 · 专项强化",
            "priority": "HIGH",
            "reason": "岗位要求熟练掌握 B+ 树索引覆盖与聚集索引调优",
            "action_type": "INTERVIEW_PRACTICE"
        },
        {
            "title": "完成 1 次 Redis/MySQL 专项模拟面试并复盘",
            "competency_name": "综合表达",
            "stage": "第二阶段 · 专项强化",
            "priority": "MEDIUM",
            "reason": "通过定向模拟检验专项强化成果，形成可量化的提升证据",
            "action_type": "INTERVIEW_PRACTICE"
        },
        {
            "title": "分布式系统高可用设计：发号器与防重幂等设计演练",
            "competency_name": "系统设计",
            "stage": "第三阶段 · 架构进阶",
            "priority": "MEDIUM",
            "reason": "强化面对架构深挖题的结构化设计与表达输出",
            "action_type": "PROJECT"
        },
        {
            "title": "高并发系统设计模拟面试冲刺",
            "competency_name": "系统设计",
            "stage": "第三阶段 · 架构进阶",
            "priority": "MEDIUM",
            "reason": "综合检验架构进阶成果，冲刺目标岗位终面",
            "action_type": "INTERVIEW_PRACTICE"
        }
    ]
