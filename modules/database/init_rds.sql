-- 1. Tabla de Grupos (La unidad base de trabajo)
CREATE TABLE IF NOT EXISTS groups (
    group_id VARCHAR(50) PRIMARY KEY,
    professor_id VARCHAR(50),
    mode VARCHAR(20) CHECK (mode IN ('individual', 'colaborativo')), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Usuarios Unificada
-- Fusionamos tus dos propuestas para evitar errores de tabla duplicada
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(50) PRIMARY KEY,       -- Usamos username como ID
    password_hash TEXT NOT NULL,
    group_id VARCHAR(50) REFERENCES groups(group_id), -- Vínculo vital para el M1 y equipo
    email VARCHAR(100),
    role VARCHAR(20) NOT NULL,               -- 'student', 'professor', 'admin'
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    additional_info JSONB DEFAULT '{}'::jsonb
);

-- 3. Tabla de Sesiones
CREATE TABLE IF NOT EXISTS users_sessions (
    id UUID PRIMARY KEY,
    username VARCHAR(50) REFERENCES users(username),
    login_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(50) DEFAULT 'session'
);

-- 4. Tabla de Feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY,
    username VARCHAR(50) REFERENCES users(username),
    name VARCHAR(255),
    email VARCHAR(255),
    feedback TEXT,
    role VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabla de Solicitudes (Registro de actividad/apps)
CREATE TABLE IF NOT EXISTS application_requests (
    id UUID PRIMARY KEY,
    username VARCHAR(50) REFERENCES users(username),
    request_type VARCHAR(100),
    status VARCHAR(50),
    details JSONB,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Índices optimizados
CREATE INDEX IF NOT EXISTS idx_users_group ON users(group_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_sessions_username ON users_sessions(username);
CREATE INDEX IF NOT EXISTS idx_groups_professor ON groups(professor_id);