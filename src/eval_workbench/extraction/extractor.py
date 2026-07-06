import hashlib
import importlib.util
import os
from pathlib import Path

from src.eval_workbench.domain.extractor import Extractor
from src.eval_workbench.domain.trace import Trace
from src.eval_workbench.repo_layout import extractor_source_path


def fingerprint_source(source_text: str) -> str:
    return hashlib.sha256(source_text.strip().encode()).hexdigest()


def save_extractor_source(repo_path: str | Path, extractor_id: str, python_code: str) -> str:
    path = extractor_source_path(repo_path, extractor_id)
    path.write_text(python_code, encoding="utf-8")
    return str(path)


def read_extractor_source(source_path: str | Path) -> str:
    return Path(source_path).read_text(encoding="utf-8")


def generate_extractor_code(description: str) -> str:
    from src.eval_workbench.agents.extractor_author.agent import root_agent
    from google import genai

    client = genai.Client()
    prompt = f"""
{root_agent.instruction}

The user wants to extract: "{description}".

Return ONLY the python code for the `extract` function inside a standard markdown code block.
Do not add any explanations outside of the code block.
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = response.text or ""
    if "```python" in text:
        return text.split("```python")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text.strip()


def run_extractor(extractor: Extractor, trace: Trace) -> bool | int | float | str:
    if not os.path.exists(extractor.source_path):
        raise FileNotFoundError(f"Extractor source {extractor.source_path} not found")

    spec = importlib.util.spec_from_file_location(f"ext_{extractor.id}", extractor.source_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {extractor.source_path}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if not hasattr(mod, "extract"):
        raise ValueError(f"Extractor {extractor.id} must define an `extract(trace: Trace)` function")

    return mod.extract(trace)
