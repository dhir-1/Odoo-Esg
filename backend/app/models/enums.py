import enum

class StatusEnum(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

class RoleEnum(str, enum.Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    EMPLOYEE = "Employee"

class CategoryTypeEnum(str, enum.Enum):
    CSR_ACTIVITY = "CSR_ACTIVITY"
    CHALLENGE = "CHALLENGE"

class EmissionActivityTypeEnum(str, enum.Enum):
    PURCHASE = "Purchase"
    MANUFACTURING = "Manufacturing"
    EXPENSE = "Expense"
    FLEET = "Fleet"
    OTHER = "Other"

class GoalLifecycleStatusEnum(str, enum.Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class GoalProgressStatusEnum(str, enum.Enum):
    ON_TRACK = "OnTrack"
    AT_RISK = "AtRisk"
    ACHIEVED = "Achieved"
    MISSED = "Missed"

class PolicyStatusEnum(str, enum.Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    ARCHIVED = "Archived"

class ESGPolicyCategoryEnum(str, enum.Enum):
    ENVIRONMENTAL = "Environmental"
    SOCIAL = "Social"
    GOVERNANCE = "Governance"

class CarbonSourceModuleEnum(str, enum.Enum):
    PURCHASE = "Purchase"
    MANUFACTURING = "Manufacturing"
    EXPENSE = "Expense"
    FLEET = "Fleet"
    MANUAL = "Manual"

class CSRActivityStatusEnum(str, enum.Enum):
    PLANNED = "Planned"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class ParticipationApprovalStatusEnum(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class ChallengeDifficultyEnum(str, enum.Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class ChallengeStatusEnum(str, enum.Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    UNDER_REVIEW = "UnderReview"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"

class AuditStatusEnum(str, enum.Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    CLOSED = "Closed"

class ComplianceIssueSeverityEnum(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class ComplianceIssueStatusEnum(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "InProgress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class DiversityCategoryEnum(str, enum.Enum):
    GENDER = "Gender"
    AGE_GROUP = "AgeGroup"
    OTHER = "Other"

class TrainingRecordStatusEnum(str, enum.Enum):
    ENROLLED = "Enrolled"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"

class NotificationTypeEnum(str, enum.Enum):
    COMPLIANCE_ISSUE = "compliance_issue"
    APPROVAL_DECISION = "approval_decision"
    POLICY_REMINDER = "policy_reminder"
    BADGE_UNLOCK = "badge_unlock"

class ActivityLogEventTypeEnum(str, enum.Enum):
    CHALLENGE_COMPLETED = "ChallengeCompleted"
    CSR_COMPLETED = "CSRCompleted"
    COMPLIANCE_ISSUE_RAISED = "ComplianceIssueRaised"
    CARBON_TRANSACTION_LOGGED = "CarbonTransactionLogged"
    POLICY_ACKNOWLEDGED = "PolicyAcknowledged"
    BADGE_AWARDED = "BadgeAwarded"
    GOAL_ACHIEVED = "GoalAchieved"
    AUDIT_COMPLETED = "AuditCompleted"
