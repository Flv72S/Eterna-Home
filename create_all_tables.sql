-- Script completo per creare tutte le tabelle necessarie per Eterna Home
-- Eseguire questo script sul database di sviluppo/test

-- ============================================================================
-- TABELLA USERS (utenti)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone_number VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Indici per users
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);

-- ============================================================================
-- TABELLA ROLES (ruoli)
-- ============================================================================
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABELLA USER_ROLES (relazione many-to-many utenti-ruoli)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Indici per user_roles
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_assigned_by ON user_roles(assigned_by);

-- ============================================================================
-- TABELLA HOUSES (case)
-- ============================================================================
CREATE TABLE IF NOT EXISTS houses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indici per houses
CREATE INDEX IF NOT EXISTS ix_houses_owner_id ON houses(owner_id);
CREATE INDEX IF NOT EXISTS ix_houses_name ON houses(name);

-- ============================================================================
-- TABELLA NODES (nodi domotici)
-- ============================================================================
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    house_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (house_id) REFERENCES houses(id) ON DELETE CASCADE
);

-- Indici per nodes
CREATE INDEX IF NOT EXISTS ix_nodes_house_id ON nodes(house_id);
CREATE INDEX IF NOT EXISTS ix_nodes_type ON nodes(type);

-- ============================================================================
-- TABELLA ROOMS (stanze)
-- ============================================================================
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    house_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (house_id) REFERENCES houses(id) ON DELETE CASCADE
);

-- Indici per rooms
CREATE INDEX IF NOT EXISTS ix_rooms_house_id ON rooms(house_id);

-- ============================================================================
-- TABELLA DOCUMENTS (documenti)
-- ============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    owner_id INTEGER NOT NULL,
    house_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (house_id) REFERENCES houses(id) ON DELETE SET NULL
);

-- Indici per documents
CREATE INDEX IF NOT EXISTS ix_documents_owner_id ON documents(owner_id);
CREATE INDEX IF NOT EXISTS ix_documents_house_id ON documents(house_id);

-- ============================================================================
-- TABELLA DOCUMENT_VERSIONS (versioni dei documenti)
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    created_by_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(document_id, version_number)
);

-- Indici per document_versions
CREATE INDEX IF NOT EXISTS ix_document_versions_document_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS ix_document_versions_created_by_id ON document_versions(created_by_id);

-- ============================================================================
-- TABELLA BOOKINGS (prenotazioni)
-- ============================================================================
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indici per bookings
CREATE INDEX IF NOT EXISTS ix_bookings_room_id ON bookings(room_id);
CREATE INDEX IF NOT EXISTS ix_bookings_user_id ON bookings(user_id);
CREATE INDEX IF NOT EXISTS ix_bookings_start_time ON bookings(start_time);
CREATE INDEX IF NOT EXISTS ix_bookings_end_time ON bookings(end_time);

-- ============================================================================
-- TABELLA MAINTENANCE_RECORDS (record di manutenzione)
-- ============================================================================
CREATE TABLE IF NOT EXISTS maintenance_records (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    house_id INTEGER NOT NULL,
    node_id INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    scheduled_date TIMESTAMP WITH TIME ZONE,
    completed_date TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER NOT NULL,
    assigned_to_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (house_id) REFERENCES houses(id) ON DELETE CASCADE,
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indici per maintenance_records
CREATE INDEX IF NOT EXISTS ix_maintenance_records_house_id ON maintenance_records(house_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_records_node_id ON maintenance_records(node_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_records_created_by_id ON maintenance_records(created_by_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_records_assigned_to_id ON maintenance_records(assigned_to_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_records_status ON maintenance_records(status);
CREATE INDEX IF NOT EXISTS ix_maintenance_records_scheduled_date ON maintenance_records(scheduled_date);

-- ============================================================================
-- INSERIMENTO DATI INIZIALI
-- ============================================================================

-- Inserimento ruoli di base
INSERT INTO roles (name, description, is_active) VALUES
    ('admin', 'Amministratore del sistema', TRUE),
    ('user', 'Utente standard', TRUE),
    ('moderator', 'Moderatore', TRUE),
    ('maintenance', 'Tecnico di manutenzione', TRUE)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- COMMENTI PER DOCUMENTAZIONE
-- ============================================================================
COMMENT ON TABLE users IS 'Tabella degli utenti del sistema';
COMMENT ON TABLE roles IS 'Tabella dei ruoli disponibili nel sistema';
COMMENT ON TABLE user_roles IS 'Tabella intermedia per relazione many-to-many tra utenti e ruoli';
COMMENT ON TABLE houses IS 'Tabella delle case gestite dal sistema';
COMMENT ON TABLE nodes IS 'Tabella dei nodi domotici nelle case';
COMMENT ON TABLE rooms IS 'Tabella delle stanze nelle case';
COMMENT ON TABLE documents IS 'Tabella dei documenti caricati dagli utenti';
COMMENT ON TABLE document_versions IS 'Tabella delle versioni dei documenti';
COMMENT ON TABLE bookings IS 'Tabella delle prenotazioni delle stanze';
COMMENT ON TABLE maintenance_records IS 'Tabella dei record di manutenzione';

COMMENT ON COLUMN user_roles.assigned_by IS 'ID dell''utente che ha assegnato il ruolo';
COMMENT ON COLUMN maintenance_records.priority IS 'Priorità: low, medium, high, critical';
COMMENT ON COLUMN maintenance_records.status IS 'Stato: pending, in_progress, completed, cancelled';
COMMENT ON COLUMN bookings.status IS 'Stato: pending, confirmed, cancelled, completed'; 