#!/usr/bin/python3

codedoc = """
Register a Wikipedia article as part of a project via its talk page.

For each page in the list a project section is added to the article talk page.

Parameters:

    P1: mainlang code (default: LANGUAGE/LC_ALL/LANG)
    P2: wmproject (default: wikipedia)

    Hardcoded in the script: (language specific)
        section header
        project reference text

    stdin: List of pages, one per line
        https URLs are accepted and stripped.

Qualifiers:

    -c: Force update
    -n: Don't update talk page
    -t: Timer delta value (default: 60 = 1/minute)

Examples:

    pwb -user:geertivp register_article_project en wikipedia

Configuration:

    # Project section header and text

Tips:

    This script gets item numbers from Wikipedia pages

    Generate a Wikipedia page list via Wikidata.

        SELECT ?item ?article WHERE {
          ?item wdt:P6104 wd:Q113396871.
          ?article schema:about ?item;
            schema:inLanguage "nl";
            schema:isPartOf <https://nl.wikipedia.org/>.
        }

    Add a Wiki project to a list of item numbers: pwb add_statement

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

Author:

    Geert Van Pamel, 2023-03-10, MIT License, User:Geertivp

"""

import os               # Operating system: getenv
import pdb              # Python debugger
import pywikibot
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep

from datetime import datetime	    # now, strftime, delta time, total_seconds
from datetime import timedelta

# Global technical parameters
modnm = 'Pywikibot register_article_project'    # Module name (using the Pywikibot package)
pgmid = '2025-04-09 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

MAINLANG = 'en:mul'     # mul can have non-Romain alphabeths; EN was tradional default value


def get_item_header(header):
    """
    Get the item header (label, description, alias in user language)

    :param header: item label, description, or alias language list (string or list)
    :return: label, description, or alias in the first available language (string)
    """

    if not header:
        return '-'
    else:
        # Return preferred label
        for lang in main_languages:
            if lang in header:
                return header[lang]

        # Return any other label
        for lang in header:
            return header[lang]
    return '-'


def get_language_preferences() -> []:
    """
    Get the list of preferred languages,
    using environment variables LANG, LC_ALL, and LANGUAGE.
    'en' is always appended.

    Format: string delimited by ':'.
    Main_sublange code,

    Result:

        List of ISO 639-1 language codes
    Documentation:

        https://www.gnu.org/software/gettext/manual/html_node/Locale-Environment-Variables.html
        https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    """
    mainlang = os.getenv('LANGUAGE',
                         os.getenv('LC_ALL',
                         os.getenv('LANG', MAINLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang]

    # Cleanup language list
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)

    for lang in MAINLANG.split(':'):
        if lang not in main_languages:
            main_languages.append(lang)

    return main_languages


# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]
wmproject = 'wikipedia'

# Get program parameters
pgmnm = sys.argv.pop(0)

# Default values
page_created = False
page_update = True
timer_delta = 60.0

# Get command line qualifiers
while sys.argv and sys.argv[0][0] == '-':
    if sys.argv[0] == '-c':
        sys.argv.pop(0)
        page_created = True
    elif sys.argv[0] == '-n':
        sys.argv.pop(0)
        page_update = False
    elif sys.argv[0] == '-t':
        sys.argv.pop(0)
        timer_delta = int(sys.argv.pop(0))

# Get language code
if sys.argv:
    mainlang = sys.argv.pop(0)

    if len(mainlang) > 3:
        # Wikidata, Commons
        wmproject = mainlang

# Get Wikimedia family (project)
if sys.argv:
    wmproject = sys.argv.pop(0)

# Get language labels
try:
    amended_label = {
        'el': 'τροποποιημένο',
        'en': 'amended',
        'es': 'modificado',
        'fr': 'modifié',
        'nl': 'bijgewerkt',
    }

    amended_label = amended_label[mainlang]

    created_label = {
        'el': 'δημιουργήθηκε',
        'en': 'created',
        'es': 'creado',
        'fr': 'créee',
        'nl': 'aangemaakt',
    }

    created_label = created_label[mainlang]

    moderator_tags = {
        ## Do we need ^ ??
        'el': r'^{{Πρόταση διαγραφής',
        'en': r'^{{Article for deletion',
        'es': r'^{{Aviso ',
        'fr': r'^{{Admissibilité',
        'nl': r'^{{ne\||^{{Meebezig}}|^{{Wikicursus}}',
    }

    moderator_tags = moderator_tags[mainlang]

    # Page section headers
    page_head = {
        'el': 'Σελίδα έργου',
        'en': 'Project page',
        'es': 'Página del proyecto',
        'fr': 'Page de projet',
        'nl': 'Projectartikel',
    }

    page_head = page_head[mainlang]

except Exception as error:
    # Language probably not configered
    pywikibot.critical('Language {} not configured, {}'.format(mainlang, error))
    sys.exit(1)

page_text = 'Dit artikel werd {} op een schrijfsessie van [[Wikipedia:Wikiproject/België/Internationale Vrouwendag/2025/Gent Industriemuseum|Internationale Vrouwendag 2025]] in het [[Industriemuseum]] in samenwerking met [[Wikimedia België]].'

project_page = '== ' + page_head + ' ==\n' + page_text + ' ~~~~'

# Page headers with templates
PAGEHEADRE = re.compile(r'(==\s*' + page_head + '\s*==)')
MODERATORTAGS = re.compile(moderator_tags, flags=re.IGNORECASE);

# Login to the Wikimedia account
site = pywikibot.Site(mainlang, wmproject)
site.login()
site_user = site.user()
account = pywikibot.User(site, site_user)
wmbotflag = 'bot' in account.groups()

try:    # Old accounts do not have a registration date
    accregdt = account.registration().strftime('%Y-%m-%d')
except Exception:
    accregdt = ''

pywikibot.debug(pgmnm)
pywikibot.log(account.groups())
pywikibot.log(account.rights())
pywikibot.info('{}, {}, {}, {}'.format(modnm, pgmid, pgmlic, creator))
pywikibot.info('Project: {}'.format(site))
pywikibot.info('Account: {} {} {}\n'
               .format(site_user, account.editCount(), accregdt))
pywikibot.info(project_page)

donecnt = 0
pagecnt = 0
pageerr = 0
skipcnt = 0

# Get all pages
inputfile = sys.stdin.read()
item_list = sorted(set(inputfile.splitlines()))

# Start the main transaction timer
now = datetime.now() + timedelta(seconds=-timer_delta)

for pagename in item_list:
  if pagename > '/':
    try:
        # Remove URL
        pagename = re.sub('.*\.org/wiki/', '', pagename)

        # Remove redundant language prefix (Campaign dashboard)
        len_lang = len(mainlang + ':')
        if pagename[:len_lang] == mainlang + ':':
            pagename = pagename[len_lang:]

        # Get page status (Campaign dashboard)
        amend = amended_label
        if page_created:
            amend = created_label
        elif pagename[-7:] == '(nieuw)':
            pagename = pagename[:-8]
            amend = created_label

        # Get the primary sitelink
        page = pywikibot.Page(site, pagename)
        while page.isRedirectPage():
            page = page.getRedirectTarget()
            pagename = page.title()

        # Get Talk page (odd number)
        namespace = page.namespace().id
        if namespace % 2:
            pywikibot.error('Bad namespace {:d}: {}:{}'
                            .format(namespace, site.namespace(namespace), pagename))
            pageerr += 1
        elif not page.text:
            # Empty page's should not have a talk page
            pywikibot.warning('Page {} not found'.format(pagename))
            skipcnt += 1
        else:
            # Get lemma talk page
            lemma = pagename
            if namespace > 0:
                lemma = lemma.split(':', 1)[1]
            talkpage = pywikibot.Page(site, lemma, namespace + 1)

            if MODERATORTAGS.search(page.text):
                # Attention needed
                pywikibot.warning('Moderator tag found in {}'.format(pagename))

            # Page changed by script?
            page_modified = True
            if not talkpage.text:
                # New talk page
                talkpage.text = project_page.format(amend)
            elif PAGEHEADRE.search(talkpage.text):
                # Could trigger a null-edit
                page_modified = False
                # Project page allready done
                pywikibot.info('Page {} done'.format(pagename))
                donecnt += 1
            else:
                # Append project in talkpage
                pywikibot.warning('Page {} has already text'.format(talkpage.title()))
                talkpage.text += '\n\n' + project_page.format(amend)

            if page_modified and page_update:
                # Save a Wikipedia page (max 1/min for non-bot accounts)
                # A non-bot account should limit its speed to 1 transaction per minute
                # We could possibly overrule with another timer value
                timer = timer_delta - (datetime.now() - now).total_seconds()
                if not wmbotflag and timer > 0.0:
                    time.sleep(timer)

                # Remove trailing spaces
                talkpage.text = re.sub(r'[ \t\r\f\v]+$', '', talkpage.text, flags=re.MULTILINE)
                pagecnt += 1
                talkpage.save('#pwb ' + page_head)

                # Restart the main transaction timer
                now = datetime.now()

            if namespace == 0:
                try:
                    # Get Wikidata item for Wikipedia page
                    # Show Wikidata label and item number (this could be input for another script)
                    item = pywikibot.ItemPage.fromPage(page)
                    qnumber = item.title()
                    page_label = get_item_header(item.labels)
                    pywikibot.info('Wikidata item: {} ({})'.format(page_label, qnumber))

                except Exception as error:
                    # No wikidata item number assigned
                    pywikibot.error('Error processing {}, {}'.format(pagename, error))
                    pageerr += 1

    except Exception as error:
        pywikibot.error('Error processing {}, {}'.format(pagename, error))
        pageerr += 1

pywikibot.info('{:d} pages processed\n{:d} failed\n{:d} already done\n{:d} skipped'
               .format(pagecnt, pageerr, donecnt, skipcnt))
