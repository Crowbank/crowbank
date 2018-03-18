param([int]$sleep = 10, [string]$url = "http://www.crowbank.site/messaging/dispatch")
$env:DJANGO_ENVIRONMENT = "prod"
python C:\Python27\lib\site-packages\Crowbank\responder.py -sleep $sleep -url $url