-- ====================================================================
-- 作业附件功能 - 数据库更新脚本
-- 版本: v1.0
-- 创建日期: 2026-01-05
-- 说明: 
--   1. 创建作业附件表(pbl_task_attachments)
--   2. 支持学生提交作业时上传Word/PDF附件
--   3. 此脚本可重复执行(使用 CREATE TABLE IF NOT EXISTS)
-- 兼容性: MySQL 5.7 - 8.0
-- ====================================================================

-- ----------------------------
-- Table structure for pbl_task_attachments
-- ----------------------------
CREATE TABLE IF NOT EXISTS `pbl_task_attachments` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '附件ID',
  `uuid` VARCHAR(36) NOT NULL COMMENT 'UUID，唯一标识',
  `progress_id` BIGINT(20) NOT NULL COMMENT '任务进度ID（关联pbl_task_progress）',
  `user_id` BIGINT(20) NOT NULL COMMENT '上传用户ID',
  `filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
  `stored_filename` VARCHAR(255) NOT NULL COMMENT '存储文件名（UUID生成）',
  `file_type` VARCHAR(50) NOT NULL COMMENT '文件类型（word/pdf）',
  `file_ext` VARCHAR(20) NOT NULL COMMENT '文件扩展名（.doc/.docx/.pdf）',
  `file_size` BIGINT(20) NOT NULL COMMENT '文件大小（字节）',
  `file_url` VARCHAR(500) NOT NULL COMMENT '文件访问路径',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已删除（0:未删除 1:已删除）',
  `deleted_at` DATETIME DEFAULT NULL COMMENT '删除时间',
  `deleted_by` BIGINT(20) DEFAULT NULL COMMENT '删除操作人ID',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_uuid` (`uuid`),
  KEY `idx_progress_id` (`progress_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='PBL作业附件表';

-- ----------------------------
-- 说明
-- ----------------------------
-- 1. progress_id: 关联到 pbl_task_progress 表，一个任务提交可以有多个附件
-- 2. file_type: 区分文件类型（word/pdf），用于前端展示不同图标
-- 3. file_ext: 保存实际的文件扩展名，用于下载时设置正确的Content-Type
-- 4. stored_filename: 使用UUID生成的唯一文件名，防止文件名冲突
-- 5. file_url: 相对路径，如 /uploads/task-attachments/xxx.pdf
-- 6. 附件与任务进度绑定，删除任务进度时可级联删除附件
-- 7. is_deleted: 软删除标记，0表示未删除，1表示已删除
-- 8. deleted_at: 记录删除时间，用于审计追踪
-- 9. deleted_by: 记录删除操作人，用于审计追踪

