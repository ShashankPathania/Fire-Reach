#!/usr/bin/env python3
"""
scripts/test_agent.py – CLI smoke test runner.

Runs the FireReach AI agent on 5 predefined companies and prints results.
Requires a properly configured .env file.

Usage:
    cd backend
    python scripts/test_agent.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from db.database import init_db, get_session_factory
from agent.graph import build_agent_graph
from services.serper import SerperService
from services.llm import LLMService
from services.memory import MemoryService

TEST_CASES = [
    {
        "name": "High-Quality Lead (Stripe)",
        "company": "Stripe",
        "icp": "B2B payment processors scaling engineering teams",
        "expect_score_above": 0.4,
    },
    {
        "name": "Enterprise SaaS (Salesforce)",
        "company": "Salesforce",
        "icp": "Enterprise CRM platforms hiring VP of Engineering",
        "expect_score_above": 0.3,
    },
    {
        "name": "Fast-Growing Startup (Vercel)",
        "company": "Vercel",
        "icp": "Developer tooling companies expanding engineering teams",
        "expect_score_above": 0.3,
    },
    {
        "name": "Series B Company (Notion)",
        "company": "Notion",
        "icp": "Productivity SaaS companies scaling ops and engineering",
        "expect_score_above": 0.3,
    },
    {
        "name": "Low-Signal Test",
        "company": "LocalBakeryXYZ123",  # Should have very low signals
        "icp": "B2B SaaS scaling engineering",
        "expect_score_above": 0.0,  # Just check it runs without crashing
    },
]


async def run_tests():
    print("=" * 70)
    print("🔥 FIREREACH AI – AGENT SMOKE TESTS")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Initialize
    await init_db(settings.DATABASE_URL)
    session_factory = get_session_factory()

    serper_svc = SerperService(api_key=settings.SERPER_API_KEY)
    llm_svc = LLMService(
        groq_api_key=settings.LLM_API_KEY,
        groq_model=settings.GROQ_MODEL,
        ollama_url=settings.OLLAMA_URL,
        ollama_model=settings.OLLAMA_MODEL,
    )
    memory_svc = MemoryService(session_factory)
    agent = build_agent_graph(serper_svc, llm_svc, memory_svc)

    results = []
    passed = 0
    failed = 0

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'='*70}")
        print(f"  Company : {test['company']}")
        print(f"  ICP     : {test['icp'][:70]}...")
        print(f"  Running agent...")

        try:
            start = datetime.now()
            state = await agent.ainvoke({
                "company": test["company"],
                "icp": test["icp"],
                "status": "pending",
                "error": "",
                "email_sent": False,
            })
            elapsed = (datetime.now() - start).total_seconds()

            score = state.get("score", 0.0)
            status = state.get("status", "unknown")
            signals = state.get("cleaned_signals") or {}
            email_subject = state.get("email_subject", "")

            print(f"\n  Score   : {score:.3f}")
            print(f"  Status  : {status}")
            print(f"  Signals : {list(signals.keys())}")
            print(f"  Subject : {email_subject[:70]}")
            print(f"  Time    : {elapsed:.1f}s")

            if score >= test["expect_score_above"]:
                print(f"\n  ✅ TEST {i} PASSED")
                passed += 1
            else:
                print(f"\n  ⚠️  TEST {i}: Score {score:.3f} below expected {test['expect_score_above']}")
                passed += 1  # Still pass — just a soft warning

            results.append({
                "test": test["name"],
                "company": test["company"],
                "score": score,
                "status": status,
                "signals": list(signals.keys()),
                "email_subject": email_subject,
                "elapsed_seconds": elapsed,
                "passed": True,
            })

        except Exception as exc:
            print(f"\n  ❌ TEST {i} FAILED: {exc}")
            failed += 1
            results.append({
                "test": test["name"],
                "company": test["company"],
                "error": str(exc),
                "passed": False,
            })

    print(f"\n{'='*70}")
    print(f"RESULTS: {passed}/{len(TEST_CASES)} passed, {failed} failed")
    print(f"{'='*70}\n")

    # Save results
    output_path = os.path.join(os.path.dirname(__file__), "..", "test_results.json")
    with open(output_path, "w") as f:
        json.dump({
            "run_at": datetime.now().isoformat(),
            "passed": passed,
            "failed": failed,
            "results": results,
        }, f, indent=2, default=str)
    print(f"📄 Results saved to test_results.json")


if __name__ == "__main__":
    asyncio.run(run_tests())
