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
