#!/usr/bin/python3

codedoc = """
Send an e-mail to a list of Wikimedia users.

Parameters:

    In the script:
    
        mail subject
        body text
        
    stdin: list of user names

    You can choose the project to connect to.

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial
    You need noratelimit right.

Author: Geert Van Pamel, 2020-01-22, GNU General Public License v3.0, User:Geertivp
"""

import sys		    	        # System: argv, exit (get the parameters, terminate the program)
import pywikibot
from datetime import datetime	# now, strftime, delta time, total_seconds

inputfile = sys.stdin.read()
mailto = sorted(set(inputfile.split('\n')))

mailsubject = 'Wiki Loves Heritage Belgium 2020'
mailbody = """Je hebt deelgenomen aan de fotowedstrijd "Wiki Loves Heritage Belgium", waarvoor heel hartelijk dank.
Je hebt helaas geen prijs gewonnen, maar deelnemen is belangrijker dan winnen, nietwaar?
Gelieve hieronder het juryrapport te vinden.

Vous avez participé au concours photo "Wiki Loves Heritage Belgium", pour lequel nous vous remercions vivement.
Malheureusement, vous n'avez pas gagné de prix, mais participer est plus important que gagner, n'est-ce pas ?
Vous trouverez ci-dessous le rapport du jury.

You participated in the photo contest "Wiki Loves Heritage Belgium", for which we thank you very much.
Unfortunately, you did not win a prize, but participating is more important than winning, isn't it?
Please find the jury report below.

* https://be.wikimedia.org/wiki/Wiki_Loves_Heritage/2020/Report

-- Geert Van Pamel, Wikimedia Belgium
"""

# Login to Wikimedia account
site = pywikibot.Site('be', 'wikimedia')
site.login()    # Must login to send email
account = pywikibot.User(site, site.user())

try:    # Old accounts do not have a registration date
    accregdt = account.registration().strftime('%Y-%m-%d')
except Exception:
    accregdt = ''

print ('Account:', site.user(), account.editCount(), accregdt, account.groups())

mailcnt = 0
mailerr = 0

for user in mailto:
  if user != '':
    try:
        wikiuser = pywikibot.User(site, user)
        gender = wikiuser.gender()
        mailstat = wikiuser.send_email(subject=mailsubject, text=mailbody)
        now = datetime.now()	# Start the main transaction timer
        isotime = now.strftime('%Y-%m-%d %H:%M:%S') # Only needed to format output
        print('%s\t%s\t%s\t%d' % (isotime, user, wikiuser.editCount(), gender))
        mailcnt += 1
#       time.sleep(10)
    except Exception as error:
        print('Error sending to %s,' % (user), format(error))
        mailerr += 1

print('%d mails sent\n%d failed' % (mailcnt, mailerr))
