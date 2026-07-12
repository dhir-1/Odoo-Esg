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

        # -------------------------------------------------------------
        # TEST 1: ESG Weights & Configurations
        # -------------------------------------------------------------
        logger.info("Testing GET /settings/esg-configuration...")
        res = await client.get(f"{BASE_REST}/settings/esg-configuration", headers=admin_headers)
        assert res.status_code == 200
        config = res.json()
        assert "environmental_weight" in config
        assert "social_weight" in config
        assert "governance_weight" in config
        logger.info(f"Default config loaded: {config}")

        logger.info("Testing PATCH /settings/esg-configuration with valid weights (sum to 1.0)...")
        res = await client.patch(
            f"{BASE_REST}/settings/esg-configuration",
            json={
                "environmental_weight": 0.35,
                "social_weight": 0.35,
                "governance_weight": 0.30
            },
            headers=admin_headers
        )
        assert res.status_code == 200
        updated_config = res.json()
        assert float(updated_config["environmental_weight"]) == 0.35
        assert float(updated_config["social_weight"]) == 0.35
        assert float(updated_config["governance_weight"]) == 0.30
        print("[PASS] Valid weights update successfully applied.")

        logger.info("Testing PATCH /settings/esg-configuration with invalid weights (sum != 1.0)...")
        res = await client.patch(
            f"{BASE_REST}/settings/esg-configuration",
            json={
                "environmental_weight": 0.40,
                "social_weight": 0.40,
                "governance_weight": 0.40
            },
            headers=admin_headers
        )
        assert res.status_code == 422
        logger.info(f"Invalid weights sum correctly rejected with HTTP 422: {res.json()}")
        print("[PASS] Invalid weights sum correctly rejected with 422.")

        # -------------------------------------------------------------
        # TEST 2: Notification Preferences (4 Toggles Only)
        # -------------------------------------------------------------
        logger.info("Testing GET /settings/notification-preferences...")
        res = await client.get(f"{BASE_REST}/settings/notification-preferences", headers=admin_headers)
        assert res.status_code == 200
        prefs = res.json()
        # Verify exactly the four wireframe toggles are present
        assert "auto_emission_calculation_enabled" in prefs
        assert "evidence_requirement_enabled" in prefs
        assert "badge_auto_award_enabled" in prefs
        assert "notify_on_compliance_issue" in prefs
        # Make sure internal-only fields are NOT returned
        assert "notify_on_approval_decision" not in prefs
        assert "notify_on_policy_reminder" not in prefs
        assert "notify_on_badge_unlock" not in prefs
        logger.info(f"Exposed settings screen preferences: {prefs}")
        print("[PASS] Notification preferences endpoints map exactly to the four wireframe fields.")

        logger.info("Testing PATCH /settings/notification-preferences...")
        res = await client.patch(
            f"{BASE_REST}/settings/notification-preferences",
            json={
                "auto_emission_calculation_enabled": True,
                "evidence_requirement_enabled": True,
                "badge_auto_award_enabled": True,
                "notify_on_compliance_issue": False
            },
            headers=admin_headers
        )
        assert res.status_code == 200
        updated_prefs = res.json()
        assert updated_prefs["auto_emission_calculation_enabled"] is True
        assert updated_prefs["evidence_requirement_enabled"] is True
        assert updated_prefs["badge_auto_award_enabled"] is True
        assert updated_prefs["notify_on_compliance_issue"] is False
        print("[PASS] Notification preferences updated successfully.")

        # -------------------------------------------------------------
        # TEST 3: Department Pre-Joined Listing & Ancestor Loops
        # -------------------------------------------------------------
        logger.info("Creating Department A (Parent)...")
        res = await client.post(
            f"{BASE_REST}/departments/",
            json={"name": "Dept A", "code": "DEPTA", "status": "Active"},
            headers=admin_headers
        )
        assert res.status_code == 201
        dept_a_id = res.json()["id"]

        logger.info("Creating Department B (Child of A)...")
        res = await client.post(
            f"{BASE_REST}/departments/",
            json={"name": "Dept B", "code": "DEPTB", "status": "Active", "parent_department_id": dept_a_id},
            headers=admin_headers
        )
        assert res.status_code == 201
        dept_b_id = res.json()["id"]

        logger.info("Testing Department circular loop validation check (Updating parent of A to B)...")
        res = await client.patch(
            f"{BASE_REST}/departments/{dept_a_id}",
            json={"parent_department_id": dept_b_id},
            headers=admin_headers
        )
        assert res.status_code == 400
        logger.info(f"Loop update correctly rejected with HTTP 400: {res.json()['detail']}")
        print("[PASS] Circular hierarchy loop check correctly validated.")

        logger.info("Testing pre-joined fields on GET /departments list...")
        # Add head employee to Department B
        # Let's search for an active employee (ID=1)
        res = await client.patch(
            f"{BASE_REST}/departments/{dept_b_id}",
            json={"head_employee_id": 1},
            headers=admin_headers
        )
        assert res.status_code == 200
        
        # Query departments list and inspect pre-joined names
        res = await client.get(f"{BASE_REST}/departments/", headers=admin_headers)
        assert res.status_code == 200
        depts = res.json()
        
        # Check pre-joined properties exist
        dept_b_list_item = next(d for d in depts if d["id"] == dept_b_id)
        assert dept_b_list_item["parent_department_name"] == "Dept A"
        assert dept_b_list_item["head_employee_name"] is not None
        
        logger.info(f"Dept B listing item verified: {dept_b_list_item}")
        print("[PASS] Department listings return pre-joined Head Employee and Parent Department names.")

        print("\n[ALL ESG SETTINGS & DEPARTMENTS TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    asyncio.run(main())
