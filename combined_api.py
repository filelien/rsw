"""RAXUS Combined API Server - All services on a single port for Render"""
import sys
import os
import importlib.util

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAXUS API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "services": ["gateway", "alertmanager", "inventory", "notifier", "taskmanager", "slo-engine", "rules-engine"]}


@app.get("/")
async def root():
    return {"message": "RAXUS API - All services running", "docs": "/docs"}


def load_service_app(service_name: str, service_dir: str):
    """Load a service's FastAPI app from its main.py using importlib"""
    main_path = os.path.join(service_dir, "main.py")
    if not os.path.exists(main_path):
        print(f"Warning: {main_path} not found")
        return None
    spec = importlib.util.spec_from_file_location(f"{service_name}_main", main_path)
    mod = importlib.util.module_from_spec(spec)
    # Add service dir to sys.path so relative imports work
    abs_dir = os.path.abspath(service_dir)
    if abs_dir not in sys.path:
        sys.path.insert(0, abs_dir)
    spec.loader.exec_module(mod)
    return getattr(mod, "app", None)


# Mount each service under a prefix
MOUNT_CONFIG = [
    ("alertmanager", "services/alertmanager", "/alertmanager"),
    ("inventory", "services/inventory", "/inventory"),
    ("notifier", "services/notifier", "/notifier"),
    ("taskmanager", "services/taskmanager", "/taskmanager"),
    ("slo_engine", "services/slo-engine", "/slo"),
    ("rules_engine", "services/rules-engine", "/rules"),
]

for service_name, service_dir, prefix in MOUNT_CONFIG:
    try:
        svc_app = load_service_app(service_name, service_dir)
        if svc_app:
            app.mount(prefix, svc_app)
            print(f"Mounted {service_name} at {prefix}")
    except Exception as e:
        print(f"Warning: Could not mount {service_name}: {e}")

# Gateway routes at root level
try:
    gateway_app = load_service_app("gateway", "services/gateway")
    if gateway_app:
        for route in gateway_app.routes:
            if hasattr(route, "path") and route.path.startswith("/api"):
                app.routes.append(route)
        print("Mounted gateway routes at root")
except Exception as e:
    print(f"Warning: Could not mount gateway routes: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
