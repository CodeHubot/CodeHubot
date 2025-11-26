-- ============================================================================
-- 添加 LLM 模型惩罚参数字段
-- ============================================================================
-- 说明：添加 frequency_penalty 和 presence_penalty 字段，用于控制模型生成的多样性
-- ============================================================================

-- 添加频率惩罚和存在惩罚字段
ALTER TABLE `aiot_llm_models`
ADD COLUMN `frequency_penalty` decimal(3,2) NOT NULL DEFAULT '0.00' COMMENT '频率惩罚参数' AFTER `enable_deep_thinking`,
ADD COLUMN `presence_penalty` decimal(3,2) NOT NULL DEFAULT '0.00' COMMENT '存在惩罚参数' AFTER `frequency_penalty`,
ADD COLUMN `config` json DEFAULT NULL COMMENT '其他配置参数' AFTER `presence_penalty`;

