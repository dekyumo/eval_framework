import { BorderedSection } from '../ui/PageLayout';
import { Heading } from '../ui/Typography';
import { CaseMetadataFields } from './CaseMetadataFields';
import { CaseMetricsSection } from './CaseMetricsSection';
import { CaseToolFaultSection } from './CaseToolFaultSection';
import type { MetricRow } from './types';

interface CaseOthersPaneProps {
  caseName: string;
  onCaseNameChange: (value: string) => void;
  datasetId: string;
  onDatasetChange: (value: string) => void;
  datasets: { id: string; name: string }[];
  distributionPosition: string;
  onDistributionChange: (value: string) => void;
  problemType: string;
  onProblemTypeChange: (value: string) => void;
  split: string;
  onSplitChange: (value: string) => void;
  metrics: MetricRow[];
  onMetricsChange: (metrics: MetricRow[]) => void;
  rubrics: { id: string; name: string; items?: { type: string }[] }[];
  extractors: { id: string; name: string }[];
  toolFaultEnabled: boolean;
  onToolFaultEnabledChange: (enabled: boolean) => void;
  toolFaultName: string;
  onToolFaultNameChange: (value: string) => void;
  toolFaultType: string;
  onToolFaultTypeChange: (value: string) => void;
}

export function CaseOthersPane(props: CaseOthersPaneProps) {
  const {
    metrics,
    onMetricsChange,
    rubrics,
    extractors,
    toolFaultEnabled,
    onToolFaultEnabledChange,
    toolFaultName,
    onToolFaultNameChange,
    toolFaultType,
    onToolFaultTypeChange,
    ...metadataProps
  } = props;

  return (
    <BorderedSection position="top" data-testid="case-others-pane">
      <Heading level={3} className="mb-3">Case Type &amp; Evaluation</Heading>
      <div className="space-y-6">
        <div>
          <Heading level={4} className="mb-3 text-sm font-semibold text-on-surface-variant">
            Case Type
          </Heading>
          <CaseMetadataFields {...metadataProps} />
        </div>

        <div>
          <Heading level={4} className="mb-3 text-sm font-semibold text-on-surface-variant">
            Metrics
          </Heading>
          <CaseMetricsSection
            metrics={metrics}
            rubrics={rubrics}
            extractors={extractors}
            onChange={onMetricsChange}
          />
        </div>

        <div data-testid="tool-fault-section">
          <Heading level={4} className="mb-3 text-sm font-semibold text-on-surface-variant">
            Tool Fault Injection
          </Heading>
          <CaseToolFaultSection
            enabled={toolFaultEnabled}
            onEnabledChange={onToolFaultEnabledChange}
            toolName={toolFaultName}
            onToolNameChange={onToolFaultNameChange}
            faultType={toolFaultType}
            onFaultTypeChange={onToolFaultTypeChange}
          />
        </div>
      </div>
    </BorderedSection>
  );
}
