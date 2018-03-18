RESTORE DATABASE petadmin6 FROM DISK = 'D:\DB-Backups\petadmin6.bak'
WITH CHECKSUM, MOVE 'blank' TO 'C:\Program Files\Microsoft SQL Server\MSSQL13.SQLEXPRESS_DEV\MSSQL\DATA\petadmin6.mdf', 
MOVE 'blank_log' TO 'C:\Program Files\Microsoft SQL Server\MSSQL13.SQLEXPRESS_DEV\MSSQL\DATA\petadmin6.ldf', 
RECOVERY, REPLACE, STATS = 10;

RESTORE DATABASE crowbank FROM DISK = 'D:\DB-Backups\crowbank.bak'
WITH CHECKSUM, MOVE 'crowbank' TO 'C:\Program Files\Microsoft SQL Server\MSSQL13.SQLEXPRESS_DEV\MSSQL\DATA\crowbank.mdf', 
MOVE 'crowbank_log' TO 'C:\Program Files\Microsoft SQL Server\MSSQL13.SQLEXPRESS_DEV\MSSQL\DATA\crowbank.ldf', 
RECOVERY, REPLACE, STATS = 10;