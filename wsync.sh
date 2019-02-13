TMP_DRIVE=/e/tmp
REMOTE_BIN=dev/bin
DLRun="/c/Program Files (x86)/Data Loader 4.8/DLRun.exe"
mysql="/c/Program Files/MariaDB 10.3/bin/mysql.exe"
mysqldump="/c/Program Files/MariaDB 10.3/bin/mysqldump.exe"
zip="/c/Crowbank/zip.exe"
unzip="/c/Crowbank/unzip.exe"

cd $TMP_DRIVE

timestamp="$(date '+%Y%m%d_%H%M%S')"

# Step 1: Copy remote data, both form (rg_lead etc.) and message (messages etc.) from remote database to local mysql

# a. Run the remote script prepare_messages.sh. This script runs the following:
#    cd ~/dev/public_html/staging
#    mysql  --execute="call crowbank_w301_dev.PrepareMessages();"
#    mysqldump -pCrowbank454 -u crowbank_petadmin -h localhost crowbank_staging crwbnk_messages crwbnk_msgmeta > remote_messages_dev.sql
#    mysqldump -pCrowbank454 -u crowbank_petadmin -h localhost crowbank_wp301 crwbnk_rg_lead crwbnk_rg_lead_detail > remote_messages.sql
#    zip remote_messages remote_messages*.sql

ssh crowbank@cp165172.hpdns.net "$REMOTE_BIN/prepare_messages.sh"

# 1

msg="$stage: Remote messages prepared"
echo "$(date '+%H:%M:%S')  $msg"

# b. Transfer the file locally
scp crowbank@cp165172.hpdns.net:dev/staging/remote_messages.zip . # || error_exit "Downloading remote_messages failed"

# c. unzip
rm remote_messages*.sql
$unzip remote_messages.zip # || error_exit "Unzipping remote_messages failed"

# 2

msg="$stage: Remote messages retrieved"
echo "$(date '+%H:%M:%S')  $msg"

"$mysql" -u root -pCrowbank454 --database=crowbank_staging < remote_messages.sql
"$mysql" -u root -pCrowbank454 --database=crowbank_staging < remote_messages_dev.sql

# 3

msg="$stage: Remote messages loaded"
echo "$(date '+%H:%M:%S')  $msg"

# e. Run DL to transfer local message content to SQL SERVER database

# first, transfer production messages to SQLExpress
"$DLRun" 1 # || error_exit "DLRun 15 failed"

sleep 10

# 5

msg="$stage: All messages loaded to MSSQL"
echo "$(date '+%H:%M:%S')  $msg"

#    f. Run SQL Server command to process new messages

# first, run production stuff

python /c/Crowbank/sqlcmd.py "Execute pimport_rg_lead"
python /c/Crowbank/sqlcmd.py "Execute pmessage_process"

# rename_vaccination_file.py || plog "rename_vaccination_file failed"
# /cygdrive/c/Program\ Files/Python37/python.exe 'C:\Program Files\Python37\Lib\site-packages\crowbank\rename_vaccination_file.py' || plog "rename_vaccination_file failed"
# python /c/Crowbank/rename_vaccination_file.py # || plog "rename_vaccination_file failed"

# 6
msg="$stage: Messages processed"
echo "$(date '+%H:%M:%S')  $msg"

#    g. Run MySQL command to mark messages as 'sent', both locally and remotely.

ssh crowbank@cp165172.hpdns.net $REMOTE_BIN/messages_processed.sh # || error_exit "Remote messages_processed failed"

# cmysql "call MessagesProcessed();" || error_exit "Local MessagesProcessed failed"

# 7
msg="$stage: Messages processed feedback"
echo "$(date '+%H:%M:%S')  $msg"

# Step 2: Transfer PetAdmin info to MySQL databases

#    a. Run pmaster on SQL Server to collect relevant information into mysql database

python /c/Crowbank/sqlcmd.py "Execute pmaster" # || error_exit "pmaster failed"
msg="$stage: pmaster executed"

echo "$(date '+%H:%M:%S')  $msg"

#    b. Run DL to transfer from SQLEXPRESS.mysql database to MySQL.staging
# first, production

"$DLRun" 2 # || error_exit "DLRun 14 failed"
sleep 10

# 9

msg="$stage: Local mysql staging populated"
echo "$(date '+%H:%M:%S')  $msg"

#    c. Dump staging database from localhost to a file, and read into remote database
"$mysqldump" --host=192.168.0.200 --result-file crowbank_petadmin.sql --user=root -pCrowbank454 --ignore-table=crowbank_staging.tbllog crowbank_staging # || error_exit "Local sqldump failed"

#    c. Run RefreshFromStaging to copy new rows into main (crowbank_petadmin) database

# mysql -u root -pCrowbank454 --database=crowbank_staging "call RefreshFromStaging();"
# cmysql "call RefreshFromStaging();" || error_exit "Local RefreshFromStaging failed"

# 10

msg="$stage: Local staging dumped"
echo "$(date '+%H:%M:%S')  $msg"

#    e. Compress

$zip crowbank_petadmin.zip crowbank_petadmin.sql
rm crowbank_petadmin_prev.sql
mv crowbank_petadmin.sql crowbank_petadmin_prev.sql

# f. ftp over to website

scp crowbank_petadmin.zip crowbank@cp165172.hpdns.net:dev/staging/crowbank_petadmin.zip
rm crowbank_petadmin.zip

# 11

msg="$stage: Local dumped uploaded"
echo "$(date '+%H:%M:%S')  $msg"

# g. Execute remote script with the following lines:

ssh crowbank@cp165172.hpdns.net $REMOTE_BIN/refresh_from_staging.sh

# 12

msg="$stage: Refresh from staging executed"
echo "$(date '+%H:%M:%S')  $msg"

# vacc_sync.bat || error_exit "vacc_sync failed"

# 13

msg='Web sync completed'
echo "$(date '+%H:%M:%S')  $msg"
