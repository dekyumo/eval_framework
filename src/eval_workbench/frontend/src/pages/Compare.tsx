import { useState, useEffect } from 'react';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { Button } from '../components/ui/Button';
import { Heading, Text, FormLabel } from '../components/ui/Typography';
import { PageContainer, PagePane, BorderedSection } from '../components/ui/PageLayout';

interface DiffChange {
  type: 'added' | 'removed' | 'modified';
  component: string;
  name: string;
  detail: string;
  before?: string | null;
  after?: string | null;
  diff?: string | null;
}

interface CompareSummary {
  tools_added: number;
  tools_removed: number;
  tools_modified: number;
  prompts_added: number;
  prompts_removed: number;
  prompts_modified: number;
  total_changes: number;
}

interface CompareResult {
  changes: DiffChange[];
  summary: CompareSummary;
}

function changeBadgeClass(type: DiffChange['type']): string {
  if (type === 'added') return 'bg-semantic-pass/20 text-semantic-pass';
  if (type === 'removed') return 'bg-semantic-fail/20 text-semantic-fail';
  return 'bg-orange-500/20 text-orange-400';
}

function DiffContent({ change }: { change: DiffChange }) {
  if (change.diff) {
    return (
      <pre className="mt-2 p-3 rounded-md bg-surface-container-lowest border border-outline-variant text-xs font-mono whitespace-pre overflow-x-auto text-on-surface">
        {change.diff}
      </pre>
    );
  }
  if (change.type === 'added' && change.after) {
    return (
      <pre className="mt-2 p-3 rounded-md bg-semantic-pass/10 border border-semantic-pass/30 text-xs font-mono whitespace-pre-wrap overflow-x-auto text-on-surface">
        {change.after}
      </pre>
    );
  }
  if (change.type === 'removed' && change.before) {
    return (
      <pre className="mt-2 p-3 rounded-md bg-semantic-fail/10 border border-semantic-fail/30 text-xs font-mono whitespace-pre-wrap overflow-x-auto text-on-surface">
        {change.before}
      </pre>
    );
  }
  return null;
}

export function Compare() {
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [selectedSnapshotA, setSelectedSnapshotA] = useState('');
  const [selectedSnapshotB, setSelectedSnapshotB] = useState('');
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/agents/snapshots')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setSnapshots(data);
      })
      .catch(console.error);
  }, []);

  const handleCompare = async () => {
    if (!selectedSnapshotA || !selectedSnapshotB) {
      setError('Select both snapshots before comparing.');
      return;
    }
    if (selectedSnapshotA === selectedSnapshotB) {
      setError('Choose two different snapshots.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('/api/agents/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          snapshot_a: selectedSnapshotA,
          snapshot_b: selectedSnapshotB,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Comparison failed');
        return;
      }
      setResult({ changes: data.changes || [], summary: data.summary });
    } catch (e) {
      console.error(e);
      setError('Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  const summaryRows = result
    ? [
        ['Tools added', result.summary.tools_added],
        ['Tools removed', result.summary.tools_removed],
        ['Tools modified', result.summary.tools_modified],
        ['Prompts added', result.summary.prompts_added],
        ['Prompts removed', result.summary.prompts_removed],
        ['Prompts modified', result.summary.prompts_modified],
      ]
    : [];

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
            disabled={loading}
          >
            {loading ? 'Comparing…' : 'Compare'}
          </Button>
        </div>
        {error && (
          <Text variant="muted" className="text-semantic-fail mt-4 text-sm">{error}</Text>
        )}
      </PagePane>

      {result && (
        <PagePane variant="card">
          <div className="flex flex-wrap gap-6 mb-6">
            <BorderedSection className="justify-between items-center cursor-default min-w-[180px]">
              <span className="font-bold text-on-surface">Total changes</span>
              <span className="font-mono text-primary-fixed font-bold">{result.summary.total_changes}</span>
            </BorderedSection>
            {summaryRows.map(([label, count]) => (
              <BorderedSection key={label} className="justify-between items-center cursor-default min-w-[180px]">
                <span className="text-on-surface-variant text-sm">{label}</span>
                <span className="font-mono text-on-surface text-sm">{count}</span>
              </BorderedSection>
            ))}
          </div>

          <Heading level={3} className="mb-4">Changes</Heading>
          <div className="space-y-4">
            {result.changes.length > 0 ? (
              result.changes.map((c, i) => (
                <BorderedSection key={i} className="flex-col items-stretch gap-2 cursor-default">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-on-surface font-mono text-sm">{c.component} • {c.name}</span>
                    <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded font-mono ${changeBadgeClass(c.type)}`}>
                      {c.type}
                    </span>
                  </div>
                  <Text variant="muted" className="text-xs">{c.detail}</Text>
                  <DiffContent change={c} />
                </BorderedSection>
              ))
            ) : (
              <Text variant="muted" className="italic text-center">
                No tool or prompt differences between these snapshots.
              </Text>
            )}
          </div>
        </PagePane>
      )}
    </PageContainer>
  );
}
