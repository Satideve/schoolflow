>>> LOADED ENV.PY: /app/backend/migrations/env.py
>>> sys.path[0]: /app/backend
>>> Warning: skipping logging config: 'formatters'
>>> Alembic DB URL: postgresql+psycopg2://admin:admin@db:5432/schoolflow
>>> Tables in Base.metadata: ['user', 'fee_plan', 'fee_component', 'fee_plan_component', 'fee_assignment', 'fee_invoice', 'payment', 'receipt']
>>> Tables in DATABASE (inspector): []
>>> Tables in METADATA: ['user', 'fee_plan', 'fee_component', 'fee_plan_component', 'fee_assignment', 'fee_invoice', 'payment', 'receipt']
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 03fca167d58d

CREATE TABLE fee_component (
    id SERIAL NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    description VARCHAR(512), 
    PRIMARY KEY (id)
);

CREATE INDEX ix_fee_component_id ON fee_component (id);

CREATE TABLE fee_invoice (
    id SERIAL NOT NULL, 
    student_id INTEGER NOT NULL, 
    period VARCHAR(64) NOT NULL, 
    amount_due NUMERIC(10, 2) NOT NULL, 
    due_date TIMESTAMP WITH TIME ZONE NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE INDEX ix_fee_invoice_id ON fee_invoice (id);

CREATE TABLE fee_plan (
    id SERIAL NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    academic_year VARCHAR(20) NOT NULL, 
    frequency VARCHAR(20) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_fee_plan_id ON fee_plan (id);

CREATE TABLE "user" (
    id SERIAL NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    hashed_password VARCHAR(255) NOT NULL, 
    role VARCHAR(50) NOT NULL, 
    is_active BOOLEAN, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_user_email ON "user" (email);

CREATE INDEX ix_user_id ON "user" (id);

CREATE TABLE fee_assignment (
    id SERIAL NOT NULL, 
    student_id INTEGER NOT NULL, 
    fee_plan_id INTEGER NOT NULL, 
    concession NUMERIC(10, 2), 
    note VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(fee_plan_id) REFERENCES fee_plan (id)
);

CREATE INDEX ix_fee_assignment_id ON fee_assignment (id);

CREATE TABLE fee_plan_component (
    id SERIAL NOT NULL, 
    fee_plan_id INTEGER NOT NULL, 
    fee_component_id INTEGER NOT NULL, 
    amount NUMERIC(10, 2) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(fee_component_id) REFERENCES fee_component (id), 
    FOREIGN KEY(fee_plan_id) REFERENCES fee_plan (id)
);

CREATE INDEX ix_fee_plan_component_id ON fee_plan_component (id);

CREATE TABLE payment (
    id SERIAL NOT NULL, 
    fee_invoice_id INTEGER NOT NULL, 
    provider VARCHAR(50) NOT NULL, 
    provider_txn_id VARCHAR(255) NOT NULL, 
    amount NUMERIC(10, 2) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    idempotency_key VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(fee_invoice_id) REFERENCES fee_invoice (id), 
    CONSTRAINT u_provider_txn UNIQUE (provider, provider_txn_id)
);

CREATE INDEX ix_payment_id ON payment (id);

CREATE INDEX ix_payment_idempotency_key ON payment (idempotency_key);

CREATE TABLE receipt (
    id SERIAL NOT NULL, 
    payment_id INTEGER NOT NULL, 
    receipt_no VARCHAR(64) NOT NULL, 
    pdf_path VARCHAR(1024) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(payment_id) REFERENCES payment (id), 
    UNIQUE (receipt_no)
);

CREATE INDEX ix_receipt_id ON receipt (id);

INSERT INTO alembic_version (version_num) VALUES ('03fca167d58d') RETURNING alembic_version.version_num;

COMMIT;

