from datetime import datetime, timedelta, timezone
import sqlite3
from typing import Optional
import urllib.request

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel


app = FastAPI(title="Mythology Service API")

# Настройки безопасности для JWT
SECRET_KEY = "super-secret-mythology-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# Инициализация схемы безопасности Bearer (будет отображаться в Swagger)
security_scheme = HTTPBearer()

# Хардкодный пользователь для нашей песочницы
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

# База данных
conn = sqlite3.connect("mythology.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        role TEXT,
        age INTEGER
    )
""")
conn.commit()


# --- СХЕМЫ PYDANTIC ---
class Character(BaseModel):
    name: str
    role: str
    age: int

class LoginRequest(BaseModel):
    username: str
    password: str

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None

class CharacterRating(BaseModel):
    character_id: int
    global_rating: float
    rank: str
    status: str


# --- ФУНКЦИЯ ВАЛИДАЦИИ ТОКЕНА (FASTAPI DEPENDENCY) ---
def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """
    Проверяет JWT токен из Headers (Authorization: Bearer <token>).
    Если токен невалидный или протух — выбрасывает 401 ошибку.
    """
    token = credentials.credentials
    try:
        # Декодируем токен, PyJWT сам проверит поле 'exp' на протухание
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или сломанный токен"
        )


# --- ЭНДПОИНТЫ АВТОРИЗАЦИИ ---
@app.post("/mythology/login", status_code=200)
def login(auth_data: LoginRequest):
    """
    Эндпоинт для генерации токена на 15 минут.
    """
    if auth_data.username != ADMIN_USERNAME or auth_data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    
    # Формируем payload токена и задаем время протухания (exp)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": auth_data.username, "exp": expire}
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": encoded_jwt, "token_type": "bearer"}


# --- ОСНОВНЫЕ ЭНДПОИНТЫ ---

@app.post("/mythology", status_code=201)
def create_character(char: Character):
    if char.age < 18:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Age must be 18 or older"
        )
    cursor.execute(
        "INSERT INTO characters (name, role, age) VALUES (?, ?, ?)", 
        (char.name, char.role, char.age)
    )
    conn.commit()
    char_id = cursor.lastrowid
    
    return {"id": char_id, "name": char.name, "role": char.role, "age": char.age}


@app.get("/mythology/{char_id}", status_code=200)
def get_character(char_id: int):
    cursor.execute("SELECT id, name, role FROM characters WHERE id = ?", (char_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"id": row[0], "name": row[1], "role": row[2]}


# Метод ЗАЩИЩЕН авторизацией: Depends(verify_jwt_token)
@app.delete("/mythology/{char_id}", status_code=204)
def delete_character(char_id: int, token_payload: dict = Depends(verify_jwt_token)):
    cursor.execute("SELECT id FROM characters WHERE id = ?", (char_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Character not found")
        
    cursor.execute("DELETE FROM characters WHERE id = ?", (char_id,))
    conn.commit()
    return None


# Метод ЗАЩИЩЕН авторизацией: Depends(verify_jwt_token)
@app.post("/mythology/{char_id}/recruit", status_code=200)
def recruit_character(char_id: int, token_payload: dict = Depends(verify_jwt_token)):
    cursor.execute("SELECT id, name, role FROM characters WHERE id = ?", (char_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return {
        "id": row[0],
        "name": row[1],
        "role": row[2],
        "status": "recruited"
    }

@app.patch("/mythology/{char_id}", status_code=200)
def update_character(char_id: int, char_data: CharacterUpdate):
    # 1. Проверяем, существует ли персонаж
    cursor.execute("SELECT name, role FROM characters WHERE id = ?", (char_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Character not found")
    
    current_name, current_role = row[0], row[1]
    
    # 2. Определяем, какие поля пришли на обновление, а какие оставить старыми
    new_name = char_data.name if char_data.name is not None else current_name
    new_role = char_data.role if char_data.role is not None else current_role
    
    # 3. Обновляем запись в базе данных
    cursor.execute(
        "UPDATE characters SET name = ?, role = ? WHERE id = ?", 
        (new_name, new_role, char_id)
    )
    conn.commit()
    
    return {"id": char_id, "name": new_name, "role": new_role}


# ======================================================================
# НЕ ДОПИЛЕННЫЙ ЭНДПОИНТ (ДЛЯ ТЕСТИРОВАНИЯ МОКОВ)
# ======================================================================
@app.get("/mythology/{char_id}/rating", status_code=200)
def get_character_rating(char_id: int):
    """
    Эндпоинт запрашивает глобальный рейтинг персонажа у внешнего микросервиса.
    Сейчас сторонний сервис лежит/недоступен, поэтому ручка будет падать с 500 ошибкой.
    """
    # Проверяем сначала, есть ли вообще такой персонаж в нашей БД
    cursor.execute("SELECT id FROM characters WHERE id = ?", (char_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Character not found")

    try:
        # Пытаемся пойти на несуществующий внешний сервис рейтингов
        # В реальной жизни тут был бы адрес партнерского API
        with urllib.request.urlopen("https://api.external-rating-service.local/v1/calc") as response:
            external_data = response.read()
            return {"status": "success", "data": external_data}
    except Exception as e:
        # Так как сервис не существует, мы ВСЕГДА будем падать сюда
        raise HTTPException(
            status_code=500, 
            detail=f"Не удалось получить ответ от внешнего сервиса рейтингов. Ошибка: {str(e)}"
        )