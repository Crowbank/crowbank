$timestamp = (Get-Date -Format "yyyymmdd_HHMMss")
$file="change_log"

Set-Location C:\Users\Fiona\Dropbox\python\crowbank_site\petadmin_data\incremental

bcp PA.dbo.change_log_dump_sql out $file -c -S localhost\SQLEXPRESS -U PA -P petadmin
if (Test-Path $file) { 
 if ((Get-Item $file).length -gt 0kb) {
    sqlcmd -U pa -d PA -P petadmin -Q "exec mark_change_log_dumped"
    Get-Content $file | mysql -u pa -ppetadmin
    & "C:\Program Files (x86)\WinSCP\winscp" /script=c:\python27\scripts\winscp_inc.txt
    Rename-Item $file $file + "_" + $timestamp
}
}
