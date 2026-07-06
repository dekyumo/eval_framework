import json
import subprocess
import os
import tempfile
from pathlib import Path
from src.eval_workbench.ssl_config import ssl_env_for_subprocess
from src.eval_workbench.runner.worktree import WorktreeRunner
from src.eval_workbench.domain.snapshot import AgentSnapshot
from src.eval_workbench.domain.case import EvalCase
from src.eval_workbench.domain.fault import FaultConfig
from src.eval_workbench.domain.trace import Trace

class AgentRunner:
    def __init__(self, snapshot: AgentSnapshot):
        self.snapshot = snapshot

    def run_case(self, case: EvalCase, model_id: str, fault_config: FaultConfig | None = None) -> Trace:
        with WorktreeRunner(self.snapshot.agent_target.repo_path, self.snapshot.commit_hash) as wt:
            
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as snap_f:
                snap_f.write(self.snapshot.model_dump_json())
                snap_path = snap_f.name
                
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as case_f:
                case_f.write(case.model_dump_json())
                case_path = case_f.name
                
            fault_path = "null"
            if fault_config:
                with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as fault_f:
                    fault_f.write(fault_config.model_dump_json())
                    fault_path = fault_f.name
            
            # The exec_script.py needs to be available. Since we run inside worktree,
            # we should copy it or just call it from our src dir if PYTHONPATH allows it.
            # Worktree sets PYTHONPATH to the main repo, but exec_script.py is here.
            # Let's just point directly to it.
            exec_script_path = Path(__file__).parent / "exec_script.py"
            
            env = ssl_env_for_subprocess(os.environ.copy())
            framework_root = Path(__file__).resolve().parents[3]
            env["PYTHONPATH"] = os.pathsep.join([str(wt.path), str(framework_root)])
            
            res = subprocess.run(
                [str(wt.python), str(exec_script_path), snap_path, case_path, model_id, fault_path],
                cwd=str(wt.path),
                env=env,
                capture_output=True,
                text=True
            )
            
            os.unlink(snap_path)
            os.unlink(case_path)
            if fault_config:
                os.unlink(fault_path)
                
            if res.returncode != 0 and not res.stdout.strip():
                # Script crashed without outputting trace
                raise RuntimeError(f"exec_script failed: {res.stderr}")
                
            try:
                # The script prints the trace JSON to stdout
                trace_json = res.stdout.strip().split('\n')[-1]
                return Trace.model_validate_json(trace_json)
            except Exception as e:
                raise RuntimeError(f"Failed to parse trace: {res.stdout}\nStderr: {res.stderr}") from e
