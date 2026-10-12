import importlib

for m in ["fastapi", "uvicorn", "cv2", "ultralytics", "numpy", "yaml",
          "psycopg", "psycopg2", "sqlalchemy", "pydantic"]:
    try:
        mod = importlib.import_module(m)
        ver = getattr(mod, "__version__", "")
        print(f"  {m:12s} OK  {ver}")
    except Exception:
        print(f"  {m:12s} TIDAK ADA")