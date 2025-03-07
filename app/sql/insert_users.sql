INSERT INTO [user_service_dev].[dbo].[TABLE_USER](
    id, nric_FullName, nric_DateOfBirth, 
    nric_Gender, nric_Address, 
    profilePicture,
    password, contactNo, 
    contactNoConfirmed, allowNotification, 
    email, emailConfirmed, 
    roleName, nric, 
    verified, active, 
    status, twoFactorEnabled, 
    lockOutEnabled,createdById, modifiedById
) VALUES 
('Afa53ec48e2f', 'JANICE ONG', '2000-02-01', 
 'F', '123 Serangoon Ave 1 #04-332 Singapore 550123',
'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162954/profile_pictures/user_Ufa53ec48e2f_profile_picture.jpg',
 '$2b$12$V5R/Wm4kL8kRq5fDltV4oew.AF0e09ytYVYj8cJp0Lp.seCyOGRQ2', '81241223',
 1, 1,
 'janice@gmail.com', 1, 
 'ADMIN', 'T0012323D', 
 1, 1,
 'ACTIVE', 0,
 0,1,1),
('Dd31e15522f4', 'DANIEL ANG', '09/05/1994', 
 'M', '123 Punggol Ave 1 #04-332 Singapore 550123',
'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162837/profile_pictures/user_Ud31e15522f4_profile_picture.jpg',
 '$2b$12$nQ5SzcexiVu8p6oNnO.Ku.y3iYasqd3yYC1AYWktiwbnjfybD.fte', '83232223',
1, 1,
 'daniel@gmail.com', 1,
 'DOCTOR', 'T0123245D',
 1, 1,
 'ACTIVE', 0,
 0,1,1),
('Gbdc5372f735', 'DAWN ONG', '2002-04-01', 
 'F', '123 Sengkang Ave 1 #04-332 Singapore 550123',
'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162875/profile_pictures/user_Ubdc5372f735_profile_picture.jpg',
 '$2b$12$4S4oqUK/bKd2mxYln/HT7ujrMDExRoCUW3eGe3KNUxXU20ml.KSX6', '85551223',
1, 1,
 'dawnong333@gmail.com', 1,
 'GUARDIAN', 'T0299934C',
 1, 1,
 'ACTIVE', 0,
 0,1,1),
 ('Gbdc5372f736', 'TAN WEI XUN', '1998-04-01', 
 'F', '123 Hougang Ave 1 #04-332 Singapore 550123',
'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162875/profile_pictures/user_Ubdc5372f735_profile_picture.jpg',
 '$2b$12$4S4oqUK/bKd2mxYln/HT7ujrMDExRoCUW3eGe3KNUxXU20ml.KSX6', '81933366',
1, 1,
 'weixun@gmail.com', 1,
 'GUARDIAN', 'S5806206E',
 1, 1,
 'ACTIVE', 0,
 0,1,1),
 ('Gbdc5372f737', 'TEONG SHU HUI', '1985-08-15', 
 'F', '123 Bukit Panjang Ave 1 #04-332 Singapore 550123',
'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162875/profile_pictures/user_Ubdc5372f735_profile_picture.jpg',
 '$2b$12$4S4oqUK/bKd2mxYln/HT7ujrMDExRoCUW3eGe3KNUxXU20ml.KSX6', '81667763',
1, 1,
 'shihui@gmail.com', 1,
 'GUARDIAN', 'S1682865C',
 1, 1,
 'ACTIVE', 0,
 0,1,1),
 ('Gbdc5372f738', 'LAM CHENG BOON', '1990-02-19', 
 'M', '123 Bukit Merah Ave 1 #04-332 Singapore 550123',
'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162875/profile_pictures/user_Ubdc5372f735_profile_picture.jpg',
 '$2b$12$4S4oqUK/bKd2mxYln/HT7ujrMDExRoCUW3eGe3KNUxXU20ml.KSX6', '62818659',
1, 1,
 'chengboon@gmail.com', 1,
 'GUARDIAN', 'S1470536H',
 1, 1,
 'ACTIVE', 0,
 0,1,1),
('Gd7acef5fa69', 'ALAN WEE', '2003-05-01', 
 'M', '123 Bukit Timah Ave 1 #04-332 Singapore 550123',
'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162902/profile_pictures/user_Ud7acef5fa69_profile_picture.jpg',
 '$2b$12$/Q9Qa2OQauodJEI6z4VP..Lekly0Do5R1tUmKKG.rjkn8vrhhFydm', '88881223',
1, 1,
 'alan@gmail.com', 1,
 'GAME THERAPIST', 'T0341345E',
 1, 1,
 'ACTIVE', 0,
 0,1,1),
('S85f3847c88b', 'JESS NG', '2000-01-20',
 'F', '123 Jurong West Ave 1 #04-332 Singapore 550123',
'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162931/profile_pictures/user_U85f3847c88b_profile_picture.jpg',
 '$2b$12$qpDckkqxzQhZydgptBJja.Re1bHgFselcw5vHuLy44vnrIpqQnrJa', '89992293',
1, 1,
 'jess@gmail.com',1,
 'SUPERVISOR', 'T0048674B',
 1, 1,
 'ACTIVE', 0,
 0,1,1),
('C01d447fkcfe', 'ADELINE TAN', '1999-04-30',
 'F', '123 Ang Mo Kio Ave 1 #04-332 Singapore 550123', 
 'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739163007/profile_pictures/user_U01d447fkcfe_profile_picture.jpg',
 '$2b$12$F8MSipfJiWONuft4Vh3F9eniepEkCtLCs2.vFhf8S6/SCF4pjVbAG', '99991223',
1, 1,
 'adeline@gmail.com', 1,
 'CAREGIVER', 'S9996953A',
 1, 1,
 'ACTIVE', 0,
 0,1,1),
('C9b44ce4l228', 'ADELINE ANG', '1980-08-10',
 'F', '123 Bishan Ave 1 #04-332 Singapore 550123',
'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739163025/profile_pictures/user_U9b44ce4l228_profile_picture.jpg',
 '$2b$12$qxNdnOxXHOznR2QlvdReF.xkobALMNWpEN377f8J39yNQ34eHt6Tu', '95231223',
1, 1,
 'adeline2@gmail.com', 1,
 'CAREGIVER', 'S8080809D',
 1, 1,
 'ACTIVE', 0,
 0,1,1);