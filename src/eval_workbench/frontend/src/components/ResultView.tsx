import { cn } from '../utils/cn';

interface ResultViewProps {
  type: "bool" | "int" | "float" | "enum";
  value: boolean | number | string;
}

export function ResultView({ type, value }: ResultViewProps) {
  if (type === 'bool') {
    return value ? (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-semantic-pass/20 text-semantic-pass font-mono border border-semantic-pass/30">
        PASS
      </span>
    ) : (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-semantic-fail/20 text-semantic-fail font-mono border border-semantic-fail/30">
        FAIL
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-surface-container-highest text-on-surface border border-outline-variant font-mono">
      {value !== undefined && value !== null ? value.toString() : 'None'}
    </span>
  );
}
