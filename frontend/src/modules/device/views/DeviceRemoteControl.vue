<template>
  <div class="device-remote-control-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回设备列表
        </el-button>
        <div class="page-title">
          <h2>{{ device?.name || '设备' }} - 远程控制</h2>
          <div class="device-tags" v-if="device">
            <el-tag :type="device.is_online ? 'success' : 'danger'" size="small">
              {{ device.is_online ? '在线' : '离线' }}
            </el-tag>
            <el-tag type="info" size="small">UUID: {{ device.uuid }}</el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="page-content" v-if="device">
      <!-- 设备状态提示 -->
      <el-alert
        v-if="!device.is_online"
        title="设备离线"
        type="warning"
        description="设备当前处于离线状态，无法发送控制指令"
        show-icon
        :closable="false"
        style="margin-bottom: 24px;"
      />

      <!-- 根据产品配置生成的控制界面 -->
      <div class="control-section" v-if="productConfig && productConfig.control_ports">
        <h3>设备控制 - {{ productConfig.product_name }}</h3>
        <div class="control-grid" v-loading="loadingConfig">
          <el-card
            v-for="(portConfig, portKey) in productConfig.control_ports"
            :key="portKey"
            class="control-card"
            shadow="hover"
            v-show="isPortEnabled(portKey, portConfig)"
            :class="{ 'disabled': !device.is_online }"
          >
            <div class="control-header">
              <div class="control-name-section">
                <div class="control-name">
                  {{ portConfig.name || portKey }}
                </div>
                <div class="control-custom-name" v-if="getControlCustomName(portKey)">
                  {{ getControlCustomName(portKey) }}
                </div>
              </div>
              <el-tag :type="getControlTypeTag(portConfig.type)" size="small">
                {{ portConfig.type }}
              </el-tag>
            </div>
            <div class="control-description" v-if="portConfig.description">
              {{ portConfig.description }}
          </div>
            
            <!-- 动态生成控制界面 -->
            <div class="control-controls" v-if="device.is_online">
              <component 
                :is="getControlComponent(portConfig.type)" 
                :config="portConfig"
                :port-key="portKey"
                @control="handlePortControl"
              />
          </div>
            
            <div v-else class="control-controls disabled">
              <el-button disabled style="width: 100%;">设备离线</el-button>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 预设控制指令（保留原有功能） -->
      <div class="presets-section" style="margin-top: 32px;">
        <h3>预设控制指令</h3>
        <div class="presets-grid" v-loading="loadingPresets">
          <el-card
            v-for="preset in presets"
            :key="preset.id"
            class="preset-card"
            shadow="hover"
            :class="{ 'disabled': !device.is_online }"
          >
            <div class="preset-header">
              <div class="preset-name">{{ preset.name }}</div>
              <el-tag :type="getPresetTypeTag(preset.type || preset.cmd)" size="small">
                {{ preset.device_type_display || (preset.device_type ? preset.device_type.toUpperCase() : preset.type) }}
              </el-tag>
        </div>
            <div class="preset-description">{{ preset.description }}</div>
            
            <!-- 预设标识显示区域 -->
            <div class="preset-identifier" v-if="getPresetIdentifier(preset)">
              <div class="identifier-label">预设标识：</div>
              <div class="identifier-value">
                <el-tag type="info" size="small">{{ getPresetIdentifier(preset) }}</el-tag>
                <el-button 
                  size="small" 
                  type="primary" 
                  text
                  @click="copyPresetIdentifier(preset)"
                  style="margin-left: 8px;"
                >
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </div>
            </div>
            
            <!-- 根据预设类型显示不同的控制界面 -->
            <div class="preset-controls" v-if="device.is_online">
              <!-- LED开关控制 -->
              <div v-if="preset.control_type === 'switch' && preset.cmd === 'led'" class="control-group">
                <el-switch
                  v-model="controlValues[preset.id]"
                  active-text="开"
                  inactive-text="关"
                  @change="handleControl(preset, controlValues[preset.id])"
              />
      </div>

              <!-- 继电器开关控制 -->
              <div v-else-if="preset.control_type === 'switch' && preset.cmd === 'relay'" class="control-group">
              <el-switch
                  v-model="controlValues[preset.id]"
                  active-text="开"
                  inactive-text="关"
                  @change="handleControl(preset, controlValues[preset.id])"
              />
            </div>
            
              <!-- 舵机速度控制（360度连续旋转舵机） -->
              <div v-else-if="preset.control_type === 'speed' && preset.cmd === 'servo'" class="control-group">
              <el-slider
                  v-model="controlValues[preset.id]"
                  :min="preset.min || 0"
                  :max="preset.max || 180"
                  :step="1"
                show-input
                  @change="handleControl(preset, controlValues[preset.id])"
              />
                <div class="control-label">
                  {{ getServoSpeedLabel(controlValues[preset.id]) }}
            </div>
                <div class="control-hint">
                  <el-text type="info" size="small">
                    90=停止，0-89=反转，91-180=正转
                  </el-text>
                </div>
            </div>
            
              <!-- 舵机停止控制 -->
              <div v-else-if="preset.control_type === 'stop' && preset.cmd === 'servo'" class="control-group">
                <el-button
                  type="warning"
                  @click="handleServoStop(preset)"
                  style="width: 100%;"
              >
                  停止舵机
                </el-button>
            </div>
            
              <!-- LED闪烁预设 -->
              <div v-else-if="preset.control_type === 'blink' && preset.cmd === 'preset'" class="control-group">
                <el-form :model="blinkParams[preset.id]" label-width="80px" size="small">
                  <el-form-item label="闪烁次数">
              <el-input-number
                      v-model="blinkParams[preset.id].count"
                      :min="1"
                      :max="20"
                      :step="1"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="亮时间(ms)">
                    <el-input-number
                      v-model="blinkParams[preset.id].on_time"
                      :min="100"
                      :max="5000"
                      :step="100"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="灭时间(ms)">
              <el-input-number
                      v-model="blinkParams[preset.id].off_time"
                      :min="100"
                      :max="5000"
                      :step="100"
                      style="width: 100%;"
                    />
                  </el-form-item>
                </el-form>
                <el-button
                  type="primary"
                  @click="handleBlink(preset)"
                  style="width: 100%;"
                >
                  执行闪烁
                </el-button>
      </div>

              <!-- LED波浪灯预设 -->
              <div v-else-if="preset.control_type === 'wave' && preset.cmd === 'preset'" class="control-group">
                <el-form :model="waveParams[preset.id]" label-width="100px" size="small">
                  <el-form-item label="间隔时间(ms)">
                    <el-input-number
                      v-model="waveParams[preset.id].interval_ms"
                      :min="50"
                      :max="5000"
                      :step="50"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="循环次数">
                    <el-input-number
                      v-model="waveParams[preset.id].cycles"
                      :min="1"
                      :max="100"
                      :step="1"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="方向">
                    <el-switch
                      v-model="waveParams[preset.id].reverse"
                      active-text="反向"
                      inactive-text="正向"
                    />
                  </el-form-item>
                </el-form>
                <el-button
                  type="primary"
                  @click="handleWave(preset)"
                  style="width: 100%;"
                >
                  执行波浪灯
                </el-button>
          </div>
              
              <!-- 舵机摆动预设（新增）-->
              <div v-else-if="preset.control_type === 'swing' && preset.cmd === 'preset'" class="control-group">
                <el-form :model="swingParams[preset.id]" label-width="100px" size="small">
                  <el-form-item label="中心角度">
                    <el-input-number
                      v-model="swingParams[preset.id].center_angle"
                      :min="0"
                      :max="180"
                      :step="5"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="摆动幅度">
                    <el-input-number
                      v-model="swingParams[preset.id].swing_angle"
                      :min="5"
                      :max="90"
                      :step="5"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="摆动速度(ms)">
                    <el-input-number
                      v-model="swingParams[preset.id].speed"
                      :min="100"
                      :max="2000"
                      :step="100"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="摆动次数">
                    <el-input-number
                      v-model="swingParams[preset.id].cycles"
                      :min="1"
                      :max="100"
                      :step="1"
                      style="width: 100%;"
                    />
                  </el-form-item>
                </el-form>
                <el-button 
                  type="primary" 
                  @click="handleSwing(preset)"
                  style="width: 100%;"
                >
                  执行摆动（摇尾巴）
                </el-button>
          </div>
              
              <!-- 舵机正反转预设（360度舵机） -->
              <div v-else-if="preset.control_type === 'rotate' && preset.cmd === 'preset'" class="control-group">
                <el-form :model="rotateParams[preset.id]" label-width="100px" size="small">
                  <el-form-item label="循环次数">
                    <el-input-number
                      v-model="rotateParams[preset.id].cycles"
                      :min="1"
                      :max="10"
                      :step="1"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="正转时间(ms)">
                    <el-input-number
                      v-model="rotateParams[preset.id].forward_duration"
                      :min="500"
                      :max="10000"
                      :step="500"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="反转时间(ms)">
                    <el-input-number
                      v-model="rotateParams[preset.id].reverse_duration"
                      :min="500"
                      :max="10000"
                      :step="500"
                      style="width: 100%;"
                    />
                  </el-form-item>
                  <el-form-item label="暂停时间(ms)">
                    <el-input-number
                      v-model="rotateParams[preset.id].pause_time"
                      :min="100"
                      :max="2000"
                      :step="100"
                      style="width: 100%;"
                    />
                  </el-form-item>
                </el-form>
            <el-button 
              type="primary" 
                  @click="handleRotate(preset)"
                  style="width: 100%;"
            >
                  执行正反转
            </el-button>
      </div>

              <!-- 继电器定时开关预设 -->
              <div v-else-if="preset.control_type === 'timed_switch' && preset.cmd === 'preset'" class="control-group">
                <el-form :model="timedParams[preset.id]" label-width="80px" size="small">
                  <el-form-item label="持续时间(秒)">
                    <el-input-number
                      v-model="timedParams[preset.id].duration"
                      :min="1"
                      :max="60"
                      :step="1"
                      style="width: 100%;"
            />
                  </el-form-item>
                </el-form>
            <el-button 
              type="primary" 
                  @click="handleTimedSwitch(preset)"
                  style="width: 100%;"
            >
                  执行定时开关（{{ timedParams[preset.id].duration }}秒）
            </el-button>
        </div>

              <!-- 序列指令预设 -->
              <div v-else-if="preset.type === 'sequence' || preset.cmd === 'sequence'" class="control-group">
                <div class="sequence-info">
                  <el-text type="info" size="small">
                    <div style="margin-bottom: 8px;">此预设包含 {{ preset.steps?.length || 0 }} 个步骤</div>
                    <div v-if="preset.steps && preset.steps.length > 0" style="font-size: 12px;">
                      <div v-for="(step, index) in preset.steps" :key="index" style="margin: 4px 0;">
                        <span>步骤{{ index + 1 }}: </span>
                        <span v-if="step.command.cmd === 'led'">
                          LED{{ step.command.device_id }} {{ step.command.value === 1 ? '打开' : '关闭' }}
                        </span>
                        <span v-else-if="step.command.cmd === 'relay'">
                          继电器{{ step.command.device_id }} {{ step.command.value === 1 ? '打开' : '关闭' }}
                        </span>
                        <span v-else>{{ step.command.cmd }}</span>
                        <span v-if="step.delay > 0" style="color: #909399;"> (延迟{{ step.delay }}秒)</span>
                      </div>
                    </div>
                  </el-text>
                </div>
                <el-button
                  type="primary"
                  @click="handleSequence(preset)"
                  style="width: 100%; margin-top: 12px;"
                  :loading="sendingSequence[preset.id]"
                >
                  执行序列指令
                </el-button>
              </div>

              <!-- 默认按钮 -->
              <div v-else class="control-group">
                <el-button
                  type="primary"
                  @click="handleControl(preset, null)"
                  style="width: 100%;"
                >
                  执行指令
                </el-button>
              </div>
            </div>
            
            <div v-else class="preset-controls disabled">
              <el-button disabled style="width: 100%;">设备离线</el-button>
            </div>
          </el-card>
    </div>

        <!-- 无预设提示 -->
        <el-empty 
          v-if="!loadingPresets && presets.length === 0" 
          description="该设备暂无预设控制指令"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, defineComponent, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElSwitch, ElSlider, ElButton, ElInputNumber } from 'element-plus'
import { ArrowLeft, DocumentCopy } from '@element-plus/icons-vue'
import { getDevicePresets, sendDeviceControl, getDeviceProductConfig, getDeviceConfig } from '@/api/device'
import { getDevicesWithProductInfo } from '@/api/device'
import logger from '../utils/logger'

const route = useRoute()
const router = useRouter()

const device = ref(null)
const productConfig = ref(null)
const deviceConfig = ref(null) // 设备自定义配置
const loadingConfig = ref(false)
const loadingPresets = ref(false)
const sending = ref(false)
const presets = ref([])
const controlValues = reactive({})
const blinkParams = reactive({})
const waveParams = reactive({})
const swingParams = reactive({})
const rotateParams = reactive({})
const timedParams = reactive({})
const sendingSequence = reactive({}) // 序列指令执行状态

// 从路由参数获取设备UUID
const deviceUuid = computed(() => route.params.uuid)

// 加载产品配置和设备配置
const loadProductConfig = async (deviceUuid) => {
  loadingConfig.value = true
  try {
    // 加载产品配置
    const productResponse = await getDeviceProductConfig(deviceUuid)
    if (productResponse.data) {
      productConfig.value = productResponse.data
      logger.info('产品配置加载成功:', productResponse.data)
    }
    
    // 加载设备自定义配置（包含启用/禁用状态和预设指令）
    const deviceResponse = await getDeviceConfig(deviceUuid)
    if (deviceResponse.data) {
      deviceConfig.value = deviceResponse.data
      logger.info('设备配置加载成功:', deviceResponse.data)
      // 打印预设指令数量用于调试
      const presetCount = deviceResponse.data.device_preset_commands?.length || 0
      logger.info(`加载到 ${presetCount} 个用户自定义预设指令`)
    }
  } catch (error) {
    logger.error('加载配置失败:', error)
    // 确保即使加载失败也有完整的初始结构
    productConfig.value = {
      control_ports: {},
      sensor_types: {}
    }
    deviceConfig.value = {
      device_control_config: {},
      device_sensor_config: {},
      device_preset_commands: [] // 重要：添加预设指令字段
    }
  } finally {
    loadingConfig.value = false
  }
}

// 加载设备信息
const loadDeviceInfo = async () => {
  try {
    const response = await getDevicesWithProductInfo()
    if (response.data) {
      device.value = response.data.find(d => d.uuid === deviceUuid.value)
      if (!device.value) {
        ElMessage.error('设备不存在')
      goBack()
      return
    }

      // 加载产品配置
      if (device.value.uuid) {
        await loadProductConfig(device.value.uuid)
      }
    }
  } catch (error) {
    logger.error('加载设备信息失败:', error)
    ElMessage.error('加载设备信息失败')
  }
}

// 加载预设指令（系统预设 + 用户自定义）
const loadPresets = async () => {
  if (!deviceUuid.value) return
  
  loadingPresets.value = true
  try {
    // 1. 从后端 API 获取系统自动生成的预设指令
    let systemPresets = []
    try {
      const response = await getDevicePresets(deviceUuid.value)
      if (response.data && response.data.presets) {
        systemPresets = response.data.presets
        logger.info('加载系统预设指令:', systemPresets.length, '个')
      }
    } catch (apiError) {
      logger.warn('获取系统预设指令失败:', apiError)
    }
    
    // 2. 加载用户自定义预设指令
    let customPresets = []
    if (deviceConfig.value && deviceConfig.value.device_preset_commands) {
      customPresets = deviceConfig.value.device_preset_commands.map((preset, index) => {
        // 转换用户自定义预设为控制界面格式
        if (preset.type === 'sequence' || preset.steps) {
          return {
            id: `custom_preset_${index}`,
            name: preset.name,
            type: 'sequence',
            cmd: 'sequence',
            description: preset.description || `自定义序列预设：${preset.name}`,
            steps: preset.steps || [],
            preset_key: preset.preset_key, // 传递 preset_key，Coze 需要这个
            isCustom: true // 标记为用户自定义
          }
        }
        return {
          id: `custom_preset_${index}`,
          name: preset.name,
          type: 'preset',
          cmd: 'preset',
          device_type: preset.device_type, // 保持小写，固件需要小写格式
          device_type_display: preset.device_type?.toUpperCase() || 'UNKNOWN', // 用于显示的大写版本
          device_id: preset.device_id || 0,
          preset_type: preset.preset_type,
          preset_key: preset.preset_key, // 传递 preset_key，Coze 需要这个
          description: `自定义预设：${preset.name}`,
          control_type: preset.preset_type, // 用于界面渲染
          parameters: preset.parameters || {},
          isCustom: true // 标记为用户自定义
        }
      })
      logger.info('加载用户自定义预设指令:', customPresets.length, '个')
    }
    
    // 3. 合并系统预设和用户自定义预设（系统预设在前，用户自定义在后）
    presets.value = [...systemPresets, ...customPresets]
    logger.info('总预设指令数:', presets.value.length, '(系统:', systemPresets.length, '+ 自定义:', customPresets.length, ')')
      
      // 初始化控制值
      presets.value.forEach(preset => {
        // 设备控制指令
        if (preset.control_type === 'switch') {
          controlValues[preset.id] = false
        } else if (preset.control_type === 'speed') {
          controlValues[preset.id] = preset.default || 90  // 90度对应停止
        }
        
      // 预设指令参数（优先使用用户配置的参数）
      if (preset.control_type === 'blink' || preset.preset_type === 'blink') {
          blinkParams[preset.id] = {
          count: preset.parameters?.count || preset.default_count || 3,
          on_time: preset.parameters?.on_time || preset.default_on_time || 500,
          off_time: preset.parameters?.off_time || preset.default_off_time || 500
          }
      } else if (preset.control_type === 'wave' || preset.preset_type === 'wave') {
          waveParams[preset.id] = {
          interval_ms: preset.parameters?.interval_ms || preset.parameters?.duration || preset.default_duration || 200,
          cycles: preset.parameters?.cycles || 3,
          reverse: preset.parameters?.reverse || false
        }
      } else if (preset.control_type === 'swing' || preset.preset_type === 'swing') {
        swingParams[preset.id] = {
          center_angle: preset.parameters?.center_angle || 90,
          swing_angle: preset.parameters?.swing_angle || 30,
          speed: preset.parameters?.speed || 500,
          cycles: preset.parameters?.cycles || 5
          }
      } else if (preset.control_type === 'rotate' || preset.preset_type === 'rotate') {
          rotateParams[preset.id] = {
          cycles: preset.parameters?.cycles || preset.default_cycles || 3,
          forward_duration: preset.parameters?.forward_duration || preset.default_forward_duration || 3000,
          reverse_duration: preset.parameters?.reverse_duration || preset.default_reverse_duration || 3000,
          pause_time: preset.parameters?.pause_time || preset.default_pause_time || 500
          }
      } else if (preset.control_type === 'timed_switch' || preset.preset_type === 'timed_switch') {
          timedParams[preset.id] = {
          duration: ((preset.parameters?.duration || preset.default_duration || 5000)) / 1000  // 转换为秒
          }
        }
      })
  } catch (error) {
    logger.error('加载预设指令失败:', error)
    ElMessage.error('加载预设指令失败')
  } finally {
    loadingPresets.value = false
  }
}

// 处理控制指令（设备控制命令）
const handleControl = async (preset, value) => {
  if (!device.value || !device.value.is_online) {
    ElMessage.warning('设备离线，无法发送控制指令')
    return
  }
  
  if (sending.value) return
  
  sending.value = true
  try {
    let command = {}
    
    // 根据统一的格式：使用device_id字段
    if (preset.cmd === 'led') {
      command = {
        cmd: 'led',
        device_id: preset.device_id,
        action: value ? 'on' : 'off'
      }
    } else if (preset.cmd === 'relay') {
      command = {
        cmd: 'relay',
        device_id: preset.device_id,
        action: value ? 'on' : 'off'
      }
    } else if (preset.cmd === 'servo') {
      if (preset.control_type === 'speed') {
        // 360度舵机速度控制：使用angle字段，90=停止，<90=反转，>90=正转
        command = {
          cmd: 'servo',
          device_id: preset.device_id,
          angle: value  // 虽然叫angle，但对于360度舵机实际上是速度控制
        }
      }
    } else if (preset.cmd === 'preset') {
      // 预设指令：完整命令格式
      command = {
        cmd: 'preset',
        device_type: preset.device_type,
        device_id: preset.device_id,
        preset_type: preset.preset_type,
        parameters: preset.parameters || {}
      }
    } else if (preset.type === 'sequence' || preset.cmd === 'sequence') {
      // 序列指令：直接使用preset的steps
      command = {
        type: 'sequence',
        steps: preset.steps || []
      }
    }
    
    // 如果command仍然是空对象，说明preset格式不正确
    if (Object.keys(command).length === 0) {
      console.error('无法构建控制命令，preset格式不正确:', preset)
      ElMessage.error('预设指令格式错误，无法发送')
      sending.value = false
      return
    }
    
    const response = await sendDeviceControl(deviceUuid.value, command)
    if (response.data && response.data.success) {
      ElMessage.success('控制指令发送成功')
    }
  } catch (error) {
    logger.error('发送控制指令失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送控制指令失败')
  } finally {
    sending.value = false
  }
}

// 处理LED闪烁预设
const handleBlink = async (preset) => {
  if (!device.value || !device.value.is_online) {
    ElMessage.warning('设备离线，无法发送控制指令')
    return
  }
  
  if (sending.value) return
  
  sending.value = true
  try {
    const params = blinkParams[preset.id]
    const command = {
      cmd: 'preset',
      device_type: preset.device_type,
      device_id: preset.device_id,
      preset_type: 'blink',
      parameters: {
        count: params.count,
        on_time: params.on_time,
        off_time: params.off_time
      }
    }
    
    const response = await sendDeviceControl(deviceUuid.value, command)
    if (response.data && response.data.success) {
      ElMessage.success(`LED闪烁指令发送成功（${params.count}次）`)
    }
  } catch (error) {
    logger.error('发送LED闪烁指令失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送控制指令失败')
  } finally {
    sending.value = false
  }
}

// 处理LED波浪效果预设
const handleWave = async (preset) => {
  if (!device.value || !device.value.is_online) {
    ElMessage.warning('设备离线，无法发送控制指令')
    return
  }
  
  if (sending.value) return
  
  sending.value = true
  try {
    const params = waveParams[preset.id]
    const command = {
      cmd: 'preset',
      device_type: preset.device_type,
      device_id: preset.device_id,
      preset_type: 'wave',
      parameters: {
        interval_ms: params.interval_ms || 200,
        cycles: params.cycles || 3,
        reverse: params.reverse || false
      }
    }
    
    const response = await sendDeviceControl(deviceUuid.value, command)
    if (response.data && response.data.success) {
      ElMessage.success(`LED波浪灯效果发送成功（${params.cycles}次循环）`)
    }
  } catch (error) {
    logger.error('发送LED波浪灯指令失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送控制指令失败')
  } finally {
    sending.value = false
  }
}

// 处理舵机摆动预设
const handleSwing = async (preset) => {
  if (!device.value || !device.value.is_online) {
    ElMessage.warning('设备离线，无法发送控制指令')
    return
  }
  
  if (sending.value) return
  
  sending.value = true
  try {
    const params = swingParams[preset.id]
    const command = {
      cmd: 'preset',
      device_type: preset.device_type,
      device_id: preset.device_id,
      preset_type: 'swing',
      parameters: {
        center_angle: params.center_angle,
        swing_angle: params.swing_angle,
        speed: params.speed,
        cycles: params.cycles
      }
    }
    
    const response = await sendDeviceControl(deviceUuid.value, command)
    if (response.data && response.data.success) {
      ElMessage.success(`舵机摆动指令发送成功（${params.cycles}次摆动）`)
    }
  } catch (error) {
    logger.error('发送舵机摆动指令失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送控制指令失败')
  } finally {
    sending.value = false
  }
}

// 处理舵机正反转预设（360度舵机）
const handleRotate = async (preset) => {
  if (!device.value || !device.value.is_online) {
    ElMessage.warning('设备离线，无法发送控制指令')
    return
  }
  
  if (sending.value) return
  
  sending.value = true
  try {
    const params = rotateParams[preset.id]
    const command = {
      cmd: 'preset',
      device_type: preset.device_type,
      device_id: preset.device_id,
      preset_type: 'rotate',
      parameters: {
        cycles: params.cycles,
        forward_duration: params.forward_duration,
        reverse_duration: params.reverse_duration,
        pause_time: params.pause_time
      }
    }
    
    const response = await sendDeviceControl(deviceUuid.value, command)
    if (response.data && response.data.success) {
      ElMessage.success(`舵机正反转指令发送成功（${params.cycles}次循环）`)
    }
  } catch (error) {
    logger.error('发送舵机正反转指令失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送控制指令失败')
  } finally {
    sending.value = false
  }
}

// 处理舵机停止
const handleServoStop = async (preset) => {
  if (!device.value || !device.value.is_online) {
    ElMessage.warning('设备离线，无法发送控制指令')
    return
  }
  
  if (sending.value) return
  
  sending.value = true
  try {
    const command = {
      cmd: 'servo',
      device_id: preset.device_id,
      angle: 90  // 90度对应停止（360度舵机）
    }
    
    const response = await sendDeviceControl(deviceUuid.value, command)
    if (response.data && response.data.success) {
      ElMessage.success('舵机停止指令发送成功')
    }
  } catch (error) {
    logger.error('发送舵机停止指令失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送控制指令失败')
  } finally {
    sending.value = false
  }
}

// 获取舵机速度标签
const getServoSpeedLabel = (value) => {
  if (value === 90) {
    return '停止'
  } else if (value < 90) {
    return `反转速度: ${90 - value} (0-89)`
  } else {
    return `正转速度: ${value - 90} (91-180)`
  }
}

// 处理继电器定时开关预设
const handleTimedSwitch = async (preset) => {
  if (!device.value || !device.value.is_online) {
    ElMessage.warning('设备离线，无法发送控制指令')
    return
  }
  
  if (sending.value) return
  
  sending.value = true
  try {
    const params = timedParams[preset.id]
    const command = {
      cmd: 'preset',
      device_type: preset.device_type,
      device_id: preset.device_id,
      preset_type: 'timed_switch',
      parameters: {
        duration: params.duration * 1000  // 转换为毫秒
      }
    }
    
    const response = await sendDeviceControl(deviceUuid.value, command)
    if (response.data && response.data.success) {
      ElMessage.success(`定时开关指令发送成功（${params.duration}秒）`)
  }
  } catch (error) {
    logger.error('发送定时开关指令失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送控制指令失败')
  } finally {
    sending.value = false
  }
}

// 处理序列指令预设
const handleSequence = async (preset) => {
  if (!device.value || !device.value.is_online) {
    ElMessage.warning('设备离线，无法发送控制指令')
    return
  }
  
  if (sendingSequence[preset.id]) return
  
  sendingSequence[preset.id] = true
  try {
    const command = {
      type: 'sequence',
      steps: preset.steps || []
    }
    
    const response = await sendDeviceControl(deviceUuid.value, command)
    if (response.data) {
      // 统一提示：执行命令已发送
      ElMessage.success('执行命令已发送')
      
      // 在控制台输出详细信息供调试
      const totalSteps = response.data.total_steps || 0
      const successCount = response.data.executed_steps?.filter(s => s.status === 'success').length || 0
      logger.info(`序列指令执行结果: ${successCount}/${totalSteps} 步骤成功`)
      
      // 在控制台打印详细的失败信息
      if (response.data.executed_steps) {
        const failedSteps = response.data.executed_steps.filter(s => s.status === 'failed')
        if (failedSteps.length > 0) {
          logger.warn('失败的步骤详情:', failedSteps)
        }
      }
    }
  } catch (error) {
    logger.error('发送序列指令失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送序列指令失败')
  } finally {
    sendingSequence[preset.id] = false
  }
}

// 获取预设类型标签
// 检查端口是否启用（根据设备配置）
const isPortEnabled = (portKey, portConfig) => {
  // 首先检查产品配置中的enabled状态（默认启用）
  if (portConfig.enabled === false) {
    return false
  }
  
  // 然后检查设备自定义配置中的enabled状态
  if (deviceConfig.value && deviceConfig.value.device_control_config) {
    const deviceControlConfig = deviceConfig.value.device_control_config[portKey]
    if (deviceControlConfig && deviceControlConfig.enabled === false) {
      return false // 用户在设备配置中禁用了该端口
    }
  }
  
  return true // 默认启用
}

// 获取控制端口的自定义功能描述
const getControlCustomName = (portKey) => {
  // 优先从设备配置中获取 custom_name
  if (deviceConfig.value && deviceConfig.value.device_control_config) {
    const deviceControlConfig = deviceConfig.value.device_control_config[portKey]
    if (deviceControlConfig && deviceControlConfig.custom_name) {
      return deviceControlConfig.custom_name // 用户自定义的功能描述，如"客厅台灯"、"摇尾巴"
    }
  }
  
  // 兼容：从 device.value 中获取（如果有的话）
  if (device.value && device.value.device_control_config) {
    const deviceControlConfig = device.value.device_control_config[portKey]
    if (deviceControlConfig && deviceControlConfig.custom_name) {
      return deviceControlConfig.custom_name
    }
  }
  
  return null
}

// 获取控制端口显示名称（优先使用用户自定义的功能描述）
const getControlDisplayName = (portKey, portConfig) => {
  // 优先从设备配置中获取 custom_name
  const customName = getControlCustomName(portKey)
  if (customName) {
    return customName // 用户自定义的功能描述，如"客厅灯"、"摇尾巴"
  }
  
  // 否则使用产品配置中的名称
  return portConfig.name || portKey
}

// 获取控制端口类型标签颜色
const getControlTypeTag = (type) => {
  if (!type) return 'info'
  const typeStr = type.toUpperCase()
  if (typeStr.includes('LED')) return 'primary'
  if (typeStr.includes('RELAY')) return 'success'
  if (typeStr.includes('SERVO')) return 'warning'
  if (typeStr.includes('MOTOR')) return 'danger'
  return 'info'
}

// 根据控制端口类型获取控制组件
const getControlComponent = (type) => {
  if (!type) return null
  const typeStr = type.toUpperCase()
  
  // LED - 开关控制
  if (typeStr.includes('LED')) {
    return defineComponent({
      props: ['config', 'portKey'],
      emits: ['control'],
      setup(props, { emit }) {
        const value = ref(false)
        const handleChange = () => {
          emit('control', {
            portKey: props.portKey,
            cmd: 'led',
            device_id: parseInt(props.portKey.match(/\d+/)?.[0] || '1'),
            action: value.value ? 'on' : 'off'
          })
        }
        return () => h(ElSwitch, {
          modelValue: value.value,
          'onUpdate:modelValue': (val) => { value.value = val },
          activeText: '开',
          inactiveText: '关',
          onChange: handleChange
        })
      }
    })
  }
  
  // RELAY - 开关控制
  if (typeStr.includes('RELAY')) {
    return defineComponent({
      props: ['config', 'portKey'],
      emits: ['control'],
      setup(props, { emit }) {
        const value = ref(false)
        const handleChange = () => {
          emit('control', {
            portKey: props.portKey,
            cmd: 'relay',
            device_id: parseInt(props.portKey.match(/\d+/)?.[0] || '1'),
            action: value.value ? 'on' : 'off'
          })
        }
        return () => h(ElSwitch, {
          modelValue: value.value,
          'onUpdate:modelValue': (val) => { value.value = val },
          activeText: '开',
          inactiveText: '关',
          onChange: handleChange
        })
      }
    })
  }
  
  // SERVO - 角度或速度控制（360度连续旋转舵机）
  if (typeStr.includes('SERVO')) {
    return defineComponent({
      props: ['config', 'portKey'],
      emits: ['control'],
      setup(props, { emit }) {
        const value = ref(90) // 默认停止
        const handleChange = () => {
          emit('control', {
            portKey: props.portKey,
            cmd: 'servo',
            device_id: parseInt(props.portKey.match(/\d+/)?.[0] || '1'),
            angle: value.value
          })
        }
        return () => h('div', { style: 'width: 100%;' }, [
          h(ElSlider, {
            modelValue: value.value,
            'onUpdate:modelValue': (val) => { value.value = val },
            min: 0,
            max: 180,
            step: 1,
            showInput: true,
            onChange: handleChange
          }),
          h('div', { 
            style: 'margin-top: 8px; font-size: 12px; color: #666; text-align: center;' 
          }, `${value.value === 90 ? '停止' : value.value < 90 ? '反转' : '正转'} (90=停止)`)
        ])
      }
    })
  }
  
  // PWM - 频率和占空比控制
  if (typeStr.includes('PWM')) {
    return defineComponent({
      props: ['config', 'portKey'],
      emits: ['control'],
      setup(props, { emit }) {
        const frequency = ref(50) // 默认50Hz（舵机标准频率）
        const dutyCycle = ref(7.5) // 默认7.5%（舵机中位）
        
        const handleApply = () => {
          // 从portKey中提取通道号（pwm_m1 -> 1, pwm_m2 -> 2）
          let channel = 2  // 默认通道2 (M2)
          const match = props.portKey.match(/pwm_m(\d+)/)
          if (match) {
            channel = parseInt(match[1])
          } else {
            // 兼容其他格式，尝试提取数字
            const numMatch = props.portKey.match(/(\d+)/)
            if (numMatch) {
              channel = parseInt(numMatch[1])
            }
          }
          
          emit('control', {
            portKey: props.portKey,
            cmd: 'pwm',
            channel: channel,
            frequency: frequency.value,
            duty_cycle: dutyCycle.value
          })
        }
        
        return () => h('div', { style: 'width: 100%;' }, [
          // 频率输入
          h('div', { style: 'margin-bottom: 12px;' }, [
            h('label', { 
              style: 'display: block; margin-bottom: 4px; font-size: 12px; color: #606266;' 
            }, '频率 (Hz)'),
            h(ElInputNumber, {
              modelValue: frequency.value,
              'onUpdate:modelValue': (val) => { frequency.value = val },
              min: 1,
              max: 40000,
              step: 100,
              style: 'width: 100%;',
              controls: true,
              controlsPosition: 'right'
            })
          ]),
          // 占空比滑块
          h('div', { style: 'margin-bottom: 12px;' }, [
            h('label', { 
              style: 'display: block; margin-bottom: 4px; font-size: 12px; color: #606266;' 
            }, `占空比: ${dutyCycle.value.toFixed(1)}%`),
            h(ElSlider, {
              modelValue: dutyCycle.value,
              'onUpdate:modelValue': (val) => { dutyCycle.value = val },
              min: 0,
              max: 100,
              step: 0.1,
              showInput: false
            })
          ]),
          // 应用按钮
          h(ElButton, {
            type: 'primary',
            style: 'width: 100%;',
            onClick: handleApply
          }, { default: () => '应用PWM设置' }),
          // 提示信息
          h('div', { 
            style: 'margin-top: 8px; font-size: 11px; color: #909399; text-align: center;' 
          }, '适用于电机、LED调光等')
        ])
      }
    })
  }
  
  // 默认：按钮控制
  return defineComponent({
    props: ['config', 'portKey'],
    emits: ['control'],
    setup(props, { emit }) {
      const handleClick = () => {
        emit('control', {
          portKey: props.portKey,
          cmd: 'unknown',
          action: 'trigger'
        })
      }
      return () => h(ElButton, {
        type: 'primary',
        style: 'width: 100%;',
        onClick: handleClick
      }, { default: () => '执行控制' })
    }
  })
}

// 处理端口控制
const handlePortControl = async (controlData) => {
  if (!device.value || !device.value.is_online) {
    ElMessage.warning('设备未在线，无法控制')
    return
  }
  
  sending.value = true
  try {
    logger.info('发送控制命令:', controlData)
    const response = await sendDeviceControl(deviceUuid.value, controlData)
    if (response.data) {
      ElMessage.success('控制命令发送成功')
}
  } catch (error) {
    logger.error('发送控制命令失败:', error)
    ElMessage.error('控制命令发送失败')
  } finally {
    sending.value = false
  }
}

const getPresetTypeTag = (type) => {
  if (!type) return 'info'
  const typeStr = type.toLowerCase()
  if (typeStr.includes('led') || typeStr === 'led') return 'primary'
  if (typeStr.includes('relay') || typeStr === 'relay') return 'success'
  if (typeStr.includes('servo') || typeStr === 'servo') return 'warning'
  return 'info'
}

// 获取预设标识（用于学生引用）
const getPresetIdentifier = (preset) => {
  // 优先返回 preset_key（用户自定义预设的完整标识，Coze 需要这个）
  if (preset.preset_key) {
    return preset.preset_key
  }
  // 或者返回 ID（系统预设）
  if (preset.id && !preset.id.toString().startsWith('custom_preset_')) {
    return preset.id
  }
  // 对于序列类型（兜底）
  if (preset.type === 'sequence' || preset.cmd === 'sequence') {
    return 'sequence'
  }
  return null
}

// 复制预设标识到剪贴板
const copyPresetIdentifier = async (preset) => {
  const identifier = getPresetIdentifier(preset)
  if (!identifier) {
    ElMessage.warning('该预设没有可复制的标识')
    return
  }
  
  try {
    // 使用 Clipboard API 复制到剪贴板
    await navigator.clipboard.writeText(identifier)
    ElMessage.success(`已复制预设标识：${identifier}`)
  } catch (error) {
    // 降级方案：使用传统方法
    try {
      const textArea = document.createElement('textarea')
      textArea.value = identifier
      textArea.style.position = 'fixed'
      textArea.style.opacity = '0'
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      ElMessage.success(`已复制预设标识：${identifier}`)
    } catch (err) {
      logger.error('复制失败:', err)
      ElMessage.error('复制失败，请手动复制')
    }
  }
}

// 返回设备列表
const goBack = () => {
  router.push('/device/devices')
}

// 生命周期
onMounted(async () => {
  await loadDeviceInfo()
  // 确保设备配置加载完成后再加载预设指令（包含用户自定义预设）
  await loadPresets()
})
</script>

<style scoped>
.device-remote-control-page {
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

.device-tags {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.presets-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.preset-card {
  transition: all 0.3s;
}

.preset-card.disabled {
  opacity: 0.6;
}

.preset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preset-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.preset-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.preset-identifier {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 13px;
}

.preset-identifier .identifier-label {
  color: #606266;
  font-weight: 500;
  margin-right: 8px;
  white-space: nowrap;
}

.preset-identifier .identifier-value {
  display: flex;
  align-items: center;
  flex: 1;
}

.preset-controls {
  margin-top: 16px;
}

.control-group {
  margin-top: 12px;
}

.control-label {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
  text-align: center;
}

.sequence-info {
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 12px;
}

/* 控制端口区域样式 */
.control-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.control-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.control-card {
  transition: all 0.3s;
}

.control-card.disabled {
  opacity: 0.6;
}

.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.control-name-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.control-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.control-custom-name {
  font-size: 13px;
  color: #409eff;
  font-weight: 500;
}

.control-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 16px;
}

.control-controls {
  margin-top: 16px;
}

.control-hint {
  margin-top: 8px;
  text-align: center;
}
</style>
