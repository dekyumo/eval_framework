import tempfile

from src.eval_workbench.web.app import create_app


def test_health(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_spa_route_serves_index(client):
    response = client.get('/agents')
    assert response.status_code == 200
    assert b'<div id="root"' in response.data


def test_spa_route_cases(client):
    response = client.get('/cases')
    assert response.status_code == 200
    assert b'<div id="root"' in response.data


def test_db_reset_route_not_registered_by_default():
    with tempfile.TemporaryDirectory() as repo_path:
        app = create_app(repo_path=repo_path, allow_db_wipe=False)
        client = app.test_client()
        response = client.post('/api/test/reset')
        assert response.status_code == 403
        assert 'DB wipe is disabled' in response.json['error']


def test_db_reset_route_available_when_enabled(monkeypatch):
    monkeypatch.setattr(
        'src.eval_workbench.web.app.repo_service.reset_database',
        lambda _repo_path: {"status": "reset_success"},
    )
    with tempfile.TemporaryDirectory() as repo_path:
        app = create_app(repo_path=repo_path, allow_db_wipe=True)
        client = app.test_client()
        response = client.post('/api/test/reset')
        assert response.status_code == 200
        assert response.json == {"status": "reset_success"}
