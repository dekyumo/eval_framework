import { BorderedSection } from '../ui/PageLayout';
import { Heading, FormLabel, Text } from '../ui/Typography';
import { Select } from '../ui/Select';

interface Gym {
  id: string;
  name: string;
}

interface CaseAgenticUserPaneProps {
  enabled: boolean;
  onEnabledChange: (enabled: boolean) => void;
  userAgentPath: string;
  onUserAgentPathChange: (value: string) => void;
  gymRef: string;
  onGymRefChange: (value: string) => void;
  userTools: string;
  onUserToolsChange: (value: string) => void;
  solverTools: string;
  onSolverToolsChange: (value: string) => void;
  maxTurns: number;
  onMaxTurnsChange: (value: number) => void;
  terminationMethod: string;
  onTerminationMethodChange: (value: string) => void;
  gyms: Gym[];
}

const INFO = 'Gym methods are bound methods exposed as tools. Configure the gym\'s initial state under the reserved "gym" key in Session State.';

const inputClass =
  'w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed';

export function CaseAgenticUserPane({
  enabled,
  onEnabledChange,
  userAgentPath,
  onUserAgentPathChange,
  gymRef,
  onGymRefChange,
  userTools,
  onUserToolsChange,
  solverTools,
  onSolverToolsChange,
  maxTurns,
  onMaxTurnsChange,
  terminationMethod,
  onTerminationMethodChange,
  gyms,
}: CaseAgenticUserPaneProps) {
  return (
    <BorderedSection position="top" data-testid="agentic-user-pane">
      <div className="mb-3 flex items-center gap-2">
        <Heading level={3}>Agentic User</Heading>
        <span
          className="text-on-surface-variant text-xs border border-outline-variant rounded-full w-4 h-4 inline-flex items-center justify-center cursor-help select-none"
          title={INFO}
        >
          ?
        </span>
      </div>
      <div className="bg-surface-container-low border border-outline-variant rounded-md p-4 space-y-4">
        <div>
          <FormLabel htmlFor="agentic_user_mode">Mode</FormLabel>
          <Select
            id="agentic_user_mode"
            aria-label="Agentic user mode"
            data-testid="agentic-user-section"
            value={enabled ? 'enabled' : 'none'}
            onChange={e => onEnabledChange(e.target.value === 'enabled')}
          >
            <option value="none">None</option>
            <option value="enabled">Agentic User (user_agent, gym)</option>
          </Select>
        </div>

        {enabled && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <FormLabel htmlFor="agentic_user_agent_path">User Agent Path</FormLabel>
                <input
                  id="agentic_user_agent_path"
                  aria-label="User agent path"
                  className={`${inputClass} font-mono`}
                  value={userAgentPath}
                  onChange={e => onUserAgentPathChange(e.target.value)}
                  placeholder="module.path:variable"
                />
              </div>
              <div>
                <FormLabel htmlFor="agentic_gym_ref">Gym</FormLabel>
                <Select
                  id="agentic_gym_ref"
                  aria-label="Gym"
                  value={gymRef}
                  onChange={e => onGymRefChange(e.target.value)}
                >
                  <option value="">Select a gym…</option>
                  {gyms.map(g => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <FormLabel htmlFor="agentic_user_tools">User Tools</FormLabel>
                <input
                  id="agentic_user_tools"
                  aria-label="User tools"
                  className={inputClass}
                  value={userTools}
                  onChange={e => onUserToolsChange(e.target.value)}
                  placeholder="e.g. get_context, ask"
                />
                <Text variant="muted" as="p" className="text-xs mt-1">
                  comma-separated gym method names
                </Text>
              </div>
              <div>
                <FormLabel htmlFor="agentic_solver_tools">Solver Tools</FormLabel>
                <input
                  id="agentic_solver_tools"
                  aria-label="Solver tools"
                  className={inputClass}
                  value={solverTools}
                  onChange={e => onSolverToolsChange(e.target.value)}
                  placeholder="e.g. book_flight, cancel"
                />
                <Text variant="muted" as="p" className="text-xs mt-1">
                  comma-separated gym method names
                </Text>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <FormLabel htmlFor="agentic_max_turns">Max Turns</FormLabel>
                <input
                  id="agentic_max_turns"
                  type="number"
                  aria-label="Max turns"
                  className={inputClass}
                  value={maxTurns}
                  onChange={e => onMaxTurnsChange(Number(e.target.value))}
                />
              </div>
              <div>
                <FormLabel htmlFor="agentic_termination_method">Termination Method</FormLabel>
                <input
                  id="agentic_termination_method"
                  aria-label="Termination method"
                  className={`${inputClass} font-mono`}
                  value={terminationMethod}
                  onChange={e => onTerminationMethodChange(e.target.value)}
                  placeholder="gym method returning bool"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </BorderedSection>
  );
}
