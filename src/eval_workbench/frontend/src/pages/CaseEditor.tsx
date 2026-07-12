import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { PageContainer, PagePane } from '../components/ui/PageLayout';
import { CaseGenerationPane } from '../components/cases/CaseGenerationPane';
import { CaseAgentInputPane } from '../components/cases/CaseAgentInputPane';
import { CaseAgenticUserPane } from '../components/cases/CaseAgenticUserPane';
import { CaseOthersPane } from '../components/cases/CaseOthersPane';
import { useCaseEditor } from '../hooks/useCaseEditor';
import { formStateToPayload, apiCaseToFormState } from '../lib/caseForm';
import { Heading, Text } from '../components/ui/Typography';

type EditorIntent = 'create' | 'edit' | 'duplicate' | 'version';

interface CaseImpact {
  run_count: number;
  snapshot_count: number;
  scored_count: number;
}

export function CaseEditor() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const intent = (searchParams.get('intent') || 'create') as EditorIntent;
  const sourceCaseId = searchParams.get('caseId');

  const [datasets, setDatasets] = useState<any[]>([]);
  const [rubrics, setRubrics] = useState<any[]>([]);
  const [extractors, setExtractors] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [gyms, setGyms] = useState<any[]>([]);
  const [snapshotId, setSnapshotId] = useState('');
  const [caseAgentPrompt, setCaseAgentPrompt] = useState('');
  const [isGeneratingCase, setIsGeneratingCase] = useState(false);
  const [loading, setLoading] = useState(intent !== 'create');
  const [sourceCaseIdForVersion, setSourceCaseIdForVersion] = useState<string | null>(null);
  const [impact, setImpact] = useState<CaseImpact | null>(null);
  const [showImpactDialog, setShowImpactDialog] = useState(false);

  const editor = useCaseEditor();

  useEffect(() => {
    Promise.all([
      fetch('/api/registries/datasets').then(res => res.json()),
      fetch('/api/registries/rubrics').then(res => res.json()),
      fetch('/api/registries/extractors').then(res => res.json()),
      fetch('/api/agents/snapshots').then(res => res.json()),
      fetch('/api/registries/gyms').then(res => res.json()),
    ]).then(([datasetsData, rubricsData, extractorsData, snapshotsData, gymsData]) => {
      if (Array.isArray(datasetsData)) {
        setDatasets(datasetsData);
        if (datasetsData.length > 0 && intent === 'create') {
          editor.setDatasetId(datasetsData[0].id);
        }
      }
      if (Array.isArray(rubricsData)) setRubrics(rubricsData);
      if (Array.isArray(extractorsData)) setExtractors(extractorsData);
      if (Array.isArray(snapshotsData)) {
        setSnapshots(snapshotsData);
        if (snapshotsData.length > 0) setSnapshotId(snapshotsData[0].id);
      }
      if (Array.isArray(gymsData)) setGyms(gymsData);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (!sourceCaseId || intent === 'create') {
      setLoading(false);
      return;
    }

    setLoading(true);
    fetch(`/api/cases/${sourceCaseId}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          console.error(data.error);
          return;
        }
        const state = apiCaseToFormState(data);
        if (intent === 'duplicate') {
          state.editingCaseId = null;
          state.caseName = `${state.caseName || data.id} (copy)`;
        } else if (intent === 'version') {
          state.editingCaseId = null;
          setSourceCaseIdForVersion(sourceCaseId);
        }
        editor.loadFormState(state);
      })
      .finally(() => setLoading(false));
  }, [sourceCaseId, intent]);

  const pageTitle = useMemo(() => {
    switch (intent) {
      case 'edit':
        return 'Edit case';
      case 'duplicate':
        return 'Duplicate case';
      case 'version':
        return 'New version';
      default:
        return 'Create case';
    }
  }, [intent]);

  const saveButtonLabel = useMemo(() => {
    switch (intent) {
      case 'edit':
        return 'Save changes';
      case 'duplicate':
        return 'Save duplicate';
      case 'version':
        return 'Save case — new version';
      default:
        return 'Save case';
    }
  }, [intent]);

  const rubricResultType = (rubricRef: string) => {
    const rubric = rubrics.find(r => r.id === rubricRef);
    return rubric?.items?.[0]?.type || 'bool';
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
      editor.applyGeneratedCase(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsGeneratingCase(false);
    }
  };

  const validateBeforeSave = () => {
    editor.setJsonError(null);
    if (!editor.form.datasetId) {
      editor.setJsonError('Select a dataset before saving.');
      return false;
    }
    for (const turn of editor.form.turns) {
      if (turn.role === 'user_media' && !turn.media_base64) {
        editor.setJsonError('Wait for the media upload to finish before saving.');
        return false;
      }
    }
    return true;
  };

  const savePayload = (options?: { newId?: string; fromVersionOf?: string }) => {
    return formStateToPayload(editor.form, rubricResultType, options);
  };

  const finishSave = (savedId: string) => {
    navigate(`/cases?highlight=${savedId}`);
  };

  const performPost = async (options?: { newId?: string; fromVersionOf?: string }) => {
    const payload = savePayload(options);
    const res = await fetch('/api/cases/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      editor.setJsonError(data.error || 'Save failed');
      return;
    }
    finishSave(data.id);
  };

  const performPut = async (cascade: boolean) => {
    const caseId = editor.form.editingCaseId;
    if (!caseId) return;
    const payload = savePayload();
    delete payload.id;
    delete payload.from_version_of;
    const res = await fetch(`/api/cases/${caseId}?cascade=${cascade ? 'true' : 'false'}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      editor.setJsonError(data.error || 'Update failed');
      return;
    }
    finishSave(caseId);
  };

  const handleSaveCase = async () => {
    if (!validateBeforeSave()) return;

    try {
      savePayload();
    } catch (err) {
      editor.setJsonError(err instanceof Error ? err.message : 'Invalid JSON');
      return;
    }

    if (intent === 'edit' && editor.form.editingCaseId) {
      const impactRes = await fetch(`/api/cases/${editor.form.editingCaseId}/impact`);
      const impactData = await impactRes.json();
      if (impactData.run_count > 0) {
        setImpact(impactData);
        setShowImpactDialog(true);
        return;
      }
      try {
        await performPut(false);
      } catch (err) {
        editor.setJsonError(err instanceof Error ? err.message : 'Save failed');
      }
      return;
    }

    if (intent === 'version' && sourceCaseIdForVersion) {
      try {
        await performPost({
          newId: `case_${crypto.randomUUID().substring(0, 8)}`,
          fromVersionOf: sourceCaseIdForVersion,
        });
      } catch (err) {
        editor.setJsonError(err instanceof Error ? err.message : 'Save failed');
      }
      return;
    }

    try {
      await performPost({
        newId: `case_${crypto.randomUUID().substring(0, 8)}`,
      });
    } catch (err) {
      editor.setJsonError(err instanceof Error ? err.message : 'Save failed');
    }
  };

  const handleForceModify = async () => {
    setShowImpactDialog(false);
    try {
      await performPut(true);
    } catch (err) {
      editor.setJsonError(err instanceof Error ? err.message : 'Save failed');
    }
  };

  const handleSaveAsNewVersion = async () => {
    setShowImpactDialog(false);
    if (!editor.form.editingCaseId) return;
    try {
      await performPost({
        newId: `case_${crypto.randomUUID().substring(0, 8)}`,
        fromVersionOf: editor.form.editingCaseId,
      });
    } catch (err) {
      editor.setJsonError(err instanceof Error ? err.message : 'Save failed');
    }
  };

  if (loading) {
    return (
      <PageContainer variant="standard">
        <Text variant="muted">Loading case…</Text>
      </PageContainer>
    );
  }

  return (
    <PageContainer variant="standard">
      <PagePane
        variant="content"
        title={pageTitle}
        headerActions={
          <div className="flex gap-2">
            <Button variant="normal" size="sm" onClick={() => navigate('/cases')}>
              Cancel
            </Button>
            <Button variant="normal" className="new-case-btn" size="sm" onClick={() => editor.reset(editor.form.datasetId)}>
              Clear Form
            </Button>
          </div>
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
            inputMode={editor.form.inputMode}
            onInputModeChange={editor.setInputMode}
            sessionStateJson={editor.form.sessionStateJson}
            onSessionStateChange={editor.setSessionStateJson}
            inputPayloadJson={editor.form.inputPayloadJson}
            onInputPayloadChange={editor.setInputPayloadJson}
            turns={editor.form.turns}
            onAddTurn={editor.handleAddTurn}
            onRemoveTurn={editor.handleRemoveTurn}
            onTurnChange={editor.handleTurnChange}
            onMediaUpload={editor.handleMediaUpload}
            jsonError={editor.jsonError}
          />

          <CaseAgenticUserPane
            enabled={editor.form.agenticEnabled}
            onEnabledChange={editor.setAgenticEnabled}
            userAgentPath={editor.form.userAgentPath}
            onUserAgentPathChange={editor.setUserAgentPath}
            gymRef={editor.form.agenticGymRef}
            onGymRefChange={editor.setAgenticGymRef}
            userTools={editor.form.agenticUserTools}
            onUserToolsChange={editor.setAgenticUserTools}
            solverTools={editor.form.agenticSolverTools}
            onSolverToolsChange={editor.setAgenticSolverTools}
            maxTurns={editor.form.agenticMaxTurns}
            onMaxTurnsChange={editor.setAgenticMaxTurns}
            terminationMethod={editor.form.agenticTerminationMethod}
            onTerminationMethodChange={editor.setAgenticTerminationMethod}
            gyms={gyms}
          />

          <CaseOthersPane
            caseName={editor.form.caseName}
            onCaseNameChange={editor.setCaseName}
            datasetId={editor.form.datasetId}
            onDatasetChange={editor.setDatasetId}
            datasets={datasets}
            distributionPosition={editor.form.distributionPosition}
            onDistributionChange={editor.setDistributionPosition}
            problemType={editor.form.problemType}
            onProblemTypeChange={editor.setProblemType}
            split={editor.form.split}
            onSplitChange={editor.setSplit}
            metrics={editor.form.metrics}
            onMetricsChange={editor.setMetrics}
            rubrics={rubrics}
            extractors={extractors}
            toolFaultEnabled={editor.form.toolFaultEnabled}
            onToolFaultEnabledChange={editor.setToolFaultEnabled}
            toolFaultName={editor.form.toolFaultName}
            onToolFaultNameChange={editor.setToolFaultName}
            toolFaultType={editor.form.toolFaultType}
            onToolFaultTypeChange={editor.setToolFaultType}
          />

          <Button variant="cta" size="lg" onClick={handleSaveCase}>
            {saveButtonLabel}
          </Button>
        </div>
      </PagePane>

      {showImpactDialog && impact && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-outline-variant rounded-lg p-6 max-w-md w-full space-y-4">
            <Heading level={3}>Existing evals on this case</Heading>
            <Text variant="body">
              This case has {impact.run_count} run(s) across {impact.snapshot_count} snapshot(s)
              ({impact.scored_count} scored). Choose how to proceed.
            </Text>
            <div className="flex flex-col gap-2">
              <Button variant="cta" onClick={handleForceModify}>
                Force modify (delete runs and update)
              </Button>
              <Button variant="normal" onClick={handleSaveAsNewVersion}>
                Save as new version
              </Button>
              <Button variant="normal" onClick={() => setShowImpactDialog(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
