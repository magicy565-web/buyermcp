# Sourcing Quote Portal - End-to-End Test Guide

## 端到端测试流程

完整验证真实供应商报价入口的功能。

---

## 前置条件

1. **服务器环境**
   - 可访问的公网服务器
   - 域名：`sourcing.yourdomain.com`
   - Python 3.10+
   - Caddy 已安装

2. **测试账号**
   - 买手 ID: `test_buyer`
   - 测试供应商联系人（手机号或邮箱）

---

## 步骤 1: 部署服务

### 1.1 安装依赖

```bash
cd /opt/sourcing-mcp/sourcing_mvp
pip install -r requirements.txt
```

### 1.2 初始化数据库

```bash
python -m sourcing_mvp.init_data
```

### 1.3 启动 API 服务

```bash
# 方式 1: 直接启动（开发测试）
python -m sourcing_mvp.quote_api

# 方式 2: systemd 服务（生产）
sudo cp deployment/systemd/quote-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start quote-api
sudo systemctl enable quote-api
```

### 1.4 配置 Caddy

```bash
# 复制配置
sudo cp deployment/Caddyfile /etc/caddy/Caddyfile

# 启动 Caddy
sudo systemctl start caddy
sudo systemctl enable caddy
```

### 1.5 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 公网访问
curl https://sourcing.yourdomain.com/health
```

---

## 步骤 2: 通过 MCP 创建报价请求

### 2.1 启动 MCP Server

```bash
cd /opt/sourcing-mcp
python -m sourcing_mvp.mcp_server
```

### 2.2 在 Claude 中创建采购案例

```
Can you help me source 500 stainless steel insulated bottles?
```

Claude 会调用 `discover_suppliers` 创建案例。

### 2.3 创建报价请求

```
Create a quote request for supplier_001 for this case.
Product: 500ml Stainless Steel Insulated Bottle
Quantity: 500 units
Confirm: yes
Base URL: https://sourcing.yourdomain.com
```

Claude 调用 `create_quote_request`，返回：
- quote_request_id
- quote_link
- expires_at

---

## 步骤 3: 供应商提交报价

### 3.1 分享链接

将 `quote_link` 发送给测试联系人（微信/邮件）

### 3.2 供应商访问链接

在手机浏览器打开链接，验证：
- ✅ 页面正常加载
- ✅ 产品信息正确显示
- ✅ 表单为中英文双语
- ✅ 移动端界面友好

### 3.3 填写报价

- Unit Price: `18.50`
- Currency: `USD`
- MOQ: `100`
- Lead Time: `25` days
- Trade Terms: `FOB`
- Quote Valid Until: 选择未来日期
- Payment Terms: `30% deposit, 70% before shipping`

### 3.4 提交

点击"Submit Quotation"，验证：
- ✅ 表单验证正确
- ✅ 提交确认对话框
- ✅ 提交成功提示
- ✅ 表单禁用（不可再提交）

---

## 步骤 4: 买手查询报价

### 4.1 在 Claude 中查询

```
Show me the quotes for this case
```

Claude 调用 `get_quotes`，返回：
- 供应商名称
- 价格、MOQ、交期
- 贸易条款
- 报价有效期
- 提交时间

### 4.2 验证数据一致性

检查返回的报价是否与供应商提交的完全一致：
- ✅ 单价 `USD 18.50/unit`
- ✅ MOQ `100 units`
- ✅ 交期 `25 days`
- ✅ 贸易条款 `FOB`
- ✅ 付款条件正确
- ✅ 有效期正确

---

## 步骤 5: 验证数据库持久化

### 5.1 查询数据库

```bash
sqlite3 /var/lib/sourcing/sourcing_mvp.db

-- 查询报价请求
SELECT * FROM quote_request;

-- 查询报价
SELECT * FROM supplier_quote;

-- 查询版本历史
SELECT * FROM quote_version;

-- 查询 Token
SELECT * FROM quote_token;
```

### 5.2 验证

- ✅ 报价记录存在
- ✅ 版本历史记录存在
- ✅ Token 记录存在
- ✅ 数据完整且一致

---

## 步骤 6: 测试安全功能

### 6.1 过期 Token

等待 Token 过期（或修改数据库 expires_at），重新访问链接：
- ✅ 显示"Token has expired"错误

### 6.2 撤销 Token

```bash
sqlite3 /var/lib/sourcing/sourcing_mvp.db
UPDATE quote_token SET is_revoked = 1 WHERE token_hash = '<hash>';
```

重新访问链接：
- ✅ 显示"Token has been revoked"错误

### 6.3 权限验证

使用不同 buyer_id 查询报价：
- ✅ 返回"Access denied: not your case"

---

## 步骤 7: 重启测试

### 7.1 重启服务

```bash
sudo systemctl restart quote-api
```

### 7.2 查询报价

在 Claude 中再次查询报价：
- ✅ 报价仍然存在
- ✅ 数据完全一致

---

## 验收标准

全部通过以下检查：

1. ✅ 手机浏览器可访问报价链接
2. ✅ 表单中英文切换正常
3. ✅ 供应商成功提交报价
4. ✅ MCP 查询返回正确数据
5. ✅ 数据库持久化正确
6. ✅ 版本历史完整
7. ✅ Token 验证功能正常（过期、撤销）
8. ✅ 买手权限验证正常
9. ✅ 服务重启后数据仍存在
10. ✅ 提交数据与查询数据完全一致

---

## 故障排查

### API 无法访问

```bash
# 检查服务状态
sudo systemctl status quote-api

# 查看日志
sudo journalctl -u quote-api -f

# 检查端口
sudo netstat -tlnp | grep 8000
```

### Caddy 无法启动

```bash
# 检查配置
caddy validate --config /etc/caddy/Caddyfile

# 查看日志
sudo journalctl -u caddy -f
```

### 数据库错误

```bash
# 检查数据库文件
ls -la /var/lib/sourcing/sourcing_mvp.db

# 检查权限
sudo chown sourcing:sourcing /var/lib/sourcing/sourcing_mvp.db
```

### MCP 工具报错

```bash
# 检查 MCP Server 日志
python -m sourcing_mvp.mcp_server --debug
```

---

## 完成

完成所有步骤后，即可证明：
- ✅ 真实供应商可以提交报价
- ✅ 买手可以通过 AI 查询报价
- ✅ 数据安全、完整、可追溯
- ✅ 系统可靠、可重启、可部署

这是第一个完整的真实业务闭环！
