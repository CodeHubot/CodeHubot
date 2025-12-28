/**
 * 日志工具类
 * 统一管理前端日志输出，生产环境自动禁用调试日志
 */

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  NONE: 4
}

class Logger {
  constructor() {
    // 根据环境设置日志级别
    this.level = this._getLogLevel()
    this.isProduction = import.meta.env.MODE === 'production'
  }

  _getLogLevel() {
    const mode = import.meta.env.MODE
    
    // 生产环境只显示错误
    if (mode === 'production') {
      return LOG_LEVELS.ERROR
    }
    
    // 测试环境显示警告及以上
    if (mode === 'testing') {
      return LOG_LEVELS.WARN
    }
    
    // 开发环境显示所有日志
    return LOG_LEVELS.DEBUG
  }

  _shouldLog(level) {
    return level >= this.level
  }

  _formatMessage(level, ...args) {
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    return [`[${timestamp}] [${level}]`, ...args]
  }

  /**
   * 调试日志 - 仅开发环境
   * @param {...any} args 
   */
  debug(...args) {
    if (this._shouldLog(LOG_LEVELS.DEBUG)) {
      console.log(...this._formatMessage('DEBUG', ...args))
    }
  }

  /**
   * 信息日志
   * @param {...any} args 
   */
  info(...args) {
    if (this._shouldLog(LOG_LEVELS.INFO)) {
      console.log(...this._formatMessage('INFO', ...args))
    }
  }

  /**
   * 警告日志
   * @param {...any} args 
   */
  warn(...args) {
    if (this._shouldLog(LOG_LEVELS.WARN)) {
      console.warn(...this._formatMessage('WARN', ...args))
    }
  }

  /**
   * 错误日志
   * @param {...any} args 
   */
  error(...args) {
    if (this._shouldLog(LOG_LEVELS.ERROR)) {
      console.error(...this._formatMessage('ERROR', ...args))
    }
    
    // TODO: 可以在这里添加错误上报到服务器的逻辑
    // this._reportError(args)
  }

  /**
   * API请求日志
   * @param {string} method 
   * @param {string} url 
   * @param {any} data 
   */
  api(method, url, data = null) {
    if (this._shouldLog(LOG_LEVELS.DEBUG)) {
      const message = [`API ${method.toUpperCase()}:`, url]
      if (data) {
        message.push('\nData:', data)
      }
      console.log(...this._formatMessage('API', ...message))
    }
  }

  /**
   * API响应日志
   * @param {number} status 
   * @param {string} url 
   * @param {any} data 
   */
  apiResponse(status, url, data = null) {
    if (this._shouldLog(LOG_LEVELS.DEBUG)) {
      const level = status >= 400 ? 'ERROR' : 'DEBUG'
      const message = [`API Response [${status}]:`, url]
      if (data && this._shouldLog(LOG_LEVELS.DEBUG)) {
        message.push('\nResponse:', data)
      }
      
      if (level === 'ERROR') {
        console.error(...this._formatMessage(level, ...message))
      } else {
        console.log(...this._formatMessage(level, ...message))
      }
    }
  }

  /**
   * 路由导航日志
   * @param {string} from 
   * @param {string} to 
   */
  route(from, to) {
    if (this._shouldLog(LOG_LEVELS.DEBUG)) {
      console.log(...this._formatMessage('ROUTE', `${from} → ${to}`))
    }
  }

  /**
   * 分组日志
   * @param {string} title 
   * @param {Function} callback 
   */
  group(title, callback) {
    if (this._shouldLog(LOG_LEVELS.DEBUG)) {
      console.group(title)
      callback()
      console.groupEnd()
    }
  }

  /**
   * 性能监控
   * @param {string} label 
   */
  time(label) {
    if (this._shouldLog(LOG_LEVELS.DEBUG)) {
      console.time(label)
    }
  }

  /**
   * 性能监控结束
   * @param {string} label 
   */
  timeEnd(label) {
    if (this._shouldLog(LOG_LEVELS.DEBUG)) {
      console.timeEnd(label)
    }
  }
}

// 创建单例
const logger = new Logger()

// 导出
export default logger

// 也可以导出类，允许创建多个实例
export { Logger }







