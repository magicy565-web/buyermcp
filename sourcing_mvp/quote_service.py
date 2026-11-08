"""
报价服务层 - 业务逻辑和原子操作

确保报价提交和版本历史的原子性
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple
from uuid import uuid4
import json

from .token_manager import TokenValidator


class QuoteService:
    """报价业务服务"""

    def __init__(self, db):
        """
        初始化服务

        Args:
            db: Database 实例
        """
        self.db = db
        self.token_validator = TokenValidator(db)

    def submit_quote_atomic(
        self,
        token: str,
        unit_price: str,
        currency: str,
        moq: int,
        lead_time_days: int,
        trade_term: str,
        quote_valid_until: str,
        payment_terms: Optional[str] = None,
        specification_notes: Optional[str] = None,
        raw_data: Optional[dict] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        原子性提交报价（报价记录 + 版本快照必须同时成功）

        Args:
            token: 访问 Token
            unit_price: 单价（Decimal 字符串）
            currency: 币种
            moq: 最小起订量
            lead_time_days: 交货期（天）
            trade_term: 贸易条款
            quote_valid_until: 报价有效期
            payment_terms: 付款条件
            specification_notes: 规格差异说明
            raw_data: 原始表单数据

        Returns:
            (success, quote_id, error_message)
        """
        # 1. 验证 Token 和报价请求
        is_valid, token_record, quote_request, error = (
            self.token_validator.validate_and_check_request(token)
        )
        if not is_valid:
            return False, None, error

        # 2. 验证价格格式
        try:
            price_decimal = Decimal(unit_price)
            if price_decimal <= 0:
                return False, None, "Unit price must be positive"
        except (InvalidOperation, ValueError):
            return False, None, "Invalid unit price format"

        # 3. 检查是否已有报价（获取最大版本号）
        existing_quotes = self.db.get_supplier_quotes(quote_request["id"])
        version = len(existing_quotes) + 1

        # 4. 准备报价记录
        quote_id = str(uuid4())
        now = datetime.now()

        quote_data = {
            "id": quote_id,
            "quote_request_id": quote_request["id"],
            "supplier_id": token_record["supplier_id"],
            "version": version,
            "unit_price": unit_price,  # 存储为字符串
            "currency": currency,
            "moq": moq,
            "lead_time_days": lead_time_days,
            "trade_term": trade_term,
            "quote_valid_until": quote_valid_until,
            "payment_terms": payment_terms,
            "specification_notes": specification_notes,
            "status": "submitted",
            "submitted_at": now.isoformat(),
            "submitted_via": "quote_portal",
            "raw_data": raw_data or {},
        }

        # 5. 准备版本快照
        version_data = {
            "id": str(uuid4()),
            "quote_id": quote_id,
            "version": version,
            "snapshot": quote_data.copy(),  # 完整快照
            "changed_fields": [],  # 首次提交无变更字段
            "change_reason": "Initial submission" if version == 1 else "Quote update",
            "created_at": now.isoformat(),
        }

        # 6. 原子性写入（使用事务）
        try:
            with self.db.get_connection() as conn:
                # 开启事务（SQLite 默认自动开启，commit 时提交）

                # 写入报价记录
                conn.execute("""
                    INSERT INTO supplier_quote (
                        id, quote_request_id, supplier_id, version,
                        unit_price, currency, moq, lead_time_days, trade_term,
                        quote_valid_until, payment_terms, specification_notes,
                        status, submitted_at, submitted_via, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    quote_data["id"],
                    quote_data["quote_request_id"],
                    quote_data["supplier_id"],
                    quote_data["version"],
                    quote_data["unit_price"],
                    quote_data["currency"],
                    quote_data["moq"],
                    quote_data["lead_time_days"],
                    quote_data["trade_term"],
                    quote_data["quote_valid_until"],
                    quote_data.get("payment_terms"),
                    quote_data.get("specification_notes"),
                    quote_data["status"],
                    quote_data["submitted_at"],
                    quote_data["submitted_via"],
                    json.dumps(quote_data["raw_data"]),
                ))

                # 写入版本历史
                conn.execute("""
                    INSERT INTO quote_version (
                        id, quote_id, version, snapshot,
                        changed_fields, change_reason, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    version_data["id"],
                    version_data["quote_id"],
                    version_data["version"],
                    json.dumps(version_data["snapshot"]),
                    json.dumps(version_data["changed_fields"]),
                    version_data["change_reason"],
                    version_data["created_at"],
                ))

                # 更新报价请求状态
                conn.execute("""
                    UPDATE quote_request
                    SET status = 'received', updated_at = ?
                    WHERE id = ?
                """, (now.isoformat(), quote_request["id"]))

                # 提交事务
                conn.commit()

            # 7. 记录 Token 访问
            self.token_validator.record_access(token)

            return True, quote_id, None

        except Exception as e:
            # 事务会自动回滚
            return False, None, f"Failed to save quote: {str(e)}"

    def get_quote_with_history(self, quote_id: str) -> Optional[dict]:
        """
        获取报价及其完整版本历史

        Args:
            quote_id: 报价 ID

        Returns:
            报价数据（包含版本历史）
        """
        # 查询报价（通过 case 查询，这里简化实现）
        # 实际应该添加单独的 get_quote_by_id 方法
        return None  # TODO: 实现

    def validate_buyer_access(
        self, buyer_id: str, case_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        验证买手对案件的访问权限

        Args:
            buyer_id: 买手 ID
            case_id: 案件 ID

        Returns:
            (has_access, error_message)
        """
        case = self.db.get_case(case_id)
        if not case:
            return False, "Case not found"

        if case["buyer_id"] != buyer_id:
            return False, "Access denied: not your case"

        return True, None
