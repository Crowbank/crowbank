$folder = (Get-Date -Format "yyyyMMdd_HHmmss")

Set-Location 'E:\DB Backups\petadmin_data'

If (Test-Path $folder) {
	Write-Host "folder $folder exists - deleting"
	Remove-Item -Recurse $folder
}

New-Item -ItemType directory -Path $folder
Set-Location $folder

New-Item -ItemType directory -Path prod
New-Item -ItemType directory -Path dev

petadmin_dump prod
petadmin_import prod
petadmin_dump dev
petadmin_import dev

Move-Item prod\petadmin.sql .\petadmin_prod.sql
Move-Item dev\petadmin.sql .\petadmin_dev.sql

Get-Content petadmin_dev.sql | mysql -u pa -ppetadmin petadmin_data

Copy-Item .\petadmin_prod.sql 'E:\DB Backups\petadmin_data\latest\petadmin_prod.sql'
Copy-Item .\petadmin_dev.sql 'E:\DB Backups\petadmin_data\latest\petadmin_qa.sql'

Set-Location 'E:\DB Backups\petadmin_data\latest'

& "C:\Program Files (x86)\WinSCP\winscp" /script=c:\python27\scripts\winscp.txt