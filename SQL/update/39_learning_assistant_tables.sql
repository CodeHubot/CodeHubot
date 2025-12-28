-- ========================================
-- AI学习助手 Phase 1 - 数据库表结构
-- 文件: 39_learning_assistant_tables.sql
-- 说明: 可重复执行的更新脚本
-- 功能: 基础对话 + 上下文感知 + 个性化记忆 + 教师查看 + 内容审核
-- ========================================

-- ========================================
-- 1. 会话表
-- ========================================
CREATE TABLE IF NOT EXISTS `pbl_learning_assistant_conversations` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `uuid` VARCHAR(36) NOT NULL UNIQUE COMMENT '会话UUID',
  `user_id` INT(11) NOT NULL COMMENT '学生用户ID',
  `title` VARCHAR(200) DEFAULT '新的对话' COMMENT '会话标题',
  
  -- 学习上下文
  `course_uuid` VARCHAR(36) DEFAULT NULL COMMENT '关联课程UUID',
  `course_name` VARCHAR(200) DEFAULT NULL COMMENT '课程名称（冗余）',
  `unit_uuid` VARCHAR(36) DEFAULT NULL COMMENT '关联单元UUID',
  `unit_name` VARCHAR(200) DEFAULT NULL COMMENT '单元名称（冗余）',
  `current_resource_id` VARCHAR(36) DEFAULT NULL COMMENT '当前资源ID',
  `current_resource_type` VARCHAR(50) DEFAULT NULL COMMENT '资源类型',
  `current_resource_title` VARCHAR(200) DEFAULT NULL COMMENT '资源标题',
  
  -- 会话来源
  `source` ENUM('manual', 'course_learning', 'homework_help') 
    DEFAULT 'manual' COMMENT '来源：manual=手动新建，course_learning=课程学习，homework_help=作业帮助',
  
  -- 统计信息
  `message_count` INT(11) DEFAULT 0 COMMENT '消息总数',
  `user_message_count` INT(11) DEFAULT 0 COMMENT '用户消息数',
  `ai_message_count` INT(11) DEFAULT 0 COMMENT 'AI消息数',
  
  -- 质量指标
  `helpful_count` INT(11) DEFAULT 0 COMMENT '有帮助的回复数',
  `avg_response_time` INT(11) DEFAULT NULL COMMENT '平均响应时间(ms)',
  
  -- 教师关注
  `teacher_reviewed` TINYINT(1) DEFAULT 0 COMMENT '教师是否已查看',
  `teacher_flagged` TINYINT(1) DEFAULT 0 COMMENT '教师是否标记关注',
  `teacher_comment` TEXT DEFAULT NULL COMMENT '教师备注',
  
  -- 内容审核
  `moderation_status` ENUM('pending', 'approved', 'flagged', 'blocked') 
    DEFAULT 'approved' COMMENT '审核状态',
  `moderation_flags` JSON DEFAULT NULL COMMENT '审核标记',
  
  -- 时间记录
  `started_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `last_message_at` DATETIME DEFAULT NULL COMMENT '最后消息时间',
  `ended_at` DATETIME DEFAULT NULL COMMENT '结束时间',
  
  `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否活跃',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  KEY `idx_user_id` (`user_id`),
  KEY `idx_course_uuid` (`course_uuid`),
  KEY `idx_unit_uuid` (`unit_uuid`),
  KEY `idx_source` (`source`),
  KEY `idx_last_message_at` (`last_message_at`),
  KEY `idx_teacher_flagged` (`teacher_flagged`),
  KEY `idx_moderation_status` (`moderation_status`),
  KEY `idx_user_course` (`user_id`, `course_uuid`),
  KEY `idx_active_recent` (`is_active`, `last_message_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='AI学习助手-会话表';

-- ========================================
-- 2. 消息表
-- ========================================
CREATE TABLE IF NOT EXISTS `pbl_learning_assistant_messages` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `uuid` VARCHAR(36) NOT NULL UNIQUE COMMENT '消息UUID',
  `conversation_id` BIGINT(20) NOT NULL COMMENT '会话ID',
  `role` ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色：user=用户，assistant=AI，system=系统',
  `content` TEXT NOT NULL COMMENT '消息内容',
  `content_hash` VARCHAR(64) DEFAULT NULL COMMENT '内容哈希(用于去重)',
  
  -- 上下文快照（发送时的学习上下文）
  `context_snapshot` JSON DEFAULT NULL COMMENT '上下文快照',
  
  -- AI回复扩展信息
  `knowledge_sources` JSON DEFAULT NULL COMMENT '知识库来源',
  `token_usage` JSON DEFAULT NULL COMMENT 'Token使用量 {"prompt":100,"completion":50,"total":150}',
  `model_used` VARCHAR(100) DEFAULT NULL COMMENT '使用的LLM模型',
  `response_time_ms` INT(11) DEFAULT NULL COMMENT '响应时间(毫秒)',
  
  -- 内容审核
  `moderation_result` JSON DEFAULT NULL COMMENT '审核结果',
  `was_blocked` TINYINT(1) DEFAULT 0 COMMENT '是否被拦截(1=是,0=否)',
  `original_content` TEXT DEFAULT NULL COMMENT '原始内容(如被过滤)',
  
  -- 用户反馈
  `was_helpful` TINYINT(1) DEFAULT NULL COMMENT '是否有帮助(1=是,0=否,NULL=未评价)',
  `user_feedback` TEXT DEFAULT NULL COMMENT '用户反馈文本',
  
  -- 教师干预
  `teacher_corrected` TINYINT(1) DEFAULT 0 COMMENT '教师是否修正',
  `teacher_correction` TEXT DEFAULT NULL COMMENT '教师修正内容',
  
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  KEY `idx_conversation_id` (`conversation_id`),
  KEY `idx_role` (`role`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_was_helpful` (`was_helpful`),
  KEY `idx_teacher_corrected` (`teacher_corrected`),
  KEY `idx_conv_role_created` (`conversation_id`, `role`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='AI学习助手-消息表';

-- 添加外键约束（如果不存在）
SET @fk_exists = (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
    WHERE CONSTRAINT_SCHEMA = DATABASE()
    AND TABLE_NAME = 'pbl_learning_assistant_messages'
    AND CONSTRAINT_NAME = 'fk_pbl_message_conversation'
);

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE `pbl_learning_assistant_messages` 
     ADD CONSTRAINT `fk_pbl_message_conversation` 
     FOREIGN KEY (`conversation_id`) 
     REFERENCES `pbl_learning_assistant_conversations`(`id`) 
     ON DELETE CASCADE',
    'SELECT "Foreign key already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ========================================
-- 3. 学生学习档案表（简化版）
-- ========================================
CREATE TABLE IF NOT EXISTS `pbl_student_learning_profiles` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT(11) NOT NULL UNIQUE COMMENT '学生用户ID',
  
  -- 基础统计
  `total_conversations` INT(11) DEFAULT 0 COMMENT '总对话数',
  `total_messages` INT(11) DEFAULT 0 COMMENT '总消息数',
  `total_questions` INT(11) DEFAULT 0 COMMENT '总提问数',
  
  -- 学习统计
  `courses_learned` JSON DEFAULT NULL COMMENT '学习过的课程列表 [{"uuid":"xxx","name":"xxx","last_active":"2024-01-01"}]',
  `units_learned` JSON DEFAULT NULL COMMENT '学习过的单元列表',
  `total_learning_time` INT(11) DEFAULT 0 COMMENT '总学习时长(分钟)',
  
  -- 知识掌握（简化，JSON存储）
  `knowledge_map` JSON DEFAULT NULL COMMENT '知识掌握地图 {"knowledge_point_id": {"mastery":0.8,"last_practiced":"2024-01-01"}}',
  `weak_points` JSON DEFAULT NULL COMMENT '薄弱知识点列表 ["知识点1","知识点2"]',
  `strong_points` JSON DEFAULT NULL COMMENT '擅长知识点列表',
  
  -- 学习特征
  `learning_style` VARCHAR(50) DEFAULT NULL COMMENT '学习风格(visual/auditory/kinesthetic)',
  `avg_questions_per_session` DECIMAL(10,2) DEFAULT 0 COMMENT '平均每次提问数',
  `preferred_question_types` JSON DEFAULT NULL COMMENT '偏好的问题类型 {"concept":30,"example":50,"practice":20}',
  
  -- 最近活动
  `last_active_at` DATETIME DEFAULT NULL COMMENT '最后活跃时间',
  `last_course_uuid` VARCHAR(36) DEFAULT NULL COMMENT '最近学习课程UUID',
  `last_unit_uuid` VARCHAR(36) DEFAULT NULL COMMENT '最近学习单元UUID',
  
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  KEY `idx_user_id` (`user_id`),
  KEY `idx_last_active` (`last_active_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='学生学习档案表';

-- ========================================
-- 4. 内容审核日志表
-- ========================================
CREATE TABLE IF NOT EXISTS `pbl_content_moderation_logs` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `message_id` BIGINT(20) DEFAULT NULL COMMENT '关联消息ID',
  `conversation_id` BIGINT(20) DEFAULT NULL COMMENT '关联会话ID',
  `user_id` INT(11) NOT NULL COMMENT '用户ID',
  
  `content_type` ENUM('user_message', 'ai_response') COMMENT '内容类型',
  `original_content` TEXT NOT NULL COMMENT '原始内容',
  `filtered_content` TEXT DEFAULT NULL COMMENT '过滤后内容',
  
  -- 审核结果
  `status` ENUM('pass', 'warning', 'blocked') COMMENT '审核状态：pass=通过，warning=警告，blocked=拦截',
  `flags` JSON DEFAULT NULL COMMENT '触发的标记 ["sensitive_words","asking_for_answers"]',
  `risk_score` DECIMAL(5,2) DEFAULT NULL COMMENT '风险分数(0-100)',
  
  -- 审核详情
  `sensitive_words` JSON DEFAULT NULL COMMENT '敏感词列表',
  `moderation_service` VARCHAR(50) DEFAULT NULL COMMENT '审核服务(local/aliyun/baidu)',
  `moderation_response` JSON DEFAULT NULL COMMENT '审核服务原始响应',
  
  -- 处理
  `action_taken` VARCHAR(100) DEFAULT NULL COMMENT '采取的措施',
  `notified_teacher` TINYINT(1) DEFAULT 0 COMMENT '是否通知教师',
  
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  KEY `idx_message_id` (`message_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_conversation_id` (`conversation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='内容审核日志表';

-- ========================================
-- 5. 教师查看日志表
-- ========================================
CREATE TABLE IF NOT EXISTS `pbl_teacher_view_logs` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `teacher_id` INT(11) NOT NULL COMMENT '教师用户ID',
  `student_id` INT(11) NOT NULL COMMENT '学生用户ID',
  `conversation_id` BIGINT(20) DEFAULT NULL COMMENT '查看的会话ID',
  
  `action` VARCHAR(50) NOT NULL COMMENT '操作类型(view_conversations/view_conversation_detail/correct_message/flag_conversation)',
  `details` TEXT DEFAULT NULL COMMENT '操作详情',
  
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  KEY `idx_teacher_id` (`teacher_id`),
  KEY `idx_student_id` (`student_id`),
  KEY `idx_conversation_id` (`conversation_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_teacher_student` (`teacher_id`, `student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='教师查看日志表';

-- ========================================
-- 6. 敏感词库表
-- ========================================
CREATE TABLE IF NOT EXISTS `pbl_sensitive_words` (
  `id` INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `word` VARCHAR(100) NOT NULL COMMENT '敏感词',
  `category` VARCHAR(50) DEFAULT NULL COMMENT '分类',
  `severity` ENUM('low', 'medium', 'high') DEFAULT 'medium' COMMENT '严重程度',
  `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_word` (`word`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='敏感词库';

-- 插入一些示例敏感词（实际使用时需要完善）
INSERT IGNORE INTO `pbl_sensitive_words` (`word`, `category`, `severity`) VALUES
('答案', 'cheating', 'medium'),
('作业答案', 'cheating', 'high'),
('考试答案', 'cheating', 'high'),
('直接给我', 'cheating', 'medium'),
('帮我做', 'cheating', 'high');

-- ========================================
-- 7. 创建系统学习助手智能体记录
-- ========================================

-- 检查系统学习助手是否已存在
SET @agent_exists = (
    SELECT COUNT(*) FROM `agent_main` 
    WHERE `uuid` = 'system-learning-assistant'
);

-- 获取一个有效的用户ID（优先使用超级管理员，其次使用第一个用户）
SET @system_user_id = COALESCE(
    (SELECT id FROM `core_users` WHERE `role` = 'super_admin' ORDER BY `id` ASC LIMIT 1),
    (SELECT id FROM `core_users` ORDER BY `id` ASC LIMIT 1)
);

-- 如果不存在且有有效用户ID，则创建
-- 注意：使用 is_system=1 标记为系统级智能体，虽然有user_id但表示由哪个管理员维护
SET @sql = IF(@agent_exists = 0 AND @system_user_id IS NOT NULL,
    CONCAT("INSERT INTO `agent_main` 
    (`uuid`, `name`, `description`, `system_prompt`, `user_id`, `is_system`, `is_active`, `created_at`) 
    VALUES (
        'system-learning-assistant',
        'AI学习助手',
        '专为学生学习设计的智能助手，提供个性化学习指导和答疑',
        '你是一个耐心的AI学习助手，专门帮助学生学习。你的职责是：\\n1. 引导学生主动思考，而不是直接给出答案\\n2. 根据学生的学习进度和知识掌握情况提供个性化建议\\n3. 鼓励学生自己探索和解决问题\\n4. 当学生遇到困难时，提供循序渐进的提示\\n5. 保持友好、耐心和鼓励的态度',
        ", @system_user_id, ",
        1,
        1,
        NOW()
    )"),
    IF(@agent_exists > 0,
        'SELECT "System learning assistant already exists" AS notice',
        'SELECT "Cannot create agent: No users found in core_users table" AS warning'
    )
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ========================================
-- 执行完成提示
-- ========================================
SELECT 'AI学习助手 Phase 1 数据库表创建完成！' AS result;
SELECT COUNT(*) AS pbl_learning_conversations_count FROM `pbl_learning_assistant_conversations`;
SELECT COUNT(*) AS pbl_learning_messages_count FROM `pbl_learning_assistant_messages`;
SELECT COUNT(*) AS pbl_student_profiles_count FROM `pbl_student_learning_profiles`;
SELECT COUNT(*) AS pbl_moderation_logs_count FROM `pbl_content_moderation_logs`;
SELECT COUNT(*) AS pbl_teacher_view_logs_count FROM `pbl_teacher_view_logs`;
SELECT COUNT(*) AS pbl_sensitive_words_count FROM `pbl_sensitive_words`;
SELECT * FROM `agent_main` WHERE `uuid` = 'system-learning-assistant';

