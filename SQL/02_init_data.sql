-- ==========================================================================================================
-- CodeHubot 系统初始化数据脚本
-- ==========================================================================================================
-- 
-- 脚本名称: init_data.sql
-- 脚本版本: 1.0.0
-- 创建日期: 2025-01-02
-- 兼容版本: MySQL 5.7.x, 8.0.x
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
--
-- ==========================================================================================================
-- 脚本说明
-- ==========================================================================================================
--
-- 1. 用途说明:
--    本脚本用于初始化 CodeHubot 系统的基础数据，包括：
--    - 系统配置数据
--    - 平台配置信息
--    - 用户协议和隐私政策
--    - AI学习助手配置
--    - 系统知识库
--    - 提示词模板
--
-- 2. 前置条件:
--    - 必须先执行 init_database.sql 创建核心表
--    - 目标数据库已存在且包含所有必需的表
--
-- 3. 执行方式:
--    mysql -h hostname -u username -p --default-character-set=utf8mb4 aiot_admin < init_data.sql
--
-- 4. 注意事项:
--    - 本脚本使用 INSERT IGNORE，可安全重复执行
--    - 如果数据已存在，不会覆盖现有数据
--    - 建议在数据库结构初始化后立即执行
--
-- ==========================================================================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ==========================================================================================================
-- 系统配置数据
-- ==========================================================================================================

SELECT '========================================' AS '';
SELECT '开始初始化系统配置数据...' AS '';
SELECT '========================================' AS '';

-- 平台基础配置
INSERT IGNORE INTO `core_system_config` 
(`config_key`, `config_value`, `config_type`, `description`, `category`, `is_public`) 
VALUES 
('platform_name', 'CodeHubot', 'string', '平台名称', 'system', 1),
('platform_description', 'AIoT智能体开发与管理平台', 'string', '平台描述', 'system', 1),
('enable_user_registration', 'false', 'boolean', '是否开启用户注册', 'module', 1),
('enable_device_module', 'true', 'boolean', '是否开启AIoT设备模块', 'module', 1),
('enable_ai_module', 'true', 'boolean', '是否开启AI智能体模块', 'module', 1);

-- AI智能体模块功能开关
INSERT IGNORE INTO `core_system_config` 
(`config_key`, `config_value`, `config_type`, `description`, `category`, `is_public`) 
VALUES 
('ai_module_knowledge_base_enabled', 'false', 'boolean', 'AI智能体-RAG知识库功能是否启用（暂未开放）', 'feature', 1),
('ai_module_workflow_enabled', 'false', 'boolean', 'AI智能体-工作流编排功能是否启用（暂未开放）', 'feature', 1),
('ai_module_agent_enabled', 'true', 'boolean', 'AI智能体-对话功能是否启用', 'feature', 1),
('ai_module_prompt_template_enabled', 'true', 'boolean', 'AI智能体-插件系统功能是否启用', 'feature', 1);

-- 设备MQTT连接配置
-- ⚠️ 重要：部署完成后需要在管理平台中修改这个配置！
-- 这个地址是告诉物联网设备应该连接到哪个MQTT服务器
-- 必须填写设备可以访问的外部地址（域名或IP）
-- 配置路径：管理平台 -> 系统管理 -> MQTT配置
INSERT IGNORE INTO `core_system_config` 
(`config_key`, `config_value`, `config_type`, `description`, `category`, `is_public`) 
VALUES 
('device_mqtt_broker', 'mqtt.example.com', 'string', '设备连接的MQTT Broker地址（外部可访问的域名或IP）', 'device', 0),
('device_mqtt_port', '1883', 'integer', '设备连接的MQTT Broker端口', 'device', 0),
('device_mqtt_use_ssl', 'false', 'boolean', '设备连接MQTT是否使用SSL/TLS', 'device', 0),
('device_config_server_url', 'http://config.example.com:8001', 'string', '设备配置服务器地址（设备配网时填写，获取MQTT等配置信息）', 'device', 1);

SELECT '✓ 系统配置数据初始化完成' AS '';

-- ==========================================================================================================
-- 用户协议和隐私政策
-- ==========================================================================================================

SELECT '开始初始化用户协议和隐私政策...' AS '';

-- 用户协议
INSERT IGNORE INTO `core_system_config` 
(`config_key`, `config_value`, `config_type`, `description`, `category`, `is_public`) 
VALUES 
('user_agreement', '
# CodeHubot 用户协议

欢迎使用 CodeHubot 智能物联网管理平台！

## 1. 服务条款
1.1 用户应遵守国家相关法律法规
1.2 用户应妥善保管账号和密码
1.3 禁止利用平台从事违法活动

## 2. 使用规范
2.1 尊重知识产权，不得侵权
2.2 保护个人隐私，不得泄露他人信息
2.3 维护平台秩序，不得发布不良信息

## 3. 免责声明
3.1 平台不对用户发布的内容负责
3.2 因不可抗力导致的服务中断，平台不承担责任

更新日期：2025-01-02
', 'text', '用户协议', 'policy', 1);

-- 隐私政策
INSERT IGNORE INTO `core_system_config` 
(`config_key`, `config_value`, `config_type`, `description`, `category`, `is_public`) 
VALUES 
('privacy_policy', '
# CodeHubot 隐私政策

我们重视您的隐私保护。

## 1. 信息收集
1.1 我们收集您的基本信息（用户名、邮箱等）
1.2 我们记录您的操作行为数据
1.3 我们保存您的设备操作日志

## 2. 信息使用
2.1 用于提供平台服务
2.2 用于改进平台功能
2.3 用于数据分析和优化

## 3. 信息保护
3.1 采用加密技术保护数据
3.2 严格限制数据访问权限
3.3 定期备份和安全检查

## 4. 信息共享
4.1 不会向第三方出售您的信息
4.2 依法配合司法机关调查
4.3 征得同意后的技术研究

更新日期：2025-01-02
', 'text', '隐私政策', 'policy', 1);

SELECT '✓ 用户协议和隐私政策初始化完成' AS '';

-- ==========================================================================================================
-- AI学习助手智能体
-- ==========================================================================================================

SELECT '开始初始化AI学习助手...' AS '';

-- 获取管理员用户ID
SET @admin_id = (SELECT id FROM `core_users` WHERE `role` = 'super_admin' LIMIT 1);
SET @admin_id = IFNULL(@admin_id, (SELECT id FROM `core_users` ORDER BY id ASC LIMIT 1));

-- 创建系统AI助手智能体
INSERT IGNORE INTO `agent_main` 
(`uuid`, `name`, `description`, `system_prompt`, `user_id`, `is_system`, `is_active`, `created_at`) 
VALUES (
    'system-ai-assistant',
    'AI智能助手',
    '通用AI助手，提供智能问答、技术咨询和设备控制辅助',
    '你是一个专业的AI智能助手。你的职责是：
1. 理解用户的需求并提供准确的回答
2. 协助用户进行设备管理和控制
3. 提供技术咨询和问题解决方案
4. 分析设备数据并给出合理的建议
5. 保持友好、专业和高效的服务态度',
    @admin_id,
    1,
    1,
    NOW()
);

SELECT '✓ AI智能助手创建完成' AS '';

-- ==========================================================================================================
-- 系统知识库
-- ==========================================================================================================

SELECT '开始初始化系统知识库...' AS '';

-- 创建系统知识库
INSERT IGNORE INTO `kb_main` 
(`uuid`, `name`, `description`, `scope_type`, `owner_id`, `access_level`) 
VALUES (
    'kb-system-ai-docs', 
    'AIoT技术知识库', 
    '包含AI智能体、IoT设备、MQTT协议等技术文档，为AI助手提供专业知识支持。', 
    'system', 
    @admin_id, 
    'public'
);

-- 关联知识库到AI助手
SET @agent_id = (SELECT id FROM `agent_main` WHERE `uuid` = 'system-ai-assistant');
SET @kb_id = (SELECT id FROM `kb_main` WHERE `uuid` = 'kb-system-ai-docs');

INSERT IGNORE INTO `agent_knowledge_bases` 
(`agent_id`, `knowledge_base_id`, `priority`, `is_enabled`, `top_k`, `similarity_threshold`, `retrieval_mode`) 
VALUES (@agent_id, @kb_id, 10, 1, 5, 0.70, 'hybrid');

SELECT '✓ 系统知识库初始化完成' AS '';

-- ==========================================================================================================
-- 执行完成信息
-- ==========================================================================================================

SELECT '========================================' AS '';
SELECT 'CodeHubot 系统初始化数据执行完成！' AS 'Status';
SELECT '========================================' AS '';

-- 统计信息
SELECT 
    'System Config' AS 'Data Type',
    COUNT(*) AS 'Record Count'
FROM `core_system_config`
UNION ALL
SELECT 
    'AI Agents' AS 'Data Type',
    COUNT(*) AS 'Record Count'
FROM `agent_main` WHERE `is_system` = 1
UNION ALL
SELECT 
    'Knowledge Bases' AS 'Data Type',
    COUNT(*) AS 'Record Count'
FROM `kb_main` WHERE `scope_type` = 'system';

SELECT '========================================' AS '';
SELECT '初始化数据已成功导入！' AS '';
SELECT '下一步：根据需要调整配置项' AS '';
SELECT '========================================' AS '';

-- ==========================================================================================================
-- 脚本结束
-- ==========================================================================================================

