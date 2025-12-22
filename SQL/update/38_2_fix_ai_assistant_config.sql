-- ==========================================================================================================
-- 快速修复：插入或更新 AI 助手配置项
-- ==========================================================================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用 REPLACE INTO 来插入或更新配置
-- 如果配置已存在（根据 UNIQUE KEY uk_config_key），则先删除再插入
-- 如果不存在，则直接插入
REPLACE INTO `core_system_config` (
    `config_key`,
    `config_value`,
    `config_type`,
    `description`,
    `category`,
    `is_public`,
    `created_at`,
    `updated_at`
) VALUES (
    'enable_ai_assistant_in_unit',
    'false',  -- 设置为 false 来禁用 AI 助手
    'boolean',
    '是否在单元学习页面显示AI助手图标',
    'feature',
    1,  -- 必须是 1（公开配置）
    NOW(),
    NOW()
);

-- 验证插入结果
SELECT '✅ 配置已插入/更新' AS '';
SELECT 
    id AS 'ID',
    config_key AS '配置键',
    config_value AS '配置值 (false=隐藏, true=显示)',
    config_type AS '类型',
    is_public AS '是否公开 (必须是1)'
FROM `core_system_config` 
WHERE `config_key` = 'enable_ai_assistant_in_unit';

SELECT '' AS '';
SELECT '💡 刷新浏览器页面即可看到效果' AS '';

