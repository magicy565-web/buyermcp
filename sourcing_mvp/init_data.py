"""
初始化脚本 - 加载初始供应商数据
"""
import json
import logging
from pathlib import Path

from .database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_suppliers():
    """加载初始供应商数据"""
    suppliers_file = Path(__file__).parent / "data" / "suppliers.json"

    if not suppliers_file.exists():
        logger.error(f"Suppliers file not found: {suppliers_file}")
        return

    with open(suppliers_file, "r", encoding="utf-8") as f:
        suppliers = json.load(f)

    logger.info(f"Loading {len(suppliers)} suppliers...")

    for supplier in suppliers:
        try:
            # 检查是否已存在
            existing = db.get_supplier(supplier["id"])
            if existing:
                logger.info(f"Supplier {supplier['id']} already exists, skipping")
                continue

            # 创建供应商
            db.create_supplier(supplier)
            logger.info(f"✓ Created supplier: {supplier['name']}")

        except Exception as e:
            logger.error(f"Failed to create supplier {supplier['id']}: {e}")

    logger.info("Supplier data loaded successfully")


def init_database():
    """初始化数据库"""
    logger.info("Initializing database...")

    # 数据库表会在 Database 初始化时自动创建
    logger.info("✓ Database tables created")

    # 加载供应商数据
    load_suppliers()

    logger.info("✓ Database initialization complete")


if __name__ == "__main__":
    init_database()
