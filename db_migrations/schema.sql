CREATE DATABASE IF NOT EXISTS smart_supermarket;
USE smart_supermarket;

-- Users Table (Role-based: admin, staff, customer)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'staff', 'customer') NOT NULL DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    barcode VARCHAR(50) UNIQUE,
    weight_g INT NOT NULL DEFAULT 0,  -- Weight in grams for validation
    image_url VARCHAR(255),
    category VARCHAR(50)
);

-- Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount DECIMAL(10, 2) NOT NULL,
    total_expected_weight INT NOT NULL DEFAULT 0, -- Summarized weight of cart in grams
    payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    exit_status ENUM('pending', 'verified', 'recheck', 'inspection', 'alert') DEFAULT 'pending',
    exit_code VARCHAR(10) UNIQUE,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT NOT NULL DEFAULT 1,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
