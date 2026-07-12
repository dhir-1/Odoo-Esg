from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.config import settings
from app.db.database import get_db
from app.models.employee import Employee
from app.models.enums import RoleEnum
from app.schemas.auth import TokenData

security_scheme = HTTPBearer()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> Employee:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=user_id)
    except JWTError:
        raise credentials_exception
        
    result = await db.execute(select(Employee).filter(Employee.id == token_data.user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    if user.status.value != "Active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return user

def require_role(*allowed_roles: str):
    async def role_dependency(current_user: Employee = Depends(get_current_user)) -> Employee:
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role"
            )
        return current_user
    return role_dependency

async def has_department_access(
    db: AsyncSession,
    employee: Employee,
    target_department_id: int
) -> bool:
    if employee.role == RoleEnum.ADMIN:
        return True
    if employee.role == RoleEnum.EMPLOYEE:
        return employee.department_id == target_department_id
        
    if employee.role == RoleEnum.MANAGER:
        if employee.department_id == target_department_id:
            return True
            
        # Recursive CTE checking if target_department_id is a child of employee.department_id
        query = text("""
            WITH RECURSIVE subdeps AS (
                SELECT id FROM departments WHERE id = :manager_dept_id
                UNION ALL
                SELECT d.id FROM departments d JOIN subdeps s ON d.parent_department_id = s.id
            ) SELECT 1 FROM subdeps WHERE id = :target_dept_id;
        """)
        result = await db.execute(query, {
            "manager_dept_id": employee.department_id,
            "target_dept_id": target_department_id
        })
        return result.fetchone() is not None
        
    return False
