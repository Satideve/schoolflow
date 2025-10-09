--
-- PostgreSQL database dump
--

\restrict 7cLzrgb6aQuKUQEGa3h3qhaCGyGgohQNul67cgpXcL2ZjwSBPFEOe7APLdXgWaE

-- Dumped from database version 15.14 (Debian 15.14-1.pgdg13+1)
-- Dumped by pg_dump version 15.14 (Debian 15.14-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: admin
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO admin;

--
-- Name: class_sections; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.class_sections (
    id integer NOT NULL,
    name character varying NOT NULL,
    academic_year character varying NOT NULL
);


ALTER TABLE public.class_sections OWNER TO admin;

--
-- Name: class_sections_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.class_sections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.class_sections_id_seq OWNER TO admin;

--
-- Name: class_sections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.class_sections_id_seq OWNED BY public.class_sections.id;


--
-- Name: fee_assignment; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.fee_assignment (
    id integer NOT NULL,
    student_id integer NOT NULL,
    fee_plan_id integer NOT NULL,
    concession numeric(10,2),
    note character varying(255)
);


ALTER TABLE public.fee_assignment OWNER TO admin;

--
-- Name: fee_assignment_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.fee_assignment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fee_assignment_id_seq OWNER TO admin;

--
-- Name: fee_assignment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.fee_assignment_id_seq OWNED BY public.fee_assignment.id;


--
-- Name: fee_component; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.fee_component (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(512)
);


ALTER TABLE public.fee_component OWNER TO admin;

--
-- Name: fee_component_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.fee_component_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fee_component_id_seq OWNER TO admin;

--
-- Name: fee_component_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.fee_component_id_seq OWNED BY public.fee_component.id;


--
-- Name: fee_invoice; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.fee_invoice (
    id integer NOT NULL,
    student_id integer NOT NULL,
    period character varying(64) NOT NULL,
    amount_due numeric(10,2) NOT NULL,
    due_date timestamp with time zone NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    invoice_no character varying(64) NOT NULL
);


ALTER TABLE public.fee_invoice OWNER TO admin;

--
-- Name: fee_invoice_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.fee_invoice_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fee_invoice_id_seq OWNER TO admin;

--
-- Name: fee_invoice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.fee_invoice_id_seq OWNED BY public.fee_invoice.id;


--
-- Name: fee_plan; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.fee_plan (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    academic_year character varying(20) NOT NULL,
    frequency character varying(20) NOT NULL
);


ALTER TABLE public.fee_plan OWNER TO admin;

--
-- Name: fee_plan_component; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.fee_plan_component (
    id integer NOT NULL,
    fee_plan_id integer NOT NULL,
    fee_component_id integer NOT NULL,
    amount numeric(10,2) NOT NULL
);


ALTER TABLE public.fee_plan_component OWNER TO admin;

--
-- Name: fee_plan_component_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.fee_plan_component_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fee_plan_component_id_seq OWNER TO admin;

--
-- Name: fee_plan_component_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.fee_plan_component_id_seq OWNED BY public.fee_plan_component.id;


--
-- Name: fee_plan_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.fee_plan_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fee_plan_id_seq OWNER TO admin;

--
-- Name: fee_plan_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.fee_plan_id_seq OWNED BY public.fee_plan.id;


--
-- Name: payment; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.payment (
    id integer NOT NULL,
    fee_invoice_id integer NOT NULL,
    provider character varying(50) NOT NULL,
    provider_txn_id character varying(255) NOT NULL,
    amount numeric(10,2) NOT NULL,
    status character varying(20) NOT NULL,
    idempotency_key character varying(255),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.payment OWNER TO admin;

--
-- Name: payment_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.payment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.payment_id_seq OWNER TO admin;

--
-- Name: payment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.payment_id_seq OWNED BY public.payment.id;


--
-- Name: receipt; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.receipt (
    id integer NOT NULL,
    payment_id integer NOT NULL,
    receipt_no character varying(64) NOT NULL,
    pdf_path character varying(1024) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    created_by integer NOT NULL
);


ALTER TABLE public.receipt OWNER TO admin;

--
-- Name: receipt_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.receipt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.receipt_id_seq OWNER TO admin;

--
-- Name: receipt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.receipt_id_seq OWNED BY public.receipt.id;


--
-- Name: students; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.students (
    id integer NOT NULL,
    name character varying NOT NULL,
    roll_number character varying NOT NULL,
    class_section_id integer NOT NULL
);


ALTER TABLE public.students OWNER TO admin;

--
-- Name: students_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.students_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.students_id_seq OWNER TO admin;

--
-- Name: students_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.students_id_seq OWNED BY public.students.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    role character varying(50) NOT NULL,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public."user" OWNER TO admin;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO admin;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: class_sections id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.class_sections ALTER COLUMN id SET DEFAULT nextval('public.class_sections_id_seq'::regclass);


--
-- Name: fee_assignment id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_assignment ALTER COLUMN id SET DEFAULT nextval('public.fee_assignment_id_seq'::regclass);


--
-- Name: fee_component id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_component ALTER COLUMN id SET DEFAULT nextval('public.fee_component_id_seq'::regclass);


--
-- Name: fee_invoice id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_invoice ALTER COLUMN id SET DEFAULT nextval('public.fee_invoice_id_seq'::regclass);


--
-- Name: fee_plan id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_plan ALTER COLUMN id SET DEFAULT nextval('public.fee_plan_id_seq'::regclass);


--
-- Name: fee_plan_component id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_plan_component ALTER COLUMN id SET DEFAULT nextval('public.fee_plan_component_id_seq'::regclass);


--
-- Name: payment id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment ALTER COLUMN id SET DEFAULT nextval('public.payment_id_seq'::regclass);


--
-- Name: receipt id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.receipt ALTER COLUMN id SET DEFAULT nextval('public.receipt_id_seq'::regclass);


--
-- Name: students id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.students ALTER COLUMN id SET DEFAULT nextval('public.students_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.alembic_version (version_num) FROM stdin;
20250929_inv_constraints
\.


--
-- Data for Name: class_sections; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.class_sections (id, name, academic_year) FROM stdin;
1	IX-A	2025-2026
2	X-B	2025-2026
\.


--
-- Data for Name: fee_assignment; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.fee_assignment (id, student_id, fee_plan_id, concession, note) FROM stdin;
1	1	2	\N	\N
\.


--
-- Data for Name: fee_component; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.fee_component (id, name, description) FROM stdin;
1	Tuition	Tuition
2	Transport	Transport
3	Lab Fee	Lab Fee
\.


--
-- Data for Name: fee_invoice; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.fee_invoice (id, student_id, period, amount_due, due_date, status, created_at, invoice_no) FROM stdin;
1	1	Oct-2025	1650.00	2025-10-01 00:00:00+00	pending	2025-09-18 16:13:07.702959+00	INV-00001
2	3	Oct-2025	1650.00	2025-10-10 00:00:00+00	pending	2025-09-19 10:58:33.71132+00	INV-00002
3	1	2025-09	5000.00	2025-09-30 00:00:00+00	paid	2025-09-23 16:21:52.815935+00	INV-00003
\.


--
-- Data for Name: fee_plan; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.fee_plan (id, name, academic_year, frequency) FROM stdin;
1	Standard-IX-2025	2025	monthly
2	Standard-IX-2025	2025	monthly
\.


--
-- Data for Name: fee_plan_component; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.fee_plan_component (id, fee_plan_id, fee_component_id, amount) FROM stdin;
1	2	1	1200.00
2	2	2	300.00
3	2	3	150.00
\.


--
-- Data for Name: payment; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.payment (id, fee_invoice_id, provider, provider_txn_id, amount, status, idempotency_key, created_at) FROM stdin;
1	1	UPI	txn_20250919_001	1650.00	completed	pay_anjali_oct2025	2025-09-18 16:18:40.315234+00
2	2	manual	TXN123456	1650.00	paid	\N	2025-09-19 11:00:37.639709+00
3	3	fake	txn_test_12345	5000.00	captured	txn_test_12345	2025-09-23 17:44:42.905296+00
\.


--
-- Data for Name: receipt; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.receipt (id, payment_id, receipt_no, pdf_path, created_at, created_by) FROM stdin;
3	2	RCT-2025-0002	app/data/receipts/RCT-2025-0002.pdf	2025-09-19 12:44:49.943713+00	1
4	1	REC-98C9B9F3F4	app/data/receipts/REC-98C9B9F3F4.pdf	2025-09-19 17:10:52.879021+00	1
5	3	REC-8407D90DBE	app/data/receipts/REC-8407D90DBE.pdf	2025-09-23 17:44:42.952427+00	1
\.


--
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.students (id, name, roll_number, class_section_id) FROM stdin;
1	Anjali Singh	1A-001	1
2	Rahul Sharma	1A-002	1
3	Test Student	TS001	1
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public."user" (id, email, hashed_password, role, is_active, created_at, updated_at) FROM stdin;
1	admin@example.com	$2b$12$.W3v1pdcV8/s5oZr4iaa7OH1sPrk5qRUthkVfNSu.JeaCEDjmLV.6	admin	t	2025-09-17 06:52:28.688227+00	2025-09-22 16:04:47.768888+00
2	schooladmin@example.com	$2b$12$ziXJnf2SkzArZw5ZyJV.8e0vyiHdHpQAEzjI1LlN7.QrcG/qYF5XG	admin	t	2025-09-26 14:06:34.924277+00	\N
3	sandboxman@example.com	$2b$12$BEeyVLvtFrblzRdiZcALr.3x/EsGoc.g988SmQRME.7VVaHfNC/kW	admin	t	2025-09-27 16:59:20.519779+00	\N
5	testadmin@example.com	$2b$12$L8A490L1Vn5z/V2lvqzX.euWq5Xk01oOaA6Gbdk4Uce7BUzy3yY2u	admin	t	2025-10-04 08:45:50.51989+00	\N
\.


--
-- Name: class_sections_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.class_sections_id_seq', 2, true);


--
-- Name: fee_assignment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.fee_assignment_id_seq', 1, true);


--
-- Name: fee_component_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.fee_component_id_seq', 3, true);


--
-- Name: fee_invoice_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.fee_invoice_id_seq', 8, true);


--
-- Name: fee_plan_component_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.fee_plan_component_id_seq', 3, true);


--
-- Name: fee_plan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.fee_plan_id_seq', 2, true);


--
-- Name: payment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.payment_id_seq', 3, true);


--
-- Name: receipt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.receipt_id_seq', 5, true);


--
-- Name: students_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.students_id_seq', 3, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.user_id_seq', 5, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: class_sections class_sections_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.class_sections
    ADD CONSTRAINT class_sections_pkey PRIMARY KEY (id);


--
-- Name: fee_assignment fee_assignment_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_assignment
    ADD CONSTRAINT fee_assignment_pkey PRIMARY KEY (id);


--
-- Name: fee_component fee_component_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_component
    ADD CONSTRAINT fee_component_pkey PRIMARY KEY (id);


--
-- Name: fee_invoice fee_invoice_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_invoice
    ADD CONSTRAINT fee_invoice_pkey PRIMARY KEY (id);


--
-- Name: fee_plan_component fee_plan_component_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_plan_component
    ADD CONSTRAINT fee_plan_component_pkey PRIMARY KEY (id);


--
-- Name: fee_plan fee_plan_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_plan
    ADD CONSTRAINT fee_plan_pkey PRIMARY KEY (id);


--
-- Name: payment payment_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment
    ADD CONSTRAINT payment_pkey PRIMARY KEY (id);


--
-- Name: receipt receipt_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT receipt_pkey PRIMARY KEY (id);


--
-- Name: receipt receipt_receipt_no_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT receipt_receipt_no_key UNIQUE (receipt_no);


--
-- Name: students students_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_pkey PRIMARY KEY (id);


--
-- Name: payment u_provider_txn; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment
    ADD CONSTRAINT u_provider_txn UNIQUE (provider, provider_txn_id);


--
-- Name: fee_invoice uq_fee_invoice_invoice_no; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_invoice
    ADD CONSTRAINT uq_fee_invoice_invoice_no UNIQUE (invoice_no);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: ix_class_sections_academic_year; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_class_sections_academic_year ON public.class_sections USING btree (academic_year);


--
-- Name: ix_class_sections_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_class_sections_id ON public.class_sections USING btree (id);


--
-- Name: ix_class_sections_name; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_class_sections_name ON public.class_sections USING btree (name);


--
-- Name: ix_fee_assignment_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fee_assignment_id ON public.fee_assignment USING btree (id);


--
-- Name: ix_fee_component_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fee_component_id ON public.fee_component USING btree (id);


--
-- Name: ix_fee_invoice_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fee_invoice_created_at ON public.fee_invoice USING btree (created_at);


--
-- Name: ix_fee_invoice_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fee_invoice_id ON public.fee_invoice USING btree (id);


--
-- Name: ix_fee_invoice_invoice_no; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_fee_invoice_invoice_no ON public.fee_invoice USING btree (invoice_no);


--
-- Name: ix_fee_invoice_student_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fee_invoice_student_id ON public.fee_invoice USING btree (student_id);


--
-- Name: ix_fee_plan_component_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fee_plan_component_id ON public.fee_plan_component USING btree (id);


--
-- Name: ix_fee_plan_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fee_plan_id ON public.fee_plan USING btree (id);


--
-- Name: ix_payment_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_id ON public.payment USING btree (id);


--
-- Name: ix_payment_idempotency_key; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_idempotency_key ON public.payment USING btree (idempotency_key);


--
-- Name: ix_receipt_created_by; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_receipt_created_by ON public.receipt USING btree (created_by);


--
-- Name: ix_receipt_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_receipt_id ON public.receipt USING btree (id);


--
-- Name: ix_students_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_students_id ON public.students USING btree (id);


--
-- Name: ix_students_roll_number; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_students_roll_number ON public.students USING btree (roll_number);


--
-- Name: ix_user_email; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_user_email ON public."user" USING btree (email);


--
-- Name: ix_user_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_user_id ON public."user" USING btree (id);


--
-- Name: fee_assignment fee_assignment_fee_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_assignment
    ADD CONSTRAINT fee_assignment_fee_plan_id_fkey FOREIGN KEY (fee_plan_id) REFERENCES public.fee_plan(id);


--
-- Name: fee_assignment fee_assignment_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_assignment
    ADD CONSTRAINT fee_assignment_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: fee_invoice fee_invoice_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_invoice
    ADD CONSTRAINT fee_invoice_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: fee_plan_component fee_plan_component_fee_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_plan_component
    ADD CONSTRAINT fee_plan_component_fee_component_id_fkey FOREIGN KEY (fee_component_id) REFERENCES public.fee_component(id);


--
-- Name: fee_plan_component fee_plan_component_fee_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_plan_component
    ADD CONSTRAINT fee_plan_component_fee_plan_id_fkey FOREIGN KEY (fee_plan_id) REFERENCES public.fee_plan(id);


--
-- Name: receipt fk_receipt_created_by_user; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT fk_receipt_created_by_user FOREIGN KEY (created_by) REFERENCES public."user"(id);


--
-- Name: payment payment_fee_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment
    ADD CONSTRAINT payment_fee_invoice_id_fkey FOREIGN KEY (fee_invoice_id) REFERENCES public.fee_invoice(id);


--
-- Name: receipt receipt_payment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT receipt_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES public.payment(id);


--
-- Name: students students_class_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_class_section_id_fkey FOREIGN KEY (class_section_id) REFERENCES public.class_sections(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 7cLzrgb6aQuKUQEGa3h3qhaCGyGgohQNul67cgpXcL2ZjwSBPFEOe7APLdXgWaE

