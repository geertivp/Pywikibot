#!/usr/bin/python3

codedoc = """
Send a message to Wikimedia users by appending it to their user talk page.

You can choose the language, the project and the message text.

For each user in the list, a message is delivered to their user talk page.

Constraints:

    The user account must exist on the local project.

Parameters:

    P1: language code (default: LANG)
    P2: project (default: wikipedia)

    stdin: List of usernames, one per line

Author:

    Geert Van Pamel, 2022-02-12, GNU General Public License v3.0, User:Geertivp

Prequisites:

    Install Pywikibot client software

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Examples:

    ./deliver_message.py commons commons

Usage:

    This is ideal to deliver a mass-communication via the talk page.

"""

import os               # Operating system: getenv
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import pywikibot
from datetime import datetime	# now, strftime, delta time, total_seconds

messagetitle = 'Wiki Loves Heritage Belgium 2021'
usermessage = """

== Wiki Loves Heritage Belgium 2021 ==
Beste vriend van Wikimedia België, U hebt meegedaan met de fotowedstrijd. Gelieve [[wmbe:Wiki_Loves_Heritage/2021/Report|het juryrapport]] te lezen. Helaas hebt u niet gewonnen. Toch hartelijk dank voor uw bijdrage; vanaf 1 juli kan u opnieuw deelnemen.

Cher ami de Wikimedia Belgique, Vous avez participé au concours photo. Veuillez lire [[wmbe:Wiki_Loves_Heritage/2021/Rapport|le rapport du jury]]. Malheureusement, vous n'avez pas gagné. Cependant, merci beaucoup pour votre contribution; vous pourriez participer à nouveau à partir du 1er juillet.

Dear friend of Wikimedia Belgium, You have participated in the photo contest. Please read [[wmbe:Wiki_Loves_Heritage/2021/Report|the jury report]]. Unfortunately you did not win. However, thank you very much for your contribution; you can participate again from July 1st.
~~~~
"""

# Get program parameters
pgmnm = sys.argv.pop(0)
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
wmproject = 'wikipedia'

if len(sys.argv) > 0:
    mainlang = sys.argv.pop(0)

if len(sys.argv) > 0:
    wmproject = sys.argv.pop(0)

# Login to the Wikimedia account
site = pywikibot.Site(mainlang, wmproject)
site.login()    # Must login to get the logged in username
account = pywikibot.User(site, site.user())

try:    # Old accounts do not have a registration date
    accregdt = account.registration().strftime('%Y-%m-%d')
except Exception:
    accregdt = ''

print('Account:', site.user(), account.editCount(), accregdt, account.groups(), file=sys.stderr)
print(site, file=sys.stderr)
print(usermessage, file=sys.stderr)

skipcnt = 0
usercnt = 0
usererr = 0

inputfile = sys.stdin.read()
itemlist = sorted(set(inputfile.split('\n')))

for user in itemlist:
  if user > '/':
    try:
        wikiuser = pywikibot.User(site, user)
        wp = wikiuser.getprops()
        if 'userid' in wp:
            page = pywikibot.Page(site,'User_talk:' + user)
            page.text += usermessage
            page.save(messagetitle)
            usercnt += 1
        else:
            print('User %s does not exist' % (user), file=sys.stderr)
            skipcnt += 1

    except Exception as error:
        print(format(error), file=sys.stderr)
        usererr += 1

print('%d users processed\n%d failed\n%d skipped' % (usercnt, usererr, skipcnt), file=sys.stderr)

# Einde van de miserie