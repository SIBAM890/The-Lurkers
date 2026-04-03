from langgraph.graph import StateGraph, END
from core.state import OnboardingState
from core.tools import (
    check_airtable_duplicate, send_email, create_drive_folder, 
    set_drive_permissions, create_notion_page, create_airtable_record, log_event
)
from core.llm import get_llm
from core.prompts import ONBOARDING_EMAIL_PROMPT
from datetime import datetime

KNOWN_STAFF = ["Priya Sharma", "John Doe", "Jane Smith"]

def validate_input(state: OnboardingState) -> dict:
    flags = list(state.get("flags", []))
    status = state.get("status", "running")
    
    # Check required fields
    required = ["brand_name", "account_manager", "contract_start_date"]
    for req in required:
        if not state.get(req):
            flags.append(f"Missing required field: {req}")
    
    if state.get("account_manager") not in KNOWN_STAFF:
        flags.append(f"Unknown account manager: {state.get('account_manager')}")
        
    start_date = state.get("contract_start_date")
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            if start_date_obj < datetime.now():
                flags.append(f"Contract start date {start_date} is in the past")
        except ValueError:
            flags.append(f"Invalid date format: {start_date}")

    if flags:
        status = "flagged"
        
    return {"flags": flags, "status": status, "steps_completed": state.get("steps_completed", []) + ["validate_input"]}

def check_duplicate(state: OnboardingState) -> dict:
    flags = list(state.get("flags", []))
    status = state.get("status", "running")
    
    result = check_airtable_duplicate("Clients", "brand_name", state.get("brand_name", ""))
    if result.get("duplicate_found"):
        flags.append(f"Duplicate brand found: {state.get('brand_name')}")
        status = "flagged"
        
    return {"flags": flags, "status": status, "steps_completed": state.get("steps_completed", []) + ["check_duplicate"]}

def send_welcome_email(state: OnboardingState) -> dict:
    errors = list(state.get("errors", []))
    welcome_email_sent = state.get("welcome_email_sent", False)
    
    try:
        llm = get_llm()
        prompt = ONBOARDING_EMAIL_PROMPT.format(
            brand_name=state.get("brand_name", ""),
            account_manager=state.get("account_manager", ""),
            contract_start_date=state.get("contract_start_date", ""),
            monthly_deliverable_count=state.get("monthly_deliverable_count", 0)
        )
        response = llm.invoke(prompt)
        email_body = response.content
        
        send_email(
            to=state.get("billing_contact_email", "billing@example.com"),
            subject=f"Welcome to Scrollhouse, {state.get('brand_name')}!",
            body=email_body
        )
        welcome_email_sent = True
    except Exception as e:
        errors.append(f"Failed to send welcome email: {str(e)}")
        
    return {"errors": errors, "welcome_email_sent": welcome_email_sent, "steps_completed": state.get("steps_completed", []) + ["send_welcome_email"]}

def create_drive_folder_node(state: OnboardingState) -> dict:
    result = create_drive_folder(state.get("brand_name", ""), state.get("contract_start_date", ""))
    folder_id = result.get("folder_id")
    folder_url = result.get("url")
    
    set_drive_permissions(
        folder_id=folder_id,
        client_email=state.get("billing_contact_email", ""),
        manager_email=f"{state.get('account_manager', '').replace(' ', '.').lower()}@scrollhouse.com"
    )
    
    return {"drive_folder_url": folder_url, "steps_completed": state.get("steps_completed", []) + ["create_drive_folder_node"]}

def create_notion_page_node(state: OnboardingState) -> dict:
    data = {
        "brand_name": state.get("brand_name"),
        "account_manager": state.get("account_manager"),
        "contract_start_date": state.get("contract_start_date"),
        "drive_folder_url": state.get("drive_folder_url")
    }
    result = create_notion_page("client_hub_template", data)
    return {"notion_page_url": result.get("url"), "steps_completed": state.get("steps_completed", []) + ["create_notion_page_node"]}

def create_airtable_record_node(state: OnboardingState) -> dict:
    fields = {
        "brand_name": state.get("brand_name"),
        "account_manager": state.get("account_manager"),
        "brand_category": state.get("brand_category"),
        "contract_start_date": state.get("contract_start_date"),
        "monthly_deliverable_count": state.get("monthly_deliverable_count"),
        "billing_contact_email": state.get("billing_contact_email"),
        "invoice_cycle": state.get("invoice_cycle"),
        "drive_folder_url": state.get("drive_folder_url"),
        "notion_page_url": state.get("notion_page_url")
    }
    result = create_airtable_record("Clients", fields)
    return {"airtable_record_id": result.get("record_id"), "steps_completed": state.get("steps_completed", []) + ["create_airtable_record_node"]}

def send_completion_summary(state: OnboardingState) -> dict:
    body = f"Onboarding completed for {state.get('brand_name')}.\n"
    body += f"Drive: {state.get('drive_folder_url')}\n"
    body += f"Notion: {state.get('notion_page_url')}\n"
    body += f"Airtable: {state.get('airtable_record_id')}\n"
    
    manager_email = f"{state.get('account_manager', '').replace(' ', '.').lower()}@scrollhouse.com"
    send_email(to=manager_email, subject=f"Onboarding Complete: {state.get('brand_name')}", body=body)
    
    status = "completed" if state.get("status") != "flagged" else "flagged"
    return {"status": status, "steps_completed": state.get("steps_completed", []) + ["send_completion_summary"]}

def log_onboarding(state: OnboardingState) -> dict:
    log_event(
        state.get("ps_id", "PS-01"),
        "onboarding_finished",
        {
            "brand": state.get("brand_name"),
            "status": state.get("status"),
            "flags": state.get("flags"),
            "errors": state.get("errors")
        }
    )
    return {"steps_completed": state.get("steps_completed", []) + ["log_onboarding"]}

def check_status_validate(state: OnboardingState) -> str:
    if state.get("status") == "flagged":
        return "log_onboarding"
    return "check_duplicate"

def check_status_duplicate(state: OnboardingState) -> str:
    if state.get("status") == "flagged":
        return "log_onboarding"
    return "send_welcome_email"

def build_ps01_graph() -> StateGraph:
    graph = StateGraph(OnboardingState)
    
    graph.add_node("validate_input", validate_input)
    graph.add_node("check_duplicate", check_duplicate)
    graph.add_node("send_welcome_email", send_welcome_email)
    graph.add_node("create_drive_folder_node", create_drive_folder_node)
    graph.add_node("create_notion_page_node", create_notion_page_node)
    graph.add_node("create_airtable_record_node", create_airtable_record_node)
    graph.add_node("send_completion_summary", send_completion_summary)
    graph.add_node("log_onboarding", log_onboarding)
    
    graph.set_entry_point("validate_input")
    
    graph.add_conditional_edges("validate_input", check_status_validate, {
        "log_onboarding": "log_onboarding",
        "check_duplicate": "check_duplicate"
    })
    
    graph.add_conditional_edges("check_duplicate", check_status_duplicate, {
        "log_onboarding": "log_onboarding",
        "send_welcome_email": "send_welcome_email"
    })
    
    graph.add_edge("send_welcome_email", "create_drive_folder_node")
    graph.add_edge("create_drive_folder_node", "create_notion_page_node")
    graph.add_edge("create_notion_page_node", "create_airtable_record_node")
    graph.add_edge("create_airtable_record_node", "send_completion_summary")
    graph.add_edge("send_completion_summary", "log_onboarding")
    graph.add_edge("log_onboarding", END)
    
    return graph
