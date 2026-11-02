USE [user_service_dev];
GO

BEGIN TRY
    BEGIN TRANSACTION;

    ------------------------------------------------------------
    -- 1) Seed system access levels if missing
    ------------------------------------------------------------
    IF NOT EXISTS (SELECT 1 FROM [dbo].[TABLE_ACCESS_LEVELS] WHERE [code] = 'NONE')
    BEGIN
        INSERT INTO [dbo].[TABLE_ACCESS_LEVELS]
            ([id], [code], [levelRank], [levelName], [description], [isSystem], [createdById], [modifiedById])
        VALUES
            ('ACL00001', 'NONE',   0, 'None',   'No access to sensitive data',            1, 'SYSTEM', 'SYSTEM'),
            ('ACL00002', 'LOW',    1, 'Low',    'Limited access to low-sensitivity data', 1, 'SYSTEM', 'SYSTEM'),
            ('ACL00003', 'MEDIUM', 2, 'Medium', 'Access to moderately sensitive data',    1, 'SYSTEM', 'SYSTEM'),
            ('ACL00004', 'HIGH',   3, 'High',   'Full access to highly sensitive data',   1, 'SYSTEM', 'SYSTEM');
    END;

    ------------------------------------------------------------
    -- 2) Seed roles if missing
    ------------------------------------------------------------
    IF NOT EXISTS (SELECT 1 FROM [dbo].[TABLE_ROLES] WHERE [roleName] = 'ADMIN')
    BEGIN
        INSERT INTO [dbo].[TABLE_ROLES]
            ([id], [isDeleted], [roleName], [description], [accessLevelId], [createdDate], [modifiedDate], [createdById], [modifiedById])
        VALUES
            ('ADmin123', 0, 'ADMIN',           'Full administrative access to user and system management',           'ACL00001', GETDATE(), GETDATE(), '1', '1'),
            ('DOctor12', 0, 'DOCTOR',          'Provides clinical services and accesses relevant patient records',   'ACL00004', GETDATE(), GETDATE(), '1', '1'),
            ('Guard123', 0, 'GUARDIAN',        'Represents and manages matters for assigned patients',              'ACL00004', GETDATE(), GETDATE(), '1', '1'),
            ('Game1234', 0, 'GAME THERAPIST',  'Conducts therapy activities with limited sensitive access',         'ACL00002', GETDATE(), GETDATE(), '1', '1'),
            ('Super085', 0, 'SUPERVISOR',      'Supervises operations and staff workflows',                         'ACL00004', GETDATE(), GETDATE(), '1', '1'),
            ('Care1562', 0, 'CAREGIVER',       'Supports daily care and accesses moderately sensitive information', 'ACL00003', GETDATE(), GETDATE(), '1', '1');
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
GO