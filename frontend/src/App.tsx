import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, theme } from 'antd';
import { Suspense, lazy } from 'react';
import AppLayout from './components/layout/AppLayout';
import PageLoading from './components/common/PageLoading';
import ErrorBoundary from './components/ErrorBoundary';
import { getAntdThemeConfig } from './styles/colors';

// 懒加载页面组件 - 代码分割优化
const ExperimentList = lazy(() => import('./pages/ExperimentList'));
const ExperimentDetail = lazy(() => import('./pages/ExperimentDetail'));
const TaskLibrary = lazy(() => import('./pages/TaskLibrary'));
const TaskDetail = lazy(() => import('./pages/TaskDetail'));
const PassRateDiff = lazy(() => import('./pages/PassRateDiff'));
const TaskExplorer = lazy(() => import('./pages/TaskExplorer'));
const TrajectoryExplorer = lazy(() => import('./pages/TrajectoryExplorer'));
const TrajectoryViewer = lazy(() => import('./pages/TrajectoryViewer'));
const DatasetList = lazy(() => import('./pages/DatasetList'));
const TraceSearch = lazy(() => import('./pages/TraceSearch'));
const TraceViewer = lazy(() => import('./pages/TraceViewer'));
const ServiceMonitor = lazy(() => import('./pages/ServiceMonitor'));
const AlertManagement = lazy(() => import('./pages/AlertManagement'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
});

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider
          theme={{
            algorithm: theme.darkAlgorithm,
            ...getAntdThemeConfig(),
          }}
        >
          <BrowserRouter>
            <Suspense fallback={<PageLoading />}>
              <Routes>
                <Route element={<AppLayout />}>
                  <Route path="/" element={<Navigate to="/experiments" replace />} />
                  <Route path="/experiments" element={<ExperimentList />} />
                  <Route path="/tasks" element={<TaskLibrary />} />
                  <Route path="/tasks/:taskId" element={<TaskDetail />} />
                  <Route path="/experiments/:id/pass-rate-diff" element={<PassRateDiff />} />
                  <Route path="/experiments/:id/:tabKey" element={<ExperimentDetail />} />
                  <Route path="/experiments/:id" element={<ExperimentDetail />} />
                  <Route path="/datasets" element={<DatasetList />} />
                  <Route path="/datasets/:id/tasks" element={<TaskExplorer />} />
                  <Route path="/datasets/:id/trajectories" element={<TrajectoryExplorer />} />
                  <Route path="/trajectories" element={<TrajectoryExplorer />} />
                  <Route path="/experiments/:id/tasks" element={<TaskExplorer />} />
                  <Route path="/experiments/:id/trajectories" element={<TrajectoryExplorer />} />
                  <Route path="/tasks/:taskId/trajectories" element={<TrajectoryExplorer />} />
                  <Route path="/trajectories/:id" element={<TrajectoryViewer />} />
                  <Route path="/traces" element={<TraceSearch />} />
                  <Route path="/traces/:traceId" element={<TraceViewer />} />
                  <Route path="/monitor" element={<ServiceMonitor />} />
                  <Route path="/alerts" element={<AlertManagement />} />
                </Route>
              </Routes>
            </Suspense>
          </BrowserRouter>
        </ConfigProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
