import os
import random
from string import digits
from typing import List, Optional
from jinja2 import Template
from pydantic import BaseModel
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# SQLAlchemy (데이터베이스 연동 엔진)
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ─────────────────────────────────────────────
# 🔥 [자동화] templates 폴더 및 에러 방지용 HTML 파일 자동 생성
# ─────────────────────────────────────────────
if not os.path.exists("templates"):
    os.makedirs("templates")

# color.html 자동 생성
if not os.path.exists("templates/color.html"):
    with open("templates/color.html", "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head><title>Jinja Color</title></head>
        <body style="height:100vh; display:flex; justify-content:center; align-items:center; background-color:{{color}}; color:white; font-size:80px; margin:0; font-family:monospace;">
            <div>Jinja: {{color}}</div>
        </body>
        </html>
        """)

# item.html 자동 생성
if not os.path.exists("templates/item.html"):
    with open("templates/item.html", "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head><title>Read Item</title></head>
        <body style="font-family: Arial; text-align: center; background-color: #f4f6f9; padding-top: 100px;">
            <div style="max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2>🔍 아이템 상세 조회 결과</h2>
                <p style="font-size: 24px; color: #3498db; font-weight: bold;">입력된 ID: {{id}}</p>
                <p style="color: #7f8c8d;">Jinja2 외부 템플릿을 통해 안전하게 렌더링된 화면입니다.</p>
            </div>
        </body>
        </html>
        """)

# ─────────────────────────────────────────────
# 1. 데이터베이스(DB) 및 테이블 설정
# ─────────────────────────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBBook(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, nullable=False)
    category = Column(String, nullable=False)
    is_borrowed = Column(Boolean, default=False)
    borrower = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─────────────────────────────────────────────
# 2. FastAPI 데이터 검증 양식 (Pydantic 스키마)
# ─────────────────────────────────────────────
class BookCreate(BaseModel):
    id: int
    title: str
    author: str
    category: str

class BookBorrowRequest(BaseModel):
    borrower_name: str

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    category: str
    is_borrowed: bool
    borrower: Optional[str] = None

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# 3. FastAPI 웹 서버 초기화 및 실습 설정
# ─────────────────────────────────────────────
app = FastAPI(
    title="통합 디지털 도서관 시스템",
    description="조상구 교수님 기말과제 - 싱글 파일 구성 및 대출자 추적 기능 탑재",
    version="2.0.0"
)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
HEX_CHARS = digits + "abcdef"

# ─────────────────────────────────────────────
# [기능 1] 웹 홈 화면 (HTML Response)
# ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head><title>Digital Library System</title></head>
        <body style="font-family: Arial; text-align: center; background-color: #f4f6f9; padding-top: 100px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h1>📚 고급 디지털 도서관</h1>
                <p>SQLAlchemy DB 연동 및 대출자 실명 추적 시스템 가동 중</p>
                <div style="text-align: left; background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <li style="margin: 5px 0;"><b>실습 /colors:</b> <a href="/colors" target="_blank">바로가기 (인라인 방식)</a></li>
                    <li style="margin: 5px 0;"><b>실습 /jinja:</b> <a href="/jinja" target="_blank">바로가기 (외부 템플릿 자동생성 완료)</a></li>
                    <li style="margin: 5px 0;"><b>실습 /items/777:</b> <a href="/items/777" target="_blank">바로가기 (파라미터 주입 완료)</a></li>
                </div>
                <a href="/docs" style="display:inline-block; padding:12px 24px; background-color:#3498db; color:white; text-decoration:none; border-radius:5px; font-weight:bold;">대화형 API 문서(Swagger UI)로 이동</a>
            </div>
        </body>
    </html>
    """

@app.get("/colors", response_class=HTMLResponse)
def random_color():
    hex_color = "#" + "".join(random.choices(HEX_CHARS, k=6))
    html_template = "<html><body style='height:100vh; display:flex; justify-content:center; align-items:center; background-color:{{color}}; color:white; font-size:100px; margin:0;'><div>{{color}}</div></body></html>"
    return Template(html_template).render(color=hex_color)

@app.get("/jinja", response_class=HTMLResponse)
def jinja_color(request: Request):
    hex_color = "#" + "".join(random.choices(HEX_CHARS, k=6))
    return templates.TemplateResponse(request=request, name="color.html", context={"color": hex_color})

@app.get("/items/{id}", response_class=HTMLResponse)
def read_item(request: Request, id: str):
    return templates.TemplateResponse(request=request, name="item.html", context={"id": id})

# ─────────────────────────────────────────────
# 💻 [기말과제 핵심 API] 도서관 비즈니스 로직 및 엔드포인트
# ─────────────────────────────────────────────
@app.get("/api/books", response_model=List[BookResponse], tags=["도서관 시스템 (DB 연동)"])
def read_all_books(db: Session = Depends(get_db)):
    return db.query(DBBook).all()

@app.post("/api/books", response_model=BookResponse, tags=["도서관 시스템 (DB 연동)"])
def add_new_book(book: BookCreate, db: Session = Depends(get_db)):
    if db.query(DBBook).filter(DBBook.id == book.id).first():
        raise HTTPException(status_code=400, detail="이미 등록된 도서 번호입니다.")
    db_book = DBBook(id=book.id, title=book.title, author=book.author, category=book.category)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.put("/api/books/{book_id}/borrow", tags=["도서관 시스템 (DB 연동)"])
def process_borrow(book_id: int, request_data: BookBorrowRequest, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다.")
    if db_book.is_borrowed:
        raise HTTPException(status_code=400, detail=f"이미 '{db_book.borrower}'님이 빌려간 도서입니다.")
    
    db_book.is_borrowed = True
    db_book.borrower = request_data.borrower_name
    db.commit()
    return {"status": "success", "message": f"'{db_book.title}'이(가) '{request_data.borrower_name}'님께 대출되었습니다."}

@app.put("/api/books/{book_id}/return", tags=["도서관 시스템 (DB 연동)"])
def process_return(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다.")
    if not db_book.is_borrowed:
        raise HTTPException(status_code=400, detail="이미 반납 완료되어 보관 중인 도서입니다.")
    
    prev_borrower = db_book.borrower
    db_book.is_borrowed = False
    db_book.borrower = None
    db.commit()
    return {"status": "success", "message": f"'{db_book.title}' 반납 완료 (직전 대출자: {prev_borrower})"}