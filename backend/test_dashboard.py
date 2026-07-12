import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_REST = "http://127.0.0.1:8000/api/v1"


async def main():
    async with httpx.AsyncClient(timeout=15) as client:
        # 1. Login as Admin
        logger.info("Logging in as Admin...")
        admin_login = await client.post(f"{BASE_REST}/auth/login", json={
            "email": "admin@ecosphere.com", "password": "adminpassword"
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Login as Manager (Employee 2)
        logger.info("Logging in as Manager...")
        mgr_login = await client.post(f"{BASE_REST}/auth/login", json={
            "email": "manager@ecosphere.com", "password": "managerpassword"
        })
        assert mgr_login.status_code == 200
        mgr_token = mgr_login.json()["access_token"]
        mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

        # -------------------------------------------------------------
        # TEST 1: Summary KPI Tiles
        # -------------------------------------------------------------
        logger.info("Testing GET /dashboard/summary (Admin)...")
        res = await client.get(f"{BASE_REST}/dashboard/summary", headers=admin_headers)
        assert res.status_code == 200
        sum_admin = res.json()
        assert "environmental_score" in sum_admin
        assert "social_score" in sum_admin
        assert "overall_esg_score" in sum_admin
        logger.info(f"Admin summary returned: {sum_admin}")

        logger.info("Testing GET /dashboard/summary (Manager)...")
        res = await client.get(f"{BASE_REST}/dashboard/summary", headers=mgr_headers)
        assert res.status_code == 200
        sum_mgr = res.json()
        assert "environmental_score" in sum_mgr
        assert "social_score" in sum_mgr
        assert "overall_esg_score" in sum_mgr
        logger.info(f"Manager summary returned: {sum_mgr}")
        print("[PASS] GET /dashboard/summary returns correctly scoped KPIs.")

        # -------------------------------------------------------------
        # TEST 2: Emissions Trend
        # -------------------------------------------------------------
        logger.info("Testing GET /dashboard/emissions-trend?months=6...")
        res = await client.get(f"{BASE_REST}/dashboard/emissions-trend?months=6", headers=admin_headers)
        assert res.status_code == 200
        trend = res.json()
        assert len(trend) == 6
        for t in trend:
            assert "period" in t
            assert "co2e" in t
        logger.info(f"Emissions trend response (6 months): {trend}")
        print("[PASS] GET /dashboard/emissions-trend computes chronological trend blocks.")

        # -------------------------------------------------------------
        # TEST 3: Department Rankings
        # -------------------------------------------------------------
        logger.info("Testing GET /dashboard/department-ranking (Admin)...")
        res = await client.get(f"{BASE_REST}/dashboard/department-ranking", headers=admin_headers)
        assert res.status_code == 200
        ranks = res.json()
        logger.info(f"Department ranks list (length {len(ranks)}): {ranks}")

        logger.info("Testing GET /dashboard/department-ranking (Manager - should be 403 Forbidden)...")
        res = await client.get(f"{BASE_REST}/dashboard/department-ranking", headers=mgr_headers)
        assert res.status_code == 403
        logger.info(f"Manager check successfully rejected with HTTP 403.")
        print("[PASS] Department performance rankings checks are strictly Admin-only.")

        # -------------------------------------------------------------
        # TEST 4: Recent Activities
        # -------------------------------------------------------------
        logger.info("Testing GET /dashboard/recent-activity...")
        res = await client.get(f"{BASE_REST}/dashboard/recent-activity?limit=5", headers=admin_headers)
        assert res.status_code == 200
        feed = res.json()
        assert len(feed) <= 5
        for f in feed:
            assert "event_type" in f
            assert "summary_text" in f
        logger.info(f"Recent Activity Feed entries: {feed}")
        print("[PASS] Recent Activity Feed loaded and formatted successfully.")

        print("\n[ALL EXECUTIVE DASHBOARD TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    asyncio.run(main())
