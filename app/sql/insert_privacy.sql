INSERT INTO [user_service_dev].[dbo].[PRIVACY_LEVEL_SETTING](
    id, active, privacyLevelSensitive, 
    createdDate, modifiedDate, 
    createdById, modifiedById
) VALUES 
('Ubdc5372f735', 'True', 1, GETDATE(), GETDATE(), 1, 1),
('Ubdc5372f736', 'True', 2, GETDATE(), GETDATE(), 1, 1),
('Ubdc5372f737', 'True', 3, GETDATE(), GETDATE(), 1, 1),
('Ubdc5372f738', 'False', NULL, GETDATE(), GETDATE(), 1, 1)
