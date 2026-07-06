import { useState, useEffect } from 'react';
import { LineageGraph } from '../components/LineageGraph';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { Button } from '../components/ui/Button';
import { Textarea, TextAreaWithLabel } from '../components/ui/Textarea';
import { Heading } from '../components/ui/Typography';
import { PageContainer, PageHeader, PagePane } from '../components/ui/PageLayout';

export function Agents() {
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<any>(null);

  useEffect(() => {
    fetch('/api/agents/snapshots')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setSnapshots(data);
      })
      .catch(console.error);
  }, []);

  const handleSelect = (id: string) => {
    if (!id) {
      setSelectedSnapshot(null);
      return;
    }
    fetch(`/api/agents/snapshots/${id}`)
      .then(res => res.json())
      .then(data => setSelectedSnapshot(data))
      .catch(console.error);
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
              <Button 
                variant="cta"
                onClick={() => {}}
              >
                Save Distribution
              </Button>
            </div>
          </PagePane>
        </>
      ) : (
        <div className="text-on-surface-variant italic p-8 text-center border border-outline-variant rounded-xl bg-surface-container-low shadow-sm">
          No snapshot selected. Please select one from the dropdown above.
        </div>
      )}
    </PageContainer>
  );
}
