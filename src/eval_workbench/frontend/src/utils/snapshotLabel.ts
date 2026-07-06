export interface SnapshotLike {
  id: string;
  commit_hash?: string;
  agent_target?: {
    agent_path?: string;
    name?: string;
  };
}

export function shortCommitHash(commitHash: string, length = 7): string {
  if (!commitHash) return '';
  return commitHash.length > length ? commitHash.slice(0, length) : commitHash;
}

/** Human-readable snapshot label: short_hash:module.path:agent_var */
export function formatSnapshotLabel(snapshot: SnapshotLike): string {
  const agentPath = snapshot.agent_target?.agent_path;
  const commit = snapshot.commit_hash || snapshot.id.split(':')[0] || '';
  const shortHash = shortCommitHash(commit);

  if (agentPath) {
    return `${shortHash}:${agentPath}`;
  }

  // Fallback: shorten commit prefix of canonical id (commit:module:var)
  const colon = snapshot.id.indexOf(':');
  if (colon > 0) {
    const idCommit = snapshot.id.slice(0, colon);
    const rest = snapshot.id.slice(colon + 1);
    return `${shortCommitHash(idCommit)}:${rest}`;
  }

  return snapshot.id;
}
