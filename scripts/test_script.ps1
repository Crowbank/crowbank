$folder = (Get-Date -Format "yyyyMMdd_HHmmss")

Set-Location 'D:\db-backups\website'

If (Test-Path $folder) {
	Write-Host "folder $folder exists - deleting"
	Remove-Item -Recurse $folder
}

New-Item -ItemType directory -Path $folder
Set-Location $folder


bcp crowbank.dbo.vwcustomer_mysql out pa_customer.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin
