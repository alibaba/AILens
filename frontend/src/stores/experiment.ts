import { create } from 'zustand';

export interface ExperimentInfo {
  name: string;
  status: string;
  scaffolds: string[];
  model: string;
}

interface ExperimentStore {
  currentExperiment: ExperimentInfo | null;
  setCurrentExperiment: (info: ExperimentInfo | null) => void;
}

export const useExperimentStore = create<ExperimentStore>(set => ({
  currentExperiment: null,
  setCurrentExperiment: info => set({ currentExperiment: info }),
}));
