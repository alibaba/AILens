import { Spin } from 'antd';
import { colors } from '../../styles/theme';

/**
 * 页面级加载组件，用于React.Suspense的fallback
 * 统一的loading样式，保持与设计系统一致
 */
export default function PageLoading() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '50vh',
        backgroundColor: colors.pageBg,
      }}
    >
      <Spin size="large" />
    </div>
  );
}
