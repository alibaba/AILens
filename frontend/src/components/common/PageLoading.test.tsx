import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import PageLoading from './PageLoading';

describe('PageLoading', () => {
  it('renders loading spinner', () => {
    const { container } = render(<PageLoading />);

    // 检查Spin组件是否渲染（通过class名检查）
    const spinner = container.querySelector('.ant-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('has correct container styles', () => {
    const { container } = render(<PageLoading />);
    const loadingContainer = container.firstChild as HTMLElement;

    // getComputedStyle is mocked in setup; check inline style attribute directly
    const style = loadingContainer.getAttribute('style') ?? '';
    expect(style).toContain('display: flex');
    expect(style).toContain('justify-content: center');
    expect(style).toContain('align-items: center');
    expect(style).toContain('height: 50vh');
  });
});
