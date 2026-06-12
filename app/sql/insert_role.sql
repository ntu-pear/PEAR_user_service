INSERT INTO [user_service_dev].[dbo].[TABLE_ROLES] (
    [id],
    [isDeleted],
    [roleName],
    [description],
    [accessLevelId],
    [createdDate],
    [modifiedDate],
    [createdById],
    [modifiedById]
) VALUES
('ADmin123', 0, 'ADMIN',          'Full administrative access to user and system management',           'ACL00001', GETDATE(), GETDATE(), '1', '1'),
('DOctor12', 0, 'DOCTOR',         'Provides clinical services and accesses relevant patient records',   'ACL00004', GETDATE(), GETDATE(), '1', '1'),
('Guard123', 0, 'GUARDIAN',       'Represents and manages matters for assigned patients',              'ACL00004', GETDATE(), GETDATE(), '1', '1'),
('Game1234', 0, 'GAME THERAPIST', 'Conducts therapy activities with limited sensitive access',         'ACL00002', GETDATE(), GETDATE(), '1', '1'),
('Super085', 0, 'SUPERVISOR',     'Supervises operations and staff workflows',                         'ACL00004', GETDATE(), GETDATE(), '1', '1'),
('Care1562', 0, 'CAREGIVER',      'Supports daily care and accesses moderately sensitive information', 'ACL00003', GETDATE(), GETDATE(), '1', '1');