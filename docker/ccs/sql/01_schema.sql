/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.6.23-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: coredumps
-- ------------------------------------------------------
-- Server version	10.6.23-MariaDB-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

CREATE DATABASE IF NOT EXISTS coredumps;
USE coredumps;

--
-- Table structure for table `cla_backtrace`
--
CREATE TABLE IF NOT EXISTS `cla_backtrace` (
  `cle_id` int(11) NOT NULL AUTO_INCREMENT,
  `cle_core` int(11) DEFAULT NULL,
  `cle_line_no` int(11) DEFAULT NULL,
  `cle_line` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`cle_id`),
  KEY `cla_idx` (`cle_core`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Table structure for table `cla_core`
--

CREATE TABLE IF NOT EXISTS `cla_core` (
  `clc_id` int(11) NOT NULL AUTO_INCREMENT,
  `clc_sw_rev` int(11) DEFAULT NULL,
  `clc_device` int(11) DEFAULT NULL,
  `clc_core_name` varchar(255) DEFAULT NULL,
  `clc_core_binary` varchar(512) DEFAULT NULL,
  `clc_core_signal` int(11) DEFAULT NULL,
  `clc_core_file` varchar(512) DEFAULT NULL,
  `clc_date` datetime DEFAULT NULL,
  `clc_bt_csum` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`clc_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Table structure for table `cla_devices`
--

CREATE TABLE IF NOT EXISTS `cla_devices` (
  `cla_id` int(11) NOT NULL AUTO_INCREMENT,
  `cla_ip_addr` varchar(64) DEFAULT NULL,
  `cla_eqm_label` varchar(255) DEFAULT NULL,
  `cla_upgrade_method` int(11) DEFAULT NULL,
  `cla_eqm_type` int(11) DEFAULT NULL,
  `cla_eqm_name` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`cla_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Table structure for table `cla_journal`
--

CREATE TABLE IF NOT EXISTS `cla_journal` (
  `cld_id` int(11) NOT NULL AUTO_INCREMENT,
  `cld_core` int(11) DEFAULT NULL,
  `cld_line_no` int(11) DEFAULT NULL,
  `cld_line` varchar(512) DEFAULT NULL,
  `cld_date` datetime DEFAULT NULL,
  PRIMARY KEY (`cld_id`),
  KEY `cla_idx` (`cld_core`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Table structure for table `cla_sw_rev`
--

CREATE TABLE IF NOT EXISTS `cla_sw_rev` (
  `clb_id` int(11) NOT NULL AUTO_INCREMENT,
  `clb_rev` varchar(64) DEFAULT NULL,
  `clb_type` int(11) DEFAULT NULL,
  PRIMARY KEY (`clb_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Table structure for table `cla_ticket`
--

CREATE TABLE IF NOT EXISTS `cla_ticket` (
  `clt_id` int(11) NOT NULL AUTO_INCREMENT,
  `clt_bt_csum` varchar(64) NOT NULL,
  `clt_issue` varchar(32) NOT NULL,
  `clt_note` varchar(255) DEFAULT NULL,
  `clt_created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`clt_id`),
  UNIQUE KEY `clt_csum_unique` (`clt_bt_csum`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

