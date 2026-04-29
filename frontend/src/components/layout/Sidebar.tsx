import { useNavigate, useLocation } from 'react-router-dom';
import {
  DatabaseOutlined,
  ExperimentOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { colors, fontSize, spacing } from '../../styles/theme';
import { useLayoutStore } from '../../stores/layout';

interface MenuItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  path: string;
}

interface MenuGroup {
  title: string;
  items: MenuItem[];
}

const menuGroups: MenuGroup[] = [
  {
    title: 'TRAINING',
    items: [
      {
        key: 'experiments',
        label: 'Experiments',
        icon: <ExperimentOutlined />,
        path: '/experiments',
      },
      {
        key: 'datasets',
        label: 'Datasets',
        icon: <DatabaseOutlined />,
        path: '/datasets',
      },
    ],
  },
  // {
  //   title: 'SERVING',
  //   items: [
  //     {
  //       key: 'monitor',
  //       label: 'Monitor',
  //       icon: <DashboardOutlined />,
  //       path: '/monitor',
  //     },
  //   ],
  // },
  // {
  //   title: 'DEBUGGING',
  //   items: [
  //     {
  //       key: 'traces',
  //       label: 'Traces',
  //       icon: <ApartmentOutlined />,
  //       path: '/traces',
  //     },
  //   ],
  // },
  // {
  //   title: 'SYSTEM',
  //   items: [
  //     {
  //       key: 'alerts',
  //       label: 'Alerts',
  //       icon: <AlertOutlined />,
  //       path: '/alerts',
  //     },
  //   ],
  // },
];

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useLayoutStore();
  const navigate = useNavigate();
  const location = useLocation();

  const collapsed = sidebarCollapsed;
  const width = collapsed ? spacing.sidebarCollapsed : spacing.sidebarExpanded;

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <aside
      style={{
        width,
        minWidth: width,
        height: '100vh',
        backgroundColor: colors.sidebarBg,
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s ease, min-width 0.2s ease',
        overflow: 'hidden',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Logo area */}
      <div
        style={{
          height: spacing.topBarHeight,
          display: 'flex',
          alignItems: 'center',
          padding: collapsed ? '0 16px' : '0 20px',
          borderBottom: `1px solid ${colors.borderSecondary}`,
        }}
      >
        <span
          style={{
            fontSize: fontSize.lg,
            fontWeight: 700,
            color: colors.brand,
            whiteSpace: 'nowrap',
          }}
        >
          {collapsed ? 'AI' : 'AILens'}
        </span>
      </div>

      {/* Menu groups */}
      <nav style={{ flex: 1, padding: '12px 0', overflowY: 'auto' }}>
        {menuGroups.map(group => (
          <div key={group.title} style={{ marginBottom: 16 }}>
            {/* Group title */}
            {!collapsed && (
              <div
                style={{
                  fontSize: fontSize.axis,
                  fontWeight: 600,
                  color: colors.textDisabled,
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                  padding: '4px 20px 6px',
                }}
              >
                {group.title}
              </div>
            )}

            {/* Menu items */}
            {group.items.map(item => {
              const active = isActive(item.path);
              return (
                <div
                  key={item.key}
                  onClick={() => navigate(item.path)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => {
                    if (e.key === 'Enter' || e.key === ' ') navigate(item.path);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: collapsed ? '10px 0' : '10px 20px',
                    justifyContent: collapsed ? 'center' : 'flex-start',
                    cursor: 'pointer',
                    color: active ? colors.brand : colors.textTertiary,
                    fontSize: fontSize.bodyCompact,
                    fontWeight: active ? 600 : 400,
                    position: 'relative',
                    transition: 'color 0.15s, background-color 0.15s',
                    borderLeft: active ? `3px solid ${colors.brand}` : '3px solid transparent',
                    backgroundColor: active ? 'rgba(250, 204, 21, 0.05)' : 'transparent',
                  }}
                  onMouseEnter={e => {
                    if (!active) {
                      e.currentTarget.style.color = colors.textSecondary;
                      e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.03)';
                    }
                  }}
                  onMouseLeave={e => {
                    if (!active) {
                      e.currentTarget.style.color = colors.textTertiary;
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <span style={{ fontSize: fontSize.lg, display: 'flex', alignItems: 'center' }}>
                    {item.icon}
                  </span>
                  {!collapsed && <span style={{ whiteSpace: 'nowrap' }}>{item.label}</span>}
                </div>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div
        style={{
          borderTop: `1px solid ${colors.borderSecondary}`,
          padding: '12px 0',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <button
          onClick={toggleSidebar}
          style={{
            background: 'none',
            border: 'none',
            color: colors.textTertiary,
            cursor: 'pointer',
            fontSize: fontSize.lg,
            padding: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 4,
            transition: 'color 0.15s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.color = colors.textSecondary;
          }}
          onMouseLeave={e => {
            e.currentTarget.style.color = colors.textTertiary;
          }}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        </button>
        {!collapsed && (
          <span style={{ fontSize: fontSize.axis, color: colors.textDisabled, marginLeft: 8 }}>
            v0.1.0
          </span>
        )}
      </div>
    </aside>
  );
}
