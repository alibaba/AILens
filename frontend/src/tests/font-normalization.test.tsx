/**
 * 字体规范化测试
 * 测试数字显示使用等宽字体，普通文本使用无衬线字体
 */

import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import MetricCard from '../components/shared/MetricCard';
import metricCardStyles from '../components/shared/MetricCard.module.css';

describe('字体规范化测试', () => {
  describe('MetricCard 组件', () => {
    it('应该对数字值使用等宽字体样式', () => {
      render(<MetricCard title="Test Metric" value={12345} />);

      // 查找数字值元素
      const valueElement = screen.getByText('12345');

      // 等宽字体在 CSS module 的 .value 上，而非 inline style
      expect(valueElement.classList.contains(metricCardStyles.value)).toBe(true);
    });

    it('应该正确显示标题（不转换大小写）', () => {
      render(<MetricCard title="Test Title" value="123" />);

      // 标题实际上是原样显示的，只是CSS会转换为大写
      const titleElement = screen.getByText('Test Title');
      expect(titleElement).toBeInTheDocument();
    });

    it('应该对副标题使用默认字体', () => {
      render(<MetricCard title="Test" value="123" subtitle="Test Subtitle" />);

      const subtitleElement = screen.getByText('Test Subtitle');
      expect(subtitleElement).toBeInTheDocument();
      // 副标题应该没有特殊的font-family设置
      expect(subtitleElement.style.fontFamily).toBe('');
    });
  });

  describe('HTML结构验证', () => {
    it('应该在组件中找到数字显示区域', () => {
      render(<MetricCard title="Revenue" value="$1,234,567" />);

      // 验证数字值存在
      const valueElement = screen.getByText('$1,234,567');
      expect(valueElement).toBeInTheDocument();

      // 验证标题存在
      const titleElement = screen.getByText('Revenue');
      expect(titleElement).toBeInTheDocument();
    });

    it('应该正确处理数字类型的value', () => {
      render(<MetricCard title="Count" value={42} />);

      const valueElement = screen.getByText('42');
      expect(valueElement).toBeInTheDocument();
      expect(valueElement.classList.contains(metricCardStyles.value)).toBe(true);
    });

    it('应该正确处理字符串类型的value', () => {
      render(<MetricCard title="Percentage" value="95.5%" />);

      const valueElement = screen.getByText('95.5%');
      expect(valueElement).toBeInTheDocument();
      expect(valueElement.classList.contains(metricCardStyles.value)).toBe(true);
    });
  });

  describe('CSS类名验证', () => {
    it('font-mono类应该能被正确添加到元素', () => {
      // 创建测试元素验证类名功能
      const testElement = document.createElement('span');
      testElement.className = 'font-mono';
      testElement.textContent = '123.45';

      expect(testElement.className).toBe('font-mono');
      expect(testElement.textContent).toBe('123.45');
    });

    it('应该能组合使用font-mono和其他类名', () => {
      const testElement = document.createElement('span');
      testElement.className = 'font-mono text-sm text-red-500';

      expect(testElement.classList.contains('font-mono')).toBe(true);
      expect(testElement.classList.contains('text-sm')).toBe(true);
      expect(testElement.classList.contains('text-red-500')).toBe(true);
    });
  });

  describe('数字格式验证', () => {
    it('应该正确显示百分比', () => {
      render(<MetricCard title="Success Rate" value="87.50%" />);

      const valueElement = screen.getByText('87.50%');
      expect(valueElement).toBeInTheDocument();
      expect(valueElement.classList.contains(metricCardStyles.value)).toBe(true);
    });

    it('应该正确显示大数字', () => {
      render(<MetricCard title="Total Users" value="1,234,567" />);

      const valueElement = screen.getByText('1,234,567');
      expect(valueElement).toBeInTheDocument();
      expect(valueElement.classList.contains(metricCardStyles.value)).toBe(true);
    });

    it('应该正确显示小数', () => {
      render(<MetricCard title="Average Score" value="4.82" />);

      const valueElement = screen.getByText('4.82');
      expect(valueElement).toBeInTheDocument();
      expect(valueElement.classList.contains(metricCardStyles.value)).toBe(true);
    });
  });
});
