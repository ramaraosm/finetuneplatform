/finetune-platform/
├── backend/            # FastAPI service
│   ├── app/
│   │   ├── api/
│   │   ├── core/       # Config, security
│   │   ├── crud/
│   │   ├── models/     # Pydantic models
│   │   ├── schemas/    # SQLAlchemy models
│   │   ├── services/   # Business logic (HF, S3, etc.)
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/           # React App
│   ├── public/
│   ├── src/
│   └── package.json
|    |--- Dockerfile
├── worker/             # RunPod Worker
│   ├── app/
│   │   ├── main.py     # Worker entrypoint
│   │   └── finetune.py # Unsloth logic
│   ├── Dockerfile
│   └── requirements.txt
├── shared/                   # <--- This is your 'shared' package
│   ├── __init__.py
│   └── db/
│       ├── __init__.py
│       └── base.py
├── k8s/                # Kubernetes manifests
└── docker-compose.yml  # For local development
