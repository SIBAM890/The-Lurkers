from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import uvicorn
from datetime import datetime

from core.runner import run_agent
from core.logger import get_logger

app = FastAPI(title="Scrollhouse Agent API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger()

class AgentRequest(BaseModel):
    data: dict

class WebhookRequest(BaseModel):
    thread_id: str
    message: str = None
    is_timeout: bool = False

@app.get("/")
def health_check():
    return {"status": "running", "agents": ["ps01", "ps02", "ps03", "ps04"]}

@app.post("/ps01")
def run_ps01(request: AgentRequest):
    from agents.ps01_onboarding import build_ps01_graph
    from core.state import OnboardingState
    graph = build_ps01_graph()
    initial_state = {
        "ps_id": "PS-01",
        "status": "running",
        "input_data": request.data,
        "steps_completed": [],
        "errors": [],
        "flags": [],
        "output": {},
        "timestamp": datetime.now().isoformat(),
        "welcome_email_sent": False,
        "drive_folder_url": None,
        "notion_page_url": None,
        "airtable_record_id": None,
        **request.data
    }
    return run_agent(graph, initial_state, "PS-01")

@app.post("/ps02")
def run_ps02(request: AgentRequest):
    from agents.ps02_brief_pipeline import build_ps02_graph
    graph = build_ps02_graph()
    initial_state = {
        "ps_id": "PS-02",
        "status": "running",
        "input_data": request.data,
        "steps_completed": [],
        "errors": [],
        "flags": [],
        "output": {},
        "timestamp": datetime.now().isoformat(),
        "brand_context": None,
        "internal_brief": None,
        "notion_brief_url": None,
        "scriptwriter_assigned": None,
        "ambiguity_flags": [],
        **request.data
    }
    return run_agent(graph, initial_state, "PS-02")

@app.post("/ps03")
def run_ps03(request: AgentRequest):
    from agents.ps03_approval_loop import build_ps03_graph
    thread_id = request.data.get("thread_id", f"PS03_{datetime.now().timestamp()}")
    graph = build_ps03_graph()
    initial_state = {
        "ps_id": "PS-03",
        "status": "running",
        "input_data": request.data,
        "steps_completed": [],
        "errors": [],
        "flags": [],
        "output": {},
        "timestamp": datetime.now().isoformat(),
        "approval_status": "pending",
        "follow_up_count": 0,
        "revision_notes": None,
        "version_number": 1,
        "max_loops": 0,
        **request.data
    }
    return run_agent(graph, initial_state, "PS-03", thread_id=thread_id, interrupt_before=["process_response"])

@app.post("/ps03/reply")
def ps03_reply(req: WebhookRequest):
    from agents.ps03_approval_loop import build_ps03_graph
    from core.runner import resume_agent
    graph = build_ps03_graph()
    
    update_data = {}
    if req.is_timeout:
        update_data = {"output": {"timeout": True}}
    elif req.message:
        update_data = {"output": {"client_response": req.message}}
        
    return resume_agent(graph, req.thread_id, "PS-03", update_state=update_data)

@app.post("/ps04")
def run_ps04(request: AgentRequest):
    from agents.ps04_reporting import ps04_reporting_agent
    return ps04_reporting_agent(request.data)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
