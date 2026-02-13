/*
================================================================================
PARSONS FINANCE SIMULATION - SAMPLE DATA GENERATION
================================================================================
Generates realistic financial data for testing the analytics suite.
- 300 Clients
- 1,000 Projects
- 15,000 Invoices
- ~5,000 Unbilled Work entries

Run AFTER 01_create_schema.sql
================================================================================
*/

USE ParsonsFinanceSim;
GO

SET NOCOUNT ON;

PRINT 'Starting data generation...';
PRINT '================================================================================';

-- ============================================================================
-- STEP 1: Generate 300 Clients
-- ============================================================================
PRINT 'Generating Clients (300 records)...';

DECLARE @Industries TABLE (ID INT, Name NVARCHAR(100));
INSERT INTO @Industries VALUES 
    (1, 'Oil & Gas'), (2, 'Infrastructure'), (3, 'Transport'), 
    (4, 'Technology'), (5, 'Healthcare'), (6, 'Real Estate'),
    (7, 'Energy'), (8, 'Manufacturing'), (9, 'Telecommunications'), (10, 'Government'),
    (11, 'Defense'), (12, 'Aviation'), (13, 'Utilities'), (14, 'Mining'), (15, 'Logistics');

DECLARE @ClientNames TABLE (ID INT, BaseName NVARCHAR(100));
INSERT INTO @ClientNames VALUES
    (1, 'Saudi Aramco'), (2, 'SABIC'), (3, 'STC'), (4, 'NEOM Company'),
    (5, 'Red Sea Global'), (6, 'Qiddiya'), (7, 'ACWA Power'), (8, 'Maaden'),
    (9, 'Almarai'), (10, 'Mobily'), (11, 'Zain KSA'), (12, 'Riyad Bank'),
    (13, 'Al Rajhi Bank'), (14, 'Saudi Electricity'), (15, 'SAPTCO'),
    (16, 'Riyadh Metro'), (17, 'Haramain Railway'), (18, 'King Salman Energy Park'),
    (19, 'Royal Commission'), (20, 'Diriyah Gate'), (21, 'ROSHN Group'),
    (22, 'SNB Bank'), (23, 'Alinma Bank'), (24, 'Saudi Airlines'),
    (25, 'Tasnee'), (26, 'Yanbu Petrochemical'), (27, 'SAFCO'),
    (28, 'Saudi Cement'), (29, 'Zamil Industrial'), (30, 'Al Jazeera Bank');

DECLARE @i INT = 1;
WHILE @i <= 300
BEGIN
    DECLARE @BaseName NVARCHAR(100);
    DECLARE @Industry NVARCHAR(100);
    
    SELECT @BaseName = BaseName FROM @ClientNames WHERE ID = ((@i - 1) % 30) + 1;
    SELECT @Industry = Name FROM @Industries WHERE ID = ((@i - 1) % 15) + 1;
    
    INSERT INTO Clients (ClientName, Industry, PaymentTerms, CreditLimit, ContactEmail, City, Country)
    VALUES (
        @BaseName + ' - Division ' + CAST(CEILING(@i / 30.0) AS VARCHAR(2)),
        @Industry,
        CASE 
            WHEN @i % 5 = 0 THEN 60
            WHEN @i % 3 = 0 THEN 45
            ELSE 30
        END,
        CAST((500000 + (@i * 50000) + (RAND(CHECKSUM(NEWID())) * 3000000)) AS DECIMAL(18,2)),
        'finance@' + LOWER(REPLACE(@BaseName, ' ', '')) + CAST(@i AS VARCHAR(3)) + '.sa',
        CASE (@i % 6)
            WHEN 0 THEN 'Riyadh'
            WHEN 1 THEN 'Jeddah'
            WHEN 2 THEN 'Dammam'
            WHEN 3 THEN 'NEOM'
            WHEN 4 THEN 'Mecca'
            ELSE 'Madinah'
        END,
        'Saudi Arabia'
    );
    SET @i = @i + 1;
END;

PRINT '   > 300 Clients created';

-- ============================================================================
-- STEP 2: Generate 1000 Projects
-- ============================================================================
PRINT 'Generating Projects (1000 records)...';

DECLARE @Sectors TABLE (ID INT, Name NVARCHAR(100));
INSERT INTO @Sectors VALUES 
    (1, 'Transport'), (2, 'Energy'), (3, 'Infrastructure'), 
    (4, 'Technology'), (5, 'Healthcare'), (6, 'Real Estate'),
    (7, 'Water'), (8, 'Telecom'), (9, 'Aviation'), (10, 'Defense');

DECLARE @Regions TABLE (ID INT, Name NVARCHAR(100));
INSERT INTO @Regions VALUES 
    (1, 'RIYADH'), (2, 'NEOM'), (3, 'JEDDAH'), 
    (4, 'DAMMAM'), (5, 'MECCA'), (6, 'MADINAH'),
    (7, 'ABHA'), (8, 'TABUK'), (9, 'JUBAIL'), (10, 'YANBU');

DECLARE @ProjectPrefixes TABLE (ID INT, Prefix NVARCHAR(100));
INSERT INTO @ProjectPrefixes VALUES
    (1, 'Highway Expansion'), (2, 'Metro Line'), (3, 'Power Plant'),
    (4, 'Smart City'), (5, 'Hospital Complex'), (6, 'Airport Terminal'),
    (7, 'Industrial Zone'), (8, 'Railway Extension'), (9, 'Data Center'),
    (10, 'Water Treatment'), (11, 'Solar Farm'), (12, 'Logistics Hub'),
    (13, 'Port Upgrade'), (14, 'Telecom Network'), (15, 'Defense Base'),
    (16, 'Residential Complex'), (17, 'Commercial Tower'), (18, 'University Campus'),
    (19, 'Sports Arena'), (20, 'Entertainment District');

DECLARE @ClientID INT;
DECLARE @ProjectCount INT;
DECLARE @p INT;
DECLARE @TotalProjectsCreated INT = 0;

DECLARE client_cursor CURSOR FOR SELECT ClientID FROM Clients;
OPEN client_cursor;
FETCH NEXT FROM client_cursor INTO @ClientID;

WHILE @@FETCH_STATUS = 0 AND @TotalProjectsCreated < 1000
BEGIN
    -- Each client gets 2-5 projects to reach ~1000 total
    SET @ProjectCount = 2 + ABS(CHECKSUM(NEWID()) % 4);
    SET @p = 1;
    
    WHILE @p <= @ProjectCount AND @TotalProjectsCreated < 1000
    BEGIN
        DECLARE @Prefix NVARCHAR(100);
        DECLARE @Sector NVARCHAR(100);
        DECLARE @Region NVARCHAR(100);
        
        SELECT @Prefix = Prefix FROM @ProjectPrefixes WHERE ID = (ABS(CHECKSUM(NEWID())) % 20) + 1;
        SELECT @Sector = Name FROM @Sectors WHERE ID = (ABS(CHECKSUM(NEWID())) % 10) + 1;
        SELECT @Region = Name FROM @Regions WHERE ID = (ABS(CHECKSUM(NEWID())) % 10) + 1;
        
        DECLARE @StartDate DATE = DATEADD(day, -(ABS(CHECKSUM(NEWID())) % 1095 + 180), GETDATE());
        DECLARE @EndDate DATE = CASE 
            WHEN ABS(CHECKSUM(NEWID())) % 3 = 0 THEN NULL
            ELSE DATEADD(day, ABS(CHECKSUM(NEWID())) % 730 + 180, @StartDate)
        END;
        
        INSERT INTO Projects (ProjectName, ClientID, Sector, Region, StartDate, EndDate, Budget, Status, ProjectManager)
        VALUES (
            @Prefix + ' - Phase ' + CAST(@p AS VARCHAR(2)) + '-' + CAST(@ClientID AS VARCHAR(3)),
            @ClientID,
            @Sector,
            @Region,
            @StartDate,
            @EndDate,
            CAST((1000000 + (ABS(CHECKSUM(NEWID())) % 19000000)) AS DECIMAL(18,2)),
            CASE 
                WHEN @EndDate IS NOT NULL AND @EndDate < GETDATE() THEN 'Completed'
                WHEN ABS(CHECKSUM(NEWID())) % 10 = 0 THEN 'On Hold'
                ELSE 'Active'
            END,
            'PM-' + RIGHT('000' + CAST(@ClientID AS VARCHAR(3)), 3)
        );
        SET @p = @p + 1;
        SET @TotalProjectsCreated = @TotalProjectsCreated + 1;
    END;
    
    FETCH NEXT FROM client_cursor INTO @ClientID;
END;

CLOSE client_cursor;
DEALLOCATE client_cursor;

DECLARE @TotalProjects INT;
SELECT @TotalProjects = COUNT(*) FROM Projects;
PRINT '   > ' + CAST(@TotalProjects AS VARCHAR(10)) + ' Projects created';

-- ============================================================================
-- STEP 3: Generate 15,000 Invoices
-- ============================================================================
PRINT 'Generating Invoices (15,000 records)...';

DECLARE @InvoiceCount INT = 0;
DECLARE @TargetInvoices INT = 15000;
DECLARE @ProjectID INT;
DECLARE @PaymentTerms INT;
DECLARE @InvoiceNum INT = 1;

WHILE @InvoiceCount < @TargetInvoices
BEGIN
    SELECT TOP 1 
        @ProjectID = p.ProjectID,
        @ClientID = p.ClientID,
        @PaymentTerms = c.PaymentTerms
    FROM Projects p
    JOIN Clients c ON p.ClientID = c.ClientID
    ORDER BY NEWID();
    
    DECLARE @InvoiceDate DATE = DATEADD(day, -(ABS(CHECKSUM(NEWID())) % 1095), GETDATE());
    DECLARE @DueDate DATE = DATEADD(day, @PaymentTerms, @InvoiceDate);
    DECLARE @InvoiceAmount DECIMAL(18,2) = CAST((5000 + (ABS(CHECKSUM(NEWID())) % 195000)) AS DECIMAL(18,2));
    
    DECLARE @Status NVARCHAR(50);
    DECLARE @PaidDate DATE = NULL;
    DECLARE @PaidAmount DECIMAL(18,2) = NULL;
    DECLARE @DaysLate INT = ABS(CHECKSUM(NEWID())) % 120;
    DECLARE @RandomPct INT = ABS(CHECKSUM(NEWID())) % 100;
    
    IF @DueDate < GETDATE()
    BEGIN
        IF @RandomPct < 60
        BEGIN
            SET @Status = 'Paid';
            SET @PaidDate = DATEADD(day, 
                CASE 
                    WHEN @RandomPct < 35 THEN -ABS(CHECKSUM(NEWID())) % 10
                    WHEN @RandomPct < 50 THEN 0
                    ELSE @DaysLate
                END, 
                @DueDate);
            SET @PaidAmount = @InvoiceAmount;
        END
        ELSE IF @RandomPct < 80
        BEGIN
            SET @Status = 'Overdue';
        END
        ELSE IF @RandomPct < 92
        BEGIN
            SET @Status = 'Partial';
            SET @PaidDate = DATEADD(day, @DaysLate, @DueDate);
            SET @PaidAmount = CAST(@InvoiceAmount * (0.3 + (ABS(CHECKSUM(NEWID())) % 40) / 100.0) AS DECIMAL(18,2));
        END
        ELSE
        BEGIN
            SET @Status = 'Pending';
        END
    END
    ELSE
    BEGIN
        IF @RandomPct < 25
        BEGIN
            SET @Status = 'Paid';
            SET @PaidDate = DATEADD(day, -(ABS(CHECKSUM(NEWID())) % 15), @DueDate);
            SET @PaidAmount = @InvoiceAmount;
        END
        ELSE
        BEGIN
            SET @Status = 'Pending';
        END
    END
    
    IF @PaidDate > GETDATE()
        SET @PaidDate = CAST(GETDATE() AS DATE);
    
    INSERT INTO Invoices (InvoiceNumber, ClientID, ProjectID, InvoiceAmount, InvoiceDate, DueDate, PaidDate, PaidAmount, Status)
    VALUES (
        'INV-' + FORMAT(@InvoiceDate, 'yyyy') + '-' + RIGHT('00000' + CAST(@InvoiceNum AS VARCHAR(5)), 5),
        @ClientID,
        @ProjectID,
        @InvoiceAmount,
        @InvoiceDate,
        @DueDate,
        @PaidDate,
        @PaidAmount,
        @Status
    );
    
    SET @InvoiceNum = @InvoiceNum + 1;
    SET @InvoiceCount = @InvoiceCount + 1;
    
    IF @InvoiceCount % 3000 = 0
        PRINT '      Progress: ' + CAST(@InvoiceCount AS VARCHAR(10)) + ' / ' + CAST(@TargetInvoices AS VARCHAR(10));
END;

PRINT '   > 15,000 Invoices created';

-- ============================================================================
-- STEP 4: Generate ~5,000 Unbilled Work (WIP) entries
-- ============================================================================
PRINT 'Generating Unbilled Work entries (~5,000 records)...';

DECLARE @Descriptions TABLE (ID INT, WorkDesc NVARCHAR(200));
INSERT INTO @Descriptions VALUES
    (1, 'Engineering design review'),
    (2, 'Site inspection and assessment'),
    (3, 'Technical documentation'),
    (4, 'Project management hours'),
    (5, 'Quality assurance testing'),
    (6, 'Stakeholder coordination'),
    (7, 'Environmental impact study'),
    (8, 'Safety compliance audit'),
    (9, 'Materials specification'),
    (10, 'Construction supervision'),
    (11, 'Procurement support'),
    (12, 'Contract administration'),
    (13, 'Risk assessment'),
    (14, 'Cost estimation'),
    (15, 'Schedule development');

DECLARE @Departments TABLE (ID INT, Name NVARCHAR(100));
INSERT INTO @Departments VALUES
    (1, 'Engineering'), (2, 'Design'), (3, 'Project Management'),
    (4, 'Quality Assurance'), (5, 'Construction'), (6, 'Consulting'),
    (7, 'Procurement'), (8, 'Legal'), (9, 'Finance'), (10, 'IT');

DECLARE @WIPCount INT = 0;
DECLARE @TargetWIP INT = 5000;

DECLARE proj_cursor CURSOR FOR 
    SELECT ProjectID FROM Projects WHERE Status IN ('Active', 'On Hold');

OPEN proj_cursor;
FETCH NEXT FROM proj_cursor INTO @ProjectID;

WHILE @@FETCH_STATUS = 0 AND @WIPCount < @TargetWIP
BEGIN
    DECLARE @NumEntries INT = 5 + ABS(CHECKSUM(NEWID())) % 15;
    DECLARE @e INT = 1;
    
    WHILE @e <= @NumEntries AND @WIPCount < @TargetWIP
    BEGIN
        DECLARE @WorkDescription NVARCHAR(200);
        DECLARE @Dept NVARCHAR(100);
        DECLARE @Hours DECIMAL(10,2) = CAST((4 + (ABS(CHECKSUM(NEWID())) % 120)) AS DECIMAL(10,2));
        DECLARE @Rate DECIMAL(10,2) = CAST((150 + (ABS(CHECKSUM(NEWID())) % 450)) AS DECIMAL(10,2));
        
        SELECT @WorkDescription = WorkDesc FROM @Descriptions WHERE ID = (ABS(CHECKSUM(NEWID())) % 15) + 1;
        SELECT @Dept = Name FROM @Departments WHERE ID = (ABS(CHECKSUM(NEWID())) % 10) + 1;
        
        INSERT INTO UnbilledWork (ProjectID, Description, EstimatedValue, LogDate, HoursWorked, HourlyRate, Department)
        VALUES (
            @ProjectID,
            @WorkDescription,
            @Hours * @Rate,
            DATEADD(day, -(ABS(CHECKSUM(NEWID())) % 180), GETDATE()),
            @Hours,
            @Rate,
            @Dept
        );
        
        SET @WIPCount = @WIPCount + 1;
        SET @e = @e + 1;
    END;
    
    FETCH NEXT FROM proj_cursor INTO @ProjectID;
END;

CLOSE proj_cursor;
DEALLOCATE proj_cursor;

PRINT '   > ' + CAST(@WIPCount AS VARCHAR(10)) + ' Unbilled Work entries created';

-- ============================================================================
-- SUMMARY STATISTICS
-- ============================================================================
PRINT '';
PRINT '================================================================================';
PRINT 'DATA GENERATION COMPLETE';
PRINT '================================================================================';
PRINT '';

SELECT 'Clients' AS TableName, COUNT(*) AS RecordCount FROM Clients
UNION ALL
SELECT 'Projects', COUNT(*) FROM Projects
UNION ALL
SELECT 'Invoices', COUNT(*) FROM Invoices
UNION ALL
SELECT 'UnbilledWork', COUNT(*) FROM UnbilledWork;

PRINT '';
PRINT 'Invoice Status Distribution:';
SELECT Status, COUNT(*) AS Count, 
       FORMAT(SUM(InvoiceAmount), 'N2') AS TotalAmount
FROM Invoices 
GROUP BY Status 
ORDER BY Count DESC;

PRINT '';
PRINT 'Aging Summary (Unpaid Invoices):';
SELECT 
    CASE 
        WHEN DATEDIFF(day, DueDate, GETDATE()) <= 0 THEN 'Not Yet Due'
        WHEN DATEDIFF(day, DueDate, GETDATE()) <= 30 THEN 'Current (0-30)'
        WHEN DATEDIFF(day, DueDate, GETDATE()) <= 60 THEN '31-60 Days'
        WHEN DATEDIFF(day, DueDate, GETDATE()) <= 90 THEN '61-90 Days'
        ELSE '90+ Days (Toxic)'
    END AS AgingBucket,
    COUNT(*) AS InvoiceCount,
    FORMAT(SUM(InvoiceAmount), 'N2') AS TotalAmount
FROM Invoices 
WHERE Status IN ('Pending', 'Overdue', 'Partial')
GROUP BY 
    CASE 
        WHEN DATEDIFF(day, DueDate, GETDATE()) <= 0 THEN 'Not Yet Due'
        WHEN DATEDIFF(day, DueDate, GETDATE()) <= 30 THEN 'Current (0-30)'
        WHEN DATEDIFF(day, DueDate, GETDATE()) <= 60 THEN '31-60 Days'
        WHEN DATEDIFF(day, DueDate, GETDATE()) <= 90 THEN '61-90 Days'
        ELSE '90+ Days (Toxic)'
    END;

PRINT '';
PRINT 'Top 10 WIP Projects:';
SELECT TOP 10
    p.ProjectName,
    p.Sector,
    FORMAT(SUM(u.EstimatedValue), 'N2') AS UnbilledValue
FROM UnbilledWork u
JOIN Projects p ON u.ProjectID = p.ProjectID
WHERE u.IsBilled = 0
GROUP BY p.ProjectName, p.Sector
ORDER BY SUM(u.EstimatedValue) DESC;

PRINT '';
PRINT '================================================================================';
PRINT 'Database is ready for Financial Analysis!';
PRINT 'Run main.py to start the automation suite.';
PRINT '================================================================================';
GO
