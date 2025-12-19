/**
 * 日期时间格式化工具函数
 */

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期对象或日期字符串
 * @param {string} format - 格式化模板，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '-'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化日期（不包含时间）
 * @param {string|Date} date - 日期对象或日期字符串
 * @returns {string} 格式化后的日期字符串 YYYY-MM-DD
 */
export function formatDateOnly(date) {
  return formatDate(date, 'YYYY-MM-DD')
}

/**
 * 格式化时间（不包含日期）
 * @param {string|Date} date - 日期对象或日期字符串
 * @returns {string} 格式化后的时间字符串 HH:mm:ss
 */
export function formatTimeOnly(date) {
  return formatDate(date, 'HH:mm:ss')
}

/**
 * 相对时间格式化（如：刚刚、5分钟前、2小时前等）
 * @param {string|Date} date - 日期对象或日期字符串
 * @returns {string} 相对时间描述
 */
export function formatRelativeTime(date) {
  if (!date) return '-'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  
  const now = new Date()
  const diff = now - d // 毫秒差
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  // 超过7天显示完整日期
  return formatDate(date, 'YYYY-MM-DD')
}
