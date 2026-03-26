-- 1. Tabla de Usuarios (Sustituye al contenedor 'users')
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY, -- El username
    password TEXT NOT NULL,
    role VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    additional_info JSONB DEFAULT '{}'::jsonb
);

-- 2. Tabla de Sesiones (Sustituye al contenedor 'user_sessions')
CREATE TABLE IF NOT EXISTS users_sessions (
    id UUID PRIMARY KEY,
    username VARCHAR(255) REFERENCES users(id),
    login_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(50) DEFAULT 'session'
);

-- 3. Tabla de Feedback (Sustituye al contenedor 'user_feedback')
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY,
    username VARCHAR(255) REFERENCES users(id),
    name VARCHAR(255),
    email VARCHAR(255),
    feedback TEXT,
    role VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabla de Solicitudes (Sustituye al contenedor 'application_requests')
CREATE TABLE IF NOT EXISTS application_requests (
    id UUID PRIMARY KEY,
    username VARCHAR(255) REFERENCES users(id),
    request_type VARCHAR(100),
    status VARCHAR(50),
    details JSONB,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimizar las búsquedas de los 7 alumnos
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_sessions_username ON users_sessions(username);
