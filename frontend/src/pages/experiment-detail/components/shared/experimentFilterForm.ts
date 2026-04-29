export type ExperimentFilterFormValues = Record<string, unknown>;

export interface ExperimentQueryFilters {
  splitBy: string;
  scaffoldFilter: string | undefined;
  languageFilter: string | undefined;
  toolSchemaFilter: string | undefined;
}

export function toExperimentQueryFilters(
  v: ExperimentFilterFormValues | undefined
): ExperimentQueryFilters {
  const splitByRaw = v?.splitBy;
  const splitBy =
    splitByRaw !== undefined && splitByRaw !== null && splitByRaw !== ''
      ? String(splitByRaw)
      : 'none';

  const sf = v?.scaffoldFilter;
  const lf = v?.languageFilter;
  const tf = v?.toolSchemaFilter;

  return {
    splitBy,
    scaffoldFilter: sf === undefined || sf === null || sf === 'all' ? undefined : String(sf),
    languageFilter: lf === undefined || lf === null || lf === 'all' ? undefined : String(lf),
    toolSchemaFilter: tf === undefined || tf === null || tf === 'all' ? undefined : String(tf),
  };
}
