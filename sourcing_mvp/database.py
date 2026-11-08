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
        """初始化数据库表"""
        with self.get_connection() as conn:
            # 开启外键约束
            conn.execute("PRAGMA foreign_keys = ON")
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
                    active INTEGER DEFAULT 1,
                    is_test_data INTEGER DEFAULT 0
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

            # Quote Requests
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quote_request (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    supplier_id TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    product_description TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    specifications TEXT,  -- JSON
                    quote_deadline TEXT NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    status TEXT NOT NULL,
                    buyer_id TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES sourcing_case(id),
                    FOREIGN KEY (supplier_id) REFERENCES supplier(id)
                )
            """)

            # Quote Tokens
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quote_token (
                    id TEXT PRIMARY KEY,
                    token_hash TEXT UNIQUE NOT NULL,
                    quote_request_id TEXT NOT NULL,
                    supplier_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    is_revoked INTEGER DEFAULT 0,
                    revoked_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (quote_request_id) REFERENCES quote_request(id)
                )
            """)

            # Supplier Quotes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS supplier_quote (
                    id TEXT PRIMARY KEY,
                    quote_request_id TEXT NOT NULL,
                    supplier_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    unit_price TEXT NOT NULL,  -- Decimal as string for precision
                    currency TEXT NOT NULL,
                    moq INTEGER NOT NULL,
                    lead_time_days INTEGER NOT NULL,
                    trade_term TEXT NOT NULL,
                    quote_valid_until TEXT NOT NULL,
                    payment_terms TEXT,
                    specification_notes TEXT,
                    status TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    submitted_via TEXT DEFAULT 'quote_portal',
                    raw_data TEXT,  -- JSON
                    FOREIGN KEY (quote_request_id) REFERENCES quote_request(id)
                )
            """)

            # Quote Version History
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quote_version (
                    id TEXT PRIMARY KEY,
                    quote_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    snapshot TEXT NOT NULL,  -- JSON
                    changed_fields TEXT,  -- JSON array
                    change_reason TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (quote_id) REFERENCES supplier_quote(id)
                )
            """)

            # 索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_case_buyer ON sourcing_case(buyer_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inquiry_case ON inquiry(case_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inquiry_supplier ON inquiry(supplier_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_message_case ON message(case_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_quote_request_case ON quote_request(case_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_quote_request_supplier ON quote_request(supplier_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_quote_token_hash ON quote_token(token_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_supplier_quote_request ON supplier_quote(quote_request_id)")

            conn.commit()

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # 每次连接都开启外键约束
        conn.execute("PRAGMA foreign_keys = ON")
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
                    response_rate, avg_response_time_hours, notes, active, is_test_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                1 if supplier.get("is_test_data", False) else 0,
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
                    "is_test_data": bool(row["is_test_data"] if "is_test_data" in row.keys() else 0),
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
                    "is_test_data": bool(row["is_test_data"] if "is_test_data" in row.keys() else 0),
                }

                # 过滤品类
                if categories:
                    if any(cat in supplier["categories"] for cat in categories):
                        suppliers.append(supplier)
                else:
                    suppliers.append(supplier)

            return suppliers

    def update_supplier(self, supplier_id: str, supplier: dict) -> bool:
        """更新供应商信息"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE supplier SET
                    name = ?,
                    contact_email = ?,
                    contact_wechat = ?,
                    contact_phone = ?,
                    contact_person = ?,
                    categories = ?,
                    capabilities = ?,
                    verification = ?,
                    response_rate = ?,
                    avg_response_time_hours = ?,
                    notes = ?,
                    active = ?,
                    is_test_data = ?
                WHERE id = ?
            """, (
                supplier["name"],
                supplier["contact"]["email"],
                supplier["contact"].get("wechat"),
                supplier["contact"].get("phone"),
                supplier["contact"].get("contact_person"),
                json.dumps(supplier.get("categories", [])),
                json.dumps(supplier.get("capabilities", {})),
                json.dumps(supplier.get("verification", {})),
                supplier.get("response_rate"),
                supplier.get("avg_response_time_hours"),
                supplier.get("notes"),
                1 if supplier.get("active", True) else 0,
                1 if supplier.get("is_test_data", False) else 0,
                supplier_id,
            ))
            conn.commit()
            return conn.total_changes > 0

    # ========================================================================
    # Quote Request CRUD
    # ========================================================================

    def create_quote_request(self, request: dict) -> str:
        """创建报价请求"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO quote_request (
                    id, case_id, supplier_id, product_name, product_description,
                    quantity, specifications, quote_deadline, currency,
                    status, buyer_id, approved_by, approved_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request["id"],
                request["case_id"],
                request["supplier_id"],
                request["product_name"],
                request["product_description"],
                request["quantity"],
                json.dumps(request.get("specifications", {})),
                request["quote_deadline"],
                request.get("currency", "USD"),
                request["status"],
                request["buyer_id"],
                request.get("approved_by"),
                request.get("approved_at"),
                request["created_at"],
                request["updated_at"],
            ))
            conn.commit()
        return request["id"]

    def get_quote_request(self, request_id: str) -> Optional[dict]:
        """获取报价请求"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM quote_request WHERE id = ?",
                (request_id,)
            ).fetchone()
            if row:
                return {
                    "id": row["id"],
                    "case_id": row["case_id"],
                    "supplier_id": row["supplier_id"],
                    "product_name": row["product_name"],
                    "product_description": row["product_description"],
                    "quantity": row["quantity"],
                    "specifications": json.loads(row["specifications"]),
                    "quote_deadline": row["quote_deadline"],
                    "currency": row["currency"],
                    "status": row["status"],
                    "buyer_id": row["buyer_id"],
                    "approved_by": row["approved_by"],
                    "approved_at": row["approved_at"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
        return None

    def update_quote_request(self, request_id: str, updates: dict) -> bool:
        """更新报价请求"""
        updates["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [request_id]

        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE quote_request SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            return conn.total_changes > 0

    # ========================================================================
    # Quote Token CRUD
    # ========================================================================

    def create_quote_token(self, token: dict) -> str:
        """创建报价 Token"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO quote_token (
                    id, token_hash, quote_request_id, supplier_id,
                    expires_at, is_revoked, revoked_at,
                    access_count, last_accessed_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                token["id"],
                token["token_hash"],
                token["quote_request_id"],
                token["supplier_id"],
                token["expires_at"],
                1 if token.get("is_revoked", False) else 0,
                token.get("revoked_at"),
                token.get("access_count", 0),
                token.get("last_accessed_at"),
                token["created_at"],
            ))
            conn.commit()
        return token["id"]

    def get_quote_token_by_hash(self, token_hash: str) -> Optional[dict]:
        """通过哈希获取 Token"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM quote_token WHERE token_hash = ?",
                (token_hash,)
            ).fetchone()
            if row:
                return {
                    "id": row["id"],
                    "token_hash": row["token_hash"],
                    "quote_request_id": row["quote_request_id"],
                    "supplier_id": row["supplier_id"],
                    "expires_at": row["expires_at"],
                    "is_revoked": bool(row["is_revoked"]),
                    "revoked_at": row["revoked_at"],
                    "access_count": row["access_count"],
                    "last_accessed_at": row["last_accessed_at"],
                    "created_at": row["created_at"],
                }
        return None

    def increment_token_access(self, token_hash: str) -> bool:
        """增加 Token 访问次数"""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE quote_token
                SET access_count = access_count + 1,
                    last_accessed_at = ?
                WHERE token_hash = ?
            """, (now, token_hash))
            conn.commit()
            return conn.total_changes > 0

    def revoke_token(self, token_hash: str) -> bool:
        """撤销 Token"""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE quote_token
                SET is_revoked = 1, revoked_at = ?
                WHERE token_hash = ?
            """, (now, token_hash))
            conn.commit()
            return conn.total_changes > 0

    # ========================================================================
    # Supplier Quote CRUD
    # ========================================================================

    def create_supplier_quote(self, quote: dict) -> str:
        """创建供应商报价"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO supplier_quote (
                    id, quote_request_id, supplier_id, version,
                    unit_price, currency, moq, lead_time_days, trade_term,
                    quote_valid_until, payment_terms, specification_notes,
                    status, submitted_at, submitted_via, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quote["id"],
                quote["quote_request_id"],
                quote["supplier_id"],
                quote["version"],
                str(quote["unit_price"]),  # Decimal as string
                quote["currency"],
                quote["moq"],
                quote["lead_time_days"],
                quote["trade_term"],
                quote["quote_valid_until"],
                quote.get("payment_terms"),
                quote.get("specification_notes"),
                quote["status"],
                quote["submitted_at"],
                quote.get("submitted_via", "quote_portal"),
                json.dumps(quote.get("raw_data", {})),
            ))
            conn.commit()
        return quote["id"]

    def get_supplier_quotes(self, quote_request_id: str) -> list[dict]:
        """获取某个报价请求的所有报价"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM supplier_quote WHERE quote_request_id = ? ORDER BY version DESC",
                (quote_request_id,)
            ).fetchall()
            quotes = []
            for row in rows:
                quotes.append({
                    "id": row["id"],
                    "quote_request_id": row["quote_request_id"],
                    "supplier_id": row["supplier_id"],
                    "version": row["version"],
                    "unit_price": row["unit_price"],  # String, convert to Decimal in app
                    "currency": row["currency"],
                    "moq": row["moq"],
                    "lead_time_days": row["lead_time_days"],
                    "trade_term": row["trade_term"],
                    "quote_valid_until": row["quote_valid_until"],
                    "payment_terms": row["payment_terms"],
                    "specification_notes": row["specification_notes"],
                    "status": row["status"],
                    "submitted_at": row["submitted_at"],
                    "submitted_via": row["submitted_via"],
                    "raw_data": json.loads(row["raw_data"]),
                })
            return quotes

    def get_quotes_by_case(self, case_id: str) -> list[dict]:
        """获取某个采购案例的所有报价"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT sq.* FROM supplier_quote sq
                JOIN quote_request qr ON sq.quote_request_id = qr.id
                WHERE qr.case_id = ?
                ORDER BY sq.submitted_at DESC
            """, (case_id,)).fetchall()
            quotes = []
            for row in rows:
                quotes.append({
                    "id": row["id"],
                    "quote_request_id": row["quote_request_id"],
                    "supplier_id": row["supplier_id"],
                    "version": row["version"],
                    "unit_price": row["unit_price"],
                    "currency": row["currency"],
                    "moq": row["moq"],
                    "lead_time_days": row["lead_time_days"],
                    "trade_term": row["trade_term"],
                    "quote_valid_until": row["quote_valid_until"],
                    "payment_terms": row["payment_terms"],
                    "specification_notes": row["specification_notes"],
                    "status": row["status"],
                    "submitted_at": row["submitted_at"],
                    "submitted_via": row["submitted_via"],
                    "raw_data": json.loads(row["raw_data"]),
                })
            return quotes

    # ========================================================================
    # Quote Version CRUD
    # ========================================================================

    def create_quote_version(self, version: dict) -> str:
        """创建报价版本记录（不可变）"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO quote_version (
                    id, quote_id, version, snapshot,
                    changed_fields, change_reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                version["id"],
                version["quote_id"],
                version["version"],
                json.dumps(version["snapshot"]),
                json.dumps(version.get("changed_fields", [])),
                version.get("change_reason"),
                version["created_at"],
            ))
            conn.commit()
        return version["id"]

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


# 全局数据库实例 - 从环境变量读取路径（与 mcp_server 和 quote_api 统一）
import os as _os
_DB_PATH = _os.environ.get("DATABASE_PATH", "sourcing_mvp.db")
db = Database(_DB_PATH)
