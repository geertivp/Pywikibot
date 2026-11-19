#!/usr/bin/python3

codedoc = """
Register a Wikipedia article as part of a project via its talk page.

For each page in the list a project section is added to the article talk page.

The Wikidata item number is shown, if available. This can then be used with copy_label to further amend Wikidata, Wikimedia Commons, and other Wikipedia pages.

Parameters:

    P1: mainlang code (default: LANGUAGE/LC_ALL/LANG)
    P2: wmproject (default: wikipedia)
    P3: Category (default: list of pages via stdin)
    P4: Location
    P5: Partner

    stdin: List of pages, one per line
        https URLs are accepted and stripped.
        Ignored when P3 category is present.

Qualifiers:

    -a: Include amended pages
    -c: Force created tag
    -n: Don't update talk page; no delays
    -t: Timer delta value (default: 30 = 2/minute)

Examples:

    pwb -user:geertivp register_article_project fr wikipedia

    pwb register_article_project -n nl wikipedia Overleden_Wikipedianen
    
    pwb register_article_project -t 0 nl wikipedia - Lokeren 'Stadsarchief Lokeren'

Configuration:

    Hardcoded in the script: (language specific)
        project section header
        project reference text

Tips:

    This script shows item numbers from Wikipedia pages

    Generate a Wikipedia page list via Wikidata Query:

        SELECT ?item ?article WHERE {
          ?item wdt:P6104 wd:Q113396871.
          ?article schema:about ?item;
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
from pywikibot import pagegenerators as pg

# Global technical parameters
modnm = 'Pywikibot register_article_project'    # Module name (using the Pywikibot package)
pgmid = '2026-03-11 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

MAINLANG = 'en:mul'     # mul can have non-Romain alphabeths; EN was tradional default value

# https://www.mediawiki.org/wiki/Help:Namespaces
MAINNAMESPACE = 0
PROJECTNAMESPACE = 4

# Languages that doesn't want Discussion project heads
veto_lang = {'en'}


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


def get_item_page(qnumber) -> pywikibot.ItemPage:
    """
    Get the item; handle redirects.
    """
    if isinstance(qnumber, str):
        item = pywikibot.ItemPage(repo, qnumber)
        try:
            item.get()
        except pywikibot.exceptions.IsRedirectPageError:
            # Resolve a single redirect error
            item = item.getRedirectTarget()
            label = get_item_header(item.labels)
            pywikibot.warning('Item {} ({}) redirects to {}'.format(
                              label, qnumber, item.getID()))
            ##pdb.set_trace()
            qnumber = item.getID()
        except Exception as error:
            pywikibot.error('{} ({}), {}'.format(item, qnumber, error))      # Site error
            item = None
    else:
        item = qnumber
        qnumber = item.getID()

    # Resolve redirect pages
    while item and item.isRedirectPage():
        ## Should fix the sitelinks
        item = item.getRedirectTarget()
        label = get_item_header(item.labels)
        pywikibot.warning('Item {} ({}) redirects to {}'.format(
                          label, qnumber, item.getID()))
        ##pdb.set_trace()
        qnumber = item.getID()

    return item


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


def get_url_pagename(subject) -> str:
    """
    Extract pagename from URL.
    """
    hashpos = subject.find('#')
    if hashpos > 0:
        subject = subject[:hashpos]

    amperpos = subject.find('&')
    if amperpos > 0:
        subject = subject[:amperpos]

    slashpos = subject.rfind('/')
    if slashpos > 0:
        subject = subject[slashpos + 1:]

    if subject.find('index.php?title=') == 0:
        subject = subject[16:]
    return subject.strip()


# Default values
include_amended = False
page_created = False
page_update = True
recurse_list = False
timer_delta = 30.0

# Get language list
main_languages = get_language_preferences()

QSUFFRE = re.compile(r'(Q[0-9]+)')      # Q-number

# Get program parameters
pgmnm = sys.argv.pop(0)

# Get command line qualifiers
while sys.argv and sys.argv[0][0] == '-':
    if sys.argv[0] == '-a':
        nularg = sys.argv.pop(0)
        include_amended = True
        pywikibot.info('Include amended pages')
    if sys.argv[0] == '-c':
        nularg = sys.argv.pop(0)
        page_created = True
        pywikibot.info('Forced creation tag for talk pages')
    elif sys.argv[0] == '-n':
        nularg = sys.argv.pop(0)
        page_update = False
        timer_delta = 0.0       # No update; no need for delay
        pywikibot.info("Don't amend talk pages")
    elif sys.argv[0] == '-t':
        nularg = sys.argv.pop(0)
        timer_delta = int(sys.argv.pop(0))  # Convert string to number

# Get language code
mainlang = main_languages[0]
if sys.argv:
    mainlang = sys.argv.pop(0)

    if mainlang in veto_lang:
        pywikibot.error("Language '{}' not allowed".format(mainlang))
        sys.exit(20)
    elif len(mainlang) > 3:
        # Wikidata, Commons
        wmproject = mainlang

# Get Wikimedia family (project)
wmproject = 'wikipedia'
if sys.argv:
    wmproject = sys.argv.pop(0)

# Get language labels; please add all languages that are to be supported
try:
    amended_label = {
        'el': 'τροποποιημένο',
        'en': 'amended',
        'es': 'modificado',
        'fr': 'modifié',
        'nl': 'bijgewerkt',
    }[mainlang]

    created_label = {
        'el': 'δημιουργήθηκε',
        'en': 'created',
        'es': 'creado',
        'fr': 'créee',
        'nl': 'aangemaakt',
    }[mainlang]

    moderator_tags = {
        'el': r'{{Πρόταση διαγραφής',
        'en': r'{{Article for deletion',
        'es': r'{{Aviso ',
        'fr': r'{{Admissibilité',
        'nl': r'{{ne\||{{Meebezig|{{Wikicursus|{{Nuweg',
    }[mainlang]

    # Page section headers
    page_head = {
        'el': 'Σελίδα έργου',
        'en': 'Project page',
        'es': 'Página del proyecto',
        'fr': 'Page de projet',
        'nl': 'Projectartikel',
    }[mainlang]

except Exception as error:
    # Language probably not configered
    pywikibot.critical('Language {} not configured, {}'.format(mainlang, error))
    sys.exit(1)

page_text = 'Cet article fait partie du projet [[Wikipédia:Wikiproject/Amazone gender mainstreaming|Amazone gender mainstreaming]] en collaboration avec [[Wikimédia Belgique]].'
page_text = 'This article was {} as part of the [[nl:Wikipedia:Wikiproject/Erfgoed/Vlaanderen/Guido Gezellearchief/Vrouwen van papier|Vrouwen van papier]] project of the [[nl:Archief Guido Gezelle|Guido Gezellearchief]] in collaboration with [[nl:meemoo|meemoo]] and [[nl:Wikimedia Belgium|Wikimedia Belgium]].'
page_text = 'Dit artikel werd bijgewerkt in het kader van het project [[Wikipedia:Wikiproject/Erfgoed/Vlaanderen/Midwest/Erfgoedlijnen Roeselare|Erfgoedlijnen Roeselare]] van het Erfgoedcel TERF/BIE Midwest en Stadsarchief Roeselare in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd bijgewerkt in het kader van het project [[Wikipedia:GLAM/Fotomuseum Antwerpen/Gevaert-papierproject|Gevaert-fotopapierproject]] van het [[Fotomuseum Antwerpen]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd bijgewerkt in het kader van het project [[Wikipedia:Wikiproject/Cultuur/Vlaanderen/Iedereen Leest|Iedereen Leest]] van [[Iedereen Leest]] in samenwerking met [[meemoo]] en [[Wikimedia België]].'
page_text = 'Dit artikel werd bijgewerkt in het kader van het project [[Wikipedia:Wikiproject/Erfgoed/Vlaanderen/Beveren/Bibliotheek|Bibliotheek Beveren]] van [[Avansa]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd bijgewerkt in het kader van het project [[Wikipedia:Educatieprogramma/Vlaams Architectuurinstituut/Cementovens|Cementovens in België]] van de [[Universiteit Gent|faculteit ingenieurs Architect UGent]] in samenwerking met het [[Vlaams Architectuurinstituut]] en [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van het project [[m:Event:Wikimedia Belgium/Muntuit/Gemeenschapsmunten|Gemeenschapsmunten]] op initiatief van [[Muntuit]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van het [[m:Event:Wikimedia Belgium/Amazone/International girls in ICT day/2024-04-25/nl|Internationale meisjes in ICT dag]] van [[Amazone vzw]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van het project [[Wikipedia:GLAM/Industriemuseum Gent/Wiki Café/Belgische metaalindustrie|Belgische metaalindustrie]] van het [[ Industriemuseum]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van het project [[Wikipedia:Wikiproject/Erfgoed/Vlaanderen/Guido Gezellearchief/Vrouwen van papier|Vrouwen van papier]] van het [[Guido Gezellearchief]] in samenwerking met [[meemoo]] en [[Wikimedia België]].'
page_text = 'Dit artikel werd bijgewerkt in het kader van het project [[Wikipedia:Educatieprogramma/Universiteit Gent/Vakgroep Geschiedenis/Historische praktijk I middeleeuwen|Middeleeuwse geschiedenis]] van de [[Universiteit Gent|UGent]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} op een schrijfsessie van [[Wikipedia:Wikiproject/België/Internationale Vrouwendag/2025/Antwerpen|Internationale Vrouwendag 2025]] in het [[Museum Plantin-Moretus|Plantin-Moretus Museum]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} op een schrijfsessie van [[Wikipedia:Wikiproject/België/Internationale Vrouwendag/2025/Leuven|Internationale Vrouwendag 2025]] in het [[KADOC]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} op een schrijfsessie van [[Wikipedia:Wikiproject/België/Internationale Vrouwendag/2025/Sint-Niklaas|Internationale Vrouwendag 2025]] in het [[Stadhuis van Sint-Niklaas]] in samenwerking met [[Wikimedia België]].'
page_text = 'This article was {} at the [[m:Event:Planetary Science Wiki Edit-a-thon/2025|Planetary Science Wiki Edit-a-thon]] at the [[Royal Belgian Institute for Space Aeronomy]] in collaboration with [[Wikimedia Belgium]].'
page_text = 'Αυτό το άρθρο {} στο [[m:Event:Planetary Science Wiki Edit-a-thon/2025|Planetary Science Wiki Edit-a-thon]] στο [[Royal Belgian Institute for Space Aeronomy]] σε συνεργασία με τα [[Wikimedia Belgium]].'
page_text = 'Este artículo fue creado en el [[m:Event:Planetary Science Wiki Edit-a-thon/2025|Planetary Science Wiki Edit-a-thon]] en el [[Royal Belgian Institute for Space Aeronomy]] en colaboración con [[Wikimedia Bélgica]].'
page_text = "Cet article a été {} lors du [[m:Event:Planetary Science Wiki Edit-a-thon/2025|Planetary Science Wikithon]] à l'[[Institut royal d'Aéronomie spatiale de Belgique]] en collaboration avec [[Wikimédia Belgique]]."
page_text = 'Dit artikel werd {} tijdens een [[m:Event:Planetary Science Wiki Edit-a-thon/2025|Planetary Science schrijfsessie]] bij het [[Koninklijk Belgisch Instituut voor Ruimte-Aeronomie]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van de [[Wikipedia:Wikiproject/Belgische podiumkunsten/Dans/2025-02-26|schrijfsessie Body of Work]] van het [[STUK (kunstencentrum)|STUK]] in samenwerking met [[Wikimedia België]].'
page_text = 'This article was {} in the context of the [[:nl:Wikipedia:Wikiproject/Belgische podiumkunsten/Dans/2025-02-26|edit-a-thon Body of Work]] with [[:nl:STUK (kunstencentrum)|STUK]] in collaboration with [[:nl:Wikimedia België]].'
page_text = 'Cet article a été {}  pour un [[:nl:Wikipedia:Wikiproject/Belgische podiumkunsten/Dans/2025-02-26|Wikiton Body of Work]] avec [[:nl:STUK (kunstencentrum)|STUK]] en collaboration avec [[Wikimédia Belgique]].'
page_text = 'Dit artikel werd {} op een schrijfsessie van [[Wikipedia:Wikiproject/België/Internationale Vrouwendag/2025/Gent meemoo|Internationale Vrouwendag 2025]] in het [[meemoo]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} op een schrijfsessie van [[Wikipedia:Wikiproject/België/Internationale Vrouwendag/2025/Gent Industriemuseum|Internationale Vrouwendag 2025]] in het [[Industriemuseum]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} op een schrijfsessie van [[Wikipedia:Wikiproject/België/Internationale Vrouwendag/2025/Brugge|Internationale Vrouwendag 2025]] in de [[Bibliotheek Brugge]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} tijdens een schrijfsessie van [[m:Event:Wikimedia Belgium/Amazone/International girls in ICT day/2025-04-24|International girls in ICT day]] van [[Amazone vzw]] in samenwerking met [[Wikimedia België]].'
page_text = "Cet article a été {} lors d'une session de rédaction de [[m:Event:Wikimedia Belgium/Amazone/International girls in ICT day/2025-04-24|International girls in ICT day]] par [[Amazone asbl]] en collaboration avec [[Wikimedia Belgique]]."
page_text = 'Dit artikel werd {} in het kader van het project [[Wikipedia:Wikiproject/Jeneverstokerijen in België|Jeneverstokerijen in België]] van het [[Jenevermuseum (Hasselt)|Jenevermuseum]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van een [[Wikipedia:GLAM/Yper Museum/Ieperse Kunstenaars|schrijfsessie]] van het [[Yper Museum]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van het [[Wikipedia:Educatieprogramma/Erasmushogeschool Brussel/2025-03-03|Educatieprogramma]] van de [[Erasmushogeschool Brussel]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van een [[Event:Erfgoed/Denderland/Schrijfsessies/2025-11-29|schrijfsessie over brouwerijen en volkscafés]] van Erfgoedcel Denderland in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van een [[Event:GLAM/Huis van Alijn/Wiki Café/Circus|schrijfsessie over circussen en circusartiesten]] van het [[Huis van Alijn]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van een [[Event:Wikithon Smells Like Circus|schrijfsessie]] van het [[Circuscentrum]] in het [[Wintercircus (Gent)|Wintercircus Gent]] in samenwerking met [[Huis van Alijn]] en [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van [[Event:GLAM/Industriemuseum Gent/Wiki Café/Bakeliet|Bakeliet]], een project van het [[Industriemuseum]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van een [[Event:GLAM/Literair Gent|schrijfsessie]] van [[Literair Gent]] in het [[Stadsmuseum Gent]] in samenwerking met [[Wikimedia België]].'
page_text = 'Dit artikel werd {} in het kader van [[Event:België/Internationale Vrouwendag/2026/{}|Internationale vrouwendag 2026]], een project van [[{}]], [[FARO]], [[meemoo]] en [[Wikimedia België]].'


project_page = '== ' + page_head + ' ==\n' + page_text + ' ~~~~'

# Page headers with templates
PAGEHEADRE = re.compile(r'(==\s*' + page_head + '\s*==)')
MODERATORTAGS = re.compile(moderator_tags, flags=re.IGNORECASE)
sitelang = mainlang + 'wiki'

try:
    # Login to the Wikimedia account
    site = pywikibot.Site(mainlang, wmproject)
    site.login()
    site_user = site.user()
    account = pywikibot.User(site, site_user)
    wmbotflag = 'bot' in account.groups()

    repo = site.data_repository()
    repo.login()
    wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()
except Exception as error:
    # Other exception to be used
    fatal_error(20, 'Wikimedia error, {}'.format(error))
    
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

# Show template update message
if page_update:
    pywikibot.info(project_page)

donecnt = 0
pagecnt = 0
pageerr = 0
skipcnt = 0
wderrcnt = 0

page_list = set()
new_page = set()
if sys.argv and sys.argv[0] != '-':
    # Get Wikimedia Commons page list from category (P1)
    subject = get_url_pagename(sys.argv.pop(0))

    # Get media file list from category
    try:
        cat_list = pywikibot.Category(site, subject)
        pywikibot.info(cat_list.title())
        pywikibot.info(cat_list.categoryinfo)
        # https://www.mediawiki.org/wiki/Manual:Pywikibot/Cookbook/Page_generators
        # https://www.mediawiki.org/wiki/Manual:Pywikibot/pagegenerators.py
        # https://doc.wikimedia.org/pywikibot/stable/api_ref/pywikibot.pagegenerators.html
        page_list = pg.CategorizedPageGenerator(cat_list, recurse=recurse_list)
        # Page generator does no longer support len() function ??
        page_list = set(page_list)      ### Is CategorizedPageGenerator returning unique pages?
    except Exception as error:
        pywikibot.critical(error)
        sys.exit(2)
else:
    # Ignore redundant parameter
    if sys.argv:
        nularg = sys.argv.pop(0)

    # Get list of pages from stdin
    inputfile = sys.stdin.read()
    input_list = sorted(set(inputfile.splitlines()))
    for subject in input_list:
        try:
            subject = get_url_pagename(subject)
            item_numbers = QSUFFRE.findall(subject)
            if not subject:
                pass
            elif item_numbers:
                for qnumber in item_numbers:
                    item = get_item_page(qnumber)
                    sitelink = item.sitelinks[sitelang]
                    page = pywikibot.Page(sitelink.site, sitelink.title, sitelink.namespace)
                    page_list.add(page)
            elif subject == '-' or subject[:9] == 'wikidata:':
                # Ignore wikidata items
                pass
            else:
                # Remove redundant language prefix (Campaign dashboard)
                len_lang = len(mainlang) + 1
                if subject[:len_lang] == mainlang + ':':
                    subject = subject[len_lang:]

                if subject[-7:] == '(nieuw)':
                    # Get page status (Campaign dashboard)
                    subject = subject[:-8]
                    new_page.add(subject)

                page = pywikibot.Page(site, subject)
                if page.text:
                    page_list.add(page)
        except Exception as error:
            pywikibot.error('{}, {}'.format(subject, error))
        except KeyboardInterrupt:
            sys.exit(130)

# Get location
#pdb.set_trace()
if sys.argv:
    location = sys.argv.pop(0)

# Get partner institution
if sys.argv:
    partner = sys.argv.pop(0)

# Unused parameters/qualifiers
while sys.argv:
    inpar = sys.argv.pop(0)
    pywikibot.warning('Redundant parameter or qualifier {}'.format(inpar))

pywikibot.info('{:d} media files in list'.format(len(page_list)))

# Start the main transaction timer
now = datetime.now() + timedelta(seconds=-timer_delta)

#pdb.set_trace()
result_list = []
for page in page_list:  # Not sorted
    try:
        # Get the primary sitelink
        pagename = page.title()
        while page.isRedirectPage():
            page = page.getRedirectTarget()
            pagename = page.title()

        # Get the article last revision
        for rev in page.revisions(total = 1):
            pass
        revision_info = 'Amended by {} on {:.10}'.format(rev.user, str(rev['timestamp']))

        # Get Talk page (odd number)
        namespace = page.namespace().id
        if namespace % 2:
            pywikibot.error('Ignore namespace {:d}: {}:{}'
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
                # Get lemma name
                lemma = lemma.split(':', 1)[1]
            talkpage = pywikibot.Page(site, lemma, namespace + 1)

            if MODERATORTAGS.search(page.text):
                # Attention needed
                pywikibot.warning('Moderator tag found in {}'.format(pagename))

            # Update or create talk page
            page_modified = False
            amend = amended_label
            if page_created or pagename in new_page:
                amend = created_label

            project_text = project_page.format(amend, location, partner)
            if pagename not in new_page and not include_amended:
                pass
            elif not talkpage.text:
                # New talk page
                talkpage.text = project_text
                page_modified = True
            elif PAGEHEADRE.search(talkpage.text):
                # Could trigger a null-edit when "touching"
                # Project page allready done
                pywikibot.info('Page {} already done'.format(pagename))
                donecnt += 1
            else:
                # Append project in talkpage
                pywikibot.warning('Page {} has already text'.format(talkpage.title()))
                talkpage.text += '\n\n' + project_text
                page_modified = True

            if namespace in [MAINNAMESPACE, PROJECTNAMESPACE]:
                # Get Wikidata item for Wikimedia page
                try:
                    # Show Wikidata label and item number (this could be input for another script)
                    # Not required to be logged in for read access
                    item = pywikibot.ItemPage.fromPage(page)
                    qnumber = item.title()
                    page_label = get_item_header(item.labels)
                    result_list.append((page_label, qnumber, revision_info))
                except Exception as error:
                    # No wikidata item number assigned
                    pywikibot.error('Error processing {}, {}'.format(pagename, error))
                    wderrcnt += 1

            if page_modified and page_update:
                # Save a Wikipedia page (max 1/min for non-bot accounts)
                # A non-bot account should limit its speed to 1 transaction per minute
                # We could possibly overrule with another timer value
                timer = timer_delta - (datetime.now() - now).total_seconds()
                if not wmbotflag and timer > 0.0:
                    time.sleep(timer)

                # Remove trailing spaces
                talkpage.text = re.sub(r'[ \t\r\f\v]+$', '', talkpage.text, flags=re.MULTILINE)
                talkpage.save('#pwb ' + page_head)
                pagecnt += 1

                # Restart the main transaction timer
                now = datetime.now()

    except Exception as error:
        pywikibot.error('Error processing {}, {}'.format(pagename, error))
        pageerr += 1

for row in result_list:
    pywikibot.info('{}\t[[d:{}]]\t{}'.format(row[0], row[1], row[2]))

pywikibot.info('{:d} pages processed\n{:d} failed\n{:d} Wikidata item missing\n{:d} already done\n{:d} skipped'
               .format(pagecnt, pageerr, wderrcnt, donecnt, skipcnt))
