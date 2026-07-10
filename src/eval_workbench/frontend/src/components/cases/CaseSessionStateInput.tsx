import { useState } from 'react';
import { FormLabel, Text, Heading } from '../ui/Typography';
import { Textarea } from '../ui/Textarea';
import { Button } from '../ui/Button';

interface CaseSessionStateInputProps {
  value: string;
  onChange: (value: string) => void;
}

const GYM_INFO =
  'Reserved key "gym" holds the gym\'s init config for Agentic User cases; all other keys are injected into the solver\'s ADK session state.';

export function CaseSessionStateInput({ value, onChange }: CaseSessionStateInputProps) {
  const [formatError, setFormatError] = useState<string | null>(null);

  const handleFormat = () => {
    if (!value.trim()) {
      setFormatError(null);
      return;
    }
    try {
      onChange(JSON.stringify(JSON.parse(value), null, 2));
      setFormatError(null);
    } catch (err) {
      setFormatError(err instanceof Error ? err.message : 'Invalid JSON');
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Heading level={4} className="text-sm font-semibold text-on-surface-variant">
            Session State
          </Heading>
          <span
            className="text-on-surface-variant text-xs border border-outline-variant rounded-full w-4 h-4 inline-flex items-center justify-center cursor-help select-none"
            title={GYM_INFO}
          >
            ?
          </span>
        </div>
        <Button variant="ghost" size="sm" onClick={handleFormat}>
          Format JSON
        </Button>
      </div>
      <FormLabel htmlFor="session_state_json">Session State (JSON)</FormLabel>
      <Textarea
        id="session_state_json"
        data-testid="session-state-json"
        className="h-28 font-mono text-xs"
        placeholder={'{\n  "destination": "Acapulco",\n  "user:name": "John Smith"\n}'}
        value={value}
        onChange={e => onChange(e.target.value)}
      />
      {formatError && (
        <Text as="p" className="text-xs text-semantic-fail">
          {formatError}
        </Text>
      )}
      <Text variant="muted" as="p" className="text-xs">
        Injected into the ADK session before the run. Validated as JSON when you save.
      </Text>
    </div>
  );
}
