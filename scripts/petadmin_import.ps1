$env_type = $args[0]

Push-Location -Path $env_type

Copy tblbookingitem tblbookingitem_varchar

Get-Content c:\python27\scripts\import.sql | mysql -u pa -ppetadmin staging

mysqldump -u pa -ppetadmin --result-file=petadmin.sql staging petadmin_customer petadmin_breed petadmin_vet petadmin_pet petadmin_booking petadmin_payment petadmin_bookingitem

Pop-Location