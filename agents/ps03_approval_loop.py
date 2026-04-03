import json
from langgraph.graph import StateGraph, END
from core.state import ApprovalState
from core.tools import (
    send_email, send_slack_message, update_airtable_record, log_event
)
from core.llm import get_llm
from core.prompts import APPROVAL_MESSAGE_PROMPT, FOLLOW_UP_PROMPT, RESPONSE_EVALUATION_PROMPT
from datetime import datetime, timedelta

def prepare_approval_request(state: ApprovalState) -> dict:
    llm = get_llm()
    deadline = (datetime.now() + timedelta(hours=state.get("response_sla_hours", 48))).strftime("%Y-%m-%d %H:%M")
    
    prompt = APPROVAL_MESSAGE_PROMPT.format(
        client_name=state.get("client_name", ""),
        version_number=state.get("version_number", 1),
        deadline=deadline,
        script_text=state.get("script_text", ""),
        channel=state.get("preferred_channel", "email")
    )
    
    response = llm.invoke(prompt)
    message_text = response.content
    
    return {
        "approval_status": "pending",
        "output": {**state.get("output", {}), "approval_message": message_text},
        "steps_completed": state.get("steps_completed", []) + ["prepare_approval_request"],
        "max_loops": state.get("max_loops", 0) + 1
    }

def send_approval_request(state: ApprovalState) -> dict:
    msg = state.get("output", {}).get("approval_message", "Please approve.")
    if state.get("preferred_channel") == "slack":
        send_slack_message(f"@{state.get('client_contact')}", msg)
    else:
        send_email(state.get("client_contact", ""), "Script Approval Needed", msg)
        
    log_event(state.get("ps_id", "PS-03"), "approval_request_sent", {"version": state.get("version_number")})
    return {"steps_completed": state.get("steps_completed", []) + ["send_approval_request"]}

def process_response(state: ApprovalState) -> dict:
    # Check if a client response was injected via state update or if it's a timeout
    client_response = state.get("output", {}).get("client_response")
    timeout = state.get("output", {}).get("timeout", False)
    
    approval_status = state.get("approval_status", "pending")
    status = state.get("status", "running")
    version_number = state.get("version_number", 1)
    follow_up_count = state.get("follow_up_count", 0)
    revision_notes = state.get("revision_notes")
    max_loops = state.get("max_loops", 0)
    
    if max_loops >= 5:
        approval_status = "escalated"
        return {"approval_status": approval_status, "status": "completed"}
        
    if timeout:
        follow_up_count += 1
        if follow_up_count >= 2:
            approval_status = "escalated"
        else:
            approval_status = "pending"
    elif client_response:
        # Pass to LLM using RESPONSE_EVALUATION_PROMPT
        llm = get_llm()
        prompt = RESPONSE_EVALUATION_PROMPT.format(client_response=client_response)
        res = llm.invoke(prompt)
        
        try:
            parsed = json.loads(res.content.replace("```json", "").replace("```", "").strip())
            intent = parsed.get("intent", "revision_requested")
            notes = parsed.get("revision_notes")
        except:
            intent = "escalate"
            notes = None
            
        if intent == "approved":
            approval_status = "approved"
            status = "completed"
        elif intent == "revision_requested":
            revision_notes = notes
            version_number += 1
            approval_status = "revision_requested"
        elif intent == "escalate":
            approval_status = "escalated"

    return {
        "approval_status": approval_status,
        "status": status,
        "version_number": version_number,
        "follow_up_count": follow_up_count,
        "revision_notes": revision_notes,
        "output": {**state.get("output", {}), "client_response": None, "timeout": False}, # Reset flags
        "steps_completed": state.get("steps_completed", []) + ["process_response"]
    }

def send_follow_up(state: ApprovalState) -> dict:
    llm = get_llm()
    deadline = (datetime.now() + timedelta(hours=state.get("response_sla_hours", 48))).strftime("%Y-%m-%d %H:%M")
    
    prompt = FOLLOW_UP_PROMPT.format(
        client_name=state.get("client_name", ""),
        follow_up_count=state.get("follow_up_count", 1),
        original_sent=state.get("timestamp", ""),
        deadline=deadline,
        channel=state.get("preferred_channel", "email")
    )
    
    response = llm.invoke(prompt)
    msg = response.content
    
    if state.get("preferred_channel") == "slack":
        send_slack_message(f"@{state.get('client_contact')}", msg)
    else:
        send_email(state.get("client_contact", ""), "Action Required: Script Approval", msg)
        
    return {"steps_completed": state.get("steps_completed", []) + ["send_follow_up"]}

def escalate(state: ApprovalState) -> dict:
    send_email(
        "manager@scrollhouse.com",
        f"Escalation: {state.get('client_name')} Script Approval",
        f"Approval looped {state.get('max_loops')} times or max follow ups reached or client requested a call."
    )
    return {"status": "escalated", "steps_completed": state.get("steps_completed", []) + ["escalate"]}

def update_tracker(state: ApprovalState) -> dict:
    update_airtable_record("mock_rec_id", {
        "approval_status": state.get("approval_status"),
        "version": state.get("version_number"),
        "status": state.get("status")
    })
    return {"steps_completed": state.get("steps_completed", []) + ["update_tracker"]}

def log_approval(state: ApprovalState) -> dict:
    log_event(state.get("ps_id", "PS-03"), "approval_loop_finished", {
        "final_status": state.get("approval_status"),
        "version": state.get("version_number")
    })
    return {"steps_completed": state.get("steps_completed", []) + ["log_approval"]}

def route_after_response(state: ApprovalState) -> str:
    ans = state.get("approval_status")
    if ans == "approved":
        return "update_tracker"
    elif ans == "revision_requested":
        return "prepare_approval_request"
    elif ans == "escalated":
        return "escalate"
    else:
        # pending (timeout scenario)
        if state.get("follow_up_count", 0) < 2:
            return "send_follow_up"
        else:
            return "escalate"

def build_ps03_graph() -> StateGraph:
    graph = StateGraph(ApprovalState)
    
    graph.add_node("prepare_approval_request", prepare_approval_request)
    graph.add_node("send_approval_request", send_approval_request)
    graph.add_node("process_response", process_response)
    graph.add_node("send_follow_up", send_follow_up)
    graph.add_node("escalate", escalate)
    graph.add_node("update_tracker", update_tracker)
    graph.add_node("log_approval", log_approval)
    
    graph.set_entry_point("prepare_approval_request")
    
    graph.add_edge("prepare_approval_request", "send_approval_request")
    # Instead of wait_for_response, we transition right to process_response
    # But during run_agent we will use interrupt_before=["process_response"]
    graph.add_edge("send_approval_request", "process_response")
    
    graph.add_conditional_edges("process_response", route_after_response, {
        "update_tracker": "update_tracker",
        "prepare_approval_request": "prepare_approval_request",
        "send_follow_up": "send_follow_up",
        "escalate": "escalate"
    })
    
    graph.add_edge("send_follow_up", "process_response")
    
    graph.add_edge("escalate", "update_tracker")
    graph.add_edge("update_tracker", "log_approval")
    graph.add_edge("log_approval", END)
    
    return graph
