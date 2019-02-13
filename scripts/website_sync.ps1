sqlcmd -U PA -P petadmin -d crowbank -Q "Execute plog 'Website sync starting', 'INFO', 'website_sync.ps1', NULL, NULL, NULL, NULL"

cd C:\wamp64\tmp

# Step 1: Copy remote data, both form (rg_lead etc.) and message (messages etc.) from remote database to local mysql

#    a. Run remote PrepareMessages which copies relevant messages to remote staging database (based on most recent lastmsg table content)

& mysql --host=cp165172.hpdns.net --user crowbank_petadmin --database=crowbank_wp301_dev --execute="call PrepareMessages();" --password=Crowbank454


#    b. sqldump tables from remote staging to a file

& mysqldump --host=cp165172.hpdns.net --result-file remote_messages_dev.sql --password=Crowbank454 --user=crowbank_petadmin crowbank_staging crwbnk_messages crwbnk_msgmeta
& mysqldump --host=cp165172.hpdns.net --result-file remote_messages.sql --password=Crowbank454 --user=crowbank_petadmin crowbank_wp301 crwbnk_rg_lead crwbnk_rg_lead_detail


#    c. sql load those tables to local staging tables

Get-Content .\remote_messages.sql | mysql --host=localhost --password=Crowbank454 --user=crowbank_petadmin --database=staging
Get-Content .\remote_messages_dev.sql | mysql --host=localhost --password=Crowbank454 --user=crowbank_petadmin --database=staging


#    d. Run local PrepareMessages to add local messages to local staging tables (note - unlike the remote version, this one does not truncate)

& mysql --host=localhost --user crowbank_petadmin --database=crowbank_petadmin --execute="call PrepareMessages();" --password=Crowbank454


#    e. Run DL to transfer local message content to SQL SERVER database

DLRun 7
Start-Sleep -s 20


#    f. Run SQL Server command to process new messages

sqlcmd -U PA -P petadmin -d crowbank -Q "Execute pimport_rg_lead"
sqlcmd -U PA -P petadmin -d crowbank -Q "Execute pmessage_process"


#    g. Run MySQL command to mark messages as 'sent', both locally and remotely.

& mysql --host=cp165172.hpdns.net --user crowbank_petadmin --database=crowbank_wp301_dev --execute="call MessagesProcessed();" --password=Crowbank454
& mysql --host=localhost --user crowbank_petadmin --database=crowbank_petadmin --execute="call MessagesProcessed();" --password=Crowbank454


# Step 2: Transfer PetAdmin info to MySQL databases

#    a. Run pmaster on SQL Server to collect relevant information into mysql database

sqlcmd -U PA -P petadmin -d crowbank -Q "Execute pmaster"


#    b. Run DL to transfer from SQLEXPRESS.mysql database to MySQL.staging

DLRun 6
Start-Sleep -s 30


#    c. Run RefreshFromStaging to copy new rows into main (crowbank_petadmin) database

& mysql --host=localhost --user crowbank_petadmin --database=crowbank_petadmin --execute="call RefreshFromStaging();" --password=Crowbank454


#    d. Dump staging database from localhost to a file, and read into remote database

& mysqldump --host=localhost --result-file crowbank_petadmin.sql --password=Crowbank454 --user=crowbank_petadmin staging
Get-Content .\crowbank_petadmin.sql | mysql --host=cp165172.hpdns.net --password=Crowbank454 --user=crowbank_petadmin --database=crowbank_staging

#    e. Run RefreshFromStaging on remote database

& mysql --host=cp165172.hpdns.net --user crowbank_petadmin --database=crowbank_petadmin --execute="call RefreshFromStaging();" --password=Crowbank454

sqlcmd -U PA -P petadmin -d crowbank -Q "Execute plog 'Website sync done', 'INFO', 'website_sync.ps1', NULL, NULL, NULL, NULL"

<#
DLRun 3
DLRun 6
DLRun 5

Start-Sleep -s 300

& mysql --host localhost --user crowbank_petadmin --database=crowbank_petadmin --execute="call RefreshFromStaging();" --password=Crowbank454
sqlcmd -U PA -P petadmin -d crowbank -Q "execute pmessage_process"

& mysqldump --host=localhost --result-file crowbank_petadmin.sql --password=Crowbank454 --user=crowbank_petadmin staging
Get-Content .\crowbank_petadmin.sql | mysql --host=cp165172.hpdns.net --password=Crowbank454 --user=crowbank_petadmin --database=crowbank_staging
& mysql --host=cp165172.hpdns.net --user crowbank_petadmin --database=crowbank_petadmin --execute="call RefreshFromStaging();" --password=Crowbank454

& mysqldump --host=cp165172.hpdns.net --result-file remote_messages.sql --password=Crowbank454 --user=crowbank_petadmin crowbank_wp301_dev crwbnk_messages crwbnk_msgmeta
Get-Content .\remote_messages.sql | mysql --host=localhost --password=Crowbank454 --user=crowbank_petadmin --database=staging

#>