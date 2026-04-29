/**
 * 统一颜色配置系统入口
 *
 * 导出完整的颜色系统，包括：
 * - 基础色系(palette)
 * - 语义token(tokens)
 * - CSS变量生成函数
 *
 * 使用示例：
 * ```typescript
 * import { palette, tokens, generateCSSVariables } from '@/styles/colors';
 *
 * // 使用基础色系
 * const blueColor = palette.blue[500];
 *
 * // 使用语义token
 * const primaryColor = tokens.primary;
 * const bgColor = tokens.background.panel;
 *
 * // 生成CSS变量
 * const cssVars = generateCSSVariables();
 * ```
 */

import { palette } from './palette';
import { tokens } from './tokens';
import { TYPOGRAPHY_SEED, fontSize } from './typography';

// 导出基础色系和语义token
export { palette, tokens, fontSize, TYPOGRAPHY_SEED };
export type { ColorScale, ColorName, ColorShade } from './palette';
export type { SemanticColor, BackgroundColor, TextColor, BorderColor } from './tokens';
export type { FontSizeToken } from './typography';

/**
 * 生成CSS变量字符串
 *
 * 将所有颜色token转换为CSS变量格式，可以动态注入到页面中
 * 支持运行时主题切换
 *
 * @returns CSS变量字符串
 */
export function generateCSSVariables(): string {
  const cssVars: string[] = [];

  // 语义颜色变量
  cssVars.push(`--color-primary: ${tokens.primary};`);
  cssVars.push(`--color-success: ${tokens.success};`);
  cssVars.push(`--color-error: ${tokens.error};`);
  cssVars.push(`--color-warning: ${tokens.warning};`);
  cssVars.push(`--color-info: ${tokens.info};`);
  cssVars.push(`--color-timeout: ${tokens.timeout};`);

  // 背景色变量
  Object.entries(tokens.background).forEach(([key, value]) => {
    cssVars.push(`--color-background-${key}: ${value};`);
  });

  // 文字色变量
  Object.entries(tokens.text).forEach(([key, value]) => {
    cssVars.push(`--color-text-${key}: ${value};`);
  });

  // 边框色变量
  Object.entries(tokens.border).forEach(([key, value]) => {
    cssVars.push(`--color-border-${key}: ${value};`);
  });

  // 基础色系变量
  Object.entries(palette).forEach(([colorName, colorScale]) => {
    Object.entries(colorScale).forEach(([shade, value]) => {
      cssVars.push(`--color-${colorName}-${shade}: ${value};`);
    });
  });

  return cssVars.join('\n  ');
}

/**
 * 获取antd主题配置
 *
 * 基于统一颜色系统生成antd的主题配置
 *
 * @returns antd主题配置对象
 */
export function getAntdThemeConfig() {
  return {
    token: {
      ...TYPOGRAPHY_SEED,

      // 主要颜色
      colorPrimary: tokens.primary,

      // 背景颜色
      colorBgContainer: tokens.background.panel,
      colorBgElevated: tokens.background.hover,
      colorBgBase: tokens.background.page,

      // 边框颜色
      colorBorder: tokens.border.primary,
      colorBorderSecondary: tokens.border.secondary,

      // 文字颜色
      colorText: tokens.text.primary,
      colorTextSecondary: tokens.text.secondary,
      colorTextTertiary: tokens.text.tertiary,
      colorTextDisabled: tokens.text.disabled,

      // 语义颜色
      colorSuccess: tokens.success,
      colorError: tokens.error,
      colorWarning: tokens.warning,
      colorInfo: tokens.info,

      borderRadius: 6,
    },
    components: {
      Table: {
        headerBg: tokens.background.input,
        headerColor: tokens.text.tertiary,
        rowHoverBg: tokens.background.hover,
        borderColor: tokens.border.secondary,
        colorBgContainer: tokens.background.panel,
        headerSplitColor: tokens.border.secondary,
      },
      Select: {
        colorBgContainer: tokens.background.input,
      },
      InputNumber: {
        colorBgContainer: tokens.background.input,
      },
      Slider: {
        trackBg: tokens.primary,
        trackHoverBg: tokens.primary,
        handleColor: tokens.primary,
        handleActiveColor: tokens.primary,
        railBg: tokens.border.primary,
        railHoverBg: tokens.border.primary,
      },
      Tag: {
        defaultBg: tokens.background.hover,
        defaultColor: tokens.text.secondary,
      },
    },
  };
}

/**
 * 获取ECharts主题配置
 *
 * 基于统一颜色系统生成ECharts的主题配置
 *
 * @returns ECharts主题配置对象
 */
export function getEChartsThemeConfig() {
  return {
    backgroundColor: 'transparent',
    textStyle: {
      color: tokens.text.secondary,
      fontFamily: '"Inter", sans-serif',
    },
    color: tokens.chart,
    grid: {
      top: 40,
      right: 24,
      bottom: 32,
      left: 56,
      containLabel: false,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: tokens.background.hover,
      borderColor: tokens.border.primary,
      borderWidth: 1,
      textStyle: {
        color: tokens.text.primary,
        fontSize: fontSize.sm,
      },
    },
    legend: {
      textStyle: {
        color: tokens.text.secondary,
        fontSize: fontSize.sm,
      },
      bottom: 0,
      itemGap: 16,
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
    },
    xAxis: {
      axisLine: { lineStyle: { color: tokens.text.disabled } },
      axisTick: { lineStyle: { color: tokens.text.disabled } },
      axisLabel: { color: tokens.text.tertiary, fontSize: fontSize.axis },
      splitLine: { show: false },
    },
    yAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: tokens.text.tertiary, fontSize: fontSize.axis },
      splitLine: {
        lineStyle: {
          color: tokens.border.secondary,
          type: 'dashed' as const,
        },
      },
    },
  };
}
