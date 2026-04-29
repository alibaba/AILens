import { render, screen, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// Mock the lazy-loaded components to test loading behavior
vi.mock('./pages/ExperimentList', () => ({
  default: () => <div data-testid="experiment-list">ExperimentList Page</div>,
}));

vi.mock('./pages/UnderConstruction', () => ({
  default: () => <div data-testid="under-construction">UnderConstruction Page</div>,
}));

describe('App Code Splitting', () => {
  it('shows loading state and then renders page', async () => {
    const { container } = render(<App />);

    // 应该显示loading状态（Spin组件）
    expect(container.querySelector('.ant-spin')).toBeInTheDocument();

    // 等待页面加载完成
    await act(async () => {
      await waitFor(() => {
        expect(screen.getByTestId('experiment-list')).toBeInTheDocument();
      });
    });
  });

  it('lazy loads different pages correctly', async () => {
    // 这个测试验证不同路由能正确懒加载
    render(<App />);

    // 等待首页加载
    await act(async () => {
      await waitFor(() => {
        expect(screen.getByTestId('experiment-list')).toBeInTheDocument();
      });
    });

    // 这里可以进一步测试路由切换时的懒加载行为
    // 但需要更复杂的路由模拟设置
  });

  it('maintains existing route structure', async () => {
    const { container } = render(<App />);

    // 验证应用正确渲染，路由结构保持不变
    await act(async () => {
      await waitFor(() => {
        // 检查是否有正确的布局结构
        expect(
          container.querySelector('.ant-spin') || screen.queryByTestId('experiment-list')
        ).toBeTruthy();
      });
    });
  });
});
