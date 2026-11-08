# AI Sourcing Partner

**AI-powered sourcing from China for global buyers**

从买手的一句话开始，到获得可执行的供应商报价。

---

## 🎯 What We Are

**AI Sourcing Partner for Global Buyers**

Not a supplier directory. Not a procurement ERP. Not automation software.

A partner that can research, screen, contact and advance sourcing faster than you can yourself.

---

## 🚀 Quick Start

### For Buyers

1. Install Claude Desktop
2. Add MCP Server configuration
3. Start chatting:
   ```
   Can you find a manufacturer for portable espresso makers at MOQ 100?
   ```

See [sourcing_mvp/README.md](sourcing_mvp/README.md) for detailed setup.

### For Developers

```bash
# Install dependencies
pip install mcp pydantic

# Initialize database
cd sourcing_mvp
python -m init_data

# Run MCP server
python -m mcp_server
```

---

## 📦 Project Structure

```
buyermcp/
├── sourcing_mvp/              # MVP Implementation (Active)
│   ├── models.py              # Data models
│   ├── database.py            # SQLite
│   ├── mcp_server.py          # 4 core tools
│   ├── tools/                 # discover, prepare, send, track
│   └── data/                  # 5 initial suppliers
│
├── sourcing_mcp/              # v0.1-v0.2 (Reference only)
│   └── ...                    # Over-engineered, kept for reference
│
├── PRODUCT_VISION.md          # Product direction
├── ARCHITECTURE_COMPARISON.md # Why we pivoted
└── TESTING_GUIDE.md           # How to test
```

---

## 🛠️ Core Features

### 4 MCP Tools

1. **discover_suppliers** - Find 2-5 suitable manufacturers
2. **prepare_inquiry** - Generate professional inquiry emails
3. **send_inquiry** - Send and track inquiries
4. **track_response** - Check supplier responses

### 5 Real Suppliers

- Shenzhen Kafei Electronics (Coffee makers)
- Ningbo Home Appliance (Small appliances)
- Guangzhou Barista Tech (Premium coffee equipment) ⭐
- Dongguan Packaging (Custom packaging)
- Zhejiang Container (Food-grade containers)

---

## 📊 Key Metrics

We measure what matters:

- ✅ **Real inquiries sent** (not tool calls)
- ✅ **Supplier response rate** (not database size)
- ✅ **Quote validity** (not matches)
- ✅ **Buyer satisfaction** (not QPS)
- ✅ **Repeat usage** (not features)

---

## 🎯 Product Philosophy

### 1. Start from Intent, Not Forms

**Before**: Fill out RFQ forms, select categories, complete specs  
**Now**: "Can you find..." - AI handles the details

### 2. Real > Scale

**5 real verified suppliers** > 10,000 database records

### 3. Good Enough is Good

**SQLite** > PostgreSQL + Redis + Elasticsearch (for now)

### 4. Transparent Uncertainty

- ✅ "MOQ flexible"
- ⚠️ "Lead time not verified"
- ⚠️ "Contact not yet verified"

Never fabricate. Never guess.

---

## 📝 Documentation

### Product

- [PRODUCT_VISION.md](PRODUCT_VISION.md) - What we're building
- [ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md) - Why we pivoted
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - How to test

### Technical

- [sourcing_mvp/README.md](sourcing_mvp/README.md) - MVP setup
- [sourcing_mvp/models.py](sourcing_mvp/models.py) - Data models
- [sourcing_mvp/mcp_server.py](sourcing_mvp/mcp_server.py) - MCP server

---

## 🚀 Roadmap

### Stage 1: Discovery (Current MVP)

**Goal**: Validate buyer intent

- ✅ Buyer Magazine with products
- ✅ Conversational sourcing
- ✅ Supplier recommendations
- ✅ Inquiry coordination
- ✅ Response tracking

**Success**: 5+ buyers, 10+ inquiries, 60%+ response rate

### Stage 2: Connection

**Goal**: Validate quote quality

- Multi-round quote comparison
- Sample coordination
- Auto follow-up reminders
- Enhanced supplier profiles

**Success**: 50+ valid quotes, 10+ samples, 5+ orders

### Stage 3: Agency

**Goal**: Validate willingness to pay

- Negotiation assistance
- Order progress tracking
- QC coordination
- Long-term relationship management

**Success**: $100K+ GMV, 20%+ conversion, 70%+ retention

---

## 💡 Why We Pivoted

### v0.1-v0.2 (Abandoned)

- 6 microservices
- 4 databases
- 350KB code
- 6-month timeline
- Technical metrics

**Problem**: Over-engineered, product direction unclear

### MVP (Current)

- 4 tools
- SQLite
- 40KB code
- 2-week validation
- Business metrics

**Better**: Simple, focused, testable

See [ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md) for full analysis.

---

## 🤝 Contributing

Currently in private MVP testing. 

If you're a buyer interested in testing, or a supplier interested in participating, please reach out.

---

## 📄 License

Proprietary

---

## 🔗 Links

- **Repository**: https://github.com/magicy565-web/buyermcp
- **Issues**: https://github.com/magicy565-web/buyermcp/issues

---

**Status**: 🟢 MVP Complete, Ready for Testing  
**Version**: 0.1.0-mvp  
**Last Updated**: 2025-01-09
