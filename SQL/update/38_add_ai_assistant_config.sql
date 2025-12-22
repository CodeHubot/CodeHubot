-- ==========================================================================================================
-- AI助手配置添加脚本
-- ==========================================================================================================
-- 脚本名称: 38_add_ai_assistant_config.sql
-- 脚本版本: 1.0.0
-- 创建日期: 2025-12-22
-- 兼容版本: MySQL 5.7.x, 8.0.x
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
--
-- ==========================================================================================================
-- 脚本说明
-- ==========================================================================================================
--
-- 1. 用途说明:
--    本脚本用于添加单元学习页面AI助手的开关配置
--    管理员可以通过后台控制是否在单元学习页面显示AI助手图标
--
-- 2. 功能特性:
--    - 添加 enable_ai_assistant_in_unit 配置项
--    - 配置为公开配置（is_public=1），前端无需认证即可获取
--    - 默认值为 true（启用AI助手）
--
-- 3. 执行方式:
--    mysql -h hostname -u username -p --default-character-set=utf8mb4 数据库名 < 38_add_ai_assistant_config.sql
--
-- 4. 回滚方式:
--    DELETE FROM `core_system_config` WHERE `config_key` = 'enable_ai_assistant_in_unit';
--
-- ==========================================================================================================

-- 设置字符集
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 显示当前数据库
SELECT '========================================' AS '';
SELECT CONCAT('当前数据库: ', DATABASE()) AS '';
SELECT '开始添加AI助手配置项...' AS '';
SELECT '========================================' AS '';

-- ==========================================================================================================
-- 添加AI助手配置项（使用 INSERT IGNORE 避免重复）
-- ==========================================================================================================

INSERT IGNORE INTO `core_system_config` (
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
    'true',
    'boolean',
    '是否在单元学习页面显示AI助手图标',
    'feature',
    1,
    NOW(),
    NOW()
);

-- 检查插入结果
SELECT '✓ AI助手配置项已添加/确认存在' AS '';
SELECT 
    config_key AS '配置键',
    config_value AS '配置值',
    config_type AS '配置类型',
    description AS '描述',
    category AS '分类',
    is_public AS '是否公开'
FROM `core_system_config` 
WHERE `config_key` = 'enable_ai_assistant_in_unit';

SELECT '========================================' AS '';
SELECT '脚本执行完成！' AS '';
SELECT '========================================' AS '';

