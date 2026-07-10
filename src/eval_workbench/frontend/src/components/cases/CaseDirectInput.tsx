import { FormLabel, Text, Heading } from '../ui/Typography';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';
import { CaseConversationBuilder } from './CaseConversationBuilder';
import type { ConversationTurn, InputMode } from './types';

interface CaseDirectInputProps {
  inputMode: InputMode;
  onInputModeChange: (mode: InputMode) => void;
  inputPayloadJson: string;
  onInputPayloadChange: (value: string) => void;
  turns: ConversationTurn[];
  onAddTurn: () => void;
  onRemoveTurn: (index: number) => void;
  onTurnChange: (index: number, field: string, value: string) => void;
  onMediaUpload: (index: number, file: File | null) => void;
  jsonError: string | null;
}

export function CaseDirectInput({
  inputMode,
  onInputModeChange,
  inputPayloadJson,
  onInputPayloadChange,
  turns,
  onAddTurn,
  onRemoveTurn,
  onTurnChange,
  onMediaUpload,
  jsonError,
}: CaseDirectInputProps) {
  return (
    <div className="space-y-4">
      <Heading level={4} className="text-sm font-semibold text-on-surface-variant">
        Direct Input
      </Heading>

      <div>
        <FormLabel htmlFor="input_mode">Agent Input Mode</FormLabel>
        <Select
          id="input_mode"
          aria-label="Agent input mode"
          data-testid="input-mode"
          value={inputMode}
          onChange={e => onInputModeChange(e.target.value as InputMode)}
        >
          <option value="turns">Conversation turns</option>
          <option value="json">Structured JSON input</option>
        </Select>
        <Text variant="muted" as="p" className="mt-1 text-xs">
          Agents that have an input_schema need an input object (the dictionary will be cast to the appropriate pydantic class)
        </Text>
      </div>

      {inputMode === 'json' ? (
        <div>
          <FormLabel htmlFor="input_payload_json">Agent Input (JSON)</FormLabel>
          <Textarea
            id="input_payload_json"
            data-testid="input-payload-json"
            className="h-28 font-mono text-xs"
            placeholder={'{\n  "destination": "Acapulco"\n}'}
            value={inputPayloadJson}
            onChange={e => onInputPayloadChange(e.target.value)}
          />
        </div>
      ) : (
        <div>
          <Heading level={4} className="mb-2 text-sm font-semibold text-on-surface-variant">
            Conversation Builder
          </Heading>
          <CaseConversationBuilder
            turns={turns}
            onAddTurn={onAddTurn}
            onRemoveTurn={onRemoveTurn}
            onTurnChange={onTurnChange}
            onMediaUpload={onMediaUpload}
          />
        </div>
      )}

      {jsonError && (
        <Text variant="body" as="p" className="text-error text-sm" data-testid="json-error">
          {jsonError}
        </Text>
      )}
    </div>
  );
}
