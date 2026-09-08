"""FastAPI for ForgeKit."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from forgekit import __version__
from forgekit.factory import build_runtime
from forgekit.models import LoopMode

app = FastAPI(title="ForgeKit", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    goal: str
    mode: LoopMode = LoopMode.REACT


@app.get("/health")
def health() -> dict:
    return {"ok": True, "version": __version__}


@app.get("/tools")
def tools() -> list[dict]:
    runtime = build_runtime()
    return [s.model_dump() for s in runtime.tools.list_specs()]


@app.get("/skills")
def skills() -> dict:
    runtime = build_runtime()
    return {
        "index": [e.model_dump() for e in runtime.skills.list_index()],
        "prompt": runtime.skills.index_prompt(),
    }


@app.get("/memory")
def memory() -> dict:
    return build_runtime().memory.snapshot()


@app.post("/run")
async def run(req: RunRequest) -> dict:
    runtime = build_runtime()
    result = await runtime.run(req.goal, mode=req.mode)
    return result.model_dump(mode="json")
