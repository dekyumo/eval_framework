from src.eval_workbench.domain.trace import Trace
from src.eval_workbench.domain.case import EvalCase, MetricDef
from src.eval_workbench.domain.result import Result
from src.eval_workbench.extraction.extractor import run_extractor
from src.eval_workbench.storage.repositories import ExtractorRepository, RubricRepository
from src.eval_workbench.services.rubric_judge_runner import judge_trace_with_rubric
import kuzu

class Evaluator:
    def evaluate(self, trace: Trace, case: EvalCase, metric: MetricDef, conn: kuzu.Connection) -> list[Result]:
        raise NotImplementedError

class DeterministicEvaluator(Evaluator):
    def evaluate(self, trace: Trace, case: EvalCase, metric: MetricDef, conn: kuzu.Connection) -> list[Result]:
        if not metric.extractor_ref:
            raise ValueError("Deterministic metric needs an extractor_ref")
        
        ext_repo = ExtractorRepository(conn)
        extractor = ext_repo.get(metric.extractor_ref)
        if not extractor:
            raise ValueError(f"Extractor {metric.extractor_ref} not found")
            
        try:
            val = run_extractor(extractor, trace)
            
            # compare against ground_truth
            is_match = True
            if metric.ground_truth is not None and str(metric.ground_truth).strip() != "":
                try:
                    gt_str = str(metric.ground_truth).strip().lower()
                    val_str = str(val).strip().lower()
                    if gt_str in val_str or val_str in gt_str:
                        is_match = True
                    else:
                        is_match = (float(metric.ground_truth) == float(val))
                except Exception:
                    is_match = (str(metric.ground_truth).strip().lower() == str(val).strip().lower())
            else:
                is_match = bool(val)
                
            return [Result(
                name=metric.name,
                type=metric.result_type,
                value=is_match,
                enum_values=metric.enum_values,
                source="deterministic"
            )]
        except Exception as e:
            import traceback
            return [Result(
                name=metric.name,
                type=metric.result_type,
                value=False if metric.result_type == "bool" else (0 if metric.result_type == "int" else ""),
                traceback=traceback.format_exc(),
                source="deterministic"
            )]

class VerifierEvaluator(Evaluator):
    def evaluate(self, trace: Trace, case: EvalCase, metric: MetricDef, conn: kuzu.Connection) -> list[Result]:
        # Simple fallback verifier
        return [Result(
            name=metric.name,
            type=metric.result_type,
            value=True,
            source="verifier"
        )]
        # We do not have verifiers (in the RLVR sense) yet
        
class RubricEvaluator(Evaluator):
    def evaluate(self, trace: Trace, case: EvalCase, metric: MetricDef, conn: kuzu.Connection) -> list[Result]:
        if not metric.rubric_ref:
            raise ValueError("Rubric metric needs a rubric_ref")
            
        rubric_repo = RubricRepository(conn)
        rubric = rubric_repo.get(metric.rubric_ref)
        if not rubric:
            raise ValueError(f"Rubric {metric.rubric_ref} not found")
            
        try:
            parsed = judge_trace_with_rubric(rubric, trace)
            scores = parsed.model_dump()
            rationale = scores.get("rationale", "")

            results = []
            for item in rubric.items:
                val = scores.get(item.name)
                if item.type == "bool":
                    val = bool(val)
                elif item.type == "int":
                    val = int(val) if val is not None else 0
                elif item.type == "float":
                    val = float(val) if val is not None else 0.0
                else:
                    val = str(val) if val is not None else ""

                results.append(Result(
                    name=f"{metric.name} ({item.name})",
                    type=item.type,
                    value=val,
                    enum_values=item.enum_values,
                    confidence="high",
                    rationale=rationale,
                    source="llm_judge"
                ))
            return results
            
        except Exception:
            import traceback
            return [Result(
                name=f"{metric.name} ({item.name})",
                type=item.type,
                value=False if item.type == "bool" else (0 if item.type == "int" else ""),
                rationale=f"Judge failed: {traceback.format_exc()}",
                source="llm_judge"
            ) for item in rubric.items]

def score_trace(trace: Trace, case: EvalCase, conn: kuzu.Connection) -> list[Result]:
    results = []
    for metric in case.metrics:
        if metric.strategy == "deterministic":
            ev = DeterministicEvaluator()
        elif metric.strategy == "verifier":
            ev = VerifierEvaluator()
        elif metric.strategy == "rubric":
            ev = RubricEvaluator()
        else:
            continue
            
        results.extend(ev.evaluate(trace, case, metric, conn))
        
    return results
