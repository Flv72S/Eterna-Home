-- Script per creare le tabelle per il sistema di ruoli
-- Eseguire questo script sul database di sviluppo/test

-- Tabella roles
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabella intermedia user_roles per relazione many-to-many
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Indici per migliorare le performance
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_assigned_by ON user_roles(assigned_by);

-- Inserimento di alcuni ruoli di base
INSERT INTO roles (name, description, is_active) VALUES
    ('admin', 'Amministratore del sistema', TRUE),
    ('user', 'Utente standard', TRUE),
    ('moderator', 'Moderatore', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Commenti per documentazione
COMMENT ON TABLE roles IS 'Tabella dei ruoli disponibili nel sistema';
COMMENT ON TABLE user_roles IS 'Tabella intermedia per relazione many-to-many tra utenti e ruoli';
COMMENT ON COLUMN user_roles.assigned_by IS 'ID dell''utente che ha assegnato il ruolo'; 