import apiClient from './client';
import type { ProjectsResponse } from '../types';

export async function fetchProjects(): Promise<ProjectsResponse> {
  const response = await apiClient.get('/projects/');
  return response.data;
}
