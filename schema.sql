-- Sourcing MCP Core v0.1 — PostgreSQL 15+
-- 原则：Event 表是唯一事实来源（只增不改）；Quote / Evidence 不可变；金额与数量一律 数值+单位/币种。

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ───────────── 枚举 ─────────────
CREATE TYPE verification_status AS ENUM ('unverified','pending','verified','rejected','suspended');
CREATE TYPE rfq_status AS ENUM (
  'draft','needs_clarification','pending_approval','approved',
  'sent','quoted','negotiating','sample','closed','cancelled');
CREATE TYPE supplier_type AS ENUM ('factory','trader','unknown');
CREATE TYPE quote_status AS ENUM ('submitted','superseded','withdrawn','expired');
CREATE TYPE channel_type AS ENUM ('email','wecom','wechat_manual','phone','h5_link','api');
CREATE TYPE dispatch_status AS ENUM ('queued','sent','opened','responded','declined','expired','failed');
CREATE TYPE incoterm AS ENUM ('EXW','FCA','FAS','FOB','CFR','CIF','CPT','CIP','DAP','DPU','DDP');
CREATE TYPE approval_decision AS ENUM ('pending','approved','rejected','needs_info');
CREATE TYPE check_type AS ENUM (
  'business_registry',   -- L1 统一社会信用代码 / 工商状态
  'phone_callback',      -- L2 电话回拨核验
  'wecom_contact',       -- L2 企微联系人核验
  'certificate',         -- L3 证书文件
  'factory_audit',       -- L4 验厂
  'sample_confirmed',    -- L4 样品确认
  'sanctions_screening');

-- ───────────── 买方侧 ─────────────
CREATE TABLE buyer_org (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  legal_name text NOT NULL,
  country char(2) NOT NULL,                       -- ISO 3166-1 alpha-2
  tax_id text,
  website text,
  verification verification_status NOT NULL DEFAULT 'pending',
  verified_at timestamptz,
  rfq_quota_daily int NOT NULL DEFAULT 5,         -- 防刷询盘
  sanctions_checked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE buyer_contact (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  buyer_org_id uuid NOT NULL REFERENCES buyer_org(id),
  name text NOT NULL,
  email text NOT NULL,
  phone text,
  role text,
  verified_at timestamptz,
  UNIQUE (buyer_org_id, email)
);

-- Agent = 被授权的调用主体（OAuth client + 授权记录）
CREATE TABLE agent (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  buyer_org_id uuid NOT NULL REFERENCES buyer_org(id),
  oauth_client_id text NOT NULL UNIQUE,
  display_name text NOT NULL,
  scopes text[] NOT NULL DEFAULT '{read}',        -- read | draft | submit_rfq | disclose_buyer
  authorized_by uuid REFERENCES buyer_contact(id),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','revoked')),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (scopes <@ ARRAY['read','draft','submit_rfq','disclose_buyer'])
);

CREATE TABLE project (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  buyer_org_id uuid NOT NULL REFERENCES buyer_org(id),
  title text NOT NULL,
  created_by_agent_id uuid REFERENCES agent(id),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','closed')),
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ───────────── RFQ ─────────────
CREATE TABLE rfq (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES project(id),
  buyer_org_id uuid NOT NULL REFERENCES buyer_org(id),
  created_by_agent_id uuid REFERENCES agent(id),
  status rfq_status NOT NULL DEFAULT 'draft',
  version int NOT NULL DEFAULT 1,                 -- 乐观并发；每次内容修改 +1
  title text NOT NULL,
  category text NOT NULL DEFAULT 'cnc_machining',
  delivery_country char(2),
  delivery_city text,
  incoterm incoterm,
  target_delivery_date date,
  quote_deadline timestamptz,
  certifications text[] NOT NULL DEFAULT '{}',
  disclose_buyer boolean NOT NULL DEFAULT false,  -- 需 disclose_buyer scope
  notes_original text,
  notes_lang text,
  missing_fields jsonb NOT NULL DEFAULT '[]',     -- validate_rfq 最近一次结果
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON rfq (project_id);
CREATE INDEX ON rfq (buyer_org_id, status);

CREATE TABLE rfq_item (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rfq_id uuid NOT NULL REFERENCES rfq(id) ON DELETE CASCADE,
  line_no int NOT NULL,
  part_name text NOT NULL,
  part_number text,
  material text NOT NULL,                         -- 例 "6061-T6"
  material_standard text,
  tolerance_general text,                         -- 例 "ISO 2768-m"
  tolerance_critical jsonb NOT NULL DEFAULT '[]', -- [{feature,value}]
  surface_finish text,
  heat_treatment text,
  quantity numeric(20,6) NOT NULL CHECK (quantity > 0),
  quantity_unit text NOT NULL DEFAULT 'pcs',
  annual_volume numeric(20,6),
  target_unit_price numeric(20,6),
  target_currency char(3),
  notes_original text,
  notes_lang text,
  UNIQUE (rfq_id, line_no),
  CHECK ((target_unit_price IS NULL) = (target_currency IS NULL))
);

-- RFQ 状态机：合法流转表 + 触发器拦截
CREATE TABLE rfq_transition (
  from_status rfq_status NOT NULL,
  to_status rfq_status NOT NULL,
  PRIMARY KEY (from_status, to_status)
);
INSERT INTO rfq_transition VALUES
 ('draft','needs_clarification'),('draft','pending_approval'),
 ('needs_clarification','draft'),('needs_clarification','pending_approval'),
 ('pending_approval','approved'),('pending_approval','needs_clarification'),
 ('approved','sent'),
 ('sent','quoted'),('sent','closed'),
 ('quoted','negotiating'),('quoted','closed'),
 ('negotiating','quoted'),('negotiating','sample'),('negotiating','closed'),
 ('sample','negotiating'),('sample','closed'),
 ('draft','cancelled'),('needs_clarification','cancelled'),('pending_approval','cancelled'),
 ('approved','cancelled'),('sent','cancelled'),('quoted','cancelled'),
 ('negotiating','cancelled'),('sample','cancelled');

CREATE FUNCTION rfq_enforce_transition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status IS DISTINCT FROM OLD.status AND NOT EXISTS (
      SELECT 1 FROM rfq_transition WHERE from_status = OLD.status AND to_status = NEW.status) THEN
    RAISE EXCEPTION 'illegal rfq transition % -> %', OLD.status, NEW.status;
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END $$;
CREATE TRIGGER rfq_transition_guard BEFORE UPDATE ON rfq
  FOR EACH ROW EXECUTE FUNCTION rfq_enforce_transition();

-- 人工审批门：send_rfq 只创建 pending 记录
CREATE TABLE rfq_approval (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rfq_id uuid NOT NULL REFERENCES rfq(id),
  rfq_version int NOT NULL,                       -- 审批的是哪个版本
  requested_by_agent_id uuid REFERENCES agent(id),
  supplier_ids uuid[] NOT NULL,
  buyer_note text,
  decision approval_decision NOT NULL DEFAULT 'pending',
  reviewer text,
  reason text,
  decided_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ───────────── 供应商侧 ─────────────
CREATE TABLE supplier (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  legal_name_zh text NOT NULL,
  name_en text,
  uscc char(18) UNIQUE,                           -- 统一社会信用代码
  registration_status text,                       -- 存续 / 吊销 / 注销 ...
  registered_capital_cny numeric(20,2),
  established_on date,
  business_scope text,
  supplier_type supplier_type NOT NULL DEFAULT 'unknown',
  province text,
  city text,
  capabilities jsonb NOT NULL DEFAULT '{}',       -- {processes:[], materials:[], certs:[], machines:[], max_part_size_mm:{}}
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','paused','blocked')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE supplier_contact (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  supplier_id uuid NOT NULL REFERENCES supplier(id),
  name text NOT NULL,
  title text,
  phone text,
  wechat_id text,
  wecom_id text,
  email text,
  preferred_channel channel_type,
  verified_at timestamptz
);

CREATE TABLE evidence (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_type text NOT NULL CHECK (owner_type IN ('rfq','quote','supplier','buyer_org','message','unattached')),
  owner_id uuid,
  kind text NOT NULL CHECK (kind IN ('drawing','quote_sheet','screenshot','email','certificate','audit_report','sample_photo','other')),
  storage_key text NOT NULL,
  filename text NOT NULL,
  mime text NOT NULL,
  size_bytes bigint NOT NULL,
  sha256 bytea NOT NULL CHECK (octet_length(sha256) = 32),
  source_channel channel_type NOT NULL,
  uploaded_by_type text NOT NULL CHECK (uploaded_by_type IN ('buyer_agent','supplier','operator')),
  uploaded_by_id text,
  level_supported smallint CHECK (level_supported BETWEEN 0 AND 4),
  server_hash_verified boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON evidence (owner_type, owner_id);
CREATE INDEX ON evidence (sha256);

-- 核验项明细（不给单一分数）
CREATE TABLE supplier_verification (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  supplier_id uuid NOT NULL REFERENCES supplier(id),
  check_type check_type NOT NULL,
  result text NOT NULL CHECK (result IN ('pass','fail','inconclusive')),
  level_granted smallint CHECK (level_granted BETWEEN 0 AND 4),
  detail jsonb NOT NULL DEFAULT '{}',
  evidence_id uuid REFERENCES evidence(id),
  verified_by text NOT NULL,                      -- operator id 或 'system:<provider>'
  verified_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz
);
CREATE INDEX ON supplier_verification (supplier_id, check_type, verified_at DESC);

-- 外发记录：每次触达都是一条
CREATE TABLE rfq_dispatch (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rfq_id uuid NOT NULL REFERENCES rfq(id),
  rfq_version int NOT NULL,
  supplier_id uuid NOT NULL REFERENCES supplier(id),
  approval_id uuid NOT NULL REFERENCES rfq_approval(id),
  channel channel_type NOT NULL,
  status dispatch_status NOT NULL DEFAULT 'queued',
  quote_link_hash bytea UNIQUE,                   -- 只存一次性签名链接的哈希
  link_expires_at timestamptz,
  sent_at timestamptz,
  responded_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON rfq_dispatch (rfq_id, supplier_id);

-- ───────────── 报价（版本化、不可变） ─────────────
CREATE TABLE fx_snapshot (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  base char(3) NOT NULL,
  rates jsonb NOT NULL,                           -- {"USD":0.139,"EUR":0.128}
  source text NOT NULL,
  rate_date date NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE quote (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rfq_id uuid NOT NULL REFERENCES rfq(id),
  supplier_id uuid NOT NULL REFERENCES supplier(id),
  dispatch_id uuid REFERENCES rfq_dispatch(id),
  version int NOT NULL DEFAULT 1,
  supersedes_id uuid REFERENCES quote(id),
  status quote_status NOT NULL DEFAULT 'submitted',
  currency char(3) NOT NULL,
  tax_included boolean NOT NULL,
  tax_rate numeric(5,4),                          -- 0.1300 = 13%；tax_included=true 时必填
  incoterm incoterm,
  incoterm_place text,
  payment_terms text,
  valid_until timestamptz NOT NULL,
  quoted_by_name text NOT NULL,
  quoted_by_title text,
  quoted_by_contact text,
  source_channel channel_type NOT NULL,
  verification_level smallint NOT NULL DEFAULT 0 CHECK (verification_level BETWEEN 0 AND 4),
  verification_note text,
  supplier_note_original text,                    -- 不可信文本
  supplier_note_lang text,
  submitted_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rfq_id, supplier_id, version),
  CHECK (NOT tax_included OR tax_rate IS NOT NULL)
);
CREATE INDEX ON quote (rfq_id, status);

CREATE TABLE quote_line (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  quote_id uuid NOT NULL REFERENCES quote(id) ON DELETE RESTRICT,
  rfq_item_id uuid NOT NULL REFERENCES rfq_item(id),
  unit_price numeric(20,6) NOT NULL CHECK (unit_price >= 0),
  quantity numeric(20,6) NOT NULL CHECK (quantity > 0),   -- 该价格对应的数量档
  quantity_unit text NOT NULL,
  moq numeric(20,6),
  tooling_fee numeric(20,6),
  lead_time_days int,
  note_original text,
  note_lang text
);

-- ───────────── 消息（经运营审核中转） ─────────────
CREATE TABLE message (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rfq_id uuid NOT NULL REFERENCES rfq(id),
  supplier_id uuid NOT NULL REFERENCES supplier(id),
  direction text NOT NULL CHECK (direction IN ('buyer_to_supplier','supplier_to_buyer')),
  body_original text NOT NULL,
  body_lang text,
  untrusted boolean GENERATED ALWAYS AS (direction = 'supplier_to_buyer') STORED,
  review_status text NOT NULL DEFAULT 'pending_review'
      CHECK (review_status IN ('pending_review','released','blocked')),
  reviewed_by text,
  attachment_evidence_ids uuid[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ───────────── 事件日志（唯一事实来源，哈希链防篡改） ─────────────
CREATE TABLE event (
  seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  stream_type text NOT NULL CHECK (stream_type IN ('project','buyer_org','supplier')),
  stream_id uuid NOT NULL,                        -- 哈希链按 stream 串联
  project_id uuid REFERENCES project(id),
  type text NOT NULL,                             -- 见文件末尾事件类型清单
  actor_type text NOT NULL CHECK (actor_type IN ('agent','operator','supplier','system')),
  actor_id text,
  payload jsonb NOT NULL DEFAULT '{}',
  idempotency_key text,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  prev_hash bytea,
  hash bytea NOT NULL
);
CREATE INDEX ON event (project_id, seq);
CREATE INDEX ON event (stream_type, stream_id, seq);

CREATE FUNCTION event_chain() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE prev bytea;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended(NEW.stream_id::text, 0));
  SELECT hash INTO prev FROM event
   WHERE stream_type = NEW.stream_type AND stream_id = NEW.stream_id
   ORDER BY seq DESC LIMIT 1;
  NEW.prev_hash := prev;
  NEW.hash := digest(
     coalesce(prev, ''::bytea) ||
     convert_to(NEW.stream_id::text || '|' || NEW.type || '|' ||
                NEW.actor_type || '|' || NEW.occurred_at::text || '|' || NEW.payload::text, 'UTF8'),
     'sha256');
  RETURN NEW;
END $$;
CREATE TRIGGER event_hash_chain BEFORE INSERT ON event
  FOR EACH ROW EXECUTE FUNCTION event_chain();

CREATE FUNCTION forbid_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '% is append-only', TG_TABLE_NAME; END $$;
CREATE TRIGGER event_immutable BEFORE UPDATE OR DELETE ON event
  FOR EACH ROW EXECUTE FUNCTION forbid_mutation();
CREATE TRIGGER evidence_immutable BEFORE DELETE ON evidence   -- 证据仅允许补充 server_hash_verified，不可删
  FOR EACH ROW EXECUTE FUNCTION forbid_mutation();
CREATE TRIGGER quote_line_immutable BEFORE UPDATE OR DELETE ON quote_line
  FOR EACH ROW EXECUTE FUNCTION forbid_mutation();

-- ───────────── 幂等键 ─────────────
CREATE TABLE idempotency_key (
  agent_id uuid NOT NULL REFERENCES agent(id),
  key text NOT NULL,
  tool text NOT NULL,
  request_hash bytea NOT NULL,                    -- 同 key 不同请求体 → 拒绝
  response jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (agent_id, key)
);

/* 事件类型清单（type 字段）
 buyer_org.registered / buyer_org.verified / agent.authorized / agent.revoked
 project.created / project.closed
 rfq.draft_created / rfq.updated / rfq.validated / rfq.clarification_requested
 rfq.submitted_for_approval / rfq.approved / rfq.rejected / rfq.cancelled
 dispatch.queued / dispatch.sent / dispatch.opened / dispatch.failed / dispatch.declined / dispatch.expired
 quote.submitted / quote.superseded / quote.withdrawn / quote.expired
 evidence.uploaded / evidence.hash_verified
 supplier.created / supplier.verified / supplier.check_failed
 message.posted / message.released / message.blocked / message.received
 rfq.status_changed / reminder.sent
*/
