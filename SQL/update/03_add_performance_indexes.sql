-- =====================================================
-- 性能优化索引脚本
-- 用途：为 PBL 模块的核心表添加性能索引
-- 优化场景：渠道商课程统计查询、学生作业提交统计
-- 创建日期：2026-01-04
-- 可重复执行：是（检查索引是否存在）
-- =====================================================

-- 说明：
-- 此脚本为渠道商课程学生提交统计查询添加必要的索引
-- 预期性能提升：查询时间从 1.5-2秒 降低到 20-50ms（30-100倍提升）
-- 
-- 优化的查询：
-- - /pbl/channel/courses/{uuid}/student-submissions
-- - 学生×单元的作业提交统计
-- 
-- MySQL 兼容性：支持 MySQL 5.7 和 8.0


-- =====================================================
-- 1. pbl_task_progress 表索引
-- 用途：提升学生作业进度查询速度
-- =====================================================

-- 检查索引是否存在
SET @index_exists_1 = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_task_progress' 
    AND INDEX_NAME = 'idx_task_progress_user_task_status'
);

-- 如果索引不存在，则创建
SET @sql_1 = IF(
    @index_exists_1 = 0,
    'CREATE INDEX idx_task_progress_user_task_status ON pbl_task_progress(user_id, task_id, status)',
    'SELECT "索引 idx_task_progress_user_task_status 已存在，跳过创建" AS notice'
);

PREPARE stmt_1 FROM @sql_1;
EXECUTE stmt_1;
DEALLOCATE PREPARE stmt_1;


-- =====================================================
-- 2. pbl_tasks 表索引
-- 用途：提升按单元查询任务的速度
-- =====================================================

-- 检查索引是否存在
SET @index_exists_2 = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_tasks' 
    AND INDEX_NAME = 'idx_task_unit_id'
);

-- 如果索引不存在，则创建
SET @sql_2 = IF(
    @index_exists_2 = 0,
    'CREATE INDEX idx_task_unit_id ON pbl_tasks(unit_id)',
    'SELECT "索引 idx_task_unit_id 已存在，跳过创建" AS notice'
);

PREPARE stmt_2 FROM @sql_2;
EXECUTE stmt_2;
DEALLOCATE PREPARE stmt_2;


-- =====================================================
-- 3. pbl_class_members 表索引
-- 用途：提升班级成员查询速度
-- =====================================================

-- 检查索引是否存在
SET @index_exists_3 = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'pbl_class_members' 
    AND INDEX_NAME = 'idx_class_member_class_active'
);

-- 如果索引不存在，则创建
SET @sql_3 = IF(
    @index_exists_3 = 0,
    'CREATE INDEX idx_class_member_class_active ON pbl_class_members(class_id, is_active)',
    'SELECT "索引 idx_class_member_class_active 已存在，跳过创建" AS notice'
);

PREPARE stmt_3 FROM @sql_3;
EXECUTE stmt_3;
DEALLOCATE PREPARE stmt_3;


-- =====================================================
-- 验证索引创建结果
-- =====================================================

SELECT 
    '=== 索引创建完成，验证结果 ===' AS message;

-- 显示 pbl_task_progress 表的所有索引
SELECT 
    'pbl_task_progress 表索引' AS table_name,
    INDEX_NAME AS index_name,
    COLUMN_NAME AS column_name,
    SEQ_IN_INDEX AS seq_in_index,
    INDEX_TYPE AS index_type
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'pbl_task_progress'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- 显示 pbl_tasks 表的所有索引
SELECT 
    'pbl_tasks 表索引' AS table_name,
    INDEX_NAME AS index_name,
    COLUMN_NAME AS column_name,
    SEQ_IN_INDEX AS seq_in_index,
    INDEX_TYPE AS index_type
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'pbl_tasks'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- 显示 pbl_class_members 表的所有索引
SELECT 
    'pbl_class_members 表索引' AS table_name,
    INDEX_NAME AS index_name,
    COLUMN_NAME AS column_name,
    SEQ_IN_INDEX AS seq_in_index,
    INDEX_TYPE AS index_type
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'pbl_class_members'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- =====================================================
-- 执行说明
-- =====================================================
-- 
-- 执行方法：
-- mysql -u root -p database_name < 03_add_performance_indexes.sql
-- 
-- 或者在 MySQL 客户端中：
-- source /path/to/03_add_performance_indexes.sql;
-- 
-- 回滚方法（如需删除索引）：
-- DROP INDEX idx_task_progress_user_task_status ON pbl_task_progress;
-- DROP INDEX idx_task_unit_id ON pbl_tasks;
-- DROP INDEX idx_class_member_class_active ON pbl_class_members;
-- 
-- 注意事项：
-- 1. 此脚本可以重复执行，不会报错
-- 2. 创建索引可能需要几秒到几分钟，取决于表的数据量
-- 3. 建议在业务低峰期执行
-- 4. 如果表数据量很大（>100万行），建议使用 ALGORITHM=INPLACE 创建索引
-- 
-- =====================================================

