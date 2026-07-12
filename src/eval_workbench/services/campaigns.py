from src.eval_workbench.analysis.response_matrix import ResponseMatrix
from src.eval_workbench.domain.campaign import EvalCampaign
from src.eval_workbench.domain.result import Result
from src.eval_workbench.domain.run import EvalRun, ScoredEvalRun
from src.eval_workbench.runner.agent_runner import AgentRunner
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services._ids import build_run_id
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.services.scoring import rubric_result_name, score_trace
from src.eval_workbench.storage.repositories import (
    EvalCampaignRepository,
    EvalCaseRepository,
    EvalDatasetRepository,
    EvalRunRepository,
    RubricRepository,
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
            if not case or not case.active_for_eval:
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


def _collect_dataset_metrics(
    case_repo: EvalCaseRepository,
    rubric_repo: RubricRepository,
    case_ids: list[str],
) -> list[dict[str, str]]:
    seen: dict[str, str] = {}
    for case_id in case_ids:
        case = case_repo.get(case_id)
        if not case:
            continue
        for metric in case.metrics:
            if metric.strategy == "rubric" and metric.rubric_ref:
                rubric = rubric_repo.get(metric.rubric_ref)
                if not rubric:
                    raise ServiceError(
                        f"Rubric {metric.rubric_ref!r} not found for case {case_id}",
                        422,
                    )
                for item in rubric.items:
                    name = rubric_result_name(metric.name, item.name)
                    prev = seen.get(name)
                    if prev is not None and prev != item.type:
                        raise ServiceError(f"Metric {name!r} has conflicting types across cases", 422)
                    seen[name] = item.type
                continue
            prev = seen.get(metric.name)
            if prev is not None and prev != metric.result_type:
                raise ServiceError(f"Metric {metric.name!r} has conflicting types across cases", 422)
            seen[metric.name] = metric.result_type
    return [{"name": name, "result_type": seen[name]} for name in sorted(seen)]


def _resolve_metric(
    available_metrics: list[dict[str, str]],
    metric_name: str | None,
) -> tuple[str, str]:
    if not available_metrics:
        raise ServiceError("No metrics defined on cases in this campaign dataset", 400)
    if metric_name:
        for metric in available_metrics:
            if metric["name"] == metric_name:
                return metric["name"], metric["result_type"]
        raise ServiceError(f"Metric not found in campaign dataset: {metric_name}", 404)
    first = available_metrics[0]
    return first["name"], first["result_type"]


def _find_scored_result(results: list[Result], result_name: str) -> Result | None:
    for result in results:
        if result.name == result_name:
            return result
    suffix = f" ({result_name})"
    for result in results:
        if result.name.endswith(suffix):
            return result
    return None


def _matrix_cell(result: Result, metric_type: str) -> float:
    """One cell in the model×case response matrix."""
    if metric_type == "bool":
        if not isinstance(result.value, bool):
            raise ServiceError(f"Metric {result.name!r} is bool but result value is not", 500)
        return 1.0 if result.value else 0.0
    if metric_type in ("int", "float"):
        return float(result.value)
    raise ServiceError(
        f"Campaign matrix supports bool metrics (IRT) and int/float metrics (regression); got {metric_type!r}",
        400,
    )


def get_matrix(repo_path: str, campaign_id: str, metric_name: str | None = None) -> dict:
    connection = conn(repo_path)
    campaign = EvalCampaignRepository(connection).get(campaign_id)
    if not campaign:
        raise ServiceError("not found", 404)

    dataset = EvalDatasetRepository(connection).get(campaign.dataset_id)
    case_ids = dataset.case_ids if dataset else []
    case_repo = EvalCaseRepository(connection)
    rubric_repo = RubricRepository(connection)
    available_metrics = _collect_dataset_metrics(case_repo, rubric_repo, case_ids)
    selected_name, selected_type = _resolve_metric(available_metrics, metric_name)

    scored_runs_repo = ScoredEvalRunRepository(connection)
    runs_repo = EvalRunRepository(connection)
    all_scored = scored_runs_repo.get_all("ScoredEvalRun", "id", ScoredEvalRun)

    cell: dict[str, float] = {}
    use_regression = selected_type in ("int", "float")

    for scored in all_scored:
        run = runs_repo.get(scored.run_id)
        if not run or run.campaign_id != campaign_id:
            continue
        result = _find_scored_result(scored.results, selected_name)
        if result is None:
            continue
        if result.type != selected_type:
            raise ServiceError(
                f"Result type {result.type!r} for metric {selected_name!r} "
                f"does not match case definition {selected_type!r}",
                500,
            )
        cell[f"{run.model_id}|{run.case_id}"] = _matrix_cell(result, selected_type)

    x_rows: list[list[int]] = []
    y_values: list[float] = []
    for model_idx, model_id in enumerate(campaign.model_panel):
        for case_idx, case_id in enumerate(case_ids):
            key = f"{model_id}|{case_id}"
            if key not in cell:
                continue
            features = [0] * (len(campaign.model_panel) + len(case_ids))
            features[model_idx] = 1
            features[len(campaign.model_panel) + case_idx] = 1
            x_rows.append(features)
            y_values.append(cell[key])

    difficulty: dict[str, float] = {}
    ability: dict[str, float] = {}

    if len(set(y_values)) > 1 and x_rows:
        from sklearn.linear_model import LinearRegression, LogisticRegression

        if use_regression:
            clf = LinearRegression(fit_intercept=False)
        else:
            clf = LogisticRegression(fit_intercept=False, penalty=None)

        clf.fit(x_rows, y_values)
        coefs = clf.coef_ if use_regression else clf.coef_[0]

        for model_idx, model_id in enumerate(campaign.model_panel):
            ability[model_id] = float(coefs[model_idx])
        for case_idx, case_id in enumerate(case_ids):
            difficulty[case_id] = float(-coefs[len(campaign.model_panel) + case_idx])

    matrix = ResponseMatrix(
        campaign_id=campaign_id,
        models=campaign.model_panel,
        case_ids=case_ids,
        cell=cell,
        metric_name=selected_name,
        metric_type=selected_type,
        available_metrics=available_metrics,
        difficulty=difficulty,
        ability=ability,
        clusters={},
        redundant_pairs=[],
    )
    return matrix.model_dump()
