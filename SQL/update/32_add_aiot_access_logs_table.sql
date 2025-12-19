-- ============================================================================
-- 32_add_aiot_access_logs_table.sql
-- 创建访问日志表（config-service 使用）
-- 
-- 功能说明：
-- - 记录设备配置服务的访问日志
-- - 用于简单的速率限制和安全审计
-- 
-- 注意：
-- - 本脚本支持重复执行（使用 CREATE TABLE IF NOT EXISTS）
-- - 兼容 MySQL 5.7-8.0
-- ============================================================================

-- 创建访问日志表
CREATE TABLE IF NOT EXISTS `aiot_access_logs` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `ip_address` VARCHAR(45) NOT NULL COMMENT '访问IP地址（支持IPv4和IPv6）',
  `endpoint` VARCHAR(128) NOT NULL COMMENT '访问的端点路径',
  `mac_address` VARCHAR(17) DEFAULT NULL COMMENT '设备MAC地址（如果有）',
  `success` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '请求是否成功（1=成功，0=失败）',
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '访问时间',
  `user_agent` VARCHAR(256) DEFAULT NULL COMMENT '用户代理字符串',
  
  PRIMARY KEY (`id`),
  KEY `idx_ip_address` (`ip_address`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_mac_address` (`mac_address`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='访问日志表（用于速率限制和安全审计）';

-- 脚本执行完成提示
SELECT 'aiot_access_logs 表创建成功' AS result;
