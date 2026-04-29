import { useEffect, useState } from 'react';
import { Select, Tooltip } from 'antd';
import { useProjectStore } from '../../stores/project';
import { colors } from '../../styles/theme';

export default function ProjectSelector() {
  const { projects, currentProjectId, loading, loadProjects, setProject } = useProjectStore();
  const [hovered, setHovered] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    void loadProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Tooltip title="Switch projects" mouseEnterDelay={0} open={hovered && !dropdownOpen}>
      <div onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}>
        <Select
          value={currentProjectId ?? undefined}
          onChange={setProject}
          loading={loading}
          placeholder="Select Project"
          variant="borderless"
          style={{ minWidth: 160, color: colors.textPrimary }}
          popupMatchSelectWidth={false}
          title=""
          onOpenChange={setDropdownOpen}
          options={projects.map(p => ({
            value: p.id,
            label: p.name,
          }))}
        />
      </div>
    </Tooltip>
  );
}
