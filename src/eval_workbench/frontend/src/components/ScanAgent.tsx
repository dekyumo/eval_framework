import { useState, useEffect } from 'react';
import { Button } from './ui/Button';
import { FormLabel } from './ui/Typography';

const AGENT_PATH_KEY = 'eval_workbench_agent_path';
const COMMIT_KEY = 'eval_workbench_commit';

type ScanAgentProps = {
  onScanned: (snapshotId: string) => void;
};

export function ScanAgent({ onScanned }: ScanAgentProps) {
  const [repo, setRepo] = useState('');
  const [agentPath, setAgentPath] = useState(
    () => localStorage.getItem(AGENT_PATH_KEY) || '',
  );
  const [commit, setCommit] = useState(
    () => localStorage.getItem(COMMIT_KEY) || 'HEAD',
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/repo')
      .then(res => res.json())
      .then(data => {
        if (data.repo_path) setRepo(data.repo_path);
      })
      .catch(console.error);
  }, []);

  const handleAgentPathChange = (value: string) => {
    setAgentPath(value);
    localStorage.setItem(AGENT_PATH_KEY, value);
  };

  const handleCommitChange = (value: string) => {
    setCommit(value);
    localStorage.setItem(COMMIT_KEY, value);
  };

  const handleScan = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/agents/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_target: { repo_path: repo, agent_path: agentPath, name: 'target' },
          commit,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Failed to scan');
      }
      const snapshot = await res.json();
      onScanned(snapshot.id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to scan');
    } finally {
      setLoading(false);
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
          disabled={loading || !repo || !agentPath}
        >
          {loading ? 'Scanning...' : 'Scan Agent'}
        </Button>
      </div>
      {error && <div className="text-error text-sm">{error}</div>}
    </div>
  );
}
