import { execSync } from 'child_process';

const PORT = 5000;

/** Stop whatever is listening on 127.0.0.1:5000 (orphaned Flask from prior Playwright runs). */
export function freePort5000(): void {
  try {
    const out = execSync(`netstat -ano | findstr ":${PORT}" | findstr "LISTENING"`, {
      encoding: 'utf-8',
      shell: true,
    });
    const pids = new Set<string>();
    for (const line of out.split(/\r?\n/)) {
      const pid = line.trim().split(/\s+/).at(-1);
      if (pid && pid !== '0') pids.add(pid);
    }
    for (const pid of pids) {
      console.log(`[e2e] freeing port ${PORT}: killing PID ${pid}`);
      execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore', shell: true });
    }
  } catch {
    // nothing listening
  }
}
