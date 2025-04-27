--

-- PostgreSQL database dump

--



-- Dumped from database version 17.4

-- Dumped by pg_dump version 17.4



SET statement_timeout = 0;

SET lock_timeout = 0;

SET idle_in_transaction_session_timeout = 0;

SET transaction_timeout = 0;

SET client_encoding = 'UTF8';

SET standard_conforming_strings = on;

SELECT pg_catalog.set_config('search_path', '', false);

SET check_function_bodies = false;

SET xmloption = content;

SET client_min_messages = warning;

SET row_security = off;



--

-- Name: update_sequence_after_delete(); Type: FUNCTION; Schema: public; Owner: zhunya

--



CREATE FUNCTION public.update_sequence_after_delete() RETURNS trigger

    LANGUAGE plpgsql

    AS $$



BEGIN



    EXECUTE format('SELECT setval(''%s_%s_seq'', (SELECT COALESCE(MAX(%I), 0) + 1 FROM %I))',



                   TG_TABLE_NAME, TG_ARGV[0], TG_ARGV[0], TG_TABLE_NAME);



    RETURN NULL;



END;



$$;





ALTER FUNCTION public.update_sequence_after_delete() OWNER TO zhunya;



SET default_tablespace = '';



SET default_table_access_method = heap;



--

-- Name: app_users; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.app_users (

    user_id integer NOT NULL,

    username character varying(255) NOT NULL,

    password_hash character varying(255) NOT NULL,

    role character varying(50) NOT NULL

);





ALTER TABLE public.app_users OWNER TO zhunya;



--

-- Name: app_users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.app_users_user_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.app_users_user_id_seq OWNER TO zhunya;



--

-- Name: app_users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.app_users_user_id_seq OWNED BY public.app_users.user_id;





--

-- Name: customers; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.customers (

    customer_id integer NOT NULL,

    first_name character varying(255) NOT NULL,

    last_name character varying(255) NOT NULL,

    phone character varying(20),

    email character varying(255),

    address text

);





ALTER TABLE public.customers OWNER TO zhunya;



--

-- Name: customers_customer_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.customers_customer_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.customers_customer_id_seq OWNER TO zhunya;



--

-- Name: customers_customer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.customers_customer_id_seq OWNED BY public.customers.customer_id;





--

-- Name: employees; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.employees (

    employee_id integer NOT NULL,

    first_name character varying(255) NOT NULL,

    last_name character varying(255) NOT NULL,

    "position" character varying(255) NOT NULL,

    phone character varying(20),

    email character varying(255),

    hire_date date NOT NULL,

    salary numeric(10,2) NOT NULL

);





ALTER TABLE public.employees OWNER TO zhunya;



--

-- Name: employees_employee_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.employees_employee_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.employees_employee_id_seq OWNER TO zhunya;



--

-- Name: employees_employee_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.employees_employee_id_seq OWNED BY public.employees.employee_id;





--

-- Name: medicines; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.medicines (

    medicine_id integer NOT NULL,

    name character varying(255) NOT NULL,

    description text,

    manufacturer character varying(255),

    price numeric(10,2) NOT NULL,

    quantity_in_stock integer NOT NULL,

    expiration_date date NOT NULL,

    supplier_id integer,

    CONSTRAINT chk_price CHECK ((price > (0)::numeric)),

    CONSTRAINT chk_quantity CHECK ((quantity_in_stock >= 0))

);





ALTER TABLE public.medicines OWNER TO zhunya;



--

-- Name: medicines_medicine_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.medicines_medicine_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.medicines_medicine_id_seq OWNER TO zhunya;



--

-- Name: medicines_medicine_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.medicines_medicine_id_seq OWNED BY public.medicines.medicine_id;





--

-- Name: prescriptions; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.prescriptions (

    prescription_id integer NOT NULL,

    customer_id integer,

    medicine_id integer,

    doctor_name character varying(255) NOT NULL,

    issue_date date NOT NULL,

    expiration_date date NOT NULL,

    CONSTRAINT chk_dates CHECK ((expiration_date > issue_date))

);





ALTER TABLE public.prescriptions OWNER TO zhunya;



--

-- Name: prescriptions_prescription_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.prescriptions_prescription_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.prescriptions_prescription_id_seq OWNER TO zhunya;



--

-- Name: prescriptions_prescription_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.prescriptions_prescription_id_seq OWNED BY public.prescriptions.prescription_id;





--

-- Name: purchase_items; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.purchase_items (

    purchase_item_id integer NOT NULL,

    purchase_id integer,

    medicine_id integer,

    quantity integer NOT NULL,

    price numeric(10,2) NOT NULL

);





ALTER TABLE public.purchase_items OWNER TO zhunya;



--

-- Name: purchase_items_purchase_item_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.purchase_items_purchase_item_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.purchase_items_purchase_item_id_seq OWNER TO zhunya;



--

-- Name: purchase_items_purchase_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.purchase_items_purchase_item_id_seq OWNED BY public.purchase_items.purchase_item_id;





--

-- Name: purchases; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.purchases (

    purchase_id integer NOT NULL,

    purchase_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,

    supplier_id integer,

    total_amount numeric(10,2) NOT NULL

);





ALTER TABLE public.purchases OWNER TO zhunya;



--

-- Name: purchases_purchase_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.purchases_purchase_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.purchases_purchase_id_seq OWNER TO zhunya;



--

-- Name: purchases_purchase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.purchases_purchase_id_seq OWNED BY public.purchases.purchase_id;





--

-- Name: sale_items; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.sale_items (

    sale_item_id integer NOT NULL,

    sale_id integer,

    medicine_id integer,

    quantity integer NOT NULL,

    price numeric(10,2) NOT NULL

);





ALTER TABLE public.sale_items OWNER TO zhunya;



--

-- Name: sale_items_sale_item_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.sale_items_sale_item_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.sale_items_sale_item_id_seq OWNER TO zhunya;



--

-- Name: sale_items_sale_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.sale_items_sale_item_id_seq OWNED BY public.sale_items.sale_item_id;





--

-- Name: sales; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.sales (

    sale_id integer NOT NULL,

    sale_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,

    customer_id integer,

    employee_id integer,

    total_amount numeric(10,2) NOT NULL

);





ALTER TABLE public.sales OWNER TO zhunya;



--

-- Name: sales_sale_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.sales_sale_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.sales_sale_id_seq OWNER TO zhunya;



--

-- Name: sales_sale_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.sales_sale_id_seq OWNED BY public.sales.sale_id;





--

-- Name: suppliers; Type: TABLE; Schema: public; Owner: zhunya

--



CREATE TABLE public.suppliers (

    supplier_id integer NOT NULL,

    name character varying(255) NOT NULL,

    contact_person character varying(255),

    phone character varying(20),

    email character varying(255),

    address text

);





ALTER TABLE public.suppliers OWNER TO zhunya;



--

-- Name: suppliers_supplier_id_seq; Type: SEQUENCE; Schema: public; Owner: zhunya

--



CREATE SEQUENCE public.suppliers_supplier_id_seq

    AS integer

    START WITH 1

    INCREMENT BY 1

    NO MINVALUE

    NO MAXVALUE

    CACHE 1;





ALTER SEQUENCE public.suppliers_supplier_id_seq OWNER TO zhunya;



--

-- Name: suppliers_supplier_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zhunya

--



ALTER SEQUENCE public.suppliers_supplier_id_seq OWNED BY public.suppliers.supplier_id;





--

-- Name: app_users user_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.app_users ALTER COLUMN user_id SET DEFAULT nextval('public.app_users_user_id_seq'::regclass);





--

-- Name: customers customer_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.customers ALTER COLUMN customer_id SET DEFAULT nextval('public.customers_customer_id_seq'::regclass);





--

-- Name: employees employee_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.employees ALTER COLUMN employee_id SET DEFAULT nextval('public.employees_employee_id_seq'::regclass);





--

-- Name: medicines medicine_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.medicines ALTER COLUMN medicine_id SET DEFAULT nextval('public.medicines_medicine_id_seq'::regclass);





--

-- Name: prescriptions prescription_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.prescriptions ALTER COLUMN prescription_id SET DEFAULT nextval('public.prescriptions_prescription_id_seq'::regclass);





--

-- Name: purchase_items purchase_item_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.purchase_items ALTER COLUMN purchase_item_id SET DEFAULT nextval('public.purchase_items_purchase_item_id_seq'::regclass);





--

-- Name: purchases purchase_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.purchases ALTER COLUMN purchase_id SET DEFAULT nextval('public.purchases_purchase_id_seq'::regclass);





--

-- Name: sale_items sale_item_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.sale_items ALTER COLUMN sale_item_id SET DEFAULT nextval('public.sale_items_sale_item_id_seq'::regclass);





--

-- Name: sales sale_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.sales ALTER COLUMN sale_id SET DEFAULT nextval('public.sales_sale_id_seq'::regclass);





--

-- Name: suppliers supplier_id; Type: DEFAULT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.suppliers ALTER COLUMN supplier_id SET DEFAULT nextval('public.suppliers_supplier_id_seq'::regclass);





--

-- Data for Name: app_users; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.app_users (user_id, username, password_hash, role) FROM stdin;

1	admin	240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9	ADMIN

2	pharmacist	1c7d7f2a7668a1de0ea8f04a0ce6ff072e14781b052c51ee506a41b05d28b5cb	PHARMACIST

3	manager	866485796cfa8d7c0cf7111640205b83076433547577511d81f8030ae99ecea5	MANAGER

4	user1	58be779b29eb49f5cacaf55f1c77ef9b651c61359c0a9a956c39b33842eb3920	GUEST

\.





--

-- Data for Name: customers; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.customers (customer_id, first_name, last_name, phone, email, address) FROM stdin;

1	Анна	Иванова	+79167778899	ivanova@mail.ru	г. Москва, ул. Центральная, 10, кв. 25

2	Сергей	Фёдоров	+79168889900	fedorov@gmail.com	г. Москва, пр. Ленина, 45, кв. 12

3	Мария	Кузнецова	+79169990011	kuznetsova@yandex.ru	г. Москва, ул. Садовая, 7, кв. 34

4	Алексей	Смирнов	+79160001122	smirnov@mail.ru	г. Москва, ул. Парковая, 22, кв. 18

5	Екатерина	Попова	+79161112233	popova@gmail.com	г. Москва, ул. Школьная, 3, кв. 9

\.





--

-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.employees (employee_id, first_name, last_name, "position", phone, email, hire_date, salary) FROM stdin;

1	Ольга	Васильева	Администратор	+79161112233	vasilieva@pharmacy.ru	2018-05-10	65000.00

2	Александр	Петров	Фармацевт	+79162223344	petrov@pharmacy.ru	2019-11-15	55000.00

3	Елена	Соколова	Менеджер	+79163334455	sokolova@pharmacy.ru	2020-03-22	60000.00

4	Дмитрий	Козлов	Менеджер	+79164445566	kozlov@pharmacy.ru	2019-07-30	58000.00

5	Ирина	Николаева	Главный фармацевт	+79165556677	nikolaeva@pharmacy.ru	2021-01-12	48000.00

\.





--

-- Data for Name: medicines; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.medicines (medicine_id, name, description, manufacturer, price, quantity_in_stock, expiration_date, supplier_id) FROM stdin;

1	Парацетамол	Жаропонижающее и обезболивающее средство	Фармстандарт	50.00	100	2025-12-31	1

2	Ибупрофен	Противовоспалительное и обезболивающее средство	Биохимик	120.00	75	2024-10-15	2

3	Амоксициллин	Антибиотик широкого спектра действия	Синтез	350.00	50	2024-08-20	3

4	Лоратадин	Антигистаминное средство от аллергии	Вертекс	180.00	60	2025-05-30	4

5	Эналаприл	Гипотензивное средство	Озон	220.00	40	2025-02-28	5

6	Аспирин	Обезболивающее, жаропонижающее средство	Байер	90.00	120	2024-12-31	1

7	Умепразол	Средство от язвы желудка	Вева	280.00	35	2025-07-15	2

8	Цитрамон	Комбинированное обезболивающее средство	Фармстандарт	70.00	80	2024-11-30	3

9	Активированный уголь	Энтеросорбент	Обновление	40.00	140	2026-01-31	4

10	Валидол	Средство при стенокардии	Медисорб	60.00	90	2025-09-30	5

\.





--

-- Data for Name: prescriptions; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.prescriptions (prescription_id, customer_id, medicine_id, doctor_name, issue_date, expiration_date) FROM stdin;

1	1	3	Иванова В.Р.	2023-05-10	2023-11-10

2	2	4	Петров Б.Ш.	2023-06-15	2023-12-15

3	3	7	Сидорова Х.Т.	2023-07-20	2024-01-20

4	4	5	Кузнецова Р.Я.	2023-08-05	2024-02-05

5	1	2	Иванова В.Р.	2023-09-12	2024-03-12

\.





--

-- Data for Name: purchase_items; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.purchase_items (purchase_item_id, purchase_id, medicine_id, quantity, price) FROM stdin;

1	1	1	100	45.00

2	1	6	50	80.00

3	2	2	70	110.00

4	2	7	25	250.00

5	3	3	50	320.00

6	3	8	40	60.00

7	4	4	60	160.00

8	4	9	75	35.00

9	5	5	40	200.00

10	5	10	50	50.00

11	6	1	50	48.00

12	6	6	30	85.00

13	7	2	40	115.00

14	7	7	15	270.00

\.





--

-- Data for Name: purchases; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.purchases (purchase_id, purchase_date, supplier_id, total_amount) FROM stdin;

1	2023-01-15 10:30:00	1	5000.00

2	2023-02-20 11:45:00	2	8400.00

3	2023-03-10 09:15:00	3	17500.00

4	2023-04-05 14:20:00	4	10800.00

5	2023-05-12 16:30:00	5	6000.00

6	2025-04-16 00:00:00	1	4950.00

7	2025-04-23 00:00:00	2	8650.00

8	2025-05-09 00:00:00	3	9800.00

\.





--

-- Data for Name: sale_items; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.sale_items (sale_item_id, sale_id, medicine_id, quantity, price) FROM stdin;

1	1	1	2	50.00

2	1	3	1	350.00

3	2	4	1	180.00

4	2	6	1	90.00

5	3	2	3	120.00

6	3	7	1	280.00

7	4	5	1	220.00

8	5	8	2	70.00

9	5	10	1	60.00

10	6	1	2	50.00

11	6	2	1	120.00

12	7	3	1	350.00

13	7	4	2	180.00

14	8	5	1	220.00

15	8	6	3	90.00

16	9	7	1	280.00

17	9	8	2	70.00

18	10	9	5	40.00

19	10	10	1	60.00

20	11	1	4	50.00

21	11	3	1	350.00

22	12	2	2	120.00

23	12	4	1	180.00

24	13	5	1	220.00

25	13	7	1	280.00

26	14	9	5	40.00

28	16	9	5	40.00

\.





--

-- Data for Name: sales; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.sales (sale_id, sale_date, customer_id, employee_id, total_amount) FROM stdin;

1	2023-05-15 12:30:00	1	1	400.00

2	2023-05-16 14:45:00	2	2	240.00

3	2023-05-17 10:15:00	3	3	630.00

4	2023-05-18 16:20:00	4	1	220.00

5	2023-05-19 11:30:00	5	2	170.00

6	2025-04-08 00:00:00	1	1	220.00

7	2025-04-06 00:00:00	2	2	710.00

8	2025-04-04 00:00:00	3	3	490.00

9	2025-03-30 00:00:00	4	1	420.00

10	2025-03-25 00:00:00	5	2	260.00

11	2025-03-20 00:00:00	1	3	550.00

12	2025-03-15 00:00:00	2	1	420.00

13	2025-03-11 00:00:00	3	2	500.00

14	2025-04-09 02:53:01.479841	1	1	200.00

16	2025-04-23 15:09:11.534624	4	2	200.00

\.





--

-- Data for Name: suppliers; Type: TABLE DATA; Schema: public; Owner: zhunya

--



COPY public.suppliers (supplier_id, name, contact_person, phone, email, address) FROM stdin;

1	Фармакор	Иванов Пётр	+79111234567	sales@pharmacor.ru	г. Москва, ул. Промышленная, 15

2	Медпрепараты	Сидорова Анна	+79217654321	info@medprep.ru	г. Санкт-Петербург, пр. Наук, 42

3	Биофарм	Кузнецов Дмитрий	+79035556677	supply@biofarm.com	г. Новосибирск, ул. Академическая, 7

4	Здоровье+	Петрова Мария	+79184448899	contact@zdorovie-plus.ru	г. Казань, ул. Лесная, 33

5	Аптекарь	Смирнов Алексей	+79213332211	order@aptekar.org	г. Екатеринбург, ул. Водопроводная, 19

\.





--

-- Name: app_users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.app_users_user_id_seq', 5, true);





--

-- Name: customers_customer_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.customers_customer_id_seq', 5, true);





--

-- Name: employees_employee_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.employees_employee_id_seq', 5, true);





--

-- Name: medicines_medicine_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.medicines_medicine_id_seq', 11, true);





--

-- Name: prescriptions_prescription_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.prescriptions_prescription_id_seq', 5, true);





--

-- Name: purchase_items_purchase_item_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.purchase_items_purchase_item_id_seq', 15, true);





--

-- Name: purchases_purchase_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.purchases_purchase_id_seq', 9, true);





--

-- Name: sale_items_sale_item_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.sale_items_sale_item_id_seq', 28, true);





--

-- Name: sales_sale_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.sales_sale_id_seq', 16, true);





--

-- Name: suppliers_supplier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zhunya

--



SELECT pg_catalog.setval('public.suppliers_supplier_id_seq', 6, true);





--

-- Name: app_users app_users_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.app_users

    ADD CONSTRAINT app_users_pkey PRIMARY KEY (user_id);





--

-- Name: app_users app_users_username_key; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.app_users

    ADD CONSTRAINT app_users_username_key UNIQUE (username);





--

-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.customers

    ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id);





--

-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.employees

    ADD CONSTRAINT employees_pkey PRIMARY KEY (employee_id);





--

-- Name: medicines medicines_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.medicines

    ADD CONSTRAINT medicines_pkey PRIMARY KEY (medicine_id);





--

-- Name: prescriptions prescriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.prescriptions

    ADD CONSTRAINT prescriptions_pkey PRIMARY KEY (prescription_id);





--

-- Name: purchase_items purchase_items_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.purchase_items

    ADD CONSTRAINT purchase_items_pkey PRIMARY KEY (purchase_item_id);





--

-- Name: purchases purchases_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.purchases

    ADD CONSTRAINT purchases_pkey PRIMARY KEY (purchase_id);





--

-- Name: sale_items sale_items_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.sale_items

    ADD CONSTRAINT sale_items_pkey PRIMARY KEY (sale_item_id);





--

-- Name: sales sales_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.sales

    ADD CONSTRAINT sales_pkey PRIMARY KEY (sale_id);





--

-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.suppliers

    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (supplier_id);





--

-- Name: idx_medicines_supplier; Type: INDEX; Schema: public; Owner: zhunya

--



CREATE INDEX idx_medicines_supplier ON public.medicines USING btree (supplier_id);





--

-- Name: idx_prescriptions_customer; Type: INDEX; Schema: public; Owner: zhunya

--



CREATE INDEX idx_prescriptions_customer ON public.prescriptions USING btree (customer_id);





--

-- Name: idx_prescriptions_medicine; Type: INDEX; Schema: public; Owner: zhunya

--



CREATE INDEX idx_prescriptions_medicine ON public.prescriptions USING btree (medicine_id);





--

-- Name: idx_purchase_items_medicine; Type: INDEX; Schema: public; Owner: zhunya

--



CREATE INDEX idx_purchase_items_medicine ON public.purchase_items USING btree (medicine_id);





--

-- Name: idx_purchases_supplier; Type: INDEX; Schema: public; Owner: zhunya

--



CREATE INDEX idx_purchases_supplier ON public.purchases USING btree (supplier_id);





--

-- Name: idx_sale_items_medicine; Type: INDEX; Schema: public; Owner: zhunya

--



CREATE INDEX idx_sale_items_medicine ON public.sale_items USING btree (medicine_id);





--

-- Name: idx_sales_customer; Type: INDEX; Schema: public; Owner: zhunya

--



CREATE INDEX idx_sales_customer ON public.sales USING btree (customer_id);





--

-- Name: idx_sales_employee; Type: INDEX; Schema: public; Owner: zhunya

--



CREATE INDEX idx_sales_employee ON public.sales USING btree (employee_id);





--

-- Name: app_users trg_app_users_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_app_users_after_delete AFTER DELETE ON public.app_users FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('user_id');





--

-- Name: customers trg_customers_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_customers_after_delete AFTER DELETE ON public.customers FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('customer_id');





--

-- Name: employees trg_employees_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_employees_after_delete AFTER DELETE ON public.employees FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('employee_id');





--

-- Name: medicines trg_medicines_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_medicines_after_delete AFTER DELETE ON public.medicines FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('medicine_id');





--

-- Name: prescriptions trg_prescriptions_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_prescriptions_after_delete AFTER DELETE ON public.prescriptions FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('prescription_id');





--

-- Name: purchase_items trg_purchase_items_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_purchase_items_after_delete AFTER DELETE ON public.purchase_items FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('purchase_item_id');





--

-- Name: purchases trg_purchases_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_purchases_after_delete AFTER DELETE ON public.purchases FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('purchase_id');





--

-- Name: sale_items trg_sale_items_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_sale_items_after_delete AFTER DELETE ON public.sale_items FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('sale_item_id');





--

-- Name: sales trg_sales_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_sales_after_delete AFTER DELETE ON public.sales FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('sale_id');





--

-- Name: suppliers trg_suppliers_after_delete; Type: TRIGGER; Schema: public; Owner: zhunya

--



CREATE TRIGGER trg_suppliers_after_delete AFTER DELETE ON public.suppliers FOR EACH ROW EXECUTE FUNCTION public.update_sequence_after_delete('supplier_id');





--

-- Name: medicines medicines_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.medicines

    ADD CONSTRAINT medicines_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(supplier_id);





--

-- Name: prescriptions prescriptions_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.prescriptions

    ADD CONSTRAINT prescriptions_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);





--

-- Name: prescriptions prescriptions_medicine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.prescriptions

    ADD CONSTRAINT prescriptions_medicine_id_fkey FOREIGN KEY (medicine_id) REFERENCES public.medicines(medicine_id);





--

-- Name: purchase_items purchase_items_medicine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.purchase_items

    ADD CONSTRAINT purchase_items_medicine_id_fkey FOREIGN KEY (medicine_id) REFERENCES public.medicines(medicine_id);





--

-- Name: purchase_items purchase_items_purchase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.purchase_items

    ADD CONSTRAINT purchase_items_purchase_id_fkey FOREIGN KEY (purchase_id) REFERENCES public.purchases(purchase_id);





--

-- Name: purchases purchases_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.purchases

    ADD CONSTRAINT purchases_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(supplier_id);





--

-- Name: sale_items sale_items_medicine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.sale_items

    ADD CONSTRAINT sale_items_medicine_id_fkey FOREIGN KEY (medicine_id) REFERENCES public.medicines(medicine_id);





--

-- Name: sale_items sale_items_sale_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.sale_items

    ADD CONSTRAINT sale_items_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES public.sales(sale_id);





--

-- Name: sales sales_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.sales

    ADD CONSTRAINT sales_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);





--

-- Name: sales sales_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: zhunya

--



ALTER TABLE ONLY public.sales

    ADD CONSTRAINT sales_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id);





--

-- PostgreSQL database dump complete

--



