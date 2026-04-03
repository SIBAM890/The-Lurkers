from datetime import datetime
import uuid

def create_drive_folder(brand_name: str, start_date: str) -> dict:
    folder_id = str(uuid.uuid4())[:8]
    print(f"[MOCK DRIVE] Creating folder: {brand_name}_{start_date}")
    print(f"[MOCK DRIVE] Subfolders: /Briefs /Scripts /Approved /Footage /Reports")
    return {
        "folder_id": folder_id,
        "url": f"https://drive.google.com/mock/{folder_id}",
        "status": "created"
    }

def set_drive_permissions(folder_id: str, client_email: str, manager_email: str) -> dict:
    print(f"[MOCK DRIVE] Setting permissions on {folder_id}")
    print(f"[MOCK DRIVE] {client_email} → comment only")
    print(f"[MOCK DRIVE] {manager_email} → edit")
    return {"status": "permissions_set"}

def create_notion_page(template: str, data: dict) -> dict:
    page_id = str(uuid.uuid4())[:8]
    print(f"[MOCK NOTION] Creating page from template: {template}")
    print(f"[MOCK NOTION] Populating fields: {list(data.keys())}")
    return {
        "page_id": page_id,
        "url": f"https://notion.so/mock/{page_id}",
        "status": "created"
    }

def create_airtable_record(table: str, fields: dict) -> dict:
    record_id = f"rec{str(uuid.uuid4())[:6]}"
    print(f"[MOCK AIRTABLE] Creating record in {table}")
    print(f"[MOCK AIRTABLE] Fields: {fields}")
    return {
        "record_id": record_id,
        "url": f"https://airtable.com/mock/{record_id}",
        "status": "created"
    }

def send_email(to: str, subject: str, body: str) -> dict:
    print(f"[MOCK EMAIL] To: {to}")
    print(f"[MOCK EMAIL] Subject: {subject}")
    print(f"[MOCK EMAIL] Body preview: {body[:100]}...")
    return {"status": "sent", "message_id": str(uuid.uuid4())[:8]}

def send_slack_message(channel: str, message: str) -> dict:
    print(f"[MOCK SLACK] Channel: {channel}")
    print(f"[MOCK SLACK] Message: {message[:100]}...")
    return {"status": "sent"}

def check_airtable_duplicate(table: str, field: str, value: str) -> dict:
    print(f"[MOCK AIRTABLE] Checking duplicate: {field}={value} in {table}")
    return {"duplicate_found": False, "existing_records": []}

def update_airtable_record(record_id: str, fields: dict) -> dict:
    print(f"[MOCK AIRTABLE] Updating {record_id}: {fields}")
    return {"status": "updated"}

def log_event(ps_id: str, event: str, data: dict) -> None:
    print(f"[LOG] [{datetime.now().isoformat()}] {ps_id} | {event} | {data}")
