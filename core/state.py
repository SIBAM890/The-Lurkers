from typing import TypedDict, Optional, List, Any
from datetime import datetime

class BaseState(TypedDict):
    ps_id: str                     # "PS-01", "PS-02" etc
    status: str                    # "running", "completed", "error", "flagged"
    input_data: dict               # raw input payload from n8n
    steps_completed: List[str]     # list of completed step names
    errors: List[str]              # any errors encountered
    flags: List[str]               # human review flags
    output: dict                   # final output sent back to n8n
    timestamp: str                 # ISO timestamp

class OnboardingState(BaseState):
    brand_name: str
    account_manager: str
    brand_category: str
    contract_start_date: str
    monthly_deliverable_count: int
    billing_contact_email: str
    invoice_cycle: str
    drive_folder_url: Optional[str]
    notion_page_url: Optional[str]
    airtable_record_id: Optional[str]
    welcome_email_sent: bool

class BriefState(BaseState):
    brand_name: str
    content_type: str
    topic: str
    key_message: str
    target_audience: str
    mandatory_inclusions: str
    reference_urls: List[str]
    brand_context: Optional[str]
    internal_brief: Optional[dict]
    notion_brief_url: Optional[str]
    scriptwriter_assigned: Optional[str]
    ambiguity_flags: List[str]

class ApprovalState(BaseState):
    script_id: str
    script_text: str
    client_name: str
    client_contact: str
    preferred_channel: str
    response_sla_hours: int
    approval_status: str           # pending, approved, revision_requested, rejected, escalated
    follow_up_count: int
    revision_notes: Optional[str]
    version_number: int
    max_loops: int

class ReportingState(BaseState):
    client_list: List[str]
    reporting_month: str
    reports_generated: List[str]
    reports_failed: List[str]
    anomaly_flags: List[str]
