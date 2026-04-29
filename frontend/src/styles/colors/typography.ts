/**
 * 字号 token：与 Ant Design Design Token 阶梯一致（seed fontSize + fontFamily）。
 * 业务代码请使用 `fontSize.xxx`，勿在页面写死 px。
 *
 * 派生档位（axis / micro 等）由 antd 基础字号换算，便于日后只改一处 seed。
 */
import { theme } from 'antd';

/** 与 ConfigProvider `getAntdThemeConfig` 共用 */
export const TYPOGRAPHY_SEED = {
  fontSize: 14,
  fontFamily: '"Inter", "SF Pro Text", -apple-system, "Segoe UI", sans-serif',
} as const;

const t = theme.getDesignToken({ token: { ...TYPOGRAPHY_SEED } });

export const fontSize = {
  /** antd fontSizeSM */
  sm: t.fontSizeSM,
  /** antd fontSize（正文） */
  md: t.fontSize,
  /** antd fontSizeLG */
  lg: t.fontSizeLG,
  /** antd fontSizeXL */
  xl: t.fontSizeXL,
  heading1: t.fontSizeHeading1,
  heading2: t.fontSizeHeading2,
  heading3: t.fontSizeHeading3,
  heading4: t.fontSizeHeading4,
  heading5: t.fontSizeHeading5,
  /** antd fontSizeIcon */
  icon: t.fontSizeIcon,

  /** 图表轴、紧凑标签：SM − 1 */
  axis: t.fontSizeSM - 1,
  /** Tag / 极小号说明：SM − 2 */
  micro: t.fontSizeSM - 2,
  /** 树形折叠箭头等：SM − 3 */
  miniIcon: t.fontSizeSM - 3,
  /** 状态圆点等：SM / 2 */
  dot: Math.floor(t.fontSizeSM / 2),
  /** 次级正文、表格强调：MD − 1 */
  bodyCompact: t.fontSize - 1,
  /** 小标题、卡片标题：(MD + LG) / 2 */
  subtitle: Math.round((t.fontSize + t.fontSizeLG) / 2),
  /** 模块标题、强调：XL − 2 */
  section: t.fontSizeXL - 2,
  /** KPI 数字：Heading3 + 4 */
  metric: t.fontSizeHeading3 + 4,
  /** 空状态主图标：MD × 4 + 8 */
  hero: t.fontSize * 4 + 8,
} as const;

export type FontSizeToken = keyof typeof fontSize;
