// 为了向后兼容，这里重新导出统一颜色系统的tokens
// 新代码建议直接使用 @/styles/colors 中的 tokens
import { tokens } from './colors';

export const colors = {
  // 背景层级
  pageBg: tokens.background.page,
  panelBg: tokens.background.panel,
  hoverBg: tokens.background.hover,
  inputBg: tokens.background.input,
  sidebarBg: tokens.background.sidebar,

  // 文字
  textPrimary: tokens.text.primary,
  textSecondary: tokens.text.secondary,
  textTertiary: tokens.text.tertiary,
  textDisabled: tokens.text.disabled,

  // 边框
  borderPrimary: tokens.border.primary,
  borderSecondary: tokens.border.secondary,

  // 语义色
  brand: tokens.primary,
  success: tokens.success,
  error: tokens.error,
  warning: tokens.warning,
  info: tokens.info,
  timeout: tokens.timeout,

  // 数据可视化
  chart: tokens.chart,
} as const;

export { fontSize } from './colors';

/** 与 styles/colors/variables.css 中 --font-family-sans / --font-family-mono 保持一致 */
export const fonts = {
  sans: '"Inter", "SF Pro Text", -apple-system, "Segoe UI", sans-serif',
  mono: '"JetBrains Mono", "Fira Code", Consolas, monospace',
} as const;

export const spacing = {
  sidebarCollapsed: 56,
  sidebarExpanded: 220,
  topBarHeight: 48,
} as const;
