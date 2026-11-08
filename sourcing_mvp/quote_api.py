"""
FastAPI 报价提交服务

供应商报价入口 - 无需账号，通过 Token 访问
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional
import os

from .database import Database
from .quote_service import QuoteService
from .token_manager import TokenManager

# 初始化
app = FastAPI(title="Sourcing Quote Portal", version="0.1.0")

# 数据库
DB_PATH = os.environ.get("DATABASE_PATH", "sourcing_mvp.db")
db = Database(DB_PATH)
quote_service = QuoteService(db)

# CORS 配置
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ============================================================================
# API Models
# ============================================================================

class QuoteSubmission(BaseModel):
    """报价提交数据"""
    token: str
    unit_price: str = Field(..., description="单价（Decimal字符串）")
    currency: str = Field(..., description="币种")
    moq: int = Field(..., gt=0, description="最小起订量")
    lead_time_days: int = Field(..., gt=0, description="交货期（天）")
    trade_term: str = Field(..., description="贸易条款")
    quote_valid_until: str = Field(..., description="报价有效期（ISO 8601）")
    payment_terms: Optional[str] = Field(None, description="付款条件")
    specification_notes: Optional[str] = Field(None, description="规格差异说明")

    @validator("unit_price")
    def validate_price(cls, v):
        try:
            price = Decimal(v)
            if price <= 0:
                raise ValueError("Price must be positive")
            return v
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid price format")

    @validator("currency")
    def validate_currency(cls, v):
        allowed = ["USD", "EUR", "CNY", "GBP", "JPY"]
        if v.upper() not in allowed:
            raise ValueError(f"Currency must be one of {allowed}")
        return v.upper()

    @validator("trade_term")
    def validate_trade_term(cls, v):
        allowed = ["FOB", "CIF", "EXW", "DDP", "OTHER"]
        if v.upper() not in allowed:
            raise ValueError(f"Trade term must be one of {allowed}")
        return v.upper()

    @validator("quote_valid_until")
    def validate_valid_until(cls, v):
        try:
            valid_date = datetime.fromisoformat(v.replace("Z", "+00:00"))
            if valid_date <= datetime.now():
                raise ValueError("Valid until date must be in the future")
            return v
        except (ValueError, TypeError):
            raise ValueError("Invalid date format")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """根路径"""
    return {"service": "Sourcing Quote Portal", "version": "0.1.0"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/q/{token}", response_class=HTMLResponse)
async def get_quote_form(token: str):
    """
    获取报价表单页面

    供应商通过专属链接访问此页面
    """
    # 验证 Token
    is_valid, token_record, quote_request, error = (
        quote_service.token_validator.validate_and_check_request(token)
    )

    if not is_valid:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Invalid Link</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background: #f5f5f5;
                    }}
                    .error {{
                        background: white;
                        padding: 2rem;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        max-width: 400px;
                        text-align: center;
                    }}
                    .error h1 {{
                        color: #e53e3e;
                        margin-top: 0;
                    }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>❌ Invalid Link</h1>
                    <p>{error}</p>
                    <p>Please contact the buyer if you believe this is a mistake.</p>
                </div>
            </body>
            </html>
            """,
            status_code=400
        )

    # 记录访问
    quote_service.token_validator.record_access(token)

    # 获取供应商信息
    supplier = db.get_supplier(quote_request["supplier_id"])

    # 返回表单页面（从静态文件读取）
    form_html_path = static_dir / "quote_form.html"
    if not form_html_path.exists():
        # 如果静态文件不存在，返回简单表单
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Submit Quote</title>
            </head>
            <body>
                <h1>Submit Your Quotation</h1>
                <p><strong>Product:</strong> {quote_request['product_name']}</p>
                <p><strong>Quantity:</strong> {quote_request['quantity']} units</p>
                <p><strong>Deadline:</strong> {quote_request['quote_deadline']}</p>
                <p>Form loading... Please check static/quote_form.html</p>
            </body>
            </html>
            """
        )

    # 读取并替换模板变量
    html_content = form_html_path.read_text(encoding="utf-8")
    html_content = html_content.replace("{{TOKEN}}", token)
    html_content = html_content.replace("{{PRODUCT_NAME}}", quote_request["product_name"])
    html_content = html_content.replace("{{PRODUCT_DESCRIPTION}}", quote_request["product_description"])
    html_content = html_content.replace("{{QUANTITY}}", str(quote_request["quantity"]))
    html_content = html_content.replace("{{SUPPLIER_NAME}}", supplier["name"] if supplier else "")
    html_content = html_content.replace("{{DEADLINE}}", quote_request["quote_deadline"])

    return HTMLResponse(content=html_content)


@app.post("/api/quote/submit")
async def submit_quote(submission: QuoteSubmission):
    """
    提交报价

    原子性写入：报价记录 + 版本历史
    """
    success, quote_id, error = quote_service.submit_quote_atomic(
        token=submission.token,
        unit_price=submission.unit_price,
        currency=submission.currency,
        moq=submission.moq,
        lead_time_days=submission.lead_time_days,
        trade_term=submission.trade_term,
        quote_valid_until=submission.quote_valid_until,
        payment_terms=submission.payment_terms,
        specification_notes=submission.specification_notes,
        raw_data=submission.dict(exclude={"token"}),
    )

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return JSONResponse(
        content={
            "success": True,
            "quote_id": quote_id,
            "message": "Quote submitted successfully",
            "submitted_at": datetime.now().isoformat(),
        },
        status_code=201
    )


@app.get("/api/quote/verify/{token}")
async def verify_token(token: str):
    """
    验证 Token 有效性（用于前端预检）
    """
    is_valid, token_record, quote_request, error = (
        quote_service.token_validator.validate_and_check_request(token)
    )

    if not is_valid:
        return JSONResponse(
            content={"valid": False, "error": error},
            status_code=400
        )

    return {
        "valid": True,
        "quote_request": {
            "product_name": quote_request["product_name"],
            "quantity": quote_request["quantity"],
            "deadline": quote_request["quote_deadline"],
        },
        "expires_at": token_record["expires_at"],
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("QUOTE_API_PORT", 8000))
    host = os.environ.get("QUOTE_API_HOST", "0.0.0.0")

    uvicorn.run(
        "sourcing_mvp.quote_api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
