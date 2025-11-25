from typing import Optional
from psycopg2.extras import RealDictCursor
from db import get_db

class UserRepository:
    """使用者資料存取層"""
    
    @staticmethod
    def get_by_username(username: str) -> Optional[dict]:
        """根據用戶名取得用戶"""
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cur.fetchone()
    
    @staticmethod
    def create(username: str, password: str, role: str) -> int:
        """創建新用戶"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (username, password, role, created_at)
                VALUES (%s, %s, %s, NOW())
                RETURNING id
            """, (username, password, role))
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id