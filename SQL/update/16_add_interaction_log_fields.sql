-- ============================================================================
-- 添加交互日志表缺失字段
-- ============================================================================
-- 说明：添加 user_agent 和 session_id 字段，用于记录客户端和会话信息
-- ============================================================================

-- 添加 user_agent 和 session_id 字段
ALTER TABLE `aiot_interaction_logs`
ADD COLUMN `user_agent` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户代理（User-Agent）' AFTER `client_ip`,
ADD COLUMN `session_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '会话ID' AFTER `user_agent`;

