from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import all models here so that Base.metadata has them registered before migration generation
from app.models.department import Department
from app.models.employee import Employee
from app.models.category import Category
from app.models.environmental import EmissionFactor, ProductESGProfile, EnvironmentalGoal
from app.models.governance import ESGPolicy
from app.models.gamification import Badge, Reward
