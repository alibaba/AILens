import { Component, type ReactNode } from 'react';
import { Result, Button, ConfigProvider, theme } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { getAntdThemeConfig } from '../../styles/colors';
import styles from './index.module.css';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: Record<string, unknown> | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // 更新 state 使下一次渲染能够显示降级后的 UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: Record<string, unknown>) {
    // 捕获错误详情
    this.setState({
      error,
      errorInfo,
    });

    // 错误日志记录
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // 生产环境可以在这里添加错误上报
    if (import.meta.env.PROD) {
      // 这里可以集成错误监控服务
      // 例如: Sentry, LogRocket, 或自定义错误上报
      this.reportError(error, errorInfo);
    }
  }

  private reportError = (error: Error, errorInfo: Record<string, unknown>) => {
    // 错误上报逻辑
    try {
      // 可以发送到错误监控服务
      const errorData = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      };

      console.warn('Error reported:', errorData);
      // 实际项目中可以发送到监控API
      // fetch('/api/errors', { method: 'POST', body: JSON.stringify(errorData) });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  private handleReload = () => {
    // 重新加载页面
    window.location.reload();
  };

  private handleReset = () => {
    // 重置错误状态，尝试恢复
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      const isDev = import.meta.env.DEV;

      return (
        <ConfigProvider
          theme={{
            algorithm: theme.darkAlgorithm,
            ...getAntdThemeConfig(),
          }}
        >
          <div className={styles.container}>
            <Result
              status="500"
              title={<span className={styles.title}>page error</span>}
              subTitle={
                <span className={styles.subtitle}>
                  {isDev && this.state.error
                    ? `Development environment error message: ${this.state.error.message}`
                    : 'We apologize for the technical issue encountered on the page. Please try refreshing the page.'}
                </span>
              }
              extra={[
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={this.handleReload}
                  key="reload"
                  size="large"
                >
                  reload
                </Button>,
                <Button
                  onClick={this.handleReset}
                  key="reset"
                  size="large"
                  className={styles.secondaryButton}
                >
                  reset
                </Button>,
              ]}
            />

            {/* 开发环境显示详细错误信息 */}
            {isDev && this.state.error && (
              <details className={styles.debugDetails}>
                <summary className={styles.debugSummary}>
                  🐛 Development and Debugging Information (Click to Expand)
                </summary>
                <div className={styles.debugContent}>
                  <div className={styles.errorSection}>
                    <div className={styles.errorLabel}>Error message:</div>
                    <div className={styles.errorMessage}>{this.state.error.message}</div>
                  </div>

                  <div className={styles.errorSection}>
                    <div className={styles.errorLabel}>Error Stack:</div>
                    <div className={styles.errorStack}>{this.state.error.stack}</div>
                  </div>

                  {this.state.errorInfo?.componentStack && (
                    <div>
                      <div className={styles.errorLabel}>Component Stack:</div>
                      <div className={styles.componentStack}>
                        {String(this.state.errorInfo.componentStack)}
                      </div>
                    </div>
                  )}
                </div>
              </details>
            )}
          </div>
        </ConfigProvider>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
