import json
from typing import TypeVar, Type, Optional, List
from pydantic import BaseModel
import kuzu
import time

T = TypeVar('T', bound=BaseModel)

from src.eval_workbench.storage.schema import NODE_TABLES

class BaseRepository:
    def __init__(self, conn: kuzu.Connection):
        self.conn = conn

    def _create_edge(self, rel_table: str, from_node: str, to_node: str, from_id: str, to_id: str, from_pk: str = "id", to_pk: str = "id"):
        query = f"""
        MATCH (a:{from_node} {{{from_pk}: $from_id}}), (b:{to_node} {{{to_pk}: $to_id}})
        MERGE (a)-[r:{rel_table}]->(b)
        """
        self.conn.execute(query, {"from_id": from_id, "to_id": to_id})

    def _delete_node(self, label: str, pk_field: str, pk_val: str):
        query = f"MATCH (n:{label} {{{pk_field}: $pk_val}}) DETACH DELETE n"
        self.conn.execute(query, {"pk_val": pk_val})

    def _save_node(self, label: str, pk_field: str, model: BaseModel):
        schema_def = NODE_TABLES.get(label, "")
        allowed_fields = [p.strip().split(" ")[0] for p in schema_def.split(",") if "PRIMARY KEY" not in p]
        
        data = model.model_dump(exclude_none=True)
        fields = []
        values = []
        for k, v in data.items():
            if allowed_fields and k not in allowed_fields:
                continue
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            fields.append(k)
            values.append(v)
        
        pk_val = getattr(model, pk_field)
        
        query = f"MERGE (n:{label} {{{pk_field}: $pk_val}}) "
        if len(fields) > 0:
            set_clauses = ", ".join([f"n.{f} = ${f}" for f in fields if f != pk_field])
            if set_clauses:
                query += f"SET {set_clauses}"
            
        params = {"pk_val": pk_val}
        for f, v in zip(fields, values):
            if f != pk_field:
                params[f] = v
            
        self.conn.execute(query, params)

    def _parse_node_data(self, node_data, model_class: Type[T]) -> T:
        from pydantic_core import PydanticUndefined
        parsed_data = {}
        for field_name, field_info in model_class.model_fields.items():
            val = node_data.get(field_name)
            if isinstance(val, str) and val != "":
                try:
                    if (val.startswith('{') and val.endswith('}')) or (val.startswith('[') and val.endswith(']')):
                        val = json.loads(val)
                except Exception:
                    pass
                    
            if val == "" or val is None:
                if field_info.default is not PydanticUndefined:
                    val = field_info.default
                elif field_info.default_factory is not None:
                    val = field_info.default_factory()
                else:
                    ann = str(field_info.annotation).lower()
                    if 'list' in ann:
                        val = []
                    elif 'dict' in ann:
                        val = {}
                    elif 'str' in ann:
                        val = ""
                    elif 'float' in ann and field_name == 'created_at':
                        val = time.time()
                    else:
                        val = None
                        
            parsed_data[field_name] = val
            
        return model_class.model_validate(parsed_data)

    def _get_node(self, label: str, pk_field: str, pk_val: str, model_class: Type[T]) -> Optional[T]:
        query = f"MATCH (n:{label} {{{pk_field}: $pk_val}}) RETURN n"
        result = self.conn.execute(query, {"pk_val": pk_val})
        if not result.has_next():
            return None
            
        row = result.get_next()
        return self._parse_node_data(row[0], model_class)

    def get_all(self, label: str, pk_field: str, model_class: Type[T]) -> List[T]:
        query = f"MATCH (n:{label}) RETURN n"
        result = self.conn.execute(query)
        items = []
        while result.has_next():
            row = result.get_next()
            items.append(self._parse_node_data(row[0], model_class))
        return items

from src.eval_workbench.domain.tag import Tag
class TagRepository(BaseRepository):
    def save(self, tag: Tag):
        self._save_node("Tag", "id", tag)
    def get(self, id: str) -> Optional[Tag]:
        return self._get_node("Tag", "id", id, Tag)
    def delete(self, id: str):
        self._delete_node("Tag", "id", id)

from src.eval_workbench.domain.case import EvalCase
class EvalCaseRepository(BaseRepository):
    def save(self, case: EvalCase):
        self._save_node("EvalCase", "id", case)
        for tag in case.tags:
            self.conn.execute("MERGE (t:Tag {id: $id}) ON CREATE SET t.name = $id, t.color = '#31C48D'", {"id": tag})
            self._create_edge("TAGGED", "EvalCase", "Tag", case.id, tag, from_pk="id", to_pk="id")
    def get(self, id: str) -> Optional[EvalCase]:
        return self._get_node("EvalCase", "id", id, EvalCase)

from src.eval_workbench.domain.rubric import Rubric
class RubricRepository(BaseRepository):
    def save(self, rubric: Rubric):
        self._save_node("Rubric", "id", rubric)
    def get(self, id: str) -> Optional[Rubric]:
        return self._get_node("Rubric", "id", id, Rubric)
    def delete(self, id: str):
        self._delete_node("Rubric", "id", id)
        
from src.eval_workbench.domain.extractor import Extractor
class ExtractorRepository(BaseRepository):
    def save(self, ext: Extractor):
        self._save_node("Extractor", "id", ext)
    def get(self, id: str) -> Optional[Extractor]:
        return self._get_node("Extractor", "id", id, Extractor)
    def delete(self, id: str):
        self._delete_node("Extractor", "id", id)

from src.eval_workbench.domain.fault import FaultConfig
class FaultConfigRepository(BaseRepository):
    def save(self, conf: FaultConfig):
        self._save_node("FaultConfig", "id", conf)
    def get(self, id: str) -> Optional[FaultConfig]:
        return self._get_node("FaultConfig", "id", id, FaultConfig)
        
from src.eval_workbench.domain.campaign import EvalCampaign
class EvalCampaignRepository(BaseRepository):
    def save(self, camp: EvalCampaign):
        self._save_node("EvalCampaign", "id", camp)
    def get(self, id: str) -> Optional[EvalCampaign]:
        return self._get_node("EvalCampaign", "id", id, EvalCampaign)

from src.eval_workbench.domain.case import EvalDataset
class EvalDatasetRepository(BaseRepository):
    def save(self, ds: EvalDataset):
        self._save_node("EvalDataset", "id", ds)
    def get(self, id: str) -> Optional[EvalDataset]:
        return self._get_node("EvalDataset", "id", id, EvalDataset)
    def delete(self, id: str):
        self._delete_node("EvalDataset", "id", id)

from src.eval_workbench.domain.human_eval import HumanEval
class HumanEvalRepository(BaseRepository):
    def save(self, he: HumanEval):
        self._save_node("HumanEval", "id", he)
    def get(self, id: str) -> Optional[HumanEval]:
        return self._get_node("HumanEval", "id", id, HumanEval)

from src.eval_workbench.domain.run import EvalRun, ScoredEvalRun
class EvalRunRepository(BaseRepository):
    def save(self, run: EvalRun):
        self._save_node("EvalRun", "id", run)
        self._create_edge("RUN_OF_CASE", "EvalRun", "EvalCase", run.id, run.case_id)
        self._create_edge("RUN_OF_SNAPSHOT", "EvalRun", "Snapshot", run.id, run.snapshot_id)
        if run.campaign_id:
            self._create_edge("IN_CAMPAIGN", "EvalRun", "EvalCampaign", run.id, run.campaign_id)
            
    def get(self, id: str) -> Optional[EvalRun]:
        return self._get_node("EvalRun", "id", id, EvalRun)

class ScoredEvalRunRepository(BaseRepository):
    def save(self, run: ScoredEvalRun):
        self._save_node("ScoredEvalRun", "id", run)
        self._create_edge("SCORED_FROM", "ScoredEvalRun", "EvalRun", run.id, run.run_id)
        
    def get(self, id: str) -> Optional[ScoredEvalRun]:
        return self._get_node("ScoredEvalRun", "id", id, ScoredEvalRun)

from src.eval_workbench.domain.snapshot import AgentSnapshot
class SnapshotRepository(BaseRepository):
    def save(self, snap: AgentSnapshot):
        self._save_node("Snapshot", "id", snap)
        self.conn.execute("MERGE (c:Commit {hash: $hash})", {"hash": snap.commit_hash})
        self._create_edge("SNAPSHOT_OF", "Snapshot", "Commit", snap.id, snap.commit_hash, from_pk="id", to_pk="hash")
        
        # Save distribution if exists and create edge
        if snap.distribution:
            self._save_node("AgentDistribution", "snapshot_id", snap.distribution)
            self._create_edge("HAS_DISTRIBUTION", "Snapshot", "AgentDistribution", snap.id, snap.distribution.snapshot_id, from_pk="id", to_pk="snapshot_id")
            
        # Save manifest nodes
        for model in snap.manifest.models:
            self._save_node("ModelNode", "id", model)
        for tool in snap.manifest.tools:
            self._save_node("ToolNode", "id", tool)
        for prompt in snap.manifest.prompts:
            self._save_node("PromptNode", "id", prompt)
            
        for agent in snap.manifest.agents:
            # We construct a unique key for the agent node because name might not be globally unique
            agent_key = f"{snap.id}:{agent.name}"
            # Add key into the dictionary for saving
            agent_dump = agent.model_dump()
            agent_dump["key"] = agent_key
            agent_dump["snapshot_id"] = snap.id
            
            # Pop list fields that are handled via graph edges, since they are not in the AgentNode schema
            for edge_field in ["tool_ids", "skill_ids", "hook_ids", "subagent_names"]:
                agent_dump.pop(edge_field, None)
            
            # Pop fields that aren't strictly part of the AgentNode schema in schema.py
            # The schema for AgentNode is: key, snapshot_id, name, model_id, prompt_id
            keys_to_keep = {"key", "snapshot_id", "name", "model_id", "prompt_id"}
            agent_dump = {k: v for k, v in agent_dump.items() if k in keys_to_keep}
            
            # Use raw query since model doesn't have key
            fields = list(agent_dump.keys())
            query = f"MERGE (n:AgentNode {{key: $key}}) "
            set_clauses = ", ".join([f"n.{f} = ${f}" for f in fields if f != "key"])
            if set_clauses:
                query += f"SET {set_clauses}"
                
            params = {}
            for k, v in agent_dump.items():
                params[k] = json.dumps(v) if isinstance(v, (list, dict)) else (v if v is not None else "")
                
            self.conn.execute(query, params)
            
            # Create HAS_AGENT edge
            self._create_edge("HAS_AGENT", "Snapshot", "AgentNode", snap.id, agent_key, from_pk="id", to_pk="key")
            
            # Edges from AgentNode
            if agent.model_id:
                self._create_edge("USES_MODEL", "AgentNode", "ModelNode", agent_key, agent.model_id, from_pk="key", to_pk="id")
            if agent.prompt_id:
                self._create_edge("CONTAINS_PROMPT", "AgentNode", "PromptNode", agent_key, agent.prompt_id, from_pk="key", to_pk="id")
            for t_id in agent.tool_ids:
                self._create_edge("USES_TOOL", "AgentNode", "ToolNode", agent_key, t_id, from_pk="key", to_pk="id")
            for sub_name in agent.subagent_names:
                sub_key = f"{snap.id}:{sub_name}"
                self._create_edge("DELEGATES_TO", "AgentNode", "AgentNode", agent_key, sub_key, from_pk="key", to_pk="key")
                
    def get(self, id: str) -> Optional[AgentSnapshot]:
        snap = self._get_node("Snapshot", "id", id, AgentSnapshot)
        if snap:
            # Manually re-hydrate edges if necessary?
            # Kuzu doesn't magically join unless we query.
            # But AgentManifest might already be stored correctly as a string payload for now.
            pass
        return snap
        
    def get_all_snapshots(self) -> List[AgentSnapshot]:
        return self.get_all("Snapshot", "id", AgentSnapshot)

