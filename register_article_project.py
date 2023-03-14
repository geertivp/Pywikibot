#!/usr/bin/python3

codedoc = """
Register an article as part of a project via its talk page.

For each page in the list a section is added to the article talk page.

Parameters:

    P1: mainlang code (default: LANGUAGE/LC_ALL/LANG)
    P2: wmproject (default: wikipedia)

    Hardcoded in the script: project reference text

    stdin:  List of pages, one per line

Examples:

    pwb register_article_project en wikipedia

Configuration:

    * Project section header and text

Author:

    Geert Van Pamel, 2023-03-10, MIT License, User:Geertivp

Prequisites:

    Install Pywikibot client software

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial
    https://www.gnu.org/software/gettext/manual/html_node/Locale-Environment-Variables.html

    https://en.wikipedia.org/wiki/Wikipedia:Namespace
    https://fr.wikipedia.org/wiki/Aide:Espace_de_noms
    https://nl.wikipedia.org/wiki/Help:Naamruimte

Source:

    https://github.com/geertivp/Pywikibot/blob/main/register_article_project.py

"""

import os               # Operating system: getenv
import pywikibot
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
from datetime import datetime	    # now, strftime, delta time, total_seconds

ENLANG = 'en'


def get_language_preferences():
    """
    Get the list of preferred languages,
    using environment variables LANG, LC_ALL, and LANGUAGE.
    Result:
        List of ISO 639-1 language codes
    """
    mainlang = os.getenv('LANGUAGE',
                         os.getenv('LC_ALL',
                         os.getenv('LANG', ENLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang] + ['nl', 'fr', 'en', 'de', 'es', 'it']
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)
    return main_languages


# Global technical parameters
modnm = 'Pywikibot register_article_project'    # Module name (using the Pywikibot package)
pgmid = '2023-03-14 (gvp)'	    # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]
wmproject = 'wikipedia'

# Should be configured
page_head = 'Page de projet'
page_head = 'Project page'
page_head = 'Projectartikel'

PAGEHEADRE = re.compile(r'(==\s*' + page_head + '\s*==)')        # Page headers with templates

project_page = """== """ + page_head + """ ==
Cet article a été rédigé dans le cadre du projet [[Projet:Femmes et sciences 2022 - Réjouisciences|]]. ~~~~"""

project_page = """== """ + page_head + """ ==
This article was amended as part of the [[Wikipedia:WikiProject African Archaeology|]] project. ~~~~"""

project_page = """== """ + page_head + """ ==
Dit artikel werd bijgewerkt in het kader van het [[Wikipedia:GLAM/KOERS museum Roeselare/Vlaamse kermiskoersen|Vlaamse kermiskoersen]] project. ~~~~"""

# Get program parameters
pgmnm = sys.argv.pop(0)

# Get language code
if sys.argv:
    mainlang = sys.argv.pop(0)

# Get Wikimedia family (project)
if sys.argv:
    wmproject = sys.argv.pop(0)

# Login to the Wikimedia account
site = pywikibot.Site(mainlang, wmproject)
site.login()    # Must login to get the logged in username
site_user = site.user()
account = pywikibot.User(site, site_user)

try:    # Old accounts do not have a registration date
    accregdt = account.registration().strftime('%Y-%m-%d')
except Exception:
    accregdt = ''

pywikibot.debug(pgmnm)
pywikibot.info('Project: {}'.format(site))
pywikibot.info('Account: {} {} {}'
               .format(site_user, account.editCount(), accregdt))
pywikibot.log(account.groups())
pywikibot.log(account.rights())
pywikibot.info(project_page)

donecnt = 0
pagecnt = 0
pageerr = 0
skipcnt = 0

inputfile = sys.stdin.read()
item_list = sorted(set(inputfile.split('\n')))

for pagename in item_list:
  if pagename > '/':
    try:
        page = pywikibot.Page(site, pagename)
        if page.isRedirectPage():
            page = page.getRedirectTarget()

        # Get Talk page
        namespace = page.namespace().id + 1
        talkpage = pywikibot.Page(site, page.title(), namespace)

        if not page.text:
            # Empty main page
            skipcnt += 1
        elif not talkpage.text:
            # New talk page
            talkpage.text = project_page
            talkpage.save('#pwb ' + page_head)
            pagecnt += 1
        elif PAGEHEADRE.search(talkpage.text):
            # Project page allready done
            donecnt += 1
        else:
            # Append project in talkpage
            talkpage.text += '\n\n' + project_page
            talkpage.save('#pwb ' + page_head)
            pagecnt += 1

    except Exception as error:
        pywikibot.error('Error processing {}, {}'.format(pagename, error))
        pageerr += 1

pywikibot.info('{:d} pages processed\n{:d} failed\n{:d} already done\n{:d} skipped'
               .format(pagecnt, pageerr, donecnt, skipcnt))
