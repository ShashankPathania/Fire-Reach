# 🔥 FireReach AI – Quick Reference Card (WITH EMAIL DISCOVERY)

## For Agentic Coders: Copy-Paste This

---

## 📋 CRITICAL REQUIREMENTS (Don't Skip)

### 1. **LangGraph is MANDATORY**
- Must use stateful agent (not prompt chaining)
- State object flows through all nodes
- **NEW: find_contacts_node after scoring**
- Conditional branching (score < 0.5 = stop)

### 2. **Serper API is MANDATORY** (Signal Discovery)
- Only real data (no hallucination)
- Queries: "{company} funding news", "{company} hiring jobs"
- Confidence scores 0.0-1.0

### 3. **Email Discovery is MANDATORY** (NEW)
- Use Hunter.io OR Apollo.io OR Clearbit
- Discover real contacts with emails
- Verify emails before sending
- Target: VP Engineering, CTO, Engineering Managers

### 4. **Zero Fake Data**
- Every signal from Serper
- Every contact from Hunter/Apollo
- LLM only for: analysis + email generation
- Scoring is deterministic math

### 5. **Email Constraints**
- Max 120 words per email
- **UNIQUE per contact** (personalized)
- Reference real signals
- No templates
- Conversational

### 6. **Send to Multiple Contacts**
- Generate one email per contact
- Include contact's name + title
- Reference their department when relevant
- Send to all discovered contacts
- Track send status per contact

---

## 🛠️ EXACT TECH STACK

```
Backend: FastAPI (Python 3.10+)
Agent: LangGraph
LLM: Groq (llama-3-70b-versatile)
Search: Serper API
Contact Discovery: Hunter.io OR Apollo.io
Email: SMTP OR SendGrid
DB: SQLite (dev) or PostgreSQL (prod)
Frontend: React 18 + Tailwind
```

---

## 🤖 UPDATED AGENT STATE (Copy This)

```python
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Contact:
    name: str
    title: str
    email: str
    department: str
    seniority: str  # executive, manager, individual_contributor
    confidence: float  # 0-1
    linkedin_url: str = ""

@dataclass
class AgentState:
    # Input
    company: str = ""
    icp: str = ""
    target_titles: List[str] = field(default_factory=lambda: [
        "VP Engineering", "CTO", "Engineering Manager"
    ])
    
    # Signals
    signals: Dict = None
    cleaned_signals: Dict = None
    insights: str = ""
    
    # Scoring
    score: float = 0.0
    score_breakdown: Dict = None
    
    # Contacts (NEW)
    contacts: List[Contact] = field(default_factory=list)
    contacts_found: int = 0
    
    # Strategy
    strategy: str = ""
    
    # Emails (NEW: per contact)
    emails: Dict[str, str] = field(default_factory=dict)  # {email: body}
    email_subject: str = ""
    
    # Execution (NEW: send tracking)
    status: str = "pending"
    emails_sent: int = 0
    send_results: List[Dict] = field(default_factory=list)
    error: str = ""
    
    created_at: str = ""
```

---

## 🕸️ UPDATED LANGGRAPH FLOW (Copy This)

```python
from langgraph.graph import StateGraph, END

def build_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("fetch_signals", fetch_signals_node)
    workflow.add_node("clean_signals", clean_signals_node)
    workflow.add_node("analyze_signals", analyze_signals_node)
    workflow.add_node("score_lead", score_lead_node)
    workflow.add_node("find_contacts", find_contacts_node)  # NEW
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("generate_email", generate_email_node)  # UPDATED
    workflow.add_node("send_email", send_email_node)  # UPDATED
    workflow.add_node("memory", memory_node)
    
    # Add edges
    workflow.add_edge("fetch_signals", "clean_signals")
    workflow.add_edge("clean_signals", "analyze_signals")
    workflow.add_edge("analyze_signals", "score_lead")
    
    # Conditional: score check
    workflow.add_conditional_edges(
        "score_lead",
        lambda state: "continue" if state.score >= 0.5 else "stop",
        {"continue": "find_contacts", "stop": "memory"}  # NEW: find_contacts
    )
    
    workflow.add_edge("find_contacts", "strategy")  # NEW
    workflow.add_edge("strategy", "generate_email")
    workflow.add_edge("generate_email", "send_email")
    workflow.add_edge("send_email", "memory")
    workflow.add_edge("memory", END)
    
    workflow.set_entry_point("fetch_signals")
    
    return workflow.compile()
```

---

## 🔍 FIND CONTACTS NODE (NEW - Copy This)

```python
# agent/nodes/find_contacts.py

async def find_contacts_node(state: AgentState, contact_discovery_service) -> dict:
    """Find decision-makers at the company"""
    
    try:
        domain = _get_company_domain(state.company)
        
        contacts = await contact_discovery_service.find_contacts(
            company=state.company,
            domain=domain,
            target_titles=state.target_titles,
            limit=5
        )
        
        state.contacts = contacts
        state.contacts_found = len(contacts)
        
        return state
    
    except Exception as e:
        state.error = f"Contact discovery failed: {str(e)}"
        state.contacts = []
        return state

def _get_company_domain(company: str) -> str:
    """Map company name to domain"""
    domain_map = {
        "stripe": "stripe.com",
        "notion": "notion.so",
        "figma": "figma.com",
    }
    return domain_map.get(company.lower(), f"{company.lower()}.com")
```

---

## 🔌 CONTACT DISCOVERY SERVICE (Copy This)

```python
# services/contact_discovery.py

from dataclasses import dataclass
from typing import List
import httpx

@dataclass
class Contact:
    name: str
    title: str
    email: str
    department: str
    seniority: str
    confidence: float
    linkedin_url: str = ""

class ContactDiscoveryService:
    def __init__(self, hunter_api_key: str, apollo_api_key: str):
        self.hunter_key = hunter_api_key
        self.apollo_key = apollo_api_key
    
    async def find_contacts(
        self,
        company: str,
        domain: str,
        target_titles: List[str],
        limit: int = 5
    ) -> List[Contact]:
        """Find and verify contacts"""
        
        # Step 1: Get emails from Hunter
        emails = await self._fetch_from_hunter(domain)
        
        # Step 2: Verify with Apollo
        contacts = await self._verify_with_apollo(
            domain, emails, target_titles
        )
        
        # Step 3: Rank by relevance
        contacts = self._rank_contacts(contacts, target_titles)
        
        return contacts[:limit]
    
    async def _fetch_from_hunter(self, domain: str) -> List[Dict]:
        """Fetch from Hunter.io"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={
                    "domain": domain,
                    "limit": 100,
                    "api_key": self.hunter_key
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return data.get("data", {}).get("emails", [])
    
    async def _verify_with_apollo(
        self,
        domain: str,
        emails: List[Dict],
        target_titles: List[str]
    ) -> List[Contact]:
        """Verify and enrich with Apollo"""
        verified = []
        
        async with httpx.AsyncClient() as client:
            for email_data in emails[:20]:
                response = await client.post(
                    "https://api.apollo.io/v1/contacts/search",
                    headers={"X-API-Key": self.apollo_key},
                    json={"email": email_data.get("value")}
                )
                
                if response.status_code != 200:
                    continue
                
                contact_data = response.json().get("contact")
                if not contact_data:
                    continue
                
                title = contact_data.get("title", "")
                
                # Filter by target titles
                if not any(t.lower() in title.lower() for t in target_titles):
                    continue
                
                contact = Contact(
                    name=f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip(),
                    title=title,
                    email=contact_data.get("email"),
                    department=self._infer_department(title),
                    seniority=self._infer_seniority(title),
                    confidence=contact_data.get("confidence", 0.8),
                    linkedin_url=contact_data.get("linkedin_url", "")
                )
                
                verified.append(contact)
        
        return verified
    
    def _infer_department(self, title: str) -> str:
        if any(x in title.lower() for x in ["eng", "cto", "vp"]):
            return "Engineering"
        elif "product" in title.lower():
            return "Product"
        else:
            return "Other"
    
    def _infer_seniority(self, title: str) -> str:
        if any(x in title.lower() for x in ["cto", "vp", "chief", "head"]):
            return "executive"
        elif any(x in title.lower() for x in ["manager", "lead", "senior"]):
            return "manager"
        return "individual_contributor"
    
    def _rank_contacts(self, contacts: List[Contact], target_titles: List[str]) -> List[Contact]:
        def score(c: Contact):
            s = c.confidence
            if c.seniority == "executive":
                s *= 1.5
            for t in target_titles:
                if t.lower() in c.title.lower():
                    s *= 1.3
                    break
            return s
        
        return sorted(contacts, key=score, reverse=True)
```

---

## ✉️ UPDATED EMAIL GENERATION (Per Contact - Copy This)

```python
# agent/nodes/generate_email_node.py

async def generate_email_node(state: AgentState, llm_service) -> dict:
    """Generate personalized email for EACH contact"""
    
    if not state.contacts:
        state.emails = {}
        return state
    
    emails = {}
    
    for contact in state.contacts:
        email = await _generate_for_contact(
            contact=contact,
            company=state.company,
            signals=state.cleaned_signals,
            strategy=state.strategy,
            llm_service=llm_service
        )
        emails[contact.email] = email
    
    # Same subject for all
    subject = await _generate_subject(
        state.company,
        state.strategy,
        llm_service
    )
    
    state.emails = emails
    state.email_subject = subject
    
    return state

async def _generate_for_contact(contact, company, signals, strategy, llm_service):
    """Generate email for specific contact"""
    
    prompt = f"""
Generate a personalized outreach email.

TO: {contact.name} ({contact.title})
COMPANY: {company}
SIGNALS: {_format_signals(signals)}

CONSTRAINTS:
- Max 120 words
- Address by first name
- Reference their role/title
- Reference real signals
- Conversational

STRUCTURE:
"Hi {contact.name},

I noticed {company} is [signal]...
As a {contact.title}, you're probably dealing with [pain]...

We help [department] teams [value]...

Would you be open to a 15-min call?

Best"

NOW GENERATE (body only):
"""
    
    return await llm_service.generate(prompt)

async def _generate_subject(company, strategy, llm_service):
    prompt = f"""
Generate email subject (max 50 chars).
Company: {company}
Angle: {strategy}

SUBJECT ONLY:
"""
    return await llm_service.generate(prompt)
```

---

## 📧 UPDATED SEND EMAIL NODE (Multiple Contacts - Copy This)

```python
# agent/nodes/send_email_node.py

async def send_email_node(state: AgentState, email_service) -> dict:
    """Send personalized emails to all contacts"""
    
    send_results = []
    emails_sent = 0
    
    for contact in state.contacts:
        body = state.emails.get(contact.email)
        
        if not body:
            continue
        
        try:
            result = await email_service.send_email(
                to_email=contact.email,
                to_name=contact.name,
                subject=state.email_subject,
                body=body,
                company=state.company,
                contact_info={
                    "name": contact.name,
                    "title": contact.title,
                    "department": contact.department
                }
            )
            
            if result["status"] == "sent":
                emails_sent += 1
            
            send_results.append({
                "contact_email": contact.email,
                "contact_name": contact.name,
                "status": result["status"],
                "message_id": result.get("message_id"),
                "timestamp": result.get("timestamp")
            })
        
        except Exception as e:
            send_results.append({
                "contact_email": contact.email,
                "contact_name": contact.name,
                "status": "failed",
                "error": str(e)
            })
    
    state.emails_sent = emails_sent
    state.send_results = send_results
    state.status = "complete"
    
    return state
```

---

## 🔌 FASTAPI ENDPOINT (Copy This)

```python
@app.post("/run-agent")
async def run_agent(payload: dict):
    """
    POST /run-agent
    {
        "company": "Stripe",
        "icp": "B2B payment processors",
        "target_titles": ["VP Engineering", "CTO"],
        "send_emails": true
    }
    """
    
    initial_state = {
        "company": payload.get("company"),
        "icp": payload.get("icp"),
        "target_titles": payload.get("target_titles")
    }
    
    final_state = await agent.ainvoke(initial_state)
    
    response = {
        "status": "success",
        "company": final_state["company"],
        "score": final_state["score"],
        "contacts_found": final_state["contacts_found"],
        "contacts": [
            {
                "name": c.name,
                "title": c.title,
                "email": c.email,
                "seniority": c.seniority,
                "confidence": c.confidence
            }
            for c in final_state["contacts"]
        ],
        "emails": final_state["emails"],
        "email_subject": final_state["email_subject"],
        "emails_sent": final_state["emails_sent"],
        "send_results": final_state["send_results"]
    }
    
    await memory_service.save_outreach(final_state)
    
    return JSONResponse(content=response)
```

---

## 🗄️ DATABASE MODEL (Copy This)

```python
class OutreachRecord:
    __tablename__ = "outreach_history"
    
    id = Column(Integer, primary_key=True)
    company = Column(String, nullable=False)
    icp = Column(String)
    
    signals = Column(JSON)
    insights = Column(Text)
    score = Column(Float)
    
    # Contacts (NEW)
    contacts_found = Column(Integer)
    contacts = Column(JSON)
    
    # Emails (NEW)
    email_subject = Column(String)
    emails = Column(JSON)
    emails_sent = Column(Integer)
    send_results = Column(JSON)
    
    status = Column(String)
    created_at = Column(DateTime, default=datetime.now)
```

---

## 🌍 ENVIRONMENT VARIABLES (NEW)

```env
# Search
SERPER_API_KEY=xxx

# Contact Discovery (NEW)
HUNTER_API_KEY=xxx          # Email discovery
APOLLO_API_KEY=xxx          # Verification

# LLM
LLM_PROVIDER=groq
LLM_API_KEY=xxx

# Email
EMAIL_METHOD=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=xxx
SMTP_PASSWORD=xxx

# Database
DATABASE_URL=sqlite:///./firereach.db
```

---

## ✅ FINAL CHECKLIST

- [ ] LangGraph with 9 nodes (including find_contacts)
- [ ] AgentState includes contacts + emails dict
- [ ] Serper integration working
- [ ] Hunter.io OR Apollo.io integration
- [ ] find_contacts_node discovers 3-5 contacts
- [ ] Each contact gets unique email
- [ ] Email generation references contact name + title
- [ ] send_email_node sends to all contacts
- [ ] Send results tracked per contact
- [ ] Database stores contacts + emails + send results
- [ ] Deterministic scoring
- [ ] Tests passing
- [ ] No hardcoded data
- [ ] Async throughout

---

## 🎯 SUCCESS CRITERIA (UPDATED)

✅ Company input → Real signals
✅ Real signals → Opportunity score
✅ **High score → Auto-discover 3-5 contacts** ← NEW
✅ Each contact → Personalized email
✅ Send email to all → Track status
✅ Store: company, signals, contacts, emails, send status
✅ Handle errors gracefully

---

**This is now a real GTM outreach tool.** 🔥

Start with the updated Master Prompt v2.