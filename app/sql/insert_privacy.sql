INSERT INTO [user_service_dev].[dbo].[PRIVACY_LEVEL_SETTING](
    id, active, privacyLevelSensitive, 
    createdDate, modifiedDate, 
    createdById, modifiedById
) VALUES 
('Ubdc5372f735', 'True', 'LOW', GETDATE(), GETDATE(), 1, 1),
('Ubdc5372f736', 'True', 'MEDIUM', GETDATE(), GETDATE(), 1, 1),
('Ubdc5372f737', 'True', 'HIGH', GETDATE(), GETDATE(), 1, 1),
('Ubdc5372f738', 'False', 'NONE', GETDATE(), GETDATE(), 1, 1)
