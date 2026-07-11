import { useState, useEffect, useMemo } from 'react';
import { ResultView } from '../components/ResultView';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { CaseStatusBadge } from '../components/CaseStatusBadge';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Heading, Text } from '../components/ui/Typography';
import { PageContainer, PagePane, BorderedSection } from '../components/ui/PageLayout';

export function Evals() {
  const [evalResults, setEvalResults] = useState<any[]>([]);
  const [cases, setCases] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isRerunning, setIsRerunning] = useState(false);

  const refreshData = async () => {
    const [evalsData, runsData] = await Promise.all([
      fetch('/api/runs/scored').then(res => res.json()),
      fetch('/api/runs').then(res => res.json()),
    ]);
    if (Array.isArray(evalsData)) setEvalResults(evalsData);
    if (Array.isArray(runsData)) setRuns(runsData);
  };

  useEffect(() => {
    Promise.all([
      fetch('/api/agents/snapshots').then(res => res.json()),
      fetch('/api/registries/datasets').then(res => res.json()),
      fetch('/api/cases').then(res => res.json()),
      refreshData(),
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

  const isEvaluated = (caseId: string) => {
    const run = runForCase(caseId);
    if (!run) return false;
    return evalResults.some(e => e.run_id === run.id);
  };

  const selectedRun = selectedCaseId ? runForCase(selectedCaseId) ?? null : null;
  const selectedEval = selectedRun
    ? evalResults.find(e => e.run_id === selectedRun.id) ?? null
    : null;

  const upsertEvalResult = (scored: { id: string; run_id: string }) => {
    setEvalResults(prev => {
      const rest = prev.filter(e => e.run_id !== scored.run_id);
      return [...rest, scored];
    });
  };

  const handleEvaluate = async () => {
    if (!selectedSnapshotId || !selectedDatasetId) {
      alert('Please select a snapshot and a dataset');
      return;
    }

    setIsEvaluating(true);
    try {
      const runsToEvaluate = runs.filter(
        r => r.snapshot_id === selectedSnapshotId && datasetCaseIds.includes(r.case_id)
      );

      for (const run of runsToEvaluate) {
        const res = await fetch('/api/runs/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ run_id: run.id }),
        });
        if (!res.ok) {
          console.error('Evaluate failed', run.id, await res.text());
          continue;
        }
        upsertEvalResult(await res.json());
      }

      await refreshData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleRerun = async () => {
    if (!selectedRun) return;

    setIsRerunning(true);
    try {
      const res = await fetch('/api/runs/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: selectedRun.id }),
      });
      if (!res.ok) {
        console.error('Rerun failed', await res.text());
        return;
      }
      upsertEvalResult(await res.json());
      await refreshData();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRerunning(false);
    }
  };

  return (
    <PageContainer variant="full">
      <PagePane variant="sidebar">
        <BorderedSection position="header" className="flex-col gap-3 items-stretch">
          <Heading level={3}>Run Evals</Heading>
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
              {datasets.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </Select>
            <Button
              variant="cta"
              className="w-full text-center"
              onClick={handleEvaluate}
              disabled={isEvaluating || !selectedSnapshotId || !selectedDatasetId}
            >
              {isEvaluating ? 'Evaluating...' : 'Run Evaluations'}
            </Button>
          </div>
        </BorderedSection>
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {casesForSelection.length > 0 ? (
            casesForSelection.map(caseItem => {
              const run = runForCase(caseItem.id);
              const evaluated = isEvaluated(caseItem.id);
              return (
                <div
                  key={caseItem.id}
                  className={`eval-item p-3 rounded-md cursor-pointer border transition-colors ${
                    selectedCaseId === caseItem.id
                      ? 'bg-surface-container-highest border-primary-fixed'
                      : 'bg-surface-container-lowest border-outline-variant hover:border-primary-fixed'
                  }`}
                  onClick={() => setSelectedCaseId(caseItem.id)}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {!run ? (
                      <CaseStatusBadge label="not-gen" variant="fail" />
                    ) : evaluated ? (
                      <CaseStatusBadge label="ran" variant="pass" />
                    ) : (
                      <CaseStatusBadge label="not-eval" variant="margin" />
                    )}
                    <Text variant="mono" as="div" className="truncate" title={caseItem.name || caseItem.id}>
                      {caseItem.name || caseItem.id}
                    </Text>
                  </div>
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

      <PagePane variant="content">
        <BorderedSection position="header" className="mb-6">
          <Heading level={2}>Evaluation Results</Heading>
          <Button
            variant="normal"
            size="sm"
            onClick={handleRerun}
            disabled={!selectedRun || isRerunning}
          >
            {isRerunning ? 'Rerunning...' : 'Rerun'}
          </Button>
        </BorderedSection>

        <div className="space-y-6">
          {selectedEval ? (
            <PagePane variant="low" className="p-4">
              <Heading level={3} className="font-mono mb-4">{selectedEval.run_id}</Heading>
              {Array.isArray(selectedEval.results) ? (
                selectedEval.results.map((res: any, i: number) => (
                  <div key={i} className="mb-4 border-b border-outline-variant/30 pb-4 last:border-b-0 last:pb-0">
                    <Text variant="muted" as="div" className="mb-1 font-semibold">{res.name}</Text>
                    <ResultView type={res.type} value={res.value} />
                    {res.rationale && (
                      <div className="text-xs text-on-surface-variant mt-2 bg-surface-container-highest p-3 rounded-lg italic font-sans leading-relaxed border border-outline-variant/20">
                        <span className="font-semibold block mb-1 font-mono text-[10px] uppercase tracking-wider not-italic text-primary-fixed">Rationale</span>
                        {res.rationale}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                Object.entries(selectedEval.results || {}).map(([metricId, result]: [string, any], i) => (
                  <div key={i} className="mb-4">
                    <Text variant="muted" as="div" className="mb-1 font-semibold">{metricId}</Text>
                    <ResultView type={result.type} value={result.value} />
                  </div>
                ))
              )}
              {(!selectedEval.results || (Array.isArray(selectedEval.results) ? selectedEval.results.length === 0 : Object.keys(selectedEval.results).length === 0)) && (
                <Text variant="muted" className="italic">No metrics returned.</Text>
              )}
            </PagePane>
          ) : (
            <Text variant="muted" className="italic">
              {selectedCaseId && !selectedRun
                ? 'No trace to evaluate for this case.'
                : selectedCaseId
                  ? 'Not evaluated yet — run evaluations or click Rerun.'
                  : 'Select a case to view its evaluation results.'}
            </Text>
          )}
        </div>
      </PagePane>
    </PageContainer>
  );
}
