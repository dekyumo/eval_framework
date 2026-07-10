from src.eval_workbench.services import registries as registries_service


def test_rubric_field_description_round_trip(tmp_path):
    repo_path = str(tmp_path)
    created = registries_service.create_rubric(repo_path, {
        "id": "rubric_test",
        "name": "Test Rubric",
        "instructions": "Grade it",
        "items": [{"name": "is_good", "type": "bool", "description": "Was the answer good?"}],
        "default_judge_prompt": "Judge: {instructions}",
        "version": 1,
        "fingerprint": "test",
        "frozen": False,
    })

    assert created["items"][0]["prompt"] == "Was the answer good?"
    assert created["items"][0]["description"] == "Was the answer good?"

    listed = registries_service.list_rubrics(repo_path)
    assert listed[0]["items"][0]["description"] == "Was the answer good?"
