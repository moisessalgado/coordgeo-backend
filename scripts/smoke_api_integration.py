import json
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000/api/v1"


def post(path: str, data: dict, headers: dict | None = None):
    body = json.dumps(data).encode("utf-8")
    request = urllib.request.Request(f"{BASE_URL}{path}", data=body, method="POST")
    request.add_header("Content-Type", "application/json")

    for key, value in (headers or {}).items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = response.read().decode("utf-8")
            return response.getcode(), json.loads(payload) if payload else {}
    except urllib.error.HTTPError as error:
        payload = error.read().decode("utf-8")
        try:
            payload = json.loads(payload)
        except Exception:
            pass
        return error.code, payload


def get(path: str, headers: dict | None = None):
    request = urllib.request.Request(f"{BASE_URL}{path}", method="GET")

    for key, value in (headers or {}).items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = response.read().decode("utf-8")
            return response.getcode(), json.loads(payload) if payload else {}
    except urllib.error.HTTPError as error:
        payload = error.read().decode("utf-8")
        try:
            payload = json.loads(payload)
        except Exception:
            pass
        return error.code, payload


def run_smoke_test():
    report: list[dict] = []

    status, demo_tokens = post(
        "/token/",
        {"email": "demo@coordgeo.local", "password": "Passw0rd!"},
    )
    report.append({"check": "login_demo", "status": status})

    demo_auth = {"Authorization": f"Bearer {demo_tokens.get('access', '')}"} if status == 200 else {}

    status, organizations = get("/user/organizations/", headers=demo_auth)
    report.append(
        {
            "check": "org_bootstrap_demo",
            "status": status,
            "organizations": len(organizations) if isinstance(organizations, list) else None,
        }
    )

    organization_id = (
        str(organizations[0]["id"])
        if status == 200 and isinstance(organizations, list) and organizations
        else None
    )

    valid_headers = dict(demo_auth)
    if organization_id:
        valid_headers["X-Organization-ID"] = organization_id

    status, projects = get("/projects/", headers=valid_headers)
    report.append(
        {
            "check": "projects_with_org",
            "status": status,
            "count": projects.get("count") if isinstance(projects, dict) else None,
        }
    )

    status, layers = get("/layers/", headers=valid_headers)
    report.append(
        {
            "check": "layers_with_org",
            "status": status,
            "count": layers.get("count") if isinstance(layers, dict) else None,
        }
    )

    status, datasources = get("/datasources/", headers=valid_headers)
    report.append(
        {
            "check": "datasources_with_org",
            "status": status,
            "count": datasources.get("count") if isinstance(datasources, dict) else None,
        }
    )

    status, _ = get("/projects/", headers=demo_auth)
    report.append({"check": "projects_missing_org_header", "status": status})

    status, outsider_tokens = post(
        "/token/",
        {"email": "outsider@coordgeo.local", "password": "Passw0rd!"},
    )
    report.append({"check": "login_outsider", "status": status})

    outsider_headers = (
        {"Authorization": f"Bearer {outsider_tokens.get('access', '')}"}
        if status == 200
        else {}
    )
    if organization_id:
        outsider_headers["X-Organization-ID"] = organization_id

    status, _ = get("/projects/", headers=outsider_headers)
    report.append({"check": "projects_outsider_forbidden", "status": status})

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_smoke_test()
