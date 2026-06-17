import os
import sys

# Ensure the repo root is on the path so `agentforge` package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agentforge.pipeline.orchestrator import Pipeline

app = FastAPI()

_allowed_origin = os.environ.get("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_allowed_origin] if _allowed_origin != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SprintRequest(BaseModel):
    title: str
    description: str


@app.get("/api/health")
@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
@app.post("/chat")
def run_sprint(req: SprintRequest):
    pipeline = Pipeline(verbose=False)

    outputs = pipeline.run(
        title=req.title,
        description=req.description,
    )

    return {
        "outputs": [
            {
                "role": o.role.value,
                "summary": o.summary,
                "approved": o.approved,
            }
            for o in outputs
        ]
    }
