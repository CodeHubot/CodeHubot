# AI助手配置说明

## 功能概述

系统支持通过后台配置来控制单元学习页面是否显示AI助手图标。管理员可以在数据库中修改配置，实时控制AI助手的显示状态。

## 配置项说明

### 配置键名
`enable_ai_assistant_in_unit`

### 配置说明
- **配置键**: `enable_ai_assistant_in_unit`
- **配置值**: `true` (显示) / `false` (隐藏)
- **配置类型**: `boolean`
- **配置分类**: `feature` (功能配置)
- **是否公开**: `是` (前端可直接读取，无需认证)
- **默认值**: `true` (默认显示AI助手)

## 使用方式

### 方式一：执行SQL脚本（推荐）

1. 执行初始化脚本添加配置项：
```bash
mysql -u root -p 数据库名 < SQL/update/38_add_ai_assistant_config.sql
```

2. 修改配置值（启用/禁用AI助手）：
```sql
-- 禁用AI助手
UPDATE core_system_config 
SET config_value = 'false' 
WHERE config_key = 'enable_ai_assistant_in_unit';

-- 启用AI助手
UPDATE core_system_config 
SET config_value = 'true' 
WHERE config_key = 'enable_ai_assistant_in_unit';
```

### 方式二：手动添加配置（如果脚本执行失败）

```sql
-- 添加配置项
INSERT INTO `core_system_config` (
    `config_key`,
    `config_value`,
    `config_type`,
    `description`,
    `category`,
    `is_public`,
    `created_at`,
    `updated_at`
) VALUES (
    'enable_ai_assistant_in_unit',
    'true',
    'boolean',
    '是否在单元学习页面显示AI助手图标',
    'feature',
    1,
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE
    `config_value` = VALUES(`config_value`),
    `updated_at` = NOW();
```

## 配置效果

### 启用AI助手 (`config_value = 'true'`)
- 单元学习页面右下角会显示悬浮的AI助手图标
- 学生可以随时点击AI助手进行学习辅导

### 禁用AI助手 (`config_value = 'false'`)
- 单元学习页面不显示AI助手图标
- 界面更简洁，学生专注于学习内容本身

## 技术实现

### 后端
- 使用 `core_system_config` 表存储配置
- 通过 `/system/configs/public` API 提供公开配置
- 配置项标记为公开（`is_public = 1`），前端无需认证即可读取

### 前端
- 在 `UnitLearning.vue` 页面加载时读取配置
- 使用 `v-if="showAIAssistant"` 控制 `FloatingAIAssistant` 组件的显示
- 配置加载失败时默认显示AI助手，不影响用户体验

## 相关文件

### SQL脚本
- `SQL/update/38_add_ai_assistant_config.sql` - 配置项初始化脚本

### 后端
- `backend/app/models/system_config.py` - 系统配置模型
- `backend/app/api/system_config.py` - 系统配置API
- `backend/app/schemas/system_config.py` - 系统配置Schema

### 前端
- `frontend/src/modules/pbl/student/views/UnitLearning.vue` - 单元学习页面
- `frontend/src/modules/device/api/systemConfig.js` - 系统配置API接口
- `frontend/src/modules/pbl/student/components/FloatingAIAssistant.vue` - AI助手组件

## 注意事项

1. **配置更新即时生效**：修改数据库配置后，用户刷新页面即可看到效果，无需重启服务器
2. **配置值格式**：boolean类型的配置值必须是字符串 `'true'` 或 `'false'`（注意引号）
3. **默认值设计**：配置加载失败时默认显示AI助手，保证功能可用性
4. **权限控制**：该配置为公开配置，所有用户都能读取，但只有平台管理员能修改

## 扩展配置

如果未来需要为其他页面也添加AI助手开关，可以参考此实现添加新的配置项：

```sql
-- 示例：为教师端添加AI助手配置
INSERT INTO `core_system_config` (
    `config_key`,
    `config_value`,
    `config_type`,
    `description`,
    `category`,
    `is_public`
) VALUES (
    'enable_ai_assistant_for_teacher',
    'true',
    'boolean',
    '是否为教师端启用AI助手',
    'feature',
    1
);
```

## 测试建议

1. **测试启用状态**：
   - 设置 `config_value = 'true'`
   - 刷新单元学习页面
   - 确认右下角显示AI助手图标

2. **测试禁用状态**：
   - 设置 `config_value = 'false'`
   - 刷新单元学习页面
   - 确认AI助手图标已隐藏

3. **测试容错性**：
   - 删除或注释掉配置项
   - 刷新页面
   - 确认AI助手仍然显示（降级到默认值）

## 常见问题

**Q: 修改配置后页面没有变化？**
A: 请刷新页面（F5 或 Ctrl+R），配置是在页面加载时读取的。

**Q: 如何查看当前配置值？**
A: 执行SQL查询：
```sql
SELECT * FROM core_system_config WHERE config_key = 'enable_ai_assistant_in_unit';
```

**Q: 能否在前端管理界面修改这个配置？**
A: 目前需要直接操作数据库。如需前端管理界面，可以扩展系统配置管理页面。

**Q: 配置会影响其他页面的AI助手吗？**
A: 不会，此配置只影响单元学习页面（`/pbl/student/units/:uuid`）的AI助手显示。

