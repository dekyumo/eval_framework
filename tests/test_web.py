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
