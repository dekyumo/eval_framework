import type { ConversationTurn, InputMode, MetricRow } from '../components/cases/types';

function csvToList(text: string): string[] {
  return text.split(',').map(s => s.trim()).filter(Boolean);
}

export function parseJsonObject(text: string, label: string): Record<string, unknown> | null {
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

export interface CaseFormState {
  editingCaseId: string | null;
  caseName: string;
  datasetId: string;
  turns: ConversationTurn[];
  inputMode: InputMode;
  sessionStateJson: string;
  inputPayloadJson: string;
  metrics: MetricRow[];
  distributionPosition: string;
  problemType: string;
  split: string;
  toolFaultEnabled: boolean;
  toolFaultName: string;
  toolFaultType: string;
  agenticEnabled: boolean;
  userAgentPath: string;
  agenticGymRef: string;
  agenticUserTools: string;
  agenticSolverTools: string;
  agenticMaxTurns: number;
  agenticTerminationMethod: string;
}

export const emptyCaseFormState = (): CaseFormState => ({
  editingCaseId: null,
  caseName: '',
  datasetId: '',
  turns: [{ role: 'user', content: '' }],
  inputMode: 'turns',
  sessionStateJson: '',
  inputPayloadJson: '',
  metrics: [],
  distributionPosition: 'in',
  problemType: 'happy',
  split: 'test',
  toolFaultEnabled: false,
  toolFaultName: 'google_search',
  toolFaultType: 'interface',
  agenticEnabled: false,
  userAgentPath: '',
  agenticGymRef: '',
  agenticUserTools: '',
  agenticSolverTools: '',
  agenticMaxTurns: 10,
  agenticTerminationMethod: '',
});

export function apiCaseToFormState(apiCase: Record<string, unknown>): CaseFormState {
  const state = emptyCaseFormState();
  state.editingCaseId = String(apiCase.id || '');
  state.caseName = String(apiCase.name || '');
  state.datasetId = String(apiCase.dataset_id || '');
  if (apiCase.distribution_position) state.distributionPosition = String(apiCase.distribution_position);
  if (apiCase.problem_type) state.problemType = String(apiCase.problem_type);
  if (apiCase.split) state.split = String(apiCase.split);

  if (apiCase.session_state && typeof apiCase.session_state === 'object') {
    state.sessionStateJson = JSON.stringify(apiCase.session_state, null, 2);
  }
  if (apiCase.input_payload && typeof apiCase.input_payload === 'object') {
    state.inputMode = 'json';
    state.inputPayloadJson = JSON.stringify(apiCase.input_payload, null, 2);
    state.turns = [{ role: 'user', content: '' }];
  } else if (Array.isArray(apiCase.conversation) && apiCase.conversation.length > 0) {
    state.inputMode = 'turns';
    state.turns = apiCase.conversation.map((turn: any) => {
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
    });
  }

  if (apiCase.tool_fault && typeof apiCase.tool_fault === 'object') {
    const fault = apiCase.tool_fault as Record<string, unknown>;
    state.toolFaultEnabled = true;
    state.toolFaultName = String(fault.tool_name || 'google_search');
    state.toolFaultType = String(fault.fault_type || 'interface');
  }

  if (Array.isArray(apiCase.metrics)) {
    state.metrics = apiCase.metrics.map((m: any) => ({
      id: m.id,
      name: m.name,
      strategy: m.strategy,
      result_type: m.result_type || 'bool',
      rubric_ref: m.rubric_ref || '',
      extractor_ref: m.extractor_ref || '',
      ground_truth: m.ground_truth != null ? String(m.ground_truth) : '',
    }));
  }

  if (apiCase.agentic_user && typeof apiCase.agentic_user === 'object') {
    const agentic = apiCase.agentic_user as Record<string, unknown>;
    state.agenticEnabled = true;
    state.userAgentPath = String(agentic.user_agent_path || '');
    state.agenticGymRef = String(agentic.gym_ref || '');
    state.agenticUserTools = Array.isArray(agentic.user_tools) ? agentic.user_tools.join(', ') : '';
    state.agenticSolverTools = Array.isArray(agentic.solver_tools) ? agentic.solver_tools.join(', ') : '';
    state.agenticMaxTurns = Number(agentic.max_turns) || 10;
    state.agenticTerminationMethod = String(agentic.termination_method || '');
  }

  return state;
}

function conversationPayload(turns: ConversationTurn[]) {
  return turns.map(t => {
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
}

export function formStateToPayload(
  state: CaseFormState,
  rubricResultType: (rubricRef: string) => string,
  options?: { newId?: string; fromVersionOf?: string },
): Record<string, unknown> {
  const session_state = parseJsonObject(state.sessionStateJson, 'Session state');
  let input_payload: Record<string, unknown> | null = null;
  if (state.inputMode === 'json') {
    input_payload = parseJsonObject(state.inputPayloadJson, 'Agent input');
    if (!input_payload) {
      throw new Error('Agent input JSON is required when using structured input mode.');
    }
  }

  const payload: Record<string, unknown> = {
    id: options?.newId || state.editingCaseId || `case_${crypto.randomUUID().substring(0, 8)}`,
    name: state.caseName || 'Unnamed Case',
    dataset_id: state.datasetId,
    distribution_position: state.distributionPosition,
    problem_type: state.problemType,
    split: state.split,
    conversation: state.inputMode === 'json' ? [] : conversationPayload(state.turns),
    session_state,
    input_payload,
    metrics: state.metrics.map(m => {
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
    tool_fault: state.toolFaultEnabled
      ? { tool_name: state.toolFaultName, fault_type: state.toolFaultType }
      : null,
    agentic_user: state.agenticEnabled
      ? {
          user_agent_path: state.userAgentPath,
          gym_ref: state.agenticGymRef,
          user_tools: csvToList(state.agenticUserTools),
          solver_tools: csvToList(state.agenticSolverTools),
          max_turns: state.agenticMaxTurns,
          termination_method: state.agenticTerminationMethod,
        }
      : null,
    source: 'manual',
  };

  if (options?.fromVersionOf) {
    payload.from_version_of = options.fromVersionOf;
  }

  return payload;
}

export function applyGeneratedDraftToFormState(
  state: CaseFormState,
  draft: Record<string, unknown>,
): CaseFormState {
  const next = { ...state };
  if (draft.name) next.caseName = String(draft.name);
  if (draft.distribution_position) next.distributionPosition = String(draft.distribution_position);
  if (draft.problem_type) next.problemType = String(draft.problem_type);
  if (draft.split) next.split = String(draft.split);

  if (Array.isArray(draft.conversation) && draft.conversation.length > 0) {
    next.inputMode = 'turns';
    next.turns = draft.conversation.map((turn: any) => {
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
    });
  }

  if (draft.tool_fault) {
    const fault = draft.tool_fault as Record<string, unknown>;
    next.toolFaultEnabled = true;
    next.toolFaultName = String(fault.tool_name || 'google_search');
    next.toolFaultType = String(fault.fault_type || 'interface');
  } else {
    next.toolFaultEnabled = false;
  }

  if (Array.isArray(draft.metrics)) {
    next.metrics = draft.metrics as MetricRow[];
  }

  return next;
}
