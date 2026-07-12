import asyncio
import os
import httpx
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_REST = "http://127.0.0.1:8000/api/v1"
ADMIN_EMAIL = os.getenv("ECOSPHERE_ADMIN_EMAIL", "your-admin-email-here")
ADMIN_PASSWORD = os.getenv("ECOSPHERE_ADMIN_PASSWORD", "your-admin-password-here")

async def test_employees_endpoint():
    async with httpx.AsyncClient(timeout=10) as client:
        # 1. Login as Admin
        logger.info("Logging in as Admin...")
        admin_login = await client.post(f"{BASE_REST}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Query /employees
        logger.info("Admin querying /employees...")
        res = await client.get(f"{BASE_REST}/employees/", headers=admin_headers)
        assert res.status_code == 200
        employees_list = res.json()
        logger.info(f"Admin saw {len(employees_list)} active employees.")
        for emp in employees_list[:2]:
            logger.info(f" - {emp['full_name']} ({emp['email']}) in {emp['department_name']} as {emp['role']}")

        # 3. Query with search filter
        logger.info("Admin querying /employees?search=admin...")
        res_search = await client.get(f"{BASE_REST}/employees/", params={"search": "admin"}, headers=admin_headers)
        assert res_search.status_code == 200
        search_list = res_search.json()
        logger.info(f"Search results for 'admin': {len(search_list)}")
        for emp in search_list:
            logger.info(f" - {emp['full_name']}")

        # 4. Check policy unacknowledged-employees exists
        logger.info("Checking unacknowledged-employees endpoint path...")
        res_pols = await client.get(f"{BASE_REST}/governance/policies/", headers=admin_headers)
        assert res_pols.status_code == 200
        policies = res_pols.json()
        if policies:
            pol_id = policies[0]["id"]
            unack_res = await client.get(f"{BASE_REST}/governance/policies/{pol_id}/unacknowledged-employees", headers=admin_headers)
            assert unack_res.status_code == 200
            logger.info(f"Policy {pol_id} unacknowledged list has {len(unack_res.json())} employees.")

        logger.info("All Employees tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_employees_endpoint())
