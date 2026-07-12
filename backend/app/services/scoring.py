"""
EcoSphere ESG Scoring Engine
=============================

This module computes Environmental, Social, and Governance sub-scores for each
department over a given [period_start, period_end] date range, then combines
them into a weighted total score using weights from ESGConfiguration.

DESIGN ASSUMPTIONS (documented here because the product spec does not prescribe
exact formulas — these are reasonable defaults for a hackathon-grade ESG tool):

1. Every sub-score outputs a value in [0, 100].  Values are clamped so they
   never exceed 100 or drop below 0.
2. The total department score = E×w_e + S×w_s + G×w_g, where w_e + w_s + w_g = 1.
3. The org-wide score = Σ(dept_total × dept_employee_count) / Σ(dept_employee_count),
   i.e. employee-count-weighted average across active departments.
4. A department with zero data for a pillar gets a neutral score of 50 (not 0),
   so new departments aren't unfairly penalised.  This is the "no-data default".
"""

import math
import logging
from datetime import date, datetime, timezone
from typing import Optional, List, Dict

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department, DepartmentScore
from app.models.carbon import CarbonTransaction
from app.models.environmental import EnvironmentalGoal
from app.models.social import (
    CSRActivity, EmployeeParticipation, DiversityMetric, TrainingRecord
)
from app.models.gamification import ChallengeParticipation
from app.models.governance import (
    ESGPolicy, PolicyAcknowledgement, Audit, ComplianceIssue
)
from app.models.employee import Employee
from app.models.settings import ESGConfiguration
from app.models.enums import (
    StatusEnum,
    GoalLifecycleStatusEnum,
    GoalProgressStatusEnum,
    ParticipationApprovalStatusEnum,
    TrainingRecordStatusEnum,
    PolicyStatusEnum,
    AuditStatusEnum,
    ComplianceIssueStatusEnum,
    ComplianceIssueSeverityEnum,
    DiversityCategoryEnum,
)
from app.services.settings import get_esg_config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — neutral score used when a department has no data for a pillar
# ---------------------------------------------------------------------------
NO_DATA_SCORE = 50.0


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a numeric value to [lo, hi]."""
    return max(lo, min(hi, value))


# ═══════════════════════════════════════════════════════════════════════════
# 1.  ENVIRONMENTAL SCORE  (0-100)
# ═══════════════════════════════════════════════════════════════════════════
#
# Formula:
#   environmental_score = 0.50 × emission_efficiency + 0.50 × goal_achievement
#
# — emission_efficiency:
#     If the department has an EnvironmentalGoal with metric_type "Total Emissions"
#     whose date range overlaps the scoring period, we use its target_value as
#     the benchmark.  Otherwise, we fall back to the org-wide average emissions
#     across all departments in the period.
#
#     efficiency = max(0, 1 − (actual_co2e / benchmark)) × 100
#
#     Interpretation: if actual < benchmark, score approaches 100.
#                     if actual == benchmark, score is 0.
#                     if actual > benchmark, score is clamped to 0.
#
# — goal_achievement:
#     (count of Active goals with progress_status in {OnTrack, Achieved})
#     ÷ (total count of Active goals for this department)
#     × 100
#
#     If no goals exist, returns NO_DATA_SCORE.
# ═══════════════════════════════════════════════════════════════════════════

async def _get_department_co2e(
    db: AsyncSession, department_id: int, period_start: date, period_end: date
) -> float:
    """Sum of calculated_co2e for a department within the scoring period."""
    result = await db.execute(
        select(func.coalesce(func.sum(CarbonTransaction.calculated_co2e), 0.0))
        .filter(
            CarbonTransaction.department_id == department_id,
            CarbonTransaction.transaction_date >= period_start,
            CarbonTransaction.transaction_date <= period_end,
        )
    )
    return float(result.scalar())


async def _get_org_avg_co2e(
    db: AsyncSession, period_start: date, period_end: date
) -> float:
    """
    Average CO₂e per department across the entire org for the period.
    Used as fallback benchmark when no environmental goal exists.
    """
    # Subquery: total co2e per department
    sub = (
        select(
            CarbonTransaction.department_id,
            func.sum(CarbonTransaction.calculated_co2e).label("dept_total"),
        )
        .filter(
            CarbonTransaction.transaction_date >= period_start,
            CarbonTransaction.transaction_date <= period_end,
        )
        .group_by(CarbonTransaction.department_id)
        .subquery()
    )
    result = await db.execute(
        select(func.coalesce(func.avg(sub.c.dept_total), 0.0))
    )
    return float(result.scalar())


async def calculate_environmental_score(
    db: AsyncSession,
    department_id: int,
    period_start: date,
    period_end: date,
) -> float:
    """
    Environmental sub-score (0-100).

    Components (equal weight):
      50% — Emission Efficiency  (lower CO₂e vs benchmark = better)
      50% — Goal Achievement Rate (% of active goals OnTrack or Achieved)
    """
    # ── Emission Efficiency ──────────────────────────────────────────────
    actual_co2e = await _get_department_co2e(db, department_id, period_start, period_end)

    # Try to find a department-specific emission reduction goal
    goal_result = await db.execute(
        select(EnvironmentalGoal)
        .filter(
            EnvironmentalGoal.department_id == department_id,
            EnvironmentalGoal.metric_type == "Total Emissions",
            EnvironmentalGoal.lifecycle_status == GoalLifecycleStatusEnum.ACTIVE,
            EnvironmentalGoal.start_date <= period_end,
            EnvironmentalGoal.target_date >= period_start,
        )
        .limit(1)
    )
    goal = goal_result.scalars().first()

    if goal and float(goal.target_value) > 0:
        # Benchmark = the goal's target_value (intended max CO₂e budget)
        benchmark = float(goal.target_value)
    else:
        # Fallback: org-wide average emissions for the period
        benchmark = await _get_org_avg_co2e(db, period_start, period_end)

    if benchmark > 0:
        # Ratio of actual to benchmark; efficiency = how far under budget we are.
        # If actual == 0 → perfect score (100).
        # If actual == benchmark → score = 0.
        # If actual > benchmark → clamped to 0.
        emission_efficiency = _clamp((1.0 - (actual_co2e / benchmark)) * 100)
    elif actual_co2e == 0:
        # No benchmark AND no emissions → neutral / perfect
        emission_efficiency = 100.0
    else:
        # Emissions exist but no benchmark at all → penalise with 0
        emission_efficiency = 0.0

    # ── Goal Achievement Rate ────────────────────────────────────────────
    goals_result = await db.execute(
        select(EnvironmentalGoal)
        .filter(
            EnvironmentalGoal.department_id == department_id,
            EnvironmentalGoal.lifecycle_status == GoalLifecycleStatusEnum.ACTIVE,
        )
    )
    goals = goals_result.scalars().all()

    if goals:
        on_track_or_achieved = sum(
            1 for g in goals
            if g.progress_status in (
                GoalProgressStatusEnum.ON_TRACK,
                GoalProgressStatusEnum.ACHIEVED,
            )
        )
        goal_achievement = (on_track_or_achieved / len(goals)) * 100
    else:
        goal_achievement = NO_DATA_SCORE  # no goals → neutral

    score = 0.50 * emission_efficiency + 0.50 * goal_achievement
    return round(_clamp(score), 2)


# ═══════════════════════════════════════════════════════════════════════════
# 2.  SOCIAL SCORE  (0-100)
# ═══════════════════════════════════════════════════════════════════════════
#
# Formula:
#   social_score = 0.25 × csr_participation_rate
#                + 0.25 × challenge_completion_rate
#                + 0.25 × training_completion_rate
#                + 0.25 × diversity_evenness
#
# — csr_participation_rate:
#     (approved participations by employees in this department, in period)
#     ÷ department headcount  × 100
#     Capped at 100 (a department where everyone participated once = 100).
#
# — challenge_completion_rate:
#     (approved challenge participations by employees in this department, in period)
#     ÷ department headcount  × 100
#     Also capped at 100.
#
# — training_completion_rate:
#     (completed TrainingRecords for employees in this department, in period)
#     ÷ department headcount  × 100
#     Also capped at 100.
#
# — diversity_evenness (Shannon Equitability Index):
#     For the most recent DiversityMetric entries (category=GENDER) for this
#     department, compute Shannon entropy H and divide by H_max = ln(k)
#     where k = number of distinct labels.
#
#     Shannon entropy:  H = −Σ (p_i × ln(p_i))   where p_i = count_i / total
#     Equitability:     J = H / ln(k)             ∈ [0, 1]
#     Score:            diversity_evenness = J × 100
#
#     If only 1 label or no data → NO_DATA_SCORE (can't measure evenness).
# ═══════════════════════════════════════════════════════════════════════════

async def _get_department_headcount(
    db: AsyncSession, department_id: int
) -> int:
    """Count of active employees in the department."""
    result = await db.execute(
        select(func.count(Employee.id))
        .filter(
            Employee.department_id == department_id,
            Employee.status == StatusEnum.ACTIVE,
        )
    )
    return int(result.scalar())


async def _get_csr_participation_count(
    db: AsyncSession, department_id: int, period_start: date, period_end: date
) -> int:
    """
    Count of approved CSR participations for employees in this department
    where the associated CSR activity falls within the scoring period.
    """
    result = await db.execute(
        select(func.count(EmployeeParticipation.id))
        .join(Employee, EmployeeParticipation.employee_id == Employee.id)
        .join(CSRActivity, EmployeeParticipation.activity_id == CSRActivity.id)
        .filter(
            Employee.department_id == department_id,
            EmployeeParticipation.approval_status == ParticipationApprovalStatusEnum.APPROVED,
            CSRActivity.activity_date >= period_start,
            CSRActivity.activity_date <= period_end,
        )
    )
    return int(result.scalar())


async def _get_challenge_completion_count(
    db: AsyncSession, department_id: int, period_start: date, period_end: date
) -> int:
    """
    Count of approved challenge participations for employees in this department
    where the participation was updated within the scoring period.
    """
    result = await db.execute(
        select(func.count(ChallengeParticipation.id))
        .join(Employee, ChallengeParticipation.employee_id == Employee.id)
        .filter(
            Employee.department_id == department_id,
            ChallengeParticipation.approval_status == ParticipationApprovalStatusEnum.APPROVED,
            ChallengeParticipation.updated_at >= period_start,
            ChallengeParticipation.updated_at <= period_end,
        )
    )
    return int(result.scalar())


async def _get_training_completion_count(
    db: AsyncSession, department_id: int, period_start: date, period_end: date
) -> int:
    """
    Count of completed training records for employees in this department
    where the completion date falls within the scoring period.
    """
    result = await db.execute(
        select(func.count(TrainingRecord.id))
        .join(Employee, TrainingRecord.employee_id == Employee.id)
        .filter(
            Employee.department_id == department_id,
            TrainingRecord.status == TrainingRecordStatusEnum.COMPLETED,
            TrainingRecord.completed_date >= period_start,
            TrainingRecord.completed_date <= period_end,
        )
    )
    return int(result.scalar())


async def _compute_diversity_evenness(
    db: AsyncSession, department_id: int
) -> float:
    """
    Shannon Equitability Index (J) for the GENDER diversity category.

    The Shannon entropy measures how evenly individuals are distributed
    across labels (e.g., "Male", "Female", "Non-binary").

    Formula:
      H     = −Σ(p_i × ln(p_i))      (Shannon entropy)
      H_max = ln(k)                    (maximum possible entropy for k labels)
      J     = H / H_max               (equitability, 0 = perfectly uneven, 1 = perfectly even)

    Returns J × 100 as a 0-100 score.

    Edge cases:
      - 0 or 1 label → NO_DATA_SCORE (evenness is undefined)
      - All counts are 0 → NO_DATA_SCORE
    """
    # Fetch the most recent period's gender diversity data for this department
    # (DiversityMetric.period is a string like "2026-Q3" — we order DESC to
    # pick the latest period alphabetically, which works for YYYY-QN format)
    result = await db.execute(
        select(DiversityMetric.label, DiversityMetric.count)
        .filter(
            DiversityMetric.department_id == department_id,
            DiversityMetric.category == DiversityCategoryEnum.GENDER,
        )
        .order_by(DiversityMetric.period.desc())
    )
    rows = result.all()

    if not rows:
        return NO_DATA_SCORE

    # Group by the latest period only
    latest_period = None
    counts: List[int] = []
    for label, count in rows:
        if latest_period is None:
            # Determine the latest period from the first row (ordered DESC)
            # We need to re-query filtering by period, but since rows are
            # already ordered, we can just take rows sharing the same period.
            latest_period_result = await db.execute(
                select(DiversityMetric.period)
                .filter(
                    DiversityMetric.department_id == department_id,
                    DiversityMetric.category == DiversityCategoryEnum.GENDER,
                )
                .order_by(DiversityMetric.period.desc())
                .limit(1)
            )
            latest_period = latest_period_result.scalar()
            break

    if latest_period is None:
        return NO_DATA_SCORE

    period_result = await db.execute(
        select(DiversityMetric.label, DiversityMetric.count)
        .filter(
            DiversityMetric.department_id == department_id,
            DiversityMetric.category == DiversityCategoryEnum.GENDER,
            DiversityMetric.period == latest_period,
        )
    )
    period_rows = period_result.all()
    counts = [int(c) for _, c in period_rows if int(c) > 0]

    k = len(counts)
    if k <= 1:
        return NO_DATA_SCORE  # can't measure evenness with 0 or 1 group

    total = sum(counts)
    if total == 0:
        return NO_DATA_SCORE

    # Shannon entropy: H = −Σ(p_i × ln(p_i))
    H = 0.0
    for c in counts:
        p = c / total
        if p > 0:
            H -= p * math.log(p)

    H_max = math.log(k)  # ln(k)

    if H_max == 0:
        return NO_DATA_SCORE

    J = H / H_max  # equitability ∈ [0, 1]
    return round(J * 100, 2)


async def calculate_social_score(
    db: AsyncSession,
    department_id: int,
    period_start: date,
    period_end: date,
) -> float:
    """
    Social sub-score (0-100).

    Components (equal weight, 25% each):
      25% — CSR Participation Rate     (approved participations / headcount × 100, cap 100)
      25% — Challenge Completion Rate  (approved completions / headcount × 100, cap 100)
      25% — Training Completion Rate   (completed trainings / headcount × 100, cap 100)
      25% — Diversity Evenness         (Shannon equitability J × 100)
    """
    headcount = await _get_department_headcount(db, department_id)

    if headcount == 0:
        # Department has no active employees — return neutral
        return NO_DATA_SCORE

    # CSR participation rate
    csr_count = await _get_csr_participation_count(db, department_id, period_start, period_end)
    csr_rate = _clamp((csr_count / headcount) * 100)

    # Challenge completion rate
    challenge_count = await _get_challenge_completion_count(db, department_id, period_start, period_end)
    challenge_rate = _clamp((challenge_count / headcount) * 100)

    # Training completion rate
    training_count = await _get_training_completion_count(db, department_id, period_start, period_end)
    training_rate = _clamp((training_count / headcount) * 100)

    # Diversity evenness (Shannon equitability)
    diversity = await _compute_diversity_evenness(db, department_id)

    score = 0.25 * csr_rate + 0.25 * challenge_rate + 0.25 * training_rate + 0.25 * diversity
    return round(_clamp(score), 2)


# ═══════════════════════════════════════════════════════════════════════════
# 3.  GOVERNANCE SCORE  (0-100)
# ═══════════════════════════════════════════════════════════════════════════
#
# Formula:
#   governance_score = 0.40 × policy_ack_rate
#                    + 0.30 × audit_completion_rate
#                    + 0.30 × compliance_health
#
# — policy_ack_rate:
#     For every ACTIVE ESGPolicy requiring acknowledgement:
#       count employees in dept who acknowledged (any version) ÷ headcount
#     Then average across all such policies. × 100.
#     If no policies require acknowledgement → NO_DATA_SCORE.
#
# — audit_completion_rate:
#     (audits for this department with status=Completed or Closed, in period)
#     ÷ (total audits for this department, in period) × 100
#     If no audits → NO_DATA_SCORE.
#
# — compliance_health:
#     Start at 100 and subtract a penalty for every OPEN or IN_PROGRESS
#     ComplianceIssue linked to an audit in this department.
#
#     Severity weights:
#       LOW = 5,  MEDIUM = 10,  HIGH = 20,  CRITICAL = 40
#
#     Overdue multiplier:  if due_date < today → penalty × 1.5
#
#     compliance_health = max(0, 100 − Σ(penalty_i))
#     Clamped to [0, 100].
# ═══════════════════════════════════════════════════════════════════════════

SEVERITY_PENALTY: Dict[ComplianceIssueSeverityEnum, float] = {
    ComplianceIssueSeverityEnum.LOW: 5.0,
    ComplianceIssueSeverityEnum.MEDIUM: 10.0,
    ComplianceIssueSeverityEnum.HIGH: 20.0,
    ComplianceIssueSeverityEnum.CRITICAL: 40.0,
}
OVERDUE_MULTIPLIER = 1.5


async def _compute_policy_ack_rate(
    db: AsyncSession, department_id: int
) -> float:
    """
    Average acknowledgement rate across all active policies that require
    acknowledgement.  For each such policy, rate = (# employees in dept who
    acknowledged) / headcount.
    """
    headcount = await _get_department_headcount(db, department_id)
    if headcount == 0:
        return NO_DATA_SCORE

    # All active policies requiring acknowledgement
    policies_result = await db.execute(
        select(ESGPolicy.id)
        .filter(
            ESGPolicy.status == PolicyStatusEnum.ACTIVE,
            ESGPolicy.requires_acknowledgement == True,
        )
    )
    policy_ids = [row[0] for row in policies_result.all()]

    if not policy_ids:
        return NO_DATA_SCORE  # nothing to acknowledge

    # For each policy, count distinct employees in dept who acknowledged
    rates = []
    for pid in policy_ids:
        ack_count_result = await db.execute(
            select(func.count(func.distinct(PolicyAcknowledgement.employee_id)))
            .join(Employee, PolicyAcknowledgement.employee_id == Employee.id)
            .filter(
                PolicyAcknowledgement.policy_id == pid,
                Employee.department_id == department_id,
                Employee.status == StatusEnum.ACTIVE,
            )
        )
        ack_count = int(ack_count_result.scalar())
        rates.append(ack_count / headcount)

    avg_rate = sum(rates) / len(rates)
    return round(_clamp(avg_rate * 100), 2)


async def _compute_audit_completion_rate(
    db: AsyncSession, department_id: int, period_start: date, period_end: date
) -> float:
    """
    Fraction of audits for this department (within the period) that reached
    Completed or Closed status.
    """
    total_result = await db.execute(
        select(func.count(Audit.id))
        .filter(
            Audit.department_id == department_id,
            Audit.audit_date >= period_start,
            Audit.audit_date <= period_end,
        )
    )
    total = int(total_result.scalar())

    if total == 0:
        return NO_DATA_SCORE  # no audits → neutral

    completed_result = await db.execute(
        select(func.count(Audit.id))
        .filter(
            Audit.department_id == department_id,
            Audit.audit_date >= period_start,
            Audit.audit_date <= period_end,
            Audit.status.in_([AuditStatusEnum.COMPLETED, AuditStatusEnum.CLOSED]),
        )
    )
    completed = int(completed_result.scalar())

    return round(_clamp((completed / total) * 100), 2)


async def _compute_compliance_health(
    db: AsyncSession, department_id: int
) -> float:
    """
    Start at 100 and subtract severity-weighted penalties for open/in-progress
    compliance issues.  Overdue issues (due_date < today) are penalised 1.5×.

    Severity penalty weights:
      LOW=5, MEDIUM=10, HIGH=20, CRITICAL=40

    compliance_health = clamp(100 − Σ penalties, 0, 100)
    """
    today = date.today()

    # Get open/in-progress compliance issues for audits in this department
    issues_result = await db.execute(
        select(ComplianceIssue.severity, ComplianceIssue.due_date)
        .join(Audit, ComplianceIssue.audit_id == Audit.id)
        .filter(
            Audit.department_id == department_id,
            ComplianceIssue.status.in_([
                ComplianceIssueStatusEnum.OPEN,
                ComplianceIssueStatusEnum.IN_PROGRESS,
            ]),
        )
    )
    issues = issues_result.all()

    if not issues:
        return 100.0  # no open issues → perfect governance health

    total_penalty = 0.0
    for severity, due_date in issues:
        base_penalty = SEVERITY_PENALTY.get(severity, 10.0)
        if due_date < today:
            # Overdue issues are penalised more heavily
            base_penalty *= OVERDUE_MULTIPLIER
        total_penalty += base_penalty

    return round(_clamp(100.0 - total_penalty), 2)


async def calculate_governance_score(
    db: AsyncSession,
    department_id: int,
    period_start: date,
    period_end: date,
) -> float:
    """
    Governance sub-score (0-100).

    Components:
      40% — Policy Acknowledgement Rate  (avg ack rate across active policies)
      30% — Audit Completion Rate         (completed+closed / total in period)
      30% — Compliance Health             (100 minus severity-weighted open issue penalties)
    """
    policy_rate = await _compute_policy_ack_rate(db, department_id)
    audit_rate = await _compute_audit_completion_rate(db, department_id, period_start, period_end)
    compliance = await _compute_compliance_health(db, department_id)

    score = 0.40 * policy_rate + 0.30 * audit_rate + 0.30 * compliance
    return round(_clamp(score), 2)


# ═══════════════════════════════════════════════════════════════════════════
# 4.  DEPARTMENT TOTAL SCORE
# ═══════════════════════════════════════════════════════════════════════════

async def calculate_department_score(
    db: AsyncSession,
    department_id: int,
    period_start: date,
    period_end: date,
) -> DepartmentScore:
    """
    Computes E, S, G sub-scores, combines them using ESGConfiguration weights,
    and persists a new DepartmentScore row.

    total = E × environmental_weight + S × social_weight + G × governance_weight

    Returns the persisted DepartmentScore ORM object.
    """
    config = await get_esg_config(db)

    env_score = await calculate_environmental_score(db, department_id, period_start, period_end)
    soc_score = await calculate_social_score(db, department_id, period_start, period_end)
    gov_score = await calculate_governance_score(db, department_id, period_start, period_end)

    total = round(
        env_score * float(config.environmental_weight)
        + soc_score * float(config.social_weight)
        + gov_score * float(config.governance_weight),
        2,
    )

    dept_score = DepartmentScore(
        department_id=department_id,
        period_start=period_start,
        period_end=period_end,
        environmental_score=env_score,
        social_score=soc_score,
        governance_score=gov_score,
        total_score=total,
        calculated_at=datetime.now(timezone.utc),
    )
    db.add(dept_score)
    await db.commit()
    await db.refresh(dept_score)

    # Broadcast score recalculation to department
    from app.websockets.manager import ws_manager
    try:
        await ws_manager.broadcast_to_department(
            department_id=department_id,
            payload={
                "event": "score_calculated",
                "data": {
                    "department_id": department_id,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "environmental_score": float(env_score),
                    "social_score": float(soc_score),
                    "governance_score": float(gov_score),
                    "total_score": float(total),
                    "calculated_at": dept_score.calculated_at.isoformat()
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to broadcast score recalculation: {e}")

    logger.info(
        "Dept %d score [%s–%s]: E=%.2f S=%.2f G=%.2f T=%.2f",
        department_id, period_start, period_end,
        env_score, soc_score, gov_score, total,
    )
    return dept_score


# ═══════════════════════════════════════════════════════════════════════════
# 5.  ORG-WIDE SCORE
# ═══════════════════════════════════════════════════════════════════════════

async def calculate_org_score(
    db: AsyncSession,
    period_start: date,
    period_end: date,
) -> dict:
    """
    Org-level ESG summary: employee-count-weighted average of all department
    scores for the given period.

    org_total = Σ(dept_total × employee_count) / Σ(employee_count)
    (Same formula applied separately for E, S, G sub-scores.)

    Returns a dict matching OrgScoreSummary schema shape.
    """
    # Fetch all department scores for the given period
    scores_result = await db.execute(
        select(DepartmentScore)
        .filter(
            DepartmentScore.period_start == period_start,
            DepartmentScore.period_end == period_end,
        )
    )
    scores = scores_result.scalars().all()

    if not scores:
        return {
            "period_start": period_start,
            "period_end": period_end,
            "total_score": 0.0,
            "environmental_avg": 0.0,
            "social_avg": 0.0,
            "governance_avg": 0.0,
            "department_count": 0,
            "department_scores": [],
        }

    # Fetch employee counts for weighting
    dept_ids = [s.department_id for s in scores]
    counts_result = await db.execute(
        select(Department.id, Department.employee_count)
        .filter(Department.id.in_(dept_ids))
    )
    headcounts = {row[0]: max(row[1], 1) for row in counts_result.all()}  # min 1 to avoid div-by-zero

    total_weight = sum(headcounts.get(s.department_id, 1) for s in scores)

    weighted_total = sum(
        float(s.total_score) * headcounts.get(s.department_id, 1) for s in scores
    )
    weighted_env = sum(
        float(s.environmental_score) * headcounts.get(s.department_id, 1) for s in scores
    )
    weighted_soc = sum(
        float(s.social_score) * headcounts.get(s.department_id, 1) for s in scores
    )
    weighted_gov = sum(
        float(s.governance_score) * headcounts.get(s.department_id, 1) for s in scores
    )

    return {
        "period_start": period_start,
        "period_end": period_end,
        "total_score": round(weighted_total / total_weight, 2),
        "environmental_avg": round(weighted_env / total_weight, 2),
        "social_avg": round(weighted_soc / total_weight, 2),
        "governance_avg": round(weighted_gov / total_weight, 2),
        "department_count": len(scores),
        "department_scores": scores,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 6.  BULK RECALCULATION  (used by the scheduler)
# ═══════════════════════════════════════════════════════════════════════════

async def recalculate_all_departments(
    db: AsyncSession,
    period_start: date,
    period_end: date,
) -> List[DepartmentScore]:
    """
    Recalculates ESG scores for every active department.
    Called by the APScheduler daily cron job and available for manual triggers.
    """
    depts_result = await db.execute(
        select(Department.id)
        .filter(Department.status == StatusEnum.ACTIVE)
    )
    dept_ids = [row[0] for row in depts_result.all()]

    results = []
    for dept_id in dept_ids:
        score = await calculate_department_score(db, dept_id, period_start, period_end)
        results.append(score)

    logger.info(
        "Recalculated ESG scores for %d departments [%s–%s]",
        len(results), period_start, period_end,
    )
    return results
