import dotenv

dotenv.load_dotenv()

from src.eval_workbench.ssl_config import configure_process_ssl

configure_process_ssl()

import argparse
import os
import sys
from src.eval_workbench.web.app import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eval Workbench")
    parser.add_argument("repo", help="Path to the target git repository")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--headless", action="store_true", help="Run benchmark without the web UI")
    parser.add_argument("--agent_path", help="Agent import path, e.g. a_single_agent.day_trip:root_agent")
    parser.add_argument("--commit", default="HEAD", help="Git commit or branch to evaluate")
    parser.add_argument("--dataset", help="Eval dataset name to run")
    parser.add_argument("--tags", nargs="*", default=[], help="Optional case tags to filter on")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Model id for trace generation")
    parser.add_argument("--format", choices=["markdown", "csv"], default="markdown", help="Output format")
    parser.add_argument("--output", default=None, help="Write output to this file path instead of stdout")
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo)
    if not os.path.isdir(repo_path):
        print(f"Error: {repo_path} is not a directory.", file=sys.stderr)
        sys.exit(1)

    if args.headless:
        if not args.agent_path or not args.dataset:
            print("Error: --headless requires --agent_path and --dataset", file=sys.stderr)
            sys.exit(2)
        from src.eval_workbench.services.benchmark import run_headless_benchmark
        from src.eval_workbench.services.errors import ServiceError

        try:
            report = run_headless_benchmark(
                repo_path=repo_path,
                agent_path=args.agent_path,
                commit=args.commit,
                dataset_name=args.dataset,
                tags=args.tags,
                model_id=args.model,
                output_format=args.format,
                output_path=args.output,
            )
            print(report)
        except ServiceError as exc:
            print(f"Error: {exc.message}", file=sys.stderr)
            sys.exit(exc.status_code)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"Warning: {repo_path} does not appear to be a git repository.")

    app = create_app(repo_path=repo_path)
    app.run(host=args.host, port=args.port, debug=True, use_reloader=False)
