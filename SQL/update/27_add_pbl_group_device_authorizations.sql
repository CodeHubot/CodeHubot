-- ==========================================================================================================
-- PBL小组设备授权功能
-- ==========================================================================================================
-- 文件: SQL/update/27_add_pbl_group_device_authorizations.sql
-- 版本: 1.0.0
-- 创建日期: 2025-01-XX
-- 兼容版本: MySQL 5.7-8.0
-- 说明: 为PBL课程系统添加设备授权功能，支持教师将设备授权给班级小组
-- ==========================================================================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建PBL小组设备授权表
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
  KEY `idx_group_device_active` (`group_id`, `device_id`, `is_active`),
  CONSTRAINT `fk_group_auth_group` FOREIGN KEY (`group_id`) REFERENCES `pbl_groups` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_group_auth_device` FOREIGN KEY (`device_id`) REFERENCES `device_main` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_group_auth_authorizer` FOREIGN KEY (`authorized_by`) REFERENCES `core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='PBL小组设备授权表（教师授权设备给小组）';

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'PBL小组设备授权表创建成功' AS result;
