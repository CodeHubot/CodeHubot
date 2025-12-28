-- ==========================================================================================================
-- 创建 PBL 小组设备授权表
-- ==========================================================================================================
-- 文件: SQL/update/34_create_pbl_group_device_authorizations.sql
-- 版本: 1.0.0
-- 创建日期: 2025-12-20
-- 兼容版本: MySQL 5.7-8.0
-- 可重复执行: 是
-- 说明: 创建 pbl_group_device_authorizations 表，支持教师将设备授权给班级小组使用
-- ==========================================================================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for pbl_group_device_authorizations
-- PBL小组设备授权表（教师授权设备给小组）
-- ----------------------------
CREATE TABLE IF NOT EXISTS `pbl_group_device_authorizations` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '授权ID',
  `uuid` VARCHAR(36) NOT NULL COMMENT 'UUID唯一标识',
  `group_id` INT(11) NOT NULL COMMENT '小组ID（pbl_groups）',
  `device_id` INT(11) NOT NULL COMMENT '设备ID（device_main）',
  `authorized_by` INT(11) NOT NULL COMMENT '授权人ID（教师）',
  `authorized_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
  `expires_at` TIMESTAMP NULL DEFAULT NULL COMMENT '过期时间（NULL表示永久有效）',
  `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否激活',
  `notes` TEXT COMMENT '备注',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_uuid` (`uuid`),
  UNIQUE KEY `uk_group_device` (`group_id`, `device_id`),
  KEY `idx_group_id` (`group_id`),
  KEY `idx_device_id` (`device_id`),
  KEY `idx_authorized_by` (`authorized_by`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_group_device_active` (`group_id`, `device_id`, `is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='PBL小组设备授权表（教师授权设备给小组）';

-- ----------------------------
-- 添加外键约束（使用动态SQL检查，避免重复添加）
-- ----------------------------

-- 检查并添加 fk_group_auth_group 外键
SET @fk_exists = (
  SELECT COUNT(*) 
  FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_group_device_authorizations' 
    AND CONSTRAINT_NAME = 'fk_group_auth_group'
);

SET @sql = IF(@fk_exists = 0,
  'ALTER TABLE `pbl_group_device_authorizations` ADD CONSTRAINT `fk_group_auth_group` FOREIGN KEY (`group_id`) REFERENCES `pbl_groups` (`id`) ON DELETE CASCADE',
  'SELECT "外键 fk_group_auth_group 已存在，跳过" AS notice'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 fk_group_auth_device 外键
SET @fk_exists = (
  SELECT COUNT(*) 
  FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_group_device_authorizations' 
    AND CONSTRAINT_NAME = 'fk_group_auth_device'
);

SET @sql = IF(@fk_exists = 0,
  'ALTER TABLE `pbl_group_device_authorizations` ADD CONSTRAINT `fk_group_auth_device` FOREIGN KEY (`device_id`) REFERENCES `device_main` (`id`) ON DELETE CASCADE',
  'SELECT "外键 fk_group_auth_device 已存在，跳过" AS notice'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 fk_group_auth_authorizer 外键
SET @fk_exists = (
  SELECT COUNT(*) 
  FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_group_device_authorizations' 
    AND CONSTRAINT_NAME = 'fk_group_auth_authorizer'
);

SET @sql = IF(@fk_exists = 0,
  'ALTER TABLE `pbl_group_device_authorizations` ADD CONSTRAINT `fk_group_auth_authorizer` FOREIGN KEY (`authorized_by`) REFERENCES `core_users` (`id`) ON DELETE CASCADE',
  'SELECT "外键 fk_group_auth_authorizer 已存在，跳过" AS notice'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------
-- 验证表创建结果
-- ----------------------------
SELECT 
  CASE 
    WHEN COUNT(*) > 0 THEN 'SUCCESS: pbl_group_device_authorizations 表已创建'
    ELSE 'ERROR: pbl_group_device_authorizations 表创建失败'
  END AS result
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME = 'pbl_group_device_authorizations';

-- 显示表结构
SHOW CREATE TABLE `pbl_group_device_authorizations`;

-- ==========================================================================================================
-- 脚本执行完成
-- ==========================================================================================================
SELECT '========================================================================================================' AS ' ';
SELECT 'PBL小组设备授权表创建完成！' AS 'Status', NOW() AS 'Completion Time';
SELECT '========================================================================================================' AS ' ';


