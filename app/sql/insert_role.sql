INSERT INTO [user_service_dev].[dbo].[TABLE_ROLES](
   active, roleName,createdDate, modifiedDate, createdById,modifiedById
) VALUES
("Y","ADMIN", GETDATE(), GETDATE(),1,1),
("Y","DOCTOR", GETDATE(), GETDATE(),1,1),
("Y","GUARDIAN", GETDATE(), GETDATE(),1,1),
("Y","GAME THERAPIST", GETDATE(), GETDATE(),1,1),
("Y","SUPERVISOR", GETDATE(), GETDATE(),1,1),
("Y","CAREGIVER", GETDATE(), GETDATE(),1,1);
