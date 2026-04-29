/**
 * 语义颜色token定义
 *
 * 基于基础色系定义功能性颜色token，包括：
 * - 主要语义色（primary、success、error、warning、info）
 * - 背景色系（页面、面板、悬停、输入框等）
 * - 文字颜色（主要、次要、第三等级、禁用）
 * - 边框颜色（主要、次要）
 *
 * 所有token都引用基础色系，便于统一管理和主题切换
 */

import { palette } from './palette';

// 主要语义颜色
export const semanticColors = {
  primary: palette.yellow[400], // 品牌主色 #FACC15
  success: palette.green[500], // 成功色 #22C55E
  error: palette.red[500], // 错误色 #EF4444
  warning: palette.yellow[500], // 警告色 #F59E0B
  info: palette.blue[500], // 信息色 #3B82F6
  timeout: palette.purple[500], // 超时色 #A855F7
} as const;

// 背景色系
export const backgroundColors = {
  page: palette.gray[900], // 页面背景 #111827
  panel: '#232436', // 面板背景（定制深色）
  hover: '#2C2D42', // 悬停背景（定制深色）
  input: '#191A2C', // 输入框背景（定制深色）
  sidebar: '#16172A', // 侧边栏背景（定制深色）
} as const;

// 文字颜色
export const textColors = {
  primary: palette.gray[200], // 主要文字 #E5E7EB
  secondary: palette.gray[400], // 次要文字 #9CA3AF
  tertiary: palette.gray[500], // 第三等级文字 #6B7280
  disabled: palette.gray[600], // 禁用文字 #4B5563
} as const;

// 边框颜色
export const borderColors = {
  primary: palette.gray[600], // 主要边框 #4B5563
  secondary: '#2D2E40', // 次要边框（定制深色）
} as const;

// 数据可视化颜色系列
export const chartColors = [
  semanticColors.primary, // #FACC15
  semanticColors.info, // #3B82F6
  semanticColors.success, // #22C55E
  semanticColors.error, // #EF4444
  semanticColors.timeout, // #A855F7
  palette.pink[500], // #EC4899
] as const;

// 统一导出所有token
export const tokens = {
  // 语义颜色
  ...semanticColors,

  // 分组颜色
  background: backgroundColors,
  text: textColors,
  border: borderColors,
  chart: chartColors,
} as const;

// 类型定义
export type SemanticColor = keyof typeof semanticColors;
export type BackgroundColor = keyof typeof backgroundColors;
export type TextColor = keyof typeof textColors;
export type BorderColor = keyof typeof borderColors;
