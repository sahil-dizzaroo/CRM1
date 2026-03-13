--
-- PostgreSQL database dump
--

\restrict aW6UP0n6LoSjFb7i72yUFVNfCGCeo4L64AperUPPeJOd05Gkc7xWgciLq4vKY4u

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

-- Started on 2026-03-11 14:05:03

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
--SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 880 (class 1247 OID 17633)
-- Name: accesstype; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.accesstype AS ENUM (
    'READ',
    'WRITE',
    'ADMIN'
);


ALTER TYPE public.accesstype OWNER TO crm_user;

--
-- TOC entry 883 (class 1247 OID 17640)
-- Name: agreement_status; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.agreement_status AS ENUM (
    'DRAFT',
    'UNDER_REVIEW',
    'UNDER_NEGOTIATION',
    'READY_FOR_SIGNATURE',
    'SENT_FOR_SIGNATURE',
    'EXECUTED',
    'CLOSED'
);


ALTER TYPE public.agreement_status OWNER TO crm_user;

--
-- TOC entry 886 (class 1247 OID 17656)
-- Name: comment_type; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.comment_type AS ENUM (
    'INTERNAL',
    'EXTERNAL',
    'SYSTEM'
);


ALTER TYPE public.comment_type OWNER TO crm_user;

--
-- TOC entry 889 (class 1247 OID 17664)
-- Name: document_category; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.document_category AS ENUM (
    'investigator_cv',
    'signed_cda',
    'cta',
    'irb_package',
    'feasibility_questionnaire',
    'feasibility_response',
    'onsite_visit_report',
    'site_visibility_report',
    'other'
);


ALTER TYPE public.document_category OWNER TO crm_user;

--
-- TOC entry 892 (class 1247 OID 17684)
-- Name: document_type; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.document_type AS ENUM (
    'sponsor',
    'site'
);


ALTER TYPE public.document_type OWNER TO crm_user;

--
-- TOC entry 895 (class 1247 OID 17690)
-- Name: messagechannel; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.messagechannel AS ENUM (
    'SMS',
    'WHATSAPP',
    'EMAIL'
);


ALTER TYPE public.messagechannel OWNER TO crm_user;

--
-- TOC entry 898 (class 1247 OID 17698)
-- Name: messagedirection; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.messagedirection AS ENUM (
    'INBOUND',
    'OUTBOUND'
);


ALTER TYPE public.messagedirection OWNER TO crm_user;

--
-- TOC entry 901 (class 1247 OID 17704)
-- Name: messagestatus; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.messagestatus AS ENUM (
    'QUEUED',
    'SENT',
    'DELIVERED',
    'FAILED'
);


ALTER TYPE public.messagestatus OWNER TO crm_user;

--
-- TOC entry 904 (class 1247 OID 17714)
-- Name: review_status; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.review_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);


ALTER TYPE public.review_status OWNER TO crm_user;

--
-- TOC entry 907 (class 1247 OID 17722)
-- Name: site_primary_status; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.site_primary_status AS ENUM (
    'UNDER_EVALUATION',
    'STARTUP',
    'INITIATING',
    'INITIATED_NOT_RECRUITING',
    'RECRUITING',
    'ACTIVE_NOT_RECRUITING',
    'COMPLETED',
    'SUSPENDED',
    'TERMINATED',
    'WITHDRAWN',
    'CLOSED'
);


ALTER TYPE public.site_primary_status OWNER TO crm_user;

--
-- TOC entry 910 (class 1247 OID 17746)
-- Name: step_status; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.step_status AS ENUM (
    'not_started',
    'in_progress',
    'completed',
    'locked'
);


ALTER TYPE public.step_status OWNER TO crm_user;

--
-- TOC entry 913 (class 1247 OID 17756)
-- Name: template_type; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.template_type AS ENUM (
    'CDA',
    'CTA',
    'BUDGET',
    'OTHER'
);


ALTER TYPE public.template_type OWNER TO crm_user;

--
-- TOC entry 916 (class 1247 OID 17766)
-- Name: userrole; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.userrole AS ENUM (
    'SPONSOR',
    'SITE_MANAGER',
    'COORDINATOR',
    'PARTICIPANT',
    'cra',
    'study_manager',
    'medical_monitor'
);


ALTER TYPE public.userrole OWNER TO crm_user;

--
-- TOC entry 919 (class 1247 OID 17782)
-- Name: workflow_step_name; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.workflow_step_name AS ENUM (
    'site_identification',
    'cda_execution',
    'feasibility',
    'site_selection_outcome',
    'agreement_executed'
);


ALTER TYPE public.workflow_step_name OWNER TO crm_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 17793)
-- Name: agreement_comments; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.agreement_comments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agreement_id uuid NOT NULL,
    version_id uuid,
    comment_type public.comment_type NOT NULL,
    content text NOT NULL,
    created_by character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.agreement_comments OWNER TO crm_user;

--
-- TOC entry 220 (class 1259 OID 17804)
-- Name: agreement_documents; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.agreement_documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agreement_id uuid NOT NULL,
    version_number integer NOT NULL,
    document_html text,
    created_from_template_id uuid,
    created_by character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_signed_version character varying(10) DEFAULT 'false'::character varying NOT NULL,
    document_content jsonb,
    document_file_path text,
    CONSTRAINT chk_agreement_document_is_signed CHECK (((is_signed_version)::text = ANY (ARRAY[('true'::character varying)::text, ('false'::character varying)::text])))
);


ALTER TABLE public.agreement_documents OWNER TO crm_user;

--
-- TOC entry 221 (class 1259 OID 17817)
-- Name: agreement_inline_comments; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.agreement_inline_comments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agreement_id uuid NOT NULL,
    document_id uuid NOT NULL,
    comment_text text NOT NULL,
    position_reference jsonb,
    comment_type public.comment_type NOT NULL,
    created_by character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.agreement_inline_comments OWNER TO crm_user;

--
-- TOC entry 222 (class 1259 OID 17829)
-- Name: agreement_signed_documents; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.agreement_signed_documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agreement_id uuid NOT NULL,
    file_path character varying(500) NOT NULL,
    signed_at timestamp with time zone,
    downloaded_from_zoho_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    zoho_request_id character varying(255)
);


ALTER TABLE public.agreement_signed_documents OWNER TO crm_user;

--
-- TOC entry 223 (class 1259 OID 17839)
-- Name: agreements; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.agreements (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    site_id uuid NOT NULL,
    title character varying(500) NOT NULL,
    status public.agreement_status DEFAULT 'DRAFT'::public.agreement_status NOT NULL,
    created_by character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_legacy character varying(10) DEFAULT 'false'::character varying NOT NULL,
    zoho_request_id character varying(255),
    signature_status character varying(50),
    study_id uuid,
    agreement_type public.template_type,
    study_site_id uuid
);


ALTER TABLE public.agreements OWNER TO crm_user;

--
-- TOC entry 224 (class 1259 OID 17854)
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.audit_logs (
    id uuid NOT NULL,
    "user" character varying(100),
    action character varying(100) NOT NULL,
    target_type character varying(50) NOT NULL,
    target_id character varying(100) NOT NULL,
    details json,
    "timestamp" timestamp with time zone DEFAULT now()
);


ALTER TABLE public.audit_logs OWNER TO crm_user;

--
-- TOC entry 225 (class 1259 OID 17864)
-- Name: chat_documents; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.chat_documents (
    id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    filename character varying(255) NOT NULL,
    content_type character varying(100) NOT NULL,
    size integer NOT NULL,
    uploaded_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.chat_documents OWNER TO crm_user;

--
-- TOC entry 226 (class 1259 OID 17876)
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.chat_messages (
    id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    mode character varying(20) NOT NULL,
    document_id uuid,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.chat_messages OWNER TO crm_user;

--
-- TOC entry 227 (class 1259 OID 17887)
-- Name: conversation_access; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.conversation_access (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    access_type public.accesstype NOT NULL,
    granted_by character varying(255),
    granted_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.conversation_access OWNER TO crm_user;

--
-- TOC entry 228 (class 1259 OID 17897)
-- Name: events; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.events (
    id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    event_name character varying(500) NOT NULL,
    internal_external character varying(20) NOT NULL,
    event_type character varying(100),
    date_of_event timestamp with time zone,
    event_description text,
    event_report text,
    relevant_internal_stakeholders json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.events OWNER TO crm_user;

--
-- TOC entry 229 (class 1259 OID 17908)
-- Name: feasibility_attachments; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.feasibility_attachments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    study_site_id uuid NOT NULL,
    file_path character varying(500) NOT NULL,
    file_name character varying(255) NOT NULL,
    content_type character varying(100) NOT NULL,
    size integer NOT NULL,
    uploaded_by character varying(255),
    uploaded_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.feasibility_attachments OWNER TO crm_user;

--
-- TOC entry 230 (class 1259 OID 17921)
-- Name: feasibility_requests; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.feasibility_requests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    study_site_id uuid NOT NULL,
    email character varying(255) NOT NULL,
    token character varying(255) NOT NULL,
    status character varying(50) DEFAULT 'sent'::character varying NOT NULL,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.feasibility_requests OWNER TO crm_user;

--
-- TOC entry 231 (class 1259 OID 17935)
-- Name: feasibility_responses; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.feasibility_responses (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    request_id uuid NOT NULL,
    question_text text NOT NULL,
    question_id uuid,
    answer text NOT NULL,
    section character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.feasibility_responses OWNER TO crm_user;

--
-- TOC entry 232 (class 1259 OID 17946)
-- Name: iis_studies; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.iis_studies (
    id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    study_title character varying(500) NOT NULL,
    asset character varying(255),
    indication character varying(255),
    phases character varying(50),
    enrollment integer,
    enrollment_start_date timestamp with time zone,
    completion_date timestamp with time zone,
    other_associated_hcp_ids json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.iis_studies OWNER TO crm_user;

--
-- TOC entry 233 (class 1259 OID 17956)
-- Name: project_feasibility_custom_questions; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.project_feasibility_custom_questions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    study_id uuid NOT NULL,
    workflow_step character varying(50) DEFAULT 'feasibility'::character varying NOT NULL,
    question_text text NOT NULL,
    section character varying(255),
    expected_response_type character varying(50),
    display_order integer DEFAULT 0 NOT NULL,
    created_by character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.project_feasibility_custom_questions OWNER TO crm_user;

--
-- TOC entry 234 (class 1259 OID 17971)
-- Name: rd_studies; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.rd_studies (
    id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    study_title character varying(500) NOT NULL,
    nct_number character varying(50),
    asset character varying(255),
    indication character varying(255),
    enrollment integer,
    phases character varying(50),
    start_date timestamp with time zone,
    completion_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.rd_studies OWNER TO crm_user;

--
-- TOC entry 235 (class 1259 OID 17981)
-- Name: site_documents; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.site_documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    site_id uuid NOT NULL,
    category public.document_category NOT NULL,
    file_path character varying(500) NOT NULL,
    file_name character varying(255) NOT NULL,
    content_type character varying(100) NOT NULL,
    size integer NOT NULL,
    uploaded_by character varying(255),
    uploaded_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    description text,
    metadata jsonb DEFAULT '{}'::jsonb,
    document_type public.document_type DEFAULT 'site'::public.document_type,
    review_status public.review_status DEFAULT 'pending'::public.review_status,
    tmf_filed character varying(10) DEFAULT 'false'::character varying NOT NULL
);


ALTER TABLE public.site_documents OWNER TO crm_user;

--
-- TOC entry 236 (class 1259 OID 18000)
-- Name: site_profiles; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.site_profiles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    site_id uuid NOT NULL,
    site_name character varying(500),
    hospital_name character varying(500),
    pi_name character varying(255),
    pi_email character varying(255),
    pi_phone character varying(50),
    primary_contracting_entity character varying(500),
    authorized_signatory_name character varying(255),
    authorized_signatory_email character varying(255),
    authorized_signatory_title character varying(255),
    address_line_1 character varying(500),
    city character varying(255),
    state character varying(255),
    country character varying(255),
    postal_code character varying(50),
    site_coordinator_name character varying(255),
    site_coordinator_email character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.site_profiles OWNER TO crm_user;

--
-- TOC entry 237 (class 1259 OID 18010)
-- Name: site_status_history; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.site_status_history (
    id uuid NOT NULL,
    site_id uuid NOT NULL,
    status public.site_primary_status NOT NULL,
    previous_status public.site_primary_status,
    metadata json,
    triggering_event character varying(100),
    reason text,
    changed_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.site_status_history OWNER TO crm_user;

--
-- TOC entry 238 (class 1259 OID 18019)
-- Name: site_statuses; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.site_statuses (
    id uuid NOT NULL,
    site_id uuid NOT NULL,
    current_status public.site_primary_status NOT NULL,
    previous_status public.site_primary_status,
    metadata json,
    effective_at timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.site_statuses OWNER TO crm_user;

--
-- TOC entry 239 (class 1259 OID 18030)
-- Name: site_workflow_steps; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.site_workflow_steps (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    site_id uuid,
    step_name public.workflow_step_name NOT NULL,
    status public.step_status DEFAULT 'not_started'::public.step_status NOT NULL,
    step_data jsonb DEFAULT '{}'::jsonb,
    completed_at timestamp with time zone,
    completed_by character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    study_site_id uuid
);


ALTER TABLE public.site_workflow_steps OWNER TO crm_user;

--
-- TOC entry 240 (class 1259 OID 18043)
-- Name: sites; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.sites (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    site_id character varying(100) NOT NULL,
    name character varying(500) NOT NULL,
    code character varying(100),
    location character varying(500),
    principal_investigator character varying(255),
    address text,
    city character varying(255),
    country character varying(255),
    status character varying(50),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.sites OWNER TO crm_user;

--
-- TOC entry 241 (class 1259 OID 18054)
-- Name: studies; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.studies (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    study_id character varying(100) NOT NULL,
    name character varying(500) NOT NULL,
    description text,
    status character varying(50),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.studies OWNER TO crm_user;

--
-- TOC entry 242 (class 1259 OID 18065)
-- Name: study_sites; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.study_sites (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    study_id uuid NOT NULL,
    site_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.study_sites OWNER TO crm_user;

--
-- TOC entry 243 (class 1259 OID 18074)
-- Name: study_templates; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.study_templates (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    study_id uuid NOT NULL,
    template_name character varying(255) NOT NULL,
    template_type public.template_type NOT NULL,
    document_html text,
    created_by character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_active character varying(10) DEFAULT 'true'::character varying NOT NULL,
    template_content jsonb,
    placeholder_config json,
    template_file_path text,
    field_mappings json,
    CONSTRAINT chk_study_template_is_active CHECK (((is_active)::text = ANY (ARRAY[('true'::character varying)::text, ('false'::character varying)::text])))
);


ALTER TABLE public.study_templates OWNER TO crm_user;

--
-- TOC entry 244 (class 1259 OID 18089)
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.user_profiles (
    id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    name character varying(255),
    address text,
    phone character varying(50),
    email character varying(255),
    affiliation character varying(500),
    specialty character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.user_profiles OWNER TO crm_user;

--
-- TOC entry 245 (class 1259 OID 18098)
-- Name: user_role_assignments; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.user_role_assignments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying(255) NOT NULL,
    role public.userrole NOT NULL,
    site_id uuid,
    study_id uuid,
    assigned_by character varying(255),
    assigned_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_role_type CHECK ((role = ANY (ARRAY['cra'::public.userrole, 'study_manager'::public.userrole, 'medical_monitor'::public.userrole])))
);


ALTER TABLE public.user_role_assignments OWNER TO crm_user;

--
-- TOC entry 246 (class 1259 OID 18111)
-- Name: user_sites; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.user_sites (
    id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    site_id uuid NOT NULL,
    role character varying(50),
    assigned_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.user_sites OWNER TO crm_user;

--
-- TOC entry 247 (class 1259 OID 18118)
-- Name: users; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    name character varying(255),
    email character varying(255),
    password_hash character varying(255),
    role public.userrole NOT NULL,
    is_privileged character varying(10) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO crm_user;

--
-- TOC entry 5391 (class 0 OID 17793)
-- Dependencies: 219
-- Data for Name: agreement_comments; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.agreement_comments (id, agreement_id, version_id, comment_type, content, created_by, created_at) FROM stdin;
d6d93826-90dc-4946-9610-229e80007086	9e97dd2f-4c67-4aae-a51f-fb14b51debaf	\N	SYSTEM	Agreement draft created from template 'Second Missing Blob Template'	\N	2026-03-09 09:32:14.246132+05:30
b88a4cdc-2bbb-495f-a8d7-14e60b3411da	9e97dd2f-4c67-4aae-a51f-fb14b51debaf	\N	SYSTEM	Agreement draft created from template 'Second Missing Blob Template'	\N	2026-03-09 09:50:53.377379+05:30
5ebc3cb8-9d40-4dfe-87c8-3a155d9ef9ae	ab030b35-2150-4ce0-8342-6e8dc9f105af	\N	SYSTEM	Agreement draft created from template 'versioning'	\N	2026-03-11 11:55:38.075374+05:30
71e225b6-0b5b-4411-a5b1-da0dd7129a8e	ab030b35-2150-4ce0-8342-6e8dc9f105af	\N	SYSTEM	Version 2 created after ONLYOFFICE save.	\N	2026-03-11 11:57:25.306509+05:30
54b71d59-cbf4-4783-a1c6-60f873cb71eb	ab030b35-2150-4ce0-8342-6e8dc9f105af	\N	SYSTEM	Version 3 created after ONLYOFFICE save.	\N	2026-03-11 11:58:13.765558+05:30
\.


--
-- TOC entry 5392 (class 0 OID 17804)
-- Dependencies: 220
-- Data for Name: agreement_documents; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.agreement_documents (id, agreement_id, version_number, document_html, created_from_template_id, created_by, created_at, is_signed_version, document_content, document_file_path) FROM stdin;
5337a862-7d62-45d6-b87c-7c446507f02c	9e97dd2f-4c67-4aae-a51f-fb14b51debaf	1		58f7b845-eec9-4fa6-a5a2-46d895f2d975	testuser2	2026-03-09 09:50:53.377379+05:30	false	null	uploads\\agreements\\9e97dd2f-4c67-4aae-a51f-fb14b51debaf\\version_1_7144b222-4d60-47f9-8ea6-e48a1a93dd24.docx
42784bf8-a2c3-4175-9079-36f0dabc552f	ab030b35-2150-4ce0-8342-6e8dc9f105af	1		fccf1287-9361-4be3-b6fc-8c979e60c2c5	001	2026-03-11 11:55:38.075374+05:30	false	null	uploads\\agreements\\ab030b35-2150-4ce0-8342-6e8dc9f105af\\version_1_4025b0c8-00b0-45e5-a2cd-d261bb545eb2.docx
92e03c19-ed67-4977-951f-d864f682b939	ab030b35-2150-4ce0-8342-6e8dc9f105af	2		\N	001	2026-03-11 11:57:25.306509+05:30	false	\N	uploads\\agreements\\ab030b35-2150-4ce0-8342-6e8dc9f105af\\version_2_eac51010-bd5b-455d-a093-d751cb049afd.docx
89a31519-309f-4764-86de-f8a719121403	ab030b35-2150-4ce0-8342-6e8dc9f105af	3		\N	001	2026-03-11 11:58:13.765558+05:30	false	\N	uploads\\agreements\\ab030b35-2150-4ce0-8342-6e8dc9f105af\\version_3_93a80228-56d9-4162-b828-73c120949559.docx
\.


--
-- TOC entry 5393 (class 0 OID 17817)
-- Dependencies: 221
-- Data for Name: agreement_inline_comments; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.agreement_inline_comments (id, agreement_id, document_id, comment_text, position_reference, comment_type, created_by, created_at) FROM stdin;
\.


--
-- TOC entry 5394 (class 0 OID 17829)
-- Dependencies: 222
-- Data for Name: agreement_signed_documents; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.agreement_signed_documents (id, agreement_id, file_path, signed_at, downloaded_from_zoho_at, zoho_request_id) FROM stdin;
\.


--
-- TOC entry 5395 (class 0 OID 17839)
-- Dependencies: 223
-- Data for Name: agreements; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.agreements (id, site_id, title, status, created_by, created_at, updated_at, is_legacy, zoho_request_id, signature_status, study_id, agreement_type, study_site_id) FROM stdin;
9e97dd2f-4c67-4aae-a51f-fb14b51debaf	f801bc3d-1c18-4903-982b-57b28dffd1a4	testing feature	DRAFT	001	2026-02-17 15:05:06.310971+05:30	2026-02-27 09:23:17.550027+05:30	false	\N	\N	f7984413-4268-4720-a3ab-00f5b4044864	\N	45a872ba-8ff7-45a1-95b6-9badf41b0087
2d04e394-6918-45a4-b266-72be3b8aa5a6	f801bc3d-1c18-4903-982b-57b28dffd1a4	CDA testing	DRAFT	001	2026-02-27 10:58:30.863945+05:30	2026-02-27 12:31:35.332511+05:30	false	\N	\N	23b3f254-ae38-4d3f-8a0d-33d654a7f8a0	CDA	75614010-992a-4183-8bfb-6e3a6a7a0bb1
ab030b35-2150-4ce0-8342-6e8dc9f105af	f801bc3d-1c18-4903-982b-57b28dffd1a4	CDA	DRAFT	001	2026-02-27 10:41:28.667824+05:30	2026-03-09 10:54:23.550765+05:30	false	\N	\N	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	CDA	dbded13f-074b-44da-bacf-c2cc39b02d2b
\.


--
-- TOC entry 5396 (class 0 OID 17854)
-- Dependencies: 224
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.audit_logs (id, "user", action, target_type, target_id, details, "timestamp") FROM stdin;
b355a37a-f9ae-47bb-8729-c3a05cffa008	\N	message_created	message	899e19a6-e77a-490b-a913-94e4676c5e3e	{"conversation_id": "a2f575f1-caf7-44bb-9e69-7d3ec3215a36", "channel": "email"}	2026-01-07 21:48:16.528723+05:30
0b5f3dd5-eb43-4cec-95cf-8ce8935b00df	\N	message_created	message	71b1b44f-7524-46bc-a805-df553ee28a9a	{"conversation_id": "a2f575f1-caf7-44bb-9e69-7d3ec3215a36", "channel": "email"}	2026-01-07 22:11:39.381367+05:30
06107a2e-856f-4b66-934a-b1ce01b0eb77	\N	message_created	message	8e5137ad-3f58-4c2b-8c42-bc7888a790d3	{"conversation_id": "abb988ef-7db6-4cdc-bf84-357856a6ef17", "channel": "email"}	2026-01-07 22:21:49.333376+05:30
02634a68-84f8-48f9-9dd0-265b6a8793e7	\N	message_created	message	fb87739e-81a8-4c13-8f2f-b03e3c527643	{"conversation_id": "7a391ee4-f169-46dd-b34d-0d911724724a", "channel": "email"}	2026-01-07 23:02:22.102752+05:30
483c9a8e-af7c-4586-baa5-8543931ec7f1	\N	message_created	message	3edb395c-b88f-41e1-8d6c-fac6dab142c9	{"conversation_id": "4d922a8a-4a39-447f-a992-b021fe414a80", "channel": "email"}	2026-01-07 23:03:57.068071+05:30
1e75fdcf-37c1-482f-a9f5-1a60be744c17	\N	message_created	message	9ca88fcb-cf45-4b52-ab01-66343f7f44cd	{"conversation_id": "7a391ee4-f169-46dd-b34d-0d911724724a", "channel": "email"}	2026-01-07 23:05:05.949923+05:30
be0564bd-530f-479e-8cfe-2cf42676c881	\N	message_created	message	233f3f36-94d1-454d-a41a-814bffacfd91	{"conversation_id": "036faca6-ddf7-45b4-8589-69240d90d26e", "channel": "email"}	2026-01-07 23:07:19.125144+05:30
332a6013-31fe-47b0-9b3e-97875a0ce5b4	\N	message_created	message	fb77dcb9-7736-49f2-8f40-eab27c097921	{"conversation_id": "f7f44c31-6957-4fde-9d37-e1e0578dec5b", "channel": "email"}	2026-01-07 23:09:38.434627+05:30
d06fabe8-c113-4de0-9a6a-d7217790fd6e	\N	message_created	message	3cd326b2-422f-42b0-be64-d69686b1c340	{"conversation_id": "036faca6-ddf7-45b4-8589-69240d90d26e", "channel": "email"}	2026-01-07 23:14:46.974673+05:30
285092da-ecf0-4829-95c9-3a620e431256	\N	message_created	message	472e7e4b-5c0b-435b-a095-16b8d81df74f	{"conversation_id": "036faca6-ddf7-45b4-8589-69240d90d26e", "channel": "email"}	2026-01-07 23:18:46.649443+05:30
3c36c21c-3f6d-4e95-ba8e-1ffc9ff06604	\N	message_created	message	f046bcf2-39cf-45cd-97f7-e2ce3c35edf8	{"conversation_id": "0ab52439-0171-443c-8464-acf0e8e7759b", "channel": "email"}	2026-01-07 23:27:19.414684+05:30
96a1b325-8f24-4892-b685-05357e248fd4	\N	message_created	message	5ecab0fe-c9bd-4a46-939d-69bdc254801a	{"conversation_id": "472242d1-77b1-420c-942f-0a9a5f82a621", "channel": "email"}	2026-01-07 23:30:32.111362+05:30
dd25bc65-be96-461c-944d-01dc0b8f5fff	\N	message_created	message	938d8a78-d0b4-49c2-96b9-e20259e8bf1b	{"conversation_id": "472242d1-77b1-420c-942f-0a9a5f82a621", "channel": "email"}	2026-01-07 23:31:27.213375+05:30
ee1a9f43-65d1-4bad-8ca0-838f5b618ee2	\N	message_created	message	cf9d0abd-b1db-4e64-ab3d-267f3128c512	{"conversation_id": "70f2a67d-34b7-4e5a-b595-10640a0e9e20", "channel": "email"}	2026-01-07 23:33:18.425284+05:30
77441be0-6300-4713-8353-5fc18562e79f	\N	message_created	message	c779f16f-2647-4e64-a956-7b070076b2f1	{"conversation_id": "818d3265-c5b3-449e-8fca-fea77b5736c4", "channel": "email"}	2026-01-07 23:49:11.327961+05:30
95de5bfe-2450-4c38-bf6c-02d5e3b3ed2b	\N	message_created	message	563086c1-68be-4bf0-bbd2-b8a6bd12ecce	{"conversation_id": "160358d1-85be-417d-b154-b76d2441f803", "channel": "email"}	2026-01-07 23:53:28.065202+05:30
a338c7b2-fe25-470a-b85b-54758f9ac1e4	\N	message_created	message	c63020b8-cdad-41c8-8427-62f2c49b7e5d	{"conversation_id": "660cecf5-cf58-4baf-ba31-6ea21385b4e6", "channel": "email"}	2026-01-07 23:55:25.461873+05:30
8ecafb69-5cc0-42cc-8968-97c099ccb133	\N	message_created	message	aa2823f4-19d0-43f9-a84d-c6b8c4393dff	{"conversation_id": "c7380d47-7363-447c-801b-9808392092a1", "channel": "email"}	2026-01-20 14:14:05.88135+05:30
0ba29530-de4d-4349-b49a-31684302adc1	\N	message_created	message	4bef8a0f-6f65-4010-8bb3-9970f28af84d	{"conversation_id": "c7380d47-7363-447c-801b-9808392092a1", "channel": "email"}	2026-01-20 14:18:11.194554+05:30
8482d2da-9647-49b4-b85c-efd5dba0d64c	\N	message_created	message	0801170c-5554-4935-9b93-c9dd61256caf	{"conversation_id": "c7380d47-7363-447c-801b-9808392092a1", "channel": "email"}	2026-01-20 14:23:10.219568+05:30
7bc99bb8-6417-4129-b410-59c3acf27c0a	\N	message_created	message	e9660958-b66a-4e76-8f3f-0f06db7d2464	{"conversation_id": "4c6a4654-9124-4c5e-aa2b-0ad4d595cacc", "channel": "email"}	2026-01-20 14:29:20.053182+05:30
7e8ece10-fc2b-4d46-b818-30fdbc952e27	\N	message_created	message	87d421fb-ac79-4345-916d-50b7073b6785	{"conversation_id": "ee144223-ab9a-409f-8e64-77293468ca13", "channel": "email"}	2026-01-20 14:35:52.313362+05:30
e6c5be23-9e4f-4e1c-8cbb-5b6038e74d7c	\N	message_created	message	d95b8702-b1bb-4936-9ee8-311fe596ea0f	{"conversation_id": "78cb3325-1036-4fe1-87aa-3f8532ddf32c", "channel": "email"}	2026-02-10 12:48:11.758526+05:30
a054e888-1da3-4dba-8a29-15c9813c8c60	\N	message_created	message	264f33ae-cc60-4d0b-bfa7-8f8b61209f93	{"conversation_id": "78cb3325-1036-4fe1-87aa-3f8532ddf32c", "channel": "email"}	2026-02-10 14:54:29.346892+05:30
521e2fb7-5cda-40a0-b6a0-f508f23d729d	\N	message_created	message	366b1066-4951-46df-92f9-7310c554372a	{"conversation_id": "e6f474f1-e9a1-4a01-bd96-f1b0cb8a5af8", "channel": "email"}	2026-02-10 14:57:28.594224+05:30
fe95e83d-f913-4096-a9fd-a6ac7e8c246a	\N	message_created	message	b3e42dea-1cd1-48d0-b227-f1e18fd16ddd	{"conversation_id": "e6f474f1-e9a1-4a01-bd96-f1b0cb8a5af8", "channel": "email"}	2026-02-10 15:03:28.185915+05:30
c0e9d64e-b350-4c77-8ef7-a3c945301001	\N	message_created	message	2a9a7e7a-74f4-4ffe-86d9-069f77b62d27	{"conversation_id": "e6f474f1-e9a1-4a01-bd96-f1b0cb8a5af8", "channel": "email"}	2026-02-10 15:07:11.13038+05:30
f0e12849-3120-4771-aec7-87b188d004c4	\N	message_created	message	6b1d09eb-490b-4a98-a1d2-9e3c870efcc6	{"conversation_id": "e6f474f1-e9a1-4a01-bd96-f1b0cb8a5af8", "channel": "email"}	2026-02-10 15:13:27.24778+05:30
59b89940-dd6f-4e44-8eda-5e5699aa42a0	\N	message_created	message	aced3556-3364-4532-957e-9e22469758ae	{"conversation_id": "e6f474f1-e9a1-4a01-bd96-f1b0cb8a5af8", "channel": "email"}	2026-02-10 15:23:00.078093+05:30
c6489075-80fd-47fa-b104-fec7b983c513	\N	message_created	message	a5af1835-a7fb-460c-a6c2-ac0bae6ec977	{"conversation_id": "e6f474f1-e9a1-4a01-bd96-f1b0cb8a5af8", "channel": "email"}	2026-02-10 15:23:25.033701+05:30
417394fa-2279-4830-922f-26a17f2cd2b6	\N	message_created	message	8c72c6ca-87e7-45b3-ac02-a3081baec99a	{"conversation_id": "e6f474f1-e9a1-4a01-bd96-f1b0cb8a5af8", "channel": "email"}	2026-02-10 15:29:29.614087+05:30
5c3e59e4-d4b8-436a-a32e-68124ca80093	\N	message_created	message	39949fcc-e2f2-4c73-b4a5-7fc56fed7889	{"conversation_id": "46d9a1f2-899d-411f-951d-a5c1d41738d0", "channel": "email"}	2026-02-10 15:31:20.126922+05:30
ef71efce-970f-4a80-aacf-a8a2b5de4382	\N	message_created	message	cf1ea3fe-b26d-4d36-bd66-70d9bf043a22	{"conversation_id": "1daac950-d8ef-4a44-ae01-107fd4122fed", "channel": "email"}	2026-02-12 10:12:03.821131+05:30
e82cc85e-1db8-46d5-9c6a-6e3b74273e0a	\N	message_created	message	eafcfb5b-4a5b-492f-a112-222c2c206b41	{"conversation_id": "1daac950-d8ef-4a44-ae01-107fd4122fed", "channel": "email"}	2026-02-12 10:13:52.527213+05:30
030c81a7-757f-43f0-8586-7adfb6039ce7	\N	message_created	message	21b51fe6-2e44-4280-8943-7c3270afdd5b	{"conversation_id": "1daac950-d8ef-4a44-ae01-107fd4122fed", "channel": "email"}	2026-02-12 10:14:54.693411+05:30
a76b30df-ca3d-4c56-b2a2-4f129f13ccca	\N	message_created	message	c679a2a7-651d-49fb-8907-6421b8452d0b	{"conversation_id": "1daac950-d8ef-4a44-ae01-107fd4122fed", "channel": "email"}	2026-02-12 10:19:58.352495+05:30
69539e11-ec94-4094-9c02-ac29d322d7e4	\N	message_created	message	60c72398-ba7d-43ce-8698-5b6b44038d13	{"conversation_id": "1daac950-d8ef-4a44-ae01-107fd4122fed", "channel": "email"}	2026-02-12 10:23:20.303519+05:30
598a8a01-aacb-4f7c-a4ae-38ffec0c1fba	\N	message_created	message	c138d7bb-7848-4daa-8784-350d59490d36	{"conversation_id": "1daac950-d8ef-4a44-ae01-107fd4122fed", "channel": "email"}	2026-02-12 10:25:53.336454+05:30
3859e1b4-74d1-41ad-8cf8-e64542d94543	\N	message_created	message	b1ebf01f-6960-4200-8df9-5d4e5e6ba080	{"conversation_id": "1daac950-d8ef-4a44-ae01-107fd4122fed", "channel": "email"}	2026-02-12 10:31:16.153421+05:30
d7896549-04f4-4dba-83fa-c52d4ca37275	\N	message_created	message	bc3ea62f-8b07-47ab-81d6-166e9f6d9e9a	{"conversation_id": "0aeb5b45-305a-41e4-98bf-9244190c2482", "channel": "email"}	2026-02-12 15:35:35.059115+05:30
bed28fdb-108a-49e0-806c-adab21c95057	\N	message_created	message	157da021-eeec-458a-a6fb-79d029476aaa	{"conversation_id": "0aeb5b45-305a-41e4-98bf-9244190c2482", "channel": "email"}	2026-02-12 15:36:28.949436+05:30
8a67ba41-cd03-4339-a456-6c37bf7ac5b1	\N	message_created	message	a64a5f1d-c374-48da-96de-4c7df426bdb8	{"conversation_id": "d62f9403-ff8d-4a72-b45c-ddf1f7f08b79", "channel": "email"}	2026-03-06 09:58:18.300849+05:30
dbed15a3-e69d-4b7c-91bd-bb15f315ce9e	\N	message_created	message	b1594b93-f223-49b8-b68a-079b73fb6722	{"conversation_id": "2ea37a0e-470b-49bb-afd6-1ae21d20eebe", "channel": "email"}	2026-03-09 09:14:03.785273+05:30
\.


--
-- TOC entry 5397 (class 0 OID 17864)
-- Dependencies: 225
-- Data for Name: chat_documents; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.chat_documents (id, user_id, file_path, filename, content_type, size, uploaded_at) FROM stdin;
be070b4d-491c-4518-8e70-65b81a6634d1	001	uploads/93c700e4-0c6a-4c7e-8098-686f6a58298b.docx	Test_doc_2.docx	application/vnd.openxmlformats-officedocument.wordprocessingml.document	17305	2026-03-04 12:07:53.060999+05:30
\.


--
-- TOC entry 5398 (class 0 OID 17876)
-- Dependencies: 226
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.chat_messages (id, user_id, role, content, mode, document_id, created_at) FROM stdin;
5df6f06a-51e6-4c37-b823-3fa31988575a	001	user	how this application works?	general	\N	2026-03-04 12:07:33.659567+05:30
6a6ad742-9c2d-4f49-b6ea-cfafa4e2a358	001	assistant	To explain how "this" application works, I need a little more information! Could you please tell me:\n\n1.  **What is the name of the application?** (e.g., Spotify, Microsoft Word, Gmail, a specific AI tool, etc.)\n2.  **What kind of application is it?** (e.g., a mobile app, a website, desktop software, a specific AI model, etc.)\n3.  **What do you generally use it for, or what problem does it solve?**\n\nOnce I know which application you're referring to, I can give you a detailed explanation!	general	\N	2026-03-04 12:07:33.810688+05:30
298c469e-2bc8-4b72-90b1-6f1d5fa56b36	001	user	give me summary	document	be070b4d-491c-4518-8e70-65b81a6634d1	2026-03-04 12:07:59.951976+05:30
3aa309c9-3672-4dba-8dc3-38a14f278fa5	001	assistant	I encountered an error processing your request: . Please try again or contact support if the issue persists.	document	be070b4d-491c-4518-8e70-65b81a6634d1	2026-03-04 12:07:59.996071+05:30
\.


--
-- TOC entry 5399 (class 0 OID 17887)
-- Dependencies: 227
-- Data for Name: conversation_access; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.conversation_access (id, conversation_id, user_id, access_type, granted_by, granted_at) FROM stdin;
\.


--
-- TOC entry 5400 (class 0 OID 17897)
-- Dependencies: 228
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.events (id, user_id, event_name, internal_external, event_type, date_of_event, event_description, event_report, relevant_internal_stakeholders, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 5401 (class 0 OID 17908)
-- Dependencies: 229
-- Data for Name: feasibility_attachments; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.feasibility_attachments (id, study_site_id, file_path, file_name, content_type, size, uploaded_by, uploaded_at) FROM stdin;
55d1f3e5-574e-4df9-aeb2-3c5bed2fc980	75614010-992a-4183-8bfb-6e3a6a7a0bb1	/app/app/uploads/feasibility_attachments/f7df81de-2b0a-4935-989a-e089ae5ab2a6.pdf	Receipt-2091-5277.pdf	application/pdf	309131	001	2026-01-27 12:17:26.364136+05:30
39343a8f-494a-408f-997d-779d067c930f	dbded13f-074b-44da-bacf-c2cc39b02d2b	/app/app/uploads/feasibility_attachments/26ae23eb-3db3-4ab4-9779-9f54824f227a.pdf	Receipt-2034-0353.pdf	application/pdf	310883	001	2026-02-10 14:48:37.220997+05:30
\.


--
-- TOC entry 5402 (class 0 OID 17921)
-- Dependencies: 230
-- Data for Name: feasibility_requests; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.feasibility_requests (id, study_site_id, email, token, status, expires_at, created_at, updated_at) FROM stdin;
dab797e2-2521-48be-84da-5f3dfe9bdaaa	dbded13f-074b-44da-bacf-c2cc39b02d2b	labeshg@dizzaroo.com	IDopUTNrm4B0T2gpaZWB4VueR7sxMxheK6m8AOpXLH4	completed	2026-03-12 14:48:40.842577+05:30	2026-02-10 14:48:40.304054+05:30	2026-02-10 14:50:27.178533+05:30
\.


--
-- TOC entry 5403 (class 0 OID 17935)
-- Dependencies: 231
-- Data for Name: feasibility_responses; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.feasibility_responses (id, request_id, question_text, question_id, answer, section, created_at) FROM stdin;
9e4cbdcc-50dd-4a60-b9aa-41d647472cec	dab797e2-2521-48be-84da-5f3dfe9bdaaa	How many patients with unresectable, locally advanced, or metastatic Renal Cell Carcinoma (RCC) does your site currently manage per month?	\N	1	Patient Population & Database	2026-02-10 14:50:27.171007+05:30
caf5eab6-8d31-4453-be34-e236d85133af	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Of your total RCC patient population, what percentage have the clear cell (ccRCC) histology?	\N	1	Patient Population & Database	2026-02-10 14:50:27.171007+05:30
e2dab43e-3383-4074-904e-75ae6fadc3a1	dab797e2-2521-48be-84da-5f3dfe9bdaaa	How do you currently track patient treatment history, including specific agents used and lines of therapy for advanced disease?	\N	11	Patient Population & Database	2026-02-10 14:50:27.171007+05:30
d4fa3678-516a-4a3c-87b5-06612d20dda4	dab797e2-2521-48be-84da-5f3dfe9bdaaa	From your patient database, please estimate the number of patients in the last 12 months who have progressed after treatment with BOTH a PD-1/L1 checkpoint inhibitor AND a VEGF-TKI.	\N	1	Patient Population & Database	2026-02-10 14:50:27.171007+05:30
47e0b4ed-9fdf-4951-9bf9-d809eae43342	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Please describe your site's standard process for identifying potential participants for clinical trials (e.g., database queries, tumor boards, physician referrals).	\N	1	Patient Population & Database	2026-02-10 14:50:27.171007+05:30
015e8d9c-7380-4c9d-8c7f-0222b8bc3473	dab797e2-2521-48be-84da-5f3dfe9bdaaa	This protocol requires documented disease progression on or after BOTH a PD-1/L1 inhibitor AND a VEGF-TKI. Do you anticipate any difficulty in documenting this specific treatment history for your patients?	\N	1	Specific Inclusion Criteria	2026-02-10 14:50:27.171007+05:30
4a2796e0-4752-41aa-90a4-d7edf2f67199	dab797e2-2521-48be-84da-5f3dfe9bdaaa	How many patients in your current database meet the prior therapy requirement (Inclusion #4) and have also received no more than 3 prior systemic regimens for advanced RCC (Inclusion #5)?	\N	1	Specific Inclusion Criteria	2026-02-10 14:50:27.171007+05:30
35e41bf0-7e42-41a9-a9cc-65ace929f8e8	dab797e2-2521-48be-84da-5f3dfe9bdaaa	The protocol requires a Karnofsky Performance Status (KPS) score of at least 70%. Is KPS a standard assessment at your site, or do you primarily use ECOG? If you use ECOG, please confirm your staff is trained on KPS.	\N	1	Specific Inclusion Criteria	2026-02-10 14:50:27.171007+05:30
514484fe-752d-4dff-8274-22759bbaaa03	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Regarding the adequate organ function labs (Inclusion #7), do you foresee any of the specific thresholds (e.g., Hgb ≥10.0 g/dL, CrCl ≥51 mL/min) being particularly challenging for this pre-treated patient population?	\N	1	Specific Inclusion Criteria	2026-02-10 14:50:27.171007+05:30
bb4e13d8-d053-4d6a-ab96-5448e4a4a40c	dab797e2-2521-48be-84da-5f3dfe9bdaaa	A tumor specimen (archival or newly obtained) is mandatory prior to randomization (Inclusion #8). For what percentage of your potential candidates do you anticipate having a suitable archival specimen available?	\N	1	Specific Inclusion Criteria	2026-02-10 14:50:27.171007+05:30
9df5dc46-2737-4e29-a280-8cb3514efb3b	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Exclusion #1 prohibits prior treatment with any HIF-2α inhibitor or any mTOR inhibitor (e.g., everolimus). How many patients in your potential pool would be excluded due to prior everolimus use?	\N	1	Specific Exclusion Criteria	2026-02-10 14:50:27.171007+05:30
e9c1208b-9bca-432f-814c-6ef36d6678c7	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Exclusion #2 relates to active CNS metastases. For patients with previously treated brain metastases, what is your site's standard procedure for determining and documenting stability?	\N	1	Specific Exclusion Criteria	2026-02-10 14:50:27.171007+05:30
51532d5a-1013-4ce1-89ed-998b25c42241	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Exclusion #3 prohibits patients requiring supplemental oxygen. Do you anticipate this will be a significant barrier for this advanced RCC population?	\N	1	Specific Exclusion Criteria	2026-02-10 14:50:27.171007+05:30
962c8c53-318d-4329-822f-ebc0f8218ddf	dab797e2-2521-48be-84da-5f3dfe9bdaaa	For Exclusion #5 ('poorly controlled hypertension'), please describe the specific, measurable criteria your site would use to define this condition.	\N	1	Specific Exclusion Criteria	2026-02-10 14:50:27.171007+05:30
e5ce7e9f-dbb7-4ede-ad88-510cd1f2e178	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Exclusion #11 prohibits strong or moderate inhibitors/inducers of CYP3A4. What is your site's standard process for reviewing and managing concomitant medications to ensure compliance?	\N	1	Specific Exclusion Criteria	2026-02-10 14:50:27.171007+05:30
77926e99-5ce7-4270-bc4d-475f7841e4b4	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Regarding tumor tissue (Inclusion #8), does your site have the capability to perform fresh core or excisional biopsies for patients without available archival tissue?	\N	1	Site Capabilities & Procedures	2026-02-10 14:50:27.171007+05:30
59bfe3f3-19fe-4e62-a904-f871e2811833	dab797e2-2521-48be-84da-5f3dfe9bdaaa	If a fresh biopsy is required, what is your standard turnaround time from the procedure to having a formalin-fixed paraffin-embedded (FFPE) block ready for shipment to a central lab?	\N	2	Site Capabilities & Procedures	2026-02-10 14:50:27.171007+05:30
7643803c-d161-48b7-bcac-d4394827276a	dab797e2-2521-48be-84da-5f3dfe9bdaaa	The protocol requires tumor imaging (CT/MRI) per RECIST 1.1 (Inclusion #3). Are your radiologists trained and experienced in applying RECIST 1.1 criteria?	\N	3	Site Capabilities & Procedures	2026-02-10 14:50:27.171007+05:30
5952ff8b-da92-4111-8e90-add621957ea8	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Does your site have the capability to electronically transmit DICOM images to a central imaging vendor for Blinded Independent Central Review (BICR)?	\N	2	Site Capabilities & Procedures	2026-02-10 14:50:27.171007+05:30
9f2f68ac-e5fa-483c-a4cd-1538d3a50157	dab797e2-2521-48be-84da-5f3dfe9bdaaa	This study requires sparse pharmacokinetic (PK) blood samples at timed intervals on Week 1 Day 1 (predose, 1, 2, and 4 hours postdose). Does your clinic have the staffing and workflow to accommodate these timed collections?	\N	2	Site Capabilities & Procedures	2026-02-10 14:50:27.171007+05:30
b581e970-c932-452e-bd9e-45cbe8b5c82f	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Please confirm your site uses a central laboratory for clinical laboratory assessments (hematology, chemistry, etc.) as required by the protocol.	\N	2	Site Capabilities & Procedures	2026-02-10 14:50:27.171007+05:30
df18c990-2af7-40d0-80d2-a183a03859c2	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Based on a review of all inclusion/exclusion criteria, please provide your realistic estimate for the number of patients your site can enroll per month.	\N	1	Recruitment & Enrollment Projections	2026-02-10 14:50:27.171007+05:30
8a0766d3-0768-4c64-a13e-d4e100262da3	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Based on your enrollment estimate, how many patients would you anticipate screening per month to achieve that target?	\N	0	Recruitment & Enrollment Projections	2026-02-10 14:50:27.171007+05:30
ac141b95-4c2b-4bac-8b78-53f6e2f60e79	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Please identify the top 3 inclusion/exclusion criteria that you predict will be the biggest barriers to enrollment at your site. For each, please provide a brief explanation.	\N	1	Recruitment & Enrollment Projections	2026-02-10 14:50:27.171007+05:30
066e95fa-1b1a-4c0d-9d86-50d928ed5c3f	dab797e2-2521-48be-84da-5f3dfe9bdaaa	Test ques	651493a4-1900-44a4-8cc0-8b38d9c16173	1	\N	2026-02-10 14:50:27.171007+05:30
\.


--
-- TOC entry 5404 (class 0 OID 17946)
-- Dependencies: 232
-- Data for Name: iis_studies; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.iis_studies (id, user_id, study_title, asset, indication, phases, enrollment, enrollment_start_date, completion_date, other_associated_hcp_ids, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 5405 (class 0 OID 17956)
-- Dependencies: 233
-- Data for Name: project_feasibility_custom_questions; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.project_feasibility_custom_questions (id, study_id, workflow_step, question_text, section, expected_response_type, display_order, created_by, created_at, updated_at) FROM stdin;
651493a4-1900-44a4-8cc0-8b38d9c16173	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	feasibility	Test ques	\N	text	24	001	2026-01-28 12:49:58.46181+05:30	2026-01-28 12:49:58.46181+05:30
\.


--
-- TOC entry 5406 (class 0 OID 17971)
-- Dependencies: 234
-- Data for Name: rd_studies; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.rd_studies (id, user_id, study_title, nct_number, asset, indication, enrollment, phases, start_date, completion_date, created_at, updated_at) FROM stdin;
dda202f7-c2af-4137-8c20-d1ccb8d81d04	testuser2	Test R&D Study for Templates	NCT12345678	Test Asset	\N	\N	\N	\N	\N	2026-03-06 11:05:50.505599+05:30	2026-03-06 11:05:50.505599+05:30
\.


--
-- TOC entry 5407 (class 0 OID 17981)
-- Dependencies: 235
-- Data for Name: site_documents; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.site_documents (id, site_id, category, file_path, file_name, content_type, size, uploaded_by, uploaded_at, description, metadata, document_type, review_status, tmf_filed) FROM stdin;
199a7ca7-c2aa-4682-bdee-cb06e719536b	f801bc3d-1c18-4903-982b-57b28dffd1a4	site_visibility_report	uploads/site_documents/7a6355be-2d44-4262-b106-520c0803e7e0.pdf	Receipt-2091-5277.pdf	application/pdf	309131	001	2026-01-20 13:22:18.914568+05:30	Site Visibility Report	{}	site	pending	false
abef0e0c-c786-4a7f-b148-44e01efa1e7c	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	uploads/site_documents/44d7ca27-ee6b-45f8-b736-f604e5ed32a6.pdf	Receipt-2091-5277.pdf	application/pdf	309131	001	2026-01-20 13:22:31.319221+05:30	Signed CDA	{}	site	pending	false
12fc0939-1746-44e3-8c8a-efcb8588e7e0	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	uploads/site_documents/b98d3a31-7dfa-441c-88e1-440a38b897de.pdf	Receipt-2091-5277.pdf	application/pdf	309131	001	2026-01-20 15:08:54.716962+05:30	Signed CDA	{}	site	pending	false
e964cae2-0ec0-4e6f-8011-be77277438ae	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/uploads/cda_snapshots/75614010-992a-4183-8bfb-6e3a6a7a0bb1_ASLAN001-009_Site 01.html	CDA_Signed_ASLAN001-009_Site_01_20260128.html	text/html	12409	\N	2026-01-28 12:22:11.605468+05:30	Signed CDA - ASLAN001-009 - Site 01	{}	site	pending	false
686cae90-df24-47a3-a246-52e0602fd578	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.html	CDA_Signed_MK-6482_Site_01_20260128.html	text/html	12408	\N	2026-01-28 12:43:34.845648+05:30	Signed CDA - MK-6482 - Site 01	{}	site	pending	false
aae9e639-28d6-4c28-82f8-e3cadc625943	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/uploads/cda_snapshots/75614010-992a-4183-8bfb-6e3a6a7a0bb1_ASLAN001-009_Site 01.signed.pdf	CDA_Signed_ASLAN001-009_Site_01_20260204.pdf	application/pdf	114942	\N	2026-02-04 13:26:16.979269+05:30	Signed CDA via Zoho Sign - ASLAN001-009 - Site 01	{}	site	pending	false
de5eb608-1b6d-4066-96bd-d22200202684	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.signed.pdf	CDA_Signed_MK-6482_Site_01_20260204.pdf	application/pdf	133559	\N	2026-02-04 13:33:10.041228+05:30	Signed CDA via Zoho Sign - MK-6482 - Site 01	{}	site	pending	false
f5a2215f-185b-4871-90ed-fa4bab4d1085	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.signed.pdf	CDA_Signed_MK-6482_Site_01_20260205.pdf	application/pdf	114927	\N	2026-02-05 11:39:44.079414+05:30	Signed CDA via Zoho Sign - MK-6482 - Site 01	{}	site	pending	false
0b722c05-b83d-4d9a-a2a5-4a79e9b207e7	f801bc3d-1c18-4903-982b-57b28dffd1a4	other	uploads/site_documents/85a733f2-b6a0-42e4-8a37-002292da558d.pdf	Receipt-2091-5277.pdf	application/pdf	309131	001	2026-02-08 14:30:03.418733+05:30	Testing document.	{}	sponsor	pending	false
51edca49-b228-4881-b316-cc86ca03024e	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.signed.pdf	CDA_Signed_MK-6482_Site_01_20260209.pdf	application/pdf	114939	\N	2026-02-09 10:37:30.056196+05:30	Signed CDA via Zoho Sign - MK-6482 - Site 01	{}	site	pending	false
184d46a4-748b-4aa6-8be8-94c528f5252f	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.signed.pdf	CDA_Signed_MK-6482_Site_01_20260209.pdf	application/pdf	116407	\N	2026-02-09 10:51:10.917877+05:30	Signed CDA via Zoho Sign - MK-6482 - Site 01	{}	site	pending	false
8c96fef3-06f0-426a-8324-4a476a1f7f34	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/api/v1/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.signed.pdf	CDA_Signed_MK-6482_Site_01_20260212.pdf	application/pdf	116441	\N	2026-02-12 11:11:14.524037+05:30	Signed CDA via Zoho Sign - MK-6482 - Site 01	{}	site	pending	false
31c3f45e-ff28-426f-8c40-3e3355768a39	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/api/v1/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.signed.pdf	CDA_Signed_MK-6482_Site_01_20260212.pdf	application/pdf	116443	\N	2026-02-12 12:29:15.10279+05:30	Signed CDA via Zoho Sign - MK-6482 - Site 01	{}	site	pending	false
99b822fa-4596-442e-94c3-25d1abf6539f	f801bc3d-1c18-4903-982b-57b28dffd1a4	onsite_visit_report	uploads\\site_documents\\ff20a9ce-31c4-4381-8bff-43ce64a43488.pdf	PUBLICATION25.pdf	application/pdf	503920	001	2026-03-06 09:26:55.536725+05:30	On-site Visit Report	{}	site	pending	false
8bb2a076-c6df-4612-9557-7f47e1ebd53b	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.signed.pdf	CDA_Signed_MK-6482_Site_01_20260209.pdf	application/pdf	114939	\N	2026-02-09 10:57:57.569692+05:30	Signed CDA via Zoho Sign - MK-6482 - Site 01	{}	site	approved	true
27634159-66aa-4a9c-b787-beb914dfdd45	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/api/v1/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.signed.pdf	CDA_Signed_MK-6482_Site_01_20260212.pdf	application/pdf	114971	\N	2026-02-12 11:05:20.08499+05:30	Signed CDA via Zoho Sign - MK-6482 - Site 01	{}	site	approved	true
022d1b52-9a07-4e2c-a0b2-f377f627ebdd	f801bc3d-1c18-4903-982b-57b28dffd1a4	signed_cda	/app/app/api/v1/uploads/cda_snapshots/dbded13f-074b-44da-bacf-c2cc39b02d2b_MK-6482_Site 01.signed.pdf	CDA_Signed_MK-6482_Site_01_20260210.pdf	application/pdf	114933	\N	2026-02-10 14:48:04.211825+05:30	Signed CDA via Zoho Sign - MK-6482 - Site 01	{}	site	approved	true
\.


--
-- TOC entry 5408 (class 0 OID 18000)
-- Dependencies: 236
-- Data for Name: site_profiles; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.site_profiles (id, site_id, site_name, hospital_name, pi_name, pi_email, pi_phone, primary_contracting_entity, authorized_signatory_name, authorized_signatory_email, authorized_signatory_title, address_line_1, city, state, country, postal_code, site_coordinator_name, site_coordinator_email, created_at, updated_at) FROM stdin;
51c0eab0-8f53-425d-95bb-4aa7037d71ee	f801bc3d-1c18-4903-982b-57b28dffd1a4	Ghaziabad	Mahindra hospital	Priyank	priyank@gmail.com	7060627262	Abhishek	Abhishek P	Abhishek@dizzaroo.com	Abhishek 	Balewadi	Pune	Maharasthra	India	412207	Atharva	atharava@dizzaroo.com	2026-02-23 08:37:08.066572+05:30	2026-02-25 09:03:22.228881+05:30
\.


--
-- TOC entry 5409 (class 0 OID 18010)
-- Dependencies: 237
-- Data for Name: site_status_history; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.site_status_history (id, site_id, status, previous_status, metadata, triggering_event, reason, changed_at) FROM stdin;
\.


--
-- TOC entry 5410 (class 0 OID 18019)
-- Dependencies: 238
-- Data for Name: site_statuses; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.site_statuses (id, site_id, current_status, previous_status, metadata, effective_at, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 5411 (class 0 OID 18030)
-- Dependencies: 239
-- Data for Name: site_workflow_steps; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.site_workflow_steps (id, site_id, step_name, status, step_data, completed_at, completed_by, created_at, updated_at, study_site_id) FROM stdin;
56f5dc0e-4f5a-45c4-a13a-c4fa63ccc26c	\N	feasibility	locked	{}	\N	\N	2026-02-04 13:31:24.448266+05:30	2026-02-04 13:31:24.448266+05:30	75614010-992a-4183-8bfb-6e3a6a7a0bb1
0b1d3fac-d4cc-4377-9d65-5259131bad7c	\N	site_selection_outcome	locked	{}	\N	\N	2026-02-04 13:31:24.448266+05:30	2026-02-04 13:31:24.448266+05:30	75614010-992a-4183-8bfb-6e3a6a7a0bb1
0509fc23-2fe5-4c9e-bd76-de7dcd3ec356	f801bc3d-1c18-4903-982b-57b28dffd1a4	site_selection_outcome	locked	{}	\N	\N	2026-01-20 15:25:17.6428+05:30	2026-01-20 15:25:17.6428+05:30	45a872ba-8ff7-45a1-95b6-9badf41b0087
d019e74b-c5bb-49ab-9bd3-2fdc96e7a855	f801bc3d-1c18-4903-982b-57b28dffd1a4	site_identification	completed	{"comments": "", "decision": "proceed"}	2026-01-27 10:09:31.355526+05:30	001	2026-01-20 15:25:17.6428+05:30	2026-01-27 10:09:31.355947+05:30	45a872ba-8ff7-45a1-95b6-9badf41b0087
02bfb418-8646-4d99-9b1d-219c639fa60a	f801bc3d-1c18-4903-982b-57b28dffd1a4	cda_execution	completed	{"cda_status": "NOT_APPLICABLE", "cda_required": "not_applicable"}	2026-01-27 10:10:40.105484+05:30	001	2026-01-20 15:25:17.6428+05:30	2026-01-27 10:10:40.105507+05:30	45a872ba-8ff7-45a1-95b6-9badf41b0087
268ad0fe-6e52-463c-962c-f4ad9529e5c6	\N	site_selection_outcome	locked	{}	\N	\N	2026-01-27 10:45:51.779667+05:30	2026-01-27 10:45:51.779667+05:30	de85ab8f-4032-47df-8f2b-aef37156ace7
1a602db8-6058-4709-bcdd-6cb73e6c9dac	f801bc3d-1c18-4903-982b-57b28dffd1a4	feasibility	not_started	{}	\N	\N	2026-01-20 15:25:17.6428+05:30	2026-01-28 12:51:25.9395+05:30	45a872ba-8ff7-45a1-95b6-9badf41b0087
9e87ad15-dbc7-4122-8e07-85f342c997a5	\N	feasibility	not_started	{}	\N	\N	2026-01-27 10:45:51.779667+05:30	2026-01-28 12:51:25.9395+05:30	de85ab8f-4032-47df-8f2b-aef37156ace7
2cd9c9fd-16b7-4187-9cd6-1966fdf79603	\N	site_identification	completed	{"comments": "", "decision": "proceed"}	2026-02-09 11:11:59.935197+05:30	001	2026-02-04 13:31:24.448266+05:30	2026-02-09 11:11:59.935254+05:30	75614010-992a-4183-8bfb-6e3a6a7a0bb1
878ff4b5-e29f-48a5-b757-2a8cab18e072	\N	site_identification	completed	{"comments": "", "decision": "proceed"}	2026-01-27 10:48:06.303632+05:30	001	2026-01-27 10:45:51.779667+05:30	2026-01-27 10:48:06.30366+05:30	de85ab8f-4032-47df-8f2b-aef37156ace7
62217295-224f-439b-be2a-9c20a3a79594	\N	cda_execution	completed	{"cda_status": "NOT_APPLICABLE", "cda_required": "not_applicable"}	2026-01-27 10:48:08.764919+05:30	001	2026-01-27 10:45:51.779667+05:30	2026-01-27 10:48:08.764957+05:30	de85ab8f-4032-47df-8f2b-aef37156ace7
e64e8f1f-9439-442c-993c-8a043a03dc51	\N	cda_execution	in_progress	{"cc_emails": ["labeshg@dizzaroo.com"], "cda_status": "CDA_SENT", "cda_comment": "", "cda_sent_at": "2026-02-09T05:42:10.170249+00:00", "cda_sent_by": "001", "cda_required": true, "zoho_sign_status": "SENT", "site_signer_email": "labeshg@dizzaroo.com", "sponsor_signer_email": "labeshg@dizzaroo.com", "zoho_sign_request_id": "148878000000063369"}	\N	\N	2026-02-04 13:31:24.448266+05:30	2026-02-09 11:12:10.170386+05:30	75614010-992a-4183-8bfb-6e3a6a7a0bb1
db244060-adab-4de3-ae0f-2585fd37cae5	\N	site_identification	completed	{"comments": "", "decision": "proceed"}	2026-03-05 14:40:12.408251+05:30	001	2026-03-04 12:50:40.421568+05:30	2026-03-05 14:40:12.408269+05:30	dbded13f-074b-44da-bacf-c2cc39b02d2b
168a5abe-d284-4003-af6f-34b830422823	\N	cda_execution	completed	{"cda_status": "NOT_REQUIRED", "cda_comment": "sf", "cda_required": false}	2026-03-06 09:26:19.638319+05:30	001	2026-03-04 12:50:40.421568+05:30	2026-03-06 09:26:19.638368+05:30	dbded13f-074b-44da-bacf-c2cc39b02d2b
c6feb7cb-7226-4c73-b98a-29e8c8a93fa9	\N	feasibility	completed	{"document_id": "99b822fa-4596-442e-94c3-25d1abf6539f", "response_received": true, "response_received_at": "2026-03-06T03:56:57.092Z", "onsite_visit_required": true, "additional_feasibility": false, "onsite_report_uploaded": true}	2026-03-06 09:26:57.125615+05:30	001	2026-03-04 12:50:40.421568+05:30	2026-03-06 09:26:57.125647+05:30	dbded13f-074b-44da-bacf-c2cc39b02d2b
987d6c56-f249-4e8f-9991-3a658827cb8e	\N	site_selection_outcome	not_started	{}	\N	\N	2026-03-04 12:50:40.421568+05:30	2026-03-06 09:26:57.147967+05:30	dbded13f-074b-44da-bacf-c2cc39b02d2b
\.


--
-- TOC entry 5412 (class 0 OID 18043)
-- Dependencies: 240
-- Data for Name: sites; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.sites (id, site_id, name, code, location, principal_investigator, address, city, country, status, created_at, updated_at) FROM stdin;
f801bc3d-1c18-4903-982b-57b28dffd1a4	site01	Site 01	SITE01	\N	\N	\N	\N	\N	active	2026-01-20 13:12:13.051649+05:30	2026-01-20 13:12:13.051649+05:30
\.


--
-- TOC entry 5413 (class 0 OID 18054)
-- Dependencies: 241
-- Data for Name: studies; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.studies (id, study_id, name, description, status, created_at, updated_at) FROM stdin;
f7984413-4268-4720-a3ab-00f5b4044864	DB-06	DB-06	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
206942ca-6d36-4f6d-ae1f-f0d661ac31cd	New study	MK-6482	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
7b502ee0-0e4b-4408-b300-f6b52194013d	DG-04 Ver 2	DG-04 Ver 2	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
0da0799e-04fa-4ab0-9711-0e12c122dd4a	Zani	ZWI-ZW25	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
98e0b119-d77b-4185-8846-989013874b9f	Destiny B04	Destiny B04	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
92807a47-a0ee-4e84-8a85-703146e0c220	Study00001	Study00001	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
4bd0aae0-673b-4901-8854-8c5e0772231f	Study00002	Study00002	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
23b3f254-ae38-4d3f-8a0d-33d654a7f8a0	ASLAN001-009	ASLAN001-009	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
2b079c1e-16de-4b5a-a8ac-c76291120291	Dizzaroo_001	Breast Cancer DP	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
c058a05b-a1d6-412d-b733-28f629fcd37f	MK-6482-013	MK-6482-013	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
96a8e9b5-530c-4965-8062-90b9fb2f1ecd	test 123	test 123	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
01ea63b5-7a62-42ba-b488-dfa189ddae75	study1	study1	\N	active	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
a6572547-819c-4294-9480-c0d128a5b96e	STUDY001	Test Study for Templates	Test study to verify template upload functionality	active	2026-03-06 11:18:20.995906+05:30	2026-03-06 11:18:20.995906+05:30
\.


--
-- TOC entry 5414 (class 0 OID 18065)
-- Dependencies: 242
-- Data for Name: study_sites; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.study_sites (id, study_id, site_id, created_at, updated_at) FROM stdin;
45a872ba-8ff7-45a1-95b6-9badf41b0087	f7984413-4268-4720-a3ab-00f5b4044864	f801bc3d-1c18-4903-982b-57b28dffd1a4	2026-01-27 10:45:49.528077+05:30	2026-01-27 10:45:49.528077+05:30
de85ab8f-4032-47df-8f2b-aef37156ace7	7b502ee0-0e4b-4408-b300-f6b52194013d	f801bc3d-1c18-4903-982b-57b28dffd1a4	2026-01-27 10:45:51.779667+05:30	2026-01-27 10:45:51.779667+05:30
dbded13f-074b-44da-bacf-c2cc39b02d2b	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	f801bc3d-1c18-4903-982b-57b28dffd1a4	2026-01-27 10:46:48.563265+05:30	2026-01-27 10:46:48.563265+05:30
75614010-992a-4183-8bfb-6e3a6a7a0bb1	23b3f254-ae38-4d3f-8a0d-33d654a7f8a0	f801bc3d-1c18-4903-982b-57b28dffd1a4	2026-01-27 11:30:52.767996+05:30	2026-01-27 11:30:52.767996+05:30
\.


--
-- TOC entry 5415 (class 0 OID 18074)
-- Dependencies: 243
-- Data for Name: study_templates; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.study_templates (id, study_id, template_name, template_type, document_html, created_by, created_at, updated_at, is_active, template_content, placeholder_config, template_file_path, field_mappings) FROM stdin;
05cff5ee-7f56-49bf-9e77-5b64aaab7ade	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	test	CDA		001	2026-02-17 15:02:36.996572+05:30	2026-02-18 16:05:51.462544+05:30	false	{"type": "doc", "content": [{"type": "paragraph", "content": [{"text": "Receipt", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Invoice number NKPOOSTS0009", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Receipt number 20340353", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Date paid February 8, 2026", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Cursor Bill to", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "801 West End Avenue Dhiraj Gambhire", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "New York, New York 10025 3 Balewadi Road", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "United States Pune 411045", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "1 8314259504 Maharashtra", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "hi@cursor.com India", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "labeshg@dizzaroo.com", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "$23.60 paid on February 8, 2026", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Description Qty Unit price Tax Amount", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Cursor Pro 1 $20.00 18% $20.00", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Feb 4Mar 4, 2026", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Subtotal $20.00", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Total excluding tax $20.00", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "GST - India 18% on $20.00 $3.60", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Total $23.60", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Amount paid $23.60", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Payment history", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Payment method Date Amount paid Receipt number", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Visa - 5064 February 8, 2026 $23.60 20340353", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Anysphere, Inc.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "US EIN 874436547", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Page 1 of 1", "type": "text"}]}]}	\N	\N	\N
791762b4-0ca2-4dc3-b3cf-395e548e8fb0	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing part 2	CDA		001	2026-02-23 10:54:32.156371+05:30	2026-02-23 12:07:31.819356+05:30	false	{"type": "doc", "content": [{"type": "heading", "attrs": {"level": 1}, "content": [{"text": "Confidential Disclosure Agreement (CDA)", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "(Mutual – Plain-English Version)", "type": "text", "marks": [{"type": "bold"}]}]}, {"type": "paragraph", "content": [{"text": "This Agreement is between:", "type": "text"}]}, {"type": "orderedList", "content": [{"type": "listItem", "content": [{"text": "Dizzaroo Private Limited", "type": "text", "marks": [{"type": "bold"}]}, {"type": "hardBreak"}, {"text": "SR NO 3112, Speciality Business Center, B-211, Baner Gaon,", "type": "text"}, {"type": "hardBreak"}, {"text": "Pune, Maharashtra, India, 411045 (“Dizzaroo”)", "type": "text"}]}]}, {"type": "paragraph", "content": [{"text": "and", "type": "text"}]}, {"type": "orderedList", "content": [{"type": "listItem", "content": [{"text": "Transform Hospitals", "type": "text", "marks": [{"type": "bold"}]}, {"type": "hardBreak"}, {"text": "A 302, Gagan Utopia, Keshavnagar, Mundhwa, Pune- 411036 (“Transform Hospitals”).", "type": "text"}]}]}, {"type": "paragraph", "content": [{"text": "Dizzaroo and the Other Party are together called “the parties”.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Date:", "type": "text", "marks": [{"type": "bold"}]}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "1. Purpose", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The parties want to share confidential information with each other to explore and evaluate a potential working relationship, collaboration, project, service arrangement, or any related business discussion (the", "type": "text"}, {"text": "“Purpose”", "type": "text", "marks": [{"type": "bold"}]}, {"text": ").", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "2. Confidential Information", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "“Confidential Information” means any non-public information one party (“Disclosing Party”) shares with the other (“Receiving Party”), in any form (verbal, written, electronic, etc.), including:", "type": "text"}]}, {"type": "bulletList", "content": [{"type": "listItem", "content": [{"text": "technical information, software, models, algorithms, research, designs;", "type": "text"}]}, {"type": "listItem", "content": [{"text": "business plans, strategies, forecasts, pricing, and financials;", "type": "text"}]}, {"type": "listItem", "content": [{"text": "customer, partner, or supplier information;", "type": "text"}]}, {"type": "listItem", "content": [{"text": "presentations, documents, reports, data, analyses, or summaries;", "type": "text"}]}, {"type": "listItem", "content": [{"text": "any notes or copies based on the above.", "type": "text"}]}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "3. What is", "type": "text"}, {"text": "not", "type": "text", "marks": [{"type": "italic"}]}, {"text": "Confidential Information", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Information is not considered Confidential Information if the Receiving Party can show that:", "type": "text"}]}, {"type": "orderedList", "content": [{"type": "listItem", "content": [{"text": "it was already public when received;", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "it became public later without the Receiving Party breaking this Agreement;", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "it was already in the Receiving Party’s possession legally;", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "it was received from someone who was allowed to share it; or", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "it was developed independently without using the Disclosing Party’s information.", "type": "text"}]}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "4. Obligations of the Receiving Party", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The Receiving Party agrees to:", "type": "text"}]}, {"type": "orderedList", "content": [{"type": "listItem", "content": [{"text": "use Confidential Information", "type": "text"}, {"text": "only", "type": "text", "marks": [{"type": "bold"}]}, {"text": "for the Purpose;", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "not share it with anyone except employees, directors, contractors, or advisors who:", "type": "text"}, {"type": "bulletList", "content": [{"type": "listItem", "content": [{"text": "need to know it for the Purpose, and", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "are bound to keep it confidential;", "type": "text"}, {"type": "hardBreak"}]}]}]}, {"type": "listItem", "content": [{"text": "protect the information with the same care it uses for its own confidential information (and at least reasonable care);", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "immediately notify the Disclosing Party of any unauthorised use or disclosure.", "type": "text"}]}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "5. Disclosures required by law", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "If the Receiving Party must disclose Confidential Information because of law, court order, or a government requirement, it may do so, but must:", "type": "text"}]}, {"type": "orderedList", "content": [{"type": "listItem", "content": [{"text": "notify the Disclosing Party as soon as legally allowed; and", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "share only the minimum information required.", "type": "text"}]}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "6. Ownership", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Confidential Information remains the property of the Disclosing Party. Nothing in this Agreement gives ownership or licence rights beyond the limited right to use the information for the Purpose.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "7. Term and confidentiality duration", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This Agreement begins on the Date above.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The obligation to keep information confidential continues for", "type": "text"}, {"text": "five (5) years", "type": "text", "marks": [{"type": "bold"}]}, {"text": "after the last disclosure of Confidential Information.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "8. Return or destruction of information", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Upon written request, the Receiving Party will:", "type": "text"}]}, {"type": "orderedList", "content": [{"type": "listItem", "content": [{"text": "return or destroy all Confidential Information and copies within a reasonable time, and", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "confirm in writing that this has been done,", "type": "text"}]}]}, {"type": "paragraph", "content": [{"text": "except for copies it must retain by law or that exist only in backup systems (which remain protected).", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "9. Breach and remedies", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The Receiving Party understands that unauthorised use or disclosure may cause serious harm.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The Disclosing Party may seek: - an injunction or court order to stop further disclosure; and", "type": "text"}, {"type": "hardBreak"}, {"text": "- any other remedies available under the law (including damages).", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "10. Governing law and jurisdiction", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This Agreement is governed by the laws of", "type": "text"}, {"text": "India", "type": "text", "marks": [{"type": "bold"}]}, {"text": ".", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Any disputes will be subject to the courts of", "type": "text"}, {"text": "Pune, Maharashtra", "type": "text", "marks": [{"type": "bold"}]}, {"text": ", which will have non-exclusive jurisdiction.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "11. General", "type": "text"}]}, {"type": "orderedList", "content": [{"type": "listItem", "content": [{"text": "This Agreement is the complete agreement between the parties regarding confidentiality for the Purpose.", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "Any changes must be in writing and signed by both parties.", "type": "text"}, {"type": "hardBreak"}]}, {"type": "listItem", "content": [{"text": "If a court finds any provision invalid, the rest will continue to apply to the fullest extent allowed by law.", "type": "text"}]}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "Signatures", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "For Dizzaroo Private Limited", "type": "text", "marks": [{"type": "bold"}]}]}, {"type": "paragraph", "content": [{"text": "Name:", "type": "text"}, {"type": "hardBreak"}, {"text": "Title:", "type": "text"}, {"type": "hardBreak"}, {"text": "Signature:", "type": "text"}, {"type": "hardBreak"}, {"text": "Date:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "For Transform Hospitals", "type": "text", "marks": [{"type": "bold"}]}]}, {"type": "paragraph", "content": [{"text": "Name:", "type": "text"}, {"type": "hardBreak"}, {"text": "Title:", "type": "text"}, {"type": "hardBreak"}, {"text": "Signature:", "type": "text"}, {"type": "hardBreak"}, {"text": "Date:", "type": "text"}]}]}	{}	\N	\N
7397dbd1-3ae3-4bb5-a367-49c4b795f73e	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing	CDA		001	2026-02-23 08:58:25.529147+05:30	2026-02-23 12:07:33.792271+05:30	false	{"type": "doc", "content": [{"type": "paragraph", "content": [{"text": "CONFIDENTIALITY AGREEMENT", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This Agreement is made between:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Sponsor: {{PRIMARY_CONTRACTING_ENTITY}}", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "and", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Site Name: {{HOSPITAL_NAME}}", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Principal Investigator: {{PI_NAME}}", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Email: {{PI_EMAIL}}", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Site Address:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "{{ADDRESS_LINE_1}}", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "{{CITY}}, {{STATE}}, {{COUNTRY}} - {{POSTAL_CODE}}", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Authorized Signatory: {{AUTHORIZED_SIGNATORY_NAME}}", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Signatory Email: {{AUTHORIZED_SIGNATORY_EMAIL}}", "type": "text"}]}]}	\N	\N	\N
e9477bf1-e8c2-4b19-997b-904d4c873a79	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	CDA	CDA		001	2026-02-18 16:31:09.333766+05:30	2026-02-23 12:07:35.597063+05:30	false	{"type": "doc", "content": [{"type": "paragraph", "content": [{"text": "Confidential Disclosure Agreement (CDA)", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "(Mutual – Plain-English Version)", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This Agreement is between:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "1. Dizzaroo Private Limited", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "SR NO 3112, Speciality Business Center, B-211, Baner Gaon,", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Pune, Maharashtra, India, 411045 (“Dizzaroo”)", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "and", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "2. Transform Hospitals", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "A 302, Gagan Utopia, Keshavnagar, Mundhwa, Pune- 411036 (“Transform", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Hospitals”).", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Dizzaroo and the Other Party are together called “the parties”.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Date:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "1. Purpose", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The parties want to share confidential information with each other to explore and", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "evaluate a potential working relationship, collaboration, project, service arrangement, or", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "any related business discussion (the “Purpose”).", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "2. Confidential Information", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "“Confidential Information” means any non-public information one party (“Disclosing", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Party”) shares with the other (“Receiving Party”), in any form (verbal, written, electronic,", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "etc.), including:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": " technical information, software, models, algorithms, research, designs;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": " business plans, strategies, forecasts, pricing, and financials;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": " customer, partner, or supplier information;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": " presentations, documents, reports, data, analyses, or summaries;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": " any notes or copies based on the above.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Speciality Business Center -, 2 B 1 1", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Baner - B alewadi Rd, Balewa d i", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Pune, India - 4 11045", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "www.dizzaroo.com", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "3. What is not Confidential Information", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Information is not considered Confidential Information if the Receiving Party can show", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "that:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "a) it was already public when received;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "b) it became public later without the Receiving Party breaking this Agreement;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "c) it was already in the Receiving Party’s possession legally;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "d) it was received from someone who was allowed to share it; or", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "e) it was developed independently without using the Disclosing Party’s information.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "4. Obligations of the Receiving Party", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The Receiving Party agrees to:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "a) use Confidential Information only for the Purpose;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "b) not share it with anyone except employees, directors, contractors, or advisors", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "who:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "o need to know it for the Purpose, and", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "o are bound to keep it confidential;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "c) protect the information with the same care it uses for its own confidential", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "information (and at least reasonable care);", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "d) immediately notify the Disclosing Party of any unauthorised use or disclosure.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "5. Disclosures required by law", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "If the Receiving Party must disclose Confidential Information because of law, court", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "order, or a government requirement, it may do so, but must:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Speciality Business Center -, 2 B 1 1", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Baner - B alewadi Rd, Balewa d i", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Pune, India - 4 11045", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "www.dizzaroo.com", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "a) notify the Disclosing Party as soon as legally allowed; and", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "b) share only the minimum information required.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "6. Ownership", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Confidential Information remains the property of the Disclosing Party. Nothing in this", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Agreement gives ownership or licence rights beyond the limited right to use the", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "information for the Purpose.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "7. Term and confidentiality duration", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This Agreement begins on the Date above.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The obligation to keep information confidential continues for five (5) years after the last", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "disclosure of Confidential Information.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "8. Return or destruction of information", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Upon written request, the Receiving Party will:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "a) return or destroy all Confidential Information and copies within a reasonable time,", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "and", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "b) confirm in writing that this has been done,", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "except for copies it must retain by law or that exist only in backup systems (which", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "remain protected).", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "9. Breach and remedies", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The Receiving Party understands that unauthorised use or disclosure may cause", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "serious harm.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Speciality Business Center -, 2 B 1 1", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Baner - B alewadi Rd, Balewa d i", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Pune, India - 4 11045", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "www.dizzaroo.com", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The Disclosing Party may seek: - an injunction or court order to stop further disclosure;", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "and", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "- any other remedies available under the law (including damages).", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "10. Governing law and jurisdiction", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This Agreement is governed by the laws of India.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Any disputes will be subject to the courts of Pune, Maharashtra, which will have non-", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "exclusive jurisdiction.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "11. General", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "a) This Agreement is the complete agreement between the parties regarding", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "confidentiality for the Purpose.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "b) Any changes must be in writing and signed by both parties.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "c) If a court finds any provision invalid, the rest will continue to apply to the fullest", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "extent allowed by law.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Signatures", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "For Dizzaroo Private Limited", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Name:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Title:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Signature:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Date:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "For Transform Hospitals", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Name:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Title:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Speciality Business Center -, 2 B 1 1", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Baner - B alewadi Rd, Balewa d i", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Pune, India - 4 11045", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "www.dizzaroo.com", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Signature:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Date:", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Speciality Business Center -, 2 B 1 1", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Baner - B alewadi Rd, Balewa d i", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Pune, India - 4 11045", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "www.dizzaroo.com", "type": "text"}]}]}	\N	\N	\N
79318562-ce06-4456-aa30-ad5062b18c0f	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing part 3	CDA		001	2026-02-23 12:07:48.895403+05:30	2026-02-23 15:49:37.342151+05:30	false	null	{}	uploads/templates/template_ecc7d372-b2bc-4741-b5d9-2a1d77ad15e9.docx	\N
737b0cd2-e642-435a-8503-cf85a424c4e2	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing part 4	CDA		001	2026-02-23 15:49:50.28288+05:30	2026-02-23 15:54:25.750613+05:30	false	null	{}	uploads/templates/template_1d737447-339e-49a1-95bb-42e7d732c014.docx	\N
d5e647cf-a9eb-405c-8755-5612fb6c192f	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing part 5	CDA		001	2026-02-23 15:54:39.595434+05:30	2026-02-24 09:30:03.94932+05:30	false	null	{}	uploads/templates/template_69722a41-f2d1-49af-9897-4476cc92df01.docx	\N
c4a38372-107e-42ae-a540-876650bfdb61	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 5	CDA		001	2026-02-24 09:30:17.769329+05:30	2026-02-24 10:10:37.980218+05:30	false	null	{}	uploads/templates/template_bef785a4-fee8-433b-8cdc-5e626a4d7a80.docx	\N
37abfa3a-647a-494d-904e-0fa25d5573c3	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 7	CDA		001	2026-02-24 10:13:25.973219+05:30	2026-02-24 11:17:34.70911+05:30	false	null	{}	uploads/templates/template_c814e1cd-cfb3-44ea-8379-4348c887cc26.docx	\N
548da346-47e6-43f9-8d06-119ac1180c93	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing 6	CDA		001	2026-02-24 10:10:56.680133+05:30	2026-02-24 11:17:36.33491+05:30	false	null	{}	uploads/templates/template_3220be92-b03c-472f-ada8-73ead90cf0e6.docx	\N
8328016d-eb21-44f3-911e-458a0b70a22b	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing 7	CDA		001	2026-02-24 11:17:50.681419+05:30	2026-02-24 13:18:38.939944+05:30	false	null	{}	uploads/templates/template_2bd2a41a-7ad7-4ddd-a968-852385199549.docx	{"SITE_PROFILE:": "site_profile.testing"}
ff4fb425-b10e-4a70-b009-cd86944d0fb4	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing 12	CDA		001	2026-02-24 15:06:27.95405+05:30	2026-02-24 16:22:11.432123+05:30	false	null	{"PI_NAME": {"editable": true}, "SITE_CITY": {"editable": true}, "SITE_NAME": {"editable": false}}	uploads/templates/template_3cded3d9-cb32-4ddd-89db-7823c986c00c.docx	{"SITE_NAME": "site_profile.site_name"}
c7cede2f-417d-4f01-9d96-319c8910d60c	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 10	CDA		001	2026-02-24 13:19:41.117598+05:30	2026-02-24 15:05:40.913497+05:30	false	null	{"PI_NAME": {"editable": false}, "SITE_CITY": {"editable": true}, "SITE_NAME": {"editable": true}}	uploads/templates/template_f075c413-fe42-44e3-a95a-c2a383f268c1.docx	{"SITE_NAME": "site_profile.Labesh", "SITE_CITY": "site_profile.Testing"}
b397d485-e8b9-4ea7-8108-77075e074339	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing 9	CDA		001	2026-02-24 12:22:37.597454+05:30	2026-02-24 13:18:33.246517+05:30	false	null	{"PI_NAME": {"editable": false}, "SITE_CITY": {"editable": false}, "SITE_NAME": {"editable": true}}	uploads/templates/template_a9eb227f-673f-40ee-a4fa-99b872051844.docx	{"SITE_NAME": "site_profile.Labesh Kumar Garg"}
13bb047a-d253-4910-b734-34071be4b8ae	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing 8	CDA		001	2026-02-24 12:18:52.275726+05:30	2026-02-24 13:18:36.475537+05:30	false	null	{}	uploads/templates/template_34dd2e46-e51b-4440-900a-c2c0748079e7.docx	{"SITE_NAME": "site_profile.Testing"}
3cd90c2a-3b92-46ab-a914-79afc63adcf1	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing 11	CDA		001	2026-02-24 15:05:54.227355+05:30	2026-02-24 16:22:13.417492+05:30	false	null	{}	uploads/templates/template_8b18a9e8-fb2b-44a4-ab99-b8971f09d99f.docx	null
97bc2534-b797-4793-8510-36def4c28321	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 14	CDA		001	2026-02-25 08:51:57.455444+05:30	2026-02-25 12:12:32.709994+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "CITY": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "STATE": {"editable": true}}	uploads/templates/template_1f1d30c0-07ad-406e-820b-6aa157678b6a.docx	{"CITY": "site_profile.city", "SITE_NAME": "site_profile.site_name", "PI_NAME": "site_profile.pi_name", "AUTHORIZED_SIGNATORY_NAME": "site_profile. authorized_signatory_name"}
1ec8fa40-89dd-48e6-baf1-d75915425032	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing 13	CDA		001	2026-02-24 16:22:26.179291+05:30	2026-02-25 08:51:45.573094+05:30	false	null	{}	uploads/templates/template_59cb7e4b-e85c-405b-ba33-b9763a141feb.docx	null
0c8ade35-3a73-4a3a-8193-ad2ccbf398c3	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 17	CDA		001	2026-02-25 12:26:42.102968+05:30	2026-02-25 12:45:06.911773+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": false}, "AUTHORIZED_SIGNATORY_NAME": {"editable": false}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": false}, "CITY": {"editable": false}, "COUNTRY": {"editable": false}, "HOSPITAL_NAME": {"editable": false}, "PI_EMAIL": {"editable": false}, "PI_NAME": {"editable": false}, "PI_PHONE": {"editable": false}, "POSTAL_CODE": {"editable": false}, "PRIMARY_CONTRACTING_ENTITY": {"editable": false}, "STATE": {"editable": false}}	uploads/templates/template_7d16ff12-e236-4a4f-a2f4-b633da13b0d6.docx	{"CITY": "site_profile.city", "SITE_NAME": "site_profile.site_name", "STATE": "site_profile.state", "COUNTRY": "site_profile.country", "AUTHORIZED_SIGNATORY_NAME": "site_profile. authorized_signatory_name"}
f4f99032-7ac0-4fe3-8858-a0c357882acc	23b3f254-ae38-4d3f-8a0d-33d654a7f8a0	test	CDA		001	2026-03-05 17:07:48.714532+05:30	2026-03-05 17:07:48.714532+05:30	true	null	{"PI_NAME": {"editable": true}, "SITE_NAME": {"editable": true}}	uploads\\templates\\template_8e3cb125-0fca-4973-89c9-e5fe23c3454c.docx	null
316e65fb-36f2-488c-a582-a7cbb57895cd	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 19	CDA		001	2026-02-25 14:48:26.167769+05:30	2026-02-25 15:01:33.848943+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": false}, "AUTHORIZED_SIGNATORY_NAME": {"editable": false}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": false}, "CITY": {"editable": false}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "STATE": {"editable": true}}	uploads/templates/template_43c4cc49-810f-4a13-8959-6ced3f2960db.docx	{"SITE_NAME": "site_profile.site_name", "CITY": "site_profile.city", "STATE": "site_profile.state", "COUNTRY": "site_profile.country", "AUTHORIZED_SIGNATORY_NAME": "site_profile.authorized_signatory_name", "AUTHORIZED_SIGNATORY_EMAIL": "site_profile.authorized_signatory_email", "HOSPITAL_NAME": "site_profile.hospital_name", "ADDRESS_LINE_1": "site_profile. address_line_1", "POSTAL_CODE": "site_profile.postal_code"}
0f899d8f-7ec0-4e85-b3f8-922689f8497a	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing 16	CDA		001	2026-02-25 12:22:58.23332+05:30	2026-02-25 12:26:28.387152+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": false}, "AUTHORIZED_SIGNATORY_NAME": {"editable": false}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": false}, "CITY": {"editable": false}, "COUNTRY": {"editable": false}, "HOSPITAL_NAME": {"editable": false}, "PI_EMAIL": {"editable": false}, "PI_NAME": {"editable": false}, "PI_PHONE": {"editable": false}, "POSTAL_CODE": {"editable": false}, "PRIMARY_CONTRACTING_ENTITY": {"editable": false}, "STATE": {"editable": false}}	uploads/templates/template_5b2af6e4-ba45-40a5-89c8-04014ee79dd2.docx	{"SITE_NAME": "site_profile.site_name", "CITY": "site_profile.city", "COUNTRY": "site_profile.country", "STATE": "site_profile.state"}
2f28e5f0-a8b0-44fe-abb8-405f75c92795	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 15	CDA		001	2026-02-25 12:12:47.238107+05:30	2026-02-25 12:26:30.322886+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "CITY": {"editable": true}, "COUNTRY": {"editable": false}, "HOSPITAL_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "STATE": {"editable": true}}	uploads/templates/template_717147a8-3d65-4aec-830a-0ebd4b9d1a4f.docx	null
979f827b-3597-4cc7-9e25-0259638245e4	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 21	CDA		001	2026-02-25 15:31:09.130402+05:30	2026-02-25 15:52:44.687402+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "CITY": {"editable": false}, "COUNTRY": {"editable": false}, "HOSPITAL_NAME": {"editable": false}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "STATE": {"editable": true}}	uploads/templates/template_3e3cac2d-3b07-4fd8-b018-929d838380a1.docx	{"CITY": "site_profile.city", "COUNTRY": "site_profile.country", "STATE": "site_profile.state", "AUTHORIZED_SIGNATORY_EMAIL": "site_profile.authorized_signatory_email", "POSTAL_CODE": "site_profile.postal_code", "HOSPITAL_NAME": "site_profile.hospital_name", "PRIMARY_CONTRACTING_ENTITY": "site_profile.primary_contracting_entity"}
b6db30a6-78d9-4e14-a7b6-3a75bb179aa2	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 18	CDA		001	2026-02-25 12:45:20.031486+05:30	2026-02-25 14:48:02.371716+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": false}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "CITY": {"editable": false}, "COUNTRY": {"editable": false}, "HOSPITAL_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "STATE": {"editable": true}}	uploads/templates/template_1c7be7df-c484-442d-a497-df965fbb6423.docx	{"SITE_NAME": "site_profile.site_name", "CITY": "site_profile.city", "STATE": "site_profile.state", "COUNTRY": "site_profile.country"}
32cdb4c1-644d-409e-9787-b3911de7f3e4	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing 20	CDA		001	2026-02-25 15:02:11.592117+05:30	2026-02-25 15:30:51.674807+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "CITY": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "STATE": {"editable": true}}	uploads/templates/template_4fc7d0da-748b-47b4-b57d-62f3225732b3.docx	{"SITE_NAME": "site_profile.site_name", "COUNTRY": "site_profile.country", "STATE": "site_profile.state", "CITY": "site_profile.city", "ADDRESS_LINE_1": "site_profile.address_line_1", "POSTAL_CODE": "site_profile.postal_code"}
5bbcc924-a367-4f43-a5e3-e73d70984328	23b3f254-ae38-4d3f-8a0d-33d654a7f8a0	testing 1	CDA		001	2026-02-27 10:58:18.909905+05:30	2026-02-27 10:58:18.909905+05:30	true	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "CITY": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "STATE": {"editable": true}}	uploads/templates/template_7ea15630-6656-4d06-9743-4ba000e60829.docx	null
520c052c-f0fa-4b65-92ce-a9b9070a4206	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 22	CDA		001	2026-02-25 15:52:55.351027+05:30	2026-02-27 23:20:43.577891+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": false}, "AUTHORIZED_SIGNATORY_NAME": {"editable": false}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": false}, "CITY": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": false}, "PI_PHONE": {"editable": false}, "POSTAL_CODE": {"editable": false}, "PRIMARY_CONTRACTING_ENTITY": {"editable": false}, "SITE_SIGNATURE_BLOCK": {"editable": false}, "SPONSOR_SIGNATURE_BLOCK": {"editable": false}, "STATE": {"editable": false}}	uploads/templates/template_89a93a6e-0e9b-4b57-a802-0db8a3b0e456.docx	{"AUTHORIZED_SIGNATORY_EMAIL": "site_profile.authorized_signatory_email", "AUTHORIZED_SIGNATORY_NAME": "site_profile.authorized_signatory_name", "AUTHORIZED_SIGNATORY_TITLE": "site_profile.authorized_signatory_title", "CITY": "site_profile.city", "COUNTRY": "site_profile.country", "HOSPITAL_NAME": "site_profile.hospital_name", "PI_EMAIL": "site_profile.pi_email", "PI_NAME": "site_profile.pi_name", "PI_PHONE": "site_profile.pi_phone", "POSTAL_CODE": "site_profile.postal_code", "PRIMARY_CONTRACTING_ENTITY": "site_profile.primary_contracting_entity", "STATE": "site_profile.state"}
79034975-2da3-4818-afcd-1c638366a5b8	f7984413-4268-4720-a3ab-00f5b4044864	Real Azure Template	CDA		test2@example.com	2026-03-06 14:21:45.407008+05:30	2026-03-06 14:21:45.407008+05:30	true	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_f1d84d16-f5b8-4f73-8557-ad61f363f4c0.docx	null
3f3a5b06-b640-43f6-91f9-38fbc4eab1cc	f7984413-4268-4720-a3ab-00f5b4044864	test	CDA		001	2026-03-06 15:11:57.379087+05:30	2026-03-06 15:11:57.379087+05:30	true	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_fd8dff30-c4a5-4734-9adb-196e96147a60.docx	null
f0da4537-6129-45c2-a09e-77901bb6a7d4	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	alpha test	CDA		001	2026-03-09 11:23:07.906093+05:30	2026-03-09 15:04:29.821439+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_13efe2fb-dbe5-49ef-820e-91a09c3020da.docx	null
f41f5179-8a83-4c7f-becb-bd0b89454aeb	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	testing	CDA		001	2026-03-09 10:54:04.742347+05:30	2026-03-09 15:04:31.75225+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_f60b6318-d246-4764-8253-1462eccf223b.docx	null
5d548249-6fbd-40f5-9f74-50bfc1b153aa	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	azure	CDA		001	2026-03-09 10:06:35.836999+05:30	2026-03-09 15:04:33.747068+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_3be4175a-5bdb-4738-8d6d-ecf89f0e954a.docx	null
ee22a9f9-03ae-4775-a692-5b29a11761f8	f7984413-4268-4720-a3ab-00f5b4044864	Missing Blob Template	CDA		test2@example.com	2026-03-08 00:23:02.591952+05:30	2026-03-08 00:23:02.591952+05:30	true	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_a13c3895-50f6-4dfe-ad37-1ddd47e8c275.docx	null
58f7b845-eec9-4fa6-a5a2-46d895f2d975	f7984413-4268-4720-a3ab-00f5b4044864	Second Missing Blob Template	CDA		test2@example.com	2026-03-08 00:27:25.249619+05:30	2026-03-08 00:27:25.249619+05:30	true	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_08685176-bb7e-45f0-8862-d1720eba515b.docx	null
de19fd59-c0ab-4878-a868-58a021659466	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	demo	CDA		001	2026-03-06 12:03:34.078931+05:30	2026-03-09 15:03:59.793174+05:30	false	null	{}	uploads\\templates\\template_253e7fa8-9be8-4638-9d0c-218ffc2553bd.docx	null
50334d96-83ae-4c9f-aaa9-fcbf3da10f18	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	Testing 23	CDA		001	2026-02-27 23:20:54.999448+05:30	2026-03-09 15:04:02.549674+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "CITY": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": false}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "STATE": {"editable": true}}	uploads/templates/template_12caf4fa-f06b-4ad4-ab34-4c120a23168f.docx	{"COUNTRY": "site_profile.country", "CITY": "site_profile.city"}
8ef8cfc5-e001-483a-a74f-d3304d3f9b8b	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	demo2	CDA		001	2026-03-06 12:06:33.255024+05:30	2026-03-09 15:04:12.080942+05:30	false	null	{}	uploads\\templates\\template_36fb9bbf-9552-46cb-b787-aff893a2c3f4.docx	null
5bb9a746-5f9a-4c05-920a-716a6ec102d2	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	final_demo	CDA		001	2026-03-06 12:13:58.821764+05:30	2026-03-09 15:04:15.034158+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_08685176-bb7e-45f0-8862-d1720eba515b.docx	null
2cb59857-8de8-4cc5-a865-860589a4f191	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	test_azure	CDA		001	2026-03-06 12:19:44.112034+05:30	2026-03-09 15:04:16.84558+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_f1d84d16-f5b8-4f73-8557-ad61f363f4c0.docx	null
9bb63c7a-e597-4731-97c8-6b80d22dee9d	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	test	CDA		001	2026-03-06 12:44:09.972507+05:30	2026-03-09 15:04:18.693392+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_08685176-bb7e-45f0-8862-d1720eba515b.docx	null
efea1a84-70d3-4ccf-b3c7-5dce5d9e73d3	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	new	CDA		001	2026-03-06 13:32:51.970709+05:30	2026-03-09 15:04:21.162467+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_08685176-bb7e-45f0-8862-d1720eba515b.docx	{}
4a23a141-a65e-4fa9-8415-01862821b0ec	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	summary	CTA		001	2026-03-09 14:33:11.107282+05:30	2026-03-09 15:04:25.023559+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CTA__summary.docx	null
ef70e6a4-f3fc-4d76-8c45-7ddb63b8e4f2	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	tt	CDA		001	2026-03-09 12:08:05.491998+05:30	2026-03-09 15:04:26.690316+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_25acb578-1256-4235-aff4-a28190247402.docx	null
a5d0c135-0411-4512-b289-eefa6928666a	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	beta test	CDA		001	2026-03-09 11:23:54.152199+05:30	2026-03-09 15:04:28.377487+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/template_639474d4-0ee8-4204-8378-eb395121f23d.docx	null
e6c0a082-577d-42ce-9a6f-ac72bdce6cee	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	aa	CDA		001	2026-03-09 15:27:56.045366+05:30	2026-03-10 09:27:47.438129+05:30	false	null	{"STATE": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "CITY": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_PHONE": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "POSTAL_CODE": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__aa.docx	{"AUTHORIZED_SIGNATORY_NAME": "site_profile.site_name", "CITY": "site_profile.city"}
3fcc1e34-17f3-4aab-a77a-b2b6704c3103	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	ccc	CDA		001	2026-03-09 15:59:38.754717+05:30	2026-03-10 09:27:50.106978+05:30	false	null	{"SITE_SIGNATURE_BLOCK": {"editable": true}, "PI_PHONE": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "PI_EMAIL": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "STATE": {"editable": true}, "COUNTRY": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "CITY": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__ccc.docx	{"CITY": "site_profile.city", "COUNTRY": "site_profile.country"}
0e05980c-c352-4708-a3cd-46268085d04c	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	azureTest	BUDGET		001	2026-03-09 15:05:19.417567+05:30	2026-03-10 09:27:44.70862+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__BUDGET__azureTest.docx	{}
c707d386-75dd-49d9-9930-c528763cf05f	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	n	CDA		001	2026-03-10 14:16:25.172097+05:30	2026-03-11 11:52:42.191878+05:30	false	null	{"AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "PI_EMAIL": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "ADDRESS_LINE_1": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "POSTAL_CODE": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "CITY": {"editable": true}, "STATE": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__n.docx	{"ADDRESS_LINE_1": "site_profile.address_line_1", "CITY": "site_profile.city"}
7a773898-4141-4303-a520-09d886c1b6a5	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	TestAzureDoc	CTA		001	2026-03-10 10:01:26.232943+05:30	2026-03-10 12:49:00.060171+05:30	false	null	{"PI_PHONE": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "POSTAL_CODE": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "CITY": {"editable": true}, "STATE": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "COUNTRY": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CTA__TestAzureDoc.docx	{"CITY": "site_profile.city", "COUNTRY": "site_profile.country", "HOSPITAL_NAME": "site_profile.hospital_name", "PI_EMAIL": "site_profile.pi_email", "PI_NAME": "site_profile.pi_name", "PI_PHONE": "site_profile.pi_phone", "POSTAL_CODE": "site_profile.postal_code", "STATE": "site_profile.state"}
28e09fad-71ed-4546-b898-1ecb0874ac87	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	mk	CDA		001	2026-03-09 16:14:21.230332+05:30	2026-03-10 09:27:51.731741+05:30	false	null	{"AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "PI_PHONE": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "PI_EMAIL": {"editable": true}, "STATE": {"editable": true}, "PI_NAME": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "CITY": {"editable": true}, "POSTAL_CODE": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__mk.docx	{"PI_NAME": "site_profile.pi_name", "HOSPITAL_NAME": "site_profile.hospital_name", "CITY": "site_profile.city"}
e155ac90-2bac-4bde-ab69-1a044af187a8	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	xs	CDA		001	2026-03-09 16:38:17.56986+05:30	2026-03-10 09:27:54.088557+05:30	false	null	{"CITY": {"editable": true}, "PI_PHONE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "PI_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "POSTAL_CODE": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "COUNTRY": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "STATE": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__xs.docx	{"CITY": "site_profile.city"}
7c7d4028-7e60-4929-9b4a-df930569fa24	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	cv	CDA		001	2026-03-09 16:44:30.792486+05:30	2026-03-10 09:27:57.314835+05:30	false	null	{}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__cv.docx	null
0d361ca8-a433-4d9d-b8b6-47b9cbcb2d82	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	abc	CDA		001	2026-03-09 16:55:40.36896+05:30	2026-03-10 09:27:59.889114+05:30	false	null	{"COUNTRY": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "STATE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "PI_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "POSTAL_CODE": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "PI_PHONE": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "CITY": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__abc.docx	{"COUNTRY": "site_profile.country", "CITY": "site_profile.city", "PI_PHONE": "site_profile.pi_phone", "HOSPITAL_NAME": "site_profile.hospital_name"}
63dcbd41-9ba1-4c1a-9119-faf63c1e2d5a	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	mmmm	OTHER		001	2026-03-09 23:24:44.07111+05:30	2026-03-10 10:02:44.972727+05:30	false	null	{"CITY": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "PI_EMAIL": {"editable": true}, "STATE": {"editable": true}, "COUNTRY": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "POSTAL_CODE": {"editable": true}, "PI_NAME": {"editable": true}, "PI_PHONE": {"editable": true}, "HOSPITAL_NAME": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__OTHER__mmmm.docx	{"COUNTRY": "site_profile.country", "HOSPITAL_NAME": "site_profile.hospital_name", "PI_EMAIL": "site_profile.pi_email", "PI_NAME": "site_profile.pi_name", "CITY": "site_profile.city", "STATE": "site_profile.state", "PI_PHONE": "site_profile.pi_phone", "POSTAL_CODE": "site_profile.postal_code"}
a3f2e8bf-ed4c-4422-a731-deb0bad74f57	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	JK	CDA		001	2026-03-10 12:02:11.0486+05:30	2026-03-10 12:48:55.366479+05:30	false	null	{"POSTAL_CODE": {"editable": true}, "PI_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "PI_PHONE": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "CITY": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "ADDRESS_LINE_1": {"editable": true}, "COUNTRY": {"editable": true}, "STATE": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__JK.docx	{"ADDRESS_LINE_1": "site_profile.address_line_1", "CITY": "site_profile.city", "COUNTRY": "site_profile.country", "HOSPITAL_NAME": "site_profile.hospital_name", "PI_EMAIL": "site_profile.pi_email", "PI_NAME": "site_profile.pi_name", "PI_PHONE": "site_profile.pi_phone", "POSTAL_CODE": "site_profile.postal_code", "STATE": "site_profile.state"}
5747c4e3-103d-4787-8697-25f371025330	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	mnn	CDA		001	2026-03-10 11:52:24.547008+05:30	2026-03-10 12:48:57.06241+05:30	false	null	{"POSTAL_CODE": {"editable": true}, "PI_NAME": {"editable": false}, "PI_EMAIL": {"editable": false}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "PI_PHONE": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "CITY": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "ADDRESS_LINE_1": {"editable": true}, "COUNTRY": {"editable": true}, "STATE": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__mnn.docx	{"ADDRESS_LINE_1": "site_profile.address_line_1", "CITY": "site_profile.city", "COUNTRY": "site_profile.country", "HOSPITAL_NAME": "site_profile.hospital_name", "PI_EMAIL": "site_profile.pi_email", "PI_NAME": "site_profile.pi_name", "PI_PHONE": "site_profile.pi_phone", "POSTAL_CODE": "site_profile.postal_code", "STATE": "site_profile.state"}
2c222064-ef48-4173-ae30-823e64131d96	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	azureTesting	CDA		001	2026-03-09 15:51:24.101573+05:30	2026-03-10 12:50:06.664418+05:30	false	null	{"STATE": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "CITY": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_PHONE": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "PI_NAME": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "POSTAL_CODE": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__azureTesting.docx	{"CITY": "site_profile.city", "PI_EMAIL": "site_profile.pi_name", "PI_PHONE": "site_profile.pi_phone"}
2fd994c7-9aff-454c-839f-4c9f3e9ef731	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	v	CDA		001	2026-03-10 11:27:32.630177+05:30	2026-03-10 12:48:58.517688+05:30	false	null	{"POSTAL_CODE": {"editable": true}, "PI_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "PI_PHONE": {"editable": false}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "CITY": {"editable": false}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "HOSPITAL_NAME": {"editable": false}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "ADDRESS_LINE_1": {"editable": true}, "COUNTRY": {"editable": true}, "STATE": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__v.docx	{"ADDRESS_LINE_1": "site_profile.address_line_1", "HOSPITAL_NAME": "site_profile.hospital_name", "PI_EMAIL": "site_profile.pi_email", "PI_NAME": "site_profile.pi_email", "PI_PHONE": "site_profile.pi_phone", "POSTAL_CODE": "site_profile.postal_code", "CITY": "site_profile.city", "STATE": "site_profile.state", "COUNTRY": "site_profile.country"}
e8d1acd8-4bbb-44cc-bf09-cc457026bdec	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	feature 	CTA		001	2026-03-10 12:50:35.255554+05:30	2026-03-11 11:52:36.268336+05:30	false	null	{"AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "PI_EMAIL": {"editable": true}, "PI_PHONE": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "POSTAL_CODE": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "STATE": {"editable": true}, "ADDRESS_LINE_1": {"editable": true}, "COUNTRY": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "PI_NAME": {"editable": true}, "CITY": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CTA__feature.docx	{"CITY": "site_profile.city"}
cfaf497e-32e9-41fa-a504-7896218f64cb	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	new	CTA		001	2026-03-10 13:57:23.482854+05:30	2026-03-11 11:52:38.789481+05:30	false	null	{"SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "ADDRESS_LINE_1": {"editable": true}, "STATE": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "POSTAL_CODE": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "PI_PHONE": {"editable": true}, "COUNTRY": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "CITY": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "PI_NAME": {"editable": true}, "PI_EMAIL": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CTA__new.docx	{"CITY": "site_profile.city", "COUNTRY": "site_profile.country", "HOSPITAL_NAME": "site_profile.hospital_name", "PI_EMAIL": "site_profile.pi_email", "STATE": "site_profile.state", "ADDRESS_LINE_1": "site_profile.address_line_1", "PI_PHONE": "site_profile.pi_phone", "POSTAL_CODE": "site_profile.postal_code", "PI_NAME": "site_profile.pi_name"}
fccf1287-9361-4be3-b6fc-8c979e60c2c5	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	versioning	CDA		001	2026-03-11 11:53:09.520386+05:30	2026-03-11 11:55:16.470961+05:30	true	null	{"PI_NAME": {"editable": false}, "CITY": {"editable": true}, "ADDRESS_LINE_1": {"editable": true}, "PRIMARY_CONTRACTING_ENTITY": {"editable": true}, "AUTHORIZED_SIGNATORY_TITLE": {"editable": true}, "SITE_SIGNATURE_BLOCK": {"editable": true}, "AUTHORIZED_SIGNATORY_EMAIL": {"editable": true}, "PI_EMAIL": {"editable": false}, "PI_PHONE": {"editable": false}, "STATE": {"editable": true}, "AUTHORIZED_SIGNATORY_NAME": {"editable": true}, "POSTAL_CODE": {"editable": true}, "SPONSOR_SIGNATURE_BLOCK": {"editable": true}, "HOSPITAL_NAME": {"editable": true}, "COUNTRY": {"editable": true}}	https://datasetaws.blob.core.windows.net/crm-templates/MK_6482__Site_01__CDA__versioning.docx	{"CITY": "site_profile.city", "COUNTRY": "site_profile.country", "HOSPITAL_NAME": "site_profile.hospital_name", "PI_EMAIL": "site_profile.pi_email", "PI_NAME": "site_profile.pi_name", "PI_PHONE": "site_profile.pi_phone", "ADDRESS_LINE_1": "site_profile.address_line_1", "POSTAL_CODE": "site_profile.postal_code", "STATE": "site_profile.state"}
\.


--
-- TOC entry 5416 (class 0 OID 18089)
-- Dependencies: 244
-- Data for Name: user_profiles; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.user_profiles (id, user_id, name, address, phone, email, affiliation, specialty, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 5417 (class 0 OID 18098)
-- Dependencies: 245
-- Data for Name: user_role_assignments; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.user_role_assignments (id, user_id, role, site_id, study_id, assigned_by, assigned_at, created_at, updated_at) FROM stdin;
f8f00f7c-0aaa-477c-97d5-292fb895fcb3	001	cra	\N	f7984413-4268-4720-a3ab-00f5b4044864	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
246ebeb5-1de5-4a23-9cd8-12b908d48703	001	cra	\N	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
ca5ba152-73e8-47fc-8896-72f1141eb497	001	cra	\N	7b502ee0-0e4b-4408-b300-f6b52194013d	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
ce13882e-b91f-403f-860d-0147794aecce	001	cra	\N	0da0799e-04fa-4ab0-9711-0e12c122dd4a	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
c1fe05b4-a748-4ece-8c11-92019273cb91	001	cra	\N	98e0b119-d77b-4185-8846-989013874b9f	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
336b2b81-f325-4d6a-8b68-761492ccb77a	001	cra	\N	92807a47-a0ee-4e84-8a85-703146e0c220	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
edc17a16-2266-4e16-a41f-08da9dccdda3	001	cra	\N	4bd0aae0-673b-4901-8854-8c5e0772231f	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
fbe8fd19-e763-41ca-8a00-410017738b75	001	cra	\N	23b3f254-ae38-4d3f-8a0d-33d654a7f8a0	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
836e055d-a4ae-4fe4-be28-6dc49b60fef8	001	cra	\N	2b079c1e-16de-4b5a-a8ac-c76291120291	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
0bad5992-f430-4447-9ad2-406e0d0a25ea	001	cra	\N	c058a05b-a1d6-412d-b733-28f629fcd37f	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
8b361f8f-6f1f-4753-84b1-bca825867004	001	cra	\N	96a8e9b5-530c-4965-8062-90b9fb2f1ecd	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
2ecb66f6-7aa2-4a1c-8a3d-17358d7fad72	001	cra	\N	01ea63b5-7a62-42ba-b488-dfa189ddae75	system	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30	2026-01-20 13:04:02.960126+05:30
6a39c3c2-3d99-4bb2-b86e-086d439111ee	001	cra	f801bc3d-1c18-4903-982b-57b28dffd1a4	\N	system	2026-01-20 13:12:13.051649+05:30	2026-01-20 13:12:13.051649+05:30	2026-01-20 13:12:13.051649+05:30
f8ad51f9-109f-4da4-859d-509101edf319	002	study_manager	f801bc3d-1c18-4903-982b-57b28dffd1a4	\N	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
b9e3249f-aa8b-4b72-984e-bce26328c257	002	cra	\N	f7984413-4268-4720-a3ab-00f5b4044864	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
0996c648-fc85-4e5e-977f-22c72910d7c6	002	cra	\N	206942ca-6d36-4f6d-ae1f-f0d661ac31cd	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
6e65e304-2113-413b-8a00-7b32530f6073	002	cra	\N	7b502ee0-0e4b-4408-b300-f6b52194013d	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
c6a1432d-a628-42e0-8bba-511183ba0862	002	cra	\N	0da0799e-04fa-4ab0-9711-0e12c122dd4a	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
b79a0a6a-e194-422c-b5a7-76754c08b7a3	002	cra	\N	98e0b119-d77b-4185-8846-989013874b9f	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
7cf58730-f9e5-4103-a811-377a8068e8f4	002	cra	\N	92807a47-a0ee-4e84-8a85-703146e0c220	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
403f47ea-7ecd-4acc-bd5b-569b1a7d3ff4	002	cra	\N	4bd0aae0-673b-4901-8854-8c5e0772231f	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
f24e098a-13b4-4ec5-b9e8-b920dbc065ed	002	cra	\N	23b3f254-ae38-4d3f-8a0d-33d654a7f8a0	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
74b0704c-6517-4ff0-ba17-6b7d065fecff	002	cra	\N	2b079c1e-16de-4b5a-a8ac-c76291120291	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
8ad36c68-130e-4fec-b9e1-5253f137a81a	002	cra	\N	c058a05b-a1d6-412d-b733-28f629fcd37f	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
68c868aa-076e-4eca-8ffc-2944b3931918	002	cra	\N	96a8e9b5-530c-4965-8062-90b9fb2f1ecd	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
258dc985-0b45-4d3e-9115-f32f00097291	002	cra	\N	01ea63b5-7a62-42ba-b488-dfa189ddae75	001	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30	2026-02-12 10:30:05.770407+05:30
\.


--
-- TOC entry 5418 (class 0 OID 18111)
-- Dependencies: 246
-- Data for Name: user_sites; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.user_sites (id, user_id, site_id, role, assigned_at) FROM stdin;
e90797b5-0460-47f0-a1fe-4a9e2ed5232b	001	f801bc3d-1c18-4903-982b-57b28dffd1a4	coordinator	2026-01-20 13:12:13.051649+05:30
\.


--
-- TOC entry 5419 (class 0 OID 18118)
-- Dependencies: 247
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.users (id, user_id, name, email, password_hash, role, is_privileged, created_at) FROM stdin;
adb4c5ae-2b90-493e-8ecb-6dcb01cceb4b	001	Labesh Kumar Garg	labeshg@dizzaroo.com	$2b$12$VcMzcqmauxbtrdsj5XwNgeRKPMOHVkpsN7i23PaMGlvF5niNttqOq	PARTICIPANT	false	2026-01-07 21:40:11.956293+05:30
ba63321c-629d-41e2-b66e-dc7e7a9cf851	002	Test	labesh.garg@gmail.com	$2b$12$HeQMv4ksYFoni3Wr73WLaOUTVkyJc6jGg8nMxA4wQWQq2Ixrs/ejK	PARTICIPANT	false	2026-02-12 10:27:14.040594+05:30
b7b2a6a1-7eeb-4080-b44a-c69302f5b7aa	testuser	Test User	test@example.com	$2b$12$hNKFgQ1Q6DoeuweF1O7tuekq9LiptH3xu6HqlH3V8a5GwLnJY6Kfa	PARTICIPANT	false	2026-03-05 14:31:44.801764+05:30
7b7f7a24-6a13-4878-ba35-e21a642bcc9a	testuser2	Test User 2	test2@example.com	$2b$12$Qe4CCDs1/Hk4.GrXwgLWNOSPf3gX4z3rzZCLiCW26VMtTpMdXOgs6	PARTICIPANT	false	2026-03-05 14:53:23.142444+05:30
\.


--
-- TOC entry 5089 (class 2606 OID 18131)
-- Name: agreement_comments agreement_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_comments
    ADD CONSTRAINT agreement_comments_pkey PRIMARY KEY (id);


--
-- TOC entry 5094 (class 2606 OID 18133)
-- Name: agreement_documents agreement_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_documents
    ADD CONSTRAINT agreement_documents_pkey PRIMARY KEY (id);


--
-- TOC entry 5100 (class 2606 OID 18135)
-- Name: agreement_inline_comments agreement_inline_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_inline_comments
    ADD CONSTRAINT agreement_inline_comments_pkey PRIMARY KEY (id);


--
-- TOC entry 5104 (class 2606 OID 18137)
-- Name: agreement_signed_documents agreement_signed_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_signed_documents
    ADD CONSTRAINT agreement_signed_documents_pkey PRIMARY KEY (id);


--
-- TOC entry 5107 (class 2606 OID 18139)
-- Name: agreements agreements_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreements
    ADD CONSTRAINT agreements_pkey PRIMARY KEY (id);


--
-- TOC entry 5114 (class 2606 OID 18141)
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 5116 (class 2606 OID 18143)
-- Name: chat_documents chat_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.chat_documents
    ADD CONSTRAINT chat_documents_pkey PRIMARY KEY (id);


--
-- TOC entry 5118 (class 2606 OID 18145)
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- TOC entry 5120 (class 2606 OID 18147)
-- Name: conversation_access conversation_access_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.conversation_access
    ADD CONSTRAINT conversation_access_pkey PRIMARY KEY (id);


--
-- TOC entry 5122 (class 2606 OID 18149)
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- TOC entry 5124 (class 2606 OID 18151)
-- Name: feasibility_attachments feasibility_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.feasibility_attachments
    ADD CONSTRAINT feasibility_attachments_pkey PRIMARY KEY (id);


--
-- TOC entry 5126 (class 2606 OID 18153)
-- Name: feasibility_attachments feasibility_attachments_study_site_id_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.feasibility_attachments
    ADD CONSTRAINT feasibility_attachments_study_site_id_key UNIQUE (study_site_id);


--
-- TOC entry 5129 (class 2606 OID 18155)
-- Name: feasibility_requests feasibility_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.feasibility_requests
    ADD CONSTRAINT feasibility_requests_pkey PRIMARY KEY (id);


--
-- TOC entry 5131 (class 2606 OID 18157)
-- Name: feasibility_requests feasibility_requests_token_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.feasibility_requests
    ADD CONSTRAINT feasibility_requests_token_key UNIQUE (token);


--
-- TOC entry 5137 (class 2606 OID 18159)
-- Name: feasibility_responses feasibility_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.feasibility_responses
    ADD CONSTRAINT feasibility_responses_pkey PRIMARY KEY (id);


--
-- TOC entry 5141 (class 2606 OID 18161)
-- Name: iis_studies iis_studies_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.iis_studies
    ADD CONSTRAINT iis_studies_pkey PRIMARY KEY (id);


--
-- TOC entry 5145 (class 2606 OID 18163)
-- Name: project_feasibility_custom_questions project_feasibility_custom_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.project_feasibility_custom_questions
    ADD CONSTRAINT project_feasibility_custom_questions_pkey PRIMARY KEY (id);


--
-- TOC entry 5147 (class 2606 OID 18165)
-- Name: rd_studies rd_studies_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.rd_studies
    ADD CONSTRAINT rd_studies_pkey PRIMARY KEY (id);


--
-- TOC entry 5154 (class 2606 OID 18167)
-- Name: site_documents site_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_documents
    ADD CONSTRAINT site_documents_pkey PRIMARY KEY (id);


--
-- TOC entry 5157 (class 2606 OID 18169)
-- Name: site_profiles site_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_profiles
    ADD CONSTRAINT site_profiles_pkey PRIMARY KEY (id);


--
-- TOC entry 5159 (class 2606 OID 18171)
-- Name: site_profiles site_profiles_site_id_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_profiles
    ADD CONSTRAINT site_profiles_site_id_key UNIQUE (site_id);


--
-- TOC entry 5161 (class 2606 OID 18173)
-- Name: site_status_history site_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_status_history
    ADD CONSTRAINT site_status_history_pkey PRIMARY KEY (id);


--
-- TOC entry 5163 (class 2606 OID 18175)
-- Name: site_statuses site_statuses_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_statuses
    ADD CONSTRAINT site_statuses_pkey PRIMARY KEY (id);


--
-- TOC entry 5165 (class 2606 OID 18177)
-- Name: site_statuses site_statuses_site_id_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_statuses
    ADD CONSTRAINT site_statuses_site_id_key UNIQUE (site_id);


--
-- TOC entry 5171 (class 2606 OID 18179)
-- Name: site_workflow_steps site_workflow_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_workflow_steps
    ADD CONSTRAINT site_workflow_steps_pkey PRIMARY KEY (id);


--
-- TOC entry 5175 (class 2606 OID 18181)
-- Name: sites sites_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT sites_pkey PRIMARY KEY (id);


--
-- TOC entry 5177 (class 2606 OID 18183)
-- Name: sites sites_site_id_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT sites_site_id_key UNIQUE (site_id);


--
-- TOC entry 5179 (class 2606 OID 18185)
-- Name: studies studies_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.studies
    ADD CONSTRAINT studies_pkey PRIMARY KEY (id);


--
-- TOC entry 5181 (class 2606 OID 18187)
-- Name: studies studies_study_id_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.studies
    ADD CONSTRAINT studies_study_id_key UNIQUE (study_id);


--
-- TOC entry 5185 (class 2606 OID 18189)
-- Name: study_sites study_sites_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.study_sites
    ADD CONSTRAINT study_sites_pkey PRIMARY KEY (id);


--
-- TOC entry 5191 (class 2606 OID 18191)
-- Name: study_templates study_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.study_templates
    ADD CONSTRAINT study_templates_pkey PRIMARY KEY (id);


--
-- TOC entry 5098 (class 2606 OID 18193)
-- Name: agreement_documents uq_agreement_document_version; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_documents
    ADD CONSTRAINT uq_agreement_document_version UNIQUE (agreement_id, version_number);


--
-- TOC entry 5187 (class 2606 OID 18195)
-- Name: study_sites uq_study_site; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.study_sites
    ADD CONSTRAINT uq_study_site UNIQUE (study_id, site_id);


--
-- TOC entry 5193 (class 2606 OID 18197)
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (id);


--
-- TOC entry 5195 (class 2606 OID 18199)
-- Name: user_profiles user_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_key UNIQUE (user_id);


--
-- TOC entry 5202 (class 2606 OID 18201)
-- Name: user_role_assignments user_role_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_role_assignments
    ADD CONSTRAINT user_role_assignments_pkey PRIMARY KEY (id);


--
-- TOC entry 5204 (class 2606 OID 18203)
-- Name: user_sites user_sites_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_sites
    ADD CONSTRAINT user_sites_pkey PRIMARY KEY (id);


--
-- TOC entry 5206 (class 2606 OID 18205)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 5208 (class 2606 OID 18207)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 5210 (class 2606 OID 18209)
-- Name: users users_user_id_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_user_id_key UNIQUE (user_id);


--
-- TOC entry 5095 (class 1259 OID 18210)
-- Name: idx_agreement_documents_agreement_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_agreement_documents_agreement_id ON public.agreement_documents USING btree (agreement_id);


--
-- TOC entry 5096 (class 1259 OID 18211)
-- Name: idx_agreement_documents_template_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_agreement_documents_template_id ON public.agreement_documents USING btree (created_from_template_id);


--
-- TOC entry 5105 (class 1259 OID 18212)
-- Name: idx_agreement_signed_documents_agreement_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_agreement_signed_documents_agreement_id ON public.agreement_signed_documents USING btree (agreement_id);


--
-- TOC entry 5101 (class 1259 OID 18213)
-- Name: idx_inline_comments_agreement_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_inline_comments_agreement_id ON public.agreement_inline_comments USING btree (agreement_id);


--
-- TOC entry 5102 (class 1259 OID 18214)
-- Name: idx_inline_comments_document_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_inline_comments_document_id ON public.agreement_inline_comments USING btree (document_id);


--
-- TOC entry 5188 (class 1259 OID 18215)
-- Name: idx_study_templates_is_active; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_study_templates_is_active ON public.study_templates USING btree (is_active);


--
-- TOC entry 5189 (class 1259 OID 18216)
-- Name: idx_study_templates_study_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_study_templates_study_id ON public.study_templates USING btree (study_id);


--
-- TOC entry 5090 (class 1259 OID 18217)
-- Name: ix_agreement_comments_agreement_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_agreement_comments_agreement_id ON public.agreement_comments USING btree (agreement_id);


--
-- TOC entry 5091 (class 1259 OID 18218)
-- Name: ix_agreement_comments_created_at; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_agreement_comments_created_at ON public.agreement_comments USING btree (created_at DESC);


--
-- TOC entry 5092 (class 1259 OID 18219)
-- Name: ix_agreement_comments_version_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_agreement_comments_version_id ON public.agreement_comments USING btree (version_id);


--
-- TOC entry 5108 (class 1259 OID 18220)
-- Name: ix_agreements_created_at; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_agreements_created_at ON public.agreements USING btree (created_at DESC);


--
-- TOC entry 5109 (class 1259 OID 18221)
-- Name: ix_agreements_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_agreements_site_id ON public.agreements USING btree (site_id);


--
-- TOC entry 5110 (class 1259 OID 18222)
-- Name: ix_agreements_status; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_agreements_status ON public.agreements USING btree (status);


--
-- TOC entry 5111 (class 1259 OID 18223)
-- Name: ix_agreements_study_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_agreements_study_site_id ON public.agreements USING btree (study_site_id);


--
-- TOC entry 5127 (class 1259 OID 18224)
-- Name: ix_feasibility_attachments_study_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_feasibility_attachments_study_site_id ON public.feasibility_attachments USING btree (study_site_id);


--
-- TOC entry 5132 (class 1259 OID 18225)
-- Name: ix_feasibility_requests_email; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_feasibility_requests_email ON public.feasibility_requests USING btree (email);


--
-- TOC entry 5133 (class 1259 OID 18226)
-- Name: ix_feasibility_requests_status; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_feasibility_requests_status ON public.feasibility_requests USING btree (status);


--
-- TOC entry 5134 (class 1259 OID 18227)
-- Name: ix_feasibility_requests_study_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_feasibility_requests_study_site_id ON public.feasibility_requests USING btree (study_site_id);


--
-- TOC entry 5135 (class 1259 OID 18228)
-- Name: ix_feasibility_requests_token; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_feasibility_requests_token ON public.feasibility_requests USING btree (token);


--
-- TOC entry 5138 (class 1259 OID 18229)
-- Name: ix_feasibility_responses_question_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_feasibility_responses_question_id ON public.feasibility_responses USING btree (question_id);


--
-- TOC entry 5139 (class 1259 OID 18230)
-- Name: ix_feasibility_responses_request_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_feasibility_responses_request_id ON public.feasibility_responses USING btree (request_id);


--
-- TOC entry 5142 (class 1259 OID 18231)
-- Name: ix_project_feasibility_custom_questions_study_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_project_feasibility_custom_questions_study_id ON public.project_feasibility_custom_questions USING btree (study_id);


--
-- TOC entry 5143 (class 1259 OID 18232)
-- Name: ix_project_feasibility_custom_questions_workflow_step; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_project_feasibility_custom_questions_workflow_step ON public.project_feasibility_custom_questions USING btree (workflow_step);


--
-- TOC entry 5148 (class 1259 OID 18233)
-- Name: ix_site_documents_category; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_documents_category ON public.site_documents USING btree (category);


--
-- TOC entry 5149 (class 1259 OID 18234)
-- Name: ix_site_documents_document_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_documents_document_type ON public.site_documents USING btree (document_type);


--
-- TOC entry 5150 (class 1259 OID 18235)
-- Name: ix_site_documents_review_status; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_documents_review_status ON public.site_documents USING btree (review_status);


--
-- TOC entry 5151 (class 1259 OID 18236)
-- Name: ix_site_documents_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_documents_site_id ON public.site_documents USING btree (site_id);


--
-- TOC entry 5152 (class 1259 OID 18237)
-- Name: ix_site_documents_uploaded_at; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_documents_uploaded_at ON public.site_documents USING btree (uploaded_at DESC);


--
-- TOC entry 5155 (class 1259 OID 18238)
-- Name: ix_site_profiles_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_profiles_site_id ON public.site_profiles USING btree (site_id);


--
-- TOC entry 5166 (class 1259 OID 18239)
-- Name: ix_site_workflow_steps_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_workflow_steps_site_id ON public.site_workflow_steps USING btree (site_id);


--
-- TOC entry 5167 (class 1259 OID 18240)
-- Name: ix_site_workflow_steps_status; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_workflow_steps_status ON public.site_workflow_steps USING btree (status);


--
-- TOC entry 5168 (class 1259 OID 18241)
-- Name: ix_site_workflow_steps_step_name; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_workflow_steps_step_name ON public.site_workflow_steps USING btree (step_name);


--
-- TOC entry 5169 (class 1259 OID 18242)
-- Name: ix_site_workflow_steps_study_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_site_workflow_steps_study_site_id ON public.site_workflow_steps USING btree (study_site_id);


--
-- TOC entry 5182 (class 1259 OID 18243)
-- Name: ix_study_sites_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_study_sites_site_id ON public.study_sites USING btree (site_id);


--
-- TOC entry 5183 (class 1259 OID 18244)
-- Name: ix_study_sites_study_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_study_sites_study_id ON public.study_sites USING btree (study_id);


--
-- TOC entry 5196 (class 1259 OID 18245)
-- Name: ix_user_role_assignments_role; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_user_role_assignments_role ON public.user_role_assignments USING btree (role);


--
-- TOC entry 5197 (class 1259 OID 18246)
-- Name: ix_user_role_assignments_site_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_user_role_assignments_site_id ON public.user_role_assignments USING btree (site_id);


--
-- TOC entry 5198 (class 1259 OID 18247)
-- Name: ix_user_role_assignments_study_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_user_role_assignments_study_id ON public.user_role_assignments USING btree (study_id);


--
-- TOC entry 5199 (class 1259 OID 18248)
-- Name: ix_user_role_assignments_user_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_user_role_assignments_user_id ON public.user_role_assignments USING btree (user_id);


--
-- TOC entry 5200 (class 1259 OID 18249)
-- Name: ix_user_role_assignments_user_role; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_user_role_assignments_user_role ON public.user_role_assignments USING btree (user_id, role);


--
-- TOC entry 5112 (class 1259 OID 18250)
-- Name: uq_agreements_study_site_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX uq_agreements_study_site_type ON public.agreements USING btree (study_id, site_id, agreement_type) WHERE ((study_id IS NOT NULL) AND (agreement_type IS NOT NULL));


--
-- TOC entry 5172 (class 1259 OID 18251)
-- Name: uq_site_workflow_step; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX uq_site_workflow_step ON public.site_workflow_steps USING btree (site_id, step_name) WHERE (site_id IS NOT NULL);


--
-- TOC entry 5173 (class 1259 OID 18252)
-- Name: uq_study_site_workflow_step; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX uq_study_site_workflow_step ON public.site_workflow_steps USING btree (study_site_id, step_name) WHERE (study_site_id IS NOT NULL);


--
-- TOC entry 5211 (class 2606 OID 18253)
-- Name: agreement_comments agreement_comments_agreement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_comments
    ADD CONSTRAINT agreement_comments_agreement_id_fkey FOREIGN KEY (agreement_id) REFERENCES public.agreements(id) ON DELETE CASCADE;


--
-- TOC entry 5212 (class 2606 OID 18258)
-- Name: agreement_documents agreement_documents_agreement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_documents
    ADD CONSTRAINT agreement_documents_agreement_id_fkey FOREIGN KEY (agreement_id) REFERENCES public.agreements(id) ON DELETE CASCADE;


--
-- TOC entry 5213 (class 2606 OID 18263)
-- Name: agreement_documents agreement_documents_created_from_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_documents
    ADD CONSTRAINT agreement_documents_created_from_template_id_fkey FOREIGN KEY (created_from_template_id) REFERENCES public.study_templates(id) ON DELETE SET NULL;


--
-- TOC entry 5214 (class 2606 OID 18268)
-- Name: agreement_inline_comments agreement_inline_comments_agreement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_inline_comments
    ADD CONSTRAINT agreement_inline_comments_agreement_id_fkey FOREIGN KEY (agreement_id) REFERENCES public.agreements(id) ON DELETE CASCADE;


--
-- TOC entry 5215 (class 2606 OID 18273)
-- Name: agreement_inline_comments agreement_inline_comments_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_inline_comments
    ADD CONSTRAINT agreement_inline_comments_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.agreement_documents(id) ON DELETE CASCADE;


--
-- TOC entry 5217 (class 2606 OID 18278)
-- Name: agreements agreements_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreements
    ADD CONSTRAINT agreements_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id) ON DELETE CASCADE;


--
-- TOC entry 5218 (class 2606 OID 18283)
-- Name: agreements agreements_study_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreements
    ADD CONSTRAINT agreements_study_id_fkey FOREIGN KEY (study_id) REFERENCES public.studies(id);


--
-- TOC entry 5219 (class 2606 OID 18288)
-- Name: agreements agreements_study_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreements
    ADD CONSTRAINT agreements_study_site_id_fkey FOREIGN KEY (study_site_id) REFERENCES public.study_sites(id);


--
-- TOC entry 5220 (class 2606 OID 18293)
-- Name: chat_documents chat_documents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.chat_documents
    ADD CONSTRAINT chat_documents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5221 (class 2606 OID 18298)
-- Name: chat_messages chat_messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5222 (class 2606 OID 18303)
-- Name: events events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5216 (class 2606 OID 18308)
-- Name: agreement_signed_documents fk_agreement_signed_documents_agreement; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.agreement_signed_documents
    ADD CONSTRAINT fk_agreement_signed_documents_agreement FOREIGN KEY (agreement_id) REFERENCES public.agreements(id) ON DELETE CASCADE;


--
-- TOC entry 5223 (class 2606 OID 18313)
-- Name: feasibility_attachments fk_feasibility_attachments_study_site; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.feasibility_attachments
    ADD CONSTRAINT fk_feasibility_attachments_study_site FOREIGN KEY (study_site_id) REFERENCES public.study_sites(id) ON DELETE CASCADE;


--
-- TOC entry 5224 (class 2606 OID 18318)
-- Name: feasibility_requests fk_feasibility_requests_study_site; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.feasibility_requests
    ADD CONSTRAINT fk_feasibility_requests_study_site FOREIGN KEY (study_site_id) REFERENCES public.study_sites(id) ON DELETE CASCADE;


--
-- TOC entry 5225 (class 2606 OID 18323)
-- Name: feasibility_responses fk_feasibility_responses_request; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.feasibility_responses
    ADD CONSTRAINT fk_feasibility_responses_request FOREIGN KEY (request_id) REFERENCES public.feasibility_requests(id) ON DELETE CASCADE;


--
-- TOC entry 5227 (class 2606 OID 18328)
-- Name: project_feasibility_custom_questions fk_project_feasibility_custom_questions_study; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.project_feasibility_custom_questions
    ADD CONSTRAINT fk_project_feasibility_custom_questions_study FOREIGN KEY (study_id) REFERENCES public.studies(id) ON DELETE CASCADE;


--
-- TOC entry 5230 (class 2606 OID 18333)
-- Name: site_profiles fk_site_profile_site; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_profiles
    ADD CONSTRAINT fk_site_profile_site FOREIGN KEY (site_id) REFERENCES public.sites(id) ON DELETE CASCADE;


--
-- TOC entry 5239 (class 2606 OID 18338)
-- Name: user_role_assignments fk_user_role_site; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_role_assignments
    ADD CONSTRAINT fk_user_role_site FOREIGN KEY (site_id) REFERENCES public.sites(id) ON DELETE CASCADE;


--
-- TOC entry 5240 (class 2606 OID 18343)
-- Name: user_role_assignments fk_user_role_study; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_role_assignments
    ADD CONSTRAINT fk_user_role_study FOREIGN KEY (study_id) REFERENCES public.studies(id) ON DELETE CASCADE;


--
-- TOC entry 5241 (class 2606 OID 18348)
-- Name: user_role_assignments fk_user_role_user; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_role_assignments
    ADD CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- TOC entry 5226 (class 2606 OID 18353)
-- Name: iis_studies iis_studies_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.iis_studies
    ADD CONSTRAINT iis_studies_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5228 (class 2606 OID 18358)
-- Name: rd_studies rd_studies_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.rd_studies
    ADD CONSTRAINT rd_studies_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5229 (class 2606 OID 18363)
-- Name: site_documents site_documents_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_documents
    ADD CONSTRAINT site_documents_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id) ON DELETE CASCADE;


--
-- TOC entry 5231 (class 2606 OID 18368)
-- Name: site_status_history site_status_history_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_status_history
    ADD CONSTRAINT site_status_history_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- TOC entry 5232 (class 2606 OID 18373)
-- Name: site_statuses site_statuses_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_statuses
    ADD CONSTRAINT site_statuses_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- TOC entry 5233 (class 2606 OID 18378)
-- Name: site_workflow_steps site_workflow_steps_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_workflow_steps
    ADD CONSTRAINT site_workflow_steps_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id) ON DELETE CASCADE;


--
-- TOC entry 5234 (class 2606 OID 18383)
-- Name: site_workflow_steps site_workflow_steps_study_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.site_workflow_steps
    ADD CONSTRAINT site_workflow_steps_study_site_id_fkey FOREIGN KEY (study_site_id) REFERENCES public.study_sites(id) ON DELETE CASCADE;


--
-- TOC entry 5235 (class 2606 OID 18388)
-- Name: study_sites study_sites_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.study_sites
    ADD CONSTRAINT study_sites_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id) ON DELETE CASCADE;


--
-- TOC entry 5236 (class 2606 OID 18393)
-- Name: study_sites study_sites_study_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.study_sites
    ADD CONSTRAINT study_sites_study_id_fkey FOREIGN KEY (study_id) REFERENCES public.studies(id) ON DELETE CASCADE;


--
-- TOC entry 5237 (class 2606 OID 18398)
-- Name: study_templates study_templates_study_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.study_templates
    ADD CONSTRAINT study_templates_study_id_fkey FOREIGN KEY (study_id) REFERENCES public.studies(id) ON DELETE CASCADE;


--
-- TOC entry 5238 (class 2606 OID 18403)
-- Name: user_profiles user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- TOC entry 5242 (class 2606 OID 18408)
-- Name: user_sites user_sites_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_sites
    ADD CONSTRAINT user_sites_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- TOC entry 5243 (class 2606 OID 18413)
-- Name: user_sites user_sites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.user_sites
    ADD CONSTRAINT user_sites_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


-- Completed on 2026-03-11 14:05:04

--
-- PostgreSQL database dump complete
--

\unrestrict aW6UP0n6LoSjFb7i72yUFVNfCGCeo4L64AperUPPeJOd05Gkc7xWgciLq4vKY4u

