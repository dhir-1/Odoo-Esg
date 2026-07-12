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

        # 2. Login as Manager (Test Employee with Manager role)
        # Employee 2 (manager@ecosphere.com) represents Manager of Administration (dept 2)
        logger.info("Logging in as Manager...")
        mgr_login = await client.post(f"{BASE_REST}/auth/login", json={
            "email": "manager@ecosphere.com", "password": "managerpassword"
        })
        assert mgr_login.status_code == 200
        mgr_token = mgr_login.json()["access_token"]
        mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

        # -------------------------------------------------------------
        # TEST 1: Fixed Report Endpoints (Admin & Manager)
        # -------------------------------------------------------------
        logger.info("Testing GET /reports/environmental...")
        res = await client.get(f"{BASE_REST}/reports/environmental", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert "total_emissions_co2e" in data
        assert "goals" in data
        assert "product_profiles" in data
        print("[PASS] GET /reports/environmental returns structured JSON.")

        logger.info("Testing GET /reports/social...")
        res = await client.get(f"{BASE_REST}/reports/social", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert "diversity_breakdown" in data
        assert "csr_stats" in data
        assert "training_completion_rate" in data
        print("[PASS] GET /reports/social returns structured JSON.")

        logger.info("Testing GET /reports/governance...")
        res = await client.get(f"{BASE_REST}/reports/governance", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert "policies" in data
        assert "audits" in data
        assert "compliance_summary" in data
        print("[PASS] GET /reports/governance returns structured JSON.")

        logger.info("Testing GET /reports/esg-summary...")
        res = await client.get(f"{BASE_REST}/reports/esg-summary", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert "org_total_score" in data
        assert "department_comparison" in data
        print("[PASS] GET /reports/esg-summary returns structured JSON.")

        # -------------------------------------------------------------
        # TEST 2: Custom Builder & Exports (Admin)
        # -------------------------------------------------------------
        logger.info("Testing custom report builder (JSON)...")
        res = await client.post(
            f"{BASE_REST}/reports/custom",
            json={"export_format": "json"},
            headers=admin_headers
        )
        assert res.status_code == 200
        data = res.json()
        assert "filter_criteria" in data
        assert "environmental" in data
        assert "social" in data
        print("[PASS] POST /reports/custom with json format works.")

        logger.info("Testing custom report builder (CSV)...")
        res = await client.post(
            f"{BASE_REST}/reports/custom",
            json={"export_format": "csv"},
            headers=admin_headers
        )
        assert res.status_code == 200
        assert res.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in res.headers["content-disposition"]
        print("[PASS] POST /reports/custom with CSV format returns StreamingResponse file.")

        logger.info("Testing custom report builder (XLSX)...")
        res = await client.post(
            f"{BASE_REST}/reports/custom",
            json={"export_format": "xlsx"},
            headers=admin_headers
        )
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in res.headers["content-disposition"]
        print("[PASS] POST /reports/custom with XLSX format returns structured spreadsheet.")

        logger.info("Testing custom report builder (PDF)...")
        res = await client.post(
            f"{BASE_REST}/reports/custom",
            json={"export_format": "pdf"},
            headers=admin_headers
        )
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert "attachment" in res.headers["content-disposition"]
        print("[PASS] POST /reports/custom with PDF format returns ReportLab document.")

        # -------------------------------------------------------------
        # TEST 3: Manager RBAC override scoping
        # -------------------------------------------------------------
        logger.info("Testing Manager RBAC override scoping filters...")
        # Manager is in Administration (dept 2). Let's attempt to filter on department 1 (Engineering)
        # The API should silently override this to their department tree (Administration) instead of failing.
        res = await client.post(
            f"{BASE_REST}/reports/custom",
            json={"department_id": 1, "export_format": "json"},
            headers=mgr_headers
        )
        assert res.status_code == 200
        data = res.json()
        # Verify that engineered query scoped department list does NOT contain department 1, but contains 2
        scoped_depts = data["filter_criteria"]["departments_scoped"]
        assert 1 not in scoped_depts
        assert 2 in scoped_depts
        print("[PASS] Manager department override scoping correctly restricts view permissions.")

        print("\n[ALL ESG REPORTS TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    asyncio.run(main())
