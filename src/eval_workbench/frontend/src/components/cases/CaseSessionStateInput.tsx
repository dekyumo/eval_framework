import { FormLabel, Text, Heading } from '../ui/Typography';
import { Textarea } from '../ui/Textarea';

interface CaseSessionStateInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function CaseSessionStateInput({ value, onChange }: CaseSessionStateInputProps) {
  return (
    <div className="space-y-2">
      <Heading level={4} className="text-sm font-semibold text-on-surface-variant">
        Session State
      </Heading>
      <FormLabel htmlFor="session_state_json">Session State (JSON)</FormLabel>
      <Textarea
        id="session_state_json"
        data-testid="session-state-json"
        className="h-28 font-mono text-xs"
        placeholder={'{\n  "destination": "Acapulco",\n  "user:name": "John Smith"\n}'}
        value={value}
        onChange={e => onChange(e.target.value)}
      />
      <Text variant="muted" as="p" className="text-xs">
        Injected into the ADK session before the run. Validated as JSON when you save.
      </Text>
    </div>
  );
}
