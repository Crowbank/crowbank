$timestamp = (Get-Date -Format "yyyyMMdd_HHmmss")
$env:SQLCMDPASSWORD = "petadmin"
$env:SQLCMDUSER = "PA"

sqlcmd -E -S localhost\SQLEXPRESS -d master -i C:\Python27\lib\site-packages\crowbank\Scripts\sqldump.sql
sqlcmd -E -S localhost\SQLEXPRESS_DEV -d master -i C:\Python27\lib\site-packages\crowbank\Scripts\sqlrestore.sql