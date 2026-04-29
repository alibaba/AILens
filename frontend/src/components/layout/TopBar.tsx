import { useLocation, Link } from 'react-router-dom';
import { Tag } from 'antd';
import ProjectSelector from './ProjectSelector';
import { useExperimentStore } from '../../stores/experiment';
import styles from './TopBar.module.css';

/** Map path segments to human-readable labels */
const segmentLabels: Record<string, string> = {
  experiments: 'Experiments',
  datasets: 'Datasets',
  tasks: 'Tasks',
  trajectories: 'Trajectories',
  traces: 'Traces',
  monitor: 'Monitor',
  alerts: 'Alerts',
};

interface Crumb {
  label: string;
  path: string;
}

function useBreadcrumbs(): Crumb[] {
  const location = useLocation();
  const parts = location.pathname.split('/').filter(Boolean);

  const crumbs: Crumb[] = [];

  let currentPath = '';
  for (const part of parts) {
    currentPath += `/${part}`;
    const label = segmentLabels[part] ?? part;
    crumbs.push({ label, path: currentPath });
  }

  return crumbs;
}

export default function TopBar() {
  const crumbs = useBreadcrumbs();
  const currentExperiment = useExperimentStore(s => s.currentExperiment);

  // Detect if we're on an experiment detail page
  const location = useLocation();
  const isExperimentDetail = /^\/experiments\/[^/]+/.test(location.pathname);
  const isTasksPage = location.pathname.startsWith('/tasks');
  const isTrajectoriesPage = location.pathname === '/trajectories';
  const isExperimentTasks = /^\/experiments\/([^/]+)\/tasks$/.exec(location.pathname);
  const isExperimentTrajectories = /^\/experiments\/([^/]+)\/trajectories$/.exec(location.pathname);
  const isTaskTrajectories = /^\/tasks\/([^/]+)\/trajectories$/.exec(location.pathname);
  const isDatasetTasks = /^\/datasets\/([^/]+)\/tasks$/.exec(location.pathname);
  const isDatasetTrajectories = /^\/datasets\/([^/]+)\/trajectories$/.exec(location.pathname);
  const searchParams = new URLSearchParams(location.search);
  const trajectoryExperimentId =
    searchParams.get('experiment') ||
    (isExperimentTrajectories ? isExperimentTrajectories[1] : null);
  const trajectoryTaskId =
    searchParams.get('task_id') ||
    searchParams.get('task') ||
    (isTaskTrajectories ? isTaskTrajectories[1] : null);

  return (
    <header className={styles.header}>
      {/* Left: Breadcrumbs + Experiment Info */}
      <div className={styles.left}>
        {/* Breadcrumbs */}
        {isDatasetTrajectories ? (
          <nav className={styles.crumbNav}>
            <Link to="/datasets" className={styles.crumbLink}>
              Datasets
            </Link>
            <span className={styles.crumbSep}> › </span>
            <Link to={`/datasets/${isDatasetTrajectories[1]}/tasks`} className={styles.crumbLink}>
              {decodeURIComponent(isDatasetTrajectories[1])}
            </Link>
            <span className={styles.crumbSep}> › </span>
            <span className={styles.crumbCurrent}>Trajectory Explorer</span>
          </nav>
        ) : isDatasetTasks ? (
          <nav className={styles.crumbNav}>
            <Link to="/datasets" className={styles.crumbLink}>
              Datasets
            </Link>
            <span className={styles.crumbSep}> › </span>
            <Link to={`/datasets/${isDatasetTasks[1]}/tasks`} className={styles.crumbLink}>
              {decodeURIComponent(isDatasetTasks[1])}
            </Link>
            <span className={styles.crumbSep}> › </span>
            <span className={styles.crumbCurrent}>Task Explorer</span>
          </nav>
        ) : (isTrajectoriesPage || isTaskTrajectories) && trajectoryTaskId ? (
          <nav className={styles.crumbNav}>
            <Link to="/tasks" className={styles.crumbLink}>
              Tasks
            </Link>
            <span className={styles.crumbSep}> › </span>
            <Link to={`/tasks/${trajectoryTaskId}`} className={styles.crumbLink}>
              {trajectoryTaskId}
            </Link>
            <span className={styles.crumbSep}> › </span>
            <span className={styles.crumbCurrent}>Trajectory Explorer</span>
          </nav>
        ) : isExperimentTasks ? (
          <nav className={styles.crumbNav}>
            <Link to="/experiments" className={styles.crumbLink}>
              Experiments
            </Link>
            <span className={styles.crumbSep}> › </span>
            <Link to={`/experiments/${isExperimentTasks[1]}`} className={styles.crumbLink}>
              {isExperimentTasks[1]}
            </Link>
            <span className={styles.crumbSep}> › </span>
            <span className={styles.crumbCurrent}>Task Explorer</span>
          </nav>
        ) : (isTrajectoriesPage || isExperimentTrajectories) && trajectoryExperimentId ? (
          <nav className={styles.crumbNav}>
            <Link to="/experiments" className={styles.crumbLink}>
              Experiments
            </Link>
            <span className={styles.crumbSep}> › </span>
            <Link to={`/experiments/${trajectoryExperimentId}`} className={styles.crumbLink}>
              {trajectoryExperimentId}
            </Link>
            <span className={styles.crumbSep}> › </span>
            <span className={styles.crumbCurrent}>Trajectory Explorer</span>
          </nav>
        ) : (
          <nav className={styles.crumbNav}>
            {crumbs.map((crumb, i) => {
              const isLast = i === crumbs.length - 1;
              // On experiment detail, skip the ID crumb (last one)
              if (isExperimentDetail && isLast) return null;
              return (
                <span key={crumb.path} className={styles.crumbSegment}>
                  {i > 0 && <span className={styles.crumbSep}> › </span>}
                  {isLast ? (
                    <span className={styles.crumbCurrent}>{crumb.label}</span>
                  ) : (
                    <Link to={crumb.path} className={styles.crumbLink}>
                      {crumb.label}
                    </Link>
                  )}
                </span>
              );
            })}
          </nav>
        )}

        {/* Experiment info inline (only on experiment detail page) */}
        {isExperimentDetail && currentExperiment && (
          <>
            <span className={styles.crumbSep}> › </span>
            <span className={styles.experimentName}>{currentExperiment.name}</span>
            <span className={styles.experimentMeta}>
              Scaffolds:{' '}
              {currentExperiment.scaffolds.map(s => (
                <Tag key={s} className={styles.tagScaffold}>
                  {s}
                </Tag>
              ))}
            </span>
            <span className={styles.experimentMeta}>
              Model: <Tag>{currentExperiment.model}</Tag>
            </span>
          </>
        )}
      </div>

      {/* Right: Project Selector (hidden on Tasks pages) */}
      {!(isTasksPage || isTaskTrajectories) && <ProjectSelector />}
    </header>
  );
}
