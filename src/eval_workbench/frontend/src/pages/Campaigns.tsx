import { useState, useEffect, useCallback } from 'react';
import { SnapshotSelect } from '../components/SnapshotSelect';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Heading, Text, FormLabel } from '../components/ui/Typography';
import { PageContainer, PagePane } from '../components/ui/PageLayout';
import { useDomainEvent, useTasks } from '../context/TaskContext';
import { enqueueRunCampaign } from '../lib/jobsApi';

function cellColor(value: number, metricType: string): string {
  if (metricType === 'bool') {
    return value > 0.5 ? '#31C48D' : '#F5698E';
  }
  const t = Math.max(0, Math.min(1, value));
  const r = Math.round(245 + (49 - 245) * t);
  const g = Math.round(152 + (196 - 152) * t);
  const b = Math.round(142 + (141 - 142) * t);
  return `rgb(${r}, ${g}, ${b})`;
}

function shortCaseId(caseId: string): string {
  return caseId.length > 12 ? `${caseId.slice(0, 10)}…` : caseId;
}

export function Campaigns() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [matrixData, setMatrixData] = useState<any>(null);

  const [campaignName, setCampaignName] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [selectedSnapshotId, setSelectedSnapshotId] = useState('');
  const [modelsInput, setModelsInput] = useState('gemini-2.5-flash, gemini-2.5-flash-lite');
  const [selectedCampaignId, setSelectedCampaignId] = useState('');
  const [selectedMetric, setSelectedMetric] = useState('');
  const { activeTasks } = useTasks();

  const isLaunching = activeTasks.some(task => task.type === 'run_campaign');

  const refreshCampaigns = useCallback(async () => {
    const res = await fetch('/api/campaigns');
    const data = await res.json();
    if (Array.isArray(data)) setCampaigns(data);
    return data;
  }, []);

  useEffect(() => {
    Promise.all([
      refreshCampaigns(),
      fetch('/api/registries/datasets').then(res => res.json()),
      fetch('/api/agents/snapshots').then(res => res.json()),
    ]).then(([, dsData, snapsData]) => {
      if (Array.isArray(dsData)) setDatasets(dsData);
      if (Array.isArray(snapsData)) setSnapshots(snapsData);
    }).catch(console.error);
  }, [refreshCampaigns]);

  const loadMatrix = useCallback((campId: string, metric?: string) => {
    if (!campId) {
      setMatrixData(null);
      setSelectedMetric('');
      return;
    }
    const params = metric ? `?metric=${encodeURIComponent(metric)}` : '';
    fetch(`/api/campaigns/${campId}/matrix${params}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          console.error(data.error);
          return;
        }
        setMatrixData(data);
        if (data.metric_name) setSelectedMetric(data.metric_name);
      })
      .catch(console.error);
  }, []);

  useDomainEvent('campaign_finished', (data) => {
    const campaignId = data.campaign_id as string | undefined;
    refreshCampaigns().then(() => {
      if (campaignId) {
        setSelectedCampaignId(campaignId);
        loadMatrix(campaignId);
      }
    }).catch(console.error);
  });

  const handleSelectCampaign = (campId: string) => {
    setSelectedCampaignId(campId);
    setSelectedMetric('');
    loadMatrix(campId);
  };

  const handleSelectMetric = (metric: string) => {
    setSelectedMetric(metric);
    if (selectedCampaignId) loadMatrix(selectedCampaignId, metric);
  };

  const handleLaunch = async () => {
    if (!campaignName || !selectedDatasetId || !selectedSnapshotId) {
      alert('Please fill in all fields');
      return;
    }

    try {
      const models = modelsInput.split(',').map(s => s.trim());
      const payload = {
        id: `campaign_${crypto.randomUUID().substring(0, 8)}`,
        name: campaignName,
        dataset_id: selectedDatasetId,
        model_panel: models,
        base_snapshot_id: selectedSnapshotId,
        created_at: Math.floor(Date.now() / 1000),
      };

      await enqueueRunCampaign(payload);
      setSelectedCampaignId(payload.id);
      await refreshCampaigns();
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : 'Failed to launch campaign');
    }
  };

  const metricType = matrixData?.metric_type ?? 'bool';
  const isBoolMetric = metricType === 'bool';
  const availableMetrics: { name: string; result_type: string }[] = matrixData?.available_metrics ?? [];

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
          <Button variant="cta" onClick={handleLaunch} disabled={isLaunching}>
            {isLaunching ? 'Launching...' : 'Launch'}
          </Button>
        </div>
      </PagePane>

      <PagePane variant="card">
        <div className="flex justify-between items-start gap-4 mb-4 flex-wrap">
          <div>
            <Heading level={2}>Response Matrix</Heading>
            {matrixData && (
              <Text variant="muted" className="text-sm mt-2 max-w-2xl">
                {isBoolMetric ? (
                  <>
                    Bool metric — IRT logistic fit:{' '}
                    <span className="font-mono">P(pass) = σ(θ<sub>model</sub> − b<sub>case</sub>)</span>
                    {' '}(σ = logistic). True = pass by rubric convention.
                  </>
                ) : (
                  <>
                    Numeric metric — regression fit:{' '}
                    <span className="font-mono">score ~ θ<sub>model</sub> − b<sub>case</sub> + N(0, σ<sub>error</sub>)</span>
                    . Higher is better by rubric convention.
                  </>
                )}
              </Text>
            )}
          </div>
          <div className="flex gap-4 flex-wrap">
            <Select
              fullWidth={false}
              aria-label="Campaign"
              value={selectedCampaignId}
              onChange={e => handleSelectCampaign(e.target.value)}
            >
              <option value="">Select Campaign...</option>
              {campaigns.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </Select>
            <Select
              fullWidth={false}
              aria-label="Metric"
              value={selectedMetric}
              disabled={!matrixData || availableMetrics.length === 0}
              onChange={e => handleSelectMetric(e.target.value)}
            >
              {availableMetrics.length === 0 ? (
                <option value="">No metrics</option>
              ) : (
                availableMetrics.map(m => (
                  <option key={m.name} value={m.name}>
                    {m.name} ({m.result_type})
                  </option>
                ))
              )}
            </Select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse min-w-max">
            <thead className="bg-surface-container-low border-b border-outline-variant text-on-surface-variant">
              <tr>
                <th className="p-3 font-bold sticky left-0 bg-surface-container-low">Model</th>
                {matrixData?.case_ids.map((cid: string) => (
                  <th
                    key={cid}
                    className="p-2 font-mono text-xs text-center min-w-[3.5rem] max-w-[5rem]"
                    title={cid}
                  >
                    {shortCaseId(cid)}
                  </th>
                ))}
                <th className="p-3 font-bold text-right border-l border-outline-variant whitespace-nowrap">
                  Ability θ
                </th>
              </tr>
            </thead>
            <tbody>
              {matrixData ? (
                matrixData.models.map((m: string, i: number) => (
                  <tr key={i} className="matrix-row border-b border-outline-variant/50">
                    <td className="p-3 font-medium text-on-surface font-mono sticky left-0 bg-surface-container">
                      {m}
                    </td>
                    {matrixData.case_ids.map((cid: string) => {
                      const key = `${m}|${cid}`;
                      const val = matrixData.cell[key];
                      const hasValue = Object.prototype.hasOwnProperty.call(matrixData.cell, key);
                      return (
                        <td key={cid} className="p-1 text-center">
                          <div
                            className="w-8 h-8 mx-auto rounded-sm border border-outline-variant/30 flex items-center justify-center text-[10px] font-mono text-on-surface"
                            style={{
                              backgroundColor: hasValue
                                ? cellColor(val, metricType)
                                : 'transparent',
                            }}
                            title={
                              hasValue
                                ? `${cid}: ${isBoolMetric ? (val > 0.5 ? 'pass' : 'fail') : val.toFixed(2)}`
                                : `${cid}: no score`
                            }
                          >
                            {!hasValue ? '—' : !isBoolMetric ? val.toFixed(1) : ''}
                          </div>
                        </td>
                      );
                    })}
                    <td className="p-3 text-right font-mono border-l border-outline-variant text-on-surface">
                      {matrixData.ability?.[m]?.toFixed(2) ?? '—'}
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
                  <td className="p-3 font-bold sticky left-0 bg-surface-container-low whitespace-nowrap">
                    Difficulty b
                  </td>
                  {matrixData.case_ids.map((cid: string) => (
                    <td key={cid} className="p-2 text-center font-mono text-xs" title={cid}>
                      {matrixData.difficulty?.[cid] != null
                        ? matrixData.difficulty[cid].toFixed(2)
                        : '—'}
                    </td>
                  ))}
                  <td className="p-3 border-l border-outline-variant" />
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </PagePane>
    </PageContainer>
  );
}
