import { useState, useEffect, useMemo } from 'react';
import { TraceView } from '../components/TraceView';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { CaseStatusBadge } from '../components/CaseStatusBadge';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Heading, Text } from '../components/ui/Typography';
import { PageContainer, PagePane, BorderedSection } from '../components/ui/PageLayout';

export function Runs() {
  const [runs, setRuns] = useState<any[]>([]);
  const [cases, setCases] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
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
      fetch('/api/cases').then(res => res.json()),
      refreshRuns(),
    ]).then(([snapsData, datasetsData, casesData]) => {
      if (Array.isArray(snapsData)) setSnapshots(snapsData);
      if (Array.isArray(datasetsData)) setDatasets(datasetsData);
      if (Array.isArray(casesData)) setCases(casesData);
    }).catch(console.error);
  }, []);

  const selectedDataset = datasets.find(d => d.id === selectedDatasetId);
  const datasetCaseIds: string[] = selectedDataset?.case_ids || [];

  const casesForSelection = useMemo(() => {
    if (!selectedSnapshotId || !selectedDatasetId) return [];
    return datasetCaseIds
      .map(id => cases.find(c => c.id === id))
      .filter((c): c is NonNullable<typeof c> => Boolean(c));
  }, [cases, datasetCaseIds, selectedSnapshotId, selectedDatasetId]);

  const runForCase = (caseId: string) =>
    runs.find(r => r.snapshot_id === selectedSnapshotId && r.case_id === caseId);

  const selectedRun = selectedCaseId ? runForCase(selectedCaseId) ?? null : null;

  const handleGenerate = async () => {
    if (!selectedSnapshotId || !selectedDatasetId) {
      alert('Please select a snapshot and a dataset');
      return;
    }

    setIsGenerating(true);
    try {
      for (const case_id of datasetCaseIds) {
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
    if (!selectedRun) return;

    setIsRerunning(true);
    try {
      const res = await fetch('/api/runs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          snapshot_id: selectedRun.snapshot_id,
          case_id: selectedRun.case_id,
          model_id: selectedRun.model_id,
          force: true,
        }),
      });
      if (!res.ok) {
        console.error('Rerun failed', await res.text());
        return;
      }
      await refreshRuns();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRerunning(false);
    }
  };

  return (
    <PageContainer variant="full">
      <PagePane variant="sidebar" className="h-full flex flex-col">
        <BorderedSection position="header" className="flex-col gap-3 items-stretch">
          <Heading level={3}>Run Generation</Heading>
          <div className="space-y-2">
            <SnapshotSelect
              aria-label="Snapshot"
              value={selectedSnapshotId}
              onChange={e => {
                setSelectedSnapshotId(e.target.value);
                setSelectedCaseId(null);
              }}
              snapshots={snapshots}
              placeholder="Select Snapshot..."
            />
            <Select
              aria-label="Dataset"
              value={selectedDatasetId}
              onChange={e => {
                setSelectedDatasetId(e.target.value);
                setSelectedCaseId(null);
              }}
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
              disabled={isGenerating || !selectedSnapshotId || !selectedDatasetId}
            >
              {isGenerating ? 'Generating...' : 'Generate Traces'}
            </Button>
          </div>
        </BorderedSection>
        <div className="flex-1 overflow-y-auto p-2">
          {casesForSelection.length > 0 ? (
            casesForSelection.map(caseItem => {
              const run = runForCase(caseItem.id);
              const generated = Boolean(run);
              return (
                <div
                  key={caseItem.id}
                  className={`trace-item p-3 border rounded-md cursor-pointer mb-2 transition-colors ${
                    selectedCaseId === caseItem.id
                      ? 'bg-surface-container-highest border-primary-fixed'
                      : 'bg-surface-container-lowest border-outline-variant hover:border-primary-fixed'
                  }`}
                  onClick={() => setSelectedCaseId(caseItem.id)}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {generated ? (
                      <CaseStatusBadge label="ran" variant="pass" />
                    ) : (
                      <CaseStatusBadge label="not-gen" variant="margin" />
                    )}
                    <Text variant="body" as="div" className="font-medium truncate">
                      {caseItem.name || caseItem.id}
                    </Text>
                  </div>
                  {run && (
                    <Text variant="caption" as="div" className="mt-1 font-mono pl-4">
                      {run.trace?.latency_ms || 0}ms
                    </Text>
                  )}
                </div>
              );
            })
          ) : (
            <div className="p-4 text-center">
              <Text variant="muted" className="italic">
                {selectedSnapshotId && selectedDatasetId
                  ? 'No cases in this dataset.'
                  : 'Select a snapshot and dataset to view cases.'}
              </Text>
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
              <Text variant="muted" className="italic">
                {selectedCaseId ? 'No trace yet for this case.' : 'Select a case to view details'}
              </Text>
            </div>
          )}
        </div>
      </PagePane>
    </PageContainer>
  );
}
