from sqlalchemy import text
from sqlalchemy.orm import Session


def get_today_stats(db: Session, user_id: int) -> dict:
    """返回今日专注分钟与分心次数（按本地时间）。

    Returns:
        {"focus_minutes": int, "distraction_count": int}
    """
    focus_sql = text(
        """
        SELECT COALESCE(SUM(duration), 0) AS focus_minutes
        FROM focus_sessions
        WHERE user_id = :user_id
          AND date(started_at) = date('now', 'localtime')
        """
    )
    distraction_sql = text(
        """
        SELECT COUNT(*) AS distraction_count
        FROM distractions
        WHERE user_id = :user_id
          AND date(happened_at) = date('now', 'localtime')
        """
    )
    focus_row = db.execute(focus_sql, {"user_id": user_id}).fetchone()
    distraction_row = db.execute(distraction_sql, {"user_id": user_id}).fetchone()
    return {
        "focus_minutes": int(focus_row[0] or 0),
        "distraction_count": int(distraction_row[0] or 0),
    }


def get_week_trend(db: Session, user_id: int) -> list:
    """返回最近 7 天（含今日）每日专注时长，按日期升序，无数据补 0，共 7 条。

    Returns:
        [{"date": "YYYY-MM-DD", "focus_minutes": int}, ...]
    """
    sql = text(
        """
        WITH RECURSIVE days(day, idx) AS (
            SELECT date('now', 'localtime', '-6 days'), 0
            UNION ALL
            SELECT date(day, '+1 days'), idx + 1 FROM days WHERE idx < 6
        )
        SELECT d.day AS date,
               COALESCE(SUM(fs.duration), 0) AS focus_minutes
        FROM days d
        LEFT JOIN focus_sessions fs
            ON fs.user_id = :user_id
            AND date(fs.started_at) = d.day
        GROUP BY d.day
        ORDER BY d.day
        """
    )
    rows = db.execute(sql, {"user_id": user_id}).fetchall()
    return [
        {"date": row[0], "focus_minutes": int(row[1] or 0)}
        for row in rows
    ]


def get_hour_distraction(db: Session, user_id: int) -> list:
    """返回今日 0~23 点每小时分心次数，按小时升序，补齐 24 条。

    Returns:
        [{"hour": int, "distraction_count": int}, ...]
    """
    sql = text(
        """
        WITH RECURSIVE hours(hour, idx) AS (
            SELECT 0, 0
            UNION ALL
            SELECT hour + 1, idx + 1 FROM hours WHERE idx < 23
        )
        SELECT h.hour AS hour,
               COALESCE(COUNT(d.id), 0) AS distraction_count
        FROM hours h
        LEFT JOIN distractions d
            ON d.user_id = :user_id
            AND CAST(strftime('%H', d.happened_at) AS INTEGER) = h.hour
            AND date(d.happened_at) = date('now', 'localtime')
        GROUP BY h.hour
        ORDER BY h.hour
        """
    )
    rows = db.execute(sql, {"user_id": user_id}).fetchall()
    return [
        {"hour": int(row[0]), "distraction_count": int(row[1] or 0)}
        for row in rows
    ]
