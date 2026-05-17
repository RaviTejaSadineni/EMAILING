EMAIL_CLASSIFICATION_PROMPT = """
You classify legal/business emails.
Return strict JSON: {"items":[{"id":"...","category":"...","email_type":"...","urgency":"...","sentiment":"...","ai_confidence":0.0}]}
Allowed category: Contract, Legal Review, Finance, Procurement, Compliance, HR, Sales, General, Administrative.
Allowed email_type: Request, Response, Approval, Rejection, Escalation, FYI/Information, Negotiation, Sign-off, Follow-up, Reminder.
Allowed urgency: Critical, High, Medium, Low.
Allowed sentiment: Positive, Neutral, Negative, Escalated.
"""

THREAD_MERGE_PROMPT = """
Decide if candidate email groups represent same conversation.
Return strict JSON: {"items":[{"group_a":"...","group_b":"...","should_merge":true,"confidence":0.0,"reason":"..."}]}
"""

CONTRACT_EXTRACTION_PROMPT = """
Extract contract metadata from thread context.
Return strict JSON with keys: agreement_name, agreement_type, counterparty_name, counterparty_email,
key_clauses (array), contract_value, effective_date, expiry_date, risk_score, complexity_score, ai_summary, delay_reasons (array).
"""

STAKEHOLDER_EXTRACTION_PROMPT = """
Extract stakeholder profile for each person.
Return strict JSON: {"items":[{"email_address":"...","name":"...","department":"...","role":"...","is_internal":true,"influence_score":0.0,"department_mentions":[]}]}.
"""

LIFECYCLE_STAGE_PROMPT = """
Classify contract thread emails into lifecycle stages.
Stages: 1 Request, 2 Legal Review, 3 Finance Review, 4 Procurement/Compliance, 5 Redline Negotiation, 6 Leadership Sign-off, 7 Repository & Obligation Tracking.
Return strict JSON: {"current_stage":"...","stage_history":[{"stage":1,"email_id":"...","date":"...","actor":"...","notes":"..."}],"predicted_completion":"..."}
"""

EMAIL_SUMMARY_PROMPT = """
Summarize email text in one concise paragraph.
Return strict JSON: {"summary":"..."}
"""

THREAD_SUMMARY_PROMPT = """
Create a concise lifecycle story for the thread.
Return strict JSON: {"summary":"..."}
"""

CLAUSE_DETECTION_PROMPT = """
Detect contract clause mentions and extract clause type and evidence.
Return strict JSON: {"clauses":[{"type":"Liability","evidence":"..."}]}
"""

DELAY_ANALYSIS_PROMPT = """
Analyze delays between lifecycle stages.
Return strict JSON: {"delay_reasons":[{"stage":"...","reason":"...","owner":"...","internal":true}]}
"""
