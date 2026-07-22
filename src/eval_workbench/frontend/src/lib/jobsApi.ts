export type TaskStatus = 'queued' | 'running' | 'succeeded' | 'failed';

export type Task = {
  id: string;
  type: string;
  status: TaskStatus;
  label: string;
  progress?: { done: number; total: number };
  error?: string | null;
};

export type FailedTask = Task & { failedAt: number };

export const FAILED_TASK_DISPLAY_MS = 30_000;

export type DomainEventHandler = (data: Record<string, unknown>) => void;

async function postJob(path: string, body: Record<string, unknown>): Promise<Task> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || `Job enqueue failed (${res.status})`);
  }
  return data.task as Task;
}

export async function enqueueGenerateTraces(
  snapshotId: string,
  datasetId: string,
  modelId: string,
  force = false,
): Promise<Task> {
  return postJob('/api/jobs/generate-traces', {
    snapshot_id: snapshotId,
    dataset_id: datasetId,
    model_id: modelId,
    force,
  });
}

export async function enqueueGenerateTrace(
  snapshotId: string,
  caseId: string,
  modelId: string,
  force = false,
): Promise<Task> {
  return postJob('/api/jobs/generate-trace', {
    snapshot_id: snapshotId,
    case_id: caseId,
    model_id: modelId,
    force,
  });
}

export async function enqueueEvaluateTraces(
  snapshotId: string,
  datasetId: string,
  force = false,
): Promise<Task> {
  return postJob('/api/jobs/evaluate-traces', {
    snapshot_id: snapshotId,
    dataset_id: datasetId,
    force,
  });
}

export async function enqueueEvaluateTrace(runId: string, force = false): Promise<Task> {
  return postJob('/api/jobs/evaluate-trace', { run_id: runId, force });
}

export async function enqueueRunCampaign(campaign: Record<string, unknown>): Promise<Task> {
  return postJob('/api/jobs/run-campaign', campaign);
}

export async function enqueueScanAgent(
  agentTarget: Record<string, unknown>,
  commit: string,
): Promise<Task> {
  return postJob('/api/jobs/scan-agent', { agent_target: agentTarget, commit });
}

export async function fetchActiveTasks(): Promise<Task[]> {
  const res = await fetch('/api/jobs/');
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}
