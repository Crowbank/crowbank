$folder = (Get-Date -Format "yyyyMMdd_HHmmss")
$mysql = "C:\wamp64\bin\mysql\mysql5.7.14"

Set-Location 'D:\db-backups\website'

If (Test-Path $folder) {
	Write-Host "folder $folder exists - deleting"
	Remove-Item -Recurse $folder
}

New-Item -ItemType directory -Path $folder
Set-Location $folder

bcp crowbank.dbo.vwcustomer_mysql out pa_customer.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin
bcp crowbank.dbo.vwspecies_mysql out pa_species.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin
bcp crowbank.dbo.vwbreed_mysql out pa_breed.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin
bcp crowbank.dbo.vwbillcategory_mysql out pa_billcategory.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin
bcp crowbank.dbo.vwvet_mysql out pa_vet.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin
bcp crowbank.dbo.vwpet_mysql out pa_pet.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin
bcp crowbank.dbo.vwbooking_mysql out pa_booking.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin
bcp crowbank.dbo.vwbookingitem_mysql out pa_bookingitem.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin
bcp crowbank.dbo.vwavailability_mysql out pa_availability.txt -c -S localhost\SQLEXPRESS -U PA -Ppetadmin


#& mysqlimport --host=cp165172.hpdns.net --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_customer.txt
#& mysqlimport --host=cp165172.hpdns.net --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_species.txt
#& mysqlimport --host=cp165172.hpdns.net --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_billcategory.txt
#& mysqlimport --host=cp165172.hpdns.net --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_breed.txt
#& mysqlimport --host=cp165172.hpdns.net --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_vet.txt
#& mysqlimport --host=cp165172.hpdns.net --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_pet.txt
#& mysqlimport --host=cp165172.hpdns.net --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_booking.txt
#& "$mysql\bin\mysql" --host cp165172.hpdns.net --user crowbank_petadmin --database=crowbank_petadmin --execute="truncate table pa_bookingitem" --password=Crowbank454
#& mysqlimport --host=cp165172.hpdns.net --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_bookingitem.txt
#& "$mysql\bin\mysql" --host cp165172.hpdns.net --user crowbank_petadmin --database=crowbank_petadmin --execute="truncate table pa_availability" --password=Crowbank454
#& mysqlimport --host=cp165172.hpdns.net --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_availability.txt

& mysqlimport --host=localhost --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_customer.txt
& mysqlimport --host=localhost --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_species.txt
& mysqlimport --host=localhost --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_billcategory.txt
& mysqlimport --host=localhost --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_breed.txt
& mysqlimport --host=localhost --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_vet.txt
& mysqlimport --host=localhost --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_pet.txt
& mysqlimport --host=localhost --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_booking.txt
& mysql --host localhost --user crowbank_petadmin --database=crowbank_petadmin --execute="truncate table pa_bookingitem" --password=Crowbank454
& mysqlimport --host=localhost --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_bookingitem.txt
& mysql --host localhost --user crowbank_petadmin --database=crowbank_petadmin --execute="truncate table pa_availability" --password=Crowbank454
& mysqlimport --host=localhost --local --password=Crowbank454 --replace --user=crowbank_petadmin crowbank_petadmin pa_availability.txt

& mysqldump --host=localhost --result-file crowbank_petadmin.sql --password=Crowbank454 --user=crowbank_petadmin crowbank_petadmin
Get-Content .\crowbank_petadmin.sql | mysql --host=cp165172.hpdns.net --password=Crowbank454 --user=crowbank_petadmin --database=crowbank_petadmin

& mysqldump --host=cp165172.hpdns.net --result-file rg_lead.sql --password=Crowbank454 --user=crowbank_petadmin crowbank_wp301 crwbnk_rg_lead
& mysqldump --host=cp165172.hpdns.net --result-file rg_lead_detail.sql --password=Crowbank454 --user=crowbank_petadmin crowbank_wp301 crwbnk_rg_lead_detail

Get-Content .\rg_lead.sql | mysql --host=localhost --password=Crowbank454 --user=crowbank --database=crowbank_petadmin
Get-Content .\rg_lead_detail.sql | mysql --host=localhost --password=Crowbank454 --user=crowbank --database=crowbank_petadmin

Push-Location "$mysql\Uploads"
New-Item -ItemType directory -Path $folder
Set-Location $folder

& mysqldump --host=localhost --result-file rg_lead.sql --tab="C:\ProgramData\MySQL\MySQL Server 5.7\Uploads\$folder" --password=Crowbank454 --user=crowbank crowbank_petadmin crwbnk_rg_lead

& mysql --host=localhost  --password=Crowbank454 --user=crowbank --database=crowbank_petadmin --execute "update crwbnk_rg_lead_detail set value = replace(replace(value, '\r', '<CR>'), '\n', '<LF>') where id > 0;"
& mysqldump --host=localhost --result-file rg_lead_detail.sql --tab="C:\ProgramData\MySQL\MySQL Server 5.7\Uploads\$folder" --password=Crowbank454 --user=crowbank crowbank_petadmin crwbnk_rg_lead_detail

(Get-Content .\crwbnk_rg_lead.txt) -join "`r`n" | Out-File -Encoding ascii rg_lead.txt
(Get-Content .\crwbnk_rg_lead_detail.txt) -join "`r`n" | Out-File -Encoding ascii rg_lead_detail.txt

sqlcmd -U PA -P petadmin -d crowbank -Q "truncate table tblrg_lead_staging"
sqlcmd -U PA -P petadmin -d crowbank -Q "truncate table tblrg_lead_detail_staging"

bcp tblrg_lead_staging in "$mysql\Uploads\$folder\rg_lead.txt" -c -d crowbank -S localhost\SQLEXPRESS -U PA -Ppetadmin
bcp tblrg_lead_detail_staging in "$mysql\Uploads\$folder\rg_lead_detail.txt" -c -d crowbank -S localhost\SQLEXPRESS -U PA -Ppetadmin

sqlcmd -U PA -P petadmin -d crowbank -Q "execute pimport_rg_lead"

Pop-Location
Set-Location '..'
