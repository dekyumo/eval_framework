import { Button } from './Button';
import { Heading } from './Typography';

interface AgentPromptInputProps {
  title?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading?: boolean;
  submitLabel?: string;
  inputAriaLabel?: string;
  'data-testid'?: string;
}

export function AgentPromptInput({
  title = 'Ask Assistant Agent',
  placeholder = 'Describe what to generate...',
  value,
  onChange,
  onSubmit,
  isLoading = false,
  submitLabel = 'Generate',
  inputAriaLabel = 'Agent prompt',
  'data-testid': testId,
}: AgentPromptInputProps) {
  return (
    <div
      className="bg-surface-container-low border border-outline-variant rounded-xl p-4 space-y-3"
      data-testid={testId}
    >
      <Heading level={3} className="flex items-center gap-2">
        <span className="text-primary-fixed">🤖</span>
        {title}
      </Heading>
      <div className="flex gap-2">
        <input
          type="text"
          aria-label={inputAriaLabel}
          placeholder={placeholder}
          className="flex-1 bg-surface-container-highest border border-outline-variant rounded-md p-2 text-sm text-on-surface focus:outline-none focus:border-primary-fixed placeholder:text-on-surface-variant/40"
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !isLoading) onSubmit();
          }}
        />
        <Button variant="cta" onClick={onSubmit} disabled={isLoading || !value.trim()}>
          {isLoading ? 'Generating...' : submitLabel}
        </Button>
      </div>
    </div>
  );
}
