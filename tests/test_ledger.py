import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_full_ledger_flow_and_concurrency():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Account
        res = await ac.post("/api/v1/accounts", json={"name": "Alice"})
        assert res.status_code == 201
        acc_a = res.json()["id"]
        assert float(res.json()["balance"]) == 0.0

        # 2. Credit 100
        res = await ac.post(f"/api/v1/accounts/{acc_a}/transactions", json={
            "type": "credit", "amount": 100.0, "description": "Deposit", "reference_id": "REF_ENV_01"
        })
        assert res.status_code == 201
        assert float(res.json()["current_balance"]) == 100.0

        # 3. Reject Duplicate reference_id
        res = await ac.post(f"/api/v1/accounts/{acc_a}/transactions", json={
            "type": "credit", "amount": 10.0, "description": "Dup", "reference_id": "REF_ENV_01"
        })
        assert res.status_code == 409

        # 4. Reject debit exceeding balance
        res = await ac.post(f"/api/v1/accounts/{acc_a}/transactions", json={
            "type": "debit", "amount": 500.0, "description": "Too big", "reference_id": "REF_ENV_FAIL"
        })
        assert res.status_code == 422

        # 5. Concurrency Race Condition Test:
        # Fire 7 parallel debits of 20 each (total 140 requested on 100 balance)
        tasks = [
            ac.post(f"/api/v1/accounts/{acc_a}/transactions", json={
                "type": "debit", "amount": 20.0, "description": f"Parallel {i}", "reference_id": f"P_ENV_REF_{i}"
            })
            for i in range(7)
        ]
        responses = await asyncio.gather(*tasks)
        successes = sum(1 for r in responses if r.status_code == 201)
        failures = sum(1 for r in responses if r.status_code == 422)

        # Exactly 5 should succeed (5 x 20 = 100), 2 must fail with 422
        assert successes == 5
        assert failures == 2

        # Balance must now be exactly 0.00
        bal = await ac.get(f"/api/v1/accounts/{acc_a}/balance")
        assert float(bal.json()["balance"]) == 0.0