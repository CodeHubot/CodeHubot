-- ====================================================================
-- 作业附件表添加软删除字段 - 数据库更新脚本
-- 版本: v1.1
-- 创建日期: 2026-01-05
-- 说明: 
--   1. 为 pbl_task_attachments 表添加软删除字段
--   2. 支持附件的软删除功能（标记删除而不物理删除）
--   3. 此脚本可重复执行（使用动态SQL检查字段是否存在）
-- 兼容性: MySQL 5.7 - 8.0
-- ====================================================================

-- 添加 is_deleted 字段（软删除标记）
SET @column_exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_task_attachments' 
    AND COLUMN_NAME = 'is_deleted'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `pbl_task_attachments` ADD COLUMN `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''是否已删除（0:未删除 1:已删除）'' AFTER `file_url`',
    'SELECT "Column is_deleted already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 deleted_at 字段（删除时间）
SET @column_exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_task_attachments' 
    AND COLUMN_NAME = 'deleted_at'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `pbl_task_attachments` ADD COLUMN `deleted_at` DATETIME DEFAULT NULL COMMENT ''删除时间'' AFTER `is_deleted`',
    'SELECT "Column deleted_at already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 deleted_by 字段（删除操作人）
SET @column_exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_task_attachments' 
    AND COLUMN_NAME = 'deleted_by'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `pbl_task_attachments` ADD COLUMN `deleted_by` BIGINT(20) DEFAULT NULL COMMENT ''删除操作人ID'' AFTER `deleted_at`',
    'SELECT "Column deleted_by already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 idx_is_deleted 索引（优化查询性能）
SET @index_exists = (
    SELECT COUNT(*) FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_task_attachments' 
    AND INDEX_NAME = 'idx_is_deleted'
);

SET @sql = IF(@index_exists = 0,
    'ALTER TABLE `pbl_task_attachments` ADD KEY `idx_is_deleted` (`is_deleted`)',
    'SELECT "Index idx_is_deleted already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ----------------------------
-- 更新说明
-- ----------------------------
-- 1. is_deleted: 软删除标记，0表示未删除，1表示已删除
-- 2. deleted_at: 记录删除时间，用于审计追踪
-- 3. deleted_by: 记录删除操作人ID，用于审计追踪
-- 4. 软删除的优势：
--    - 防止误删除，可以恢复数据
--    - 保留审计追踪，符合合规要求
--    - 物理文件保留，避免数据丢失
-- 5. idx_is_deleted: 索引优化查询性能，加速 WHERE is_deleted=0 查询

