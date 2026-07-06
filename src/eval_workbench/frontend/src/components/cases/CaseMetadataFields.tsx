import { FormLabel } from '../ui/Typography';
import { Select } from '../ui/Select';

interface CaseMetadataFieldsProps {
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
}

export function CaseMetadataFields({
  caseName,
  onCaseNameChange,
  datasetId,
  onDatasetChange,
  datasets,
  distributionPosition,
  onDistributionChange,
  problemType,
  onProblemTypeChange,
  split,
  onSplitChange,
}: CaseMetadataFieldsProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <FormLabel htmlFor="case_name">Case Name</FormLabel>
          <input
            id="case_name"
            className="w-full bg-surface-container-highest border border-outline-variant rounded-md p-2 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-fixed text-sm"
            placeholder="e.g. Refund request"
            value={caseName}
            onChange={e => onCaseNameChange(e.target.value)}
          />
        </div>
        <div>
          <FormLabel htmlFor="case_dataset">Dataset</FormLabel>
          <Select
            id="case_dataset"
            aria-label="Dataset"
            value={datasetId}
            onChange={e => onDatasetChange(e.target.value)}
          >
            {datasets.length === 0 && <option value="">No datasets available</option>}
            {datasets.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <FormLabel htmlFor="case_distribution_position">Distribution Position</FormLabel>
          <Select
            id="case_distribution_position"
            aria-label="Distribution Position"
            value={distributionPosition}
            onChange={e => onDistributionChange(e.target.value)}
          >
            <option value="in">in</option>
            <option value="margin">margin</option>
            <option value="ood">ood</option>
          </Select>
        </div>
        <div>
          <FormLabel htmlFor="case_problem_type">Problem Type</FormLabel>
          <Select
            id="case_problem_type"
            aria-label="Problem Type"
            value={problemType}
            onChange={e => onProblemTypeChange(e.target.value)}
          >
            <option value="happy">happy</option>
            <option value="technical">technical</option>
            <option value="adversarial">adversarial</option>
            <option value="client">client</option>
          </Select>
        </div>
        <div>
          <FormLabel htmlFor="case_split">Split</FormLabel>
          <Select
            id="case_split"
            aria-label="Split"
            value={split}
            onChange={e => onSplitChange(e.target.value)}
          >
            <option value="test">test</option>
            <option value="train">train</option>
          </Select>
        </div>
      </div>
    </div>
  );
}
