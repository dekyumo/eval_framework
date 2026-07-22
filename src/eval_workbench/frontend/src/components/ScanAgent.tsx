import { useState, useEffect } from 'react';
import { Button } from './ui/Button';
import { FormLabel } from './ui/Typography';
import { useTasks } from '../context/TaskContext';
import { enqueueScanAgent } from '../lib/jobsApi';

const AGENT_PATH_KEY = 'eval_workbench_agent_path';
const COMMIT_KEY = 'eval_workbench_commit';

type ScanAgentProps = {
  onScanned: (snapshotId: string) => void;
  onScanEnqueued?: () => void;
};

export function ScanAgent({ onScanned, onScanEnqueued }: ScanAgentProps) {
  const [repo, setRepo] = useState('');
  const [agentPath, setAgentPath] = useState(
    () => localStorage.getItem(AGENT_PATH_KEY) || '',
  );
  const [commit, setCommit] = useState(
    () => localStorage.getItem(COMMIT_KEY) || 'HEAD',
  );
  const [error, setError] = useState('');
  const { activeTasks, subscribe } = useTasks();

  const isScanning = activeTasks.some(task => task.type === 'scan_agent');

  useEffect(() => {
    fetch('/api/repo')
      .then(res => res.json())
      .then(data => {
        if (data.repo_path) setRepo(data.repo_path);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    return subscribe('snapshot_scanned', (data) => {
      const snapshot = data.snapshot as { id?: string } | undefined;
      if (snapshot?.id) {
        onScanned(snapshot.id);
      }
    });
  }, [onScanned, subscribe]);

  const handleAgentPathChange = (value: string) => {
    setAgentPath(value);
    localStorage.setItem(AGENT_PATH_KEY, value);
  };

  const handleCommitChange = (value: string) => {
    setCommit(value);
    localStorage.setItem(COMMIT_KEY, value);
  };

  const handleScan = async () => {
    setError('');
    try {
      await enqueueScanAgent(
        { repo_path: repo, agent_path: agentPath, name: 'target' },
        commit,
      );
      onScanEnqueued?.();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to scan');
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-2 min-w-[280px] flex-1">
          <FormLabel className="font-mono text-xs uppercase tracking-widest text-on-surface-variant">
            Agent path
          </FormLabel>
          <input
            aria-label="Agent path"
            className="w-full bg-surface-container-lowest border border-outline-variant rounded-md py-2 px-3 text-on-surface font-mono text-sm focus:border-primary-fixed outline-none"
            value={agentPath}
            onChange={e => handleAgentPathChange(e.target.value)}
            placeholder="src.agent:my_agent"
          />
        </div>
        <div className="flex flex-col gap-2 w-40">
          <FormLabel className="font-mono text-xs uppercase tracking-widest text-on-surface-variant">
            Commit / ref
          </FormLabel>
          <input
            aria-label="Commit"
            className="w-full bg-surface-container-lowest border border-outline-variant rounded-md py-2 px-3 text-on-surface font-mono text-sm focus:border-primary-fixed outline-none"
            value={commit}
            onChange={e => handleCommitChange(e.target.value)}
          />
        </div>
        <Button
          variant="cta"
          onClick={handleScan}
          disabled={isScanning || !repo || !agentPath}
        >
          {isScanning ? 'Scanning...' : 'Scan Agent'}
        </Button>
      </div>
      {error && <div className="text-error text-sm">{error}</div>}
    </div>
  );
}
