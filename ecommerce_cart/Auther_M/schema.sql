-- Auther_M2 Database Schema (MySQL)

CREATE DATABASE IF NOT EXISTS abt_dev;
USE abt_dev;

CREATE TABLE IF NOT EXISTS users (
  id CHAR(36) NOT NULL,
  full_name VARCHAR(255) NULL,
  email VARCHAR(255) NOT NULL,
  mobile VARCHAR(20) NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','user','vendor') NOT NULL DEFAULT 'user',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  is_verified TINYINT(1) NOT NULL DEFAULT 0,
  otp_code VARCHAR(10) NULL,
  otp_expires_at DATETIME NULL,
  otp_verified_at DATETIME NULL,
  reset_token VARCHAR(500) NULL,
  reset_token_expires DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  KEY ix_users_email (email),
  KEY ix_users_mobile (mobile)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
