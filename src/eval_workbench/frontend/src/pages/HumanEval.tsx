import { useState, useEffect } from 'react';
import { TraceView } from '../components/TraceView';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Heading, Text, FormLabel } from '../components/ui/Typography';
import { PageContainer, PagePane, BorderedSection } from '../components/ui/PageLayout';

export function HumanEval() {
  const [runs, setRuns] = useState<any[]>([]);
  const [rubrics, setRubrics] = useState<any[]>([]);
  const [selectedRunId, setSelectedRunId] = useState('');
  const [selectedRubricId, setSelectedRubricId] = useState('');

  useEffect(() => {
    Promise.all([
      fetch('/api/runs/').then(res => res.json()),
      fetch('/api/registries/rubrics').then(res => res.json())
    ]).then(([runsData, rubricsData]) => {
      if (Array.isArray(runsData)) setRuns(runsData);
      if (Array.isArray(rubricsData)) setRubrics(rubricsData);
    }).catch(console.error);
  }, []);

  const selectedRun = runs.find(r => r.id === selectedRunId);
  const selectedRubric = rubrics.find(r => r.id === selectedRubricId) || (rubrics.length > 0 ? rubrics[0] : null);

  const handleSubmit = async () => {
    const rubricId = selectedRubricId || selectedRubric?.id;
    if (!selectedRunId || !rubricId) return;

    const results: Record<string, boolean | string | number> = {};
    if (selectedRubric?.items) {
      for (const item of selectedRubric.items) {
        const field = document.getElementById(item.name) as HTMLSelectElement | HTMLInputElement | null;
        if (!field) continue;
        if (item.type === 'bool') {
          results[item.name] = (field as HTMLSelectElement).value === 'True';
        } else {
          results[item.name] = field.value;
        }
      }
    } else {
      const fallback = document.getElementById('is_achievable') as HTMLSelectElement | null;
      if (fallback) {
        results.is_achievable = fallback.value === 'True';
      }
    }

    try {
      await fetch('/api/human-eval', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: `he_${crypto.randomUUID().substring(0, 8)}`,
          run_id: selectedRunId,
          rubric_id: rubricId,
          results,
          comments: ""
        })
      });
      alert('Saved!');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <PageContainer variant="full">
      <PagePane variant="sidebar" className="flex-1 h-full flex flex-col">
        <BorderedSection position="header" className="flex-col gap-3 items-stretch">
          <Heading level={3}>Human Eval / Select Trace</Heading>
          <Select
            aria-label="Run to grade"
            data-testid="human-eval-run-select"
            value={selectedRunId}
            onChange={e => setSelectedRunId(e.target.value)}
          >
            <option value="">Select a run to grade...</option>
            {runs.map((r, idx) => (
              <option key={idx} value={r.id}>{r.id}</option>
            ))}
          </Select>
        </BorderedSection>
        <div className="flex-1 overflow-hidden">
          {selectedRun ? (
            <TraceView trace={selectedRun.trace} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <Text variant="muted" className="italic">No trace selected</Text>
            </div>
          )}
        </div>
      </PagePane>

      <PagePane variant="sidebar" className="h-full flex flex-col p-6">
        <Heading level={2} className="mb-6">Grade Trace</Heading>
        
        <div className="space-y-6 flex-1 overflow-y-auto">
          {selectedRun ? (
            <div className="space-y-4">
              <Text variant="muted" className="mb-4">Select a rubric and grade the trace.</Text>
              <div>
                <FormLabel>Rubric</FormLabel>
                <Select
                  aria-label="Rubric"
                  value={selectedRubricId}
                  onChange={e => setSelectedRubricId(e.target.value)}
                >
                  <option value="">Select Rubric...</option>
                  {rubrics.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                </Select>
              </div>

              {selectedRubric && selectedRubric.items && selectedRubric.items.map((item: any, idx: number) => (
                <div key={idx}>
                  <FormLabel htmlFor={item.name}>{item.name}</FormLabel>
                  {item.type === 'bool' ? (
                    <Select id={item.name}>
                      <option>False</option>
                      <option>True</option>
                    </Select>
                  ) : (
                    <input id={item.name} className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface focus:outline-none focus:border-primary-fixed text-sm" />
                  )}
                </div>
              ))}
              
              {!selectedRubric && (
                <div>
                  <FormLabel htmlFor="is_achievable">is_achievable (Fallback)</FormLabel>
                  <Select id="is_achievable">
                    <option>False</option>
                    <option>True</option>
                  </Select>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center">
              <Text variant="muted" className="italic">No traces available to grade.</Text>
            </div>
          )}
        </div>
        
        <BorderedSection position="footer">
          <Button 
            variant="cta"
            className="w-full text-center"
            onClick={handleSubmit}
            disabled={!selectedRun}
          >
            Submit Grade
          </Button>
        </BorderedSection>
      </PagePane>
    </PageContainer>
  );
}
