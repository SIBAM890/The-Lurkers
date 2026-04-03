ONBOARDING_EMAIL_PROMPT = """
You are writing a professional welcome email for Scrollhouse, a content agency.

Client details:
- Brand: {brand_name}
- Account Manager: {account_manager}
- Contract Start: {contract_start_date}
- Monthly Deliverables: {monthly_deliverable_count} pieces

Write a warm, professional welcome email that:
1. Introduces the Scrollhouse team and process
2. Sets expectations for the first two weeks
3. Mentions a kickoff call
4. Is signed by {account_manager}

Keep it under 200 words. Return only the email body.
"""

BRIEF_INTERPRETATION_PROMPT = """
You are a senior content strategist at Scrollhouse, a short-form video agency.

Raw client brief:
{raw_brief}

Brand context:
{brand_context}

Rewrite this into Scrollhouse's internal brief format. Return a JSON object with these exact keys:
- hook_direction: list of 2-3 hook options ranked by strength
- tone_of_voice: mapped from brand guidelines
- visual_treatment: suggestion for visual approach
- scriptwriter_notes: what to prioritise, avoid, and what client likely wants but didn't say
- brief_summary: one line for Slack notification
- ambiguity_flags: list of any unclear or missing critical information (empty list if none)

Return only valid JSON, no markdown, no explanation.
"""

APPROVAL_MESSAGE_PROMPT = """
You are writing a professional script approval request for Scrollhouse.

Script details:
- Client: {client_name}
- Version: {version_number}
- Deadline for feedback: {deadline}

Script content:
{script_text}

Write a {channel} message that:
1. Presents the script clearly
2. Asks for: Approve / Request Revisions / Reject with reason
3. States the feedback deadline
4. Is friendly but professional

Return only the message text.
"""

FOLLOW_UP_PROMPT = """
Write a follow-up message for a script approval that has not received a response.

Context:
- Client: {client_name}
- Follow-up number: {follow_up_count} (1 = gentle reminder, 2 = urgent)
- Original sent: {original_sent}
- Deadline: {deadline}
- Channel: {channel}

Return only the message text.
"""

PERFORMANCE_NARRATIVE_PROMPT = """
You are a data analyst writing a monthly performance report for a social media content client.

Client: {client_name}
Reporting month: {reporting_month}
Performance data:
{performance_data}

Previous month summary (for comparison):
{previous_summary}

Write a performance narrative with:
1. What happened this month (data summary, 1 paragraph)
2. What worked and why (specific posts/formats, 1 paragraph)
3. What underperformed and hypothesis (1 paragraph)
4. Month-over-month comparison (1 paragraph)
5. 3-5 specific data-backed recommendations for next month

Also output a health label: "Strong Month", "On Track", or "Needs Attention"

Return as JSON with keys: narrative, recommendations (list), health_label
Return only valid JSON, no markdown.
"""
