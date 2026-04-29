import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import LanguageStatsSection from './LanguageStatsSection';
import type { LanguageStatsItem } from '../../types';

describe('LanguageStatsSection', () => {
  const mockData: LanguageStatsItem[] = [
    {
      language: 'Python',
      count: 50,
      pass_rate: 0.8,
      max_turns_passed: 5,
      avg_turns_passed: 2.5,
      max_duration_passed_ms: 30000,
      avg_duration_passed_ms: 15000,
    },
    {
      language: 'JavaScript',
      count: 30,
      pass_rate: 0.7,
      max_turns_passed: 4,
      avg_turns_passed: 2.0,
      max_duration_passed_ms: 25000,
      avg_duration_passed_ms: 12000,
    },
  ];

  beforeEach(() => {
    // 清理 DOM
    document.body.innerHTML = '';
  });

  it('renders Language Stats table with correct header', () => {
    render(<LanguageStatsSection data={mockData} />);

    // 检查标题
    expect(screen.getByText('Language Stats')).toBeInTheDocument();

    // 检查列标题 - 使用新的术语 "Trajectories"
    expect(screen.getByText('Trajectories')).toBeInTheDocument();
    expect(screen.queryByText('频次')).not.toBeInTheDocument();
  });

  it('renders data rows correctly', () => {
    render(<LanguageStatsSection data={mockData} />);

    // 检查数据行
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
    expect(screen.getByText('50')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
  });

  it('renders summary row at the bottom', () => {
    render(<LanguageStatsSection data={mockData} />);

    // 检查合计行
    const summaryRow = screen.getByText('Total');
    expect(summaryRow).toBeInTheDocument();

    // 合计行应该显示合计数据
    expect(screen.getByText('80')).toBeInTheDocument(); // 50 + 30 = 80
  });

  it('summary row stays at bottom during sorting', () => {
    render(<LanguageStatsSection data={mockData} />);

    // 点击 Trajectories 列进行排序
    const trajectoryHeader = screen.getByText('Trajectories');
    fireEvent.click(trajectoryHeader);

    // 获取表格所有行
    const rows = screen.getAllByRole('row');

    // 最后一行应该是合计行（排除表头）
    const dataRows = rows.slice(1); // 去掉表头
    const lastRow = dataRows[dataRows.length - 1];

    expect(lastRow).toHaveTextContent('Total');
  });

  it('summary row has distinct styling', () => {
    render(<LanguageStatsSection data={mockData} />);

    // LanguageStatsSection uses Table.Summary which renders inside tfoot
    const summaryCell = screen.getByText('Total');
    expect(summaryCell.closest('tfoot')).toBeInTheDocument();
  });

  it('sorting excludes summary row from sort operation', () => {
    render(<LanguageStatsSection data={mockData} />);

    // 点击 Pass Rate 列进行排序（默认降序）
    const passRateHeader = screen.getByText('Pass Rate');
    fireEvent.click(passRateHeader);

    // 获取数据行（不包括表头和合计行）
    const rows = screen.getAllByRole('row');
    const dataRows = rows.slice(1, -1); // 去掉表头和最后的合计行

    // Python (0.8) 应该在 JavaScript (0.7) 之前（降序排列）
    expect(dataRows[0]).toHaveTextContent('Python');
    expect(dataRows[1]).toHaveTextContent('JavaScript');

    // 合计行仍然在最后
    const lastRow = rows[rows.length - 1];
    expect(lastRow).toHaveTextContent('Total');
  });

  it('calculates summary values correctly', () => {
    render(<LanguageStatsSection data={mockData} />);

    // 检查合计行的计算值
    expect(screen.getByText('80')).toBeInTheDocument(); // total count: 50 + 30

    // 加权平均通过率应该约为 0.767 = (0.8*50 + 0.7*30) / 80
    const passRateElements = screen.getAllByText(/76\.25%|76\.3%/);
    expect(passRateElements.length).toBeGreaterThan(0);
  });

  it('handles empty data gracefully', () => {
    render(<LanguageStatsSection data={[]} />);

    // 应该渲染标题但没有数据行
    expect(screen.getByText('Language Stats')).toBeInTheDocument();

    // 不应该有合计行（因为没有数据）
    expect(screen.queryByText('Total')).not.toBeInTheDocument();
  });

  it('displays all required columns', () => {
    render(<LanguageStatsSection data={mockData} />);

    // 检查所有列标题
    expect(screen.getByText('Language')).toBeInTheDocument();
    expect(screen.getByText('Trajectories')).toBeInTheDocument();
    expect(screen.getByText('Pass Rate')).toBeInTheDocument();
    expect(screen.getByText('Max Turns')).toBeInTheDocument();
    expect(screen.getByText('Avg Turns')).toBeInTheDocument();
    expect(screen.getByText('Max Duration')).toBeInTheDocument();
    expect(screen.getByText('Avg Duration')).toBeInTheDocument();
  });
});
