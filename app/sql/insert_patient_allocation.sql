INSERT INTO [user_service_dev].[dbo].[PATIENT_ALLOCATION](
    patientId, active, doctorId,
    gameTherapistId, supervisorId, caregiverId,
    guardianId, tempDoctorId, tempCaregiverId, 
    guardian2Id, createdDate, modifiedDate,
    createdById, modifiedById
) VALUES 
('Pc8ec553e5f0', 1, 'Dd31e15522f4', 
'Gd7acef5fa69', 'S85f3847c88b', 'C01d447fkcfe',
'Gbdc5372f735', NULL, NULL,
NULL, GETDATE(), GETDATE(), 
1, 1),

('Pb895f80031b', 1, 'Dd31e15522f4',
'Gd7acef5fa69', 'S85f3847c88b', 'C01d447fkcfe',
'Gbdc5372f735', NULL, NULL,
NULL, GETDATE(), GETDATE(), 
1, 1),

('Pc0d01686374', 1, 'Dd31e15522f4', 
'Gd7acef5fa69', 'S85f3847c88b', 'C01d447fkcfe',
'Gbdc5372f736', NULL, NULL,
NULL, GETDATE(), GETDATE(), 
1, 1),

('Pbe117b0c697', 1, 'Dd31e15522f4', 
'Gd7acef5fa69', 'S85f3847c88b', 'C01d447fkcfe',
'Gbdc5372f737', NULL, NULL,
'Gbdc5372f738', GETDATE(), GETDATE(), 
1, 1)