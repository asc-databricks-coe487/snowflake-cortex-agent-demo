from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests, os, re, base64

app = FastAPI(title="Jira MCP Gateway — CORTEX Project")

JIRA_BASE  = os.environ.get("JIRA_BASE_URL",  "https://ascendion-databricks-coe.atlassian.net")
JIRA_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL",     "")

def _headers():
    creds = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {creds}",
        "Accept":        "application/json",
        "Content-Type":  "application/json"
    }

def _adf_to_text(node, out=None):
    """Flatten Atlassian Document Format → plain text."""
    if out is None:
        out = []
    if not node:
        return ""
    if isinstance(node, dict):
        if node.get("type") == "text":
            out.append(node.get("text", ""))
        for child in node.get("content", []):
            _adf_to_text(child, out)
    return "\n".join(out).strip()

def _parse_epic_description(text: str) -> dict:
    """
    Extract structured fields from the epic description.
    Looks for:
      FTL input table: <fully_qualified_name>
      PI gold table:   <fully_qualified_name>
      Schema delta missing / new columns
    """
    result = {
        "ftl_source_table": None,
        "pi_gold_table":    None,
        "missing_in_ftl":   [],
        "new_in_ftl":       []
    }
    m = re.search(r"FTL input table\s*[:\-]\s*([A-Z0-9_.]+)", text, re.IGNORECASE)
    if m:
        result["ftl_source_table"] = m.group(1).strip()

    m = re.search(r"PI gold table\s*[:\-]\s*([A-Z0-9_.]+)", text, re.IGNORECASE)
    if m:
        result["pi_gold_table"] = m.group(1).strip()

    missing = re.findall(r"Missing in FTL\s*[:\-]\s*([A-Z0-9_,\s]+)", text, re.IGNORECASE)
    if missing:
        result["missing_in_ftl"] = [c.strip() for c in re.split(r"[,\n]", missing[0]) if c.strip()]

    new_cols = re.findall(r"New in FTL\s*[:\-]\s*([A-Z0-9_,\s]+)", text, re.IGNORECASE)
    if new_cols:
        result["new_in_ftl"] = [c.strip() for c in re.split(r"[,\n]", new_cols[0]) if c.strip()]

    return result


# ── Tool 1: Read any ticket ────────────────────────────────────
class ReadTicketInput(BaseModel):
    ticket_id: str

@app.post("/tools/read_ticket")
def read_ticket(body: ReadTicketInput):
    url = f"{JIRA_BASE}/rest/api/3/issue/{body.ticket_id}"
    r   = requests.get(url, headers=_headers())

    if r.status_code == 401:
        raise HTTPException(401, "Jira auth failed — check JIRA_EMAIL and JIRA_API_TOKEN")
    if r.status_code == 404:
        raise HTTPException(404, f"Ticket {body.ticket_id} not found in project CORTEX")
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text[:300])

    data   = r.json()
    fields = data.get("fields", {})

    # Description — handle ADF or plain string
    desc_raw = fields.get("description", "")
    desc_text = _adf_to_text(desc_raw) if isinstance(desc_raw, dict) else str(desc_raw or "")

    # Parse structured fields (only populated for Epics)
    parsed = _parse_epic_description(desc_text)

    # Epic link on a Story
    epic_key = None
    if fields.get("parent"):
        epic_key = fields["parent"].get("key")

    # Sub-tasks or Story children
    subtasks = [
        {
            "key":     s["key"],
            "summary": s["fields"].get("summary", ""),
            "status":  s["fields"].get("status", {}).get("name", "")
        }
        for s in fields.get("subtasks", [])
    ]

    return {
        "ticket_id":        body.ticket_id,
        "summary":          fields.get("summary", ""),
        "description":      desc_text,
        "status":           fields.get("status", {}).get("name", ""),
        "issue_type":       fields.get("issuetype", {}).get("name", ""),
        "reporter":         (fields.get("reporter") or {}).get("displayName", ""),
        "project":          fields.get("project", {}).get("key", ""),
        "epic_key":         epic_key,
        "subtasks":         subtasks,
        # Parsed table names — ready for pipeline
        "ftl_source_table": parsed["ftl_source_table"],
        "pi_gold_table":    parsed["pi_gold_table"],
        "missing_in_ftl":   parsed["missing_in_ftl"],
        "new_in_ftl":       parsed["new_in_ftl"],
    }


# ── Tool 2: Post a comment ─────────────────────────────────────
class PostCommentInput(BaseModel):
    ticket_id: str
    comment:   str

@app.post("/tools/post_comment")
def post_comment(body: PostCommentInput):
    url = f"{JIRA_BASE}/rest/api/3/issue/{body.ticket_id}/comment"
    payload = {
        "body": {
            "type": "doc", "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": body.comment}]
            }]
        }
    }
    r = requests.post(url, headers=_headers(), json=payload)
    return {
        "status": "ok" if r.status_code == 201 else f"error:{r.status_code}",
        "detail": "" if r.status_code == 201 else r.text[:200]
    }


# ── Tool 3: Transition ticket status ──────────────────────────
class UpdateStatusInput(BaseModel):
    ticket_id:       str
    transition_name: str   # e.g. "In Progress", "Done"

@app.post("/tools/update_status")
def update_status(body: UpdateStatusInput):
    url = f"{JIRA_BASE}/rest/api/3/issue/{body.ticket_id}/transitions"
    transitions = requests.get(url, headers=_headers()).json().get("transitions", [])
    match = next(
        (t for t in transitions if t["name"].lower() == body.transition_name.lower()),
        None
    )
    if not match:
        return {"status": "error",
                "available": [t["name"] for t in transitions]}
    r = requests.post(url, headers=_headers(), json={"transition": {"id": match["id"]}})
    return {"status": "ok" if r.status_code == 204 else f"error:{r.status_code}"}


# ── Health + manifest ─────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "jira": JIRA_BASE, "project": "CORTEX"}

@app.get("/tools")
def list_tools():
    return {"tools": ["read_ticket", "post_comment", "update_status"]}