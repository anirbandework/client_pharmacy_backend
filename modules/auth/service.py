from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", truncate_error=True)

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

class AuthService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[schemas.TokenData]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("user_id")
            user_type: str = payload.get("user_type")
            shop_id: Optional[int] = payload.get("shop_id")
            email: Optional[str] = payload.get("email")
            
            if user_id is None or user_type is None:
                return None
            
            return schemas.TokenData(
                user_id=user_id,
                user_type=user_type,
                shop_id=shop_id,
                email=email
            )
        except JWTError:
            return None
    
    # Admin Authentication
    @staticmethod
    def create_admin(db: Session, admin_data: schemas.AdminCreate) -> models.Admin:
        hashed_password = AuthService.hash_password(admin_data.password)
        db_admin = models.Admin(
            phone=admin_data.phone,
            email=admin_data.email,
            password_hash=hashed_password,
            full_name=admin_data.full_name
        )
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        return db_admin
    
    @staticmethod
    def authenticate_admin(db: Session, email: str, password: str) -> Optional[models.Admin]:
        admin = db.query(models.Admin).filter(models.Admin.email == email).first()
        if not admin or not admin.is_active:
            return None
        if not AuthService.verify_password(password, admin.password_hash):
            return None
        return admin
    
    # Staff Authentication
    @staticmethod
    def authenticate_staff(db: Session, uuid: str) -> Optional[models.Staff]:
        staff = db.query(models.Staff).filter(models.Staff.uuid == uuid).first()
        if not staff or not staff.is_active:
            return None
        
        # Update last login
        staff.last_login = datetime.utcnow()
        db.commit()
        
        return staff
    
    # Shop Management
    @staticmethod
    def create_shop(db: Session, admin_id: int, shop_data: schemas.ShopCreate, admin_name: str) -> models.Shop:
        db_shop = models.Shop(
            admin_id=admin_id,
            created_by_admin=admin_name,
            **shop_data.model_dump()
        )
        db.add(db_shop)
        db.commit()
        db.refresh(db_shop)
        return db_shop
    
    @staticmethod
    def get_all_shops(db: Session):
        """Get all shops from all admins"""
        return db.query(models.Shop).all()
    
    @staticmethod
    def get_admin_shops(db: Session, admin_id: int):
        return db.query(models.Shop).filter(models.Shop.admin_id == admin_id).all()
    
    # Staff Management
    @staticmethod
    def create_staff(db: Session, shop_id: int, staff_data: schemas.StaffCreate, admin_name: str) -> models.Staff:
        db_staff = models.Staff(
            shop_id=shop_id,
            created_by_admin=admin_name,
            **staff_data.model_dump()
        )
        db.add(db_staff)
        db.commit()
        db.refresh(db_staff)
        return db_staff
    
    @staticmethod
    def get_all_staff(db: Session):
        """Get all staff from all shops"""
        return db.query(models.Staff).all()
    
    @staticmethod
    def get_shop_staff(db: Session, shop_id: int):
        return db.query(models.Staff).filter(models.Staff.shop_id == shop_id).all()
