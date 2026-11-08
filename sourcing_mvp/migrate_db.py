"""
数据库迁移脚本 - 添加 is_test_data 字段到现有数据库
"""
import sqlite3
import os


def migrate_database(db_path: str):
    """迁移现有数据库"""
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}, skipping migration")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查 is_test_data 字段是否存在
        cursor.execute("PRAGMA table_info(supplier)")
        columns = [col[1] for col in cursor.fetchall()]

        if "is_test_data" not in columns:
            print("Adding is_test_data column to supplier table...")
            cursor.execute("ALTER TABLE supplier ADD COLUMN is_test_data INTEGER DEFAULT 0")
            conn.commit()
            print("✅ Migration completed")
        else:
            print("✅ is_test_data column already exists")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    # 默认数据库路径
    db_path = os.environ.get("DATABASE_PATH", "sourcing_mvp.db")
    migrate_database(db_path)
