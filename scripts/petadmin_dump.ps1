$env_type = $args[0]

If ($env_type -eq 'prod') {
    $server = 'SQLEXPRESS'
}

If ($env_type -eq 'dev') {
    $server = 'SQLEXPRESS01'
}

Push-Location -Path $env_type

bcp crowbank.dbo.vwcustomer_dump out tblcustomer -c -S localhost\$server -U PA -P petadmin
bcp crowbank.dbo.vwbreed_dump out tblbreed -c -S localhost\$server -U PA -P petadmin
bcp crowbank.dbo.vwvet_dump out tblvet -c -S localhost\$server -U PA -P petadmin
bcp crowbank.dbo.vwpet_dump out tblpet -c -S localhost\$server -U PA -P petadmin
bcp crowbank.dbo.vwbooking_dump out tblbooking -c -S localhost\$server -U PA -P petadmin
bcp crowbank.dbo.vwbookingitem_dump out tblbookingitem -c -S localhost\$server -U PA -P petadmin
bcp crowbank.dbo.vwpayment_dump out tblpayment -c -S localhost\$server -U PA -P petadmin
sqlcmd -U pa -d crowbank -P petadmin -S localhost\$server -Q "exec mark_change_log_dumped"

Pop-Location