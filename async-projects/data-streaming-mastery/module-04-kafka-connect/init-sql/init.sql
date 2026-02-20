-- ============================================================================
-- Module 4: Kafka Connect - MySQL Initialization Script
-- Creates sample employees and departments schema with data.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS company;
USE company;

-- ----------------------------------------------------------------------------
-- Departments table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    budget DECIMAL(12, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- Employees table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    department_id INT,
    hire_date DATE NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- ----------------------------------------------------------------------------
-- Projects table (for additional exercises)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    department_id INT,
    start_date DATE,
    end_date DATE,
    status ENUM('planning', 'active', 'completed', 'cancelled') DEFAULT 'planning',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- ----------------------------------------------------------------------------
-- Seed data: Departments
-- ----------------------------------------------------------------------------
INSERT INTO departments (name, location, budget) VALUES
    ('Engineering', 'San Francisco', 2500000.00),
    ('Marketing', 'New York', 1200000.00),
    ('Sales', 'Chicago', 1800000.00),
    ('Human Resources', 'San Francisco', 800000.00),
    ('Finance', 'New York', 950000.00),
    ('Product', 'San Francisco', 1500000.00),
    ('Customer Support', 'Austin', 600000.00),
    ('Data Science', 'San Francisco', 2000000.00);

-- ----------------------------------------------------------------------------
-- Seed data: Employees
-- ----------------------------------------------------------------------------
INSERT INTO employees (first_name, last_name, email, department_id, hire_date, salary, is_active) VALUES
    ('Alice', 'Johnson', 'alice.johnson@company.com', 1, '2020-03-15', 135000.00, 1),
    ('Bob', 'Smith', 'bob.smith@company.com', 1, '2019-07-22', 142000.00, 1),
    ('Carol', 'Williams', 'carol.williams@company.com', 2, '2021-01-10', 95000.00, 1),
    ('David', 'Brown', 'david.brown@company.com', 3, '2018-11-05', 110000.00, 1),
    ('Eve', 'Davis', 'eve.davis@company.com', 1, '2022-06-01', 125000.00, 1),
    ('Frank', 'Miller', 'frank.miller@company.com', 4, '2020-09-14', 88000.00, 1),
    ('Grace', 'Wilson', 'grace.wilson@company.com', 5, '2019-04-30', 105000.00, 1),
    ('Henry', 'Moore', 'henry.moore@company.com', 6, '2021-08-20', 130000.00, 1),
    ('Ivy', 'Taylor', 'ivy.taylor@company.com', 2, '2022-02-28', 92000.00, 1),
    ('Jack', 'Anderson', 'jack.anderson@company.com', 3, '2020-12-01', 115000.00, 1),
    ('Karen', 'Thomas', 'karen.thomas@company.com', 7, '2021-05-15', 72000.00, 1),
    ('Leo', 'Jackson', 'leo.jackson@company.com', 8, '2019-10-10', 145000.00, 1),
    ('Mia', 'White', 'mia.white@company.com', 8, '2022-04-18', 138000.00, 1),
    ('Nathan', 'Harris', 'nathan.harris@company.com', 1, '2023-01-09', 120000.00, 1),
    ('Olivia', 'Martin', 'olivia.martin@company.com', 6, '2020-07-25', 128000.00, 1),
    ('Peter', 'Garcia', 'peter.garcia@company.com', 5, '2021-11-12', 98000.00, 1),
    ('Quinn', 'Martinez', 'quinn.martinez@company.com', 3, '2022-09-05', 108000.00, 1),
    ('Rachel', 'Robinson', 'rachel.robinson@company.com', 4, '2023-03-20', 85000.00, 1),
    ('Sam', 'Clark', 'sam.clark@company.com', 7, '2020-06-18', 75000.00, 1),
    ('Tina', 'Rodriguez', 'tina.rodriguez@company.com', 2, '2021-10-30', 97000.00, 0);

-- ----------------------------------------------------------------------------
-- Seed data: Projects
-- ----------------------------------------------------------------------------
INSERT INTO projects (name, department_id, start_date, end_date, status) VALUES
    ('Platform Redesign', 1, '2024-01-15', '2024-06-30', 'active'),
    ('Q1 Marketing Campaign', 2, '2024-01-01', '2024-03-31', 'active'),
    ('Sales Dashboard', 3, '2024-02-01', '2024-04-15', 'planning'),
    ('Employee Onboarding Portal', 4, '2024-03-01', '2024-08-31', 'planning'),
    ('ML Recommendation Engine', 8, '2023-09-01', '2024-03-31', 'active'),
    ('Customer Feedback Analysis', 7, '2024-01-15', '2024-05-31', 'active'),
    ('Budget Forecasting Tool', 5, '2023-11-01', '2024-02-28', 'completed'),
    ('Mobile App v2', 6, '2024-02-15', '2024-09-30', 'planning');

-- ----------------------------------------------------------------------------
-- Create a replica target table for the JDBC sink connector
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees_replica (
    id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    department_id INT,
    hire_date DATE,
    salary DECIMAL(10, 2),
    is_active TINYINT(1),
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL
);

-- ----------------------------------------------------------------------------
-- Grant privileges to connect user
-- ----------------------------------------------------------------------------
GRANT ALL PRIVILEGES ON company.* TO 'connect_user'@'%';
FLUSH PRIVILEGES;
