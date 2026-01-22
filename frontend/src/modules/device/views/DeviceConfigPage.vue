<template>
  <div class="device-config-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回设备列表
        </el-button>
        <div class="page-title">
          <h2>{{ device?.name || '设备' }} - 设备配置</h2>
        </div>
      </div>
      <div class="header-controls">
        <el-tag v-if="saving" type="info" effect="plain">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在保存...
        </el-tag>
        <el-tag v-else-if="lastSaveTime" type="success" effect="plain">
          <el-icon><Check /></el-icon>
          已自动保存 ({{ lastSaveTime }})
        </el-tag>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="page-content" v-if="device">
      <el-form :model="configForm" label-width="150px" ref="configFormRef">
        <!-- 传感器配置 -->
        <el-card class="config-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>传感器配置</span>
            </div>
          </template>
          
          <div v-if="sensorConfigs.length > 0">
            <el-form-item
              v-for="(sensor, index) in sensorConfigs"
              :key="sensor.key"
              :label="sensor.name"
            >
              <div class="sensor-config-item">
                <div class="config-row">
                  <el-switch
                    v-model="sensor.enabled"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                  <span class="sensor-info">
                    {{ sensor.type }}
                    {{ sensor.unit ? `单位: ${sensor.unit}` : '' }}
                    {{ sensor.range ? `范围: ${sensor.range.min}-${sensor.range.max}` : '' }}
                  </span>
                </div>
                <!-- 功能描述输入框 - 已注释
                <div class="config-row" style="margin-top: 8px;">
                  <el-input
                    v-model="sensor.custom_name"
                    placeholder="自定义功能描述（如：客厅温度、卧室温度等）"
                    class="description-input"
                    clearable
                  >
                    <template #prepend>功能描述</template>
                  </el-input>
                </div>
                -->
              </div>
            </el-form-item>
          </div>
          <el-empty v-else description="该产品暂无传感器配置" :image-size="80" />
        </el-card>

        <!-- 控制端口配置 -->
        <el-card class="config-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>控制端口配置</span>
            </div>
          </template>
          
          <div v-if="controlConfigs.length > 0">
            <el-form-item
              v-for="(control, index) in controlConfigs"
              :key="control.key"
              :label="control.name"
            >
              <div class="control-config-item">
                <div class="config-row">
                  <el-switch
                    v-model="control.enabled"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                  <span class="control-info">
                    {{ control.type }}
                    {{ control.voltage ? `电压: ${control.voltage}` : '' }}
                  </span>
                </div>
                <!-- 功能描述输入框 - 已注释
                <div class="config-row" style="margin-top: 8px;">
                  <el-input
                    v-model="control.custom_name"
                    placeholder="自定义功能描述（如：客厅灯、卧室台灯、开窗帘、关窗帘、摇尾巴等）"
                    class="description-input"
                    clearable
                  >
                    <template #prepend>功能描述</template>
                  </el-input>
                </div>
                -->
              </div>
            </el-form-item>
          </div>
          <el-empty v-else description="该产品暂无控制端口配置" :image-size="80" />
        </el-card>

        <!-- 预设指令配置 -->
        <el-card class="config-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>预设指令配置</span>
              <el-button type="primary" size="small" @click="showAddPresetDialog">
                <el-icon><Plus /></el-icon>
                添加预设指令
              </el-button>
            </div>
          </template>
          
          <div v-if="presetCommands.length > 0">
            <div
              v-for="(preset, index) in presetCommands"
              :key="index"
              class="preset-item"
            >
              <div class="preset-header">
                <span class="preset-name">{{ preset.name }}</span>
                <span class="preset-type-badge">{{ getPresetTypeLabel(preset.device_type, preset.preset_type) }}</span>
                <div class="preset-actions">
                  <el-button 
                    size="small" 
                    type="success"
                    :loading="testingPreset[preset.preset_key]"
                    @click="testPreset(preset)"
                  >
                    <el-icon><VideoPlay /></el-icon>
                    测试
                  </el-button>
                  <el-button size="small" @click="editPreset(index)">编辑</el-button>
                  <el-button size="small" type="danger" @click="deletePreset(index)">删除</el-button>
                </div>
              </div>
              <div class="preset-details">
                <div class="preset-field" v-if="preset.preset_key">
                  <span class="field-label">预设标识：</span>
                  <span class="field-value preset-key-value">
                    <code>{{ preset.preset_key }}</code>
                    <el-button 
                      size="small" 
                      text 
                      @click="copyPresetKey(preset.preset_key)"
                      style="margin-left: 8px;"
                    >
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-button>
                  </span>
                </div>
                <div class="preset-field">
                  <span class="field-label">设备类型：</span>
                  <span class="field-value">{{ preset.device_type }}</span>
                </div>
                <div class="preset-field">
                  <span class="field-label">预设类型：</span>
                  <span class="field-value">{{ preset.preset_type }}</span>
                </div>
                <div class="preset-field" v-if="preset.device_id !== undefined">
                  <span class="field-label">目标设备：</span>
                  <span class="field-value">{{ getDeviceIdLabel(preset.device_type, preset.device_id) }}</span>
                </div>
                <div class="preset-field" v-if="preset.type === 'sequence' || preset.preset_type === 'sequence'">
                  <span class="field-label">步骤：</span>
                  <span class="field-value">{{ formatSequenceSteps(preset.steps) }}</span>
                </div>
                <div class="preset-field" v-else-if="preset.parameters && Object.keys(preset.parameters).length > 0">
                  <span class="field-label">参数：</span>
                  <span class="field-value">{{ formatParameters(preset.parameters) }}</span>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无预设指令，点击上方按钮添加" :image-size="80" />
        </el-card>
      </el-form>
    </div>

    <!-- 添加/编辑预设指令对话框 -->
    <el-dialog
      v-model="presetDialogVisible"
      :title="presetDialogMode === 'add' ? '添加预设指令' : '编辑预设指令'"
      width="600px"
    >
      <el-form :model="presetForm" label-width="120px" ref="presetFormRef">
        <el-form-item label="指令名称" required>
          <el-input v-model="presetForm.name" placeholder="如：LED流水灯、继电器定时开关等" clearable />
        </el-form-item>
        
        <el-form-item label="设备类型" required>
          <el-select v-model="presetForm.device_type" placeholder="选择设备类型" @change="onDeviceTypeChange">
            <el-option label="LED" value="led" />
            <!-- <el-option label="舵机 (Servo)" value="servo" /> -->
            <el-option label="继电器 (Relay)" value="relay" />
            <el-option label="PWM输出" value="pwm" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="预设类型" required v-if="presetForm.device_type">
          <el-select v-model="presetForm.preset_type" placeholder="选择预设类型" @change="onPresetTypeChange">
            <el-option
              v-for="option in availablePresetTypes"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        
        <!-- 目标设备 - 暂时注释 -->
        <!-- <el-form-item label="目标设备" v-if="presetForm.device_type">
          <el-select v-model="presetForm.device_id" placeholder="选择要控制的设备">
            <el-option
              v-for="port in availablePorts"
              :key="port.value"
              :label="port.label"
              :value="port.value"
            >
              <span>{{ port.label }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px; margin-left: 10px;">
                {{ port.desc }}
              </span>
            </el-option>
          </el-select>
          <span class="form-tip">选择要执行预设指令的具体设备端口</span>
        </el-form-item> -->
        
        <!-- LED - Blink 参数 -->
        <template v-if="presetForm.device_type === 'led' && presetForm.preset_type === 'blink'">
          <el-form-item label="闪烁次数">
            <el-input-number v-model="presetForm.parameters.count" :min="1" :max="100" />
          </el-form-item>
          <el-form-item label="开启时间(ms)">
            <el-input-number v-model="presetForm.parameters.on_time" :min="50" :max="10000" :step="50" />
          </el-form-item>
          <el-form-item label="关闭时间(ms)">
            <el-input-number v-model="presetForm.parameters.off_time" :min="50" :max="10000" :step="50" />
          </el-form-item>
        </template>
        
        <!-- LED - Wave 参数 -->
        <template v-if="presetForm.device_type === 'led' && presetForm.preset_type === 'wave'">
          <el-form-item label="LED序列">
            <el-select
              v-model="ledSequenceMode"
              @change="onLedSequenceModeChange"
              placeholder="选择序列模式"
              style="width: 200px; margin-right: 10px;"
            >
              <el-option label="使用所有LED" value="all" />
              <el-option label="自定义序列" value="custom" />
            </el-select>
            <el-input
              v-if="ledSequenceMode === 'custom'"
              v-model="ledSequenceInput"
              placeholder="如: 1,3,4,2"
              style="width: 200px;"
              @blur="updateLedSequence"
            />
            <span class="form-tip">
              {{ ledSequenceMode === 'all' ? '使用所有可用的LED (1-4)' : '输入LED编号，用逗号分隔，定义流水顺序' }}
            </span>
          </el-form-item>
          
          <el-form-item label="当前序列" v-if="ledSequenceMode === 'custom' && presetForm.parameters.led_sequence && presetForm.parameters.led_sequence.length > 0">
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              <el-tag
                v-for="(ledId, index) in presetForm.parameters.led_sequence"
                :key="index"
                type="info"
                effect="plain"
              >
                {{ index + 1 }}. LED{{ ledId }}
              </el-tag>
            </div>
            <span class="form-tip">流水灯将按此顺序依次点亮</span>
          </el-form-item>
          
          <el-form-item label="间隔时间(ms)">
            <el-input-number v-model="presetForm.parameters.interval_ms" :min="50" :max="5000" :step="50" />
            <span class="form-tip">每个LED亮起的间隔时间</span>
          </el-form-item>
          <el-form-item label="循环次数">
            <el-input-number v-model="presetForm.parameters.cycles" :min="1" :max="100" />
            <span class="form-tip">完整波浪效果重复次数</span>
          </el-form-item>
          <el-form-item label="反向播放">
            <el-switch
              v-model="presetForm.parameters.reverse"
              active-text="是（从后往前）"
              inactive-text="否（从前往后）"
            />
            <span class="form-tip">反向播放将逆序执行LED序列</span>
          </el-form-item>
        </template>
        
        <!-- Servo - Swing 参数（新增：舵机摆动）-->
        <template v-if="presetForm.device_type === 'servo' && presetForm.preset_type === 'swing'">
          <el-form-item label="中心角度">
            <el-input-number v-model="presetForm.parameters.center_angle" :min="0" :max="180" :step="5" />
            <span class="form-tip">摆动的中心位置（0-180度）</span>
          </el-form-item>
          <el-form-item label="摆动幅度">
            <el-input-number v-model="presetForm.parameters.swing_angle" :min="5" :max="90" :step="5" />
            <span class="form-tip">左右摆动的角度（±度数）</span>
          </el-form-item>
          <el-form-item label="摆动速度(ms)">
            <el-input-number v-model="presetForm.parameters.speed" :min="100" :max="2000" :step="100" />
            <span class="form-tip">每次摆动的时间</span>
          </el-form-item>
          <el-form-item label="摆动次数">
            <el-input-number v-model="presetForm.parameters.cycles" :min="1" :max="100" />
            <span class="form-tip">完整左右摆动的次数</span>
          </el-form-item>
        </template>
        
        <!-- Servo - Rotate 参数 -->
        <template v-if="presetForm.device_type === 'servo' && presetForm.preset_type === 'rotate'">
          <el-form-item label="循环次数">
            <el-input-number v-model="presetForm.parameters.cycles" :min="1" :max="100" />
          </el-form-item>
          <el-form-item label="正转时间(ms)">
            <el-input-number v-model="presetForm.parameters.forward_duration" :min="100" :max="30000" :step="100" />
          </el-form-item>
          <el-form-item label="反转时间(ms)">
            <el-input-number v-model="presetForm.parameters.reverse_duration" :min="100" :max="30000" :step="100" />
          </el-form-item>
          <el-form-item label="暂停时间(ms)">
            <el-input-number v-model="presetForm.parameters.pause_time" :min="0" :max="10000" :step="100" />
          </el-form-item>
        </template>
        
        <!-- Relay - Timed Switch 参数 -->
        <template v-if="presetForm.device_type === 'relay' && presetForm.preset_type === 'timed_switch'">
          <el-form-item label="持续时间(ms)">
            <el-input-number v-model="presetForm.parameters.duration" :min="100" :max="60000" :step="100" />
          </el-form-item>
          <el-form-item label="初始状态">
            <el-switch
              v-model="presetForm.parameters.initial_state"
              active-text="开启"
              inactive-text="关闭"
            />
          </el-form-item>
        </template>
        
        <!-- PWM - Fade 渐变参数 -->
        <template v-if="presetForm.device_type === 'pwm' && presetForm.preset_type === 'fade'">
          <el-form-item label="PWM频率(Hz)">
            <el-input-number v-model="presetForm.parameters.frequency" :min="1" :max="40000" :step="100" />
            <span class="form-tip">PWM输出频率</span>
          </el-form-item>
          <el-form-item label="起始占空比(%)">
            <el-input-number v-model="presetForm.parameters.start_duty" :min="0" :max="100" :step="0.1" :precision="1" />
            <span class="form-tip">渐变开始时的占空比</span>
          </el-form-item>
          <el-form-item label="目标占空比(%)">
            <el-input-number v-model="presetForm.parameters.end_duty" :min="0" :max="100" :step="0.1" :precision="1" />
            <span class="form-tip">渐变结束时的占空比</span>
          </el-form-item>
          <el-form-item label="总时长(ms)">
            <el-input-number v-model="presetForm.parameters.duration" :min="100" :max="10000" :step="100" />
            <span class="form-tip">完成渐变的总时间</span>
          </el-form-item>
          <el-form-item label="步进间隔(ms)">
            <el-input-number v-model="presetForm.parameters.step_interval" :min="10" :max="1000" :step="10" />
            <span class="form-tip">每次调整占空比的间隔时间，影响平滑度</span>
          </el-form-item>
        </template>
        
        <!-- PWM - Breathe 呼吸灯参数 -->
        <template v-if="presetForm.device_type === 'pwm' && presetForm.preset_type === 'breathe'">
          <el-form-item label="PWM频率(Hz)">
            <el-input-number v-model="presetForm.parameters.frequency" :min="1" :max="40000" :step="100" />
          </el-form-item>
          <el-form-item label="最小占空比(%)">
            <el-input-number v-model="presetForm.parameters.min_duty" :min="0" :max="100" :step="0.1" :precision="1" />
            <span class="form-tip">呼吸效果的最暗值</span>
          </el-form-item>
          <el-form-item label="最大占空比(%)">
            <el-input-number v-model="presetForm.parameters.max_duty" :min="0" :max="100" :step="0.1" :precision="1" />
            <span class="form-tip">呼吸效果的最亮值</span>
          </el-form-item>
          <el-form-item label="渐亮时间(ms)">
            <el-input-number v-model="presetForm.parameters.fade_in_time" :min="100" :max="5000" :step="100" />
            <span class="form-tip">从暗到亮的时间</span>
          </el-form-item>
          <el-form-item label="渐暗时间(ms)">
            <el-input-number v-model="presetForm.parameters.fade_out_time" :min="100" :max="5000" :step="100" />
            <span class="form-tip">从亮到暗的时间</span>
          </el-form-item>
          <el-form-item label="保持时间(ms)">
            <el-input-number v-model="presetForm.parameters.hold_time" :min="0" :max="3000" :step="100" />
            <span class="form-tip">达到最亮或最暗时的保持时间</span>
          </el-form-item>
          <el-form-item label="循环次数">
            <el-input-number v-model="presetForm.parameters.cycles" :min="1" :max="100" />
            <span class="form-tip">重复呼吸效果的次数</span>
          </el-form-item>
        </template>
        
        <!-- PWM - Step 步进参数 -->
        <template v-if="presetForm.device_type === 'pwm' && presetForm.preset_type === 'step'">
          <el-form-item label="PWM频率(Hz)">
            <el-input-number v-model="presetForm.parameters.frequency" :min="1" :max="40000" :step="100" />
          </el-form-item>
          <el-form-item label="起始占空比(%)">
            <el-input-number v-model="presetForm.parameters.start_duty" :min="0" :max="100" :step="0.1" :precision="1" />
            <span class="form-tip">步进开始时的占空比</span>
          </el-form-item>
          <el-form-item label="目标占空比(%)">
            <el-input-number v-model="presetForm.parameters.end_duty" :min="0" :max="100" :step="0.1" :precision="1" />
            <span class="form-tip">步进结束时的占空比</span>
          </el-form-item>
          <el-form-item label="每步变化值(%)">
            <el-input-number v-model="presetForm.parameters.step_value" :min="0.1" :max="50" :step="0.1" :precision="1" />
            <span class="form-tip">每次步进改变的占空比大小</span>
          </el-form-item>
          <el-form-item label="步进间隔(ms)">
            <el-input-number v-model="presetForm.parameters.step_delay" :min="50" :max="2000" :step="50" />
            <span class="form-tip">每次步进之间的延迟时间</span>
          </el-form-item>
        </template>
        
        <!-- PWM - Pulse 脉冲参数 -->
        <template v-if="presetForm.device_type === 'pwm' && presetForm.preset_type === 'pulse'">
          <el-form-item label="PWM频率(Hz)">
            <el-input-number v-model="presetForm.parameters.frequency" :min="1" :max="40000" :step="100" />
          </el-form-item>
          <el-form-item label="高占空比(%)">
            <el-input-number v-model="presetForm.parameters.duty_high" :min="0" :max="100" :step="0.1" :precision="1" />
            <span class="form-tip">脉冲高电平时的占空比</span>
          </el-form-item>
          <el-form-item label="低占空比(%)">
            <el-input-number v-model="presetForm.parameters.duty_low" :min="0" :max="100" :step="0.1" :precision="1" />
            <span class="form-tip">脉冲低电平时的占空比</span>
          </el-form-item>
          <el-form-item label="高电平时间(ms)">
            <el-input-number v-model="presetForm.parameters.high_time" :min="50" :max="5000" :step="50" />
            <span class="form-tip">保持高占空比的时间</span>
          </el-form-item>
          <el-form-item label="低电平时间(ms)">
            <el-input-number v-model="presetForm.parameters.low_time" :min="50" :max="5000" :step="50" />
            <span class="form-tip">保持低占空比的时间</span>
          </el-form-item>
          <el-form-item label="脉冲次数">
            <el-input-number v-model="presetForm.parameters.cycles" :min="1" :max="100" />
            <span class="form-tip">高低切换的循环次数</span>
          </el-form-item>
        </template>
        
        <!-- PWM - Fixed 固定输出参数 -->
        <template v-if="presetForm.device_type === 'pwm' && presetForm.preset_type === 'fixed'">
          <el-form-item label="PWM频率(Hz)">
            <el-input-number v-model="presetForm.parameters.frequency" :min="1" :max="40000" :step="100" />
            <span class="form-tip">PWM输出频率</span>
          </el-form-item>
          <el-form-item label="占空比(%)">
            <el-input-number v-model="presetForm.parameters.duty_cycle" :min="0" :max="100" :step="0.1" :precision="1" />
            <span class="form-tip">固定的占空比值</span>
          </el-form-item>
          <el-form-item label="持续时间(ms)">
            <el-input-number v-model="presetForm.parameters.duration" :min="0" :max="60000" :step="1000" />
            <span class="form-tip">输出持续时间，0表示持续输出</span>
          </el-form-item>
        </template>
        
        <!-- 序列指令配置 - 优化版：根据设备类型自动适配 -->
        <template v-if="presetForm.preset_type === 'sequence'">
          <el-form-item label="序列步骤">
            <div style="width: 100%;">
              <div v-for="(step, index) in sequenceSteps" :key="index" style="margin-bottom: 16px; padding: 12px; border: 1px solid #dcdfe6; border-radius: 4px; background-color: #f5f7fa;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <span style="font-weight: 600;">步骤 {{ index + 1 }} - {{ getDeviceTypeLabel(presetForm.device_type) }}</span>
                  <el-button size="small" type="danger" text @click="removeSequenceStep(index)">删除</el-button>
                </div>
                <el-form :model="step" label-width="110px" size="small">
                  
                  <!-- LED/继电器类型 -->
                  <template v-if="presetForm.device_type === 'led' || presetForm.device_type === 'relay'">
                    <el-form-item :label="presetForm.device_type === 'led' ? 'LED编号' : '继电器编号'" required>
                      <el-select v-model="step.command.device_id" placeholder="选择设备" style="width: 100%;">
                        <el-option v-for="port in availablePorts" :key="port.value" :label="port.label" :value="port.value" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="状态" required>
                      <el-select v-model="step.command.value" placeholder="选择状态" style="width: 100%;">
                        <el-option label="打开 (ON)" :value="1" />
                        <el-option label="关闭 (OFF)" :value="0" />
                      </el-select>
                    </el-form-item>
                  </template>
                  
                  <!-- 舵机类型 -->
                  <template v-if="presetForm.device_type === 'servo'">
                    <el-form-item label="舵机编号" required>
                      <el-select v-model="step.command.device_id" placeholder="选择舵机" style="width: 100%;">
                        <el-option v-for="port in availablePorts" :key="port.value" :label="port.label" :value="port.value" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="角度(°)" required>
                      <el-input-number v-model="step.command.angle" :min="0" :max="180" style="width: 100%;" />
                      <span class="form-tip">0-180度，90度为中心位置</span>
                    </el-form-item>
                  </template>
                  
                  <!-- PWM类型 -->
                  <template v-if="presetForm.device_type === 'pwm'">
                    <el-form-item label="PWM输出" required>
                      <el-select v-model="step.command.device_id" placeholder="选择输出端口" style="width: 100%;">
                        <el-option v-for="port in availablePorts" :key="port.value" :label="port.label" :value="port.value" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="频率(Hz)" required>
                      <el-input-number v-model="step.command.frequency" :min="1" :max="40000" :step="10" style="width: 100%;" />
                      <span class="form-tip">PWM输出频率</span>
                    </el-form-item>
                    <el-form-item label="占空比(%)" required>
                      <el-input-number v-model="step.command.duty" :min="0" :max="100" :step="0.1" :precision="1" style="width: 100%;" />
                      <span class="form-tip">0-100%</span>
                    </el-form-item>
                  </template>
                  
                  <!-- 延迟时间（所有类型通用） -->
                  <el-form-item label="延迟时间(秒)" required>
                    <el-input-number v-model="step.delay" :min="0" :max="300" :step="0.1" :precision="1" style="width: 100%;" />
                    <span class="form-tip">执行完此步骤后等待多长时间再执行下一步</span>
                  </el-form-item>
                </el-form>
              </div>
              <el-button type="primary" @click="addSequenceStep" style="width: 100%;">
                <el-icon><Plus /></el-icon>
                添加步骤
              </el-button>
              <div style="margin-top: 12px; padding: 12px; background-color: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 4px;">
                <div style="font-size: 13px; color: #1e40af; margin-bottom: 4px;">
                  <strong>💡 提示：</strong>
                </div>
                <ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #1e3a8a;">
                  <li>序列指令会按顺序执行各个步骤</li>
                  <li>延迟时间表示执行完当前步骤后等待的时间</li>
                  <li>最后一步的延迟时间通常设为0</li>
                  <li v-if="presetForm.device_type === 'pwm'">PWM频率一般设置为50Hz（舵机）或1000-5000Hz（LED调光）</li>
                </ul>
              </div>
            </div>
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <el-button @click="presetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePreset">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check, Plus, CopyDocument, Loading, VideoPlay } from '@element-plus/icons-vue'
import { getDevicesWithProductInfo } from '@/api/device'
import { getDeviceConfig, updateDeviceConfig, getDeviceProductConfig, sendDeviceControl } from '@/api/device'
import logger from '../utils/logger'

const route = useRoute()
const router = useRouter()

const device = ref(null)
const loading = ref(false)
const saving = ref(false)
const configFormRef = ref(null)
const sensorConfigs = ref([])
const controlConfigs = ref([])
const presetCommands = ref([])
const originalConfig = ref(null)
const lastSaveTime = ref('')
let saveTimer = null // 防抖定时器

// 测试预设指令的loading状态（使用preset_key作为key）
const testingPreset = ref({})

// 预设指令对话框
const presetDialogVisible = ref(false)
const presetDialogMode = ref('add') // 'add' or 'edit'
const presetFormRef = ref(null)
const editingPresetIndex = ref(-1)

// 预设指令表单
const presetForm = ref({
  name: '',
  preset_key: '',  // 添加预设标识字段
  device_type: '',
  preset_type: '',
  device_id: 0,
  parameters: {}
})

// 产品配置（响应式）
const productConfig = ref(null)

// LED序列相关
const ledSequenceMode = ref('all')  // 'all' 或 'custom'
const ledSequenceInput = ref('')  // 用户输入的LED序列，如 "1,3,4,2"

// 序列指令步骤
const sequenceSteps = ref([])

// 预设类型选项（根据设备类型动态变化）
const presetTypeOptions = {
  led: [
    // { label: 'LED闪烁 (Blink)', value: 'blink', desc: '多次快速闪烁' },
    // { label: 'LED波浪灯 (Wave)', value: 'wave', desc: 'LED依次点亮形成波浪效果' },
    { label: '序列指令 (Sequence)', value: 'sequence', desc: '自定义多步骤控制序列' }
  ],
  servo: [
    // { label: '舵机摆动 (Swing)', value: 'swing', desc: '左右摆动，适合机器狗尾巴等' },
    // { label: '舵机正反转 (Rotate)', value: 'rotate', desc: '连续旋转，适合360度舵机' },
    { label: '序列指令 (Sequence)', value: 'sequence', desc: '自定义多步骤控制序列' }
  ],
  relay: [
    // { label: '继电器定时开关 (Timed Switch)', value: 'timed_switch', desc: '定时自动关闭' },
    { label: '序列指令 (Sequence)', value: 'sequence', desc: '自定义多步骤控制序列' }
  ],
  pwm: [
    // { label: 'PWM渐变 (Fade)', value: 'fade', desc: '占空比从起始值平滑过渡到目标值' },
    // { label: 'PWM呼吸灯 (Breathe)', value: 'breathe', desc: '循环渐亮渐暗，模拟呼吸效果' },
    // { label: 'PWM步进 (Step)', value: 'step', desc: '按照设定的步进值逐级调整' },
    // { label: 'PWM脉冲 (Pulse)', value: 'pulse', desc: '快速在两个占空比之间切换' },
    // { label: 'PWM固定输出 (Fixed)', value: 'fixed', desc: '设置固定的频率和占空比' },
    { label: '序列指令 (Sequence)', value: 'sequence', desc: '自定义多步骤控制序列' }
  ]
}

// 可用的预设类型（根据设备类型）
const availablePresetTypes = computed(() => {
  if (!presetForm.value.device_type) return []
  return presetTypeOptions[presetForm.value.device_type] || []
})

// 简化的端口列表（不依赖productConfig，直接使用默认配置）
const availablePorts = computed(() => {
  const deviceType = presetForm.value.device_type
  if (!deviceType) return []
  
  // 直接返回默认端口配置，不访问productConfig
  const defaultPorts = {
    led: [
      { value: 1, label: 'LED1', desc: 'LED端口1' },
      { value: 2, label: 'LED2', desc: 'LED端口2' },
      { value: 3, label: 'LED3', desc: 'LED端口3' },
      { value: 4, label: 'LED4', desc: 'LED端口4' },
      { value: 0, label: '所有LED', desc: '控制所有LED' }
    ],
    servo: [
      { value: 1, label: '舵机1 (M1)', desc: '舵机端口M1' }
    ],
    relay: [
      { value: 1, label: '继电器1', desc: '继电器端口1' },
      { value: 2, label: '继电器2', desc: '继电器端口2' },
      { value: 0, label: '所有继电器', desc: '控制所有继电器' }
    ],
    pwm: [
      { value: 1, label: 'PWM输出 (M1)', desc: 'M1端口 - GPIO48' },
      { value: 2, label: 'PWM输出 (M2)', desc: 'M2端口 - GPIO40' }
    ]
  }
  
  return defaultPorts[deviceType] || []
})

// 默认参数（根据预设类型）
const defaultParameters = {
  led: {
    blink: { count: 3, on_time: 500, off_time: 500 },
    wave: { interval_ms: 200, cycles: 3, reverse: false }
  },
  servo: {
    swing: { center_angle: 90, swing_angle: 30, speed: 500, cycles: 5 },
    rotate: { cycles: 3, forward_duration: 3000, reverse_duration: 3000, pause_time: 500 }
  },
  relay: {
    timed_switch: { duration: 1000, initial_state: true }
  },
  pwm: {
    fade: { 
      frequency: 50, 
      start_duty: 0.0, 
      end_duty: 100.0, 
      duration: 2000, 
      step_interval: 50 
    },
    breathe: { 
      frequency: 50, 
      min_duty: 0.0, 
      max_duty: 100.0, 
      fade_in_time: 1500, 
      fade_out_time: 1500, 
      hold_time: 500, 
      cycles: 5 
    },
    step: { 
      frequency: 50, 
      start_duty: 0.0, 
      end_duty: 100.0, 
      step_value: 10.0, 
      step_delay: 300 
    },
    pulse: { 
      frequency: 50, 
      duty_high: 80.0, 
      duty_low: 20.0, 
      high_time: 500, 
      low_time: 500, 
      cycles: 10 
    },
    fixed: { 
      frequency: 50, 
      duty_cycle: 7.5, 
      duration: 0 
    }
  }
}

// 从路由参数获取设备UUID
const deviceUuid = computed(() => route.params.uuid)
const deviceId = computed(() => device.value?.id)

// 加载设备信息
const loadDeviceInfo = async () => {
  loading.value = true
  try {
    // 获取所有设备列表，然后根据UUID查找
    const response = await getDevicesWithProductInfo()
    
    if (response.data && Array.isArray(response.data)) {
      // API返回的是数组，直接查找
      device.value = response.data.find(d => d.uuid === deviceUuid.value)
      
      if (device.value) {
        logger.info('找到设备:', device.value.name, 'ID:', device.value.id)
        // 加载设备配置
        await loadDeviceConfig()
      } else {
        logger.warn('未找到设备，UUID:', deviceUuid.value)
        ElMessage.error('设备不存在')
        setTimeout(() => goBack(), 1500)
      }
    } else {
      logger.error('API返回格式错误:', response.data)
      ElMessage.error('加载设备信息失败：API返回格式错误')
      setTimeout(() => goBack(), 1500)
    }
  } catch (error) {
    logger.error('加载设备信息失败:', error)
    ElMessage.error('加载设备信息失败')
    setTimeout(() => goBack(), 1500)
  } finally {
    loading.value = false
  }
}

// 加载设备配置
const loadDeviceConfig = async () => {
  if (!deviceUuid.value) return
  
  try {
    // 加载设备的产品配置（包含传感器和控制端口定义）
    const productConfigResponse = await getDeviceProductConfig(deviceUuid.value)
    productConfig.value = productConfigResponse.data || {}
    
    // 加载设备的自定义配置
    const response = await getDeviceConfig(deviceUuid.value)
    const deviceConfig = response.data || {}
    
    // 调试日志：打印完整的响应数据
    logger.info('设备配置API响应:', response)
    logger.info('解析后的设备配置:', deviceConfig)
    
    originalConfig.value = deviceConfig
    
    // 加载预设指令
    presetCommands.value = deviceConfig.device_preset_commands || []
    logger.info(`加载预设指令: ${presetCommands.value.length} 个`)
    
    // 从产品配置中获取传感器类型定义
    const productSensors = productConfig.value.sensor_types || {}
    const deviceSensorConfig = deviceConfig.device_sensor_config || {}
    
    // 构建传感器配置列表（合并产品配置和设备配置）
    sensorConfigs.value = Object.keys(productSensors).map(key => {
      const productSensor = productSensors[key]
      const deviceSensor = deviceSensorConfig[key] || {}
      
      return {
        key,
        name: productSensor.name || key,
        type: productSensor.type || '',
        enabled: deviceSensor.enabled !== false && productSensor.enabled !== false,
        pin: deviceSensor.pin || productSensor.pin || 0,
        unit: productSensor.unit || '',
        range: productSensor.range || null,
        custom_name: deviceSensor.custom_name || '' // 用户自定义的功能描述
      }
    })
    
    // 从产品配置中获取控制端口定义
    const productControls = productConfig.value.control_ports || {}
    const deviceControlConfig = deviceConfig.device_control_config || {}
    
    // 构建控制端口配置列表（合并产品配置和设备配置）
    controlConfigs.value = Object.keys(productControls).map(key => {
      const productControl = productControls[key]
      const deviceControl = deviceControlConfig[key] || {}
      
      return {
        key,
        name: productControl.name || key,
        type: productControl.type || '',
        enabled: deviceControl.enabled !== false && productControl.enabled !== false,
        pin: deviceControl.pin || productControl.pin || 0,
        voltage: productControl.voltage || '',
        custom_name: deviceControl.custom_name || '' // 用户自定义的功能描述
      }
    })
    
    logger.info('设备配置加载成功，传感器数:', sensorConfigs.value.length, '控制端口数:', controlConfigs.value.length)
    
  } catch (error) {
    logger.error('加载设备配置失败:', error)
    ElMessage.error('加载设备配置失败')
  }
}

// 防抖保存配置（自动保存）
const autoSaveConfig = () => {
  // 清除之前的定时器
  if (saveTimer) {
    clearTimeout(saveTimer)
  }
  
  // 设置新的定时器，1秒后执行保存
  saveTimer = setTimeout(() => {
    saveConfig(true) // true 表示是自动保存
  }, 1000)
}

// 保存配置
const saveConfig = async (isAutoSave = false) => {
  if (!deviceId.value) return
  
  try {
    await configFormRef.value?.validate()
    
    saving.value = true
    
    // 构建配置对象（不保存引脚配置，引脚从产品配置读取）
    const device_sensor_config = {}
    sensorConfigs.value.forEach(sensor => {
      device_sensor_config[sensor.key] = {
        enabled: sensor.enabled,
        custom_name: sensor.custom_name || '' // 保存用户自定义的功能描述
      }
    })
    
    const device_control_config = {}
    controlConfigs.value.forEach(control => {
      device_control_config[control.key] = {
        enabled: control.enabled,
        custom_name: control.custom_name || '' // 保存用户自定义的功能描述
      }
    })
    
    const configData = {
      device_sensor_config,
      device_control_config,
      device_preset_commands: presetCommands.value
    }
    
    await updateDeviceConfig(deviceUuid.value, configData)
    
    // 更新最后保存时间
    const now = new Date()
    lastSaveTime.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
    
    if (!isAutoSave) {
      ElMessage.success('设备配置保存成功')
    }
    
    // 更新原始配置，避免重复触发保存
    originalConfig.value = JSON.parse(JSON.stringify(configData))
  } catch (error) {
    if (error !== false) { // 表单验证失败时不显示错误
      logger.error('保存设备配置失败:', error)
      ElMessage.error(error.response?.data?.detail || '保存设备配置失败')
    }
  } finally {
    saving.value = false
  }
}

// 监听配置变化，自动保存
watch([sensorConfigs, controlConfigs], () => {
  // 只有在初始加载完成后才触发自动保存
  if (device.value && !loading.value) {
    autoSaveConfig()
  }
}, { deep: true })

// 返回设备列表
const goBack = () => {
  router.push('/device/devices')
}

// 预设指令管理方法
const resetPresetForm = () => {
  presetForm.value = {
    name: '',
    preset_key: '',
    device_type: '',
    preset_type: '',
    device_id: 0,
    parameters: {}
  }
  sequenceSteps.value = []
}

const showAddPresetDialog = () => {
  resetPresetForm()
  presetDialogMode.value = 'add'
  editingPresetIndex.value = -1
  presetDialogVisible.value = true
}

const editPreset = (index) => {
  const preset = presetCommands.value[index]
  presetForm.value = JSON.parse(JSON.stringify(preset)) // 深拷贝
  
  // 确保 parameters 字段存在且是对象
  if (!presetForm.value.parameters || typeof presetForm.value.parameters !== 'object') {
    presetForm.value.parameters = {}
  }
  
  presetDialogMode.value = 'edit'
  editingPresetIndex.value = index
  
  console.log('[editPreset] 加载预设:', preset)
  
  // 如果是序列类型，加载步骤并规范化命令结构
  if (preset.type === 'sequence' || preset.preset_type === 'sequence') {
    // 确保 preset_type 被正确设置为 'sequence'
    presetForm.value.preset_type = 'sequence'
    
    if (preset.steps && preset.steps.length > 0) {
      // 规范化每个步骤的命令结构，确保编辑表单能正确显示
      sequenceSteps.value = preset.steps.map(step => {
        const command = step.command || {}
        const normalizedCommand = {
          cmd: command.cmd,
          device_id: command.device_id,
          device_type: command.device_type || command.cmd
        }
        
        // 根据命令类型，规范化控制值字段
        if (command.cmd === 'led' || command.cmd === 'relay') {
          normalizedCommand.value = command.value !== undefined ? command.value : (command.action === 'on' ? 1 : 0)
        } else if (command.cmd === 'servo') {
          normalizedCommand.angle = command.angle !== undefined ? command.angle : command.value
        } else if (command.cmd === 'pwm') {
          normalizedCommand.frequency = command.frequency !== undefined ? command.frequency : 50
          normalizedCommand.duty = command.duty !== undefined ? command.duty : command.value
        }
        
        return {
          command: normalizedCommand,
          delay: step.delay || 0
        }
      })
      
      console.log('[editPreset] 规范化后的序列步骤:', sequenceSteps.value)
    } else {
      sequenceSteps.value = []
      addSequenceStep() // 添加一个默认步骤
    }
  } else {
    sequenceSteps.value = []
    
    // 如果是LED wave预设，初始化序列模式
    if (preset.device_type === 'led' && preset.preset_type === 'wave') {
      if (preset.parameters && preset.parameters.led_sequence && preset.parameters.led_sequence.length > 0) {
        ledSequenceMode.value = 'custom'
        ledSequenceInput.value = preset.parameters.led_sequence.join(',')
      } else {
        ledSequenceMode.value = 'all'
        ledSequenceInput.value = ''
      }
    }
    
    // 对于非序列类型的预设，确保参数正确加载
    const deviceType = presetForm.value.device_type
    const presetType = presetForm.value.preset_type
    // 如果参数为空，使用默认参数
    if (!presetForm.value.parameters || Object.keys(presetForm.value.parameters).length === 0) {
      if (defaultParameters[deviceType] && defaultParameters[deviceType][presetType]) {
        presetForm.value.parameters = JSON.parse(JSON.stringify(defaultParameters[deviceType][presetType]))
      }
    }
  }
  
  presetDialogVisible.value = true
}

const deletePreset = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除这个预设指令吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    presetCommands.value.splice(index, 1)
    ElMessage.success('预设指令已删除')
    
    // 自动保存配置
    autoSaveConfig()
  } catch (error) {
    // 用户取消
  }
}

// 测试预设指令
const testPreset = async (preset) => {
  // 检查设备状态
  if (!device.value) {
    ElMessage.warning('设备信息未加载')
    return
  }

  // 检查设备在线状态（如果有在线状态字段）
  if (device.value.status === 'offline') {
    ElMessage.warning('设备离线，无法测试预设指令')
    return
  }

  const presetKey = preset.preset_key || `preset_${Date.now()}`
  
  if (testingPreset.value[presetKey]) return
  
  testingPreset.value[presetKey] = true
  
  try {
    logger.info('测试预设指令:', preset)
    
    // 根据预设类型构建测试命令
    let command
    
    if (preset.preset_type === 'sequence' || preset.type === 'sequence') {
      // 序列指令
      command = {
        type: 'sequence',
        steps: preset.steps || []
      }
    } else {
      // 单个预设指令
      command = {
        cmd: preset.cmd || preset.device_type,
        device_id: preset.device_id,
        device_type: preset.device_type,
        preset_type: preset.preset_type,
        parameters: preset.parameters || {}
      }
    }
    
    logger.info('发送测试命令:', command)
    
    const response = await sendDeviceControl(deviceUuid.value, command)
    
    if (response.data) {
      if (preset.preset_type === 'sequence' || preset.type === 'sequence') {
        // 序列指令的响应处理
        if (response.data.success) {
          const totalSteps = response.data.total_steps || 0
          const successCount = response.data.executed_steps?.filter(s => s.status === 'success').length || 0
          ElMessage.success(`测试成功：${successCount}/${totalSteps} 步骤执行成功`)
        } else {
          const totalSteps = response.data.total_steps || 0
          const successCount = response.data.executed_steps?.filter(s => s.status === 'success').length || 0
          const failedCount = totalSteps - successCount
          const message = response.data.message || `测试完成：${successCount}/${totalSteps} 步骤成功，${failedCount} 步骤失败`
          ElMessage.warning(message)
          
          // 打印失败详情
          if (response.data.executed_steps) {
            const failedSteps = response.data.executed_steps.filter(s => s.status === 'failed')
            if (failedSteps.length > 0) {
              logger.warn('失败的步骤详情:', failedSteps)
            }
          }
        }
      } else {
        // 单个预设指令的响应处理
        ElMessage.success('预设指令测试成功')
      }
    }
  } catch (error) {
    logger.error('测试预设指令失败:', error)
    ElMessage.error(error.response?.data?.detail || '测试预设指令失败')
  } finally {
    testingPreset.value[presetKey] = false
  }
}

const onDeviceTypeChange = () => {
  console.log('[onDeviceTypeChange] 设备类型改变:', presetForm.value.device_type)
  
  // 切换设备类型时，重置预设类型和参数
  presetForm.value.preset_type = ''
  presetForm.value.parameters = {}
  
  // 直接设置默认设备ID，不调用任何异步函数
  const defaultIds = {
    led: 1,
    servo: 1,
    relay: 1,
    pwm: 2
  }
  
  presetForm.value.device_id = defaultIds[presetForm.value.device_type] || 1
  console.log('[onDeviceTypeChange] 设置设备ID为:', presetForm.value.device_id)
}

const onPresetTypeChange = () => {
  // 切换预设类型时，加载默认参数
  const deviceType = presetForm.value.device_type
  const presetType = presetForm.value.preset_type
  
  // 如果是序列类型，初始化步骤
  if (presetType === 'sequence') {
    sequenceSteps.value = []
    addSequenceStep() // 添加第一个步骤
    presetForm.value.parameters = {}
  } else {
    sequenceSteps.value = []
    if (deviceType && presetType && defaultParameters[deviceType] && defaultParameters[deviceType][presetType]) {
      presetForm.value.parameters = JSON.parse(JSON.stringify(defaultParameters[deviceType][presetType]))
    } else {
      presetForm.value.parameters = {}
    }
  }
  
  // 如果是wave预设，初始化LED序列模式
  if (deviceType === 'led' && presetType === 'wave') {
    // 检查是否有自定义序列
    if (presetForm.value.parameters.led_sequence && presetForm.value.parameters.led_sequence.length > 0) {
      ledSequenceMode.value = 'custom'
      ledSequenceInput.value = presetForm.value.parameters.led_sequence.join(',')
    } else {
      ledSequenceMode.value = 'all'
      ledSequenceInput.value = ''
    }
  }
}

// LED序列模式切换
const onLedSequenceModeChange = () => {
  if (ledSequenceMode.value === 'all') {
    // 使用所有LED，删除自定义序列参数，并设置device_id=0
    if (presetForm.value.parameters.led_sequence) {
      delete presetForm.value.parameters.led_sequence
    }
    ledSequenceInput.value = ''
    // 重要：设置device_id=0来表示所有LED（固件会使用LED1-4）
    presetForm.value.device_id = 0
  } else {
    // 自定义模式，初始化为默认序列
    if (!presetForm.value.parameters.led_sequence) {
      presetForm.value.parameters.led_sequence = [1, 2, 3, 4]
      ledSequenceInput.value = '1,2,3,4'
    }
    // 自定义模式也使用device_id=0，固件会根据led_sequence来控制
    presetForm.value.device_id = 0
  }
}

// 更新LED序列
const updateLedSequence = () => {
  if (ledSequenceMode.value !== 'custom') return
  
  const input = ledSequenceInput.value.trim()
  if (!input) {
    ElMessage.warning('请输入LED序列')
    return
  }
  
  // 解析输入的序列
  try {
    const sequence = input.split(',')
      .map(s => parseInt(s.trim()))
      .filter(n => !isNaN(n) && n >= 1 && n <= 10)  // 过滤有效的LED编号
    
    if (sequence.length === 0) {
      ElMessage.warning('请输入有效的LED编号（1-10）')
      return
    }
    
    // 去重
    const uniqueSequence = [...new Set(sequence)]
    
    presetForm.value.parameters.led_sequence = uniqueSequence
    ledSequenceInput.value = uniqueSequence.join(',')
    
    ElMessage.success(`LED序列已设置: ${uniqueSequence.join(' → ')}`)
  } catch (error) {
    console.error('解析LED序列失败:', error)
    ElMessage.error('LED序列格式错误')
  }
}

// 添加序列步骤 - 根据设备类型自动初始化
const addSequenceStep = () => {
  const deviceType = presetForm.value.device_type || 'led'
  
  // 根据设备类型创建不同的初始命令
  const newStep = {
    command: {
      cmd: deviceType,
      device_type: deviceType,
      device_id: 1
    },
    delay: 0
  }
  
  // 根据设备类型设置默认控制值
  if (deviceType === 'led' || deviceType === 'relay') {
    newStep.command.value = 1
  } else if (deviceType === 'servo') {
    newStep.command.angle = 90
  } else if (deviceType === 'pwm') {
    newStep.command.frequency = 50
    newStep.command.duty = 0
  }
  
  sequenceSteps.value.push(newStep)
  
  console.log('[addSequenceStep] 添加步骤:', newStep)
}

// 删除序列步骤
const removeSequenceStep = (index) => {
  if (sequenceSteps.value.length <= 1) {
    ElMessage.warning('至少需要保留一个步骤')
    return
  }
  sequenceSteps.value.splice(index, 1)
}

const savePreset = () => {
  // 验证表单
  if (!presetForm.value.name) {
    ElMessage.warning('请输入指令名称')
    return
  }
  
  // 如果是序列类型，验证步骤
  if (presetForm.value.preset_type === 'sequence') {
    if (!presetForm.value.device_type) {
      ElMessage.warning('请选择设备类型（用于显示）')
      return
    }
    if (sequenceSteps.value.length === 0) {
      ElMessage.warning('请至少添加一个步骤')
      return
    }
    // 验证每个步骤
    for (let i = 0; i < sequenceSteps.value.length; i++) {
      const step = sequenceSteps.value[i]
      if (!step.command || !step.command.cmd) {
        ElMessage.warning(`步骤 ${i + 1} 缺少命令类型`)
        return
      }
      if (step.command.device_id === undefined || step.command.device_id === null) {
        ElMessage.warning(`步骤 ${i + 1} 缺少设备ID`)
        return
      }
      if (step.delay === undefined || step.delay === null || step.delay < 0) {
        ElMessage.warning(`步骤 ${i + 1} 延迟时间无效`)
        return
      }
      // 确保cmd和device_type与预设的device_type一致
      step.command.cmd = presetForm.value.device_type
      step.command.device_type = presetForm.value.device_type
      
      // 验证PWM类型的额外字段
      if (presetForm.value.device_type === 'pwm') {
        if (!step.command.frequency || step.command.frequency <= 0) {
          ElMessage.warning(`步骤 ${i + 1} 缺少有效的PWM频率`)
          return
        }
        if (step.command.duty === undefined || step.command.duty === null) {
          ElMessage.warning(`步骤 ${i + 1} 缺少占空比值`)
          return
        }
      }
    }
    
    // 生成唯一的preset_key（如果是新增或者编辑时没有preset_key）
    let presetKey = presetForm.value.preset_key
    if (!presetKey) {
      // 生成格式：device_type_timestamp
      const timestamp = Date.now().toString(36)  // 转为36进制缩短长度
      const deviceType = presetForm.value.device_type || 'unknown'
      presetKey = `${deviceType}_seq_${timestamp}`
    }
    
    // 检查preset_key是否重复（编辑模式下排除当前预设）
    const isDuplicate = presetCommands.value.some((preset, index) => {
      // 如果是编辑模式，排除当前正在编辑的预设
      if (presetDialogMode.value === 'edit' && index === editingPresetIndex.value) {
        return false
      }
      return preset.preset_key === presetKey
    })
    
    if (isDuplicate) {
      ElMessage.error('预设标识重复，请重新保存')
      // 重新生成preset_key
      const timestamp = Date.now().toString(36)
      const deviceType = presetForm.value.device_type || 'unknown'
      presetKey = `${deviceType}_seq_${timestamp}_${Math.random().toString(36).substr(2, 5)}`
      presetForm.value.preset_key = presetKey
      console.warn('[savePreset] 检测到preset_key重复，已重新生成:', presetKey)
    }
    
    // 构建序列预设 - 优化命令结构，保留各类型命令的原始字段
    const newPreset = {
      name: presetForm.value.name,
      preset_key: presetKey,  // 添加唯一标识
      type: 'sequence',
      preset_type: 'sequence',
      cmd: 'sequence',
      device_type: presetForm.value.device_type, // 用于显示
      description: presetForm.value.description || `序列预设：${presetForm.value.name}`,
      steps: sequenceSteps.value.map(step => {
        const command = {
          cmd: step.command.cmd,
          device_id: step.command.device_id,
          device_type: step.command.device_type || step.command.cmd
        }
        
        // 根据命令类型，保留对应的控制值字段
        if (step.command.cmd === 'led' || step.command.cmd === 'relay') {
          command.value = step.command.value !== undefined ? step.command.value : 0
        } else if (step.command.cmd === 'servo') {
          command.angle = step.command.angle !== undefined ? step.command.angle : 90
        } else if (step.command.cmd === 'pwm') {
          command.frequency = step.command.frequency !== undefined ? step.command.frequency : 50
          command.duty = step.command.duty !== undefined ? step.command.duty : 0
        }
        
        return {
          command: command,
          delay: step.delay
        }
      })
    }
    
    console.log('[savePreset] 保存序列预设:', newPreset)
    
    if (presetDialogMode.value === 'add') {
      presetCommands.value.push(newPreset)
      ElMessage.success('序列预设已添加')
    } else {
      presetCommands.value[editingPresetIndex.value] = newPreset
      ElMessage.success('序列预设已更新')
    }
  } else {
    // 普通预设
    if (!presetForm.value.device_type) {
      ElMessage.warning('请选择设备类型')
      return
    }
    if (!presetForm.value.preset_type) {
      ElMessage.warning('请选择预设类型')
      return
    }
    
    // 生成唯一的preset_key（如果是新增或者编辑时没有preset_key）
    let presetKey = presetForm.value.preset_key
    if (!presetKey) {
      const timestamp = Date.now().toString(36)
      const deviceType = presetForm.value.device_type || 'unknown'
      const presetType = presetForm.value.preset_type || 'custom'
      presetKey = `${deviceType}_${presetType}_${timestamp}`
    }
    
    // 检查preset_key是否重复（编辑模式下排除当前预设）
    const isDuplicate = presetCommands.value.some((preset, index) => {
      // 如果是编辑模式，排除当前正在编辑的预设
      if (presetDialogMode.value === 'edit' && index === editingPresetIndex.value) {
        return false
      }
      return preset.preset_key === presetKey
    })
    
    if (isDuplicate) {
      ElMessage.error('预设标识重复，请重新保存')
      // 重新生成preset_key
      const timestamp = Date.now().toString(36)
      const deviceType = presetForm.value.device_type || 'unknown'
      const presetType = presetForm.value.preset_type || 'custom'
      presetKey = `${deviceType}_${presetType}_${timestamp}_${Math.random().toString(36).substr(2, 5)}`
      presetForm.value.preset_key = presetKey
      console.warn('[savePreset] 检测到preset_key重复，已重新生成:', presetKey)
    }
    
    const newPreset = JSON.parse(JSON.stringify(presetForm.value))
    newPreset.preset_key = presetKey  // 确保preset_key存在
    
    if (presetDialogMode.value === 'add') {
      presetCommands.value.push(newPreset)
      ElMessage.success('预设指令已添加')
    } else {
      presetCommands.value[editingPresetIndex.value] = newPreset
      ElMessage.success('预设指令已更新')
    }
  }
  
  presetDialogVisible.value = false
  resetPresetForm()
  
  // 自动保存配置
  autoSaveConfig()
}

const getPresetTypeLabel = (deviceType, presetType) => {
  if (presetType === 'sequence') {
    return '序列指令'
  }
  const options = presetTypeOptions[deviceType]
  if (!options) return presetType
  
  const option = options.find(opt => opt.value === presetType)
  return option ? option.label : presetType
}

// 获取设备ID的显示标签
const getDeviceIdLabel = (deviceType, deviceId) => {
  if (deviceId === 0) {
    return `所有${deviceType === 'led' ? 'LED' : deviceType === 'relay' ? '继电器' : '设备'}`
  }
  
  const ports = getAvailablePorts(deviceType)
  const port = ports.find(p => p.value === deviceId)
  
  if (port) {
    return port.label
  }
  
  // 默认显示
  const typeNames = {
    led: 'LED',
    servo: '舵机',
    relay: '继电器',
    pwm: 'PWM输出'
  }
  return `${typeNames[deviceType] || deviceType}${deviceId}`
}

// 根据设备类型获取可用的设备端口
const getAvailablePorts = (deviceType) => {
  // 防御性检查
  if (!deviceType) {
    console.warn('[getAvailablePorts] deviceType为空')
    return []
  }
  
  const ports = []
  
  // 如果有产品配置，从配置中获取实际可用的端口
  try {
    if (productConfig.value && productConfig.value.control_ports) {
      const controlPorts = productConfig.value.control_ports
      
      // 确保controlPorts是对象
      if (typeof controlPorts !== 'object' || controlPorts === null) {
        console.warn('[getAvailablePorts] control_ports不是有效的对象:', controlPorts)
        // 继续执行，使用默认端口
      } else {
        Object.entries(controlPorts).forEach(([key, config]) => {
          // 防御性检查config
          if (!config || typeof config !== 'object') {
            console.warn(`[getAvailablePorts] 端口配置无效: ${key}`, config)
            return
          }
          
          const portType = config.type?.toLowerCase()
          
          // 匹配设备类型
          if (portType === deviceType) {
            // 提取设备ID
            let deviceId = 1
            if (key.startsWith('pwm_m')) {
              // 从 pwm_m1 或 pwm_m2 中提取数字
              const match = key.match(/pwm_m(\d+)/)
              deviceId = match ? parseInt(match[1]) : 1
            } else if (key.startsWith('servo_m')) {
              // 从 servo_m1 或 servo_m2 中提取数字
              const match = key.match(/servo_m(\d+)/)
              deviceId = match ? parseInt(match[1]) : 1
            } else {
              const parts = key.split('_')
              deviceId = parts.length > 1 ? parseInt(parts[parts.length - 1]) : 1
            }
            
            ports.push({
              value: deviceId,
              label: config.name || `${config.type}${deviceId}`,
              desc: config.description || config.custom_name || `端口: ${key}`
            })
          }
        })
      }
    }
  } catch (error) {
    console.error('[getAvailablePorts] 解析产品配置出错:', error)
    // 继续执行，使用默认端口
  }
  
  // 如果没有从配置中找到，提供默认选项
  if (ports.length === 0) {
    const defaultPorts = {
      led: [
        { value: 1, label: 'LED1', desc: 'LED端口1' },
        { value: 2, label: 'LED2', desc: 'LED端口2' },
        { value: 3, label: 'LED3', desc: 'LED端口3' },
        { value: 4, label: 'LED4', desc: 'LED端口4' },
        { value: 0, label: '所有LED', desc: '控制所有LED' }
      ],
      servo: [
        { value: 1, label: '舵机1 (M1)', desc: '舵机端口M1' }
      ],
      relay: [
        { value: 1, label: '继电器1', desc: '继电器端口1' },
        { value: 2, label: '继电器2', desc: '继电器端口2' },
        { value: 0, label: '所有继电器', desc: '控制所有继电器' }
      ],
      pwm: [
        { value: 1, label: 'PWM输出 (M1)', desc: 'M1端口 - GPIO48' },
        { value: 2, label: 'PWM输出 (M2)', desc: 'M2端口 - GPIO40' }
      ]
    }
    
    return defaultPorts[deviceType] || []
  }
  
  // 对于LED和继电器，添加"所有设备"选项
  if (deviceType === 'led' || deviceType === 'relay') {
    ports.push({
      value: 0,
      label: `所有${deviceType === 'led' ? 'LED' : '继电器'}`,
      desc: `同时控制所有${deviceType === 'led' ? 'LED' : '继电器'}`
    })
  }
  
  // 按设备ID排序
  ports.sort((a, b) => a.value - b.value)
  
  return ports
}

const formatParameters = (parameters) => {
  if (!parameters || Object.keys(parameters).length === 0) {
    return '无'
  }
  
  return Object.entries(parameters)
    .map(([key, value]) => {
      // 格式化参数显示
      if (typeof value === 'boolean') {
        return `${key}: ${value ? '是' : '否'}`
      }
      // LED序列特殊处理
      if (key === 'led_sequence' && Array.isArray(value)) {
        return `LED序列: ${value.map(id => `LED${id}`).join(' → ')}`
      }
      // 数组类型
      if (Array.isArray(value)) {
        return `${key}: [${value.join(', ')}]`
      }
      return `${key}: ${value}`
    })
    .join(', ')
}

// 格式化序列步骤显示
const formatSequenceSteps = (steps) => {
  if (!steps || steps.length === 0) {
    return '无步骤'
  }
  return `${steps.length} 个步骤`
}

// 获取设备类型的中文标签
const getDeviceTypeLabel = (deviceType) => {
  const labels = {
    led: 'LED',
    relay: '继电器',
    servo: '舵机',
    pwm: 'PWM输出'
  }
  return labels[deviceType] || deviceType
}

// 复制预设标识
const copyPresetKey = async (presetKey) => {
  try {
    // 使用Clipboard API复制
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(presetKey)
      ElMessage.success(`已复制预设标识: ${presetKey}`)
    } else {
      // 降级方案：使用document.execCommand
      const textArea = document.createElement('textarea')
      textArea.value = presetKey
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      ElMessage.success(`已复制预设标识: ${presetKey}`)
    }
  } catch (error) {
    logger.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 生命周期
onMounted(() => {
  loadDeviceInfo()
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (saveTimer) {
    clearTimeout(saveTimer)
  }
})
</script>

<style scoped>
.device-config-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  font-size: 14px;
}

.page-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-controls .el-tag {
  font-size: 13px;
  padding: 8px 16px;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.config-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.sensor-config-item,
.control-config-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.sensor-info,
.control-info {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

.description-input {
  width: 600px;
  max-width: 100%;
}

/* 预设指令样式 */
.preset-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 16px;
  background-color: #fafafa;
}

.preset-item:last-child {
  margin-bottom: 0;
}

.preset-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.preset-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.preset-type-badge {
  font-size: 12px;
  padding: 2px 8px;
  background-color: #409eff;
  color: white;
  border-radius: 4px;
}

.preset-actions {
  display: flex;
  gap: 8px;
}

.preset-details {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.preset-field {
  display: flex;
  align-items: center;
  font-size: 13px;
}

.field-label {
  color: #909399;
  margin-right: 4px;
}

.field-value {
  color: #606266;
  font-weight: 500;
}

.preset-key-value {
  display: flex;
  align-items: center;
  gap: 4px;
}

.preset-key-value code {
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #e74c3c;
  border: 1px solid #e1e4e8;
}

.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}
</style>

