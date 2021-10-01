#!/usr/bin/python3

codedoc = """
Welcome a list of Wikimedia users by creating a user talk page.

You can choose the language, the project and the welcome text.

For each user in the list a signed user talk page is created, if it does not already exist.

    The user account must exist on the local project
    Moderators and bots are skipped
    User must have completed at least one edit

Parameter:

    P1: language code (default LANG)

    stdin:  List of usernames, one per line

Author:

    Geert Van Pamel, 2021-09-07, GNU General Public License v3.0, User:Geertivp

Prequisites:

    Install Pywikibot client software

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

"""

import os               # Operating system: getenv
import sys		    	# System: argv, exit (get the parameters, terminate the program)

import pywikibot
from datetime import datetime	# now, strftime, delta time, total_seconds

# Get program parameters
pgmnm = sys.argv.pop(0)
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
if len(sys.argv) > 0:
    mainlang = sys.argv.pop(0).lower()
wmproject = 'wikipedia'

# Login to the Wikimedia account
site = pywikibot.Site(mainlang, wmproject)
site.login()    # Must login to get the logged in username
account = pywikibot.User(site, site.user())

try:    # Old accounts do not have a registration date
    accregdt = account.registration().strftime('%Y-%m-%d')
except Exception:
    accregdt = ''
##    pass

print ('Account:', site.user(), account.editCount(), accregdt, account.groups())
print (site)

wpwelcomemessage = {'nl': '{{w}} ~~~~', 'fr': '{{Bienvenue nouveau|' + site.user() + '|sign=~~~~}}', 'test': '{{w}} ~~~~'}
welcomepage = wpwelcomemessage[mainlang]
print(welcomepage)

donecnt = 0
skipcnt = 0
usercnt = 0
usererr = 0

inputfile = sys.stdin.read()
itemlist = sorted(set(inputfile.split('\n')))

for user in itemlist:
  if user != '':
    try:
        wikiuser = pywikibot.User(site, user)
        wp = wikiuser.getprops()
        if 'userid' in wp and 'user' in wp['groups'] and 'bot' not in wp['groups'] and 'bot' not in wp['rights'] and 'rollback' not in wp['rights'] and wikiuser.editCount() > 0:
            page = pywikibot.Page(site,'User_talk:' + user)
            if page.text:
                print('User %s has %d edits' % (user, wikiuser.editCount()), file=sys.stderr)
                donecnt += 1
            else:
                page.text = welcomepage
                page.save('Welcome')
                usercnt += 1
        else:
            print('User %s skipped' % (user), file=sys.stderr)
            skipcnt += 1

    except Exception as error:
        print(format(error), file=sys.stderr)
        usererr += 1

print('%d users processed\n%d failed\n%d skipped\n%d done' % (usercnt, usererr, skipcnt, donecnt), file=sys.stderr)
