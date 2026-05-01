"""Proxy routers for microservices — inventory, tasks, SLO, notifications, rules, tickets"""
from fastapi import APIRouter, Depends, Request
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.core.config import settings
import httpx

# ─── Helpers ─────────────────────────────────────────────────────
async def proxy(base_url: str, path: str, method: str = "GET", data=None, params=None):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.request(method, f"{base_url}{path}", json=data, params=params)
        return r.json()

# ─── INVENTORY ───────────────────────────────────────────────────
inventory_router = APIRouter()

@inventory_router.get("/datacenters")
async def list_datacenters(current_user: User = Depends(get_current_user)):
    return await proxy(settings.INVENTORY_URL, "/api/v1/datacenters")

@inventory_router.post("/datacenters")
async def create_datacenter(request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.INVENTORY_URL, "/api/v1/datacenters", "POST", await request.json())

@inventory_router.get("/datacenters/{dc_id}")
async def get_datacenter(dc_id: str, current_user: User = Depends(get_current_user)):
    return await proxy(settings.INVENTORY_URL, f"/api/v1/datacenters/{dc_id}")

@inventory_router.patch("/datacenters/{dc_id}")
async def update_datacenter(dc_id: str, request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.INVENTORY_URL, f"/api/v1/datacenters/{dc_id}", "PATCH", await request.json())

@inventory_router.delete("/datacenters/{dc_id}")
async def delete_datacenter(dc_id: str, current_user: User = Depends(require_role("admin"))):
    return await proxy(settings.INVENTORY_URL, f"/api/v1/datacenters/{dc_id}", "DELETE")

@inventory_router.get("/environments")
async def list_environments(current_user: User = Depends(get_current_user)):
    return await proxy(settings.INVENTORY_URL, "/api/v1/environments")

@inventory_router.post("/environments")
async def create_environment(request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.INVENTORY_URL, "/api/v1/environments", "POST", await request.json())

@inventory_router.get("/servers")
async def list_servers(current_user: User = Depends(get_current_user)):
    return await proxy(settings.INVENTORY_URL, "/api/v1/servers")

@inventory_router.post("/servers")
async def create_server(request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.INVENTORY_URL, "/api/v1/servers", "POST", await request.json())

@inventory_router.get("/servers/{server_id}")
async def get_server(server_id: str, current_user: User = Depends(get_current_user)):
    return await proxy(settings.INVENTORY_URL, f"/api/v1/servers/{server_id}")

@inventory_router.patch("/servers/{server_id}")
async def update_server(server_id: str, request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.INVENTORY_URL, f"/api/v1/servers/{server_id}", "PATCH", await request.json())

@inventory_router.delete("/servers/{server_id}")
async def delete_server(server_id: str, current_user: User = Depends(require_role("admin"))):
    return await proxy(settings.INVENTORY_URL, f"/api/v1/servers/{server_id}", "DELETE")

@inventory_router.get("/components")
async def list_components(current_user: User = Depends(get_current_user)):
    return await proxy(settings.INVENTORY_URL, "/api/v1/components")

@inventory_router.post("/components")
async def create_component(request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.INVENTORY_URL, "/api/v1/components", "POST", await request.json())

@inventory_router.get("/stats")
async def inventory_stats(current_user: User = Depends(get_current_user)):
    return await proxy(settings.INVENTORY_URL, "/api/v1/stats")

# ─── TASKS ───────────────────────────────────────────────────────
tasks_router = APIRouter()

@tasks_router.get("")
async def list_tasks(current_user: User = Depends(get_current_user)):
    return await proxy(settings.TASKMANAGER_URL, "/api/v1/tasks")

@tasks_router.post("")
async def create_task(request: Request, current_user: User = Depends(require_role("admin","operator"))):
    data = await request.json()
    data["created_by"] = current_user.id
    return await proxy(settings.TASKMANAGER_URL, "/api/v1/tasks", "POST", data)

@tasks_router.get("/{task_id}")
async def get_task(task_id: str, current_user: User = Depends(get_current_user)):
    return await proxy(settings.TASKMANAGER_URL, f"/api/v1/tasks/{task_id}")

@tasks_router.patch("/{task_id}")
async def update_task(task_id: str, request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.TASKMANAGER_URL, f"/api/v1/tasks/{task_id}", "PATCH", await request.json())

@tasks_router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: User = Depends(require_role("admin"))):
    return await proxy(settings.TASKMANAGER_URL, f"/api/v1/tasks/{task_id}", "DELETE")

@tasks_router.post("/{task_id}/execute")
async def execute_task(task_id: str, request: Request, current_user: User = Depends(require_role("admin","operator"))):
    data = (await request.json()) if request.headers.get("content-type") == "application/json" else {}
    data["triggered_by"] = current_user.id
    return await proxy(settings.TASKMANAGER_URL, f"/api/v1/tasks/{task_id}/execute", "POST", data)

@tasks_router.get("/executions")
async def list_executions(current_user: User = Depends(get_current_user)):
    return await proxy(settings.TASKMANAGER_URL, "/api/v1/executions")

@tasks_router.get("/schedules")
async def list_schedules(current_user: User = Depends(get_current_user)):
    return await proxy(settings.TASKMANAGER_URL, "/api/v1/schedules")

@tasks_router.post("/schedules")
async def create_schedule(request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.TASKMANAGER_URL, "/api/v1/schedules", "POST", await request.json())

# ─── SLO ─────────────────────────────────────────────────────────
slo_router = APIRouter()

@slo_router.get("")
async def list_slos(current_user: User = Depends(get_current_user)):
    return await proxy(settings.SLO_URL, "/api/v1/slo")

@slo_router.post("")
async def create_slo(request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.SLO_URL, "/api/v1/slo", "POST", await request.json())

@slo_router.get("/{slo_id}")
async def get_slo(slo_id: str, current_user: User = Depends(get_current_user)):
    return await proxy(settings.SLO_URL, f"/api/v1/slo/{slo_id}")

@slo_router.patch("/{slo_id}")
async def update_slo(slo_id: str, request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.SLO_URL, f"/api/v1/slo/{slo_id}", "PATCH", await request.json())

@slo_router.delete("/{slo_id}")
async def delete_slo(slo_id: str, current_user: User = Depends(require_role("admin"))):
    return await proxy(settings.SLO_URL, f"/api/v1/slo/{slo_id}", "DELETE")

@slo_router.get("/probes")
async def list_probes(current_user: User = Depends(get_current_user)):
    return await proxy(settings.SLO_URL, "/api/v1/probes")

@slo_router.post("/probes")
async def create_probe(request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.SLO_URL, "/api/v1/probes", "POST", await request.json())

@slo_router.get("/stats")
async def slo_stats(current_user: User = Depends(get_current_user)):
    return await proxy(settings.SLO_URL, "/api/v1/stats")

# ─── NOTIFICATIONS ───────────────────────────────────────────────
notifications_router = APIRouter()

@notifications_router.get("")
async def list_notifiers(current_user: User = Depends(get_current_user)):
    return await proxy(settings.NOTIFIER_URL, "/api/v1/notifiers")

@notifications_router.post("")
async def create_notifier(request: Request, current_user: User = Depends(require_role("admin"))):
    return await proxy(settings.NOTIFIER_URL, "/api/v1/notifiers", "POST", await request.json())

@notifications_router.patch("/{notifier_id}")
async def update_notifier(notifier_id: str, request: Request, current_user: User = Depends(require_role("admin"))):
    return await proxy(settings.NOTIFIER_URL, f"/api/v1/notifiers/{notifier_id}", "PATCH", await request.json())

@notifications_router.delete("/{notifier_id}")
async def delete_notifier(notifier_id: str, current_user: User = Depends(require_role("admin"))):
    return await proxy(settings.NOTIFIER_URL, f"/api/v1/notifiers/{notifier_id}", "DELETE")

@notifications_router.post("/{notifier_id}/test")
async def test_notifier(notifier_id: str, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.NOTIFIER_URL, f"/api/v1/notifiers/{notifier_id}/test", "POST", {})

@notifications_router.get("/history")
async def notification_history(current_user: User = Depends(get_current_user)):
    return await proxy(settings.NOTIFIER_URL, "/api/v1/history")

# ─── RULES ───────────────────────────────────────────────────────
rules_router = APIRouter()

@rules_router.get("")
async def list_rules(current_user: User = Depends(get_current_user)):
    return await proxy(settings.RULES_URL, "/api/v1/rules")

@rules_router.post("")
async def create_rule(request: Request, current_user: User = Depends(require_role("admin","operator"))):
    data = await request.json()
    data["created_by"] = current_user.id
    return await proxy(settings.RULES_URL, "/api/v1/rules", "POST", data)

@rules_router.get("/{rule_id}")
async def get_rule(rule_id: str, current_user: User = Depends(get_current_user)):
    return await proxy(settings.RULES_URL, f"/api/v1/rules/{rule_id}")

@rules_router.patch("/{rule_id}")
async def update_rule(rule_id: str, request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.RULES_URL, f"/api/v1/rules/{rule_id}", "PATCH", await request.json())

@rules_router.delete("/{rule_id}")
async def delete_rule(rule_id: str, current_user: User = Depends(require_role("admin"))):
    return await proxy(settings.RULES_URL, f"/api/v1/rules/{rule_id}", "DELETE")

@rules_router.post("/{rule_id}/test")
async def test_rule(rule_id: str, request: Request, current_user: User = Depends(require_role("admin","operator"))):
    return await proxy(settings.RULES_URL, f"/api/v1/rules/{rule_id}/test", "POST", await request.json())

# ─── TICKETS ─────────────────────────────────────────────────────
tickets_router = APIRouter()

@tickets_router.get("")
async def list_tickets(current_user: User = Depends(get_current_user)):
    return await proxy(settings.GATEWAY_URL if hasattr(settings, 'GATEWAY_URL') else "http://localhost:8000", "/api/v1/tickets-internal")

@tickets_router.post("")
async def create_ticket(request: Request, current_user: User = Depends(get_current_user)):
    data = await request.json()
    data["created_by"] = current_user.id
    return await proxy(settings.ALERTMANAGER_URL, "/api/v1/tickets", "POST", data)

@tickets_router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, current_user: User = Depends(get_current_user)):
    return await proxy(settings.ALERTMANAGER_URL, f"/api/v1/tickets/{ticket_id}")

@tickets_router.patch("/{ticket_id}")
async def update_ticket(ticket_id: str, request: Request, current_user: User = Depends(get_current_user)):
    return await proxy(settings.ALERTMANAGER_URL, f"/api/v1/tickets/{ticket_id}", "PATCH", await request.json())

@tickets_router.post("/{ticket_id}/comments")
async def add_comment(ticket_id: str, request: Request, current_user: User = Depends(get_current_user)):
    data = await request.json()
    data["user_id"] = current_user.id
    return await proxy(settings.ALERTMANAGER_URL, f"/api/v1/tickets/{ticket_id}/comments", "POST", data)

# Export all routers with proper names for main.py
inventory = type("M", (), {"router": inventory_router})()
tasks = type("M", (), {"router": tasks_router})()
slo = type("M", (), {"router": slo_router})()
notifications = type("M", (), {"router": notifications_router})()
rules = type("M", (), {"router": rules_router})()
tickets = type("M", (), {"router": tickets_router})()
