from src.eval_workbench.analysis.response_matrix import ResponseMatrix
from src.eval_workbench.domain.campaign import EvalCampaign
from src.eval_workbench.domain.run import EvalRun, ScoredEvalRun
from src.eval_workbench.runner.agent_runner import AgentRunner
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services._ids import build_run_id
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.services.scoring import score_trace
from src.eval_workbench.storage.repositories import (
    EvalCampaignRepository,
    EvalCaseRepository,
    EvalDatasetRepository,
    EvalRunRepository,
    ScoredEvalRunRepository,
    SnapshotRepository,
)


def list_campaigns(repo_path: str) -> list[dict]:
    campaigns = EvalCampaignRepository(conn(repo_path)).get_all("EvalCampaign", "id", EvalCampaign)
    return [campaign.model_dump() for campaign in campaigns]


def create_campaign(repo_path: str, data: dict) -> dict:
    payload = dict(data)
    payload.pop("repo_path", None)
    campaign = EvalCampaign(**payload)
    connection = conn(repo_path)
    EvalCampaignRepository(connection).save(campaign)

    dataset = EvalDatasetRepository(connection).get(campaign.dataset_id)
    snapshot = SnapshotRepository(connection).get(campaign.base_snapshot_id)
    case_repo = EvalCaseRepository(connection)
    run_repo = EvalRunRepository(connection)
    scored_repo = ScoredEvalRunRepository(connection)

    if dataset and snapshot:
        runner = AgentRunner(snapshot)
        agent_name = snapshot.agent_target.agent_path.split(":")[-1]
        for case_id in dataset.case_ids:
            case = case_repo.get(case_id)
            if not case:
                continue
            for model_id in campaign.model_panel:
                try:
                    trace = runner.run_case(case, model_id)
                    run_id = build_run_id(
                        dataset_name=dataset.name or dataset.id,
                        case_name=case.name or case.id,
                        agent_name=agent_name,
                        commit_hash=snapshot.commit_hash or "",
                        model_id=model_id,
                        trace_id=trace.id,
                        campaign_name=campaign.name,
                        campaign_id=campaign.id,
                    )
                    trace.id = run_id
                    run = EvalRun(
                        id=run_id,
                        snapshot_id=snapshot.id,
                        case_id=case_id,
                        model_id=model_id,
                        repetition_index=0,
                        trace=trace,
                        campaign_id=campaign.id,
                    )
                    run_repo.save(run)

                    results = score_trace(trace, case, connection)
                    scored = ScoredEvalRun(
                        id=f"scored_{run.id}",
                        run_id=run.id,
                        results=results,
                    )
                    scored_repo.save(scored)
                except Exception as exc:
                    print(f"Error running case {case_id} with model {model_id}: {exc}")

    return campaign.model_dump()


def get_matrix(repo_path: str, campaign_id: str) -> dict:
    connection = conn(repo_path)
    campaign = EvalCampaignRepository(connection).get(campaign_id)
    if not campaign:
        raise ServiceError("not found", 404)

    dataset = EvalDatasetRepository(connection).get(campaign.dataset_id)
    case_ids = dataset.case_ids if dataset else []

    scored_runs_repo = ScoredEvalRunRepository(connection)
    runs_repo = EvalRunRepository(connection)
    all_scored = scored_runs_repo.get_all("ScoredEvalRun", "id", ScoredEvalRun)

    cell: dict[str, float] = {}
    is_float = False

    for scored in all_scored:
        run = runs_repo.get(scored.run_id)
        if run and run.campaign_id == campaign_id:
            score_val = 0.0
            if scored.results:
                first_result = scored.results[0]
                first_val = first_result.value
                if isinstance(first_val, bool):
                    score_val = 1.0 if first_val else 0.0
                elif isinstance(first_val, (int, float)):
                    score_val = float(first_val)
                    is_float = True
            cell[f"{run.model_id}|{run.case_id}"] = score_val

    for model_id in campaign.model_panel:
        for case_id in case_ids:
            key = f"{model_id}|{case_id}"
            if key not in cell:
                cell[key] = 0.0

    x_rows: list[list[int]] = []
    y_values: list[float] = []
    for model_idx, model_id in enumerate(campaign.model_panel):
        for case_idx, case_id in enumerate(case_ids):
            features = [0] * (len(campaign.model_panel) + len(case_ids))
            features[model_idx] = 1
            features[len(campaign.model_panel) + case_idx] = 1
            x_rows.append(features)
            y_values.append(cell[f"{model_id}|{case_id}"])

    difficulty: dict[str, float] = {}
    ability: dict[str, float] = {}

    if len(set(y_values)) > 1 and len(campaign.model_panel) > 0 and len(case_ids) > 0:
        from sklearn.linear_model import LinearRegression, LogisticRegression

        if is_float:
            clf = LinearRegression(fit_intercept=False)
        else:
            clf = LogisticRegression(fit_intercept=False, penalty=None)

        clf.fit(x_rows, y_values)
        coefs = clf.coef_ if is_float else clf.coef_[0]

        for model_idx, model_id in enumerate(campaign.model_panel):
            ability[model_id] = float(coefs[model_idx])
        for case_idx, case_id in enumerate(case_ids):
            difficulty[case_id] = float(-coefs[len(campaign.model_panel) + case_idx])

    matrix = ResponseMatrix(
        campaign_id=campaign_id,
        models=campaign.model_panel,
        case_ids=case_ids,
        cell=cell,
        difficulty=difficulty,
        ability=ability,
        clusters={},
        redundant_pairs=[],
    )
    return matrix.model_dump()
