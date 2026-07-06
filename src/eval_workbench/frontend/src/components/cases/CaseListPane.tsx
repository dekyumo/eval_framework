import type { ReactNode } from 'react';
import { SplitBadge } from '../SplitBadge';
import { Text, Heading } from '../ui/Typography';

interface CaseDetailViewProps {
  caseData: Record<string, unknown>;
}

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <div className="grid grid-cols-[10rem_1fr] gap-2 text-sm">
      <Text variant="muted" as="span" className="font-medium">{label}</Text>
      <Text variant="body" as="span" className="break-all">{value}</Text>
    </div>
  );
}

export function CaseDetailView({ caseData }: CaseDetailViewProps) {
  const conversation = caseData.conversation as unknown[] | undefined;
  const metrics = caseData.metrics as unknown[] | undefined;
  const sessionState = caseData.session_state as Record<string, unknown> | undefined;
  const inputPayload = caseData.input_payload as Record<string, unknown> | undefined;
  const toolFault = caseData.tool_fault as Record<string, unknown> | undefined;

  return (
    <div
      className="mt-4 p-4 bg-surface-container-lowest border border-outline-variant rounded-md space-y-4"
      data-testid="case-detail-view"
    >
      <Heading level={4} className="text-base font-semibold">
        {(caseData.name as string) || (caseData.id as string)}
      </Heading>

      <div className="space-y-2">
        <DetailRow label="ID" value={String(caseData.id || '')} />
        <DetailRow label="Target agent" value={String(caseData.target_agent_path || '')} />
        <DetailRow label="Distribution" value={String(caseData.distribution_position || '')} />
        <DetailRow label="Problem type" value={String(caseData.problem_type || '')} />
        <DetailRow label="Split" value={String(caseData.split || '')} />
        <DetailRow label="Source" value={String(caseData.source || '')} />
      </div>

      {sessionState && Object.keys(sessionState).length > 0 && (
        <div>
          <Text variant="caption" as="div" className="font-semibold mb-1">
            Session state
          </Text>
          <pre className="text-xs font-mono bg-surface-container-highest p-3 rounded-md overflow-x-auto">
            {JSON.stringify(sessionState, null, 2)}
          </pre>
        </div>
      )}

      {inputPayload && Object.keys(inputPayload).length > 0 && (
        <div>
          <Text variant="caption" as="div" className="font-semibold mb-1">
            Input payload
          </Text>
          <pre className="text-xs font-mono bg-surface-container-highest p-3 rounded-md overflow-x-auto">
            {JSON.stringify(inputPayload, null, 2)}
          </pre>
        </div>
      )}

      {conversation && conversation.length > 0 && (
        <div>
          <Text variant="caption" as="div" className="font-semibold mb-1">
            Conversation ({conversation.length} turn{conversation.length === 1 ? '' : 's'})
          </Text>
          <pre className="text-xs font-mono bg-surface-container-highest p-3 rounded-md overflow-x-auto max-h-48">
            {JSON.stringify(conversation, null, 2)}
          </pre>
        </div>
      )}

      {metrics && metrics.length > 0 && (
        <div>
          <Text variant="caption" as="div" className="font-semibold mb-1">
            Metrics ({metrics.length})
          </Text>
          <ul className="text-sm space-y-1">
            {metrics.map((m: any, i: number) => (
              <li key={m.id || i} className="text-on-surface">
                {m.name} — {m.strategy}
                {m.rubric_ref ? ` → ${m.rubric_ref}` : ''}
                {m.extractor_ref ? ` → ${m.extractor_ref}` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}

      {toolFault && (
        <DetailRow
          label="Tool fault"
          value={`${toolFault.tool_name} (${toolFault.fault_type})`}
        />
      )}

      <details className="text-xs">
        <summary className="cursor-pointer text-on-surface-variant hover:text-on-surface">
          Raw JSON
        </summary>
        <pre className="mt-2 font-mono bg-surface-container-highest p-3 rounded-md overflow-x-auto max-h-64">
          {JSON.stringify(caseData, null, 2)}
        </pre>
      </details>
    </div>
  );
}

interface CaseListPaneProps {
  cases: any[];
  loading: boolean;
  selectedCaseId: string | null;
  onSelectCase: (caseId: string) => void;
}

export function CaseListPane({
  cases,
  loading,
  selectedCaseId,
  onSelectCase,
}: CaseListPaneProps) {
  const selectedCase = cases.find(c => c.id === selectedCaseId) ?? null;

  return (
    <div className="mt-8 pt-6 border-t border-outline-variant" data-testid="case-list-pane">
      <Heading level={3} className="mb-3">Cases &amp; Evals</Heading>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
        {cases.map(c => (
          <button
            key={c.id}
            type="button"
            data-testid={`case-item-${c.id}`}
            onClick={() => onSelectCase(c.id)}
            className={`p-3 text-left rounded-md border transition-colors ${
              selectedCaseId === c.id
                ? 'bg-surface-container-high border-primary-fixed'
                : 'bg-surface-container-lowest border-outline-variant hover:border-primary-fixed'
            }`}
          >
            <Text variant="body" as="div" className="font-medium text-on-surface mb-1">
              {c.name || c.id}
            </Text>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <SplitBadge split={c.split} />
              <Text variant="mono" as="span" className="text-xs">
                {c.distribution_position} • {c.problem_type}
              </Text>
            </div>
          </button>
        ))}
      </div>
      {cases.length === 0 && !loading && (
        <Text variant="muted" className="italic mt-2 block">
          No cases found. Create one above.
        </Text>
      )}
      {selectedCase && <CaseDetailView caseData={selectedCase} />}
    </div>
  );
}
