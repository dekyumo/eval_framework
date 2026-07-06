import { AgentPromptInput } from '../ui/AgentPromptInput';
import { FormLabel } from '../ui/Typography';
import { SnapshotSelect } from '../SnapshotSelect';
import { BorderedSection } from '../ui/PageLayout';
import { Heading } from '../ui/Typography';
import type { SnapshotLike } from '../../utils/snapshotLabel';

interface CaseGenerationPaneProps {
  snapshots: SnapshotLike[];
  snapshotId: string;
  onSnapshotChange: (id: string) => void;
  caseAgentPrompt: string;
  onPromptChange: (value: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

export function CaseGenerationPane({
  snapshots,
  snapshotId,
  onSnapshotChange,
  caseAgentPrompt,
  onPromptChange,
  onGenerate,
  isGenerating,
}: CaseGenerationPaneProps) {
  return (
    <BorderedSection position="top" data-testid="case-generation-pane">
      <Heading level={3} className="mb-3">Automatic Case Generation</Heading>
      <div className="bg-surface-container-low border border-outline-variant rounded-md p-4 space-y-4">
        <div>
          <FormLabel htmlFor="case_snapshot">Snapshot</FormLabel>
          <SnapshotSelect
            id="case_snapshot"
            aria-label="Snapshot"
            value={snapshotId}
            onChange={e => onSnapshotChange(e.target.value)}
            snapshots={snapshots}
            placeholder="Select snapshot..."
          />
        </div>

        <AgentPromptInput
          data-testid="case-generator"
          title="Ask Assistant Agent to draft an eval case"
          placeholder="e.g. Plan a day in Tokyo with a $300 budget, in-distribution happy path"
          value={caseAgentPrompt}
          onChange={onPromptChange}
          onSubmit={onGenerate}
          isLoading={isGenerating}
          submitLabel="Generate Case"
          inputAriaLabel="Case generation prompt"
        />
      </div>
    </BorderedSection>
  );
}
