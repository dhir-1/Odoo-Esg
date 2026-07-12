from pydantic import BaseModel, Field

class LeaderboardEntryRead(BaseModel):
    rank: int = Field(..., description="Calculated rank")
    entry_type: str = Field(..., description="Type of rank entry (e.g. 'employee' or 'department')")
    id: int = Field(..., description="ID of the employee or department")
    name: str = Field(..., description="Name of the employee or department")
    value: int = Field(..., description="Aggregate score value (XP points or point balance)")
