import { useState, useEffect } from 'react';
import { TraceView } from '../components/TraceView';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Heading, Text } from '../components/ui/Typography';
import { PageContainer, PagePane, BorderedSection } from '../components/ui/PageLayout';

export function Runs() {
  const [runs, setRuns] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRerunning, setIsRerunning] = useState(false);

  const refreshRuns = async () => {
    const runsRes = await fetch('/api/runs');
    const data = await runsRes.json();
    if (Array.isArray(data)) {
      setRuns(data);
    }
    return data;
  };

  useEffect(() => {
    Promise.all([
      fetch('/api/agents/snapshots').then(res => res.json()),
      fetch('/api/registries/datasets').then(res => res.json()),
      refreshRuns(),
    ]).then(([snapsData, datasetsData]) => {
      if (Array.isArray(snapsData)) setSnapshots(snapsData);
      if (Array.isArray(datasetsData)) setDatasets(datasetsData);
    }).catch(console.error);
  }, []);

  const handleGenerate = async () => {
    if (!selectedSnapshotId || !selectedDatasetId) {
      alert('Please select a snapshot and a dataset');
      return;
    }

    const dataset = datasets.find(d => d.id === selectedDatasetId);
    if (!dataset) return;

    setIsGenerating(true);
    try {
      const caseIds: string[] = dataset.case_ids || [];
      for (const case_id of caseIds) {
        await fetch('/api/runs/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            snapshot_id: selectedSnapshotId,
            case_id,
            model_id: 'gemini-2.5-flash',
            force: false,
          }),
        });
      }
      await refreshRuns();
    } catch (err) {
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRerun = async () => {
    const run = runs.find(r => r.id === selectedRunId);
    if (!run) return;

    setIsRerunning(true);
    try {
      const res = await fetch('/api/runs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          snapshot_id: run.snapshot_id,
          case_id: run.case_id,
          model_id: run.model_id,
          force: true,
        }),
      });
      if (!res.ok) {
        console.error('Rerun failed', await res.text());
        return;
      }
      const updated = await res.json();
      await refreshRuns();
      if (updated?.id) {
        setSelectedRunId(updated.id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsRerunning(false);
    }
  };

  const selectedRun = runs.find(r => r.id === selectedRunId) ?? null;

  return (
    <PageContainer variant="full">
      <PagePane variant="sidebar" className="h-full flex flex-col">
        <BorderedSection position="header" className="flex-col gap-3 items-stretch">
          <Heading level={3}>Run Generation</Heading>
          <div className="space-y-2">
            <SnapshotSelect
              aria-label="Snapshot"
              value={selectedSnapshotId}
              onChange={e => setSelectedSnapshotId(e.target.value)}
              snapshots={snapshots}
              placeholder="Select Snapshot..."
            />
            <Select
              aria-label="Dataset"
              value={selectedDatasetId}
              onChange={e => setSelectedDatasetId(e.target.value)}
            >
              <option value="">Select Dataset...</option>
              {datasets.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </Select>
            <Button
              variant="cta"
              className="w-full text-center"
              onClick={handleGenerate}
              id="generate-traces-btn"
              disabled={isGenerating}
            >
              {isGenerating ? 'Generating...' : 'Generate Traces'}
            </Button>
          </div>
        </BorderedSection>
        <div className="flex-1 overflow-y-auto p-2">
          {runs.length > 0 ? (
            runs.map((run: any) => (
              <div
                key={run.id}
                className={`trace-item p-3 border rounded-md cursor-pointer mb-2 transition-colors ${
                  selectedRunId === run.id
                    ? 'bg-surface-container-highest border-primary-fixed'
                    : 'bg-surface-container-lowest border-outline-variant hover:border-primary-fixed'
                }`}
                onClick={() => setSelectedRunId(run.id)}
              >
                <Text variant="body" as="div" className="font-medium truncate">
                  {run.case_id} • {run.id}
                </Text>
                <Text variant="caption" as="div" className="mt-1 font-mono">
                  {run.trace?.latency_ms || 0}ms
                </Text>
              </div>
            ))
          ) : (
            <div className="p-4 text-center">
              <Text variant="muted" className="italic">No traces available.</Text>
            </div>
          )}
        </div>
      </PagePane>

      <PagePane variant="sidebar" className="flex-1 h-full flex flex-col">
        <BorderedSection position="header">
          <Heading level={3}>Trace Detail</Heading>
          <Button
            variant="normal"
            size="sm"
            onClick={handleRerun}
            disabled={!selectedRun || isRerunning}
          >
            {isRerunning ? 'Rerunning...' : 'Rerun'}
          </Button>
        </BorderedSection>
        <div className="flex-1 overflow-hidden">
          {selectedRun ? (
            <TraceView trace={selectedRun.trace} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <Text variant="muted" className="italic">Select a trace to view details</Text>
            </div>
          )}
        </div>
      </PagePane>
    </PageContainer>
  );
}
