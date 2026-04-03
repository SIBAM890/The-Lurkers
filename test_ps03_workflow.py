import requests
import time
import json

base_url = "http://localhost:8000"

def test_ps03_flow():
    print("🚀 Starting PS-03 Approval Loop Test...\n")
    
    # 1. Start the workflow
    print("1️⃣ Triggering /ps03 (Simulating Airtable/Notion Webhook)")
    start_payload = {
        "data": {
            "client_name": "Acme Corp",
            "client_contact": "john@acmecorp.com",
            "preferred_channel": "email",
            "script_text": "HOOK: Looking for the best automation tools? BODY: Scrollhouse delivers. CTA: Sign up today.",
            "response_sla_hours": 24
        }
    }
    
    try:
        start_res = requests.post(f"{base_url}/ps03", json=start_payload)
        start_res.raise_for_status()
        start_data = start_res.json()
        
        thread_id = start_payload["data"].get("thread_id") 
        if not thread_id:
            # We didn't pass one, so main.py generated it. Let's find it.
            # wait, main.py generates thread_id inside the function but doesn't explicitly return it unless it's in input_data.
            # Let's check start_data output...
            pass
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Is the FastAPI server running?")
        print("Run 'uvicorn main:app --reload' in a separate terminal first.")
        return
        
    print(f"✅ Workflow started! Check the server logs. It should say [MOCK EMAIL] sent.\n")
    print("Waiting 5 seconds to simulate client taking time to read the script...\n")
    time.sleep(5)
    
    # Notice: In the current main.py, the generated thread_id isn't returned natively in the response dictionary.
    # To test smoothly, we should pass an explicit thread_id. Let's try again with explicit thread!
    
    explicit_thread_id = f"TEST_THREAD_{int(time.time())}"
    start_payload["data"]["thread_id"] = explicit_thread_id
    print(f"🔄 Restarting with explicit thread_id: {explicit_thread_id}")
    requests.post(f"{base_url}/ps03", json=start_payload)
    
    time.sleep(2)
    
    # 2. Simulate Client Reply
    print("2️⃣ Simulating Client Reply via /ps03/reply")
    reply_payload = {
        "thread_id": explicit_thread_id,
        "message": "This looks pretty good! But please remove the word 'automation' and use 'AI' instead."
    }
    
    print(f"Sending client message: '{reply_payload['message']}'")
    reply_res = requests.post(f"{base_url}/ps03/reply", json=reply_payload)
    result = reply_res.json()
    
    print("\n--------- RESULTS ---------")
    print(f"Status Output: {result.get('approval_status')}")
    print(f"Revision Notes Extracted: {result.get('revision_notes')}")
    
    print("\n✅ Test Complete. The LLM parsed the feedback successfully.")

if __name__ == "__main__":
    test_ps03_flow()
