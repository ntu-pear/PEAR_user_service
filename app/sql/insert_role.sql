INSERT INTO [user_service_dev].[dbo].[TABLE_ROLES](
   id,active, roleName,createdDate, modifiedDate, createdById,modifiedById
) VALUES
("ADmin123","Y","ADMIN", GETDATE(), GETDATE(),1,1),
("DOctor12","Y","DOCTOR", GETDATE(), GETDATE(),1,1),
("Guard123","Y","GUARDIAN", GETDATE(), GETDATE(),1,1),
("Game1234","Y","GAME THERAPIST", GETDATE(), GETDATE(),1,1),
("Super085","Y","SUPERVISOR", GETDATE(), GETDATE(),1,1),
("Care1562","Y","CAREGIVER", GETDATE(), GETDATE(),1,1);
