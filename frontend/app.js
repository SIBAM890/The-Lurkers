const MOCK_DATA = {
    "ps01": {
        endpoint: "/ps01",
        title: "PS-01: Onboarding Agent",
        data: {
            "data": {
                "brand_name": "Lumina Skincare",
                "account_manager": "Sarah Jenkins",
                "brand_category": "Beauty",
                "contract_start_date": "2024-05-01",
                "monthly_deliverable_count": 12,
                "billing_contact_email": "finance@luminaskin.com",
                "invoice_cycle": "monthly"
            }
        }
    },
    "ps02": {
        endpoint: "/ps02",
        title: "PS-02: Brief Pipeline",
        data: {
            "data": {
                "brand_name": "TechFlow",
                "content_type": "TikTok Series",
                "topic": "Productivity Hacks using our App",
                "key_message": "Save 10 hours a week with TechFlow automation.",
                "target_audience": "Freelancers and Agency Owners",
                "mandatory_inclusions": "Show the new dashboard UI",
                "reference_urls": []
            }
        }
    },
    "ps03": {
        endpoint: "/ps03",
        title: "PS-03: Approval Loop (Trigger)",
        data: {
            "data": {
                "client_name": "Acme Corp",
                "client_contact": "john@acmecorp.com",
                "preferred_channel": "email",
                "script_text": "HOOK: Tired of manual approvals?",
                "response_sla_hours": 24,
                "thread_id": "TEST_THREAD_001"
            }
        }
    },
    "ps03-reply": {
        endpoint: "/ps03/reply",
        title: "PS-03: Client Reply Webhook",
        data: {
            "thread_id": "TEST_THREAD_001",
            "message": "Looks great! Approved.",
            "is_timeout": false
        }
    },
    "ps04": {
        endpoint: "/ps04",
        title: "PS-04: Reporting Agent",
        data: {
            "data": {
                "client_list": ["Lumina Skincare", "TechFlow"],
                "reporting_month": "March 2024"
            }
        }
    }
};

const navItems = document.querySelectorAll('.nav-item');
const formTitle = document.getElementById('form-title');
const jsonInput = document.getElementById('json-input');
const jsonOutput = document.getElementById('json-output');
const runBtn = document.getElementById('run-btn');
const toast = document.getElementById('toast');
const langsmithPanel = document.getElementById('langsmith-panel');
const lsTraceLink = document.getElementById('ls-trace-link');
const lsBtnUp = document.getElementById('ls-btn-up');
const lsBtnDown = document.getElementById('ls-btn-down');

let currentActive = 'ps01';
let currentRunId = null;

// Syntax highlighting mapping
function syntaxHighlight(json) {
    if (typeof json != 'string') {
         json = JSON.stringify(json, undefined, 4);
    }
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
            } else {
                cls = 'string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'boolean';
        } else if (/null/.test(match)) {
            cls = 'null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

function typeWriterEffect(text, element, speed = 5) {
    element.innerHTML = '';
    let i = 0;
    
    // We disable syntax highlighting during typing for pure speed effect,
    // then apply it once finished to avoid HTML injection breakages.
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
            // Auto scroll to bottom
            element.parentElement.scrollTop = element.parentElement.scrollHeight;
        } else {
            // Reapply colors once fully typed
            element.innerHTML = syntaxHighlight(text);
        }
    }
    type();
}

function loadConfiguration(target) {
    currentActive = target;
    const config = MOCK_DATA[target];
    
    // Update active nav
    document.querySelector('.nav-item.active').classList.remove('active');
    document.querySelector(`[data-target="${target}"]`).classList.add('active');
    
    formTitle.innerText = config.title;
    jsonInput.value = JSON.stringify(config.data, null, 4);
    
    jsonOutput.innerHTML = `<span style="color:var(--text-muted)">// Ready to execute endpoint: ${config.endpoint}\n// Click 'Execute Agent' to start.</span>`;
}

// Initial Load
loadConfiguration('ps01');

// Tab Switching
navItems.forEach(btn => {
    btn.addEventListener('click', (e) => {
        loadConfiguration(e.target.dataset.target);
    });
});

// Run Request
runBtn.addEventListener('click', async () => {
    const config = MOCK_DATA[currentActive];
    let payload;
    
    try {
        payload = JSON.parse(jsonInput.value);
    } catch(e) {
        jsonOutput.innerHTML = `<span style='color:red'>Invalid JSON format: ${e.message}</span>`;
        return;
    }
    
    jsonOutput.innerHTML = `<span style="color:var(--color-primary)">[Systems Executing] -> POST http://localhost:8000${config.endpoint}...\nWaiting for agent...</span>`;
    
    runBtn.style.opacity = '0.5';
    runBtn.innerText = 'Running...';
    
    try {
        const res = await fetch(`http://localhost:8000${config.endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        
        // Handle LangSmith Run Configuration
        if (data.run_id) {
            currentRunId = data.run_id;
            // Native trace URL using the exact Personal Organization ID from the screenshot 
            const lsUrl = `https://smith.langchain.com/o/93e09d21-e600-4cfe-ab39-b4c2b6cf7b19/projects/p/runs/${currentRunId}?project_name=scrollhouse`;
            lsTraceLink.href = lsUrl;
            langsmithPanel.classList.remove('hidden');
        } else {
            langsmithPanel.classList.add('hidden');
        }
        
        // Typewriter reveal
        typeWriterEffect(JSON.stringify(data.agent_state || data, null, 4), jsonOutput, 2);
        
        // Toast
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
        
    } catch(err) {
        jsonOutput.innerHTML = `<span style='color:red'>Connection Refused: Are you sure FastAPI is running on port 8000?\n\nError: ${err.message}</span>`;
    } finally {
        runBtn.style.opacity = '1';
        runBtn.innerText = 'EXECUTE // AGENT';
    }
});

// Feedback handlers
async function sendFeedback(score) {
    if (!currentRunId) return;
    
    try {
        await fetch(`http://localhost:8000/feedback`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                run_id: currentRunId,
                score: score,
                comment: "Submitted via OpsOS Dashboard"
            })
        });
        toast.innerText = "Feedback Logged to LangSmith!";
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            toast.innerText = "Agent Completed Successfully";
        }, 3000);
    } catch(err) {
        console.error("Failed to send feedback", err);
    }
}

lsBtnUp.addEventListener('click', () => sendFeedback(1));
lsBtnDown.addEventListener('click', () => sendFeedback(0));
