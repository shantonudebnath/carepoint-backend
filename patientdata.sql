-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Dec 09, 2025 at 09:36 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `patientdata`
--

-- --------------------------------------------------------

--
-- Table structure for table `single_patient_15_tests`
--

CREATE TABLE `single_patient_15_tests` (
  `Patient_Name` varchar(16) DEFAULT NULL,
  `Patient_Age_Years` varchar(17) DEFAULT NULL,
  `Patient_Gender` varchar(14) DEFAULT NULL,
  `Hospital` varchar(13) DEFAULT NULL,
  `Lab` varchar(11) DEFAULT NULL,
  `Department` varchar(25) DEFAULT NULL,
  `Report_Title` varchar(33) DEFAULT NULL,
  `Sample_Type` varchar(11) DEFAULT NULL,
  `Sample_Date` varchar(16) DEFAULT NULL,
  `Report_Date` varchar(16) DEFAULT NULL,
  `Patient_ID` varchar(10) DEFAULT NULL,
  `Test_Name` varchar(20) DEFAULT NULL,
  `Result` varchar(6) DEFAULT NULL,
  `Unit` varchar(8) DEFAULT NULL,
  `Reference_Range` varchar(68) DEFAULT NULL,
  `Method` varchar(22) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `single_patient_15_tests`
--

INSERT INTO `single_patient_15_tests` (`Patient_Name`, `Patient_Age_Years`, `Patient_Gender`, `Hospital`, `Lab`, `Department`, `Report_Title`, `Sample_Type`, `Sample_Date`, `Report_Date`, `Patient_ID`, `Test_Name`, `Result`, `Unit`, `Reference_Range`, `Method`) VALUES
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'Hemoglobin', '14.1', 'g/dL', '13.0-17.0', 'Automated'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'WBC Count', '7.2', '×10^3/uL', '4.0-10.0', 'Automated'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'Platelet Count', '270', '×10^3/uL', '150-400', 'Automated'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'ALT (SGPT)', '42', 'U/L', '0-40', 'IFCC'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'AST (SGOT)', '37', 'U/L', '0-40', 'IFCC'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'Alkaline Phosphatase', '95', 'U/L', '44-147', 'Enzymatic'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'Total Bilirubin', '0.9', 'mg/dL', '0.1-1.2', 'Photometric'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'Creatinine', '1.2', 'mg/dL', '0.7-1.3', 'Enzymatic'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'Urea', '38', 'mg/dL', '15-40', 'Enzymatic'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'Fasting Glucose', '112', 'mg/dL', '70-100', 'Hexokinase'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'Total Cholesterol', '205', 'mg/dL', 'Desirable: <200; Borderline: 200-239; High: >=240', 'CHOD-PAP'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'HDL Cholesterol', '44', 'mg/dL', 'Low: <40; Desirable: >=40', 'Direct enzymatic'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'LDL Cholesterol', '132', 'mg/dL', 'Optimal: <100; Near/Above optimal: 100-129; Borderline high: 130-159', 'Friedewald formula'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'Triglycerides', '176', 'mg/dL', 'Normal: <150; Borderline high: 150-199; High: 200-499', 'Enzymatic colorimetric'),
('SHANTONU DEBNATH', '25', 'M', 'Demo Hospital', 'Central Lab', 'Biochemistry & Hematology', 'Complete Health Checkup (Fasting)', 'Blood', '20-01-2025 08:15', '20-01-2025 11:20', 'PID1001', 'TSH', '3.2', 'uIU/mL', '0.4-4.0', 'CMIA');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
