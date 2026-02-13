/*
================================================================================
PARSONS FINANCE SIMULATION DATABASE
================================================================================
Database creation script with full referential integrity.
Designed for financial analytics: DSO, Aging, WIP, and Risk Scoring.

FIXED: Multiple cascade path issue by using NO ACTION on all FKs
================================================================================
*/

-- ============================================================================
-- DATABASE CREATION
-- ============================================================================
USE master;
GO

-- Drop database if exists (for clean recreation)
IF EXISTS (SELECT name FROM sys.databases WHERE name = N'ParsonsFinanceSim')
BEGIN
    ALTER DATABASE ParsonsFinanceSim SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE ParsonsFinanceSim;
END
GO

-- Create database
CREATE DATABASE ParsonsFinanceSim;
GO

USE ParsonsFinanceSim;
GO

-- ============================================================================
-- TABLE 1: CLIENTS (Dimension Table)
-- ============================================================================
CREATE TABLE Clients (
    ClientID INT IDENTITY(1,1) PRIMARY KEY,
    ClientName NVARCHAR(200) NOT NULL,
    Industry NVARCHAR(100) NULL,
    PaymentTerms INT NOT NULL DEFAULT 30,
    CreditLimit DECIMAL(18,2) NOT NULL DEFAULT 0,
    ContactEmail NVARCHAR(255) NULL,
    ContactPhone NVARCHAR(50) NULL,
    Address NVARCHAR(500) NULL,
    City NVARCHAR(100) NULL,
    Country NVARCHAR(100) NULL DEFAULT 'Saudi Arabia',
    CreatedDate DATETIME NOT NULL DEFAULT GETDATE(),
    IsActive BIT NOT NULL DEFAULT 1,
    
    CONSTRAINT CHK_Clients_PaymentTerms CHECK (PaymentTerms > 0 AND PaymentTerms <= 365),
    CONSTRAINT CHK_Clients_CreditLimit CHECK (CreditLimit >= 0),
    CONSTRAINT UQ_Clients_ClientName UNIQUE (ClientName)
);
GO

CREATE NONCLUSTERED INDEX IX_Clients_ClientName ON Clients(ClientName);
CREATE NONCLUSTERED INDEX IX_Clients_Industry ON Clients(Industry);
GO

-- ============================================================================
-- TABLE 2: PROJECTS (Dimension Table)
-- ============================================================================
CREATE TABLE Projects (
    ProjectID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectName NVARCHAR(300) NOT NULL,
    ClientID INT NOT NULL,
    Sector NVARCHAR(100) NOT NULL,
    Region NVARCHAR(100) NOT NULL,
    StartDate DATE NOT NULL,
    EndDate DATE NULL,
    Budget DECIMAL(18,2) NOT NULL DEFAULT 0,
    Status NVARCHAR(50) NOT NULL DEFAULT 'Active',
    Description NVARCHAR(MAX) NULL,
    ProjectManager NVARCHAR(200) NULL,
    CreatedDate DATETIME NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT FK_Projects_Clients FOREIGN KEY (ClientID) 
        REFERENCES Clients(ClientID) 
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT CHK_Projects_Budget CHECK (Budget >= 0),
    CONSTRAINT CHK_Projects_Dates CHECK (EndDate IS NULL OR EndDate >= StartDate),
    CONSTRAINT CHK_Projects_Status CHECK (Status IN ('Active', 'Completed', 'On Hold', 'Cancelled'))
);
GO

CREATE NONCLUSTERED INDEX IX_Projects_ClientID ON Projects(ClientID);
CREATE NONCLUSTERED INDEX IX_Projects_Sector ON Projects(Sector);
CREATE NONCLUSTERED INDEX IX_Projects_Region ON Projects(Region);
CREATE NONCLUSTERED INDEX IX_Projects_Status ON Projects(Status);
GO

-- ============================================================================
-- TABLE 3: INVOICES (Fact Table - Core)
-- ============================================================================
CREATE TABLE Invoices (
    InvoiceID INT IDENTITY(1,1) PRIMARY KEY,
    InvoiceNumber NVARCHAR(50) NOT NULL,
    ClientID INT NOT NULL,
    ProjectID INT NOT NULL,
    InvoiceAmount DECIMAL(18,2) NOT NULL,
    InvoiceDate DATE NOT NULL,
    DueDate DATE NOT NULL,
    PaidDate DATE NULL,
    PaidAmount DECIMAL(18,2) NULL,
    Status NVARCHAR(50) NOT NULL DEFAULT 'Pending',
    Notes NVARCHAR(MAX) NULL,
    CreatedDate DATETIME NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME NULL,
    
    CONSTRAINT FK_Invoices_Clients FOREIGN KEY (ClientID) 
        REFERENCES Clients(ClientID) 
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT FK_Invoices_Projects FOREIGN KEY (ProjectID) 
        REFERENCES Projects(ProjectID) 
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT CHK_Invoices_Amount CHECK (InvoiceAmount > 0),
    CONSTRAINT CHK_Invoices_PaidAmount CHECK (PaidAmount IS NULL OR PaidAmount >= 0),
    CONSTRAINT CHK_Invoices_Dates CHECK (DueDate >= InvoiceDate),
    CONSTRAINT CHK_Invoices_PaidDate CHECK (PaidDate IS NULL OR PaidDate >= InvoiceDate),
    CONSTRAINT CHK_Invoices_Status CHECK (Status IN ('Pending', 'Paid', 'Overdue', 'Partial', 'Cancelled')),
    CONSTRAINT UQ_Invoices_InvoiceNumber UNIQUE (InvoiceNumber)
);
GO

CREATE NONCLUSTERED INDEX IX_Invoices_ClientID ON Invoices(ClientID);
CREATE NONCLUSTERED INDEX IX_Invoices_ProjectID ON Invoices(ProjectID);
CREATE NONCLUSTERED INDEX IX_Invoices_Status ON Invoices(Status);
CREATE NONCLUSTERED INDEX IX_Invoices_InvoiceDate ON Invoices(InvoiceDate);
CREATE NONCLUSTERED INDEX IX_Invoices_DueDate ON Invoices(DueDate);
CREATE NONCLUSTERED INDEX IX_Invoices_StatusDate ON Invoices(Status, DueDate) INCLUDE (InvoiceAmount);
GO

-- ============================================================================
-- TABLE 4: UNBILLED WORK (WIP Tracking)
-- ============================================================================
CREATE TABLE UnbilledWork (
    WorkID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT NOT NULL,
    Description NVARCHAR(500) NOT NULL,
    EstimatedValue DECIMAL(18,2) NOT NULL,
    LogDate DATE NOT NULL,
    HoursWorked DECIMAL(10,2) NULL,
    HourlyRate DECIMAL(10,2) NULL,
    EmployeeID NVARCHAR(50) NULL,
    Department NVARCHAR(100) NULL,
    IsBilled BIT NOT NULL DEFAULT 0,
    BilledDate DATE NULL,
    InvoiceID INT NULL,
    CreatedDate DATETIME NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT FK_UnbilledWork_Projects FOREIGN KEY (ProjectID) 
        REFERENCES Projects(ProjectID) 
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT FK_UnbilledWork_Invoices FOREIGN KEY (InvoiceID) 
        REFERENCES Invoices(InvoiceID) 
        ON DELETE SET NULL
        ON UPDATE NO ACTION,
    CONSTRAINT CHK_UnbilledWork_Value CHECK (EstimatedValue >= 0),
    CONSTRAINT CHK_UnbilledWork_Hours CHECK (HoursWorked IS NULL OR HoursWorked >= 0),
    CONSTRAINT CHK_UnbilledWork_Rate CHECK (HourlyRate IS NULL OR HourlyRate >= 0)
);
GO

CREATE NONCLUSTERED INDEX IX_UnbilledWork_ProjectID ON UnbilledWork(ProjectID);
CREATE NONCLUSTERED INDEX IX_UnbilledWork_LogDate ON UnbilledWork(LogDate);
CREATE NONCLUSTERED INDEX IX_UnbilledWork_IsBilled ON UnbilledWork(IsBilled) WHERE IsBilled = 0;
GO

-- ============================================================================
-- TRIGGER: Auto-update Invoice Status to Overdue
-- ============================================================================
GO
CREATE TRIGGER TR_Invoices_UpdateOverdue
ON Invoices
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Invoices
    SET Status = 'Overdue',
        LastModifiedDate = GETDATE()
    WHERE InvoiceID IN (SELECT InvoiceID FROM inserted)
      AND Status = 'Pending'
      AND DueDate < CAST(GETDATE() AS DATE)
      AND PaidDate IS NULL;
END;
GO

-- ============================================================================
-- TRIGGER: Validate Project belongs to same Client as Invoice
-- ============================================================================
CREATE TRIGGER TR_Invoices_ValidateProjectClient
ON Invoices
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    IF EXISTS (
        SELECT 1 
        FROM inserted i
        JOIN Projects p ON i.ProjectID = p.ProjectID
        WHERE p.ClientID != i.ClientID
    )
    BEGIN
        RAISERROR('Invoice ClientID must match the Project ClientID', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END
END;
GO

-- ============================================================================
-- VIEW: AR Aging Report
-- ============================================================================
CREATE VIEW vw_AR_Aging AS
SELECT 
    i.InvoiceID,
    i.InvoiceNumber,
    c.ClientID,
    c.ClientName,
    c.Industry,
    c.PaymentTerms,
    c.CreditLimit,
    p.ProjectID,
    p.ProjectName,
    p.Sector,
    p.Region,
    i.InvoiceAmount,
    i.InvoiceDate,
    i.DueDate,
    i.PaidDate,
    i.Status,
    DATEDIFF(day, i.DueDate, GETDATE()) AS DaysOverdue,
    CASE 
        WHEN i.PaidDate IS NOT NULL THEN DATEDIFF(day, i.InvoiceDate, i.PaidDate)
        ELSE NULL 
    END AS DaysToCollect,
    CASE 
        WHEN DATEDIFF(day, i.DueDate, GETDATE()) <= 30 THEN 'Current (0-30)'
        WHEN DATEDIFF(day, i.DueDate, GETDATE()) <= 60 THEN '31-60 Days'
        WHEN DATEDIFF(day, i.DueDate, GETDATE()) <= 90 THEN '61-90 Days'
        ELSE '90+ Days (Toxic)'
    END AS AgingBucket
FROM Invoices i
JOIN Clients c ON i.ClientID = c.ClientID
JOIN Projects p ON i.ProjectID = p.ProjectID;
GO

-- ============================================================================
-- VIEW: WIP Summary by Project
-- ============================================================================
CREATE VIEW vw_WIP_Summary AS
SELECT 
    p.ProjectID,
    p.ProjectName,
    p.Sector,
    p.Region,
    c.ClientName,
    SUM(u.EstimatedValue) AS UnbilledValue,
    COUNT(u.WorkID) AS UnbilledItems,
    MIN(u.LogDate) AS OldestEntry,
    MAX(u.LogDate) AS NewestEntry,
    DATEDIFF(day, MIN(u.LogDate), GETDATE()) AS MaxDaysSinceLogged
FROM UnbilledWork u
JOIN Projects p ON u.ProjectID = p.ProjectID
JOIN Clients c ON p.ClientID = c.ClientID
WHERE u.IsBilled = 0
GROUP BY p.ProjectID, p.ProjectName, p.Sector, p.Region, c.ClientName;
GO

-- ============================================================================
-- STORED PROCEDURE: Update Overdue Status
-- ============================================================================
CREATE PROCEDURE sp_UpdateOverdueInvoices
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @UpdatedCount INT;
    
    UPDATE Invoices
    SET Status = 'Overdue',
        LastModifiedDate = GETDATE()
    WHERE Status = 'Pending'
      AND DueDate < CAST(GETDATE() AS DATE)
      AND PaidDate IS NULL;
    
    SET @UpdatedCount = @@ROWCOUNT;
    
    PRINT 'Updated ' + CAST(@UpdatedCount AS VARCHAR(10)) + ' invoices to Overdue status.';
END;
GO

PRINT '================================================================================';
PRINT 'ParsonsFinanceSim database created successfully!';
PRINT 'Tables: Clients, Projects, Invoices, UnbilledWork';
PRINT 'Views: vw_AR_Aging, vw_WIP_Summary';
PRINT 'Triggers: TR_Invoices_UpdateOverdue, TR_Invoices_ValidateProjectClient';
PRINT 'Stored Procedures: sp_UpdateOverdueInvoices';
PRINT '================================================================================';
GO
