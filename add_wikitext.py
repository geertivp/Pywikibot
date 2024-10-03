#!/usr/bin/python3

codedoc = """
Add wiki text to a list of pages, belonging to a category

You must provide the mainlang, the wmproject, the category, and the wiki text.

The wiki text is appended to each page in the category list.

    Empty pages stay empty
    The wiki text is only added once

This script is an alternative to using AWB, which can be error-prone (manual operations).

Parameters:

    P1: mainlang code
    P2: wmproject
    P3: Category providing the list of pages. The category tree is not recursed.

    stdin:  Wiki text to add

Author:

    Geert Van Pamel, 2024-10-03, MIT License, User:Geertivp

Prequisites:

    Install Pywikibot client software

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Examples:

    pwb add_wikitext commons commons Wiki_Loves_Denderland_2024

    [[Category:Images from Wiki Loves Heritage Belgium in 2024]]

Known problems:

    This script is used to circumvent problems with merging file lists in the Montage tool,
    see https://github.com/hatnote/montage/issues/234.
    Actually the Montage tool should allow to upload multiple categories at once.

    Montages does not support multiple categories:
    https://commons.wikimedia.org/wiki/Commons_talk:Montage#Montage_should_allow_to_upload_multiple_categories_at_once
    https://phabricator.wikimedia.org/T299167

"""

# List the required modules
import os               # Operating system: getenv
import pywikibot
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)

from datetime import datetime	    # now, strftime, delta time, total_seconds
from pywikibot import pagegenerators as pg # Wikidata Query interface

# Global variables
modnm = 'Pywikibot add_wikitext'    # Module name (using the Pywikibot package)
pgmid = '2024-10-03 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

MAINNAMESPACE = 0
FILENAMESPACE = 6

MINORUPDATE = True              # Non-content updates
RECURSE = False                 # For some campaigns recursion might be needed...
pageupdated = 'Page maintenance'

# Get program parameters
pgmnm = sys.argv.pop(0)

mainlang = sys.argv.pop(0)      # Get P1
wmproject = sys.argv.pop(0)     # Get P2
category = sys.argv.pop(0)      # Get P3

# Login to the Wikimedia account
site = pywikibot.Site(mainlang, wmproject)
site.login()                    # Must login; is this really necessary?
account = pywikibot.User(site, site.user())
botflag = 'bot' in pywikibot.User(site, site.user()).groups()

try:    # Old accounts do not have a registration date
    accregdt = account.registration().strftime('%Y-%m-%d')
except Exception:
    accregdt = ''

pywikibot.info('Site: {}'.format(site))
pywikibot.info('Account: {} {} {} {}'
               .format(site.user(), account.editCount(), accregdt, account.groups()))

wikitext = sys.stdin.read()
wikitext = re.sub(r' [ \t\r\f\v]+$', ' ', wikitext, flags=re.MULTILINE)

# Remove redundant empty lines
wikitext = re.sub(r'\n\n+', '\n\n', wikitext)

# Remove redundant spaces
# Merge spaces after dot
wikitext = re.sub(r'[.] +', '. ', wikitext)

# Prepaire regular expression
wikitextre = wikitext.replace('[', r'\[')[:-1]
##print(wikitextre)

# Prepare loop
cat = pywikibot.Category(site, category)
pywikibot.info('{}'.format(cat.categoryinfo))

pagecnt = 0
pageerr = 0

for page in pg.CategorizedPageGenerator(cat, recurse=RECURSE):
    pagenm = str(page)
    ##pywikibot.info('{}'.format(pagenm))
    try:
        ##print(page.namespace())
        if page.namespace().id not in {MAINNAMESPACE, FILENAMESPACE}:
            # Namespace(id=0, custom_name='', canonical_name='', aliases=[], case='first-letter', content=True, nonincludable=False, subpages=False)
            pywikibot.warning('Unsupported namespace: {}'.format(pagenm))
            pageerr += 1
        elif page.text:
            if re.search(wikitextre, page.text, flags=re.MULTILINE | re.IGNORECASE):
                pywikibot.warning('Page already updated: {}'.format(pagenm))
                pageerr += 1
            else:
                # Maybe the wiki text might be inserted/appended at a convenient place?
                page.text += '\n' + wikitext
                page.save(summary=pageupdated, minor=MINORUPDATE) ##, bot=True) ##, bot=botflag) ## got multiple values for keyword argument 'bot'
                pagecnt += 1
                ##print(page.text)
                ##sys.exit()  ###
        else:
            pywikibot.warning('Page empty: {}'.format(pagenm))
            pageerr += 1

    except Exception as error:
        pywikibot.error('Error accessing: {}, {}'.format(pagenm, error))
        pageerr += 1
        raise

pywikibot.info('{} pages processed\n{} failed or ignored'.format(pagecnt, pageerr))
