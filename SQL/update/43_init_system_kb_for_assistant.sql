-- ========================================
-- AI学习助手 Phase 1 - 官方知识库初始化
-- 文件: 43_init_system_kb_for_assistant.sql
-- 说明: 可重复执行的更新脚本
-- 功能: 创建内置官方知识库并关联到系统学习助手
-- ========================================

-- 1. 获取管理员用户ID（优先选择平台管理员，否则选第一个用户）
SET @admin_id = (SELECT id FROM `core_users` WHERE `role` = 'platform_admin' LIMIT 1);
SET @admin_id = IFNULL(@admin_id, (SELECT id FROM `core_users` ORDER BY id ASC LIMIT 1));

-- 2. 创建内置官方知识库
-- 使用 INSERT IGNORE 避免重复创建
INSERT IGNORE INTO `kb_main` 
(`uuid`, `name`, `description`, `scope_type`, `owner_id`, `access_level`) 
VALUES (
    'kb-system-ai-curriculum', 
    '人工智能课程官方知识库', 
    '包含AI基础、Python编程、机器人技术等官方教学文档，为学习助手提供权威知识支持。', 
    'system', 
    @admin_id, 
    'public'
);

-- 3. 将知识库关联到学习助手智能体
-- 步骤 A: 获取智能体 ID 和 知识库 ID
SET @agent_id = (SELECT id FROM `agent_main` WHERE `uuid` = 'system-learning-assistant');
SET @kb_id = (SELECT id FROM `kb_main` WHERE `uuid` = 'kb-system-ai-curriculum');

-- 步骤 B: 检查关联是否已存在，不存在则添加
SET @assoc_exists = (
    SELECT COUNT(*) FROM `agent_knowledge_bases` 
    WHERE `agent_id` = @agent_id AND `knowledge_base_id` = @kb_id
);

SET @sql = IF(@assoc_exists = 0,
    'INSERT INTO `agent_knowledge_bases` 
    (`agent_id`, `knowledge_base_id`, `priority`, `is_enabled`, `top_k`, `similarity_threshold`, `retrieval_mode`) 
    VALUES (@agent_id, @kb_id, 10, 1, 5, 0.70, "hybrid")',
    'SELECT "Association already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

