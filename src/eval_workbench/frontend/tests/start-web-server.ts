import { spawn, spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { freePort5000 } from './free-port';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const goEvalBat =
  process.env.GO_EVAL_BAT ?? path.join(process.env.USERPROFILE ?? '', 'go_eval.bat');
const condaEnv = process.env.EVAL_CONDA_ENV ?? 'eval_framework';
const evalPython =
  process.env.EVAL_PYTHON ??
  path.join(process.env.USERPROFILE ?? '', 'anaconda3', 'envs', condaEnv, 'python.exe');

function resolveCaBundle(): string {
  const commands = [
    `"${evalPython}" -m certifi`,
    `call "${goEvalBat}" & python -m certifi`,
  ];

  for (const cmd of commands) {
    const result = spawnSync(cmd, { shell: true, encoding: 'utf8' });
    const bundle = (result.stdout ?? '').trim();
    if (bundle) return bundle;
  }

  throw new Error('python -m certifi produced no output from any launcher');
}

freePort5000();

const caBundle = resolveCaBundle();

const cmd = [
  `call "${goEvalBat}"`,
  `set "SSL_CERT_FILE=${caBundle}"`,
  `set "REQUESTS_CA_BUNDLE=${caBundle}"`,
  `set SSL_CERT_DIR=`,
  `python run_app.py adk_tutorial --allow-db-wipe-for-tests`,
].join(' && ');

// Inherit the parent shell env (like manual CLI). Do not spread process.env into a
// custom block — Cursor's Node env can differ from an interactive go_eval session.
const child = spawn(cmd, { shell: true, stdio: 'inherit' });

child.on('exit', (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  process.exit(code ?? 1);
});
