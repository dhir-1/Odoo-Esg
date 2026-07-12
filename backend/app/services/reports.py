import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import Employee
from app.models.department import Department, DepartmentScore
from app.models.carbon import CarbonTransaction
from app.models.environmental import EnvironmentalGoal, ProductESGProfile, EmissionFactor
from app.models.social import CSRActivity, EmployeeParticipation, DiversityMetric, TrainingRecord
from app.models.governance import ESGPolicy, PolicyAcknowledgement, Audit, ComplianceIssue
from app.models.gamification import ChallengeParticipation, Challenge, RewardRedemption
from app.models.enums import (
    StatusEnum,
    GoalLifecycleStatusEnum,
    GoalProgressStatusEnum,
    ParticipationApprovalStatusEnum,
    TrainingRecordStatusEnum,
    PolicyStatusEnum,
    AuditStatusEnum,
    ComplianceIssueSeverityEnum,
    ComplianceIssueStatusEnum,
    RoleEnum
)

logger = logging.getLogger(__name__)

async def get_allowed_department_ids(
    db: AsyncSession, current_user: Employee, filter_dept_id: Optional[int] = None
) -> List[int]:
    """
    Resolves the list of department IDs a user is authorized to view.
    - Admin: Can view all departments. If filter_dept_id is provided, restricts to that one.
    - Manager: Can view their own department and all its nested sub-departments.
               Silently ignores/overrides filter_dept_id if it's not in their sub-tree.
    - Employee: Restricted strictly to their own department.
    """
    if current_user.role == RoleEnum.ADMIN:
        if filter_dept_id is not None:
            return [filter_dept_id]
        # Return all active department IDs
        res = await db.execute(select(Department.id).filter(Department.status == StatusEnum.ACTIVE))
        return [row[0] for row in res.all()]

    # Manager: Sub-department tree check via recursive CTE
    if current_user.role == RoleEnum.MANAGER:
        manager_dept_id = current_user.department_id
        subdeps_query = text("""
            WITH RECURSIVE subdeps AS (
                SELECT id FROM departments WHERE id = :manager_dept_id
                UNION ALL
                SELECT d.id FROM departments d JOIN subdeps s ON d.parent_department_id = s.id
            ) SELECT id FROM subdeps;
        """)
        res = await db.execute(subdeps_query, {"manager_dept_id": manager_dept_id})
        allowed_ids = [row[0] for row in res.fetchall()]

        if filter_dept_id is not None:
            if filter_dept_id in allowed_ids:
                return [filter_dept_id]
            else:
                # Silently ignore the out-of-scope filter and return allowed branch IDs
                logger.warning(
                    f"Manager {current_user.id} attempted to view out-of-scope department {filter_dept_id}. Overridden."
                )
                return allowed_ids
        return allowed_ids

    # Employee: Strict self department scoping
    return [current_user.department_id]


async def get_environmental_report(db: AsyncSession, allowed_dept_ids: List[int]) -> Dict[str, Any]:
    """
    Gathers environmental statistics:
    - total emissions (CO2e)
    - emissions breakdown by source module
    - environmental goal progress
    - product ESG profiles
    """
    # 1. Total Emissions & Source breakdown
    tx_query = (
        select(
            CarbonTransaction.source_module,
            func.coalesce(func.sum(CarbonTransaction.calculated_co2e), 0.0)
        )
        .filter(CarbonTransaction.department_id.in_(allowed_dept_ids))
        .group_by(CarbonTransaction.source_module)
    )
    tx_res = await db.execute(tx_query)
    emissions_by_source = {row[0].value: float(row[1]) for row in tx_res.all()}
    total_emissions = sum(emissions_by_source.values())

    # 2. Environmental Goals
    goals_res = await db.execute(
        select(EnvironmentalGoal)
        .filter(EnvironmentalGoal.department_id.in_(allowed_dept_ids))
    )
    goals = goals_res.scalars().all()
    goals_list = []
    for g in goals:
        goals_list.append({
            "id": g.id,
            "title": g.title,
            "metric_type": g.metric_type,
            "target_value": float(g.target_value),
            "current_value": float(g.current_value),
            "unit": g.unit,
            "start_date": g.start_date.isoformat(),
            "target_date": g.target_date.isoformat(),
            "progress_status": g.progress_status.value if g.progress_status else "UNKNOWN"
        })

    # 3. Product profiles with emission factor name
    profiles_res = await db.execute(
        select(ProductESGProfile)
        .options(selectinload(ProductESGProfile.emission_factor))
        .filter(ProductESGProfile.status == StatusEnum.ACTIVE)
        .limit(20)
    )
    profiles = profiles_res.scalars().all()
    profiles_list = []
    for p in profiles:
        profiles_list.append({
            "id": p.id,
            "product_name": p.product_name,
            "sku": p.sku,
            "category": p.category,
            "sustainability_score": float(p.sustainability_score) if p.sustainability_score else None,
            "emission_factor_name": p.emission_factor.name if p.emission_factor else None
        })

    return {
        "total_emissions_co2e": round(total_emissions, 2),
        "emissions_by_source": emissions_by_source,
        "goals": goals_list,
        "product_profiles": profiles_list
    }


async def get_social_report(db: AsyncSession, allowed_dept_ids: List[int]) -> Dict[str, Any]:
    """
    Gathers social pillars data:
    - gender diversity metric breakdown (latest period)
    - CSR stats (participation counts, points)
    - training record completion rates
    """
    # 1. Diversity breakdown (Gender category, latest period)
    latest_period_res = await db.execute(
        select(DiversityMetric.period)
        .filter(DiversityMetric.department_id.in_(allowed_dept_ids))
        .order_by(DiversityMetric.period.desc())
        .limit(1)
    )
    latest_period = latest_period_res.scalar()
    
    diversity_list = []
    if latest_period:
        div_res = await db.execute(
            select(DiversityMetric.label, func.sum(DiversityMetric.count))
            .filter(
                DiversityMetric.department_id.in_(allowed_dept_ids),
                DiversityMetric.category == "Gender",
                DiversityMetric.period == latest_period
            )
            .group_by(DiversityMetric.label)
        )
        for label, count in div_res.all():
            diversity_list.append({"label": label, "count": int(count), "period": latest_period})

    # 2. CSR Stats
    csr_query = (
        select(
            func.count(EmployeeParticipation.id),
            func.coalesce(func.sum(EmployeeParticipation.points_earned), 0)
        )
        .join(Employee, EmployeeParticipation.employee_id == Employee.id)
        .filter(
            Employee.department_id.in_(allowed_dept_ids),
            EmployeeParticipation.approval_status == ParticipationApprovalStatusEnum.APPROVED
        )
    )
    csr_res = await db.execute(csr_query)
    approved_count, total_points = csr_res.first() or (0, 0)

    total_activities_res = await db.execute(
        select(func.count(CSRActivity.id))
        .filter(or_(CSRActivity.department_id.in_(allowed_dept_ids), CSRActivity.department_id == None))
    )
    total_activities = total_activities_res.scalar() or 0

    # 3. Training completion rates
    training_res = await db.execute(
        select(TrainingRecord.status, func.count(TrainingRecord.id))
        .join(Employee, TrainingRecord.employee_id == Employee.id)
        .filter(Employee.department_id.in_(allowed_dept_ids))
        .group_by(TrainingRecord.status)
    )
    status_counts = {row[0].value: int(row[1]) for row in training_res.all()}
    completed = status_counts.get("Completed", 0)
    total_trainings = sum(status_counts.values())
    completion_rate = round((completed / total_trainings * 100), 2) if total_trainings > 0 else 0.0

    return {
        "diversity_breakdown": diversity_list,
        "csr_stats": {
            "total_activities_available": total_activities,
            "approved_participations": approved_count,
            "total_points_earned": total_points
        },
        "training_completion_rate": {
            "completed": completed,
            "total": total_trainings,
            "rate_percent": completion_rate
        }
    }


async def get_governance_report(db: AsyncSession, allowed_dept_ids: List[int]) -> Dict[str, Any]:
    """
    Gathers governance data:
    - Active policy list and acknowledgement rates
    - Audit list
    - Compliance issue counts by severity & status
    """
    # 1. Headcount of active employees in scoped depts (needed for policy ack rate)
    headcount_res = await db.execute(
        select(func.count(Employee.id))
        .filter(Employee.department_id.in_(allowed_dept_ids), Employee.status == StatusEnum.ACTIVE)
    )
    headcount = max(headcount_res.scalar() or 0, 1)

    # Policies & Acks
    policies_res = await db.execute(
        select(ESGPolicy)
        .filter(ESGPolicy.status == PolicyStatusEnum.ACTIVE)
    )
    policies = policies_res.scalars().all()
    policy_list = []
    for p in policies:
        # Count acknowledgements for current policy version by active employees in allowed departments
        ack_res = await db.execute(
            select(func.count(PolicyAcknowledgement.id))
            .join(Employee, PolicyAcknowledgement.employee_id == Employee.id)
            .filter(
                PolicyAcknowledgement.policy_id == p.id,
                PolicyAcknowledgement.policy_version == p.version,
                Employee.department_id.in_(allowed_dept_ids),
                Employee.status == StatusEnum.ACTIVE
            )
        )
        acks_count = ack_res.scalar() or 0
        ack_rate = round((acks_count / headcount) * 100, 2)
        policy_list.append({
            "id": p.id,
            "title": p.title,
            "category": p.category.value,
            "version": p.version,
            "requires_acknowledgement": p.requires_acknowledgement,
            "acknowledgement_rate_percent": ack_rate
        })

    # 2. Audit list
    audits_res = await db.execute(
        select(Audit)
        .filter(Audit.department_id.in_(allowed_dept_ids))
        .order_by(Audit.audit_date.desc())
    )
    audits = audits_res.scalars().all()
    audits_list = []
    for a in audits:
        audits_list.append({
            "id": a.id,
            "title": a.title,
            "audit_date": a.audit_date.isoformat(),
            "status": a.status.value,
            "scope": a.scope,
            "overall_rating": float(a.overall_rating) if a.overall_rating else None
        })

    # 3. Compliance risk summary
    issues_res = await db.execute(
        select(ComplianceIssue.severity, ComplianceIssue.status, func.count(ComplianceIssue.id))
        .join(Audit, ComplianceIssue.audit_id == Audit.id)
        .filter(Audit.department_id.in_(allowed_dept_ids))
        .group_by(ComplianceIssue.severity, ComplianceIssue.status)
    )
    
    severity_counts = {}
    status_counts = {}
    total_issues = 0

    for severity, status_val, count in issues_res.all():
        sev_name = severity.value
        stat_name = status_val.value
        severity_counts[sev_name] = severity_counts.get(sev_name, 0) + int(count)
        status_counts[stat_name] = status_counts.get(stat_name, 0) + int(count)
        total_issues += int(count)

    return {
        "policies": policy_list,
        "audits": audits_list,
        "compliance_summary": {
            "total_issues": total_issues,
            "by_severity": severity_counts,
            "by_status": status_counts
        }
    }


async def get_esg_summary_report(db: AsyncSession, allowed_dept_ids: List[int]) -> Dict[str, Any]:
    """
    Gathers overall ESG scores summary:
    - Average org scores for period
    - Department-by-department comparisons
    """
    # 1. Fetch latest DepartmentScore for each department in branch
    dept_scores = []
    for dept_id in allowed_dept_ids:
        score_res = await db.execute(
            select(DepartmentScore)
            .filter(DepartmentScore.department_id == dept_id)
            .order_by(DepartmentScore.calculated_at.desc())
            .limit(1)
        )
        score = score_res.scalars().first()
        dept_res = await db.execute(select(Department.name).filter(Department.id == dept_id))
        dept_name = dept_res.scalar() or f"Dept {dept_id}"
        
        if score:
            dept_scores.append({
                "department_id": dept_id,
                "department_name": dept_name,
                "environmental_score": float(score.environmental_score),
                "social_score": float(score.social_score),
                "governance_score": float(score.governance_score),
                "total_score": float(score.total_score),
                "calculated_at": score.calculated_at.isoformat()
            })
        else:
            # Default empty score representation
            dept_scores.append({
                "department_id": dept_id,
                "department_name": dept_name,
                "environmental_score": 0.0,
                "social_score": 0.0,
                "governance_score": 0.0,
                "total_score": 0.0,
                "calculated_at": None
            })

    # Average scores calculation (unweighted simple average for executive overview across allowed tree)
    env_avg = sum(s["environmental_score"] for s in dept_scores) / len(dept_scores) if dept_scores else 0.0
    soc_avg = sum(s["social_score"] for s in dept_scores) / len(dept_scores) if dept_scores else 0.0
    gov_avg = sum(s["governance_score"] for s in dept_scores) / len(dept_scores) if dept_scores else 0.0
    tot_avg = sum(s["total_score"] for s in dept_scores) / len(dept_scores) if dept_scores else 0.0

    return {
        "org_total_score": round(tot_avg, 2),
        "org_environmental_avg": round(env_avg, 2),
        "org_social_avg": round(soc_avg, 2),
        "org_governance_avg": round(gov_avg, 2),
        "department_comparison": dept_scores
    }


async def get_custom_report(db: AsyncSession, allowed_dept_ids: List[int], filters: dict) -> Dict[str, Any]:
    """
    Custom report query builder filtering on departments, dates, modules, employees, etc.
    """
    dept_id = filters.get("department_id")
    # Resolve filtering department scope
    query_dept_ids = [dept_id] if dept_id is not None and dept_id in allowed_dept_ids else allowed_dept_ids

    date_from = filters.get("date_from")
    date_to = filters.get("date_to")
    module = filters.get("module")
    employee_id = filters.get("employee_id")
    challenge_id = filters.get("challenge_id")
    esg_category = filters.get("esg_category")

    report_out = {
        "filter_criteria": {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "module_requested": module,
            "departments_scoped": query_dept_ids
        },
        "environmental": {},
        "social": {},
        "governance": {},
        "gamification": {}
    }

    # Helper function for date filters
    def apply_date_filter(query, date_column):
        if date_from:
            query = query.filter(date_column >= date_from)
        if date_to:
            query = query.filter(date_column <= date_to)
        return query

    # 1. Environmental Module
    if not module or module.lower() == "environmental":
        tx_q = select(CarbonTransaction).filter(CarbonTransaction.department_id.in_(query_dept_ids))
        tx_q = apply_date_filter(tx_q, CarbonTransaction.transaction_date)
        if employee_id:
            tx_q = tx_q.filter(CarbonTransaction.created_by_id == employee_id)
        
        tx_res = await db.execute(tx_q)
        tx_list = []
        for tx in tx_res.scalars().all():
            tx_list.append({
                "id": tx.id,
                "source_module": tx.source_module.value,
                "quantity": float(tx.quantity),
                "calculated_co2e": float(tx.calculated_co2e),
                "transaction_date": tx.transaction_date.isoformat()
            })

        goals_q = select(EnvironmentalGoal).filter(EnvironmentalGoal.department_id.in_(query_dept_ids))
        goals_res = await db.execute(goals_q)
        goals_list = []
        for g in goals_res.scalars().all():
            goals_list.append({
                "id": g.id,
                "title": g.title,
                "target_value": float(g.target_value),
                "current_value": float(g.current_value),
                "progress_status": g.progress_status.value if g.progress_status else "UNKNOWN"
            })

        report_out["environmental"] = {
            "carbon_transactions": tx_list,
            "goals": goals_list
        }

    # 2. Social Module
    if not module or module.lower() == "social":
        csr_q = select(EmployeeParticipation).filter(
            EmployeeParticipation.employee_id.in_(
                select(Employee.id).filter(Employee.department_id.in_(query_dept_ids))
            )
        )
        if employee_id:
            csr_q = csr_q.filter(EmployeeParticipation.employee_id == employee_id)
        csr_q = apply_date_filter(csr_q, EmployeeParticipation.completion_date)

        csr_res = await db.execute(csr_q.options(selectinload(EmployeeParticipation.activity)))
        csr_list = []
        for p in csr_res.scalars().all():
            csr_list.append({
                "id": p.id,
                "activity_title": p.activity.title,
                "points_earned": p.points_earned,
                "approval_status": p.approval_status.value,
                "completion_date": p.completion_date.isoformat() if p.completion_date else None
            })

        div_q = select(DiversityMetric).filter(DiversityMetric.department_id.in_(query_dept_ids))
        if esg_category:
            div_q = div_q.filter(DiversityMetric.category == esg_category)
        div_res = await db.execute(div_q)
        div_list = []
        for dm in div_res.scalars().all():
            div_list.append({
                "category": dm.category.value,
                "label": dm.label,
                "count": dm.count,
                "period": dm.period
            })

        report_out["social"] = {
            "csr_participations": csr_list,
            "diversity_metrics": div_list
        }

    # 3. Governance Module
    if not module or module.lower() == "governance":
        audits_q = select(Audit).filter(Audit.department_id.in_(query_dept_ids))
        audits_q = apply_date_filter(audits_q, Audit.audit_date)
        audits_res = await db.execute(audits_q)
        audits_list = []
        for a in audits_res.scalars().all():
            audits_list.append({
                "id": a.id,
                "title": a.title,
                "audit_date": a.audit_date.isoformat(),
                "status": a.status.value,
                "overall_rating": float(a.overall_rating) if a.overall_rating else None
            })

        issues_q = select(ComplianceIssue).join(Audit).filter(Audit.department_id.in_(query_dept_ids))
        if employee_id:
            issues_q = issues_q.filter(ComplianceIssue.owner_id == employee_id)
        issues_res = await db.execute(issues_q)
        issues_list = []
        for i in issues_res.scalars().all():
            issues_list.append({
                "id": i.id,
                "severity": i.severity.value,
                "description": i.description,
                "status": i.status.value,
                "due_date": i.due_date.isoformat()
            })

        report_out["governance"] = {
            "audits": audits_list,
            "compliance_issues": issues_list
        }

    # 4. Gamification Module
    if not module or module.lower() == "gamification":
        chall_q = select(ChallengeParticipation).filter(
            ChallengeParticipation.employee_id.in_(
                select(Employee.id).filter(Employee.department_id.in_(query_dept_ids))
            )
        )
        if employee_id:
            chall_q = chall_q.filter(ChallengeParticipation.employee_id == employee_id)
        if challenge_id:
            chall_q = chall_q.filter(ChallengeParticipation.challenge_id == challenge_id)
        chall_res = await db.execute(chall_q.options(selectinload(ChallengeParticipation.challenge)))
        chall_list = []
        for cp in chall_res.scalars().all():
            chall_list.append({
                "id": cp.id,
                "challenge_title": cp.challenge.title,
                "xp_awarded": cp.xp_awarded,
                "approval_status": cp.approval_status.value
            })

        red_q = select(RewardRedemption).filter(
            RewardRedemption.employee_id.in_(
                select(Employee.id).filter(Employee.department_id.in_(query_dept_ids))
            )
        )
        if employee_id:
            red_q = red_q.filter(RewardRedemption.employee_id == employee_id)
        red_res = await db.execute(red_q.options(selectinload(RewardRedemption.reward)))
        red_list = []
        for rr in red_res.scalars().all():
            red_list.append({
                "id": rr.id,
                "reward_title": rr.reward.name,
                "points_spent": rr.points_spent,
                "redeemed_at": rr.redeemed_at.isoformat()
            })

        report_out["gamification"] = {
            "challenge_participations": chall_list,
            "reward_redemptions": red_list
        }

    return report_out
