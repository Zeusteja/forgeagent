import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agentforge.pipeline.orchestrator import Pipeline

app = FastAPI()

# Allow the separately-deployed Next.js frontend (or local dev) to call this API.
# Set FRONTEND_ORIGIN to your frontend's deployed URL in Vercel's project
# environment variables to lock this down; defaults to "*" for easy setup.
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

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/chat")
def run_sprint(req: SprintRequest):
    pipeline = Pipeline(verbose=False)

    outputs = pipeline.run(
        title=req.title,
        description=req.description
    )

    return {
        "outputs": [
            {
                "role": o.role.value,
                "summary": o.summary,
                "approved": o.approved
            }
            for o in outputs
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
