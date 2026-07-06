import { useState, useEffect } from 'react';
import { ResultView } from '../components/ResultView';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Heading, Text } from '../components/ui/Typography';
import { PageContainer, PagePane, BorderedSection } from '../components/ui/PageLayout';

export function Evals() {
  const [evalResults, setEvalResults] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const [runs, setRuns] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      fetch('/api/agents/snapshots').then(res => res.json()),
      fetch('/api/registries/datasets').then(res => res.json()),
      fetch('/api/runs/scored').then(res => res.json()),
      fetch('/api/runs').then(res => res.json())
    ]).then(([snapsData, datasetsData, evalsData, runsData]) => {
      if (Array.isArray(snapsData)) setSnapshots(snapsData);
      if (Array.isArray(datasetsData)) setDatasets(datasetsData);
      if (Array.isArray(evalsData)) setEvalResults(evalsData);
      if (Array.isArray(runsData)) setRuns(runsData);
    }).catch(console.error);
  }, []);

  const handleEvaluate = async () => {
    try {
      const runsRes = await fetch('/api/runs');
      const runs = await runsRes.json();
      
      const dataset = datasets.find(d => d.id === selectedDatasetId);
      const caseIds = dataset ? (dataset.case_ids || []) : [];
      
      const runsToEvaluate = runs.filter((r: any) => 
        r.snapshot_id === selectedSnapshotId && caseIds.includes(r.case_id)
      );

      for (const run of runsToEvaluate.length > 0 ? runsToEvaluate : runs) {
        await fetch('/api/runs/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            run_id: run.id
          })
        });
      }
      
      const evalsRes = await fetch('/api/runs/scored');
      const data = await evalsRes.json();
      if (Array.isArray(data)) {
        setEvalResults(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const selectedEval = evalResults.find(e => e.run_id === selectedRunId) || (evalResults.length > 0 ? evalResults[0] : null);

  return (
    <PageContainer variant="full">
      <PagePane variant="sidebar">
        <BorderedSection position="header" className="flex-col gap-3 items-stretch">
          <Heading level={3}>Run Evals</Heading>
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
              {datasets.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </Select>
            <Button 
              variant="cta"
              className="w-full text-center"
              onClick={handleEvaluate}
            >
              Run Evaluations
            </Button>
          </div>
        </BorderedSection>
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {evalResults.length > 0 ? (
            evalResults.map((res: any, idx: number) => {
              const run = runs.find(r => r.id === res.run_id);
              const dsName = datasets.find(d => d.case_ids?.includes(run?.case_id))?.name || 'Unknown Dataset';
              const label = run ? `${dsName} • ${run.case_id} • ${res.run_id.substring(0, 6)}` : res.run_id;
              
              return (
              <div 
                key={idx} 
                className={`eval-item p-3 rounded-md cursor-pointer border transition-colors ${selectedRunId === res.run_id ? 'bg-surface-container-highest border-primary-fixed' : 'bg-surface-container-lowest border-outline-variant hover:border-primary-fixed'}`}
                onClick={() => setSelectedRunId(res.run_id)}
              >
                <Text variant="mono" as="div" className="truncate" title={label}>{label}</Text>
              </div>
            )})
          ) : (
            <div className="p-4 text-center">
              <Text variant="muted" className="italic">No scored runs available.</Text>
            </div>
          )}
        </div>
      </PagePane>

      <PagePane variant="content">
        <Heading level={2} className="mb-6">Evaluation Results</Heading>
        
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
            <Text variant="muted" className="italic">Select a run to view its evaluation results.</Text>
          )}
        </div>
      </PagePane>
    </PageContainer>
  );
}
