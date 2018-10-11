import datetime
import webbrowser
from mako.template import Template
from petadmin import PetAdmin, MailInterface


with open("C:\Users\Fiona\Dropbox\Marketing\Logo\Letterhead Banner.png", "rb") as f:
    data = f.read()
    logo_code = data.encode("base64")

mi = MailInterface()
pa = PetAdmin()
pa.load()
bk = pa.bookings.get(2979)

if 0:
    today_date = datetime.date.today()
    d = 'C:\\Users\\Fiona\\Dropbox\\python\\petadmin\\'
    infile = 'Confirmation'
    mytemplate = Template(filename=d + infile + '.html')
    outfile = d + infile + '-out.html'
    f = open(outfile, 'w')
    f.write(mytemplate.render(today_date=today_date, bk=bk, logo_code=logo_code))
    f.close()
    webbrowser.open_new_tab(outfile)

if 1:
    today_date = datetime.date.today()
    d = "C:\Users\Fiona\Dropbox\python\petadmin\\"
    infile = 'Conf-mail'
    mytemplate = Template(filename=d + infile + '.html')
    body = mytemplate.render(today_date=today_date, bk=bk, logo_code=logo_code)
    to = 'crowbank.partners@gmail.com'
    subject = 'Crowbank Confirmation, booking #%d' % bk.no
    mi.send(to, body, subject)
