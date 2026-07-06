import { FormLabel } from '../ui/Typography';
import { Select } from '../ui/Select';

const TOOL_FAULT_TYPES = [
  'availability', 'performance', 'interface', 'correctness', 'partial_failure',
  'determinism', 'ordering', 'consistency', 'precision', 'semantics', 'security',
  'state', 'resource', 'authorization', 'side_effects', 'observability',
];

interface CaseToolFaultSectionProps {
  enabled: boolean;
  onEnabledChange: (enabled: boolean) => void;
  toolName: string;
  onToolNameChange: (value: string) => void;
  faultType: string;
  onFaultTypeChange: (value: string) => void;
}

export function CaseToolFaultSection({
  enabled,
  onEnabledChange,
  toolName,
  onToolNameChange,
  faultType,
  onFaultTypeChange,
}: CaseToolFaultSectionProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-md p-4 space-y-4">
      <div>
        <FormLabel htmlFor="tool_fault_mode">Fault Mode</FormLabel>
        <Select
          id="tool_fault_mode"
          aria-label="Tool fault mode"
          value={enabled ? 'enabled' : 'none'}
          onChange={e => onEnabledChange(e.target.value === 'enabled')}
        >
          <option value="none">None</option>
          <option value="enabled">ToolFault (tool_name, fault_type)</option>
        </Select>
      </div>
      {enabled && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormLabel htmlFor="tool_fault_name">Tool Name</FormLabel>
            <input
              id="tool_fault_name"
              aria-label="Tool fault tool name"
              className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-sm text-on-surface focus:outline-none focus:border-primary-fixed"
              value={toolName}
              onChange={e => onToolNameChange(e.target.value)}
              placeholder="e.g. google_search"
            />
          </div>
          <div>
            <FormLabel htmlFor="tool_fault_type">Fault Type</FormLabel>
            <Select
              id="tool_fault_type"
              aria-label="Tool fault type"
              value={faultType}
              onChange={e => onFaultTypeChange(e.target.value)}
            >
              {TOOL_FAULT_TYPES.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </Select>
          </div>
        </div>
      )}
    </div>
  );
}
