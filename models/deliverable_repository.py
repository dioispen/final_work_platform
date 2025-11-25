from typing import Optional
from psycopg2.extras import RealDictCursor
from db import get_db

class DeliverableRepository:
    """結案檔案資料存取層"""
    
    @staticmethod
    def get_by_project_id(project_id: int) -> Optional[dict]:
        """取得專案的結案檔案"""
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM deliverables WHERE project_id = %s", (project_id,))
            return cur.fetchone()
    
    @staticmethod
    def create(project_id: int, file_name: str, file_path: str, message: str) -> int:
        """建立結案檔案"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO deliverables (project_id, file_name, file_path, message, uploaded_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
            """, (project_id, file_name, file_path, message))
            deliverable_id = cur.fetchone()[0]
            conn.commit()
            return deliverable_id
        
    @staticmethod
    def delete_by_project_id(project_id: int) -> bool:
        """刪除專案的結案檔案"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM deliverables WHERE project_id = %s", (project_id,))
            changed = cur.rowcount > 0
            conn.commit()
            return changed