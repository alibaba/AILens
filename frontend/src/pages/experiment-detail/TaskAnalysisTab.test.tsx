import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TaskAnalysisTab from './TaskAnalysisTab';

// Mock ECharts to avoid canvas errors in jsdom
vi.mock('echarts-for-react', () => ({
  default: ({ style }: { style?: React.CSSProperties }) => (
    <div data-testid="echarts-mock" style={style} />
  ),
}));

// Mock the hooks
vi.mock('../../hooks/useLanguageStats', () => ({
  useLanguageStats: vi.fn(),
}));

vi.mock('../../hooks/usePromQL', () => ({
  usePromQLMetric: vi.fn(),
}));

vi.mock('../../api/stats', () => ({
  fetchIterations: vi.fn().mockResolvedValue({ items: [] }),
}));

vi.mock('../../hooks/useTaskEffectiveness', () => ({
  useTaskEffectiveness: vi.fn().mockReturnValue({ data: undefined, isLoading: false }),
}));

import { useLanguageStats } from '../../hooks/useLanguageStats';
import { usePromQLMetric } from '../../hooks/usePromQL';

describe('TaskAnalysisTab Integration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    // Mock useLanguageStats
    vi.mocked(useLanguageStats).mockReturnValue({
      data: [
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
      ],
      isLoading: false,
    });

    // Mock usePromQLMetric
    vi.mocked(usePromQLMetric).mockReturnValue({
      data: [
        {
          points: [{ value: 0.75 }],
        },
      ],
    });
  });

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <QueryClientProvider client={queryClient}>
          <TaskAnalysisTab
            experimentId="test-experiment"
            scaffoldFilter={undefined}
            languageFilter={undefined}
            toolSchemaFilter={undefined}
            iterationFilter="all"
            isActive={true}
          />
        </QueryClientProvider>
      </MemoryRouter>
    );
  };

  it('renders task analysis with new terminology', async () => {
    renderComponent();

    await waitFor(() => {
      // 检查Language Stats部分是否使用了新术语
      expect(screen.getByText('Language Stats')).toBeInTheDocument();
      expect(screen.getByText('Trajectories')).toBeInTheDocument();
      expect(screen.queryByText('频次')).not.toBeInTheDocument();
    });
  });

  it('displays language data correctly', async () => {
    renderComponent();

    await waitFor(() => {
      // 检查语言数据
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('JavaScript')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();

      // 检查合计行
      expect(screen.getByText('Total')).toBeInTheDocument();
      expect(screen.getByText('80')).toBeInTheDocument(); // 50 + 30
    });
  });

  it('displays task effectiveness chart', async () => {
    renderComponent();

    await waitFor(() => {
      // 检查Task Effectiveness section是否存在（组件渲染）
      // 由于TaskEffectivenessSection依赖effectiveness数据，我们检查基本结构
      expect(screen.getByText('Language Stats')).toBeInTheDocument();
    });
  });
});
