-- Таблица массовых выдач (групповой акт)
CREATE TABLE IF NOT EXISTS batch_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_return_date DATE,
    actual_return_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Выдан',
    notes TEXT,
    issued_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Таблица адресов выдачи
CREATE TABLE IF NOT EXISTS addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    full_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица инструментов
CREATE TABLE IF NOT EXISTS instruments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    inventory_number TEXT UNIQUE NOT NULL,
    serial_number TEXT,
    category TEXT,
    status VARCHAR(20) DEFAULT 'Доступен',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сотрудников
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    position TEXT,
    department TEXT,
    phone TEXT,
    email TEXT,
    status VARCHAR(20) DEFAULT 'Активен',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица индивидуальных выдач инструментов, теперь с batch_id
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER,
    instrument_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    address_id INTEGER,
    issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_return_date DATE,
    actual_return_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Выдан',
    notes TEXT,
    issued_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES batch_issues(id),
    FOREIGN KEY (instrument_id) REFERENCES instruments(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (address_id) REFERENCES addresses(id)
);

-- Таблица истории операций
CREATE TABLE IF NOT EXISTS operation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER,
    operation_type VARCHAR(20) NOT NULL,
    instrument_id INTEGER,
    employee_id INTEGER,
    operation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performed_by TEXT,
    notes TEXT,
    FOREIGN KEY (issue_id) REFERENCES issues(id),
    FOREIGN KEY (instrument_id) REFERENCES instruments(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

