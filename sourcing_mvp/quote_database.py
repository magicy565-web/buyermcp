"""
报价系统数据库操作

扩展 Database 类，添加报价相关的 CRUD 操作
"""
import json
import hashlib
from typing import Optional
from datetime import datetime


class QuoteDatabase:
    """报价系统数据库操作混入类"""

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
                quote["unit_price"],
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


# 将 QuoteDatabase 混入到 Database 类
from .database import Database

# 使用多重继承扩展 Database
class ExtendedDatabase(Database, QuoteDatabase):
    """扩展的数据库类，包含报价功能"""
    pass
