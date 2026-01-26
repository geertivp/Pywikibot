#!/usr/bin/python3

codedoc = """
Welcome a list of Wikimedia users by generating or amending a user talk page

You can choose the mainlang, the wmproject and the welcome text.

For each user in the list a signed user talk page is created, if it does not already exist.

    The user account must exist on the local wmproject.
    Moderators and bots are skipped.
    The user must have completed at least one edit.

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
pgmid = '2026-01-25 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

ENLANG = 'en'
USERTALKNAMESPACE = 3
TEMPLATENAMESPACE = 10

veto_lang = {'en'}


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

# Overrule zero page edit filter
force_create = False

while sys.argv and sys.argv[0][0] == '-':
    if sys.argv[0] == '-c':
        sys.argv.pop(0)
        force_create = True
    else:
        pywikibot.error('Non-recognised qualifier {}'.format(sys.argv.pop(0)))

# Get language or project code
if sys.argv:
    mainlang = sys.argv.pop(0)
    if mainlang in veto_lang:
        pywikibot.error("Language '{}' not allowed".format(mainlang))
        sys.exit(20)
    elif len(mainlang) > 3:
        wmproject = mainlang

# Get Wikimedia family (project)
if sys.argv:
    wmprojectparam = sys.argv.pop(0)
    if wmprojectparam != '-':
        wmproject = wmprojectparam

# Login to the Wikimedia account
site = pywikibot.Site(mainlang, wmproject)
site.login()
site_user = site.user()
account = pywikibot.User(site, site_user)
cbotflag = 'bot' in account.groups()
#account_rights = account.rights()
#pdb.set_trace()

# Get user account creation date
try:
    accregdt = account.registration().strftime('%Y-%m-%d')
except Exception:
    # Old accounts do not have a registration date
    accregdt = ''

# This script requires a bot flag
repo = site.data_repository()
repo.login()
#wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

wpwelcomemessage = {}

try:
    # Get default welcome message
    item = get_item_page('Q5611978')
    sitelink = item.sitelinks[mainlang + 'wiki']
    if (sitelink.namespace == TEMPLATENAMESPACE
            and str(sitelink.site.family) == 'wikipedia'):
        wpwelcomemessage[mainlang] = '{{' + sitelink.title + '}} ~~~~'
except Exception as error:
    pywikibot.warning(error)

# Overrule welcome message
wpwelcomemessage['en'] = '{{welcome-t}} ~~~~'
wpwelcomemessage['fr'] = '{{Bienvenue nouveau|' + site_user + '|sign=~~~~}}'
wpwelcomemessage['it'] = '{{subst:Benvenuto}} ~~~~'
wpwelcomemessage['nl'] = '{{welkom}} ~~~~'

wpwelcomemessage['commons'] = '{{welcome}} ~~~~'
wpwelcomemessage['test'] = '{{w}} ~~~~'
wpwelcomemessage['wikidata'] = '{{subst:welcome|~~~~}}'

# Get welcome text from parameter
if sys.argv:
    wpwelcomemessage[mainlang] = sys.argv.pop(0)

# Translate welcome message
try:
    welcomepage = wpwelcomemessage[mainlang]
except:
    pywikibot.error("Language '{}' is not implemented".format(mainlang))
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
        """
>>> wp['groups']
['extendedconfirmed', '*', 'user', 'autoconfirmed']

>>> wp['rights']

Normal user

['createaccount', 'read', 'edit', 'createpage', 'createtalk', 'viewmyprivateinfo', 'editmyprivateinfo', 'editmyoptions', 'urlshortener-create-url', 'centralauth-merge', 'move-rootuserpages', 'minoredit', 'editmyusercss', 'editmyuserjson', 'editmyuserjs', 'sendemail', 'applychangetags', 'changetags', 'viewmywatchlist', 'editmywatchlist', 'spamblacklistlog', 'abusefilter-blocked-external-domains-log', 'mwoauthmanagemygrants', 'patrol', 'move', 'collectionsaveasuserpage', 'collectionsaveascommunitypage', 'autoconfirmed', 'editsemiprotected', 'skipcaptcha', 'abusefilter-log-detail', 'abusefilter-view', 'abusefilter-log', 'transcode-reset', 'transcode-status',
'oathauth-enable']

Project organiser

['campaignevents-enable-registration', 'campaignevents-organize-events', 'campaignevents-email-participants', 'extendedconfirmed',
'createaccount', 'read', 'edit', 'createpage', 'createtalk', 'viewmyprivateinfo', 'editmyprivateinfo', 'editmyoptions', 'urlshortener-create-url', 'centralauth-merge', 'move-rootuserpages', 'minoredit', 'editmyusercss', 'editmyuserjson', 'editmyuserjs', 'sendemail', 'applychangetags', 'changetags', 'viewmywatchlist', 'editmywatchlist', 'spamblacklistlog', 'abusefilter-blocked-external-domains-log', 'mwoauthmanagemygrants', 'patrol', 'move', 'collectionsaveasuserpage', 'collectionsaveascommunitypage', 'autoconfirmed', 'editsemiprotected', 'skipcaptcha', 'abusefilter-log-detail', 'abusefilter-view', 'abusefilter-log', 'transcode-reset', 'transcode-status',
'enrollasmentor']

Create account???

['extendedconfirmed', 'createaccount', 'read', 'edit', 'createpage', 'createtalk', 'viewmyprivateinfo', 'editmyprivateinfo', 'editmyoptions', 'urlshortener-create-url', 'centralauth-merge', 'vipsscaler-test', 'move-rootuserpages', 'minoredit', 'editmyusercss', 'editmyuserjson', 'editmyuserjs', 'sendemail', 'applychangetags', 'changetags', 'viewmywatchlist', 'editmywatchlist', 'spamblacklistlog', 'mwoauthmanagemygrants', 'patrol', 'move', 'collectionsaveasuserpage', 'collectionsaveascommunitypage', 'autoconfirmed', 'editsemiprotected', 'skipcaptcha', 'abusefilter-log-detail', 'abusefilter-view', 'abusefilter-log', 'ipinfo', 'ipinfo-view-basic', 'transcode-reset', 'transcode-status', 'enrollasmentor']

Moderator

['abusefilter-access-protected-vars', 'checkuser-temporary-account', 'checkuser-temporary-account-auto-reveal', 'ipinfo', 'ipinfo-view-full', 'oathauth-enable', 'abusefilter-hidden-log', 'abusefilter-log', 'abusefilter-log-detail', 'abusefilter-log-private', 'abusefilter-modify', 'abusefilter-modify-blocked-external-domains', 'abusefilter-modify-restricted', 'abusefilter-privatedetails-log', 'abusefilter-protected-vars-log', 'abusefilter-revert', 'abusefilter-view', 'abusefilter-view-private', 'apihighlimits', 'autoconfirmed', 'autopatrol', 'autoreviewrestore', 'bigdelete', 'block', 'blockemail', 'browsearchive', 'campaignevents-delete-registration', 'campaignevents-email-participants', 'campaignevents-enable-registration', 'campaignevents-organize-events', 'campaignevents-view-private-participants', 'centralauth-createlocal', 'centralauth-merge', 'centralnotice-admin', 'checkuser-log', 'checkuser-temporary-account-log', 'checkuser-temporary-account-no-preference', 'createaccount', 'createpage', 'createtalk', 'delete', 'deletechangetags', 'deletedhistory', 'deletedtext', 'deletelogentry', 'deleterevision', 'edit', 'editautopatrolprotected', 'editautoreviewprotected', 'editcontentmodel', 'editeditorprotected', 'editextendedsemiprotected', 'editinterface', 'editmyoptions', 'editprotected', 'editsemiprotected', 'editsitecss', 'editsitejs', 'editsitejson', 'edittrustedprotected', 'editusercss', 'edituserjs', 'edituserjson', 'extendedconfirmed', 'flow-create-board', 'flow-delete', 'flow-edit-post', 'flow-hide', 'flow-suppress', 'globalblock-exempt', 'globalblock-whitelist', 'gwtoolset', 'hideuser', 'import', 'importupload', 'ipblock-exempt', 'ipinfo-view-log', 'managechangetags', 'managementors', 'markbotedits', 'massmessage', 'mergehistory', 'move', 'move-categorypages', 'move-rootuserpages', 'move-subpages', 'movefile', 'movestable', 'mwoauthmanageconsumer', 'mwoauthsuppress', 'mwoauthviewprivate', 'mwoauthviewsuppressed', 'newsletter-create', 'newsletter-delete', 'newsletter-manage', 'newsletter-restore', 'noratelimit', 'nuke', 'oathauth-view-log', 'override-antispoof', 'pagetranslation', 'patrol', 'patrolmarks', 'protect', 'purge', 'renameuser', 'reupload', 'reupload-own', 'reupload-shared', 'review', 'rollback', 'setmentor', 'sfsblock-bypass', 'skipcaptcha', 'spamblacklistlog', 'stablesettings', 'suppressionlog', 'suppressredirect', 'tboverride', 'tboverride-account', 'templateeditor', 'titleblacklistlog', 'torunblocked', 'transcode-status', 'translate-import', 'translate-manage', 'translate-messagereview', 'unblockself', 'undelete', 'unwatchedpages', 'upload', 'upload_by_url', 'viewsuppressed', 'writeapi', 'read', 'abusefilter-privatedetails', 'checkuser', 'transcode-reset', 'urlshortener-create-url', 'viewmyprivateinfo', 'editmyprivateinfo', 'minoredit', 'editmyusercss', 'editmyuserjson', 'editmyuserjs', 'sendemail', 'applychangetags', 'changetags', 'viewmywatchlist', 'editmywatchlist', 'abusefilter-blocked-external-domains-log', 'mwoauthmanagemygrants', 'collectionsaveasuserpage', 'collectionsaveascommunitypage', 'enrollasmentor']

        """
        if ('userid' in wp  # user exists
                and 'bot' not in wp['groups']   # skip bot
                and 'bot' not in wp['rights']   # skip bot
                and 'rollback' not in wp['rights']     # skip users with special rights
                and 'viewsuppressed' not in wp['rights']     # skip users with special rights
                and (wikiuser.editCount() > 0 or force_create)):
            page = pywikibot.Page(site, user, USERTALKNAMESPACE)    # User talk page

            if page.text:
                # Could possibly detect specific welcome messages.
                # Because there are many different welcome messages, we simply skip updating.
                # And there are other reasons why not create another welcome message...
                # e.g. the Discussion page (welcome) could already be archived...
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
