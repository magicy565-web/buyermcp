"""
Token 管理器 - 安全的报价 Token 生命周期管理

实现完整的 Token 生成、验证、撤销和过期检查
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import uuid4


class TokenManager:
    """报价 Token 管理器"""

    @staticmethod
    def generate_token() -> Tuple[str, str]:
        """
        生成随机 Token 和对应的哈希值

        Returns:
            (token, token_hash): 原始 Token 和 SHA-256 哈希值
        """
        # 生成 256 位随机 Token
        token = secrets.token_urlsafe(32)  # 32 bytes = 256 bits

        # 计算 SHA-256 哈希
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        return token, token_hash

    @staticmethod
    def hash_token(token: str) -> str:
        """
        计算 Token 的 SHA-256 哈希值

        Args:
            token: 原始 Token

        Returns:
            SHA-256 哈希值（十六进制字符串）
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def verify_token_hash(token: str, expected_hash: str) -> bool:
        """
        验证 Token 哈希（使用时间常量比较防止时序攻击）

        Args:
            token: 原始 Token
            expected_hash: 期望的哈希值

        Returns:
            是否匹配
        """
        actual_hash = TokenManager.hash_token(token)
        return secrets.compare_digest(actual_hash, expected_hash)

    @staticmethod
    def is_token_expired(expires_at: str) -> bool:
        """
        检查 Token 是否过期

        Args:
            expires_at: ISO 8601 格式的过期时间

        Returns:
            是否过期
        """
        try:
            expiry = datetime.fromisoformat(expires_at)
            return datetime.now() >= expiry
        except (ValueError, TypeError):
            # 无效的日期格式，视为已过期
            return True

    @staticmethod
    def create_token_record(
        quote_request_id: str,
        supplier_id: str,
        token: str,
        token_hash: str,
        expire_hours: int = 72
    ) -> dict:
        """
        创建完整的 Token 数据库记录

        Args:
            quote_request_id: 报价请求 ID
            supplier_id: 供应商 ID
            token: 原始 Token（不存储）
            token_hash: Token 哈希值
            expire_hours: 有效期（小时）

        Returns:
            Token 记录字典
        """
        now = datetime.now()
        expires_at = now + timedelta(hours=expire_hours)

        return {
            "id": str(uuid4()),
            "token_hash": token_hash,
            "quote_request_id": quote_request_id,
            "supplier_id": supplier_id,
            "expires_at": expires_at.isoformat(),
            "is_revoked": False,
            "revoked_at": None,
            "access_count": 0,
            "last_accessed_at": None,
            "created_at": now.isoformat(),
        }


class TokenValidator:
    """Token 验证器"""

    def __init__(self, db):
        """
        初始化验证器

        Args:
            db: Database 实例
        """
        self.db = db

    def validate_token(self, token: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        验证 Token 的完整性和有效性

        Args:
            token: 原始 Token

        Returns:
            (is_valid, token_record, error_message)
        """
        # 计算哈希
        token_hash = TokenManager.hash_token(token)

        # 查询 Token 记录
        token_record = self.db.get_quote_token_by_hash(token_hash)

        if not token_record:
            return False, None, "Invalid token"

        # 检查是否已撤销
        if token_record["is_revoked"]:
            return False, token_record, "Token has been revoked"

        # 检查是否过期
        if TokenManager.is_token_expired(token_record["expires_at"]):
            return False, token_record, "Token has expired"

        # Token 有效
        return True, token_record, None

    def validate_and_check_request(
        self, token: str
    ) -> Tuple[bool, Optional[dict], Optional[dict], Optional[str]]:
        """
        验证 Token 并检查关联的报价请求状态

        Args:
            token: 原始 Token

        Returns:
            (is_valid, token_record, quote_request, error_message)
        """
        # 验证 Token
        is_valid, token_record, error = self.validate_token(token)
        if not is_valid:
            return False, token_record, None, error

        # 获取报价请求
        quote_request = self.db.get_quote_request(token_record["quote_request_id"])
        if not quote_request:
            return False, token_record, None, "Quote request not found"

        # 检查报价请求状态
        if quote_request["status"] == "cancelled":
            return False, token_record, quote_request, "Quote request has been cancelled"

        if quote_request["status"] == "expired":
            return False, token_record, quote_request, "Quote request has expired"

        # 检查报价截止时间
        if TokenManager.is_token_expired(quote_request["quote_deadline"]):
            return False, token_record, quote_request, "Quote deadline has passed"

        # 全部验证通过
        return True, token_record, quote_request, None

    def record_access(self, token: str) -> bool:
        """
        记录 Token 访问（增加访问次数）

        Args:
            token: 原始 Token

        Returns:
            是否成功
        """
        token_hash = TokenManager.hash_token(token)
        return self.db.increment_token_access(token_hash)
