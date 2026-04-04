import pytest


@pytest.mark.asyncio
async def test_health(client):
    async with client as c:
        r = await c.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root(client):
    async with client as c:
        r = await c.get("/")
    assert r.status_code == 200
    assert "name" in r.json()


@pytest.mark.asyncio
async def test_list_jobs_default(client):
    async with client as c:
        r = await c.get("/api/jobs")
    assert r.status_code == 200
    data = r.json()
    assert "jobs" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert data["total"] >= 50
    assert len(data["jobs"]) <= 20


@pytest.mark.asyncio
async def test_list_jobs_pagination(client):
    async with client as c:
        r1 = await c.get("/api/jobs?page=1&limit=5")
        r2 = await c.get("/api/jobs?page=2&limit=5")
    assert r1.status_code == 200
    assert r2.status_code == 200
    ids1 = [j["id"] for j in r1.json()["jobs"]]
    ids2 = [j["id"] for j in r2.json()["jobs"]]
    assert len(set(ids1) & set(ids2)) == 0  # no overlap


@pytest.mark.asyncio
async def test_list_jobs_search(client):
    async with client as c:
        r = await c.get("/api/jobs?search=Engineer")
    assert r.status_code == 200
    jobs = r.json()["jobs"]
    for job in jobs:
        assert "engineer" in job["title"].lower() or "engineer" in job["company"].lower()


@pytest.mark.asyncio
async def test_list_jobs_filter_remote(client):
    async with client as c:
        r = await c.get("/api/jobs?remote=Remote")
    assert r.status_code == 200
    for job in r.json()["jobs"]:
        assert job["remote"] == "Remote"


@pytest.mark.asyncio
async def test_get_job_by_id(client):
    async with client as c:
        jobs_r = await c.get("/api/jobs?limit=1")
        job_id = jobs_r.json()["jobs"][0]["id"]
        r = await c.get(f"/api/jobs/{job_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == job_id
    assert "title" in data
    assert "company" in data
    assert "salary_min" in data


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    async with client as c:
        r = await c.get("/api/jobs/999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_skill_stats(client):
    async with client as c:
        r = await c.get("/api/stats/skills")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "skill" in first
    assert "count" in first
    assert "avg_salary" in first
    # Should be sorted by count descending
    counts = [d["count"] for d in data]
    assert counts == sorted(counts, reverse=True)


@pytest.mark.asyncio
async def test_salary_stats(client):
    async with client as c:
        r = await c.get("/api/stats/salary")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert "category" in item
        assert "avg_min" in item
        assert "avg_max" in item
        assert item["avg_max"] >= item["avg_min"]


@pytest.mark.asyncio
async def test_trends(client):
    async with client as c:
        r = await c.get("/api/stats/trends")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 12
    for point in data:
        assert "date" in point
        assert "count" in point
        assert "avg_salary" in point


@pytest.mark.asyncio
async def test_summary_stats(client):
    async with client as c:
        r = await c.get("/api/stats/summary")
    assert r.status_code == 200
    data = r.json()
    assert "total_jobs" in data
    assert "avg_salary_min" in data
    assert "avg_salary_max" in data
    assert "remote_jobs" in data
    assert "remote_pct" in data
    assert "categories" in data
    assert data["total_jobs"] >= 50
    assert data["avg_salary_max"] >= data["avg_salary_min"]


@pytest.mark.asyncio
async def test_categories(client):
    async with client as c:
        r = await c.get("/api/categories")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
