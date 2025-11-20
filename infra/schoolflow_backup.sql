--
-- PostgreSQL database dump
--

\restrict Relr5M3oPsyCRDJ8fBfFzfUl2iOZ02FdE16GA76Z7Xj8YfP2YTX1ma7Rho2yGrC

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
    note character varying(255),
    invoice_id integer
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
    invoice_no character varying(64)
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
    created_by integer
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
20251108_payidempkey
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

COPY public.fee_assignment (id, student_id, fee_plan_id, concession, note, invoice_id) FROM stdin;
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
1	1	2025-04	5000.00	2025-04-15 00:00:00+00	unpaid	2025-11-11 08:37:11.760474+00	INV-1
2	2	2025-04	5000.00	2025-04-15 00:00:00+00	unpaid	2025-11-11 08:37:11.760474+00	INV-2
3	2	2025-11	1650.00	2025-11-30 14:07:12+00	paid	2025-11-11 08:37:12.657075+00	INV-AUTO-70D8A83D
4	1	2025-12	4000.00	2025-12-30 00:00:00+00	paid	2025-11-18 09:54:23.498281+00	INV-3
\.


--
-- Data for Name: fee_plan; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.fee_plan (id, name, academic_year, frequency) FROM stdin;
1	Standard-IX-2025	2025	monthly
\.


--
-- Data for Name: fee_plan_component; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.fee_plan_component (id, fee_plan_id, fee_component_id, amount) FROM stdin;
1	1	1	1200.00
2	1	2	300.00
3	1	3	150.00
\.


--
-- Data for Name: payment; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.payment (id, fee_invoice_id, provider, provider_txn_id, amount, status, idempotency_key, created_at) FROM stdin;
1	1	fake	FAKE-TXN-0001	5000.00	captured	IDEMP-0001	2025-11-11 08:37:11.825031+00
2	3	manual	manual-b51d0b094a1742a9a1d777570d5c7346	1650.00	captured	manual-b51d0b094a1742a9a1d777570d5c7346	2025-11-11 08:37:12.664716+00
3	3	fake	FAKE-TXN-3	1650.00	captured	IDEMP-3	2025-11-11 08:37:13.562287+00
4	4	fake	manual-mi636c9w-poib9i	10000.00	captured	manual-mi636c9w-poib9i	2025-11-19 14:17:03.919961+00
5	4	fake	manual-mi65btth-lz5idl	100.00	captured	manual-mi65btth-lz5idl	2025-11-19 15:17:19.163904+00
\.


--
-- Data for Name: receipt; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.receipt (id, payment_id, receipt_no, pdf_path, created_at, created_by) FROM stdin;
1	1	REC-TEST-0001	app/data/receipts/REC-TEST-0001.pdf	2025-11-11 08:37:11.888819+00	\N
2	3	REC-63EDF4F910	/app/backend/data/receipts/REC-63EDF4F910.pdf	2025-11-11 08:37:13.570234+00	1
3	4	REC-3CD91EAE50	/app/backend/data/receipts/REC-3CD91EAE50.pdf	2025-11-19 14:17:04.042936+00	1
4	5	REC-C8E833B241	/app/backend/data/receipts/REC-C8E833B241.pdf	2025-11-19 15:17:19.189249+00	1
\.


--
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.students (id, name, roll_number, class_section_id) FROM stdin;
1	Anjali Singh	1A-001	1
2	Rahul Sharma	1A-002	1
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public."user" (id, email, hashed_password, role, is_active, created_at, updated_at) FROM stdin;
1	admin@example.com	$2b$12$jVmth3yYvXaUnNGerBaOU.RxX8kMHuTpTgXCxUWkFZYnPKwQP/Nb.	admin	t	2025-11-11 08:37:11.325529+00	\N
2	testadmin@example.com	$2b$12$tTMm1bGZ.dyXlo0pwmG0/OQQAw9kAUsQ.lY.Xljbul0CUtR.9NG4m	admin	t	2025-11-11 08:37:12.134606+00	\N
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

SELECT pg_catalog.setval('public.fee_invoice_id_seq', 4, true);


--
-- Name: fee_plan_component_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.fee_plan_component_id_seq', 3, true);


--
-- Name: fee_plan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.fee_plan_id_seq', 1, true);


--
-- Name: payment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.payment_id_seq', 5, true);


--
-- Name: receipt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.receipt_id_seq', 4, true);


--
-- Name: students_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.students_id_seq', 2, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.user_id_seq', 2, true);


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
-- Name: ix_fee_assignment_invoice_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fee_assignment_invoice_id ON public.fee_assignment USING btree (invoice_id);


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
-- Name: uq_payment_idempotency_key; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX uq_payment_idempotency_key ON public.payment USING btree (idempotency_key);


--
-- Name: fee_assignment fee_assignment_fee_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_assignment
    ADD CONSTRAINT fee_assignment_fee_plan_id_fkey FOREIGN KEY (fee_plan_id) REFERENCES public.fee_plan(id);


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
-- Name: fee_assignment fk_fee_assignment_invoice_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_assignment
    ADD CONSTRAINT fk_fee_assignment_invoice_id FOREIGN KEY (invoice_id) REFERENCES public.fee_invoice(id);


--
-- Name: fee_assignment fk_fee_assignment_student_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_assignment
    ADD CONSTRAINT fk_fee_assignment_student_id FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: fee_invoice fk_fee_invoice_student_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fee_invoice
    ADD CONSTRAINT fk_fee_invoice_student_id FOREIGN KEY (student_id) REFERENCES public.students(id);


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

\unrestrict Relr5M3oPsyCRDJ8fBfFzfUl2iOZ02FdE16GA76Z7Xj8YfP2YTX1ma7Rho2yGrC

