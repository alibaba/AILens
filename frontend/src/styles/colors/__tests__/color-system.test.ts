import { describe, it, expect } from 'vitest';
import { palette, tokens, generateCSSVariables } from '../index';

describe('统一颜色配置系统', () => {
  describe('基础色系(palette)', () => {
    it('应该包含完整的蓝色系', () => {
      expect(palette.blue).toBeDefined();
      expect(palette.blue[50]).toBe('#EFF6FF');
      expect(palette.blue[500]).toBe('#3B82F6');
      expect(palette.blue[900]).toBe('#1E3A8A');
    });

    it('应该包含完整的灰色系', () => {
      expect(palette.gray).toBeDefined();
      expect(palette.gray[50]).toBe('#F9FAFB');
      expect(palette.gray[500]).toBe('#6B7280');
      expect(palette.gray[900]).toBe('#111827');
    });

    it('应该包含完整的红色系', () => {
      expect(palette.red).toBeDefined();
      expect(palette.red[50]).toBe('#FEF2F2');
      expect(palette.red[500]).toBe('#EF4444');
      expect(palette.red[900]).toBe('#7F1D1D');
    });

    it('应该包含完整的绿色系', () => {
      expect(palette.green).toBeDefined();
      expect(palette.green[50]).toBe('#F0FDF4');
      expect(palette.green[500]).toBe('#22C55E');
      expect(palette.green[900]).toBe('#14532D');
    });

    it('应该包含完整的黄色系', () => {
      expect(palette.yellow).toBeDefined();
      expect(palette.yellow[50]).toBe('#FEFCE8');
      expect(palette.yellow[500]).toBe('#F59E0B');
      expect(palette.yellow[900]).toBe('#78350F');
    });
  });

  describe('语义颜色token', () => {
    it('应该定义主要语义颜色', () => {
      expect(tokens.primary).toBe(palette.yellow[400]);
      expect(tokens.success).toBe(palette.green[500]);
      expect(tokens.error).toBe(palette.red[500]);
      expect(tokens.warning).toBe(palette.yellow[500]);
      expect(tokens.info).toBe(palette.blue[500]);
    });

    it('应该定义背景色系', () => {
      expect(tokens.background.page).toBe(palette.gray[900]);
      expect(tokens.background.panel).toBe('#232436');
      expect(tokens.background.hover).toBe('#2C2D42');
      expect(tokens.background.input).toBe('#191A2C');
      expect(tokens.background.sidebar).toBe('#16172A');
    });

    it('应该定义文字颜色', () => {
      expect(tokens.text.primary).toBe(palette.gray[200]);
      expect(tokens.text.secondary).toBe(palette.gray[400]);
      expect(tokens.text.tertiary).toBe(palette.gray[500]);
      expect(tokens.text.disabled).toBe(palette.gray[600]);
    });

    it('应该定义边框颜色', () => {
      expect(tokens.border.primary).toBe(palette.gray[600]);
      expect(tokens.border.secondary).toBe('#2D2E40');
    });
  });

  describe('CSS变量生成', () => {
    it('应该生成完整的CSS变量字符串', () => {
      const cssVariables = generateCSSVariables();

      expect(cssVariables).toContain('--color-primary: #FACC15;');
      expect(cssVariables).toContain('--color-success: #22C55E;');
      expect(cssVariables).toContain('--color-error: #EF4444;');
      expect(cssVariables).toContain('--color-background-page: #111827;');
      expect(cssVariables).toContain('--color-text-primary: #E5E7EB;');
      expect(cssVariables).toContain('--color-border-primary: #4B5563;');
    });

    it('生成的CSS变量应该格式正确', () => {
      const cssVariables = generateCSSVariables();

      // 检查CSS变量格式
      const lines = cssVariables.split('\n').filter(line => line.trim());
      lines.forEach(line => {
        if (line.includes('--color-')) {
          expect(line).toMatch(/^\s*--color-[\w-]+:\s*#[0-9A-Fa-f]{6};\s*$/);
        }
      });
    });
  });

  describe('TypeScript类型支持', () => {
    it('palette应该有正确的类型', () => {
      // 这些在TypeScript编译时会检查类型
      const blue50: string = palette.blue[50];
      const gray500: string = palette.gray[500];
      expect(typeof blue50).toBe('string');
      expect(typeof gray500).toBe('string');
    });

    it('tokens应该有正确的类型', () => {
      const primary: string = tokens.primary;
      const bgPage: string = tokens.background.page;
      expect(typeof primary).toBe('string');
      expect(typeof bgPage).toBe('string');
    });
  });
});
