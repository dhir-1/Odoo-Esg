from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.enums import RoleEnum, StatusEnum
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.permissions import get_current_user, require_role
from app.schemas.auth import UserLogin, UserRegister, Token, EmployeeRead

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).filter(Employee.email == user_in.email))
    employee = result.scalars().first()
    if not employee or not verify_password(user_in.password, employee.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if employee.status != StatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )
    
    access_token = create_access_token(
        subject=employee.email, role=employee.role.value, user_id=employee.id
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("Admin"))
):
    # Check if user with same email or employee_code already exists
    dup_result = await db.execute(
        select(Employee).filter(
            (Employee.email == user_in.email) | (Employee.employee_code == user_in.employee_code)
        )
    )
    dup = dup_result.scalars().first()
    if dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An employee with this email or employee code already exists."
        )

    # Check if department exists
    dept_result = await db.execute(select(Department).filter(Department.id == user_in.department_id))
    department = dept_result.scalars().first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with ID {user_in.department_id} does not exist."
        )

    new_employee = Employee(
        employee_code=user_in.employee_code,
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
        department_id=user_in.department_id,
        designation=user_in.designation,
        date_joined=user_in.date_joined,
        avatar_url=user_in.avatar_url,
        status=StatusEnum.ACTIVE
    )
    
    db.add(new_employee)
    
    # Increment cached employee count in department
    department.employee_count += 1
    
    await db.commit()
    await db.refresh(new_employee)
    return new_employee

@router.get("/me", response_model=EmployeeRead)
async def get_me(current_user: Employee = Depends(get_current_user)):
    return current_user

# Test Endpoints for Role Checks
@router.get("/test-employee")
async def test_employee_route(current_user: Employee = Depends(require_role("Employee", "Manager", "Admin"))):
    return {
        "message": f"Hello {current_user.full_name}, you have accessed the Employee test route!",
        "your_role": current_user.role.value
    }

@router.get("/test-manager")
async def test_manager_route(current_user: Employee = Depends(require_role("Manager", "Admin"))):
    return {
        "message": f"Hello {current_user.full_name}, you have accessed the Manager test route!",
        "your_role": current_user.role.value
    }

@router.get("/test-admin")
async def test_admin_route(current_user: Employee = Depends(require_role("Admin"))):
    return {
        "message": f"Hello {current_user.full_name}, you have accessed the Admin test route!",
        "your_role": current_user.role.value
    }
