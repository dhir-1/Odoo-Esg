from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.enums import RoleEnum, StatusEnum
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.permissions import get_current_user, require_role
from app.schemas.auth import UserLogin, UserRegister, UserSignup, Token, EmployeeRead, PasswordChangeRequest

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


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserSignup, db: AsyncSession = Depends(get_db)):
    """
    Public self-registration endpoint. Creates an Employee-role account
    and returns a JWT so the user is immediately logged in.
    """
    # Check for duplicate email
    dup_result = await db.execute(
        select(Employee).filter(Employee.email == user_in.email)
    )
    if dup_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    # Check department exists
    dept_result = await db.execute(select(Department).filter(Department.id == user_in.department_id))
    department = dept_result.scalars().first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with ID {user_in.department_id} does not exist."
        )

    import random, string
    from datetime import date as date_mod
    employee_code = "EMP-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    new_employee = Employee(
        employee_code=employee_code,
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=RoleEnum.EMPLOYEE,
        department_id=user_in.department_id,
        designation=user_in.designation or "Sustainability Advocate",
        date_joined=date_mod.today(),
        status=StatusEnum.ACTIVE,
    )
    db.add(new_employee)
    department.employee_count += 1
    await db.commit()
    await db.refresh(new_employee)

    # Return a JWT immediately so the user is logged in
    access_token = create_access_token(
        subject=new_employee.email, role=new_employee.role.value, user_id=new_employee.id
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


@router.post("/change-password")
async def change_password(
    payload: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.password_hash = get_password_hash(payload.new_password)
    await db.commit()
    return {"detail": "Password updated successfully."}
