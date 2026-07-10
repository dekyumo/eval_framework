import { useState, useEffect } from 'react';
import { Button } from '../components/ui/Button';
import { PageContainer, PagePane } from '../components/ui/PageLayout';
import { CaseGenerationPane } from '../components/cases/CaseGenerationPane';
import { CaseAgentInputPane } from '../components/cases/CaseAgentInputPane';
import { CaseAgenticUserPane } from '../components/cases/CaseAgenticUserPane';
import { CaseOthersPane } from '../components/cases/CaseOthersPane';
import { CaseListPane } from '../components/cases/CaseListPane';
import type { ConversationTurn, InputMode, MetricRow } from '../components/cases/types';
import { snapshotAgentPath } from '../utils/snapshotLabel';

function csvToList(text: string): string[] {
  return text.split(',').map(s => s.trim()).filter(Boolean);
}

function parseJsonObject(text: string, label: string): Record<string, unknown> | null {
  if (!text.trim()) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error(`${label} must be valid JSON`);
  }
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    throw new Error(`${label} must be a JSON object`);
  }
  return parsed as Record<string, unknown>;
}

export function Cases() {
  const [cases, setCases] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [rubrics, setRubrics] = useState<any[]>([]);
  const [extractors, setExtractors] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  const [turns, setTurns] = useState<ConversationTurn[]>([{ role: 'user', content: '' }]);
  const [caseName, setCaseName] = useState('');
  const [metrics, setMetrics] = useState<MetricRow[]>([]);
  const [distributionPosition, setDistributionPosition] = useState('in');
  const [problemType, setProblemType] = useState('happy');
  const [split, setSplit] = useState('test');
  const [datasetId, setDatasetId] = useState('');
  const [snapshotId, setSnapshotId] = useState('');
  const [toolFaultEnabled, setToolFaultEnabled] = useState(false);
  const [toolFaultName, setToolFaultName] = useState('google_search');
  const [toolFaultType, setToolFaultType] = useState('interface');
  const [caseAgentPrompt, setCaseAgentPrompt] = useState('');
  const [isGeneratingCase, setIsGeneratingCase] = useState(false);
  const [sessionStateJson, setSessionStateJson] = useState('');
  const [inputMode, setInputMode] = useState<InputMode>('turns');
  const [inputPayloadJson, setInputPayloadJson] = useState('');
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [gyms, setGyms] = useState<any[]>([]);
  const [agenticEnabled, setAgenticEnabled] = useState(false);
  const [userAgentPath, setUserAgentPath] = useState('');
  const [agenticGymRef, setAgenticGymRef] = useState('');
  const [agenticUserTools, setAgenticUserTools] = useState('');
  const [agenticSolverTools, setAgenticSolverTools] = useState('');
  const [agenticMaxTurns, setAgenticMaxTurns] = useState(10);
  const [agenticTerminationMethod, setAgenticTerminationMethod] = useState('');

  useEffect(() => {
    Promise.all([
      fetch('/api/cases').then(res => res.json()),
      fetch('/api/registries/datasets').then(res => res.json()),
      fetch('/api/registries/rubrics').then(res => res.json()),
      fetch('/api/registries/extractors').then(res => res.json()),
      fetch('/api/agents/snapshots').then(res => res.json()),
      fetch('/api/registries/gyms').then(res => res.json()),
    ]).then(([casesData, datasetsData, rubricsData, extractorsData, snapshotsData, gymsData]) => {
      if (Array.isArray(casesData)) setCases(casesData);
      if (Array.isArray(datasetsData)) {
        setDatasets(datasetsData);
        if (datasetsData.length > 0) setDatasetId(datasetsData[0].id);
      }
      if (Array.isArray(rubricsData)) setRubrics(rubricsData);
      if (Array.isArray(extractorsData)) setExtractors(extractorsData);
      if (Array.isArray(snapshotsData)) {
        setSnapshots(snapshotsData);
        if (snapshotsData.length > 0) setSnapshotId(snapshotsData[0].id);
      }
      if (Array.isArray(gymsData)) setGyms(gymsData);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  const applyGeneratedCase = (draft: any) => {
    if (draft.name) setCaseName(draft.name);
    if (draft.distribution_position) setDistributionPosition(draft.distribution_position);
    if (draft.problem_type) setProblemType(draft.problem_type);
    if (draft.split) setSplit(draft.split);
    if (Array.isArray(draft.conversation) && draft.conversation.length > 0) {
      setInputMode('turns');
      setTurns(
        draft.conversation.map((turn: any) => {
          if (turn.kind === 'media' || turn.role === 'user_media') {
            return {
              role: 'user_media',
              content: turn.text || '',
              media_mime: turn.media_mime || '',
              media_base64: turn.media_base64 || '',
              fileName: turn.text || 'uploaded media',
            };
          }
          return {
            role: turn.role || 'user',
            content: turn.text || turn.content || '',
          };
        })
      );
    }
    if (draft.tool_fault) {
      setToolFaultEnabled(true);
      setToolFaultName(draft.tool_fault.tool_name || 'google_search');
      setToolFaultType(draft.tool_fault.fault_type || 'interface');
    } else {
      setToolFaultEnabled(false);
    }
    if (Array.isArray(draft.metrics)) {
      setMetrics(draft.metrics);
    }
  };

  const handleGenerateCase = async () => {
    if (!caseAgentPrompt.trim() || !snapshotId) return;
    setIsGeneratingCase(true);
    try {
      const res = await fetch('/api/cases/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          snapshot_id: snapshotId,
          specification: caseAgentPrompt,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        console.error(data.error || 'Case generation failed');
        return;
      }
      applyGeneratedCase(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsGeneratingCase(false);
    }
  };

  const resetForm = () => {
    setTurns([{ role: 'user', content: '' }]);
    setCaseName('');
    setMetrics([]);
    setDistributionPosition('in');
    setProblemType('happy');
    setSplit('test');
    setToolFaultEnabled(false);
    setToolFaultName('google_search');
    setToolFaultType('interface');
    setCaseAgentPrompt('');
    setSessionStateJson('');
    setInputMode('turns');
    setInputPayloadJson('');
    setJsonError(null);
    setAgenticEnabled(false);
    setUserAgentPath('');
    setAgenticGymRef('');
    setAgenticUserTools('');
    setAgenticSolverTools('');
    setAgenticMaxTurns(10);
    setAgenticTerminationMethod('');
  };

  const handleAddTurn = () => {
    setTurns([...turns, { role: 'user', content: '' }]);
  };

  const handleTurnChange = (index: number, field: string, value: string) => {
    const newTurns = [...turns];
    newTurns[index] = { ...newTurns[index], [field]: value };
    setTurns(newTurns);
  };

  const handleMediaUpload = (index: number, file: File | null) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || '');
      const base64 = result.includes(',') ? result.split(',')[1] : result;
      const newTurns = [...turns];
      newTurns[index] = {
        ...newTurns[index],
        role: 'user_media',
        media_mime: file.type || 'application/octet-stream',
        media_base64: base64,
        fileName: file.name,
        content: file.name,
      };
      setTurns(newTurns);
    };
    reader.readAsDataURL(file);
  };

  const rubricResultType = (rubricRef: string) => {
    const rubric = rubrics.find(r => r.id === rubricRef);
    return rubric?.items?.[0]?.type || 'bool';
  };

  const conversationPayload = () =>
    turns.map(t => {
      if (t.role === 'user_media') {
        return {
          role: 'user',
          kind: 'media',
          media_mime: t.media_mime,
          media_base64: t.media_base64,
          text: t.fileName || t.content || 'media',
        };
      }
      return { role: t.role, kind: 'text', text: t.content };
    });

  const handleRemoveTurn = (index: number) => {
    setTurns(turns.filter((_, i) => i !== index));
  };

  const handleSaveCase = async () => {
    setJsonError(null);
    for (const turn of turns) {
      if (turn.role === 'user_media' && !turn.media_base64) {
        console.error('Wait for the media upload to finish before saving.');
        return;
      }
    }

    let session_state: Record<string, unknown> | null = null;
    let input_payload: Record<string, unknown> | null = null;
    try {
      session_state = parseJsonObject(sessionStateJson, 'Session state');
      if (inputMode === 'json') {
        input_payload = parseJsonObject(inputPayloadJson, 'Agent input');
        if (!input_payload) {
          setJsonError('Agent input JSON is required when using structured input mode.');
          return;
        }
      }
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : 'Invalid JSON');
      return;
    }

    try {
      const snapshot = snapshots.find(s => s.id === snapshotId);
      const target_agent_path = snapshotAgentPath(snapshot);
      if (!target_agent_path) {
        setJsonError('Select a snapshot in Automatic Case Generation to set the target agent.');
        return;
      }

      const payload = {
        id: `case_${crypto.randomUUID().substring(0, 8)}`,
        name: caseName || 'Unnamed Case',
        dataset_id: datasetId,
        distribution_position: distributionPosition,
        problem_type: problemType,
        split,
        target_agent_path,
        conversation: inputMode === 'json' ? [] : conversationPayload(),
        session_state,
        input_payload,
        metrics: metrics.map(m => {
          if (m.strategy === 'rubric') {
            return {
              id: m.id,
              name: m.name,
              strategy: m.strategy,
              result_type: rubricResultType(m.rubric_ref),
              rubric_ref: m.rubric_ref,
            };
          }
          return {
            id: m.id,
            name: m.name,
            strategy: m.strategy,
            result_type: 'bool',
            extractor_ref: m.extractor_ref,
            ground_truth: m.ground_truth,
            comparator: 'eq',
          };
        }),
        expected_rubrics: [],
        expected_extractors: [],
        tag_ids: [],
        fault_ids: [],
        tool_fault: toolFaultEnabled
          ? { tool_name: toolFaultName, fault_type: toolFaultType }
          : null,
        agentic_user: agenticEnabled
          ? {
              user_agent_path: userAgentPath,
              gym_ref: agenticGymRef,
              user_tools: csvToList(agenticUserTools),
              solver_tools: csvToList(agenticSolverTools),
              max_turns: Number(agenticMaxTurns) || 10,
              termination_method: agenticTerminationMethod,
            }
          : null,
        source: 'manual',
      };
      await fetch('/api/cases/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const res = await fetch('/api/cases');
      const data = await res.json();
      if (Array.isArray(data)) {
        setCases(data);
        setSelectedCaseId(payload.id);
      }

      resetForm();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <PageContainer variant="standard">
      <PagePane
        variant="content"
        title="Edit Case"
        headerActions={
          <Button variant="normal" className="new-case-btn" size="sm" onClick={resetForm}>
            New Case
          </Button>
        }
      >
        <div className="space-y-6">
          <CaseGenerationPane
            snapshots={snapshots}
            snapshotId={snapshotId}
            onSnapshotChange={setSnapshotId}
            caseAgentPrompt={caseAgentPrompt}
            onPromptChange={setCaseAgentPrompt}
            onGenerate={handleGenerateCase}
            isGenerating={isGeneratingCase}
          />

          <CaseAgentInputPane
            inputMode={inputMode}
            onInputModeChange={setInputMode}
            sessionStateJson={sessionStateJson}
            onSessionStateChange={setSessionStateJson}
            inputPayloadJson={inputPayloadJson}
            onInputPayloadChange={setInputPayloadJson}
            turns={turns}
            onAddTurn={handleAddTurn}
            onRemoveTurn={handleRemoveTurn}
            onTurnChange={handleTurnChange}
            onMediaUpload={handleMediaUpload}
            jsonError={jsonError}
          />

          <CaseAgenticUserPane
            enabled={agenticEnabled}
            onEnabledChange={setAgenticEnabled}
            userAgentPath={userAgentPath}
            onUserAgentPathChange={setUserAgentPath}
            gymRef={agenticGymRef}
            onGymRefChange={setAgenticGymRef}
            userTools={agenticUserTools}
            onUserToolsChange={setAgenticUserTools}
            solverTools={agenticSolverTools}
            onSolverToolsChange={setAgenticSolverTools}
            maxTurns={agenticMaxTurns}
            onMaxTurnsChange={setAgenticMaxTurns}
            terminationMethod={agenticTerminationMethod}
            onTerminationMethodChange={setAgenticTerminationMethod}
            gyms={gyms}
          />

          <CaseOthersPane
            caseName={caseName}
            onCaseNameChange={setCaseName}
            datasetId={datasetId}
            onDatasetChange={setDatasetId}
            datasets={datasets}
            distributionPosition={distributionPosition}
            onDistributionChange={setDistributionPosition}
            problemType={problemType}
            onProblemTypeChange={setProblemType}
            split={split}
            onSplitChange={setSplit}
            metrics={metrics}
            onMetricsChange={setMetrics}
            rubrics={rubrics}
            extractors={extractors}
            toolFaultEnabled={toolFaultEnabled}
            onToolFaultEnabledChange={setToolFaultEnabled}
            toolFaultName={toolFaultName}
            onToolFaultNameChange={setToolFaultName}
            toolFaultType={toolFaultType}
            onToolFaultTypeChange={setToolFaultType}
          />

          <Button variant="cta" onClick={handleSaveCase}>
            Save Case
          </Button>

          <CaseListPane
            cases={cases}
            loading={loading}
            selectedCaseId={selectedCaseId}
            onSelectCase={setSelectedCaseId}
          />
        </div>
      </PagePane>
    </PageContainer>
  );
}
