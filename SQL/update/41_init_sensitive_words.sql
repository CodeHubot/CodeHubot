-- ========================================
-- AI学习助手 Phase 1 - 敏感词数据大规模初始化
-- 文件: 41_init_sensitive_words.sql
-- 说明: 为中学生学习场景设计的全维度敏感词库 (语法修复版)
-- ========================================

-- 1. 学业诚信类 (针对搜题、代写、直接索要答案)
INSERT IGNORE INTO `pbl_sensitive_words` (`word`, `category`, `severity`, `is_active`) VALUES
('作弊', 'education', 'high', 1),
('考试答案', 'education', 'high', 1),
('代写作业', 'education', 'high', 1),
('作业帮', 'education', 'medium', 1),
('小猿搜题', 'education', 'medium', 1),
('题拍拍', 'education', 'medium', 1),
('抄作业', 'education', 'high', 1),
('代写', 'education', 'high', 1),
('帮我写作文', 'education', 'medium', 1),
('直接给我代码', 'education', 'high', 1),
('泄题', 'education', 'high', 1),
('真题答案', 'education', 'high', 1),
('期末考题', 'education', 'high', 1),
('买答案', 'education', 'high', 1),
('代写代码', 'education', 'high', 1),
('代做', 'education', 'high', 1),
('代考', 'education', 'high', 1);

-- 2. 校园霸凌、辱骂与谐音 (针对学生间可能的语言冲突)
INSERT IGNORE INTO `pbl_sensitive_words` (`word`, `category`, `severity`, `is_active`) VALUES
('傻逼', 'abuse', 'high', 1),
('傻X', 'abuse', 'high', 1),
('煞笔', 'abuse', 'high', 1),
('sb', 'abuse', 'high', 1),
('SB', 'abuse', 'high', 1),
('垃圾', 'abuse', 'low', 1),
('智障', 'abuse', 'medium', 1),
('脑残', 'abuse', 'medium', 1),
('废物', 'abuse', 'medium', 1),
('菜鸡', 'abuse', 'low', 1),
('孤儿', 'abuse', 'high', 1),
('死全家', 'abuse', 'high', 1),
('你妈的', 'abuse', 'high', 1),
('滚蛋', 'abuse', 'medium', 1),
('操你', 'abuse', 'high', 1),
('叼', 'abuse', 'medium', 1),
('屌', 'abuse', 'medium', 1),
('混蛋', 'abuse', 'medium', 1),
('贱人', 'abuse', 'high', 1),
('婊子', 'abuse', 'high', 1),
('底层人', 'abuse', 'medium', 1),
('低端人口', 'abuse', 'high', 1),
('死一边去', 'abuse', 'medium', 1),
('去死', 'abuse', 'high', 1),
('打死你', 'violence', 'high', 1),
('约架', 'violence', 'high', 1),
('放学别走', 'violence', 'high', 1),
('带人堵你', 'violence', 'high', 1),
('扇巴掌', 'violence', 'medium', 1),
('群殴', 'violence', 'high', 1);

-- 3. 心理健康与自残 (最高级别拦截，需引起管理员关注)
INSERT IGNORE INTO `pbl_sensitive_words` (`word`, `category`, `severity`, `is_active`) VALUES
('自杀', 'mental_health', 'high', 1),
('不想活了', 'mental_health', 'high', 1),
('割腕', 'mental_health', 'high', 1),
('跳楼', 'mental_health', 'high', 1),
('安眠药', 'mental_health', 'high', 1),
('吃药自杀', 'mental_health', 'high', 1),
('自残', 'mental_health', 'high', 1),
('抑郁', 'mental_health', 'medium', 1),
('活得太累', 'mental_health', 'medium', 1),
('没意思想死', 'mental_health', 'high', 1),
('烧炭', 'mental_health', 'high', 1),
('投河', 'mental_health', 'high', 1),
('跳轨', 'mental_health', 'high', 1);

-- 4. 色情、低俗与擦边 (针对青春期可能接触的不良信息)
INSERT IGNORE INTO `pbl_sensitive_words` (`word`, `category`, `severity`, `is_active`) VALUES
('色情', 'inappropriate', 'high', 1),
('裸聊', 'inappropriate', 'high', 1),
('约炮', 'inappropriate', 'high', 1),
('福利视频', 'inappropriate', 'high', 1),
('看片', 'inappropriate', 'high', 1),
('黄色网站', 'inappropriate', 'high', 1),
('成人电影', 'inappropriate', 'high', 1),
('自慰', 'inappropriate', 'medium', 1),
('开房', 'inappropriate', 'medium', 1),
('撩妹', 'inappropriate', 'medium', 1),
('勾引', 'inappropriate', 'medium', 1),
('淫秽', 'inappropriate', 'high', 1),
('AV', 'inappropriate', 'high', 1),
('黄片', 'inappropriate', 'high', 1);

-- 5. 违禁品、成瘾性行为与诱导
INSERT IGNORE INTO `pbl_sensitive_words` (`word`, `category`, `severity`, `is_active`) VALUES
('抽烟', 'behavior', 'medium', 1),
('喝酒', 'behavior', 'medium', 1),
('电子烟', 'behavior', 'medium', 1),
('夜店', 'behavior', 'high', 1),
('蹦迪', 'behavior', 'medium', 1),
('网吧', 'behavior', 'low', 1),
('逃课', 'behavior', 'medium', 1),
('大麻', 'illegal', 'high', 1),
('吸毒', 'illegal', 'high', 1),
('k粉', 'illegal', 'high', 1),
('纹身', 'behavior', 'low', 1),
('成人用品', 'behavior', 'high', 1);

-- 6. 金融风险与诈骗 (针对学生防范意识弱)
INSERT IGNORE INTO `pbl_sensitive_words` (`word`, `category`, `severity`, `is_active`) VALUES
('借钱', 'finance', 'low', 1),
('网贷', 'finance', 'high', 1),
('校园贷', 'finance', 'high', 1),
('裸贷', 'finance', 'high', 1),
('兼职刷单', 'finance', 'high', 1),
('高利贷', 'finance', 'high', 1),
('彩票', 'illegal', 'medium', 1),
('博彩', 'illegal', 'high', 1),
('赌博', 'illegal', 'high', 1),
('赢钱', 'illegal', 'medium', 1),
('刷钻', 'finance', 'medium', 1),
('刷粉', 'finance', 'medium', 1);

-- 7. 翻墙与网络代理 (防止学生尝试绕过监管)
INSERT IGNORE INTO `pbl_sensitive_words` (`word`, `category`, `severity`, `is_active`) VALUES
('翻墙', 'politics', 'high', 1),
('梯子', 'politics', 'high', 1),
('VPN', 'politics', 'medium', 1),
('vpn', 'politics', 'medium', 1),
('科学上网', 'politics', 'high', 1),
('Shadowsocks', 'politics', 'high', 1),
('Clash', 'politics', 'high', 1),
('SSR', 'politics', 'high', 1),
('代理服务器', 'politics', 'medium', 1),
('外网', 'politics', 'medium', 1),
('油管', 'politics', 'medium', 1),
('Youtube', 'politics', 'medium', 1),
('推特', 'politics', 'medium', 1),
('Twitter', 'politics', 'medium', 1);

-- 8. 政治敏感与基础红线
INSERT IGNORE INTO `pbl_sensitive_words` (`word`, `category`, `severity`, `is_active`) VALUES
('独裁', 'politics', 'high', 1),
('暴动', 'politics', 'high', 1),
('游行', 'politics', 'high', 1),
('反共', 'politics', 'high', 1),
('习近平', 'politics', 'high', 1),
('党中央', 'politics', 'high', 1),
('反动', 'politics', 'high', 1);

-- 查看最终统计
SELECT category, COUNT(*) as word_count FROM `pbl_sensitive_words` GROUP BY category;
