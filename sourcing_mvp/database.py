"""
Database - SQLite for MVP

极简数据库设计，够用就好
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
import json


class Database:
    """SQLite 数据库"""

    def __init__(self, db_path: str = "sourcing_mvp.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """初始化表结构"""
        with self.get_connection() as conn:
            # Sourcing Cases
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sourcing_case (
                    id TEXT PRIMARY KEY,
                    buyer_id TEXT NOT NULL,
                    initial_query TEXT NOT NULL,
                    product_description TEXT,
                    requirements TEXT,  -- JSON
                    status TEXT NOT NULL,
                    discovered_suppliers TEXT,  -- JSON array
                    message_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Suppliers
            conn.execute("""
                CREATE TABLE IF NOT EXISTS supplier (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    contact_email TEXT NOT NULL,
                    contact_wechat TEXT,
                    contact_phone TEXT,
                    contact_person TEXT,
                    categories TEXT,  -- JSON array
                    capabilities TEXT,  -- JSON
                    verification TEXT,  -- JSON
                    response_rate REAL DEFAULT 0,
                    avg_response_time_hours REAL,
                    notes TEXT,
                    active INTEGER DEFAULT 1
                )
            """)

            # Inquiries
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inquiry (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    supplier_id TEXT NOT NULL,
                    email_subject TEXT NOT NULL,
                    email_body TEXT NOT NULL,
                    language TEXT DEFAULT 'en',
                    status TEXT NOT NULL,
                    sent_at TEXT,
                    response TEXT,  -- JSON
                    follow_up_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES sourcing_case(id),
                    FOREIGN KEY (supplier_id) REFERENCES supplier(id)
                )
            """)

            # Messages
            conn.execute("""
                CREATE TABLE IF NOT EXISTS message (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,  -- JSON
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES sourcing_case(id)
                )
            """)

            # 索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_case_buyer ON sourcing_case(buyer_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inquiry_case ON inquiry(case_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inquiry_supplier ON inquiry(supplier_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_message_case ON message(case_id)")

            conn.commit()

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ========================================================================
    # Sourcing Case CRUD
    # ========================================================================

    def create_case(self, case: dict) -> str:
        """创建采购案例"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO sourcing_case (
                    id, buyer_id, initial_query, product_description,
                    requirements, status, discovered_suppliers,
                    message_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case["id"],
                case["buyer_id"],
                case["initial_query"],
                case.get("product_description"),
                json.dumps(case.get("requirements", {})),
                case["status"],
                json.dumps(case.get("discovered_suppliers", [])),
                case.get("message_count", 0),
                case["created_at"],
                case["updated_at"],
            ))
            conn.commit()
        return case["id"]

    def get_case(self, case_id: str) -> Optional[dict]:
        """获取案例"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sourcing_case WHERE id = ?",
                (case_id,)
            ).fetchone()
            if row:
                return {
                    "id": row["id"],
                    "buyer_id": row["buyer_id"],
                    "initial_query": row["initial_query"],
                    "product_description": row["product_description"],
                    "requirements": json.loads(row["requirements"]),
                    "status": row["status"],
                    "discovered_suppliers": json.loads(row["discovered_suppliers"]),
                    "message_count": row["message_count"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
        return None

    def update_case(self, case_id: str, updates: dict):
        """更新案例"""
        updates["updated_at"] = datetime.now().isoformat()

        set_clauses = []
        values = []
        for key, value in updates.items():
            if key in ["requirements", "discovered_suppliers"]:
                value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            values.append(value)

        values.append(case_id)

        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE sourcing_case SET {', '.join(set_clauses)} WHERE id = ?",
                values
            )
            conn.commit()

    # ========================================================================
    # Supplier CRUD
    # ========================================================================

    def create_supplier(self, supplier: dict) -> str:
        """创建供应商"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO supplier (
                    id, name, contact_email, contact_wechat, contact_phone,
                    contact_person, categories, capabilities, verification,
                    response_rate, avg_response_time_hours, notes, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                supplier["id"],
                supplier["name"],
                supplier["contact"]["email"],
                supplier["contact"].get("wechat"),
                supplier["contact"].get("phone"),
                supplier["contact"].get("contact_person"),
                json.dumps(supplier.get("categories", [])),
                json.dumps(supplier.get("capabilities", {})),
                json.dumps(supplier.get("verification", {})),
                supplier.get("response_rate", 0),
                supplier.get("avg_response_time_hours"),
                supplier.get("notes"),
                1 if supplier.get("active", True) else 0,
            ))
            conn.commit()
        return supplier["id"]

    def get_supplier(self, supplier_id: str) -> Optional[dict]:
        """获取供应商"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM supplier WHERE id = ?",
                (supplier_id,)
            ).fetchone()
            if row:
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "contact": {
                        "email": row["contact_email"],
                        "wechat": row["contact_wechat"],
                        "phone": row["contact_phone"],
                        "contact_person": row["contact_person"],
                    },
                    "categories": json.loads(row["categories"]),
                    "capabilities": json.loads(row["capabilities"]),
                    "verification": json.loads(row["verification"]),
                    "response_rate": row["response_rate"],
                    "avg_response_time_hours": row["avg_response_time_hours"],
                    "notes": row["notes"],
                    "active": bool(row["active"]),
                }
        return None

    def search_suppliers(self, categories: list[str] = None, active_only: bool = True) -> list[dict]:
        """搜索供应商"""
        query = "SELECT * FROM supplier WHERE 1=1"
        params = []

        if active_only:
            query += " AND active = 1"

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            suppliers = []
            for row in rows:
                supplier = {
                    "id": row["id"],
                    "name": row["name"],
                    "contact": {
                        "email": row["contact_email"],
                        "wechat": row["contact_wechat"],
                        "phone": row["contact_phone"],
                        "contact_person": row["contact_person"],
                    },
                    "categories": json.loads(row["categories"]),
                    "capabilities": json.loads(row["capabilities"]),
                    "verification": json.loads(row["verification"]),
                    "response_rate": row["response_rate"],
                    "avg_response_time_hours": row["avg_response_time_hours"],
                    "notes": row["notes"],
                    "active": bool(row["active"]),
                }

                # 过滤品类
                if categories:
                    if any(cat in supplier["categories"] for cat in categories):
                        suppliers.append(supplier)
                else:
                    suppliers.append(supplier)

            return suppliers

    # ========================================================================
    # Inquiry CRUD
    # ========================================================================

    def create_inquiry(self, inquiry: dict) -> str:
        """创建询价"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO inquiry (
                    id, case_id, supplier_id, email_subject, email_body,
                    language, status, sent_at, response, follow_up_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inquiry["id"],
                inquiry["case_id"],
                inquiry["supplier_id"],
                inquiry["email_subject"],
                inquiry["email_body"],
                inquiry.get("language", "en"),
                inquiry["status"],
                inquiry.get("sent_at"),
                json.dumps(inquiry.get("response")) if inquiry.get("response") else None,
                inquiry.get("follow_up_at"),
                inquiry["created_at"],
            ))
            conn.commit()
        return inquiry["id"]

    def get_inquiry(self, inquiry_id: str) -> Optional[dict]:
        """获取询价"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM inquiry WHERE id = ?",
                (inquiry_id,)
            ).fetchone()
            if row:
                return {
                    "id": row["id"],
                    "case_id": row["case_id"],
                    "supplier_id": row["supplier_id"],
                    "email_subject": row["email_subject"],
                    "email_body": row["email_body"],
                    "language": row["language"],
                    "status": row["status"],
                    "sent_at": row["sent_at"],
                    "response": json.loads(row["response"]) if row["response"] else None,
                    "follow_up_at": row["follow_up_at"],
                    "created_at": row["created_at"],
                }
        return None

    def update_inquiry(self, inquiry_id: str, updates: dict):
        """更新询价"""
        set_clauses = []
        values = []
        for key, value in updates.items():
            if key == "response" and value:
                value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            values.append(value)

        values.append(inquiry_id)

        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE inquiry SET {', '.join(set_clauses)} WHERE id = ?",
                values
            )
            conn.commit()

    def get_case_inquiries(self, case_id: str) -> list[dict]:
        """获取案例的所有询价"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM inquiry WHERE case_id = ? ORDER BY created_at DESC",
                (case_id,)
            ).fetchall()
            inquiries = []
            for row in rows:
                inquiries.append({
                    "id": row["id"],
                    "case_id": row["case_id"],
                    "supplier_id": row["supplier_id"],
                    "email_subject": row["email_subject"],
                    "email_body": row["email_body"],
                    "language": row["language"],
                    "status": row["status"],
                    "sent_at": row["sent_at"],
                    "response": json.loads(row["response"]) if row["response"] else None,
                    "follow_up_at": row["follow_up_at"],
                    "created_at": row["created_at"],
                })
            return inquiries

    # ========================================================================
    # Message CRUD
    # ========================================================================

    def create_message(self, message: dict) -> str:
        """创建消息"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO message (
                    id, case_id, role, content, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message["id"],
                message["case_id"],
                message["role"],
                message["content"],
                json.dumps(message.get("metadata", {})),
                message["created_at"],
            ))
            conn.commit()
        return message["id"]

    def get_case_messages(self, case_id: str) -> list[dict]:
        """获取案例的所有消息"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM message WHERE case_id = ? ORDER BY created_at ASC",
                (case_id,)
            ).fetchall()
            messages = []
            for row in rows:
                messages.append({
                    "id": row["id"],
                    "case_id": row["case_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]),
                    "created_at": row["created_at"],
                })
            return messages


# 全局数据库实例
db = Database()
