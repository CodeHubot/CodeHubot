-- ====================================================================
-- 作业附件软删除功能 - 数据库更新脚本
-- 版本: v1.1
-- 创建日期: 2026-01-05
-- 说明: 
--   1. 为 pbl_task_attachments 表添加软删除字段
--   2. 附件不会被物理删除，只标记为已删除状态
--   3. 保留审计追踪，防止误删除
-- 兼容性: MySQL 5.7 - 8.0
-- ====================================================================

-- 检查并添加 is_deleted 字段
SET @column_exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_task_attachments' 
    AND COLUMN_NAME = 'is_deleted'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `pbl_task_attachments` 
     ADD COLUMN `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''是否已删除(0:未删除 1:已删除)'' AFTER `file_url`',
    'SELECT "Column is_deleted already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 deleted_at 字段
SET @column_exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_task_attachments' 
    AND COLUMN_NAME = 'deleted_at'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `pbl_task_attachments` 
     ADD COLUMN `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT ''删除时间'' AFTER `is_deleted`',
    'SELECT "Column deleted_at already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 deleted_by 字段
SET @column_exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_task_attachments' 
    AND COLUMN_NAME = 'deleted_by'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `pbl_task_attachments` 
     ADD COLUMN `deleted_by` BIGINT(20) NULL DEFAULT NULL COMMENT ''删除操作人ID'' AFTER `deleted_at`',
    'SELECT "Column deleted_by already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 is_deleted 索引
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

-- 检查并添加 deleted_at 索引
SET @index_exists = (
    SELECT COUNT(*) FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_task_attachments' 
    AND INDEX_NAME = 'idx_deleted_at'
);

SET @sql = IF(@index_exists = 0,
    'ALTER TABLE `pbl_task_attachments` ADD KEY `idx_deleted_at` (`deleted_at`)',
    'SELECT "Index idx_deleted_at already exists" AS notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ----------------------------
-- 说明
-- ----------------------------
-- 1. is_deleted: 软删除标记（0:未删除 1:已删除）
-- 2. deleted_at: 删除时间（NULL表示未删除）
-- 3. deleted_by: 删除操作人ID（记录是谁删除的）
-- 4. 物理文件不会被删除，保留在服务器上
-- 5. 查询时需要过滤 is_deleted=0 的记录
-- 6. 管理员可以看到已删除的附件，并可以恢复

