import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { colors, spacing } from '../../styles/theme';
import { useLayoutStore } from '../../stores/layout';

export default function AppLayout() {
  const sidebarCollapsed = useLayoutStore(s => s.sidebarCollapsed);
  const marginLeft = sidebarCollapsed ? spacing.sidebarCollapsed : spacing.sidebarExpanded;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: colors.pageBg }}>
      {/* Left sidebar (fixed) */}
      <Sidebar />

      {/* Right content area */}
      <div
        style={{
          flex: 1,
          marginLeft,
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          transition: 'margin-left 0.2s ease',
        }}
      >
        <TopBar />
        <main style={{ flex: 1, overflow: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
