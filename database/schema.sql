-- ShipGuard Oracle schema
-- Complete development schema with safe cleanup section.
-- This script can be run repeatedly during development.

SET SERVEROUTPUT ON;

-- ============================================================
-- 0. CLEANUP
-- Drop existing objects if they exist.
-- This prevents ORA-00955 when re-running the schema.
-- ============================================================

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE risk_scores CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE shipment_history CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE shipments CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE routes CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE carriers CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE users CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

-- ============================================================
-- 1. CARRIERS
-- ============================================================

CREATE TABLE carriers (
    carrier_id        NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    carrier_name      VARCHAR2(100) NOT NULL,
    carrier_code      VARCHAR2(10) UNIQUE,
    on_time_pct_hist  NUMBER(5,2) DEFAULT 0 CHECK (on_time_pct_hist BETWEEN 0 AND 100),
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- ============================================================
-- 2. ROUTES
-- ============================================================

CREATE TABLE routes (
    route_id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    origin_port       VARCHAR2(80) NOT NULL,
    dest_port         VARCHAR2(80) NOT NULL,
    "mode"            VARCHAR2(10) CHECK ("mode" IN ('AIR','SEA','LAND')),
    avg_transit_days  NUMBER(5,1),
    CONSTRAINT uq_route UNIQUE (origin_port, dest_port, "mode")
);

-- ============================================================
-- 3. SHIPMENTS
-- ============================================================

CREATE TABLE shipments (
    shipment_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_ref      VARCHAR2(30) UNIQUE NOT NULL,
    carrier_id        NUMBER REFERENCES carriers(carrier_id),
    route_id          NUMBER REFERENCES routes(route_id),
    "mode"            VARCHAR2(10) CHECK ("mode" IN ('AIR','SEA','LAND')),
    cargo_type        VARCHAR2(50),
    etd               DATE NOT NULL,
    eta               DATE NOT NULL,
    actual_arrival    DATE,
    status            VARCHAR2(20) DEFAULT 'BOOKED'
                      CHECK (status IN ('BOOKED','IN_TRANSIT','DELIVERED','DELAYED')),
    container_no      VARCHAR2(50),
    vessel_name       VARCHAR2(100),
    disruption_event  VARCHAR2(255),
    consignee         VARCHAR2(100),
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT ck_eta_ge_etd CHECK (eta >= etd)
);
-- ============================================================
-- 4. SHIPMENT_HISTORY
-- ============================================================

CREATE TABLE shipment_history (
    history_id        NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_id       NUMBER REFERENCES shipments(shipment_id),
    event_type        VARCHAR2(30),
    event_ts          TIMESTAMP DEFAULT SYSTIMESTAMP,
    delay_days        NUMBER(5,1) DEFAULT 0
);

-- ============================================================
-- 5. RISK_SCORES
-- ============================================================

CREATE TABLE risk_scores (
    shipment_id   NUMBER REFERENCES shipments(shipment_id) PRIMARY KEY,
    risk_score    NUMBER(7,4) NOT NULL CHECK (risk_score BETWEEN 0 AND 1),
    risk_tier     VARCHAR2(10)
                  CHECK (risk_tier IN ('LOW','MEDIUM','HIGH')),
    top_factors   CLOB CHECK (top_factors IS JSON),
    recommendation VARCHAR2(300),
    scored_at     TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- ============================================================
-- 6. USERS
-- ============================================================

CREATE TABLE users (
    user_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name          VARCHAR2(100) NOT NULL,
    email         VARCHAR2(150) UNIQUE NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    role          VARCHAR2(20) DEFAULT 'OPS_USER'
);

-- ============================================================
-- 7. EXTERNAL TELEMETRY & INTELLIGENCE TABLES
-- ============================================================

CREATE TABLE external_weather (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    port_name VARCHAR2(100) NOT NULL,
    country_code VARCHAR2(10) NOT NULL,
    lat NUMBER,
    lon NUMBER,
    temperature_c NUMBER,
    wind_speed_kmh NUMBER,
    precipitation_mm NUMBER,
    weather_condition VARCHAR2(100),
    is_severe NUMBER(1) DEFAULT 0,
    data_source VARCHAR2(100) DEFAULT 'Open-Meteo API',
    updated_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE external_currencies (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    base_currency VARCHAR2(10) NOT NULL,
    target_currency VARCHAR2(10) NOT NULL,
    rate NUMBER NOT NULL,
    volatility_pct NUMBER DEFAULT 0.0,
    data_source VARCHAR2(100) DEFAULT 'Frankfurter FX API',
    updated_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE external_holidays (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_code VARCHAR2(10) NOT NULL,
    holiday_date DATE NOT NULL,
    holiday_name VARCHAR2(150) NOT NULL,
    is_port_closure NUMBER(1) DEFAULT 0,
    data_source VARCHAR2(100) DEFAULT 'Nager.Date API',
    updated_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE external_port_status (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    port_code VARCHAR2(30) NOT NULL,
    port_name VARCHAR2(100) NOT NULL,
    country_code VARCHAR2(10) NOT NULL,
    congestion_level VARCHAR2(20) DEFAULT 'LOW',
    avg_vessel_wait_hours NUMBER DEFAULT 4.0,
    data_source VARCHAR2(100) DEFAULT 'Global Port Intelligence',
    updated_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- ============================================================
-- 7. Helpful query for route average delay
-- ============================================================

-- Use this query from your application with :as_of_ts bound:
--
-- SELECT r.route_id,
--        AVG(sh.delay_days) AS route_avg_delay_days
-- FROM shipment_history sh
-- JOIN shipments s ON sh.shipment_id = s.shipment_id
-- JOIN routes r ON s.route_id = r.route_id
-- WHERE sh.event_ts < :as_of_ts
-- GROUP BY r.route_id;

-- ============================================================
-- 8. INDEXES
-- ============================================================

CREATE INDEX idx_shipments_eta
    ON shipments(eta);

CREATE INDEX idx_shipments_status
    ON shipments(status);

CREATE INDEX idx_shipments_mode
    ON shipments("mode");

CREATE INDEX idx_shipments_created_at
    ON shipments(created_at);

CREATE INDEX idx_shipments_carrier
    ON shipments(carrier_id);

CREATE INDEX idx_shipments_route
    ON shipments(route_id);

CREATE INDEX idx_shipments_carrier_actual
    ON shipments(carrier_id, actual_arrival);

CREATE INDEX idx_shipments_route_actual
    ON shipments(route_id, actual_arrival);

CREATE INDEX idx_shipment_history_shipment
    ON shipment_history(shipment_id);

CREATE INDEX idx_history_shipment_event
    ON shipment_history(shipment_id, event_ts);

CREATE INDEX idx_risk_scores_scored_at
    ON risk_scores(scored_at);

CREATE INDEX idx_risk_scores_tier
    ON risk_scores(risk_tier);

CREATE INDEX idx_holidays_date
    ON external_holidays(holiday_date);

CREATE INDEX idx_weather_severe_port
    ON external_weather(is_severe, port_name);
    
    

-- ============================================================
-- DONE
-- ============================================================

BEGIN
    DBMS_OUTPUT.PUT_LINE('ShipGuard schema created successfully.');
END;
/