from datetime import datetime, timedelta
from typing import Any, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import FocusSession, Task, User, get_db, init_db, SessionLocal
from services.stats import get_hour_distraction, get_today_stats, get_week_trend

SECRET_KEY = "cyber-focus-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

app = FastAPI(title="Cyber Focus API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SessionEndRequest(BaseModel):
    session_id: int
    duration: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def ok(data: Any) -> dict:
    return {"code": 0, "data": data}


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(username="admin", password=get_password_hash("admin123"))
            db.add(admin)
            db.commit()
            db.refresh(admin)
            db.add_all(
                [
                    Task(
                        title="完成 FastAPI 后端搭建",
                        description="搭建基础后端框架并对接前端",
                        user_id=admin.id,
                    ),
                    Task(
                        title="实现任务管理接口",
                        description="支持任务的增删改查",
                        user_id=admin.id,
                    ),
                ]
            )
            db.commit()
    finally:
        db.close()


@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password):
        return {"code": 1, "message": "用户名或密码错误"}
    token = create_access_token({"sub": user.username})
    return ok({"token": token})


@app.get("/api/tasks")
def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks: List[Task] = (
        db.query(Task).filter(Task.user_id == current_user.id).all()
    )
    return ok([TaskOut.model_validate(t).model_dump(mode="json") for t in tasks])


@app.post("/api/sessions/start")
def start_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = FocusSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return ok(
        {
            "session_id": session.id,
            "started_at": session.started_at.isoformat(),
        }
    )


@app.post("/api/sessions/end")
def end_session(
    req: SessionEndRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(FocusSession)
        .filter(
            FocusSession.id == req.session_id,
            FocusSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        return {"code": 1, "message": "专注记录不存在"}
    session.ended_at = datetime.utcnow()
    session.duration = req.duration
    db.commit()
    db.refresh(session)
    return ok({"session_id": session.id, "duration": session.duration})


@app.get("/api/stats")
def stats_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = get_today_stats(db, current_user.id)
    week_trend = get_week_trend(db, current_user.id)
    hour_distraction = get_hour_distraction(db, current_user.id)
    return ok(
        {
            "today": today,
            "week_trend": week_trend,
            "hour_distraction": hour_distraction,
        }
    )
