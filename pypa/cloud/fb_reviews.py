#!/usr/bin/python
from urllib.request import urlopen
from json import loads
import pymssql
import datetime
from settings import *

APP_ID = '218121085660954'

TOKEN = 'EAACEdEose0cBAMWLx2txZAEr3b3u2VnZADVDM8ZC4OmeG06CZBLygqqCUWZAdnhJfrFem2lWUBZBq2NjiqQe1wzNdDKrnebrVZAMLn0XSVef3cX2jBRYpivt2AEFLHmXKgCzsyPZBeOApyyHapAdHuwrBuH2fOit5nTLyJGlUeMZBVBkxFtJrbHwWiiV8ffeEZCbUpaEgjf2EPFwZDZD'

APP_SECRET = '39dd636ab6182b6af17997a2976acf79'

url = "https://graph.facebook.com/v3.0/crowbank?fields=ratings&access_token=EAADGYUXULxoBAM9Og5mtSHJAYI5SyZB8gcGrI3tmPegyzXo2ZALHw76bZA0TppahVZA3ns9ZCu057M6trbn5kZCxrR5kvznircbHSNhbdGAy8aXV1fik7EXEcDeTapupFVWJsBvJSLgoTGAZCIEKL86ACQwPJpsZBcjTJ3bekceDNgZDZD"
 
data = []
first = True

while True:
    f = urlopen(url)
    d = f.read()
    d = loads(d)
    if first:
        d = d['ratings']
        first = False

    data += d['data']
    p = d['paging']
    if 'next' in p:
        url = p['next']
    else:
        break

con = pymssql.connect(server=DB_SERVER, user=DB_USER, password=DB_PWD, database=DB_DATABASE)
cur = con.cursor()

sql = 'truncate table tblfb_review_staging'
cur.execute(sql)

for review in data:
    if 'review_text' in review:
        review_text = review['review_text'].encode('ascii', 'replace').replace("'", "''")
    else:
        review_text = ''
    
    reviewer_name = review['reviewer']['name'].encode('ascii', 'replace').replace("'", "''")
    sql = "insert into tblfb_review_staging (fbr_create_time, fbr_rating, fbr_text, fbr_id, fbr_name) values ("
    sql += "'%s', %d, '%s', '%s', '%s')" % (review['created_time'], review['rating'], review_text, review['reviewer']['id'], reviewer_name)
    print (sql)
    cur.execute(sql)

con.commit()

