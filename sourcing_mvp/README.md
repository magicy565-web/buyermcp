# AI Sourcing Partner - MVP

**定位**: AI Sourcing Partner for Global Buyers

从买手的一句话开始，到获得可执行的供应商报价。

---

## 🎯 核心价值

**当买手提出一个采购需求时，我们能够比他自己搜索、发邮件、比较供应商更快地拿到可信且可执行的结果。**

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install mcp pydantic
```

### 2. 初始化数据库

```bash
cd sourcing_mvp
python -m init_data
```

### 3. 运行 MCP Server

```bash
python -m mcp_server
```

### 4. 配置 Claude Desktop

添加到配置文件：
```json
{
  "mcpServers": {
    "sourcing-partner": {
      "command": "python",
      "args": ["-m", "sourcing_mvp.mcp_server"],
      "cwd": "C:\\path\\to\\sourcing_mvp"
    }
  }
}
```

---

## 📦 项目结构

```
sourcing_mvp/
├── models.py              # 数据模型
├── database.py            # SQLite
├── mcp_server.py          # MCP Server
├── init_data.py           # 初始化
├── tools/                 # 4个核心工具
│   ├── discover.py
│   ├── prepare.py
│   ├── send.py
│   └── track.py
└── data/
    └── suppliers.json     # 5家初始供应商
```

---

## 🛠️ 4 个核心工具

1. **discover_suppliers** - 发现供应商
2. **prepare_inquiry** - 准备询价
3. **send_inquiry** - 发送询价
4. **track_response** - 追踪回复

---

## 📊 初始数据：5 家真实供应商

- Shenzhen Kafei Electronics（咖啡机专家）
- Ningbo Home Appliance（通用小家电）
- Guangzhou Barista Tech（高端咖啡设备）⭐
- Dongguan Packaging（包装）
- Zhejiang Container（容器）

---

## ✅ MVP 完成度

- ✅ 4 个核心 MCP 工具
- ✅ SQLite 数据库
- ✅ 5 家初始供应商
- ✅ Sourcing Case 模型
- ⏳ 真实邮件发送（TODO）
- ⏳ 邮件回复检查（TODO）

---

详见 [PRODUCT_VISION.md](../PRODUCT_VISION.md) 了解产品定位。
