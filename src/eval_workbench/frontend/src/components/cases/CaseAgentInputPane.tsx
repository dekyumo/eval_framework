import { BorderedSection } from '../ui/PageLayout';
import { Heading } from '../ui/Typography';
import { CaseDirectInput } from './CaseDirectInput';
import { CaseSessionStateInput } from './CaseSessionStateInput';
import type { ConversationTurn, InputMode } from './types';

interface CaseAgentInputPaneProps {
  inputMode: InputMode;
  onInputModeChange: (mode: InputMode) => void;
  sessionStateJson: string;
  onSessionStateChange: (value: string) => void;
  inputPayloadJson: string;
  onInputPayloadChange: (value: string) => void;
  turns: ConversationTurn[];
  onAddTurn: () => void;
  onRemoveTurn: (index: number) => void;
  onTurnChange: (index: number, field: string, value: string) => void;
  onMediaUpload: (index: number, file: File | null) => void;
  jsonError: string | null;
}

export function CaseAgentInputPane(props: CaseAgentInputPaneProps) {
  const {
    sessionStateJson,
    onSessionStateChange,
    ...directProps
  } = props;

  return (
    <BorderedSection position="top" data-testid="advanced-agent-input">
      <Heading level={3} className="mb-3">Agent Input</Heading>
      <div className="bg-surface-container-low border border-outline-variant rounded-md p-4 flex flex-col gap-6">
        {/* DOM: state first so conversation textareas stay last (e2e uses textarea.last()) */}
        <div className="order-2">
          <CaseSessionStateInput value={sessionStateJson} onChange={onSessionStateChange} />
        </div>
        <div className="order-1">
          <CaseDirectInput {...directProps} />
        </div>
      </div>
    </BorderedSection>
  );
}
