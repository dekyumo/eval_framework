import { useCallback, useState } from 'react';
import type { ConversationTurn, InputMode, MetricRow } from '../components/cases/types';
import {
  apiCaseToFormState,
  applyGeneratedDraftToFormState,
  emptyCaseFormState,
  type CaseFormState,
} from '../lib/caseForm';

export function useCaseEditor(initialDatasetId = '') {
  const [form, setForm] = useState<CaseFormState>(() => {
    const state = emptyCaseFormState();
    if (initialDatasetId) state.datasetId = initialDatasetId;
    return state;
  });
  const [jsonError, setJsonError] = useState<string | null>(null);

  const reset = useCallback((datasetId?: string) => {
    const state = emptyCaseFormState();
    if (datasetId) state.datasetId = datasetId;
    setForm(state);
    setJsonError(null);
  }, []);

  const hydrateFromApiCase = useCallback((apiCase: Record<string, unknown>) => {
    setForm(apiCaseToFormState(apiCase));
    setJsonError(null);
  }, []);

  const loadFormState = useCallback((state: CaseFormState) => {
    setForm(state);
    setJsonError(null);
  }, []);

  const applyGeneratedCase = useCallback((draft: Record<string, unknown>) => {
    setForm(prev => applyGeneratedDraftToFormState(prev, draft));
  }, []);

  const setCaseName = (caseName: string) => setForm(prev => ({ ...prev, caseName }));
  const setDatasetId = (datasetId: string) => setForm(prev => ({ ...prev, datasetId }));
  const setTurns = (turns: ConversationTurn[]) => setForm(prev => ({ ...prev, turns }));
  const setInputMode = (inputMode: InputMode) => setForm(prev => ({ ...prev, inputMode }));
  const setSessionStateJson = (sessionStateJson: string) => setForm(prev => ({ ...prev, sessionStateJson }));
  const setInputPayloadJson = (inputPayloadJson: string) => setForm(prev => ({ ...prev, inputPayloadJson }));
  const setMetrics = (metrics: MetricRow[]) => setForm(prev => ({ ...prev, metrics }));
  const setDistributionPosition = (distributionPosition: string) =>
    setForm(prev => ({ ...prev, distributionPosition }));
  const setProblemType = (problemType: string) => setForm(prev => ({ ...prev, problemType }));
  const setSplit = (split: string) => setForm(prev => ({ ...prev, split }));
  const setToolFaultEnabled = (toolFaultEnabled: boolean) => setForm(prev => ({ ...prev, toolFaultEnabled }));
  const setToolFaultName = (toolFaultName: string) => setForm(prev => ({ ...prev, toolFaultName }));
  const setToolFaultType = (toolFaultType: string) => setForm(prev => ({ ...prev, toolFaultType }));
  const setAgenticEnabled = (agenticEnabled: boolean) => setForm(prev => ({ ...prev, agenticEnabled }));
  const setUserAgentPath = (userAgentPath: string) => setForm(prev => ({ ...prev, userAgentPath }));
  const setAgenticGymRef = (agenticGymRef: string) => setForm(prev => ({ ...prev, agenticGymRef }));
  const setAgenticUserTools = (agenticUserTools: string) => setForm(prev => ({ ...prev, agenticUserTools }));
  const setAgenticSolverTools = (agenticSolverTools: string) =>
    setForm(prev => ({ ...prev, agenticSolverTools }));
  const setAgenticMaxTurns = (agenticMaxTurns: number) => setForm(prev => ({ ...prev, agenticMaxTurns }));
  const setAgenticTerminationMethod = (agenticTerminationMethod: string) =>
    setForm(prev => ({ ...prev, agenticTerminationMethod }));

  const handleAddTurn = () => {
    setForm(prev => ({ ...prev, turns: [...prev.turns, { role: 'user', content: '' }] }));
  };

  const handleRemoveTurn = (index: number) => {
    setForm(prev => ({ ...prev, turns: prev.turns.filter((_, i) => i !== index) }));
  };

  const handleTurnChange = (index: number, field: string, value: string) => {
    setForm(prev => {
      const turns = [...prev.turns];
      turns[index] = { ...turns[index], [field]: value };
      return { ...prev, turns };
    });
  };

  const handleMediaUpload = (index: number, file: File | null) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || '');
      const base64 = result.includes(',') ? result.split(',')[1] : result;
      setForm(prev => {
        const turns = [...prev.turns];
        turns[index] = {
          ...turns[index],
          role: 'user_media',
          media_mime: file.type || 'application/octet-stream',
          media_base64: base64,
          fileName: file.name,
          content: file.name,
        };
        return { ...prev, turns };
      });
    };
    reader.readAsDataURL(file);
  };

  return {
    form,
    jsonError,
    setJsonError,
    reset,
    hydrateFromApiCase,
    loadFormState,
    applyGeneratedCase,
    setCaseName,
    setDatasetId,
    setTurns,
    setInputMode,
    setSessionStateJson,
    setInputPayloadJson,
    setMetrics,
    setDistributionPosition,
    setProblemType,
    setSplit,
    setToolFaultEnabled,
    setToolFaultName,
    setToolFaultType,
    setAgenticEnabled,
    setUserAgentPath,
    setAgenticGymRef,
    setAgenticUserTools,
    setAgenticSolverTools,
    setAgenticMaxTurns,
    setAgenticTerminationMethod,
    handleAddTurn,
    handleRemoveTurn,
    handleTurnChange,
    handleMediaUpload,
  };
}
