from src.eval_workbench.domain.manifest import AgentManifest, AgentNode, ToolNode, PromptNode
from src.eval_workbench.domain.snapshot import AgentTarget, AgentDistribution, DistributionRegion
from src.eval_workbench.runner.worktree import WorktreeRunner
from src.eval_workbench.scanner.ast_enrichment import enrich_scan_result
from src.eval_workbench.scanner.code_explorer_runner import run_code_explorer


def _build_manifest(graph: dict) -> AgentManifest:
    agents = [AgentNode(**a) for a in graph.get("agents", [])]
    tools = [
        ToolNode(
            id=t["id"],
            name=t["name"],
            signature=t["signature"],
            source_fingerprint=t["source_fingerprint"],
            reaches_external=t.get("reaches_external", False),
        )
        for t in graph.get("tools", [])
    ]
    prompts = [PromptNode(**p) for p in graph.get("prompts", [])]

    return AgentManifest(
        agents=agents,
        tools=tools,
        models=[],
        prompts=prompts,
        root_agent_name=graph.get("root_agent_name", "root"),
    )


def scan_agent(target: AgentTarget, commit: str) -> tuple[AgentManifest, AgentDistribution]:
    """
    Deterministically scan an agent by:
    1. Instantiating it in a worktree to get the ADK object graph (recursive).
    2. Using AST inspection in the main process to recover tool/callback sources.
    3. Returning the Manifest and a drafted Distribution (using AGENT2).
    """
    with WorktreeRunner(target.repo_path, commit) as wt:
        graph = wt.run_introspection(target.agent_path)

    graph = enrich_scan_result(graph, target.repo_path, commit)
    manifest = _build_manifest(graph)

    description = "Drafted distribution description from Code Explorer."
    in_distribution = ["Basic task processing"]
    margin = ["Tasks that might require more tools"]
    ood = ["Tasks outside the explicitly provided tools"]

    try:
        result = run_code_explorer(graph)
        description = result.description
        in_distribution = result.in_distribution
        ood = result.out_of_distribution
        margin = result.distribution_margin
    except Exception as e:
        print(f"Code explorer agent failed: {e}")

    distribution = AgentDistribution(
        snapshot_id=f"{commit}:{target.agent_path}",
        description=description,
        regions=DistributionRegion(
            in_distribution=in_distribution,
            margin=margin,
            ood=ood,
        ),
        editable=True,
    )

    return manifest, distribution
