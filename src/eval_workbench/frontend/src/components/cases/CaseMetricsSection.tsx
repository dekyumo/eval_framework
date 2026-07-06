import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { FormLabel } from '../ui/Typography';
import type { MetricRow } from './types';

interface CaseMetricsSectionProps {
  metrics: MetricRow[];
  rubrics: { id: string; name: string; items?: { type: string }[] }[];
  extractors: { id: string; name: string }[];
  onChange: (metrics: MetricRow[]) => void;
}

export function CaseMetricsSection({
  metrics,
  rubrics,
  extractors,
  onChange,
}: CaseMetricsSectionProps) {
  const updateMetric = (index: number, patch: Partial<MetricRow>) => {
    const next = [...metrics];
    next[index] = { ...next[index], ...patch };
    onChange(next);
  };

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-md p-4 space-y-4">
      {metrics.map((metric, index) => (
        <div key={metric.id} className="flex gap-3 items-end" data-testid="metric-row">
          <div className="flex-1">
            <FormLabel>Name</FormLabel>
            <input
              className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-sm text-on-surface focus:outline-none focus:border-primary-fixed"
              value={metric.name}
              onChange={e => updateMetric(index, { name: e.target.value })}
            />
          </div>
          <div className="flex-1">
            <FormLabel>Strategy</FormLabel>
            <Select
              value={metric.strategy}
              onChange={e => updateMetric(index, { strategy: e.target.value })}
            >
              <option value="rubric">Rubric (LLM as Judge)</option>
              <option value="deterministic">Deterministic (Extractor)</option>
            </Select>
          </div>
          {metric.strategy === 'rubric' ? (
            <div className="flex-[2]">
              <FormLabel>Rubric</FormLabel>
              <Select
                value={metric.rubric_ref}
                onChange={e => updateMetric(index, { rubric_ref: e.target.value })}
              >
                <option value="">Select Rubric...</option>
                {rubrics.map(r => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </Select>
            </div>
          ) : (
            <>
              <div className="flex-1">
                <FormLabel>Extractor</FormLabel>
                <Select
                  value={metric.extractor_ref || ''}
                  onChange={e => updateMetric(index, { extractor_ref: e.target.value })}
                >
                  <option value="">Select Extractor...</option>
                  {extractors.map(ex => (
                    <option key={ex.id} value={ex.id}>{ex.name}</option>
                  ))}
                </Select>
              </div>
              <div className="flex-1">
                <FormLabel>Ground Truth</FormLabel>
                <input
                  className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-sm text-on-surface focus:outline-none focus:border-primary-fixed"
                  value={metric.ground_truth || ''}
                  placeholder="e.g. $100 or true"
                  onChange={e => updateMetric(index, { ground_truth: e.target.value })}
                />
              </div>
            </>
          )}
          <Button
            variant="destructive"
            size="sm"
            className="h-10 px-2.5 font-bold"
            onClick={() => onChange(metrics.filter((_, i) => i !== index))}
          >
            ×
          </Button>
        </div>
      ))}
      <Button
        variant="ghost"
        size="sm"
        className="text-primary-fixed font-bold"
        onClick={() =>
          onChange([
            ...metrics,
            {
              id: `m_${crypto.randomUUID().substring(0, 8)}`,
              name: 'new_metric',
              strategy: 'rubric',
              result_type: 'bool',
              rubric_ref: '',
              extractor_ref: '',
              ground_truth: '',
            },
          ])
        }
      >
        + Add Metric
      </Button>
    </div>
  );
}
