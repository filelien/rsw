-- RAXUS Database Schema
-- Version 1.0.0

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- ─── USERS & AUTH ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email       VARCHAR(255) NOT NULL UNIQUE,
    username    VARCHAR(100) NOT NULL UNIQUE,
    full_name   VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role        ENUM('admin','operator','viewer','api') NOT NULL DEFAULT 'viewer',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    last_login  DATETIME,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS api_keys (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id     VARCHAR(36) NOT NULL,
    name        VARCHAR(100) NOT NULL,
    key_hash    VARCHAR(255) NOT NULL UNIQUE,
    key_prefix  VARCHAR(10) NOT NULL,
    permissions JSON,
    last_used   DATETIME,
    expires_at  DATETIME,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_key_hash (key_hash),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── INVENTORY ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS datacenters (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name        VARCHAR(100) NOT NULL UNIQUE,
    location    VARCHAR(255),
    description TEXT,
    tags        JSON,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS environments (
    id            VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    datacenter_id VARCHAR(36) NOT NULL,
    name          VARCHAR(100) NOT NULL,
    type          ENUM('production','staging','development','testing') NOT NULL DEFAULT 'development',
    description   TEXT,
    tags          JSON,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (datacenter_id) REFERENCES datacenters(id) ON DELETE CASCADE,
    UNIQUE KEY uq_env_name (datacenter_id, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS servers (
    id             VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    environment_id VARCHAR(36) NOT NULL,
    hostname       VARCHAR(255) NOT NULL,
    ip_address     VARCHAR(45),
    os_type        VARCHAR(100),
    os_version     VARCHAR(100),
    cpu_cores      INT,
    ram_gb         DECIMAL(10,2),
    disk_gb        DECIMAL(10,2),
    status         ENUM('active','inactive','maintenance','decommissioned') NOT NULL DEFAULT 'active',
    maintenance_mode BOOLEAN NOT NULL DEFAULT FALSE,
    tags           JSON,
    metadata       JSON,
    last_seen      DATETIME,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (environment_id) REFERENCES environments(id) ON DELETE CASCADE,
    INDEX idx_hostname (hostname),
    INDEX idx_status (status),
    INDEX idx_env (environment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS components (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    server_id   VARCHAR(36) NOT NULL,
    name        VARCHAR(255) NOT NULL,
    type        VARCHAR(100),
    version     VARCHAR(100),
    port        INT,
    status      ENUM('running','stopped','degraded','unknown') DEFAULT 'unknown',
    metadata    JSON,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    INDEX idx_server (server_id),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── ALERTS ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id           VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    fingerprint  VARCHAR(255) NOT NULL,
    name         VARCHAR(255) NOT NULL,
    severity     ENUM('critical','major','minor','warning','info') NOT NULL DEFAULT 'info',
    status       ENUM('active','pending','resolved','suppressed','acknowledged') NOT NULL DEFAULT 'pending',
    source       VARCHAR(100) NOT NULL DEFAULT 'webhook',
    instance     VARCHAR(255),
    server_id    VARCHAR(36),
    summary      TEXT,
    description  TEXT,
    labels       JSON,
    annotations  JSON,
    value        DECIMAL(20,6),
    threshold    DECIMAL(20,6),
    acknowledged_by VARCHAR(36),
    acknowledged_at DATETIME,
    resolved_at  DATETIME,
    started_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE SET NULL,
    INDEX idx_fingerprint (fingerprint),
    INDEX idx_status (status),
    INDEX idx_severity (severity),
    INDEX idx_started (started_at),
    INDEX idx_instance (instance)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS alert_history (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    alert_id    VARCHAR(36) NOT NULL,
    status      VARCHAR(50) NOT NULL,
    changed_by  VARCHAR(36),
    note        TEXT,
    metadata    JSON,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE,
    INDEX idx_alert (alert_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS suppression_windows (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name        VARCHAR(255) NOT NULL,
    reason      TEXT,
    matchers    JSON NOT NULL,
    starts_at   DATETIME NOT NULL,
    ends_at     DATETIME NOT NULL,
    created_by  VARCHAR(36),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_active (is_active),
    INDEX idx_dates (starts_at, ends_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── RULES ENGINE ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alert_rules (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    conditions  JSON NOT NULL,
    actions     JSON NOT NULL,
    priority    INT NOT NULL DEFAULT 100,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    last_triggered DATETIME,
    trigger_count INT NOT NULL DEFAULT 0,
    created_by  VARCHAR(36),
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── NOTIFICATIONS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifiers (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name        VARCHAR(255) NOT NULL UNIQUE,
    type        ENUM('email','webhook','slack','teams','pagerduty','sms') NOT NULL,
    config      JSON NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notification_templates (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name        VARCHAR(255) NOT NULL UNIQUE,
    type        VARCHAR(50) NOT NULL,
    subject     VARCHAR(500),
    body        TEXT NOT NULL,
    variables   JSON,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notifications (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    alert_id    VARCHAR(36),
    notifier_id VARCHAR(36) NOT NULL,
    status      ENUM('pending','sent','failed','retrying') NOT NULL DEFAULT 'pending',
    attempts    INT NOT NULL DEFAULT 0,
    error_msg   TEXT,
    sent_at     DATETIME,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE SET NULL,
    FOREIGN KEY (notifier_id) REFERENCES notifiers(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_alert (alert_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── TASKS & AUTOMATION ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tasks (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    script      TEXT NOT NULL,
    script_type ENUM('bash','python','ansible') NOT NULL DEFAULT 'bash',
    parameters  JSON,
    timeout_sec INT NOT NULL DEFAULT 300,
    tags        JSON,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_by  VARCHAR(36),
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS task_executions (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    task_id     VARCHAR(36) NOT NULL,
    server_id   VARCHAR(36),
    triggered_by VARCHAR(36),
    trigger_type ENUM('manual','schedule','alert','api') NOT NULL DEFAULT 'manual',
    status      ENUM('pending','running','success','failed','cancelled','timeout') NOT NULL DEFAULT 'pending',
    parameters  JSON,
    output      LONGTEXT,
    error_output TEXT,
    exit_code   INT,
    started_at  DATETIME,
    finished_at DATETIME,
    duration_ms INT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE SET NULL,
    INDEX idx_task (task_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS schedules (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    task_id     VARCHAR(36) NOT NULL,
    name        VARCHAR(255) NOT NULL,
    cron_expr   VARCHAR(100) NOT NULL,
    target_type ENUM('server','environment','datacenter','component') NOT NULL,
    target_id   VARCHAR(36),
    parameters  JSON,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    last_run    DATETIME,
    next_run    DATETIME,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    INDEX idx_task (task_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── SLO ENGINE ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS slo_targets (
    id             VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name           VARCHAR(255) NOT NULL,
    description    TEXT,
    service_name   VARCHAR(255) NOT NULL,
    sli_type       ENUM('availability','latency','error_rate','throughput') NOT NULL,
    target_percent DECIMAL(8,4) NOT NULL,
    window_days    INT NOT NULL DEFAULT 30,
    metric_query   TEXT,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_service (service_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS slo_measurements (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    slo_id      VARCHAR(36) NOT NULL,
    good_events BIGINT NOT NULL DEFAULT 0,
    total_events BIGINT NOT NULL DEFAULT 0,
    compliance  DECIMAL(8,4),
    error_budget_remaining DECIMAL(8,4),
    period_start DATETIME NOT NULL,
    period_end   DATETIME NOT NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slo_id) REFERENCES slo_targets(id) ON DELETE CASCADE,
    INDEX idx_slo (slo_id),
    INDEX idx_period (period_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS probes (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name        VARCHAR(255) NOT NULL,
    type        ENUM('http','tcp','icmp','dns') NOT NULL DEFAULT 'http',
    target      VARCHAR(500) NOT NULL,
    interval_sec INT NOT NULL DEFAULT 60,
    timeout_sec  INT NOT NULL DEFAULT 10,
    expected_status INT,
    headers     JSON,
    slo_id      VARCHAR(36),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    last_check  DATETIME,
    last_status ENUM('up','down','degraded','unknown') DEFAULT 'unknown',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slo_id) REFERENCES slo_targets(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS probe_results (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    probe_id    VARCHAR(36) NOT NULL,
    status      ENUM('up','down','degraded') NOT NULL,
    response_ms INT,
    status_code INT,
    error_msg   TEXT,
    checked_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (probe_id) REFERENCES probes(id) ON DELETE CASCADE,
    INDEX idx_probe (probe_id),
    INDEX idx_checked (checked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── MAINTENANCE WINDOWS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS maintenance_windows (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    target_type ENUM('server','environment','datacenter','component') NOT NULL,
    target_id   VARCHAR(36) NOT NULL,
    starts_at   DATETIME NOT NULL,
    ends_at     DATETIME NOT NULL,
    created_by  VARCHAR(36),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dates (starts_at, ends_at),
    INDEX idx_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── AUDIT LOG ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id     VARCHAR(36),
    action      VARCHAR(100) NOT NULL,
    resource    VARCHAR(100) NOT NULL,
    resource_id VARCHAR(36),
    details     JSON,
    ip_address  VARCHAR(45),
    user_agent  TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_resource (resource, resource_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── TICKETS ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tickets (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    title       VARCHAR(500) NOT NULL,
    description TEXT,
    priority    ENUM('critical','high','medium','low') NOT NULL DEFAULT 'medium',
    status      ENUM('open','in_progress','resolved','closed','cancelled') NOT NULL DEFAULT 'open',
    alert_id    VARCHAR(36),
    assigned_to VARCHAR(36),
    created_by  VARCHAR(36),
    tags        JSON,
    resolved_at DATETIME,
    closed_at   DATETIME,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_assigned (assigned_to)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ticket_comments (
    id          VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    ticket_id   VARCHAR(36) NOT NULL,
    user_id     VARCHAR(36),
    content     TEXT NOT NULL,
    is_internal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── DEFAULT DATA ─────────────────────────────────────────────────
INSERT INTO users (id, email, username, full_name, password_hash, role)
VALUES (
    UUID(),
    'admin@raxus.io',
    'admin',
    'RAXUS Administrator',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'admin'
) ON DUPLICATE KEY UPDATE email=email;

INSERT INTO notifiers (name, type, config) VALUES
('Default Email', 'email', '{"smtp_host": "smtp.gmail.com", "smtp_port": 587}'),
('Default Webhook', 'webhook', '{"url": "https://example.com/webhook", "method": "POST"}')
ON DUPLICATE KEY UPDATE name=name;
