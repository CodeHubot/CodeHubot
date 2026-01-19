<template>
  <div class="device-config-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回设备详情
        </el-button>
        <div class="page-title">
          <h2>设备配置</h2>
          <div class="device-info" v-if="deviceInfo.device_id">
            <span class="device-name">{{ deviceInfo.name }}</span>
            <el-tag :type="deviceInfo.is_online ? 'success' : 'danger'" size="small">
              {{ deviceInfo.is_online ? '在线' : '离线' }}
            </el-tag>
            <el-tag type="info" size="small">{{ deviceInfo.device_type }}</el-tag>
          </div>
        </div>
      </div>
      <div class="header-controls">
        <el-button @click="goToDetail">
          <el-icon><View /></el-icon>
          设备详情
        </el-button>
        <el-button @click="goToRealtime" :disabled="!deviceInfo.is_online">
          <el-icon><Monitor /></el-icon>
          实时数据
        </el-button>
        <el-button @click="goToRemoteControl" :disabled="!deviceInfo.is_online">
          <el-icon><Operation /></el-icon>
          远程控制
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="page-content" v-if="!loading">
      <!-- 配置选项卡 -->
      <el-tabs v-model="activeTab" class="config-tabs">
        <!-- 基本配置 -->
        <el-tab-pane label="基本配置" name="basic">
          <div class="config-section">
            <div class="section-header">
              <h3>设备基本信息</h3>
              <el-button type="primary" @click="saveBasicConfig" :loading="saveLoading">
                <el-icon><Check /></el-icon>
                保存配置
              </el-button>
            </div>
            <el-form :model="basicConfig" :rules="basicRules" ref="basicFormRef" label-width="120px">
              <div class="form-grid">
                <el-form-item label="设备名称" prop="name">
                  <el-input v-model="basicConfig.name" placeholder="请输入设备名称" />
                </el-form-item>
                <el-form-item label="设备类型" prop="device_type">
                  <el-select v-model="basicConfig.device_type" placeholder="请选择设备类型">
                    <el-option label="温度传感器" value="温度传感器" />
                    <el-option label="湿度传感器" value="湿度传感器" />
                    <el-option label="压力传感器" value="压力传感器" />
                    <el-option label="光照传感器" value="光照传感器" />
                    <el-option label="运动传感器" value="运动传感器" />
                    <el-option label="智能开关" value="智能开关" />
                  </el-select>
                </el-form-item>
                <el-form-item label="设备位置" prop="location">
                  <el-input v-model="basicConfig.location" placeholder="请输入设备位置" />
                </el-form-item>
                <el-form-item label="设备组" prop="group_name">
                  <el-select v-model="basicConfig.group_name" placeholder="请选择设备组">
                    <el-option label="环境监测设备组" value="环境监测设备组" />
                    <el-option label="安全监控设备组" value="安全监控设备组" />
                    <el-option label="智能控制设备组" value="智能控制设备组" />
                  </el-select>
                </el-form-item>
                <el-form-item label="数据上报间隔" prop="report_interval">
                  <el-input-number 
                    v-model="basicConfig.report_interval" 
                    :min="1" 
                    :max="3600" 
                    placeholder="秒"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item label="心跳间隔" prop="heartbeat_interval">
                  <el-input-number 
                    v-model="basicConfig.heartbeat_interval" 
                    :min="10" 
                    :max="300" 
                    placeholder="秒"
                    style="width: 100%"
                  />
                </el-form-item>
              </div>
              <el-form-item label="设备描述">
                <el-input 
                  v-model="basicConfig.description" 
                  type="textarea" 
                  rows="3" 
                  placeholder="请输入设备描述"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 传感器配置 -->
        <el-tab-pane label="传感器配置" name="sensors">
          <div class="config-section">
            <div class="section-header">
              <h3>传感器配置</h3>
              <div class="header-actions">
                <el-button @click="addSensor">
                  <el-icon><Plus /></el-icon>
                  添加传感器
                </el-button>
                <el-button type="primary" @click="saveSensorConfig" :loading="saveLoading">
                  <el-icon><Check /></el-icon>
                  保存配置
                </el-button>
              </div>
            </div>
            <div class="sensor-list">
              <div 
                v-for="(sensor, index) in sensorConfig" 
                :key="index"
                class="sensor-item"
              >
                <div class="sensor-header">
                  <span class="sensor-title">传感器 {{ index + 1 }}</span>
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click="removeSensor(index)"
                    :disabled="sensorConfig.length <= 1"
                  >
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
                <el-form :model="sensor" label-width="100px" class="sensor-form">
                  <div class="form-row">
                    <el-form-item label="传感器名称">
                      <el-input v-model="sensor.name" placeholder="请输入传感器名称" />
                    </el-form-item>
                    <el-form-item label="传感器类型">
                      <el-select v-model="sensor.type" placeholder="请选择类型">
                        <el-option label="温度" value="temperature" />
                        <el-option label="湿度" value="humidity" />
                        <el-option label="压力" value="pressure" />
                        <el-option label="光照" value="light" />
                        <el-option label="运动" value="motion" />
                        <el-option label="声音" value="sound" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="端口">
                      <el-select v-model="sensor.port" placeholder="请选择端口">
                        <el-option label="A0" value="A0" />
                        <el-option label="A1" value="A1" />
                        <el-option label="A2" value="A2" />
                        <el-option label="A3" value="A3" />
                        <el-option label="D2" value="D2" />
                        <el-option label="D3" value="D3" />
                        <el-option label="D4" value="D4" />
                        <el-option label="D5" value="D5" />
                      </el-select>
                    </el-form-item>
                  </div>
                  <div class="form-row">
                    <el-form-item label="单位">
                      <el-input v-model="sensor.unit" placeholder="如: °C, %, lux" />
                    </el-form-item>
                    <el-form-item label="最小值">
                      <el-input-number v-model="sensor.min" placeholder="最小值" style="width: 100%" />
                    </el-form-item>
                    <el-form-item label="最大值">
                      <el-input-number v-model="sensor.max" placeholder="最大值" style="width: 100%" />
                    </el-form-item>
                  </div>
                  <div class="form-row">
                    <el-form-item label="采样频率">
                      <el-input-number 
                        v-model="sensor.sample_rate" 
                        :min="1" 
                        :max="1000" 
                        placeholder="Hz"
                        style="width: 100%"
                      />
                    </el-form-item>
                    <el-form-item label="精度">
                      <el-input-number 
                        v-model="sensor.precision" 
                        :min="0" 
                        :max="10" 
                        placeholder="小数位数"
                        style="width: 100%"
                      />
                    </el-form-item>
                    <el-form-item label="启用状态">
                      <el-switch v-model="sensor.enabled" />
                    </el-form-item>
                  </div>
                </el-form>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 控制器配置 -->
        <el-tab-pane label="控制器配置" name="controls">
          <div class="config-section">
            <div class="section-header">
              <h3>控制器配置</h3>
              <div class="header-actions">
                <el-button @click="addControl">
                  <el-icon><Plus /></el-icon>
                  添加控制器
                </el-button>
                <el-button type="primary" @click="saveControlConfig" :loading="saveLoading">
                  <el-icon><Check /></el-icon>
                  保存配置
                </el-button>
              </div>
            </div>
            <div class="control-list">
              <div 
                v-for="(control, index) in controlConfig" 
                :key="index"
                class="control-item"
              >
                <div class="control-header">
                  <span class="control-title">控制器 {{ index + 1 }}</span>
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click="removeControl(index)"
                    :disabled="controlConfig.length <= 1"
                  >
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
                <el-form :model="control" label-width="100px" class="control-form">
                  <div class="form-row">
                    <el-form-item label="控制器名称">
                      <el-input v-model="control.name" placeholder="请输入控制器名称" />
                    </el-form-item>
                    <el-form-item label="控制器类型">
                      <el-select v-model="control.type" placeholder="请选择类型">
                        <el-option label="数字输出" value="digital" />
                        <el-option label="PWM输出" value="pwm" />
                        <el-option label="舵机控制" value="servo" />
                        <el-option label="继电器" value="relay" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="端口">
                      <el-select v-model="control.port" placeholder="请选择端口">
                        <el-option label="D2" value="D2" />
                        <el-option label="D3" value="D3" />
                        <el-option label="D4" value="D4" />
                        <el-option label="D5" value="D5" />
                        <el-option label="D6" value="D6" />
                        <el-option label="D7" value="D7" />
                        <el-option label="D8" value="D8" />
                        <el-option label="D9" value="D9" />
                      </el-select>
                    </el-form-item>
                  </div>
                  <div class="form-row" v-if="control.type === 'pwm' || control.type === 'servo'">
                    <el-form-item label="最小值">
                      <el-input-number v-model="control.min" placeholder="最小值" style="width: 100%" />
                    </el-form-item>
                    <el-form-item label="最大值">
                      <el-input-number v-model="control.max" placeholder="最大值" style="width: 100%" />
                    </el-form-item>
                    <el-form-item label="默认值">
                      <el-input-number v-model="control.default_value" placeholder="默认值" style="width: 100%" />
                    </el-form-item>
                  </div>
                  <div class="form-row">
                    <el-form-item label="启用状态">
                      <el-switch v-model="control.enabled" />
                    </el-form-item>
                    <el-form-item label="自动控制">
                      <el-switch v-model="control.auto_control" />
                    </el-form-item>
                  </div>
                </el-form>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 网络配置 -->
        <el-tab-pane label="网络配置" name="network">
          <div class="config-section">
            <div class="section-header">
              <h3>网络配置</h3>
              <el-button type="primary" @click="saveNetworkConfig" :loading="saveLoading">
                <el-icon><Check /></el-icon>
                保存配置
              </el-button>
            </div>

            <!-- 配置服务器地址提示 -->
            <el-alert
              title="配网提示"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 20px"
            >
              <p style="margin: 0 0 8px 0;">设备首次配网时，请填写以下配置服务器地址以自动获取网络配置：</p>
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-input
                  :model-value="configServerUrl"
                  readonly
                  style="flex: 1"
                >
                  <template #prepend>配置服务器</template>
                </el-input>
                <el-button @click="copyConfigUrl" :icon="CopyDocument">复制</el-button>
              </div>
            </el-alert>

            <el-form :model="networkConfig" :rules="networkRules" ref="networkFormRef" label-width="120px">
              <div class="form-grid">
                <el-form-item label="WiFi SSID" prop="wifi_ssid">
                  <el-input v-model="networkConfig.wifi_ssid" placeholder="请输入WiFi名称" />
                </el-form-item>
                <el-form-item label="WiFi密码" prop="wifi_password">
                  <el-input 
                    v-model="networkConfig.wifi_password" 
                    type="password" 
                    placeholder="请输入WiFi密码"
                    show-password
                  />
                </el-form-item>
                <el-form-item label="静态IP">
                  <el-switch v-model="networkConfig.use_static_ip" />
                </el-form-item>
                <el-form-item label="IP地址" v-if="networkConfig.use_static_ip" prop="static_ip">
                  <el-input v-model="networkConfig.static_ip" placeholder="192.168.1.100" />
                </el-form-item>
                <el-form-item label="子网掩码" v-if="networkConfig.use_static_ip" prop="subnet_mask">
                  <el-input v-model="networkConfig.subnet_mask" placeholder="255.255.255.0" />
                </el-form-item>
                <el-form-item label="网关" v-if="networkConfig.use_static_ip" prop="gateway">
                  <el-input v-model="networkConfig.gateway" placeholder="192.168.1.1" />
                </el-form-item>
                <el-form-item label="DNS服务器" v-if="networkConfig.use_static_ip" prop="dns_server">
                  <el-input v-model="networkConfig.dns_server" placeholder="8.8.8.8" />
                </el-form-item>
                <el-form-item label="服务器地址" prop="server_host">
                  <el-input v-model="networkConfig.server_host" placeholder="请输入服务器地址" />
                </el-form-item>
                <el-form-item label="服务器端口" prop="server_port">
                  <el-input-number 
                    v-model="networkConfig.server_port" 
                    :min="1" 
                    :max="65535" 
                    placeholder="端口号"
                    style="width: 100%"
                  />
                </el-form-item>
              </div>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 高级配置 -->
        <el-tab-pane label="高级配置" name="advanced">
          <div class="config-section">
            <div class="section-header">
              <h3>高级配置</h3>
              <el-button type="primary" @click="saveAdvancedConfig" :loading="saveLoading">
                <el-icon><Check /></el-icon>
                保存配置
              </el-button>
            </div>
            <el-form :model="advancedConfig" label-width="150px">
              <div class="form-grid">
                <el-form-item label="启用OTA升级">
                  <el-switch v-model="advancedConfig.enable_ota" />
                </el-form-item>
                <el-form-item label="启用远程调试">
                  <el-switch v-model="advancedConfig.enable_remote_debug" />
                </el-form-item>
                <el-form-item label="启用数据加密">
                  <el-switch v-model="advancedConfig.enable_encryption" />
                </el-form-item>
                <el-form-item label="低功耗模式">
                  <el-switch v-model="advancedConfig.low_power_mode" />
                </el-form-item>
                <el-form-item label="看门狗超时" prop="watchdog_timeout">
                  <el-input-number 
                    v-model="advancedConfig.watchdog_timeout" 
                    :min="1" 
                    :max="300" 
                    placeholder="秒"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item label="日志级别">
                  <el-select v-model="advancedConfig.log_level" placeholder="请选择日志级别">
                    <el-option label="DEBUG" value="DEBUG" />
                    <el-option label="INFO" value="INFO" />
                    <el-option label="WARNING" value="WARNING" />
                    <el-option label="ERROR" value="ERROR" />
                  </el-select>
                </el-form-item>
                <el-form-item label="最大日志文件数">
                  <el-input-number 
                    v-model="advancedConfig.max_log_files" 
                    :min="1" 
                    :max="100" 
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item label="配置备份">
                  <el-switch v-model="advancedConfig.config_backup" />
                </el-form-item>
              </div>
              <el-form-item label="自定义配置">
                <el-input 
                  v-model="advancedConfig.custom_config" 
                  type="textarea" 
                  rows="6" 
                  placeholder="请输入JSON格式的自定义配置"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 加载状态 -->
    <div v-else class="loading-container">
      <el-loading-directive v-loading="loading" text="加载设备配置中...">
        <div style="height: 200px;"></div>
      </el-loading-directive>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft,
  View,
  Monitor,
  Operation,
  Check,
  Plus,
  Delete,
  CopyDocument
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(true)
const saveLoading = ref(false)
const activeTab = ref('basic')
const basicFormRef = ref()
const networkFormRef = ref()
const configServerUrl = ref('http://config.example.com:8001')  // 配置服务器地址

// 设备信息
const deviceInfo = reactive({
  device_id: '',
  uuid: '',
  name: '',
  device_type: '',
  is_online: false
})

// 基本配置
const basicConfig = reactive({
  name: '',
  device_type: '',
  location: '',
  group_name: '',
  report_interval: 30,
  heartbeat_interval: 60,
  description: ''
})

// 传感器配置
const sensorConfig = ref([
  {
    name: '温度传感器',
    type: 'temperature',
    port: 'A0',
    unit: '°C',
    min: -40,
    max: 85,
    sample_rate: 1,
    precision: 2,
    enabled: true
  }
])

// 控制器配置
const controlConfig = ref([
  {
    name: 'LED灯',
    type: 'digital',
    port: 'D2',
    min: 0,
    max: 1,
    default_value: 0,
    enabled: true,
    auto_control: false
  }
])

// 网络配置
const networkConfig = reactive({
  wifi_ssid: '',
  wifi_password: '',
  use_static_ip: false,
  static_ip: '',
  subnet_mask: '255.255.255.0',
  gateway: '',
  dns_server: '8.8.8.8',
  server_host: '',
  server_port: 8080
})

// 高级配置
const advancedConfig = reactive({
  enable_ota: true,
  enable_remote_debug: false,
  enable_encryption: true,
  low_power_mode: false,
  watchdog_timeout: 30,
  log_level: 'INFO',
  max_log_files: 10,
  config_backup: true,
  custom_config: ''
})

// 验证规则
const basicRules = {
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' }
  ],
  device_type: [
    { required: true, message: '请选择设备类型', trigger: 'change' }
  ],
  location: [
    { required: true, message: '请输入设备位置', trigger: 'blur' }
  ]
}

const networkRules = {
  wifi_ssid: [
    { required: true, message: '请输入WiFi SSID', trigger: 'blur' }
  ],
  wifi_password: [
    { required: true, message: '请输入WiFi密码', trigger: 'blur' }
  ],
  server_host: [
    { required: true, message: '请输入服务器地址', trigger: 'blur' }
  ],
  server_port: [
    { required: true, message: '请输入服务器端口', trigger: 'blur' }
  ]
}

// 导航方法
const goBack = () => {
  router.push(`/device/${route.params.uuid}/detail`)
}

const goToDetail = () => {
  router.push(`/device/${route.params.uuid}/detail`)
}

const goToRealtime = () => {
  router.push(`/device/${route.params.uuid}/realtime`)
}

const goToRemoteControl = () => {
  router.push(`/device/${route.params.uuid}/remote-control`)
}

// 加载设备配置
const loadDeviceConfig = async () => {
  try {
    const uuid = route.params.uuid
    if (!uuid) {
      ElMessage.error('设备UUID参数缺失')
      goBack()
      return
    }

    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 模拟设备信息
    Object.assign(deviceInfo, {
      device_id: `DEVICE_${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
      uuid: uuid,
      name: '智能温湿度传感器-001',
      device_type: '温度传感器',
      is_online: Math.random() > 0.3
    })
    
    // 模拟基本配置
    Object.assign(basicConfig, {
      name: deviceInfo.name,
      device_type: deviceInfo.device_type,
      location: '办公室A区-工位001',
      group_name: '环境监测设备组',
      report_interval: 30,
      heartbeat_interval: 60,
      description: '用于监测环境温湿度的智能传感器设备'
    })
    
    // 模拟网络配置
    Object.assign(networkConfig, {
      wifi_ssid: 'Office-WiFi',
      wifi_password: '',
      use_static_ip: false,
      static_ip: '192.168.1.100',
      subnet_mask: '255.255.255.0',
      gateway: '192.168.1.1',
      dns_server: '8.8.8.8',
      server_host: 'iot.example.com',
      server_port: 8080
    })
    
  } catch (error) {
    ElMessage.error('加载设备配置失败')
    console.error('Load config error:', error)
  } finally {
    loading.value = false
  }
}

// 保存基本配置
const saveBasicConfig = async () => {
  if (!basicFormRef.value) return
  
  try {
    await basicFormRef.value.validate()
    saveLoading.value = true
    
    // 模拟保存配置
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('基本配置已保存')
  } catch (error) {
    if (error !== false) {
      ElMessage.error('保存基本配置失败')
    }
  } finally {
    saveLoading.value = false
  }
}

// 添加传感器
const addSensor = () => {
  sensorConfig.value.push({
    name: `传感器${sensorConfig.value.length + 1}`,
    type: 'temperature',
    port: 'A0',
    unit: '°C',
    min: 0,
    max: 100,
    sample_rate: 1,
    precision: 2,
    enabled: true
  })
}

// 删除传感器
const removeSensor = (index) => {
  sensorConfig.value.splice(index, 1)
}

// 保存传感器配置
const saveSensorConfig = async () => {
  try {
    saveLoading.value = true
    
    // 模拟保存配置
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('传感器配置已保存')
  } catch (error) {
    ElMessage.error('保存传感器配置失败')
  } finally {
    saveLoading.value = false
  }
}

// 添加控制器
const addControl = () => {
  controlConfig.value.push({
    name: `控制器${controlConfig.value.length + 1}`,
    type: 'digital',
    port: 'D2',
    min: 0,
    max: 1,
    default_value: 0,
    enabled: true,
    auto_control: false
  })
}

// 删除控制器
const removeControl = (index) => {
  controlConfig.value.splice(index, 1)
}

// 保存控制器配置
const saveControlConfig = async () => {
  try {
    saveLoading.value = true
    
    // 模拟保存配置
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('控制器配置已保存')
  } catch (error) {
    ElMessage.error('保存控制器配置失败')
  } finally {
    saveLoading.value = false
  }
}

// 保存网络配置
const saveNetworkConfig = async () => {
  if (!networkFormRef.value) return
  
  try {
    await networkFormRef.value.validate()
    saveLoading.value = true
    
    // 模拟保存配置
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('网络配置已保存')
  } catch (error) {
    if (error !== false) {
      ElMessage.error('保存网络配置失败')
    }
  } finally {
    saveLoading.value = false
  }
}

// 保存高级配置
const saveAdvancedConfig = async () => {
  try {
    saveLoading.value = true
    
    // 验证自定义配置JSON格式
    if (advancedConfig.custom_config) {
      try {
        JSON.parse(advancedConfig.custom_config)
      } catch (e) {
        ElMessage.error('自定义配置JSON格式错误')
        return
      }
    }
    
    // 模拟保存配置
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('高级配置已保存')
  } catch (error) {
    ElMessage.error('保存高级配置失败')
  } finally {
    saveLoading.value = false
  }
}

// 复制配置服务器地址
const copyConfigUrl = async () => {
  try {
    await navigator.clipboard.writeText(configServerUrl.value)
    ElMessage.success('配置服务器地址已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 加载配置服务器地址
const loadConfigServerUrl = async () => {
  try {
    const response = await request.get('/system-config/configs/public', {
      params: { exclude_policies: true }
    })
    const configs = response.data || []
    const configItem = configs.find(c => c.config_key === 'device_config_server_url')
    if (configItem && configItem.config_value) {
      configServerUrl.value = configItem.config_value
    }
  } catch (error) {
    console.error('加载配置服务器地址失败:', error)
    // 使用默认值，不显示错误消息
  }
}

// 组件挂载
onMounted(() => {
  loadDeviceConfig()
  loadConfigServerUrl()
})
</script>

<style scoped>
.device-config-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  background: white;
  padding: 20px 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  color: #409eff;
  font-size: 14px;
}

.page-title h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 20px;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-name {
  color: #606266;
  font-size: 14px;
}

.header-controls {
  display: flex;
  gap: 12px;
}

.page-content {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.config-tabs {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.config-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.sensor-list,
.control-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sensor-item,
.control-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}

.sensor-header,
.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.sensor-title,
.control-title {
  font-weight: 500;
  color: #303133;
}

.sensor-form,
.control-form {
  margin: 0;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 50vh;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  padding: 0 20px;
}

:deep(.el-tabs__content) {
  padding: 0;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .section-header {
    flex-direction: column;
    gap: 12px;
  }
}
</style>