from db import get_db
from psycopg2.extras import RealDictCursor


class ReviewRepository:

    @staticmethod
    def create_review(project_id, reviewer_id, target_id, dim1, dim2, dim3, comment):
        """新增一筆評價"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO reviews
                    (project_id, reviewer_id, target_id, dim1, dim2, dim3, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (project_id, reviewer_id, target_id, dim1, dim2, dim3, comment),
            )

    @staticmethod
    def has_reviewed(project_id, reviewer_id) -> bool:
        """同一個人對同一個專案是否已經評價過"""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1
                FROM reviews
                WHERE project_id = %s AND reviewer_id = %s
                LIMIT 1
                """,
                (project_id, reviewer_id),
            )
            return cur.fetchone() is not None

    @staticmethod
    def get_reviews_for_user(user_id):
        """取得某個被評價對象收到的所有評價（含評價者名稱）"""
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                """
                SELECT r.*, u.username AS reviewer_name
                FROM reviews r
                JOIN users u ON r.reviewer_id = u.id
                WHERE r.target_id = %s
                ORDER BY r.created_at DESC
                """,
                (user_id,),
            )
            return cur.fetchall()

    @staticmethod
    def get_user_avg_scores(user_id):
        """
        取得某個被評價對象的平均分數：
        - avg_dim1, avg_dim2, avg_dim3
        - overall_avg
        - review_count
        沒有評價時回傳 None
        """
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                """
                SELECT
                    AVG(dim1)::numeric(10,2) AS avg_dim1,
                    AVG(dim2)::numeric(10,2) AS avg_dim2,
                    AVG(dim3)::numeric(10,2) AS avg_dim3,
                    COUNT(*)                AS review_count
                FROM reviews
                WHERE target_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()

            if not row or row["review_count"] == 0:
                return None

            avg1 = float(row["avg_dim1"])
            avg2 = float(row["avg_dim2"])
            avg3 = float(row["avg_dim3"])
            row["overall_avg"] = round((avg1 + avg2 + avg3) / 3.0, 2)
            return row
