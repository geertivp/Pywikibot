#!/usr/bin/python3

codedoc = """
Welcome a list of Wikimedia users by generating a user talk page

You can choose the mainlang, the wmproject and the welcome text.

For each user in the list a signed user talk page is created, if it does not already exist.

    The user account must exist on the local wmproject.
    Moderators and bots are skipped.
    User must have completed at least one edit.

Parameter:

    P1: mainlang code (default: LANG)
    P2: wmproject/platform (default: wikipedia)
    P3: welcome message (default depending on language and platform)

    stdin:  List of usernames, one per line

    -c  Add a talk section, even if the user has 0 contributions.


Options:

    pwb -user:geertivp welcome_user

Known problems:

    pwb -user:xxx does not work for all languages/platforms

Prequisites:

    Install Pywikibot client software

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial
    https://www.w3schools.com/python/ref_string_format.asp

Examples:

    pwb welcome_user
    pwb -user:geertivp welcome_user
    pwb -debug -user:geertivp welcome_user
    pwb -user:geertivp welcome_user wikidata
    pwb welcome_user commons commons '{{Welcome to Wiki Loves Pajottenland Zennevallei 2021}}'
    pwb welcome_user |awk -F "\t" '{print $1}'

Author:

    Geert Van Pamel, 2021-09-07, MIT License, User:Geertivp

"""

import os               # Operating system: getenv
import pdb              # Python debugger
import pywikibot
import sys		    	# System: argv, exit (get the parameters, terminate the program)

from datetime import datetime	    # now, strftime, delta time, total_seconds

# Global variables
modnm = 'Pywikibot welcome_user'    # Module name (using the Pywikibot package)
pgmid = '2025-02-24 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

ENLANG = 'en'
USERTALKNAMESPACE = 3
TEMPLATENAMESPACE = 10


def get_item_header(header):
    """
    Get the item header (label, description, alias, or dict element in user language)

    :param header: item labels, descriptions, or aliases, or any dict (dict)
    :return: label, description, or alias in the first available language (string, list)

    The language is in ISO code format.
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
            pywikibot.warning('Item {} ({}) redirects to {}'
                              .format(label, qnumber, item.getID()))
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
        pywikibot.warning('Item {} ({}) redirects to {}'
                          .format(label, qnumber, item.getID()))
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
                         os.getenv('LANG', ENLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang]

    # Cleanup language list
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)

    if ENLANG not in main_languages:
        main_languages.append(ENLANG)

    return main_languages


# Default values
# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]
wmproject = 'wikipedia'

# Get program parameters
pgmnm = sys.argv.pop(0)
#pdb.set_trace()

# Overrule zero page edit filter
force_create = False
if sys.argv and sys.argv[0] == '-c':
    sys.argv.pop(0)
    force_create = True

# Get language code
if sys.argv:
    mainlang = sys.argv.pop(0)
    if len(mainlang) > 3:
        wmproject = mainlang

# Get Wikimedia family (project)
if sys.argv:
    wmprojectparam = sys.argv.pop(0)
    if wmprojectparam != '-':
        wmproject = wmprojectparam

# Login to the Wikimedia account
site = pywikibot.Site(mainlang, wmproject)
site.login()
cbotflag = 'bot' in pywikibot.User(site, site.user()).groups()
site_user = site.user()
account = pywikibot.User(site, site_user)

# Get user account creation date
try:
    accregdt = account.registration().strftime('%Y-%m-%d')
except Exception:
    # Old accounts do not have a registration date
    accregdt = ''

# This script requires a bot flag
repo = site.data_repository()
repo.login()
wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

# Get default welcome message
wpwelcomemessage = {}
item = get_item_page('Q5611978')

try:
    sitelink = item.sitelinks[mainlang + 'wiki']
    if (sitelink.namespace == TEMPLATENAMESPACE
            and str(sitelink.site.family) == 'wikipedia'):
        wpwelcomemessage[mainlang] = '{{' + sitelink.title + '}} ~~~~'
except Exception as error:
    pywikibot.warning(error)

# Overrule welcome message
wpwelcomemessage['be'] = '{{welcome}} ~~~~'
wpwelcomemessage['commons'] = '{{welcome}} ~~~~'
wpwelcomemessage['en'] = '{{welcome-t}} ~~~~'
wpwelcomemessage['fr'] = '{{Bienvenue nouveau|' + site_user + '|sign=~~~~}}'
wpwelcomemessage['it'] = '{{subst:Benvenuto}} ~~~~'
wpwelcomemessage['nl'] = '{{welkom}} ~~~~'
wpwelcomemessage['test'] = '{{w}} ~~~~'
wpwelcomemessage['wikidata'] = '{{subst:welcome|~~~~}}'

# Get welcome text
if sys.argv:
    wpwelcomemessage[mainlang] = sys.argv.pop(0)

# Translate welcome message
try:
    welcomepage = wpwelcomemessage[mainlang]
except:
    pywikibot.error('Language {} is not implemented'.format(mainlang))
    sys.exit(1)

pywikibot.debug(pgmnm)
pywikibot.info('Project: {}'.format(site))
pywikibot.info('Account: {} {} {}'
               .format(site_user, account.editCount(), accregdt))
pywikibot.log('Account: {}\n{}'
               .format(account.groups(), account.rights()))
pywikibot.info('Welcome message: {}'.format(welcomepage))

donecnt = 0
skipcnt = 0
usercnt = 0
usererr = 0

# Get list of usernames
inputfile = sys.stdin.read()
item_list = sorted(set(inputfile.splitlines()))

# Process all users
for user in item_list:
  if user > '/':    # Skip comments
    try:
        wikiuser = pywikibot.User(site, user)
        wp = wikiuser.getprops()

        # Validate user account
        if ('userid' in wp
                and 'bot' not in wp['groups']
                and 'bot' not in wp['rights']
                and 'rollback' not in wp['rights']
                and (wikiuser.editCount() > 0 or force_create)):
            page = pywikibot.Page(site, user, USERTALKNAMESPACE)    # User talk page

            if page.text:
                # Should detect welcome message.
                # Because there are many different welcome messages, we skip updating.
                pywikibot.info('{}\thas {:d} edits'
                               .format(user, wikiuser.editCount()))
                donecnt += 1
            else:
                page.text = welcomepage
                page.save('Welcome')
                usercnt += 1
        else:
            pywikibot.warning('{}\tskipped with {:d} edits'
                              .format(user, wikiuser.editCount()))
            skipcnt += 1
    except Exception as error:
        pywikibot.error('Error processing {}, {}'.format(user, error))
        usererr += 1

pywikibot.info('{:d} users processed\n{:d} failed\n{:d} skipped\n{:d} already done'
               .format(usercnt, usererr, skipcnt, donecnt))
