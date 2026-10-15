CREATE DATABASE IF NOT EXISTS DRISTI_db;
USE DRISTI_db;

-- 1. Users & Authentication (RBAC)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('citizen', 'authority') NOT NULL DEFAULT 'citizen',
    phone_number VARCHAR(20) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Environmental & Geotechnical Telemetry
CREATE TABLE IF NOT EXISTS environmental_telemetry (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    rainfall_mm_hr FLOAT NOT NULL,
    soil_moisture_pct FLOAT NOT NULL,
    slope_angle_deg FLOAT NOT NULL,
    ground_displacement_mm FLOAT NOT NULL,
    land_cover_code INT DEFAULT 2, -- 1: Dense Forest, 2: Sparse/Barren, 3: Built-up
    river_proximity_m FLOAT DEFAULT 250.0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. AI Risk Prediction Zones
CREATE TABLE IF NOT EXISTS risk_zones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    radius_meters INT DEFAULT 650,
    risk_score FLOAT NOT NULL,
    risk_level ENUM('Low', 'Medium', 'High', 'Critical') NOT NULL,
    ml_confidence FLOAT DEFAULT 0.95,
    factor_breakdown JSON NULL,
    last_evaluated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 4. Safe Relief Shelters
CREATE TABLE IF NOT EXISTS shelters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    total_capacity INT NOT NULL,
    current_occupancy INT DEFAULT 0,
    contact_number VARCHAR(20),
    ration_kits_available INT DEFAULT 500,
    medical_kits_available INT DEFAULT 120,
    is_operational BOOLEAN DEFAULT TRUE
);

-- 5. NDRF / SDRF Rapid Deployment Units
CREATE TABLE IF NOT EXISTS response_teams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_code VARCHAR(50) NOT NULL,
    unit_name VARCHAR(100) NOT NULL,
    current_lat DECIMAL(10, 8) NOT NULL,
    current_lng DECIMAL(11, 8) NOT NULL,
    personnel_count INT NOT NULL,
    status ENUM('Stationed', 'Deployed', 'In Transit', 'Resting') DEFAULT 'Stationed',
    assigned_zone VARCHAR(100) NULL
);

-- 6. Crowdsourced Citizen Incidents
CREATE TABLE IF NOT EXISTS citizen_incidents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    incident_type ENUM('Road Blocked', 'Active Landslide', 'Ground Crack', 'Flash Flood') NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    description TEXT,
    severity ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
    status ENUM('Pending', 'Verified', 'Resolved', 'Rejected') DEFAULT 'Pending',
    photo_url LONGTEXT NULL,
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Multi-Channel Alert Logs
CREATE TABLE IF NOT EXISTS alert_broadcast_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    target_sector VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    dispatched_channels JSON NOT NULL,
    recipients_count INT DEFAULT 0,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Default Accounts (Password: admin123)
INSERT INTO users (full_name, email, hashed_password, role, phone_number)
VALUES 
('District Magistrate Officer', 'authority@dristi.gov.in', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6L656G/5aE/4B9m2', 'authority', '+91-135-2710000'),
('Aarav Sharma (Citizen)', 'citizen@gmail.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6L656G/5aE/4B9m2', 'citizen', '+91-9876543210')
ON DUPLICATE KEY UPDATE id=id;

-- Seed Shelter Base
INSERT INTO shelters (name, latitude, longitude, total_capacity, current_occupancy, contact_number, ration_kits_available, medical_kits_available)
VALUES 
('Doon Community Relief Base', 30.31500000, 78.03000000, 450, 110, '+91-135-2710001', 650, 180),
('North Ridge Cantonment Shelter', 30.33800000, 78.01800000, 600, 240, '+91-135-2710002', 800, 250),
('Lower Valley Safe Campus', 30.30100000, 78.04800000, 350, 45, '+91-135-2710003', 400, 90)
ON DUPLICATE KEY UPDATE id=id;

-- Seed Response Teams
INSERT INTO response_teams (team_code, unit_name, current_lat, current_lng, personnel_count, status, assigned_zone)
VALUES
('NDRF-BAT-01', '8th Battalion NDRF (Alpha Unit)', 30.31800000, 78.03500000, 35, 'Stationed', 'HQ Base'),
('SDRF-UK-04', 'State Disaster Response Force Quick ResQ', 30.33000000, 78.02800000, 20, 'Deployed', 'Sector-DEH-01')
ON DUPLICATE KEY UPDATE id=id;

-- Seed Telemetry
INSERT INTO environmental_telemetry (sensor_id, latitude, longitude, rainfall_mm_hr, soil_moisture_pct, slope_angle_deg, ground_displacement_mm, land_cover_code, river_proximity_m)
VALUES
('DEH-01', 30.32500000, 78.04000000, 92.5, 91.0, 41.5, 5.8, 2, 80.0),
('DEH-02', 30.33200000, 78.02500000, 68.0, 78.0, 33.0, 2.1, 2, 220.0),
('DEH-03', 30.31000000, 78.02000000, 32.0, 48.0, 21.0, 0.3, 1, 600.0),
('DEH-04', 30.30500000, 78.04500000, 14.0, 28.0, 14.0, 0.0, 1, 950.0)
ON DUPLICATE KEY UPDATE id=id;