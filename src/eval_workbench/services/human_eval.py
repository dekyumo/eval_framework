from src.eval_workbench.domain.human_eval import HumanEval
from src.eval_workbench.services._conn import conn
from src.eval_workbench.storage.repositories import HumanEvalRepository


def create_human_eval(repo_path: str, data: dict) -> dict:
    raw_results = data.get("results") or {}
    results_list = []
    if isinstance(raw_results, dict):
        for name, value in raw_results.items():
            if isinstance(value, bool):
                value_type = "bool"
            elif isinstance(value, int):
                value_type = "int"
            elif isinstance(value, float):
                value_type = "float"
            else:
                value_type = "enum"
            results_list.append({
                "name": name,
                "type": value_type,
                "value": value,
                "source": "human",
            })
    else:
        results_list = raw_results

    human_eval = HumanEval(
        id=data.get("id"),
        run_id=data.get("run_id"),
        rubric_id=data.get("rubric_id"),
        results=results_list,
        comments=data.get("comments", ""),
    )
    HumanEvalRepository(conn(repo_path)).save(human_eval)
    return human_eval.model_dump()
