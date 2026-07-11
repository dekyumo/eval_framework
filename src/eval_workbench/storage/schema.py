import kuzu

NODE_TABLES = {
    "Commit": "hash STRING, branch STRING, ts INT64, PRIMARY KEY (hash)",
    "Snapshot": "id STRING, agent_target STRING, commit_hash STRING, branch STRING, timestamp DOUBLE, manifest STRING, distribution STRING, sampling_params STRING, dependency_lock STRING, framework_commit STRING, governance STRING, PRIMARY KEY (id)",
    "AgentDistribution": "snapshot_id STRING, description STRING, regions STRING, editable BOOL, PRIMARY KEY (snapshot_id)",
    "AgentNode": "key STRING, snapshot_id STRING, name STRING, model_id STRING, prompt_id STRING, PRIMARY KEY (key)",
    "ToolNode": "id STRING, name STRING, signature STRING, source_fingerprint STRING, reaches_external BOOL, PRIMARY KEY (id)",
    "ModelNode": "id STRING, provider STRING, PRIMARY KEY (id)",
    "PromptNode": "id STRING, fingerprint STRING, text STRING, PRIMARY KEY (id)",
    "EvalCase": "id STRING, name STRING, logical_id STRING, version INT64, active_for_eval BOOL, dataset_id STRING, conversation STRING, session_state STRING, input_payload STRING, agentic_user STRING, distribution_position STRING, problem_type STRING, split STRING, difficulty_prior STRING, source STRING, tags STRING, metrics STRING, fault_config STRING, tool_fault STRING, PRIMARY KEY (id)",
    "Rubric": "id STRING, name STRING, items STRING, instructions STRING, default_judge_prompt STRING, judge_model_id STRING, consumes_two_traces BOOL, version INT64, fingerprint STRING, frozen BOOL, PRIMARY KEY (id)",
    "Extractor": "id STRING, name STRING, return_type STRING, source_path STRING, fingerprint STRING, PRIMARY KEY (id)",
    "Gym": "id STRING, name STRING, class_path STRING, description STRING, PRIMARY KEY (id)",
    "EvalRun": "id STRING, snapshot_id STRING, case_id STRING, model_id STRING, repetition_index INT64, trace STRING, campaign_id STRING, PRIMARY KEY (id)",
    "ScoredEvalRun": "id STRING, run_id STRING, results STRING, aggregates STRING, PRIMARY KEY (id)",
    "EvalCampaign": "id STRING, name STRING, dataset_id STRING, base_snapshot_id STRING, model_panel STRING, repetitions INT64, PRIMARY KEY (id)",
    "EvalDataset": "id STRING, name STRING, case_ids STRING, PRIMARY KEY (id)",
    "Tag": "id STRING, name STRING, color STRING, description STRING, PRIMARY KEY (id)",
    "HumanEval": "id STRING, run_id STRING, rubric_id STRING, results STRING, comments STRING, PRIMARY KEY (id)",
    "FaultConfig": "id STRING, boundary STRING, fault_class STRING, target STRING, trigger STRING, n INT64, persistent BOOL, payload STRING, seed INT64, mocked_tools_ref STRING, mocked_tools_fingerprint STRING, PRIMARY KEY (id)",
}

REL_TABLES = [
    ("ON_TOP_OF", "FROM Commit TO Commit"),
    ("SNAPSHOT_OF", "FROM Snapshot TO Commit"),
    ("HAS_DISTRIBUTION", "FROM Snapshot TO AgentDistribution"),
    ("HAS_AGENT", "FROM Snapshot TO AgentNode"),
    ("DELEGATES_TO", "FROM AgentNode TO AgentNode"),
    ("USES_TOOL", "FROM AgentNode TO ToolNode"),
    ("USES_MODEL", "FROM AgentNode TO ModelNode"),
    ("CONTAINS_PROMPT", "FROM AgentNode TO PromptNode"),
    ("RUN_OF_CASE", "FROM EvalRun TO EvalCase"),
    ("RUN_OF_SNAPSHOT", "FROM EvalRun TO Snapshot"),
    ("IN_CAMPAIGN", "FROM EvalRun TO EvalCampaign"),
    ("SCORED_FROM", "FROM ScoredEvalRun TO EvalRun"),
    ("TAGGED", "FROM EvalCase TO Tag"),
]

def _migrate_schema(conn: kuzu.Connection):
    migrations = [
        "ALTER TABLE EvalCase ADD dataset_id STRING",
        "ALTER TABLE EvalCase ADD session_state STRING",
        "ALTER TABLE EvalCase ADD input_payload STRING",
        "ALTER TABLE EvalCase ADD agentic_user STRING",
        "ALTER TABLE Snapshot ADD governance STRING",
        "ALTER TABLE EvalCase ADD logical_id STRING",
        "ALTER TABLE EvalCase ADD version INT64",
        "ALTER TABLE EvalCase ADD active_for_eval BOOL",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
        except RuntimeError:
            pass

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_evalrun_snapshot_id ON EvalRun(snapshot_id)",
        "CREATE INDEX IF NOT EXISTS idx_evalrun_case_id ON EvalRun(case_id)",
        "CREATE INDEX IF NOT EXISTS idx_evalcase_logical_id ON EvalCase(logical_id)",
    ]
    for sql in index_statements:
        try:
            conn.execute(sql)
        except RuntimeError:
            pass


def init_schema(conn: kuzu.Connection):
    for table_name, schema in NODE_TABLES.items():
        try:
            conn.execute(f"CREATE NODE TABLE {table_name}({schema})")
        except RuntimeError as e:
            # Table probably exists
            if "already exists" not in str(e).lower():
                raise

    _migrate_schema(conn)

    for rel_name, rel_def in REL_TABLES:
        try:
            conn.execute(f"CREATE REL TABLE {rel_name}({rel_def})")
        except RuntimeError as e:
            if "already exists" not in str(e).lower():
                raise
