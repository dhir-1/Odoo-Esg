from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import all models here so that Base.metadata has them registered before migration generation
from app.models.department import Department, DepartmentScore
from app.models.employee import Employee
from app.models.category import Category
from app.models.environmental import EmissionFactor, ProductESGProfile, EnvironmentalGoal
from app.models.governance import ESGPolicy, PolicyAcknowledgement, Audit, ComplianceIssue
from app.models.gamification import Badge, Reward, Challenge, ChallengeParticipation
from app.models.carbon import CarbonTransaction
from app.models.social import CSRActivity, EmployeeParticipation, DiversityMetric, TrainingRecord
from app.models.settings import ESGConfiguration
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
