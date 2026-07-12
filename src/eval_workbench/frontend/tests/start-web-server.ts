import { spawn } from 'child_process';
import path from 'path';
import { freePort5000 } from './free-port';

const goEvalBat =
  process.env.GO_EVAL_BAT ?? path.join(process.env.USERPROFILE ?? '', 'go_eval.bat');

freePort5000();

const cmd = [
  `call "${goEvalBat}"`,
  `python run_app.py adk_tutorial --allow-db-wipe-for-tests`,
].join(' && ');

// Inherit the parent shell env (like manual CLI). Do not spread process.env into a
// custom block — Cursor's Node env can differ from an interactive go_eval session.
const child = spawn(cmd, { shell: true, stdio: 'inherit' });

child.on('exit', (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  process.exit(code ?? 1);
});
