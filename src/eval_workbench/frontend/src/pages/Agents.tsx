import { useState, useEffect, useCallback } from 'react';
import { LineageGraph } from '../components/LineageGraph';
import { ScanAgent } from '../components/ScanAgent';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { Button } from '../components/ui/Button';
import { TextAreaWithLabel } from '../components/ui/Textarea';
import { Heading } from '../components/ui/Typography';
import { PageContainer, PageHeader, PagePane } from '../components/ui/PageLayout';

type GovernanceView = {
  concern_coverage: string;
  business_case: string;
};

const CONCERN_COVERAGE_PLACEHOLDER =
  "Concerns from Govern 1.1 (Compliance) are covered by tags 'legal' and 'compliance'\n" +
  "Concerns from Govern 1.4 (Risk prioritisation) are tagged with 'high_risk'\n" +
  "Concerns from Govern 3.2 (Roles and responsibilities) tags cases with the name of the team who added them, with 'team_*' case\n" +
  '...';

export function Agents() {
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<any>(null);
  const [governance, setGovernance] = useState<GovernanceView | null>(null);
  const [savingGovernance, setSavingGovernance] = useState(false);

  const loadSnapshots = useCallback(() => {
    fetch('/api/agents/snapshots')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setSnapshots(data);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    loadSnapshots();
  }, [loadSnapshots]);

  const loadGovernance = (snapshotId: string) => {
    fetch(`/api/governance/${snapshotId}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          setGovernance(null);
          return;
        }
        setGovernance({
          concern_coverage: data.concern_coverage || '',
          business_case: data.business_case || '',
        });
      })
      .catch(console.error);
  };

  const handleSelect = useCallback((id: string) => {
    if (!id) {
      setSelectedSnapshot(null);
      setGovernance(null);
      return;
    }
    fetch(`/api/agents/snapshots/${id}`)
      .then(res => res.json())
      .then(data => {
        setSelectedSnapshot(data);
        loadGovernance(id);
      })
      .catch(console.error);
  }, []);

  const handleScanned = (snapshotId: string) => {
    loadSnapshots();
    handleSelect(snapshotId);
  };

  const saveGovernance = async () => {
    if (!selectedSnapshot?.id || !governance) return;
    setSavingGovernance(true);
    try {
      const res = await fetch(`/api/governance/${selectedSnapshot.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(governance),
      });
      const data = await res.json();
      if (!data.error) {
        setGovernance({
          concern_coverage: data.concern_coverage || '',
          business_case: data.business_case || '',
        });
      }
    } finally {
      setSavingGovernance(false);
    }
  };

  const headerActions = (
    <SnapshotSelect
      fullWidth={false}
      aria-label="Snapshot"
      snapshots={snapshots}
      placeholder="Select a snapshot..."
      value={selectedSnapshot?.id || ''}
      onChange={e => handleSelect(e.target.value)}
    />
  );

  return (
    <PageContainer variant="contained">
      <PageHeader
        title="Agents Graph & Lineage"
        description="View Agent Manifest and Lineage Graph here."
        actions={headerActions}
      />

      <PagePane variant="card" className="mb-6">
        <ScanAgent onScanned={handleScanned} />
      </PagePane>

      {selectedSnapshot ? (
        <>
          <LineageGraph manifest={selectedSnapshot.manifest} />

          <PagePane variant="card">
            <Heading level={3} className="mb-4">Distribution Definition</Heading>
            <div className="space-y-4">
              <TextAreaWithLabel
                id="agent_description"
                label="Description"
                className="h-20"
                defaultValue={selectedSnapshot.distribution?.description || ''}
              />
              <div className="grid grid-cols-3 gap-4">
                <TextAreaWithLabel
                  id="in_distribution"
                  label="In Distribution"
                  className="h-32"
                  defaultValue={(selectedSnapshot.distribution?.regions?.in_distribution || []).join('\n')}
                />
                <TextAreaWithLabel
                  id="margin"
                  label="Margin"
                  className="h-32"
                  defaultValue={(selectedSnapshot.distribution?.regions?.margin || []).join('\n')}
                />
                <TextAreaWithLabel
                  id="out_of_distribution"
                  label="Out of Distribution"
                  className="h-32"
                  defaultValue={(selectedSnapshot.distribution?.regions?.ood || []).join('\n')}
                />
              </div>
              <Button variant="cta" onClick={() => {}}>
                Save Distribution
              </Button>
            </div>
          </PagePane>

          {governance && (
            <PagePane variant="card">
              <Heading level={3} className="mb-4">NIST AI RMF Profile</Heading>
              <div className="space-y-4">
                <TextAreaWithLabel
                  id="concern_coverage"
                  label="Concern coverage"
                  className="h-40"
                  value={governance.concern_coverage}
                  onChange={e => setGovernance(prev => prev ? { ...prev, concern_coverage: e.target.value } : prev)}
                  placeholder={CONCERN_COVERAGE_PLACEHOLDER}
                />
                <TextAreaWithLabel
                  id="business_case"
                  label="Business case"
                  className="h-24"
                  value={governance.business_case}
                  onChange={e => setGovernance(prev => prev ? { ...prev, business_case: e.target.value } : prev)}
                  placeholder="Doing it with people costs $X; with the agent $Y, the probability of successfully running the agent is Z..."
                />
                <Button variant="cta" onClick={saveGovernance} disabled={savingGovernance}>
                  {savingGovernance ? 'Saving...' : 'Save Profile'}
                </Button>
              </div>
            </PagePane>
          )}
        </>
      ) : (
        <div className="text-on-surface-variant italic p-8 text-center border border-outline-variant rounded-xl bg-surface-container-low shadow-sm">
          No snapshot selected. Please select one from the dropdown above.
        </div>
      )}
    </PageContainer>
  );
}
