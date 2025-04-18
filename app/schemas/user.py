from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from app.models.user_model import GenderStatus
from typing import List

class UserBase(BaseModel):
    
    nric_FullName: str
    nric_Address: str
    nric_DateOfBirth: date= Field("YYYY-MM-DD")
    nric_Gender: GenderStatus
    nric: str
    contactNo: str
    email: str
    roleName: Optional[str] = None

class UserCreate(UserBase):
    password:str
    confirm_Password: str
    
class TempUserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    preferredName: Optional[str] = None
    contactNo: Optional[str] = None
    email: Optional[str] = None
class UserUpdate_Admin(UserUpdate):
    nric:Optional[str] = None
    nric_FullName: Optional[str] = None
    nric_Address: Optional[str] = None
    nric_DateOfBirth: Optional[date] = None
    nric_Gender: Optional[GenderStatus] = None
    lockOutReason: Optional[str] = None
    lockOutEnabled: Optional[bool]= None
    lockOutEnd : Optional[datetime]=None
    isDeleted: Optional[bool]=None
    email: Optional[str] = None
    roleName: Optional[str] = None
class UserUpdate_User(UserUpdate):
    twoFactorEnabled: Optional[bool]= None

class UpdateUsersRoleRequest(BaseModel):
    users_Id: List[str]
    role: str

class UserRead(BaseModel):
    id:str
    preferredName: Optional[str]=None
    nric_FullName: str
    nric: str
    nric_Address: str
    nric_DateOfBirth: date
    nric_Gender: GenderStatus
    roleName: Optional[str]=None
    contactNo: str
    allowNotification:bool
    profilePicture: Optional[str]=None
    email:str
    emailConfirmed:bool
    verified: bool
    isDeleted: bool
    twoFactorEnabled: bool

    @staticmethod
    def mask_nric(nric: str) -> str:
        """Mask the first 5 characters of the NRIC."""
        return "*****" + nric[5:] if nric else None

    @classmethod
    def from_orm(cls, user):
        return cls(
            id=user.id,
            preferredName=user.preferredName,
            nric_FullName=user.nric_FullName,
            nric=cls.mask_nric(user.nric),  # Masked NRIC
            nric_Address=user.nric_Address,
            nric_DateOfBirth=user.nric_DateOfBirth,
            nric_Gender=user.nric_Gender.value,
            roleName=user.roleName,
            contactNo=user.contactNo,
            email=user.email,
            allowNotification=user.allowNotification,
            profilePicture=user.profilePicture,
            status=user.status,
            emailConfirmed=user.emailConfirmed,
            verified=user.verified,
            isDeleted=user.isDeleted,
            twoFactorEnabled=user.twoFactorEnabled
        )
class AdminRead(UserRead):
    lockOutEnabled: Optional[bool]=None
    lockOutReason: Optional[str]=None
    loginTimeStamp: Optional[datetime]=None
    lastPasswordChanged: Optional[datetime]=None
    createdById: Optional[str]=None
    createdDate: Optional[datetime]=None
    modifiedById: Optional[str]=None
    modifiedDate: Optional[datetime]=None
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }

    @classmethod
    def from_orm(cls, user):
        """Extend UserRead.from_orm to include AdminRead fields."""
        base_data = super().from_orm(user)  # Get fields from UserRead
        return cls(
            **base_data.model_dump(exclude_unset=True),  # Unpack UserRead fields
            lockOutEnabled=user.lockOutEnabled,
            lockOutReason=user.lockOutReason,
            loginTimeStamp=user.loginTimeStamp,
            lastPasswordChanged=user.lastPasswordChanged,
            createdById=user.createdById,
            createdDate=user.createdDate,
            modifiedById=user.modifiedById,
            modifiedDate=user.modifiedDate
        )
class AdminSearch(BaseModel):
    id:Optional[str]=None
    preferredName: Optional[str]=None
    nric_FullName: Optional[str]=None
    nric: Optional[str]=None
    email:Optional[str]=None
    verified: Optional[bool]=None
    isDeleted:Optional[bool]=None
    twoFactorEnabled:Optional[bool]=None
    roleName: Optional[str]=None
class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    class Config:
        orm_mode = True
class UserPaginationResponse(PaginationResponse):
    users: List[AdminRead]
