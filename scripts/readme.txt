Simple python fronts:
---------------------
confirm.ps1
scan_vaccinations.ps1


Copy production Sql Server/petadmin (SQLEXPRESS) into development (SQLEXPRESS01)
--------------------------------------------------------------------------------
copy_db1.ps1

-- Using

sqldump.sql
sqlrestore.sql


Transfer petadmin data from SQL Server to MySQL
-----------------------------------------------

petadmin_update.ps1

-- Which calls

petadmin_dump.ps1
petadmin_import.ps1

--- which uses
import.sql
