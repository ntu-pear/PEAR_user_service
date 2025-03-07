INSERT INTO [user_service_dev].[dbo].[PRIVACY_LEVEL_SETTING](
    id, active, privacyLevelSensitive, 
    createdDate, modifiedDate, 
    createdById, modifiedById
) VALUES 
('Pc8ec553e5f0', 'True', 'LOW', 
GETDATE(), GETDATE(), 
1, 1),

('Pb895f80031b', 'True', 'MEDIUM',
GETDATE(), GETDATE(), 
1, 1),

('Pc0d01686374', 'True', 'HIGH', 
GETDATE(), GETDATE(), 
1, 1),

('Pbe117b0c697', 'False', 'NONE', 
GETDATE(), GETDATE(), 
1, 1)
