import { create } from 'zustand';
import type { Project } from '../types';
import { fetchProjects } from '../api/projects';

interface ProjectState {
  projects: Project[];
  currentProjectId: string | null;
  loading: boolean;
  error: string | null;

  /** Load project list from API and auto-select the first one if no selection */
  loadProjects: () => Promise<void>;

  /** Switch to a different project by ID */
  setProject: (projectId: string) => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProjectId: null,
  loading: false,
  error: null,

  loadProjects: async () => {
    set({ loading: true, error: null });
    try {
      const data = await fetchProjects();
      const projects = data.items ?? [];
      const current = get().currentProjectId;
      // Keep current if it's still valid, otherwise pick the first
      const validCurrent = current && projects.some(p => p.id === current);
      set({
        projects,
        currentProjectId: validCurrent ? current : (projects[0]?.id ?? null),
        loading: false,
      });
    } catch (err) {
      set({ error: String(err), loading: false });
    }
  },

  setProject: (projectId: string) => {
    set({ currentProjectId: projectId });
  },
}));
