import sys
import importlib

sys.path.insert(0, "backend")

try:
    m = importlib.import_module("app.main")
    app = m.app
    print("App title:", getattr(app, 'title', None))
    print("Registered routes:")
    for route in app.routes:
        methods = ','.join(sorted(route.methods or []))
        print(f"{route.path} -> {methods} (name={route.name})")
except Exception as e:
    print("Import failed:", e)
    raise
