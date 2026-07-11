import pytest
import kuzu
from src.eval_workbench.storage.schema import init_schema
from src.eval_workbench.domain.trace import Trace
from src.eval_workbench.domain.case import EvalCase, MetricDef
from src.eval_workbench.domain.extractor import Extractor
from src.eval_workbench.storage.repositories import ExtractorRepository
from src.eval_workbench.services.scoring import score_trace
import tempfile
import os

def test_scoring():
    # Setup in-memory kuzu db
    tmp = tempfile.mkdtemp()
    db = kuzu.Database(os.path.join(tmp, "db.kuzu"))
    conn = kuzu.Connection(db)
    init_schema(conn)
    
    # Create an extractor that just returns true
    ext_code = """
def extract(trace):
    return True
"""
    ext_path = os.path.join(tmp, "my_ext.py")
    with open(ext_path, "w") as f:
        f.write(ext_code)
        
    ext = Extractor(
        id="ext1",
        name="my_ext",
        return_type="bool",
        source_path=ext_path,
        fingerprint="fingerprint123"
    )
    ExtractorRepository(conn).save(ext)
    
    # Create case and trace
    metric = MetricDef(
        id="m1",
        name="test_metric",
        strategy="deterministic",
        result_type="bool",
        extractor_ref="ext1"
    )
    case = EvalCase(
        id="c1",
        dataset_id="ds1",
        conversation=[],
        distribution_position="in",
        problem_type="happy",
        metrics=[metric]
    )
    trace = Trace(
        id="t1",
        parts=[],
        snapshot_id="s1",
        case_id="c1",
        model_id="gemini-2.5-flash"
    )
    
    results = score_trace(trace, case, conn)
    assert len(results) == 1
    assert results[0].value == True
    assert results[0].name == "test_metric"
    
    conn.close()
    db.close()
