import sys
import importlib

sys.path.insert(0, "backend")

mods = ["app.routers.auth", "app.routers.reference", "app.routers.shipments", "app.routers.risk", "app.routers.ai"]
for m in mods:
    try:
        mod = importlib.import_module(m)
        print(f"Imported {m}: file={getattr(mod, '__file__', None)}")
        if hasattr(mod, 'router'):
            print(f"  -> has router: {mod.router.prefix if hasattr(mod.router, 'prefix') else 'prefix unknown'}")
    except Exception as e:
        print(f"Failed to import {m}: {e}")
