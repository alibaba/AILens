// Shared types for experiment detail page

import type { TimeSeries } from '../../types';

export interface ChartLine {
  name: string;
  data: (number | null)[];
  color: string;
  yAxisIndex?: number;
  areaOpacity?: number;
  stdData?: number[];
  dashed?: boolean;
}

export interface PieChartData {
  name: string;
  value: number;
  color: string;
}

export type { TimeSeries };
