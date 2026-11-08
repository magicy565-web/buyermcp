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

### 5 Test Suppliers (Not Production Ready)

⚠️ **All supplier data is for testing only**:
- Uses `example.com` email domains
- Not verified or contacted
- `active: false` - not available for real inquiries
- See [sourcing_mvp/data/suppliers.json](sourcing_mvp/data/suppliers.json)

**Real supplier integration is NOT yet implemented.**

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

**Goal**: 5-10 real verified suppliers with proven track records  
**Current Status**: Test data only, real supplier integration pending

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

### Stage 1: Discovery (In Development)

**Goal**: Validate buyer intent and supplier engagement

**Current Status**:
- ✅ Conversational interface (MCP tools)
- ✅ Supplier matching algorithm
- ✅ Inquiry email generation
- ❌ Real email sending (not implemented)
- ❌ Real response tracking (not implemented)
- ❌ Verified supplier network (test data only)

**Next Steps**:
1. Implement real email sending (SendGrid/SMTP)
2. Implement real response tracking (Gmail API/IMAP)
3. Integrate 5-10 verified real suppliers
4. Buyer identity and authorization
5. End-to-end test with real sourcing case

**Success Criteria**: 5+ buyers, 10+ real inquiries sent, 60%+ response rate

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
