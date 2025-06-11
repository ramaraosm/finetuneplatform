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


Commands for CPU mode:
docker-compose -f docker-compose.cpu.yml build
docker-compose -f docker-compose.cpu.yml up -d
docker-compose -f docker-compose.cpu.yml down

To access the project :
http://localhost:3000/
http://localhost:8000/docs - for swagger docs

![image](https://github.com/user-attachments/assets/47e7e0fb-3790-44f6-b68c-49d34c495e05)


