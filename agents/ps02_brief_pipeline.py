from langgraph.graph import StateGraph, END
from core.state import BriefState
from core.tools import (
    create_notion_page, send_slack_message, update_airtable_record, log_event
)
from core.llm import get_llm
from core.prompts import BRIEF_INTERPRETATION_PROMPT
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
import re

KNOWN_CLIENTS = ["GlowSkin", "TechFlow", "FitLife"]
WRITER_ROSTER = {
    "GlowSkin": "Sarah",
    "TechFlow": "Mark",
    "FitLife": "Jessica"
}

def get_vector_store():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    docs = [
        Document(page_content="Brand: GlowSkin. Category: Skincare. Tone of voice: Authentic, empowering, not salesy. Focus on real results and scientific ingredients like Vitamin C and Hyaluronic Acid.", metadata={"brand": "GlowSkin"}),
        Document(page_content="Brand: TechFlow. Category: SaaS. Tone: Professional, crisp, innovative. Focus on productivity and saving time. Avoid jargon.", metadata={"brand": "TechFlow"}),
        Document(page_content="Brand: FitLife. Category: Fitness. Tone: Energetic, motivational, direct. Focus on consistency and community. Visuals should be bright and active.", metadata={"brand": "FitLife"})
    ]
    return FAISS.from_documents(docs, embeddings)

def validate_brief(state: BriefState) -> dict:
    flags = list(state.get("ambiguity_flags", []))
    status = state.get("status", "running")
    
    required = ["brand_name", "content_type", "key_message", "target_audience"]
    missing = [req for req in required if not state.get(req)]
    
    if missing:
        flags.append(f"Missing critical fields: {', '.join(missing)}")
        status = "flagged"
        
    if state.get("brand_name") not in KNOWN_CLIENTS:
        flags.append(f"Brand {state.get('brand_name')} not in known client list.")
        
    return {"ambiguity_flags": flags, "status": status, "steps_completed": state.get("steps_completed", []) + ["validate_brief"]}

def retrieve_brand_context(state: BriefState) -> dict:
    if state.get("status") == "flagged":
        return {}
        
    brand_name = state.get("brand_name", "")
    try:
        vs = get_vector_store()
        results = vs.similarity_search(brand_name, k=1)
        if results and brand_name.lower() in results[0].page_content.lower():
            brand_context = results[0].page_content
        else:
            brand_context = "No prior context found for this brand."
    except Exception as e:
        brand_context = f"Failed to retrieve context: {str(e)}"
        
    return {"brand_context": brand_context, "steps_completed": state.get("steps_completed", []) + ["retrieve_brand_context"]}

def interpret_brief(state: BriefState) -> dict:
    if state.get("status") == "flagged":
        return {}
        
    llm = get_llm()
    prompt = BRIEF_INTERPRETATION_PROMPT.format(
        raw_brief=json.dumps(state.get("input_data", {})),
        brand_context=state.get("brand_context", "None")
    )
    
    internal_brief = {}
    flags = list(state.get("ambiguity_flags", []))
    errors = list(state.get("errors", []))
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        # Extract JSON
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            internal_brief = parsed
            
            if parsed.get("ambiguity_flags"):
                flags.extend(parsed.get("ambiguity_flags"))
        else:
            errors.append("Failed to parse JSON from LLM response")
    except Exception as e:
        errors.append(f"Error in interpret_brief: {str(e)}")
        
    return {
        "internal_brief": internal_brief, 
        "ambiguity_flags": flags, 
        "errors": errors,
        "steps_completed": state.get("steps_completed", []) + ["interpret_brief"]
    }

def check_ambiguity(state: BriefState) -> dict:
    flags = state.get("ambiguity_flags", [])
    status = state.get("status", "running")
    
    if flags:
        status = "flagged"
        flags.append("Coordinator review needed due to ambiguities.")
        
    return {"status": status, "ambiguity_flags": flags, "steps_completed": state.get("steps_completed", []) + ["check_ambiguity"]}

def create_notion_brief(state: BriefState) -> dict:
    if state.get("status") == "flagged":
        return {}
        
    internal_brief = state.get("internal_brief", {})
    result = create_notion_page("brief_template", internal_brief)
    return {"notion_brief_url": result.get("url"), "steps_completed": state.get("steps_completed", []) + ["create_notion_brief"]}

def notify_scriptwriter(state: BriefState) -> dict:
    if state.get("status") == "flagged":
        return {}
        
    brand_name = state.get("brand_name", "")
    writer = WRITER_ROSTER.get(brand_name, "backup_writer")
    
    msg = f"New brief assigned to {writer} for {brand_name}. Link: {state.get('notion_brief_url')}"
    send_slack_message(f"#{writer.lower()}-assignments", msg)
    
    return {"scriptwriter_assigned": writer, "steps_completed": state.get("steps_completed", []) + ["notify_scriptwriter"]}

def update_tracker(state: BriefState) -> dict:
    if state.get("status") == "flagged":
        return {}
        
    update_airtable_record("mock_rec_id", {
        "status": state.get("status"),
        "timestamp": state.get("timestamp"),
        "scriptwriter": state.get("scriptwriter_assigned"),
        "notion_url": state.get("notion_brief_url")
    })
    
    status = "completed" if state.get("status") != "flagged" else "flagged"
    return {"status": status, "steps_completed": state.get("steps_completed", []) + ["update_tracker"]}

def log_brief(state: BriefState) -> dict:
    log_event(state.get("ps_id", "PS-02"), "brief_pipeline_finished", {
        "brand": state.get("brand_name"),
        "status": state.get("status"),
        "flags": state.get("ambiguity_flags")
    })
    return {"steps_completed": state.get("steps_completed", []) + ["log_brief"]}

def check_status(state: BriefState) -> str:
    if state.get("status") == "flagged":
        return "log_brief"
    return "create_notion_brief"

def build_ps02_graph() -> StateGraph:
    graph = StateGraph(BriefState)
    
    graph.add_node("validate_brief", validate_brief)
    graph.add_node("retrieve_brand_context", retrieve_brand_context)
    graph.add_node("interpret_brief", interpret_brief)
    graph.add_node("check_ambiguity", check_ambiguity)
    graph.add_node("create_notion_brief", create_notion_brief)
    graph.add_node("notify_scriptwriter", notify_scriptwriter)
    graph.add_node("update_tracker", update_tracker)
    graph.add_node("log_brief", log_brief)
    
    graph.set_entry_point("validate_brief")
    
    graph.add_edge("validate_brief", "retrieve_brand_context")
    graph.add_edge("retrieve_brand_context", "interpret_brief")
    graph.add_edge("interpret_brief", "check_ambiguity")
    
    graph.add_conditional_edges("check_ambiguity", check_status, {
        "log_brief": "log_brief",
        "create_notion_brief": "create_notion_brief"
    })
    
    graph.add_edge("create_notion_brief", "notify_scriptwriter")
    graph.add_edge("notify_scriptwriter", "update_tracker")
    graph.add_edge("update_tracker", "log_brief")
    graph.add_edge("log_brief", END)
    
    return graph
