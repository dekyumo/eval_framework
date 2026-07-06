import { Select, type SelectProps } from './ui/Select';
import { formatSnapshotLabel, type SnapshotLike } from '../utils/snapshotLabel';

interface SnapshotSelectProps extends Omit<SelectProps, 'children'> {
  snapshots: SnapshotLike[];
  placeholder?: string;
}

export function SnapshotSelect({
  snapshots,
  placeholder = 'Select snapshot...',
  ...selectProps
}: SnapshotSelectProps) {
  return (
    <Select {...selectProps}>
      <option value="">{placeholder}</option>
      {snapshots.map(snapshot => (
        <option key={snapshot.id} value={snapshot.id} title={snapshot.id}>
          {formatSnapshotLabel(snapshot)}
        </option>
      ))}
    </Select>
  );
}
