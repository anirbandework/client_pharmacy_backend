--
-- PostgreSQL database dump
--

\restrict xy1D8ePSsbC48RUI3eeIXQacBvHcgtpZQYdFahba13VPMRpCmkFCgb8Vg3lFbrp

-- Dumped from database version 14.20 (Homebrew)
-- Dumped by pg_dump version 14.20 (Homebrew)

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
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.admins VALUES (2, 'TEST2', 'g@gmail.com', NULL, NULL, 'subham', '+913333333333', true, false, 'Demo SuperAdmin', '2026-02-20 10:20:06.006013');
INSERT INTO public.admins VALUES (3, 'TEST1', 's@gmail.com', NULL, NULL, 'ban', '+912222222222', true, false, 'Demo SuperAdmin', '2026-02-20 10:20:22.912518');
INSERT INTO public.admins VALUES (1, 'TEST1', 'a@gmail.com', '$2b$12$fsfF0ARj207.CuoYbZ2S7uJOC3tHv5updLFl55JQR8/4kaKIYV7L6', 'test@123', 'anir', '+911111111111', true, true, 'Demo SuperAdmin', '2026-02-20 10:18:57.4456');


--
-- Data for Name: shops; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.shops VALUES (1, 'TEST1', 'TEST1_SHOP1', 'TEST1_SHOP1', 'fcvgbjh', '1234567890', 'a@gmail.com', 'cfhvgbj', 'cyvjb', 'anir', NULL, NULL, true, '2026-02-20 10:21:37.826624');
INSERT INTO public.shops VALUES (2, 'TEST1', 'TEST1_SHOP2', 'TEST1_SHOP2', 'ytj', '1111111111', 'hgvh@gmail.com', 'fhgvbjh', 'cfghvg', 'anir', NULL, NULL, true, '2026-02-20 10:23:49.839982');


--
-- Data for Name: shop_wifi; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: staff; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.staff VALUES (2, 1, 'e47fdc49-1d85-42d4-8a69-659d3f5733f8', 'Chauhan2', 'Chauhan2', '+912222222222', NULL, NULL, 'a@gmail.com', 'staff', 12, '2026-02-10', 4, false, true, true, true, false, 'anir', NULL, NULL, true, '2026-02-20 10:23:09.088611', NULL);
INSERT INTO public.staff VALUES (1, 1, '223978de-6a9e-4770-a694-c9dbaba082c6', 'chauhan1', 'chauhan_1', '+911111111111', '$2b$12$o6Fh.TGkVWH81XwH40M5cuF5x7HzIs3Zk9lc1GfFasAEwWfaGySZ2', 'test@123', 'a@gmail.com', 'staff', 11997, '2026-02-03', 28, false, true, true, true, true, 'anir', NULL, NULL, true, '2026-02-20 10:22:37.044768', '2026-02-20 10:25:05.177661');


--
-- Data for Name: staff_devices; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: attendance_records; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: attendance_settings; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: bills; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.bills VALUES (1, 1, 1, 'chauhan1', 'BILL-20260220-1-0001', '', '', '', '', 'CASH', NULL, 23, 0, 1.1500000000000001, 24.15, 25, 0.8500000000000014, NULL, NULL, '2026-02-20 10:28:52.120202');


--
-- Data for Name: stock_racks; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.stock_racks VALUES (1, 1, '100', 'hfgj', 'gf hg');
INSERT INTO public.stock_racks VALUES (2, 1, '101', 'vgjhb', 'gjh');


--
-- Data for Name: stock_sections_audit; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.stock_sections_audit VALUES (1, 1, 1, '1000', 'vgjhb');
INSERT INTO public.stock_sections_audit VALUES (2, 1, 1, '1001', 'hvgjb');
INSERT INTO public.stock_sections_audit VALUES (3, 1, 2, '1000', 'chgvjb');


--
-- Data for Name: stock_items_audit; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.stock_items_audit VALUES (1, 1, 1, 'medicine1', 'hgvj', 'gjh', 'hcgvjhb', 1000, NULL, 200, 100, '2026-02-28', '', NULL, NULL, NULL, 0, '2026-02-20 10:26:51.35351', '2026-02-20 10:26:51.353516');
INSERT INTO public.stock_items_audit VALUES (3, 1, 3, 'yvg', 'fhg', 'bj', 'jhkj', 122, NULL, 1223, 1221, '2026-02-13', '', NULL, NULL, NULL, 0, '2026-02-20 10:27:51.803368', '2026-02-20 10:27:51.803383');
INSERT INTO public.stock_items_audit VALUES (2, 1, 2, 'medicine2', 'h', 'h ', 'hgvjh', 989, NULL, 102, 23, '2026-02-11', '', NULL, NULL, NULL, 0, '2026-02-20 10:27:21.942848', '2026-02-20 10:28:52.128785');


--
-- Data for Name: bill_items; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.bill_items VALUES (1, 1, 1, 2, 'medicine2', 'hgvjh', 'h', 'h ', '100', '1001', 1, 23, 23, 0, 0, 5, 2.5, 2.5, 0.5750000000000001, 0.5750000000000001, 1.1500000000000001, 24.15);


--
-- Data for Name: contact_records; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: customer_profiles; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: call_scripts; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: contact_interactions; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: contact_reminders; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: contact_uploads; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: customer_medical_conditions; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: customer_prescriptions; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: customer_visits; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: customer_purchases; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: daily_records; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.daily_records VALUES (1, 1, '2026-02-20', 1, 24.15, 24.15, 0, 0, NULL, 0, 0, 0, 1, 'chauhan1', '2026-02-20 10:29:10.987795', '2026-02-20 10:29:10.991196');


--
-- Data for Name: daily_expenses; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: purchase_invoices; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: purchase_invoice_items; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: expiry_alerts; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: feedbacks; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: item_sales; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: leave_requests; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: monthly_invoice_summary; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: notification_reads; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: notification_shop_targets; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: notification_staff_targets; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: otp_verifications; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.otp_verifications VALUES (1, '+919383169659', '999999', false, '2026-02-21 10:18:00.394815', '2026-02-20 10:18:00.418413');
INSERT INTO public.otp_verifications VALUES (2, '+911111111111', '999999', true, '2026-02-20 10:25:56.644645', '2026-02-20 10:20:56.644968');
INSERT INTO public.otp_verifications VALUES (3, '+919383169659', '999999', false, '2026-02-21 10:24:13.982997', '2026-02-20 10:24:13.989664');
INSERT INTO public.otp_verifications VALUES (4, '+911111111111', '999999', true, '2026-02-20 10:30:01.946711', '2026-02-20 10:25:01.94697');


--
-- Data for Name: prescription_medicines; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: purchases_audit; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: purchase_items_audit; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: refill_reminders; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: salary_records; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: salary_alerts; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: sales_audit; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: sale_items_audit; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: staff_members; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: staff_payment_info; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: stock_adjustments; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: stock_audit_records; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: stock_audit_sessions; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--



--
-- Data for Name: super_admins; Type: TABLE DATA; Schema: public; Owner: pharmacy_user
--

INSERT INTO public.super_admins VALUES (1, 'demo@superadmin.com', '$2b$12$57kCxcrUw.AcZffmaqZMRe5Muo7a4AVPIHgzMzAdrtE8XcQYwi8dW', 'Demo SuperAdmin', '+919383169659', true, '2026-02-20 10:18:03.637547');


--
-- Name: admins_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.admins_id_seq', 3, true);


--
-- Name: attendance_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.attendance_records_id_seq', 1, false);


--
-- Name: attendance_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.attendance_settings_id_seq', 1, false);


--
-- Name: bill_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.bill_items_id_seq', 1, true);


--
-- Name: bills_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.bills_id_seq', 1, true);


--
-- Name: call_scripts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.call_scripts_id_seq', 1, false);


--
-- Name: contact_interactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.contact_interactions_id_seq', 1, false);


--
-- Name: contact_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.contact_records_id_seq', 1, false);


--
-- Name: contact_reminders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.contact_reminders_id_seq', 1, false);


--
-- Name: contact_uploads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.contact_uploads_id_seq', 1, false);


--
-- Name: customer_medical_conditions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.customer_medical_conditions_id_seq', 1, false);


--
-- Name: customer_prescriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.customer_prescriptions_id_seq', 1, false);


--
-- Name: customer_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.customer_profiles_id_seq', 1, false);


--
-- Name: customer_purchases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.customer_purchases_id_seq', 1, false);


--
-- Name: customer_visits_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.customer_visits_id_seq', 1, false);


--
-- Name: daily_expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.daily_expenses_id_seq', 1, false);


--
-- Name: daily_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.daily_records_id_seq', 2, true);


--
-- Name: expiry_alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.expiry_alerts_id_seq', 1, false);


--
-- Name: feedbacks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.feedbacks_id_seq', 1, false);


--
-- Name: item_sales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.item_sales_id_seq', 1, false);


--
-- Name: leave_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.leave_requests_id_seq', 1, false);


--
-- Name: monthly_invoice_summary_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.monthly_invoice_summary_id_seq', 1, false);


--
-- Name: notification_reads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.notification_reads_id_seq', 1, false);


--
-- Name: notification_shop_targets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.notification_shop_targets_id_seq', 1, false);


--
-- Name: notification_staff_targets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.notification_staff_targets_id_seq', 1, false);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, false);


--
-- Name: otp_verifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.otp_verifications_id_seq', 4, true);


--
-- Name: prescription_medicines_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.prescription_medicines_id_seq', 1, false);


--
-- Name: purchase_invoice_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.purchase_invoice_items_id_seq', 1, false);


--
-- Name: purchase_invoices_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.purchase_invoices_id_seq', 1, false);


--
-- Name: purchase_items_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.purchase_items_audit_id_seq', 1, false);


--
-- Name: purchases_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.purchases_audit_id_seq', 1, false);


--
-- Name: refill_reminders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.refill_reminders_id_seq', 1, false);


--
-- Name: salary_alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.salary_alerts_id_seq', 1, false);


--
-- Name: salary_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.salary_records_id_seq', 1, false);


--
-- Name: sale_items_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.sale_items_audit_id_seq', 1, false);


--
-- Name: sales_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.sales_audit_id_seq', 1, false);


--
-- Name: shop_wifi_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.shop_wifi_id_seq', 1, false);


--
-- Name: shops_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.shops_id_seq', 2, true);


--
-- Name: staff_devices_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.staff_devices_id_seq', 1, false);


--
-- Name: staff_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.staff_id_seq', 2, true);


--
-- Name: staff_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.staff_members_id_seq', 1, false);


--
-- Name: staff_payment_info_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.staff_payment_info_id_seq', 1, false);


--
-- Name: stock_adjustments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.stock_adjustments_id_seq', 1, false);


--
-- Name: stock_audit_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.stock_audit_records_id_seq', 1, false);


--
-- Name: stock_audit_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.stock_audit_sessions_id_seq', 1, false);


--
-- Name: stock_items_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.stock_items_audit_id_seq', 3, true);


--
-- Name: stock_racks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.stock_racks_id_seq', 2, true);


--
-- Name: stock_sections_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.stock_sections_audit_id_seq', 3, true);


--
-- Name: super_admins_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pharmacy_user
--

SELECT pg_catalog.setval('public.super_admins_id_seq', 1, true);


--
-- PostgreSQL database dump complete
--

\unrestrict xy1D8ePSsbC48RUI3eeIXQacBvHcgtpZQYdFahba13VPMRpCmkFCgb8Vg3lFbrp

