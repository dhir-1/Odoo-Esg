import asyncio
import os
import httpx
import logging
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_REST = "http://127.0.0.1:8000/api/v1"
ADMIN_EMAIL = os.getenv("ECOSPHERE_ADMIN_EMAIL", "your-admin-email-here")
ADMIN_PASSWORD = os.getenv("ECOSPHERE_ADMIN_PASSWORD", "your-admin-password-here")
MANAGER_EMAIL = os.getenv("ECOSPHERE_MANAGER_EMAIL", "your-manager-email-here")
MANAGER_PASSWORD = os.getenv("ECOSPHERE_MANAGER_PASSWORD", "your-manager-password-here")

async def run_smoke_test():
    async with httpx.AsyncClient(timeout=30) as client:
        # =====================================================================
        # Step 1: Log in as Admin -> confirm JWT works
        # =====================================================================
        logger.info("Step 1: Logging in as Admin...")
        admin_login = await client.post(f"{BASE_REST}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if admin_login.status_code != 200:
            logger.error(f"Admin login failed: {admin_login.text}")
            return
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        logger.info("[PASS] Admin logged in, JWT obtained.")

        # =====================================================================
        # Step 2: Create a Department, a Category, an Emission Factor
        # =====================================================================
        logger.info("Step 2: Creating Department...")
        dept_code = f"SMK-{int(asyncio.get_event_loop().time())}"
        dept_res = await client.post(f"{BASE_REST}/departments/", json={
            "name": "Smoke Verification Dept",
            "code": dept_code,
            "status": "Active"
        }, headers=admin_headers)
        assert dept_res.status_code == 201, f"Dept create failed: {dept_res.text}"
        dept_id = dept_res.json()["id"]
        logger.info(f"[PASS] Created Department. ID={dept_id}, Code={dept_code}")

        logger.info("Creating Category...")
        cat_res = await client.post(f"{BASE_REST}/categories/", json={
            "name": "Smoke Verification Category",
            "type": "CSR_ACTIVITY",
            "status": "Active"
        }, headers=admin_headers)
        assert cat_res.status_code == 201, f"Category create failed: {cat_res.text}"
        cat_id = cat_res.json()["id"]
        logger.info(f"[PASS] Created CSR Category. ID={cat_id}")

        logger.info("Creating Emission Factor...")
        ef_res = await client.post(f"{BASE_REST}/emission-factors/", json={
            "name": "Smoke Verification Factor",
            "activity_type": "Purchase",
            "unit": "kWh",
            "co2e_per_unit": 0.55,
            "category_id": cat_id,
            "source_reference": "EPA 2026",
            "effective_from": "2026-01-01"
        }, headers=admin_headers)
        assert ef_res.status_code == 201, f"Emission Factor create failed: {ef_res.text}"
        ef_id = ef_res.json()["id"]
        logger.info(f"[PASS] Created Emission Factor. ID={ef_id}")

        # Ensure auto calculation enabled
        logger.info("Setting auto emission calculation setting to True...")
        settings_res = await client.patch(f"{BASE_REST}/settings/notification-preferences", json={
            "auto_emission_calculation_enabled": True
        }, headers=admin_headers)
        assert settings_res.status_code == 200, f"Settings patch failed: {settings_res.text}"

        # =====================================================================
        # Step 3: Log a Carbon Transaction, confirm calculated_co2e math is right
        # =====================================================================
        logger.info("Step 3: Logging a Carbon Transaction...")
        tx_res = await client.post(f"{BASE_REST}/carbon-transactions/simulate", json={
            "department_id": dept_id,
            "emission_factor_id": ef_id,
            "quantity": 200.0,
            "source_module": "Purchase",
            "source_reference_id": f"ref-{int(asyncio.get_event_loop().time())}",
            "transaction_date": str(date.today()),
            "notes": "Smoke test calculation"
        }, headers=admin_headers)
        assert tx_res.status_code == 201, f"Carbon transaction simulation failed: {tx_res.text}"
        tx_data = tx_res.json()
        expected_co2e = 200.0 * 0.55
        actual_co2e = float(tx_data["calculated_co2e"])
        assert abs(actual_co2e - expected_co2e) < 0.0001, f"Expected {expected_co2e}, got {actual_co2e}"
        logger.info(f"[PASS] Carbon Transaction logged. calculated_co2e: {actual_co2e} kg (Matches quantity * factor).")

        # =====================================================================
        # Step 4: Register & Join a CSR Activity as Employee -> approve as Admin/Manager
        # =====================================================================
        # Register a new Employee in the department
        logger.info("Step 4: Registering a new Employee...")
        emp_code = f"EMP-{int(asyncio.get_event_loop().time())}"
        emp_register = await client.post(f"{BASE_REST}/auth/register", json={
            "employee_code": emp_code,
            "full_name": "Smoke Employee User",
            "email": f"employee-{emp_code.lower()}@ecosphere.com",
            "password": os.getenv("ECOSPHERE_EMPLOYEE_PASSWORD", "your-employee-password-here"),
            "role": "Employee",
            "department_id": dept_id,
            "designation": "Sustainability Officer",
            "date_joined": "2026-07-01"
        }, headers=admin_headers)
        assert emp_register.status_code == 201, f"Employee registration failed: {emp_register.text}"
        emp_data = emp_register.json()
        emp_id = emp_data["id"]
        logger.info(f"[PASS] Registered Employee. ID={emp_id}, Code={emp_code}")

        # Log in as Employee
        emp_login = await client.post(f"{BASE_REST}/auth/login", json={
            "email": f"employee-{emp_code.lower()}@ecosphere.com",
            "password": os.getenv("ECOSPHERE_EMPLOYEE_PASSWORD", "your-employee-password-here")
        })
        assert emp_login.status_code == 200
        emp_token = emp_login.json()["access_token"]
        emp_headers = {"Authorization": f"Bearer {emp_token}"}

        # Create a CSR Activity
        logger.info("Creating a CSR Activity...")
        csr_res = await client.post(f"{BASE_REST}/csr/csr-activities/", json={
            "title": "Smoke Tree Planting Initiative",
            "category_id": cat_id,
            "department_id": dept_id,
            "description": "Planting trees for carbon offsets",
            "activity_date": str(date.today()),
            "points_value": 75,
            "evidence_required": False
        }, headers=admin_headers)
        assert csr_res.status_code == 201, f"CSR Activity creation failed: {csr_res.text}"
        csr_id = csr_res.json()["id"]
        logger.info(f"[PASS] Created CSR Activity. ID={csr_id}")

        # Employee joins CSR Activity
        logger.info("Employee joining CSR Activity...")
        join_res = await client.post(f"{BASE_REST}/csr/csr-activities/{csr_id}/join", headers=emp_headers)
        assert join_res.status_code == 201, f"CSR Join failed: {join_res.text}"
        part_id = join_res.json()["id"]
        logger.info(f"[PASS] Employee joined CSR Activity. Participation ID={part_id}")

        # Submit proof (optional since evidence_required is False, but good for verification)
        logger.info("Employee submitting proof...")
        proof_res = await client.patch(f"{BASE_REST}/csr/participation/{part_id}/proof", json={
            "proof_url": "http://example.com/tree.jpg"
        }, headers=emp_headers)
        assert proof_res.status_code == 200

        # Admin approves CSR Participation
        logger.info("Admin approving participation...")
        app_res = await client.patch(f"{BASE_REST}/participation/csr/{part_id}/approve", headers=admin_headers)
        assert app_res.status_code == 200, f"Approval failed: {app_res.text}"

        # Verify points_balance incremented
        logger.info("Checking if employee points_balance increased by 75...")
        me_res = await client.get(f"{BASE_REST}/auth/me", headers=emp_headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["points_balance"] == 75, f"Expected 75 points, got {me_data['points_balance']}"
        logger.info(f"[PASS] CSR completion approved. Employee points: {me_data['points_balance']}.")

        # =====================================================================
        # Step 5: Join + complete a Challenge -> confirm Badge auto-awards
        # =====================================================================
        # Create Challenge Category
        logger.info("Step 5: Creating Challenge Category...")
        chal_cat_res = await client.post(f"{BASE_REST}/categories/", json={
            "name": "Smoke Challenge Category",
            "type": "CHALLENGE",
            "status": "Active"
        }, headers=admin_headers)
        assert chal_cat_res.status_code == 201
        chal_cat_id = chal_cat_res.json()["id"]

        # Create Challenge
        logger.info("Creating a Challenge...")
        chal_res = await client.post(f"{BASE_REST}/challenges/challenges/", json={
            "title": "Smoke Green Commute Challenge",
            "category_id": chal_cat_id,
            "description": "Bike or walk to work",
            "xp_reward": 80,
            "difficulty": "Easy",
            "evidence_required": True,
            "deadline": str(date.today() + timedelta(days=7))
        }, headers=admin_headers)
        assert chal_res.status_code == 201, f"Challenge creation failed: {chal_res.text}"
        chal_id = chal_res.json()["id"]

        # Transition Challenge status from Draft to Active
        logger.info("Activating Challenge...")
        act_res = await client.patch(f"{BASE_REST}/challenges/challenges/{chal_id}", json={
            "status": "Active"
        }, headers=admin_headers)
        assert act_res.status_code == 200

        # Employee joins Challenge
        logger.info("Employee joining Challenge...")
        chal_join = await client.post(f"{BASE_REST}/challenges/challenges/{chal_id}/join", headers=emp_headers)
        assert chal_join.status_code == 201, f"Challenge Join failed: {chal_join.text}"
        chal_part_id = chal_join.json()["id"]

        # Employee submits progress proof
        logger.info("Employee submitting progress proof...")
        prog_res = await client.patch(f"{BASE_REST}/challenges/participation/{chal_part_id}/progress", json={
            "progress": 100.0,
            "proof_url": "http://example.com/bike.jpg"
        }, headers=emp_headers)
        assert prog_res.status_code == 200

        # Create Badge with unlock rule mapping: xp_threshold = 50
        logger.info("Creating Badge with XP threshold rule...")
        badge_res = await client.post(f"{BASE_REST}/badges/", json={
            "name": "Smoke Commuter Expert",
            "description": "Awarded for earning 50+ XP",
            "unlock_rule": {"xp_threshold": 50},
            "icon_url": "http://example.com/badge.png"
        }, headers=admin_headers)
        assert badge_res.status_code == 201
        badge_id = badge_res.json()["id"]

        # Enable badge auto award
        logger.info("Enabling badge auto award toggle...")
        await client.patch(f"{BASE_REST}/settings/notification-preferences", json={
            "badge_auto_award_enabled": True
        }, headers=admin_headers)

        # Admin approves Challenge Completion
        logger.info("Admin approving challenge completion...")
        chal_app = await client.patch(f"{BASE_REST}/participation/challenge/{chal_part_id}/approve", headers=admin_headers)
        assert chal_app.status_code == 200, f"Challenge approval failed: {chal_app.text}"

        # Verify XP incremented and Badge unlocked
        logger.info("Verifying employee XP and awarded badges...")
        me_res2 = await client.get(f"{BASE_REST}/auth/me", headers=emp_headers)
        me_data2 = me_res2.json()
        assert me_data2["xp_points"] == 155, f"Expected 155 XP, got {me_data2['xp_points']}"
        logger.info(f"[PASS] Challenge approved. Employee XP points: {me_data2['xp_points']}.")


        # Retrieve employee earned badges
        logger.info("Retrieving employee earned badges...")
        badges_earned_res = await client.get(f"{BASE_REST}/employees/{emp_id}/badges", headers=emp_headers)
        assert badges_earned_res.status_code == 200
        badges_earned = badges_earned_res.json()
        earned_badge_ids = [eb["badge_id"] for eb in badges_earned]
        assert badge_id in earned_badge_ids, f"Badge {badge_id} not found in earned: {earned_badge_ids}"
        logger.info("[PASS] Badge auto-award rule triggered and badge successfully awarded!")

        # =====================================================================
        # Step 6: Hit POST /scores/calculate for one department
        # =====================================================================
        logger.info("Step 6: Triggering ESG score calculation...")
        calc_res = await client.post(
            f"{BASE_REST}/scores/calculate",
            params={
                "department_id": dept_id,
                "period_start": str(date.today() - timedelta(days=30)),
                "period_end": str(date.today())
            },
            headers=admin_headers
        )
        assert calc_res.status_code == 201, f"Score calculation failed: {calc_res.text}"
        score_data = calc_res.json()["score"]
        logger.info(f"[PASS] Calculated scores: Overall Total={score_data['total_score']}, E={score_data['environmental_score']}, S={score_data['social_score']}, G={score_data['governance_score']}")
        # Make sure scores are sensible numbers
        assert float(score_data['total_score']) >= 0.0, "Score total is negative"
        assert float(score_data['social_score']) >= 0.0, "Social score is negative"

        # =====================================================================
        # Step 7: Hit GET /leaderboard and GET /participation/pending
        # =====================================================================
        logger.info("Step 7: Testing GET /leaderboard...")
        leader_res = await client.get(f"{BASE_REST}/leaderboard?entry_type=employee", headers=admin_headers)
        assert leader_res.status_code == 200
        leader_data = leader_res.json()
        logger.info(f"[PASS] Leaderboard list successfully retrieved: {leader_data[:3]}")

        logger.info("Testing GET /participation/pending...")
        pending_res = await client.get(f"{BASE_REST}/participation/pending", headers=admin_headers)
        assert pending_res.status_code == 200
        pending_data = pending_res.json()
        logger.info(f"[PASS] Pending participations list successfully retrieved. Count: {len(pending_data)}")

        # =====================================================================
        # Step 8: Hit the four GET /dashboard/* endpoints
        # =====================================================================
        logger.info("Step 8: Testing Dashboard summary...")
        res = await client.get(f"{BASE_REST}/dashboard/summary", headers=admin_headers)
        assert res.status_code == 200
        logger.info(f"[PASS] Dashboard summary: {res.json()}")

        logger.info("Testing Dashboard emissions-trend...")
        res = await client.get(f"{BASE_REST}/dashboard/emissions-trend?months=6", headers=admin_headers)
        assert res.status_code == 200
        logger.info(f"[PASS] Dashboard emissions-trend: {res.json()}")

        logger.info("Testing Dashboard department-ranking...")
        res = await client.get(f"{BASE_REST}/dashboard/department-ranking", headers=admin_headers)
        assert res.status_code == 200
        logger.info(f"[PASS] Dashboard department-ranking: {res.json()}")

        logger.info("Testing Dashboard recent-activity...")
        res = await client.get(f"{BASE_REST}/dashboard/recent-activity", headers=admin_headers)
        assert res.status_code == 200
        logger.info(f"[PASS] Dashboard recent-activity: {res.json()[:3]}")

        logger.info("\n[CONGRATULATIONS! ALL BACKEND CORE LOOP SMOKE-TESTS PASSED FLAWLESSLY!]")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
