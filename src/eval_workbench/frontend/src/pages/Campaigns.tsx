import { useState, useEffect } from 'react';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Heading, Text, FormLabel } from '../components/ui/Typography';
import { PageContainer, PagePane } from '../components/ui/PageLayout';

export function Campaigns() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [matrixData, setMatrixData] = useState<any>(null);
  
  const [campaignName, setCampaignName] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [selectedSnapshotId, setSelectedSnapshotId] = useState('');
  const [modelsInput, setModelsInput] = useState('gemini-2.5-flash, gemini-2.5-flash-lite');

  useEffect(() => {
    Promise.all([
      fetch('/api/campaigns').then(res => res.json()),
      fetch('/api/registries/datasets').then(res => res.json()),
      fetch('/api/agents/snapshots').then(res => res.json()),
    ]).then(([campData, dsData, snapsData]) => {
      if (Array.isArray(campData)) setCampaigns(campData);
      if (Array.isArray(dsData)) setDatasets(dsData);
      if (Array.isArray(snapsData)) setSnapshots(snapsData);
    }).catch(console.error);
  }, []);

  const handleSelectCampaign = (campId: string) => {
    if (!campId) {
      setMatrixData(null);
      return;
    }
    fetch(`/api/campaigns/${campId}/matrix`)
      .then(res => res.json())
      .then(data => setMatrixData(data))
      .catch(console.error);
  };

  const handleLaunch = async () => {
    if (!campaignName || !selectedDatasetId || !selectedSnapshotId) {
      alert("Please fill in all fields");
      return;
    }

    try {
      const models = modelsInput.split(',').map(s => s.strip ? s.strip() : s.trim());
      const payload = {
        id: `campaign_${crypto.randomUUID().substring(0, 8)}`,
        name: campaignName,
        dataset_id: selectedDatasetId,
        model_panel: models,
        base_snapshot_id: selectedSnapshotId,
        created_at: Math.floor(Date.now() / 1000)
      };

      await fetch('/api/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const res = await fetch('/api/campaigns');
      const data = await res.json();
      if (Array.isArray(data)) setCampaigns(data);
      
      handleSelectCampaign(payload.id);

    } catch (err) {
      console.error(err);
    }
  };

  return (
    <PageContainer variant="standard">
      <PagePane variant="card">
        <Heading level={2} className="mb-6">Launch Campaign</Heading>
        <div className="flex gap-4 items-end flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <FormLabel htmlFor="campaign_name">Campaign Name</FormLabel>
            <input 
              id="campaign_name" 
              className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface focus:outline-none focus:border-primary-fixed placeholder:text-on-surface-variant/50 text-sm" 
              placeholder="e.g. Model Size Eval" 
              value={campaignName}
              onChange={e => setCampaignName(e.target.value)}
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <FormLabel htmlFor="campaign_dataset">Dataset</FormLabel>
            <Select 
              id="campaign_dataset" 
              value={selectedDatasetId}
              onChange={e => setSelectedDatasetId(e.target.value)}
            >
              <option value="">Select Dataset...</option>
              {datasets.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </Select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <FormLabel htmlFor="campaign_snapshot">Base Snapshot</FormLabel>
            <SnapshotSelect
              id="campaign_snapshot"
              aria-label="Base Snapshot"
              value={selectedSnapshotId}
              onChange={e => setSelectedSnapshotId(e.target.value)}
              snapshots={snapshots}
              placeholder="Select Snapshot..."
            />
          </div>
          <div className="flex-[2] min-w-[300px]">
            <FormLabel htmlFor="campaign_models">Models (comma-separated)</FormLabel>
            <input 
              id="campaign_models" 
              className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface focus:outline-none focus:border-primary-fixed placeholder:text-on-surface-variant/50 text-sm" 
              value={modelsInput}
              onChange={e => setModelsInput(e.target.value)}
            />
          </div>
          <Button 
            variant="cta"
            onClick={handleLaunch}
          >
            Launch
          </Button>
        </div>
      </PagePane>
      
      <PagePane variant="card">
        <div className="flex justify-between items-center mb-6">
          <Heading level={2}>Response Matrix</Heading>
          <div className="flex gap-4">
            <Select 
              fullWidth={false}
              onChange={(e) => handleSelectCampaign(e.target.value)}
            >
              <option value="">Select Campaign...</option>
              {campaigns.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </Select>
            <Select fullWidth={false}>
              <option>Metric: detect_fault</option>
            </Select>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead className="bg-surface-container-low border-b border-outline-variant text-on-surface-variant">
              <tr>
                <th className="p-3 font-bold">Model</th>
                <th className="p-3 font-bold text-center">Cases</th>
                <th className="p-3 font-bold text-right border-l border-outline-variant">Ability θ</th>
              </tr>
            </thead>
            <tbody>
              {matrixData ? (
                matrixData.models.map((m: any, i: number) => (
                  <tr key={i} className="matrix-row border-b border-outline-variant/50">
                    <td className="p-3 font-medium text-on-surface font-mono">{m}</td>
                    <td className="p-3 text-center">
                      <div className="flex justify-center gap-1">
                        {matrixData.case_ids.map((cid: string) => (
                          <div 
                            key={cid} 
                            className="w-4 h-4 rounded-sm border border-outline-variant/30"
                            style={{ backgroundColor: matrixData.cell[`${m}|${cid}`] > 0.5 ? '#31C48D' : '#F5698E' }}
                            title={cid}
                          />
                        ))}
                      </div>
                    </td>
                    <td className="p-3 text-right font-mono border-l border-outline-variant text-on-surface">
                      {matrixData.ability?.[m]?.toFixed(2) || '0.00'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="p-4 text-center">
                    <Text variant="muted" className="italic">No campaign matrix loaded.</Text>
                  </td>
                </tr>
              )}
            </tbody>
            {matrixData && (
              <tfoot className="bg-surface-container-low border-t border-outline-variant text-on-surface-variant">
                <tr>
                  <td className="p-3 font-bold text-right">Difficulty b</td>
                  <td className="p-3 text-center font-mono">
                    <div className="flex justify-center gap-1">
                      {matrixData.case_ids.map((cid: string) => (
                        <div key={cid} className="w-4 text-[10px] transform -rotate-45 origin-bottom-left truncate" title={matrixData.difficulty?.[cid]}>
                          {matrixData.difficulty?.[cid]?.toFixed(1)}
                        </div>
                      ))}
                    </div>
                  </td>
                  <td className="p-3 border-l border-outline-variant"></td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </PagePane>
    </PageContainer>
  );
}
