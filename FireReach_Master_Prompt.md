# 🔥 FireReach AI – Production-Grade Master Build Prompt (WITH EMAIL DISCOVERY)

## For Agentic Code Generators (Cursor, GPT Engineer, Devin, etc.)

---

## 📋 EXECUTIVE BRIEF

You are an expert full-stack AI systems engineer. Build a **production-grade agentic outreach system** called **FireReach AI**.

**What it does:**
- User inputs: Company name + Ideal Customer Profile (ICP)
- System fetches real signals (news, hiring, tech stack, funding)
- **NEW: Automatically discovers decision-maker contacts (emails)**
- LLM analyzes signals against ICP → identifies pain points
- Generates hyper-personalized emails for EACH contact
- Sends emails automatically to all discovered contacts
- Stores history to avoid duplicate outreach

**This is NOT:** A simple LLM app or manual email tool
**This IS:** A structured agentic system with real data + intelligent reasoning + automated contact discovery

---

## 🧠 CORE SYSTEM REQUIREMENTS

### 1. AGENTIC ARCHITECTURE (MANDATORY)

Use **LangGraph** (not just LLM chains).

Graph structure:

```
START
  ↓
[fetch_signals_node] → Real data from Serper/APIs
  ↓
[clean_signals_node] → Structured, typed data
  ↓
[analyze_signals_node] → LLM interprets against ICP
  ↓
[score_lead_node] → Deterministic scoring (0-1)
  ↓
[conditional_node] → Decision: proceed or stop
  ├─ IF score < 0.5 → STOP (insufficient signals)
  │
  ├─ IF score >= 0.5 → continue
      ↓
  [find_contacts_node] ← NEW: Email discovery
      ↓
  [strategy_node] → Identify outreach angle
      ↓
  [generate_email_node] → Create email for EACH contact
      ↓
  [send_email_node] → Send to all discovered contacts
      ↓
  [memory_node] → Log all contacts + emails
      ↓
  END
```

### 2. STATE MANAGEMENT (CRITICAL)

Define a **typed state** that flows through all nodes:

```python
from typing import Dict, List
from dataclasses import dataclass, field

@dataclass
class Contact:
    """Individual contact at the company"""
    name: str
    title: str
    email: str
    department: str
    seniority: str  # executive, manager, individual_contributor
    confidence: float  # 0-1, email match confidence
    linkedin_url: str = ""

@dataclass
class AgentState:
    # Input
    company: str = ""
    icp: str = ""
    target_titles: List[str] = field(default_factory=lambda: [
        "VP Engineering", "CTO", "Engineering Manager", "Tech Lead"
    ])
    
    # Processing
    signals: Dict[str, any] = None  # Raw signals from Serper
    cleaned_signals: Dict[str, any] = None  # Structured signals
    insights: str = ""  # LLM analysis (2 paragraphs)
    
    # Scoring
    score: float = 0.0  # 0-1
    score_breakdown: Dict[str, float] = None  # Components
    
    # Contact Discovery (NEW)
    contacts: List[Contact] = field(default_factory=list)  # Discovered contacts
    contacts_found: int = 0
    
    # Strategy
    strategy: str = ""  # Outreach angle
    
    # Email
    emails: Dict[str, str] = field(default_factory=dict)  # {email: body}
    email_subject: str = ""
    
    # Execution
    status: str = "pending"  # pending | complete | failed | stopped
    emails_sent: int = 0
    send_results: List[Dict] = field(default_factory=list)  # [{email, status, timestamp}]
    error: str = ""
    
    # Memory
    created_at: str = ""
```

---

## 🌐 SIGNAL INGESTION (REAL DATA ONLY)

### Data Sources

Use **Serper API** as primary source. Implement queries:

```
{company} funding announcement
{company} hiring jobs
{company} expansion news
{company} tech stack tools
{company} leadership changes
{company} product launch
```

Structure extracted signals:

```json
{
  "funding": {
    "status": "raised",
    "amount": "$500M",
    "round": "Series I",
    "date": "2024-01-15",
    "confidence": 0.95
  },
  "hiring": {
    "open_roles": 20,
    "departments": ["Engineering", "Sales"],
    "growth_rate": "high",
    "date": "2024-01-20",
    "confidence": 0.9
  },
  "expansion": {
    "regions": ["APAC", "Europe"],
    "description": "Expanding into new markets",
    "confidence": 0.85
  },
  "tech_stack": {
    "identified": ["Kubernetes", "AWS", "PostgreSQL"],
    "changes": "Migrated to K8s",
    "confidence": 0.8
  },
  "news": {
    "latest": "Acquiring competitor X",
    "date": "2024-01-18",
    "confidence": 0.92
  }
}
```

---

## 🔍 EMAIL DISCOVERY (NEW - CRITICAL NODE)

### Overview

**find_contacts_node** automatically discovers decision-makers at the company.

### Data Sources for Email Discovery

Use ONE primary source (recommend Hunter.io or Apollo.io):

#### Option 1: **Hunter.io API** (Recommended for Startups)
```
Endpoint: GET https://api.hunter.io/v2/domain-search?domain={domain}
Returns: All emails associated with domain
```

#### Option 2: **Apollo.io API** (Recommended for Scale)
```
Endpoint: POST https://api.apollo.io/v1/contacts/search
Payload: {company_domain, job_title, seniority}
Returns: Contact records with emails, LinkedIn URLs, seniority
```

#### Option 3: **Clearbit API** (Company + Leadership Data)
```
Endpoint: GET https://api.clearbit.com/v1/companies/find?domain={domain}
Returns: Company data + leadership team info
Combine with Hunter for emails
```

#### Option 4: **RocketReach API** (B2B Database)
```
Endpoint: POST https://api.rocketreach.com/v2/people/search
Returns: Detailed contact info with confidence scores
```

**Recommendation:** Use Hunter.io + Apollo.io (Apollo for verification, Hunter for discovery)

### Implementation (Contact Discovery Service)

```python
# services/contact_discovery.py

from dataclasses import dataclass
from typing import List
import httpx

@dataclass
class ContactDiscoveryService:
    """Find decision-makers at a company"""
    
    hunter_api_key: str
    apollo_api_key: str
    
    async def find_contacts(
        self,
        company: str,
        domain: str,
        target_titles: List[str] = None,
        limit: int = 5
    ) -> List[Contact]:
        """
        Discover contacts at a company.
        
        Args:
            company: Company name (e.g., "Stripe")
            domain: Company domain (e.g., "stripe.com")
            target_titles: Job titles to target (e.g., ["VP Engineering", "CTO"])
            limit: Max contacts to return
        
        Returns:
            List[Contact] with name, title, email, confidence
        """
        
        if not target_titles:
            target_titles = [
                "VP Engineering",
                "CTO",
                "Engineering Manager",
                "Tech Lead",
                "Head of Engineering"
            ]
        
        # Strategy: Use Hunter for email discovery, Apollo for verification
        
        # Step 1: Get all emails from domain (Hunter)
        all_emails = await self._fetch_from_hunter(domain)
        
        # Step 2: Verify and enrich with Apollo (get titles, seniority)
        contacts = await self._verify_with_apollo(
            domain,
            all_emails,
            target_titles,
            limit
        )
        
        # Step 3: Rank by relevance
        contacts = self._rank_contacts(contacts, target_titles)
        
        return contacts[:limit]
    
    async def _fetch_from_hunter(self, domain: str) -> List[Dict]:
        """Fetch emails from Hunter.io"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={
                    "domain": domain,
                    "limit": 100,
                    "api_key": self.hunter_api_key
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            emails = data.get("data", {}).get("emails", [])
            
            return [
                {
                    "email": e.get("value"),
                    "first_name": e.get("first_name"),
                    "last_name": e.get("last_name"),
                    "position": e.get("position"),
                    "confidence": e.get("confidence")
                }
                for e in emails
            ]
    
    async def _verify_with_apollo(
        self,
        domain: str,
        emails: List[Dict],
        target_titles: List[str],
        limit: int
    ) -> List[Contact]:
        """Verify emails and enrich with Apollo"""
        async with httpx.AsyncClient() as client:
            verified_contacts = []
            
            for email in emails[:20]:  # Limit API calls
                response = await client.post(
                    "https://api.apollo.io/v1/contacts/search",
                    headers={"X-API-Key": self.apollo_api_key},
                    json={
                        "email": email.get("email"),
                        "domain": domain
                    }
                )
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                contact_data = data.get("contact")
                
                if not contact_data:
                    continue
                
                # Check if title matches target
                title = contact_data.get("title", "")
                matches_target = any(
                    target.lower() in title.lower()
                    for target in target_titles
                )
                
                if not matches_target:
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
                
                verified_contacts.append(contact)
            
            return verified_contacts
    
    def _infer_department(self, title: str) -> str:
        """Infer department from title"""
        title_lower = title.lower()
        
        if any(x in title_lower for x in ["engineering", "cto", "vp eng"]):
            return "Engineering"
        elif any(x in title_lower for x in ["product", "pm"]):
            return "Product"
        elif any(x in title_lower for x in ["sales", "revenue"]):
            return "Sales"
        elif any(x in title_lower for x in ["finance", "cfo"]):
            return "Finance"
        else:
            return "Other"
    
    def _infer_seniority(self, title: str) -> str:
        """Infer seniority level from title"""
        title_lower = title.lower()
        
        if any(x in title_lower for x in ["cto", "vp", "chief", "head of"]):
            return "executive"
        elif any(x in title_lower for x in ["manager", "lead", "senior"]):
            return "manager"
        else:
            return "individual_contributor"
    
    def _rank_contacts(self, contacts: List[Contact], target_titles: List[str]) -> List[Contact]:
        """Rank contacts by relevance"""
        def score_contact(contact: Contact) -> float:
            score = contact.confidence
            
            # Boost executives
            if contact.seniority == "executive":
                score *= 1.5
            
            # Boost exact title matches
            for target in target_titles:
                if target.lower() in contact.title.lower():
                    score *= 1.3
                    break
            
            return score
        
        return sorted(contacts, key=score_contact, reverse=True)
```

### find_contacts_node Implementation

```python
# agent/nodes/find_contacts.py

async def find_contacts_node(state: AgentState, contact_discovery_service) -> dict:
    """
    Discover decision-maker contacts at the company.
    
    Input: state.company, state.target_titles
    Output: state.contacts (list of Contact objects)
    """
    
    try:
        # Extract domain from company name
        domain = await _get_company_domain(state.company)
        
        if not domain:
            state.contacts = []
            state.contacts_found = 0
            return state
        
        # Discover contacts
        contacts = await contact_discovery_service.find_contacts(
            company=state.company,
            domain=domain,
            target_titles=state.target_titles,
            limit=5  # Find top 5 contacts
        )
        
        state.contacts = contacts
        state.contacts_found = len(contacts)
        
        # If no contacts found, fail gracefully
        if not contacts:
            state.status = "no_contacts_found"
        
        return state
    
    except Exception as e:
        state.status = "failed"
        state.error = f"Contact discovery failed: {str(e)}"
        return state

async def _get_company_domain(company: str) -> str:
    """
    Get company domain from company name.
    Could use Clearbit or hardcoded mapping.
    """
    # Simple mapping (expand as needed)
    domain_map = {
        "stripe": "stripe.com",
        "notion": "notion.so",
        "figma": "figma.com",
        "vercel": "vercel.com",
        "anthropic": "anthropic.com",
        "openai": "openai.com"
    }
    
    return domain_map.get(company.lower(), f"{company.lower()}.com")
```

---

## 🧠 UPDATED EMAIL GENERATION (PER CONTACT)

### generate_email_node (Updated)

```python
# agent/nodes/generate_email_node.py

async def generate_email_node(state: AgentState, llm_service) -> dict:
    """
    Generate personalized email for EACH discovered contact.
    
    Input: state.contacts, state.signals, state.strategy, state.icp
    Output: state.emails (dict of {email: body}), state.email_subject
    """
    
    if not state.contacts:
        state.emails = {}
        state.email_subject = ""
        state.status = "no_emails_generated"
        return state
    
    emails_generated = {}
    
    for contact in state.contacts:
        # Personalize for this specific contact
        email = await _generate_email_for_contact(
            contact=contact,
            company=state.company,
            signals=state.cleaned_signals,
            strategy=state.strategy,
            icp=state.icp,
            llm_service=llm_service
        )
        
        emails_generated[contact.email] = email
    
    # Generate subject (same for all)
    subject = await _generate_subject(
        company=state.company,
        strategy=state.strategy,
        llm_service=llm_service
    )
    
    state.emails = emails_generated
    state.email_subject = subject
    
    return state

async def _generate_email_for_contact(
    contact: Contact,
    company: str,
    signals: Dict,
    strategy: str,
    icp: str,
    llm_service
) -> str:
    """
    Generate email personalized for a specific contact.
    """
    
    signals_summary = _format_signals_for_email(signals)
    
    prompt = f"""
You are a B2B GTM specialist. Generate a short, personalized outreach email 
for a specific decision-maker.

CONTACT:
Name: {contact.name}
Title: {contact.title}
Department: {contact.department}

COMPANY:
Name: {company}
Signals: {signals_summary}

ICP: {icp}
Strategy: {strategy}

CONSTRAINTS:
- Max 120 words (STRICT)
- NO TEMPLATES
- MUST reference signals explicitly
- Address by first name only (natural, conversational)
- Reference their specific title/role when relevant
- Conversational tone
- Single clear CTA

REQUIRED STRUCTURE:
[Opening] - Reference signal + acknowledge their role
  "Hi {contact.name},
   I noticed {company} is [signal]...
   As a {contact.title}, you're probably dealing with [pain point]..."

[Connection] - Link signal to their pain point
  "This usually means..."

[Value prop] - 1 sentence offer
  "We help [department] teams..."

[CTA] - Ask for 15-min call
  "Would you be open to a quick 15-minute call...?"

NOW GENERATE THE EMAIL (body only, no subject):
"""
    
    email = await llm_service.generate(prompt)
    
    # Validate
    word_count = len(email.split())
    if word_count > 120:
        # Trim if needed
        email = " ".join(email.split()[:120]) + "..."
    
    return email

async def _generate_subject(company: str, strategy: str, llm_service) -> str:
    """Generate email subject"""
    
    prompt = f"""
Generate a short, compelling email subject line (max 50 chars).

Company: {company}
Strategy/Angle: {strategy}

Examples of good subjects:
- "{company}'s backend scaling momentum"
- "Accelerating {company}'s hiring ramp"
- "{company}'s APAC expansion & engineering challenges"

NOW GENERATE (subject only, no explanation):
"""
    
    subject = await llm_service.generate(prompt)
    return subject.strip()
```

---

## 📧 SEND EMAIL TO MULTIPLE CONTACTS

### send_email_node (Updated)

```python
# agent/nodes/send_email_node.py

async def send_email_node(state: AgentState, email_service) -> dict:
    """
    Send personalized emails to all discovered contacts.
    
    Input: state.contacts, state.emails, state.email_subject, state.company
    Output: state.emails_sent, state.send_results
    """
    
    send_results = []
    emails_sent = 0
    
    for contact in state.contacts:
        email_body = state.emails.get(contact.email)
        
        if not email_body:
            continue
        
        try:
            result = await email_service.send_email(
                to_email=contact.email,
                to_name=contact.name,
                subject=state.email_subject,
                body=email_body,
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
                "timestamp": result.get("timestamp"),
                "error": result.get("error")
            })
        
        except Exception as e:
            send_results.append({
                "contact_email": contact.email,
                "contact_name": contact.name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    state.emails_sent = emails_sent
    state.send_results = send_results
    state.status = "complete"
    
    return state
```

---

## 📊 SCORING ENGINE (DETERMINISTIC)

### Scoring Logic (Same as Before)

```python
def score_lead(signals: Dict[str, Dict]) -> float:
    """
    Score opportunity from 0-1.
    
    Weights:
    - Hiring signal: 0.4 (strongest indicator of growth)
    - Funding signal: 0.3 (indicates resources)
    - Expansion signal: 0.2 (new market = new needs)
    - Tech change: 0.1 (modernization efforts)
    """
    
    hiring_score = _score_signal(signals.get("hiring"), threshold=10)
    funding_score = _score_signal(signals.get("funding"), threshold=50)
    expansion_score = _score_signal(signals.get("expansion"))
    tech_score = _score_signal(signals.get("tech_stack"))
    
    composite_score = (
        hiring_score * 0.4 +
        funding_score * 0.3 +
        expansion_score * 0.2 +
        tech_score * 0.1
    )
    
    return min(1.0, composite_score)
```

---

## 🏗️ BACKEND STRUCTURE (FastAPI - UPDATED)

### Main Application

```python
# main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI(title="FireReach AI")

# Initialize services
serper_service = SerperService(api_key=os.getenv("SERPER_API_KEY"))
contact_discovery = ContactDiscoveryService(
    hunter_api_key=os.getenv("HUNTER_API_KEY"),
    apollo_api_key=os.getenv("APOLLO_API_KEY")
)
email_service = EmailService(method="smtp")
memory_service = MemoryService(db=database)
llm_service = LLMService(provider="groq", api_key=os.getenv("GROQ_API_KEY"))

# Initialize LangGraph agent
from agent.graph import build_agent_graph
agent = build_agent_graph(
    serper_service=serper_service,
    contact_discovery=contact_discovery,
    llm_service=llm_service,
    email_service=email_service,
    memory_service=memory_service
)

@app.post("/run-agent")
async def run_agent(payload: dict):
    """
    POST /run-agent
    
    Request:
    {
        "company": "Stripe",
        "icp": "B2B SaaS companies scaling engineering teams",
        "target_titles": ["VP Engineering", "CTO", "Engineering Manager"],
        "send_emails": true
    }
    
    Response:
    {
        "status": "success",
        "company": "Stripe",
        "score": 0.87,
        "signals": {...},
        "insights": "...",
        "strategy": "...",
        "contacts_found": 5,
        "contacts": [
            {
                "name": "John Doe",
                "title": "VP Engineering",
                "email": "john@stripe.com",
                "seniority": "executive",
                "confidence": 0.95
            }
        ],
        "emails": {
            "john@stripe.com": "Hi John...",
            "jane@stripe.com": "Hi Jane..."
        },
        "email_subject": "Stripe's backend scaling momentum",
        "emails_sent": 5,
        "send_results": [
            {
                "contact_email": "john@stripe.com",
                "contact_name": "John Doe",
                "status": "sent",
                "message_id": "...",
                "timestamp": "2024-01-20T10:30:00Z"
            }
        ],
        "timestamp": "2024-01-20T10:30:00Z"
    }
    """
    
    try:
        company = payload.get("company")
        icp = payload.get("icp")
        target_titles = payload.get("target_titles")
        send_emails = payload.get("send_emails", True)
        
        # Run agent
        initial_state = {
            "company": company,
            "icp": icp,
            "target_titles": target_titles or [
                "VP Engineering", "CTO", "Engineering Manager"
            ]
        }
        
        final_state = await agent.ainvoke(initial_state)
        
        # Prepare response
        response = {
            "status": "success",
            "company": final_state["company"],
            "score": final_state["score"],
            "signals": final_state["cleaned_signals"],
            "insights": final_state["insights"],
            "strategy": final_state["strategy"],
            "contacts_found": final_state["contacts_found"],
            "contacts": [
                {
                    "name": c.name,
                    "title": c.title,
                    "email": c.email,
                    "department": c.department,
                    "seniority": c.seniority,
                    "confidence": c.confidence
                }
                for c in final_state["contacts"]
            ],
            "emails": final_state["emails"],
            "email_subject": final_state["email_subject"],
            "emails_sent": final_state["emails_sent"],
            "send_results": final_state["send_results"],
            "created_at": datetime.now().isoformat()
        }
        
        # Store in memory
        await memory_service.save_outreach(final_state)
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history(company: str = None, limit: int = 10):
    """Get outreach history"""
    records = await memory_service.get_history(company=company, limit=limit)
    return {"records": records}

@app.get("/status/{company}")
async def get_status(company: str):
    """Check if company was recently contacted"""
    has_recent = await memory_service.has_recent_outreach(company)
    return {"company": company, "contacted_recently": has_recent}
```

---

## 🗄️ UPDATED DATABASE MODEL

```python
# db/models.py

from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Integer
from datetime import datetime

class OutreachRecord:
    __tablename__ = "outreach_history"
    
    id = Column(Integer, primary_key=True)
    company = Column(String, nullable=False)
    icp = Column(String)
    signals = Column(JSON)
    insights = Column(Text)
    score = Column(Float)
    
    # NEW: Contact information
    contacts_found = Column(Integer, default=0)
    contacts = Column(JSON)  # [{name, title, email, confidence}, ...]
    
    email_subject = Column(String)
    
    # NEW: Multiple emails per company
    emails = Column(JSON)  # {email: body, ...}
    emails_sent = Column(Integer, default=0)
    send_results = Column(JSON)  # [{contact_email, status, timestamp}, ...]
    
    status = Column(String)  # sent | failed | stopped | no_contacts_found
    created_at = Column(DateTime, default=datetime.now)
    error_msg = Column(String, nullable=True)
```

---

## 📡 UPDATED API ENDPOINTS

### Response Example

```json
{
  "status": "success",
  "company": "Stripe",
  "score": 0.87,
  "signals": {
    "funding": {"amount": "$500M", "confidence": 0.95},
    "hiring": {"open_roles": 20, "confidence": 0.9}
  },
  "insights": "Stripe is aggressively scaling infrastructure...",
  "strategy": "Scaling backend infrastructure",
  "contacts_found": 5,
  "contacts": [
    {
      "name": "John Doe",
      "title": "VP Engineering",
      "email": "john@stripe.com",
      "department": "Engineering",
      "seniority": "executive",
      "confidence": 0.95,
      "linkedin_url": "https://linkedin.com/in/johndoe"
    },
    {
      "name": "Jane Smith",
      "title": "Engineering Manager",
      "email": "jane@stripe.com",
      "department": "Engineering",
      "seniority": "manager",
      "confidence": 0.88
    }
  ],
  "emails": {
    "john@stripe.com": "Hi John, I noticed Stripe raised $500M...",
    "jane@stripe.com": "Hi Jane, I noticed Stripe is hiring 20+ engineers..."
  },
  "email_subject": "Scaling Stripe's backend hiring momentum",
  "emails_sent": 5,
  "send_results": [
    {
      "contact_email": "john@stripe.com",
      "contact_name": "John Doe",
      "status": "sent",
      "message_id": "msg_1234567890",
      "timestamp": "2024-01-20T10:30:00Z"
    },
    {
      "contact_email": "jane@stripe.com",
      "contact_name": "Jane Smith",
      "status": "sent",
      "message_id": "msg_0987654321",
      "timestamp": "2024-01-20T10:30:05Z"
    }
  ],
  "created_at": "2024-01-20T10:30:00Z"
}
```

---

## ⚙️ ENVIRONMENT VARIABLES (UPDATED)

```
# Serper
SERPER_API_KEY=your_serper_key

# Contact Discovery
HUNTER_API_KEY=your_hunter_key          # For email discovery
APOLLO_API_KEY=your_apollo_key          # For verification + enrichment
# OR use just one:
# CLEARBIT_API_KEY=your_clearbit_key     # Alternative

# LLM
LLM_PROVIDER=groq
LLM_API_KEY=your_llm_key

# Email
EMAIL_METHOD=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Database
DATABASE_URL=sqlite:///./firereach.db

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

---

## 🧪 UPDATED TEST EXAMPLE

```python
@pytest.mark.asyncio
async def test_full_pipeline_with_email_discovery():
    """Test complete pipeline including contact discovery"""
    
    # Initialize services
    serper = SerperService(api_key="test_key")
    contact_discovery = ContactDiscoveryService(
        hunter_api_key="test_hunter",
        apollo_api_key="test_apollo"
    )
    
    # Run agent
    state = {
        "company": "Stripe",
        "icp": "B2B payment processors"
    }
    
    result = await agent.ainvoke(state)
    
    # Validate results
    assert result["score"] > 0.5
    assert result["contacts_found"] > 0
    assert len(result["contacts"]) > 0
    assert len(result["emails"]) == result["contacts_found"]
    assert result["emails_sent"] >= 0
    
    # Check contact structure
    for contact in result["contacts"]:
        assert "name" in contact
        assert "email" in contact
        assert "title" in contact
        assert 0 <= contact["confidence"] <= 1
    
    # Check send results
    for send_result in result["send_results"]:
        assert "contact_email" in send_result
        assert "status" in send_result
        assert send_result["status"] in ["sent", "failed"]
```

---

## 📝 SAMPLE EXECUTION

### Input
```json
{
  "company": "Stripe",
  "icp": "B2B payment processors scaling engineering teams",
  "target_titles": ["VP Engineering", "CTO", "Engineering Manager"],
  "send_emails": true
}
```

### Agent Flow
```
1. fetch_signals_node
   → Serper queries find: $500M funding, 20+ engineers hiring
   
2. clean_signals_node
   → Structure: {funding: 0.95, hiring: 0.9}
   
3. analyze_signals_node
   → LLM: "Stripe scaling infrastructure to handle growth"
   
4. score_lead_node
   → Score: 0.87 (excellent opportunity)
   
5. Conditional: score >= 0.5? YES → continue
   
6. find_contacts_node ← NEW
   → Hunter.io finds: john@stripe.com (VP Eng), jane@stripe.com (Eng Manager)
   → Apollo.io verifies: Both are real, high confidence
   → Result: 2 contacts discovered
   
7. strategy_node
   → Angle: "Scaling backend infrastructure"
   
8. generate_email_node ← UPDATED
   → Email 1 (for John): "Hi John, I noticed Stripe raised $500M..."
   → Email 2 (for Jane): "Hi Jane, As an Engineering Manager, you're probably..."
   → Subject: "Scaling Stripe's backend hiring momentum"
   
9. send_email_node ← UPDATED
   → Send email 1 to john@stripe.com → SUCCESS
   → Send email 2 to jane@stripe.com → SUCCESS
   
10. memory_node
    → Store: company, score, 2 contacts, 2 emails, send status
```

### Output
```json
{
  "status": "success",
  "company": "Stripe",
  "score": 0.87,
  "contacts_found": 2,
  "contacts": [
    {
      "name": "John Doe",
      "title": "VP Engineering",
      "email": "john@stripe.com",
      "seniority": "executive",
      "confidence": 0.95
    },
    {
      "name": "Jane Smith",
      "title": "Engineering Manager",
      "email": "jane@stripe.com",
      "seniority": "manager",
      "confidence": 0.88
    }
  ],
  "emails_sent": 2,
  "email_subject": "Scaling Stripe's backend hiring momentum",
  "send_results": [
    {"contact_email": "john@stripe.com", "status": "sent"},
    {"contact_email": "jane@stripe.com", "status": "sent"}
  ]
}
```

---

## 📁 UPDATED PROJECT STRUCTURE

```
/backend
  /main.py
  /agent
    /graph.py
    /state.py
    /nodes
      /fetch_signals.py
      /clean_signals.py
      /analyze_signals.py
      /score_lead.py
      /find_contacts.py          ← NEW
      /strategy.py
      /generate_email.py
      /send_email.py
      /memory.py
  /services
    /serper.py
    /contact_discovery.py        ← NEW
    /llm.py
    /email.py
    /scoring.py
    /memory.py
  /db
    /models.py
    /database.py
```

---

## ⚠️ CRITICAL REQUIREMENTS (Updated)

1. **NO hallucinated data** – Only reference signals + discovered contacts
2. **Real email discovery** – Use Hunter.io or Apollo.io
3. **Personalized emails** – Each contact gets unique email
4. **Deterministic scoring** – No LLM for scoring
5. **Clean separation** – Each service is modular
6. **Async throughout** – All I/O operations async
7. **Error handling** – Graceful failures
8. **Contact confidence** – Only send to high-confidence emails (>0.7)

---

## 🎯 SUCCESS CRITERIA

✅ Accept company + ICP input
✅ Fetch real signals from Serper
✅ Score opportunities deterministically
✅ **Discover real contacts (with emails)** ← NEW
✅ Generate unique emails per contact
✅ Send emails to all discovered contacts
✅ Store history with contact information
✅ Handle errors gracefully

---

## 🚀 THIS IS NOW A REAL GTM TOOL

With email discovery, you've gone from "interesting demo" to **"actually useful product"**.

Instead of users providing emails manually, the system:
1. Finds decision-makers automatically
2. Personalizes for each one
3. Sends campaigns

This is what Apollo.io and Clearbit do. You're building that.

Good luck! 🔥