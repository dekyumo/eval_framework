import hashlib


def safe_id_part(value: str) -> str:
    return value.replace(" ", "_").replace(":", "_").replace("-", "_").replace("/", "_").replace("\\", "_")


def build_run_id(
    *,
    dataset_name: str,
    case_name: str,
    agent_name: str,
    commit_hash: str,
    model_id: str,
    trace_id: str,
    campaign_name: str | None = None,
    campaign_id: str | None = None,
) -> str:
    run_hash = hashlib.md5(trace_id.encode()).hexdigest()[:6]
    ds_s = safe_id_part(dataset_name)
    case_s = safe_id_part(case_name)
    agent_s = safe_id_part(agent_name)
    commit_s = safe_id_part(commit_hash[:7] if commit_hash else "HEAD")
    model_s = safe_id_part(model_id)
    snapshot_info = f"{agent_s}_{commit_s}_{model_s}"
    base_id = f"{ds_s}-{case_s}-{snapshot_info}-{run_hash}"
    if campaign_name and campaign_id:
        camp_hash = hashlib.md5(campaign_id.encode()).hexdigest()[:6]
        return f"{safe_id_part(campaign_name)}_{camp_hash}-{base_id}"
    return base_id
