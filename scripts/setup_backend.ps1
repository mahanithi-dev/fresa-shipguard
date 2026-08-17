Set-StrictMode -Version Latest
Write-Host 'Creating venv at backend\.venv'
python -m venv backend\.venv
Write-Host 'Upgrading pip and installing requirements'
& "backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
Write-Host 'Creating DB schema (backend)'
& "backend\.venv\Scripts\python.exe" -c "import os; os.chdir('backend'); from app.db import Base, engine; Base.metadata.create_all(bind=engine); print('DB created')"
Write-Host 'Seeding demo data'
& "backend\.venv\Scripts\python.exe" -c "import os; os.chdir('backend'); from app.seed import seed_demo_data; from app.db import SessionLocal; db=SessionLocal(); seed_demo_data(db); db.close(); print('Seeded')"
Write-Host 'Training model'
& "backend\.venv\Scripts\python.exe" backend\app\ml\train_model.py

Write-Host 'Setup complete.'
