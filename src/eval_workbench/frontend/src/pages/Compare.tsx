import { useState, useEffect } from 'react';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { Button } from '../components/ui/Button';
import { Heading, Text, FormLabel } from '../components/ui/Typography';
import { PageContainer, PagePane, BorderedSection } from '../components/ui/PageLayout';

export function Compare() {
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [selectedSnapshotA, setSelectedSnapshotA] = useState('');
  const [selectedSnapshotB, setSelectedSnapshotB] = useState('');
  const [diff, setDiff] = useState<any>(null);

  useEffect(() => {
    fetch('/api/agents/snapshots')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setSnapshots(data);
      })
      .catch(console.error);
  }, []);

  const handleCompare = () => {
    setDiff({
      changes: [
        { type: 'added', component: 'Tool', name: 'WebSearchTool', detail: 'Added search functionality' },
        { type: 'modified', component: 'Agent', name: 'planner_agent', detail: 'Model updated from gemini-2.0-flash to gemini-2.5-flash' }
      ],
      regressions: [
        { case_id: 'case_1', metric: 'is_achievable', base: 'True', head: 'False' }
      ]
    });
  };

  return (
    <PageContainer variant="standard">
      <PagePane variant="card">
        <Heading level={2} className="mb-6">Compare Snapshots</Heading>
        <div className="flex gap-4 items-end flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <FormLabel>Snapshot A (Base)</FormLabel>
            <SnapshotSelect
              aria-label="Snapshot A"
              value={selectedSnapshotA}
              onChange={e => setSelectedSnapshotA(e.target.value)}
              snapshots={snapshots}
              placeholder="Select snapshot..."
            />
          </div>
          <div className="text-on-surface-variant/70 pb-2 font-bold text-xl self-center">vs</div>
          <div className="flex-1 min-w-[200px]">
            <FormLabel>Snapshot B (New)</FormLabel>
            <SnapshotSelect
              aria-label="Snapshot B"
              value={selectedSnapshotB}
              onChange={e => setSelectedSnapshotB(e.target.value)}
              snapshots={snapshots}
              placeholder="Select snapshot..."
            />
          </div>
          <Button 
            variant="cta"
            onClick={handleCompare}
          >
            Compare
          </Button>
        </div>
      </PagePane>
      
      <div className="grid grid-cols-2 gap-6">
        <PagePane variant="sidebar" title="Semantic Diff" className="w-auto">
          <div className="p-4 space-y-3">
            {diff ? (
              diff.changes.map((c: any, i: number) => (
                <BorderedSection key={i} className="flex-col items-stretch gap-2 cursor-default">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-on-surface font-mono text-sm">{c.component} • {c.name}</span>
                    <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded font-mono ${c.type === 'added' ? 'bg-semantic-pass/20 text-semantic-pass' : 'bg-orange-500/20 text-orange-400'}`}>{c.type}</span>
                  </div>
                  <Text variant="muted" className="text-xs">{c.detail}</Text>
                </BorderedSection>
              ))
            ) : (
              <div className="text-center">
                <Text variant="muted" className="italic">No comparison active.</Text>
              </div>
            )}
          </div>
        </PagePane>
        
        <PagePane variant="sidebar" title="Regressions" className="w-auto">
          <div className="p-4 space-y-3">
            {diff ? (
              diff.regressions.map((r: any, i: number) => (
                <BorderedSection key={i} className="justify-between items-center cursor-default">
                  <div>
                    <span className="font-bold text-on-surface font-mono text-sm block">{r.case_id}</span>
                    <Text variant="caption" className="font-mono text-xs mt-1">{r.metric}</Text>
                  </div>
                  <div className="flex gap-2 items-center font-mono text-xs">
                    <span className="text-semantic-pass bg-semantic-pass/10 px-1.5 py-0.5 rounded">{r.base}</span>
                    <Text variant="muted" as="span">→</Text>
                    <span className="text-semantic-fail bg-semantic-fail/10 px-1.5 py-0.5 rounded">{r.head}</span>
                  </div>
                </BorderedSection>
              ))
            ) : (
              <div className="text-center">
                <Text variant="muted" className="italic">No comparison active.</Text>
              </div>
            )}
          </div>
        </PagePane>
      </div>
    </PageContainer>
  );
}
