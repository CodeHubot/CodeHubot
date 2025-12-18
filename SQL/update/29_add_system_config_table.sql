-- ==========================================================================================================
-- 系统配置表创建脚本
-- ==========================================================================================================
-- 脚本名称: 29_add_system_config_table.sql
-- 脚本版本: 1.0.1
-- 创建日期: 2025-12-17
-- 最后更新: 2025-12-17
-- 兼容版本: MySQL 5.7.x, 8.0.x
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
--
-- ==========================================================================================================
-- 脚本说明
-- ==========================================================================================================
--
-- 1. 用途说明:
--    本脚本用于创建系统配置表，支持管理员动态配置系统功能模块的启用状态
--    包括：用户注册、设备管理模块、AI模块、PBL模块等
--
-- 2. 功能特性:
--    - 支持多种配置类型：string, boolean, integer, json
--    - 支持配置分类管理
--    - 支持公开配置（前端可见）
--    - 自动初始化默认模块配置
--    - 使用纯SQL实现，不依赖存储过程
--    - 可重复执行（幂等性）
--
-- 3. 执行方式:
--    mysql -h hostname -u username -p --default-character-set=utf8mb4 aiot_admin < 29_add_system_config_table.sql
--
-- 4. 回滚方式:
--    如需回滚，执行: DROP TABLE IF EXISTS `core_system_config`;
--
-- 5. 注意事项:
--    - 本脚本可重复执行，已存在的表和数据不会被覆盖
--    - 使用动态SQL和条件判断实现兼容性
--    - 不使用存储过程，纯SQL实现
--
-- ==========================================================================================================

-- 设置字符集
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 显示当前数据库
SELECT '========================================' AS '';
SELECT CONCAT('当前数据库: ', DATABASE()) AS '';
SELECT '开始执行系统配置表创建脚本...' AS '';
SELECT '========================================' AS '';

-- ==========================================================================================================
-- 第一步：创建系统配置表（如果不存在）
-- ==========================================================================================================

CREATE TABLE IF NOT EXISTS `core_system_config` (
    `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '配置ID',
    `config_key` VARCHAR(100) NOT NULL COMMENT '配置键',
    `config_value` TEXT NULL DEFAULT NULL COMMENT '配置值',
    `config_type` VARCHAR(20) NOT NULL DEFAULT 'string' COMMENT '配置类型: string, boolean, integer, json',
    `description` VARCHAR(500) NULL DEFAULT NULL COMMENT '配置描述',
    `category` VARCHAR(50) NOT NULL DEFAULT 'system' COMMENT '配置分类: system, module, feature等',
    `is_public` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否公开（前端可见）',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_config_key` (`config_key`),
    KEY `idx_category` (`category`),
    KEY `idx_is_public` (`is_public`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

SELECT '✓ 表 core_system_config 已确保存在' AS '';

-- ==========================================================================================================
-- 第二步：初始化默认配置数据（使用 INSERT IGNORE 避免重复）
-- ==========================================================================================================

SELECT '开始初始化模块配置...' AS '';

-- 插入配置项：用户注册开关
INSERT IGNORE INTO `core_system_config` (
    `config_key`,
    `config_value`,
    `config_type`,
    `description`,
    `category`,
    `is_public`
) VALUES (
    'enable_user_registration',
    'false',
    'boolean',
    '是否开启用户注册',
    'module',
    1
);

-- 插入配置项：设备管理模块开关
INSERT IGNORE INTO `core_system_config` (
    `config_key`,
    `config_value`,
    `config_type`,
    `description`,
    `category`,
    `is_public`
) VALUES (
    'enable_device_module',
    'true',
    'boolean',
    '是否开启设备管理模块',
    'module',
    1
);

-- 插入配置项：AI模块开关
INSERT IGNORE INTO `core_system_config` (
    `config_key`,
    `config_value`,
    `config_type`,
    `description`,
    `category`,
    `is_public`
) VALUES (
    'enable_ai_module',
    'true',
    'boolean',
    '是否开启AI模块',
    'module',
    1
);

-- 插入配置项：PBL模块开关
INSERT IGNORE INTO `core_system_config` (
    `config_key`,
    `config_value`,
    `config_type`,
    `description`,
    `category`,
    `is_public`
) VALUES (
    'enable_pbl_module',
    'true',
    'boolean',
    '是否开启PBL模块',
    'module',
    1
);


-- ==========================================================================================================
-- 附加说明
-- ==========================================================================================================
--
-- 幂等性保证:
-- 1. 使用 CREATE TABLE IF NOT EXISTS 避免重复创建表
-- 2. 使用 INSERT IGNORE 避免插入重复的配置项（基于 UNIQUE KEY）
-- 3. 可以安全地多次执行本脚本
--
-- 兼容性说明:
-- 1. 兼容 MySQL 5.7 和 8.0 版本
-- 2. 不使用存储过程，纯SQL实现
-- 3. 不使用 MySQL 8.0+ 特有语法
--
-- 配置项说明:
-- - enable_user_registration: 控制用户注册功能的开关
-- - enable_device_module: 控制设备管理模块的显示和访问
-- - enable_ai_module: 控制AI智能体、知识库等模块
-- - enable_pbl_module: 控制项目式学习模块
--
-- 配置值说明:
-- - boolean 类型使用字符串 'true' 或 'false'
-- - 判断时支持: 'true', '1', 'yes' 为真
-- - 其他值为假: 'false', '0', 'no' 或其他
--
-- ==========================================================================================================
