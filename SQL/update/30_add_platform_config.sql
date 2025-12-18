-- ==========================================================================================================
-- 系统平台配置扩展脚本
-- ==========================================================================================================
-- 脚本名称: 30_add_platform_config.sql
-- 脚本版本: 1.0.0
-- 创建日期: 2025-12-19
-- 兼容版本: MySQL 5.7.x, 8.0.x
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
--
-- ==========================================================================================================
-- 脚本说明
-- ==========================================================================================================
--
-- 1. 用途说明:
--    在系统配置表中添加平台基础配置项，包括：
--    - platform_name: 平台名称（默认"CodeHubot"）
--    - platform_description: 平台描述
--    - enable_user_registration: 用户注册开关（默认关闭）
--
-- 2. 功能特性:
--    - 可重复执行（使用 INSERT IGNORE）
--    - 不依赖存储过程
--    - 兼容 MySQL 5.7/8.0
--
-- 3. 执行方式:
--    mysql -h hostname -u username -p --default-character-set=utf8mb4 aiot_admin < 30_add_platform_config.sql
--
-- ==========================================================================================================

-- 设置字符集
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 显示当前数据库
SELECT '========================================' AS '';
SELECT CONCAT('当前数据库: ', DATABASE()) AS '';
SELECT '开始添加平台配置项...' AS '';
SELECT '========================================' AS '';

-- ==========================================================================================================
-- 添加平台配置项
-- ==========================================================================================================

-- 平台名称配置
INSERT IGNORE INTO `core_system_config` (
    `config_key`,
    `config_value`,
    `config_type`,
    `description`,
    `category`,
    `is_public`
) VALUES (
    'platform_name',
    'CodeHubot',
    'string',
    '平台名称',
    'system',
    1
);

-- 平台描述配置
INSERT IGNORE INTO `core_system_config` (
    `config_key`,
    `config_value`,
    `config_type`,
    `description`,
    `category`,
    `is_public`
) VALUES (
    'platform_description',
    '智能物联网管理平台',
    'string',
    '平台描述',
    'system',
    1
);

-- 更新用户注册配置（将默认值改为关闭）
-- 使用动态SQL检查配置是否存在并更新
SET @config_exists = (
    SELECT COUNT(*) 
    FROM `core_system_config` 
    WHERE `config_key` = 'enable_user_registration'
);

-- 如果配置不存在，则插入；否则更新默认值为 false
SET @sql = IF(@config_exists = 0,
    "INSERT INTO `core_system_config` (`config_key`, `config_value`, `config_type`, `description`, `category`, `is_public`) VALUES ('enable_user_registration', 'false', 'boolean', '是否开启用户注册', 'module', 1)",
    "SELECT '用户注册配置已存在，跳过' AS notice"
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 显示结果
SELECT '========================================' AS '';
SELECT '平台配置添加完成！' AS '';
SELECT '========================================' AS '';

-- 显示已添加的配置
SELECT 
    `config_key` AS '配置键',
    `config_value` AS '配置值',
    `description` AS '描述',
    `category` AS '分类',
    `is_public` AS '是否公开'
FROM `core_system_config`
WHERE `config_key` IN (
    'platform_name',
    'platform_description',
    'enable_user_registration'
)
ORDER BY `config_key`;

-- ==========================================================================================================
-- 脚本执行完成
-- ==========================================================================================================
