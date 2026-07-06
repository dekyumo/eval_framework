import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Heading, Text, FormLabel } from '../components/ui/Typography';
import { PageContainer, PagePane } from '../components/ui/PageLayout';

export function Onboarding() {
  const [repo, setRepo] = useState('');
  const [agentPath, setAgentPath] = useState('');
  const [commit, setCommit] = useState('HEAD');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetch('/api/repo')
      .then(res => res.json())
      .then(data => {
        if (data.repo_path) setRepo(data.repo_path);
      })
      .catch(console.error);
  }, []);

  const handleScan = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/agents/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_target: { repo_path: repo, agent_path: agentPath, name: "target" },
          commit: commit
        })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Failed to scan');
      }
      navigate('/agents');
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  return (
    <PageContainer variant="centered">
      <div>
        <Heading level={1}>Add target &amp; scan</Heading>
        <Text variant="muted" className="mt-2">Initialize a new evaluation environment from a local repository.</Text>
      </div>

      <div className="flex flex-col gap-6 relative border-l border-outline-variant ml-4 pl-8 py-2">
        {/* Step 1 */}
        <div className="relative">
          <div className="absolute -left-[41px] top-1 w-6 h-6 rounded-full bg-surface-container-high border-2 border-primary-fixed flex items-center justify-center text-primary-fixed z-10">
            <span className="material-symbols-outlined text-sm font-bold">check</span>
          </div>
          <PagePane variant="card">
            <Heading level={3} className="mb-4">Step 1: Add repository</Heading>
            <div className="flex flex-col gap-2">
              <FormLabel className="font-mono text-xs uppercase tracking-widest text-on-surface-variant">Local Path</FormLabel>
              <input 
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-md py-2 px-3 text-on-surface font-mono text-sm focus:border-primary-fixed outline-none opacity-80 cursor-not-allowed" 
                value={repo}
                readOnly
                placeholder="Loading repository path..."
              />
            </div>
          </PagePane>
        </div>

        {/* Step 2 */}
        <div className="relative">
          <div className="absolute -left-[41px] top-1 w-6 h-6 rounded-full bg-surface-container-high border-2 border-outline-variant flex items-center justify-center text-on-surface-variant z-10">
            <span className="material-symbols-outlined text-sm font-bold">circle</span>
          </div>
          <PagePane variant="card">
            <Heading level={3} className="mb-4">Step 2: Identify agent target</Heading>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <FormLabel className="font-mono text-xs uppercase tracking-widest text-on-surface-variant">Python Module Path</FormLabel>
                <input 
                  className="w-full bg-surface-container-lowest border border-outline-variant rounded-md py-2 px-3 text-on-surface font-mono text-sm focus:border-primary-fixed outline-none" 
                  value={agentPath} onChange={e => setAgentPath(e.target.value)} 
                  placeholder="src.agent:my_agent"
                />
              </div>
              <div className="flex flex-col gap-2">
                <FormLabel className="font-mono text-xs uppercase tracking-widest text-on-surface-variant">Commit / Ref</FormLabel>
                <input 
                  className="w-full bg-surface-container-lowest border border-outline-variant rounded-md py-2 px-3 text-on-surface font-mono text-sm focus:border-primary-fixed outline-none" 
                  value={commit} onChange={e => setCommit(e.target.value)} 
                />
              </div>
            </div>
            <Button 
              variant="cta"
              className="mt-6"
              onClick={handleScan}
              disabled={loading || !repo || !agentPath}
            >
              {loading ? 'Scanning...' : 'Scan Agent'}
            </Button>
            {error && <div className="mt-4 text-error text-sm">{error}</div>}
          </PagePane>
        </div>
      </div>
    </PageContainer>
  );
}
