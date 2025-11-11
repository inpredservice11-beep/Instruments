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

