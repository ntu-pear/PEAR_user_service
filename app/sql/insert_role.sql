INSERT INTO [user_service_dev].[dbo].[TABLE_ROLES] (
    id, active, roleName, privacyLevelSensitive, createdDate, modifiedDate, createdById, modifiedById
) VALUES
('ADmin123', 1, 'ADMIN', 'NONE', GETDATE(), GETDATE(), 1, 1),
('DOctor12', 1, 'DOCTOR', 'HIGH', GETDATE(), GETDATE(), 1, 1),
('Guard123', 1, 'GUARDIAN', 'HIGH', GETDATE(), GETDATE(), 1, 1),
('Game1234', 1, 'GAME THERAPIST', 'LOW', GETDATE(), GETDATE(), 1, 1),
('Super085', 1, 'SUPERVISOR', 'HIGH', GETDATE(), GETDATE(), 1, 1),
('Care1562', 1, 'CAREGIVER', 'MEDIUM', GETDATE(), GETDATE(), 1, 1);

-- INSERT INTO [user_service_dev].[dbo].[TABLE_ROLES](
--     id, active, roleName, createdDate, modifiedDate, createdById, modifiedById
-- ) 
-- VALUES
--     ('ADMIN', 1, 'ADMIN', GETDATE(), GETDATE(), 1, 1),
--     ('DOCTOR', 1, 'DOCTOR', GETDATE(), GETDATE(), 1, 1),
--     ('GUARDIAN', 1, 'GUARDIAN', GETDATE(), GETDATE(), 1, 1),
--     ('GAME_THERAPIST', 1, 'GAME THERAPIST', GETDATE(), GETDATE(), 1, 1),
--     ('SUPERVISOR', 1, 'SUPERVISOR', GETDATE(), GETDATE(), 1, 1),
--     ('CAREGIVER', 1, 'CAREGIVER', GETDATE(), GETDATE(), 1, 1);
