import apiClient from './client';
import type { ExperimentsResponse, ExperimentItem } from '../types';

// ── Fetch functions ──

export async function fetchExperiments(projectId: string): Promise<ExperimentsResponse> {
  const response = await apiClient.get('/experiments/', {
    params: { project_id: projectId },
  });
  return response.data;
}

export async function fetchExperiment(id: string): Promise<ExperimentItem> {
  const response = await apiClient.get(`/experiments/${id}`);
  return response.data;
}
