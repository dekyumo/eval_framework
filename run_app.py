import argparse
import os
import sys

import dotenv


def main() -> None:
    parser = argparse.ArgumentParser(description="TrustMeBro")
    parser.add_argument("repo", help="Path to the target git repository")
    parser.add_argument(
        "--mode",
        choices=["web", "headless", "mcp"],
        default="web",
        help="web: Flask UI (default); headless: benchmark report; mcp: stdio MCP server",
    )
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")))
    parser.add_argument(
        "--api-url",
        default=os.environ.get("EVAL_WORKBENCH_API_URL"),
        help="Eval workbench base URL for MCP mode (e.g. http://127.0.0.1:5000)",
    )
    parser.add_argument("--agent_path", help="Agent import path, e.g. a_single_agent.day_trip:root_agent")
    parser.add_argument("--commit", default="HEAD", help="Git commit or branch to evaluate")
    parser.add_argument("--dataset", help="Eval dataset name to run")
    parser.add_argument("--tags", nargs="*", default=[], help="Optional case tags to filter on")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Model id for trace generation")
    parser.add_argument("--format", choices=["markdown", "csv"], default="markdown", help="Output format")
    parser.add_argument("--output", default=None, help="Write output to this file path instead of stdout")
    parser.add_argument(
        "--allow-db-wipe-for-tests",
        action="store_true",
        help="Enable POST /api/test/reset. Never use on a live database.",
    )
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo)
    if not os.path.isdir(repo_path):
        print(f"Error: {repo_path} is not a directory.", file=sys.stderr)
        sys.exit(1)

    dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

    if args.mode == "mcp":
        from src.eval_workbench.mcp.server import build_server, resolve_api_url

        api_url = resolve_api_url(args.api_url)
        build_server(api_url).run(transport="stdio")
        sys.exit(0)

    if args.mode == "headless":
        if not args.agent_path or not args.dataset:
            print("Error: --mode headless requires --agent_path and --dataset", file=sys.stderr)
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
        print(f"Warning: {repo_path} does not appear to be a git repository.", file=sys.stderr)

    from src.eval_workbench.web.app import create_app

    app = create_app(
        repo_path=repo_path,
        allow_db_wipe=args.allow_db_wipe_for_tests,
    )
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host=args.host, port=args.port, debug=debug, use_reloader=False)


if __name__ == "__main__":
    main()
