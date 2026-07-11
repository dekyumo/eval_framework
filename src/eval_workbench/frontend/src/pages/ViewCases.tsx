import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { PageContainer, PagePane } from '../components/ui/PageLayout';
import { CaseListPane } from '../components/cases/CaseListPane';
import { CaseDetailView } from '../components/cases/CaseListPane';

export function ViewCases() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get('highlight');

  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(highlightId);

  const refreshCases = async () => {
    const res = await fetch('/api/cases');
    const data = await res.json();
    if (Array.isArray(data)) setCases(data);
    return data;
  };

  useEffect(() => {
    refreshCases().finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (highlightId) setSelectedCaseId(highlightId);
  }, [highlightId]);

  const selectedCase = cases.find(c => c.id === selectedCaseId) ?? null;

  const goToEditor = (intent: string, caseId?: string) => {
    const params = new URLSearchParams({ intent });
    if (caseId) params.set('caseId', caseId);
    navigate(`/cases_editor?${params.toString()}`);
  };

  const handleDeactivate = async (caseId: string) => {
    const res = await fetch(`/api/cases/${caseId}/deactivate`, { method: 'POST' });
    if (res.ok) {
      await refreshCases();
    }
  };

  return (
    <PageContainer variant="standard">
      <PagePane
        variant="content"
        title="View Cases"
        headerActions={
          <Button variant="cta" size="sm" onClick={() => goToEditor('create')}>
            Create Case
          </Button>
        }
      >
        <CaseListPane
          cases={cases}
          loading={loading}
          selectedCaseId={selectedCaseId}
          onSelectCase={setSelectedCaseId}
          title="Cases"
          emptyMessage="No cases found. Create one in the Case Editor."
        />

        {selectedCase && (
          <div className="mt-4 space-y-4">
            <div className="flex flex-wrap gap-3">
              <Button variant="destructive" size="lg" onClick={() => goToEditor('edit', selectedCase.id)}>
                <span className="material-symbols-outlined text-xl mr-2">edit</span>
                Edit
              </Button>
              <Button variant="cta" size="lg" onClick={() => goToEditor('duplicate', selectedCase.id)}>
                <span className="material-symbols-outlined text-xl mr-2">content_copy</span>
                Duplicate
              </Button>
              <Button variant="cta" size="lg" onClick={() => goToEditor('version', selectedCase.id)}>
                <span className="material-symbols-outlined text-xl mr-2">history</span>
                New Version
              </Button>
              {selectedCase.active_for_eval !== false && (
                <Button variant="normal" size="lg" onClick={() => handleDeactivate(selectedCase.id)}>
                  <span className="material-symbols-outlined text-xl mr-2">visibility_off</span>
                  Deactivate
                </Button>
              )}
            </div>
            <CaseDetailView caseData={selectedCase} />
          </div>
        )}
      </PagePane>
    </PageContainer>
  );
}
