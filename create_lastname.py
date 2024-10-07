#!/usr/bin/python3

codedoc = """
Create a new lastname

Parameters:

    P1, P2...: optional additional claims (possibility to overrule default claims)

    stdin: the list of lastnames

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
    3 Invalid or missing parameter
    10 Homonym
    13 Maxlag error
    20 Page save error
    30 General error
    130 Ctrl-c pressed, program interrupted

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

    pip install cologne-phonetics
    pip install jellyfish
    pip install phonetisch

Author:

	Geert Van Pamel, 2021-01-06, MIT License, User:Geertivp

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string
    https://pypi.org/project/cologne-phonetics/
    https://github.com/maxwellium/cologne-phonetic
    https://maxwellium.github.io/cologne-phonetic/
    https://en.wikipedia.org/wiki/Cologne_phonetics

Known problems:

    Duplicates can possibly be created due to augmented replication delays.

"""

import cologne_phonetics
import jellyfish        # soundex
import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import unidecode        # Unicode

from datetime import datetime	# now, strftime, delta time, total_seconds
from phonetisch import caverphone
from pywikibot.data import api

# Global variables
modnm = 'Pywikibot create_lastname'     # Module name (using the Pywikibot package)
pgmid = '2024-10-07 (gvp)'	    # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

# Technical configuration flags
# Defaults: transparent and safe
errorstat = True    # Show error statistics (disable with -e)
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
shell = True		# Shell available (command line parameters are available; automatically overruled by PAWS)
showcode = False	# Show the generated SPARQL code (activate with -c)
verbose = True		# Can be set with -q or -v (better keep verbose to monitor the bot progress)

# Technical parameters

"""
    Default error penalty wait factor (can be overruled with -f).
    Larger values ensure that maxlag errors are avoided, but temporarily delay processing.
    It is advised not to overrule this value.
"""
exitstat = 0        # (default) Exit status
errwaitfactor = 4	# Extra delay after error; best to keep the default value (maximum delay of 4 x 150 = 600 s = 10 min)
maxdelay = 150		# Maximum error delay in seconds (overruling any extreme long processing delays)

# To be set in user-config.py (what parameters is PAWS using?)
"""
    maxthrottle = 60
    put_throttle = 1, for maximum transaction speed (bot account required)
    noisysleep = 60.0, to avoid the majority/all of the confusing sleep messages
    maxlag = 5, to avoid overloading the servers
    max_retries = 4
    retry_wait = 30
    retry_max = 320
"""

# Wikidata transaction comment
transcmt = '#pwb Create lastname'	    	# Wikidata transaction comment

# Properties
INSTANCEPROP = 'P31'
SUBCLASSPROP = 'P279'
SCRIPTPROP = 'P282'
COMMCATPROP = 'P373'
LASTNAMEPROP = 'P734'
NATIVELANGLABELPROP = 'P1705'
CAVERPHONPROP = 'P3880'
SOUNDEXPROP = 'P3878'
KOLNPHONPROP = 'P3879'
INFIXPROP = 'P7377'

# Instances
LATINSCRIPTINSTANCE = 'Q8229'
LASTNAMEINSTANCE = 'Q101352'
TOPONYMLASTNAMEINSTANCE = 'Q17143070'
COMPLASTNAME = 'Q60558422'
AFFIXLASTNAMEINSTANCE = 'Q66480858'

# Functional configuration flags
MAINLANG = 'en:mul'

# Set base statements
target = {
    INSTANCEPROP: LASTNAMEINSTANCE,
    SCRIPTPROP: LATINSCRIPTINSTANCE,
}

# Validation rules
propreqinst = {
    LASTNAMEPROP: {AFFIXLASTNAMEINSTANCE, COMPLASTNAME, LASTNAMEINSTANCE, TOPONYMLASTNAMEINSTANCE},
}

name_prefix_list = {
    'Van': 'Q69876093',
    'van': 'Q69872130',
    'Von': 'Q70084230',
    'von': 'Q69870160',
    ## should be extended
}


def fatal_error(errcode, errtext):
    """
    A fatal error has occurred.
    We will print the error message, and exit with an error code.
    """
    global exitstat

    exitstat = max(exitstat, errcode)
    pywikibot.critical(errtext)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        pywikibot.warning('Proceed after fatal error')


def get_item_header(header):
    """
    Get the item header (label, description, alias in user language)

    :param header: item label, description, or alias language list (string or list)
    :return: label, description, or alias in the first available language (string)
    """

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
    else:
        item = qnumber
        qnumber = item.getID()

    while item.isRedirectPage():
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


def item_is_in_list(statement_list, itemlist):
    """
    Verify if statement list contains at least one item from the itemlist
    param: statement_list: Statement list
    param: itemlist:      List of values
    return: Matching or empty string
    """
    for seq in statement_list:
        try:
            isinlist = seq.getTarget().getID()
            if isinlist in itemlist:
                return isinlist
        except:
            pass    # Ignore NoneType error
    return ''


def get_item_label_dict(qnumber) -> {}:
    """
    Get the Wikipedia labels in all languages for a Qnumber.
    :param qnumber: list number
    :return: capitalized label dict (index by ISO language code)
    Example of usage:
        Image namespace name.
    """
    labeldict = {}
    item = get_item_page(qnumber)
    # Get target labels
    for lang in item.labels:
        if ROMANRE.search(item.labels[lang]):
            labeldict[lang] = item.labels[lang]
    return labeldict


def get_item_list(item_name: str, instance_id) -> list:
    """Get list of items by name, belonging to an instance (list)

    :param item_name: Item name (string)
    :param instance_id: Instance ID (set, or list)
    :return: List of items (Q-numbers)

    See https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    """
    pywikibot.debug('Search label: {}'.format(item_name.encode('utf-8')))
    item_list = set()                   # Empty set
    params = {'action': 'wbsearchentities',
              'search': item_name,      # Get item list from label
              'type': 'item',
              'language': mainlang,     # Labels are in native language
              'uselang': mainlang,
              'strictlanguage': False,  # All languages are searched
              'format': 'json',
              'limit': 20}              # Should be reasonable value
    request = api.Request(site=repo, parameters=params)
    result = request.submit()
    pywikibot.debug(result)

    if 'search' in result:
        # Ignore accents and case
        item_name_canon = item_name
        for row in result['search']:                    # Loop though items
            ##print(row)
            item = get_item_page(row['id'])

            # Matching instance, strict equal comparison
            # Remark that most items have a proper instance
            if SUBCLASSPROP not in item.claims and (
                    INSTANCEPROP not in item.claims
                    or item_is_in_list(item.claims[INSTANCEPROP], instance_id)):
                # Search all languages
                for lang in item.labels:
                    if item_name_canon == item.labels[lang]:
                        item_list.add(item.getID())     # Label match
                        break
                for lang in item.aliases:
                    for seq in item.aliases[lang]:
                        if item_name_canon == seq:
                            item_list.add(item.getID()) # Alias match
                            break
    pywikibot.log(item_list)
    # Convert set to list; keep sort order (best matches first)
    return list(item_list)


def wd_proc_all_items():
    """
    """

    global exitstat

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    statcount = 0           # Statement count
    pictcount = 0	    	# Picture count
    safecount = 0	    	# Safe transaction
    errcount = 0	    	# Error counter
    errsleep = 0	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    pywikibot.info('Processing %d statements' % (len(itemlist)))

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for newitem in itemlist:	# Main loop for all DISTINCT items
      if  status == 'Stop':	    # Ctrl-c pressed -> stop in a proper way
        break

      objectname = ' '.join(newitem.split())
      if not objectname:
        pass
      elif not ROMANRE.search(objectname):
        status = 'Skip'
        errcount += 1
        exitstat = max(exitstat, 3)
        pywikibot.error('Bad name: {}'.format(objectname))
      else:
        transcount += 1	# New transaction
        status = 'OK'
        label = {}
        alias = []
        commonscat = '' # Commons category
        nationality = ''
        qnumber = ''    # In case or error

        try:
            # Get all matching items
            name_list = get_item_list(objectname, propreqinst[LASTNAMEPROP])

            if len(name_list) == 1 and not showcode:
                # Update the lastname
                status = 'Update'
                item = get_item_page(name_list[0])
                qnumber = item.getID()

                # Merge labels
                lang = 'mul'
                if lang not in item.labels:
                    item.labels[lang] = objectname              # Add language code
                elif objectname == item.labels[lang]:
                    pass
                elif lang not in item.aliases:
                    item.aliases[lang] = [objectname]           # Add alias
                elif objectname not in item.aliases[lang]:
                    item.aliases[lang].append(objectname)       # Merge aliases

                """
                # https://phabricator.wikimedia.org/T303677
                for lang in descr:
                    if lang not in item.descriptions:           # Skip duplicate descr
                        item.descriptions[lang] = descr[lang]
                """

                # Remove redundant aliases
                # Should also enforce mul labels
                for lang in item.labels:
                    if lang in item.aliases:
                        while item.labels[lang] in item.aliases[lang]:
                            item.aliases[lang].remove(item.labels[lang])

                item.editEntity({'labels': item.labels, 'descriptions': item.descriptions, 'aliases': item.aliases}, summary=transcmt)
            elif name_list and not showcode:
                status = 'Ambiguous'            # Item is not unique
                pywikibot.error('Ambiguous lastname {} {}'.format(objectname, name_list))
            else:
                # Create the lastname
                label['mul'] = objectname

                try:
                    item = pywikibot.ItemPage(repo)         # Create item
                    item.editEntity({'labels': label}, summary=transcmt)
                    qnumber = item.getID()
                    pywikibot.warning('Created lastname {} ({})'
                                      .format(objectname, qnumber))
                except pywikibot.exceptions.OtherPageSaveError as error:
                    pywikibot.error('Error creating %s, %s' % (objectname, error))
                    status = 'Error'	    # Handle any generic error
                    errcount += 1
                    exitstat = max(exitstat, 10)

            if status in ['OK', 'Update']:
                # Merge the statements
                for propty in targetx:
                    if (propty not in item.claims
                            or not item_is_in_list(item.claims[propty], [target[propty]])):
                        # Amend item if value is not already registered
                        claim = pywikibot.Claim(repo, propty)
                        claim.setTarget(targetx[propty])
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                        # Should confirm?

                if NATIVELANGLABELPROP not in item.claims:      # Label in official language
                    claim = pywikibot.Claim(repo, NATIVELANGLABELPROP)
                    claim.setTarget(pywikibot.WbMonolingualText(text=objectname, language='mul'))
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning('Adding native name: {}'.format(objectname))

                if SOUNDEXPROP not in item.claims:
                    soundex = jellyfish.soundex(objectname)
                    claim = pywikibot.Claim(repo, SOUNDEXPROP)
                    claim.setTarget(soundex)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning('Adding soundex: {}'.format(soundex))

                if KOLNPHONPROP not in item.claims:
                    colnphon = cologne_phonetics.encode(objectname)[0][1]
                    claim = pywikibot.Claim(repo, KOLNPHONPROP)
                    claim.setTarget(colnphon)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning('Adding Köhl phonetic: {}'.format(colnphon))

                if CAVERPHONPROP not in item.claims:
                    caverphon = caverphone.encode_word(objectname)
                    claim = pywikibot.Claim(repo, CAVERPHONPROP)
                    claim.setTarget(caverphon)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning('Adding caverphone: {}'.format(caverphon))

                # Build a list of affixes
                for name_prefix in name_prefix_list:
                    if objectname.startswith(name_prefix + ' '):
                        break
                else:
                    name_prefix = ''

                if name_prefix:
                    if not item_is_in_list(item.claims[INSTANCEPROP], [AFFIXLASTNAMEINSTANCE]):
                        claim = pywikibot.Claim(repo, INSTANCEPROP)
                        claim.setTarget(affix_namex)
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)

                    if INFIXPROP not in item.claims:
                        claim = pywikibot.Claim(repo, INFIXPROP)
                        claim.setTarget(name_prefix_list[name_prefix])
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)

                    # Need to verify on toponym first
                    if False and not item_is_in_list(item.claims[INSTANCEPROP], [TOPONYMLASTNAMEINSTANCE]):
                        claim = pywikibot.Claim(repo, INSTANCEPROP)
                        claim.setTarget(toponym_namex)
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)

                commonscat = objectname + ' (surname)'
                if 'commonswiki' in item.sitelinks:
                    sitelink = item.sitelinks['commonswiki']
                    commonscat = sitelink.title
                    colonloc = commonscat.find(':')
                    if colonloc >= 0:
                        commonscat = commonscat[colonloc + 1:]
                else:
                    # Create commonscat
                    page = pywikibot.Category(site, commonscat)
                    if cbotflag and not page.text:
                        pageupdated = transcmt + ' Add Wikidata Infobox'
                        page.text = '{{Wikidata Infobox}}'
                        pywikibot.warning('Add {} template to Commons {}'
                                          .format('Wikidata Infobox', page.title()))
                        page.save(summary=pageupdated, minor=True) #, bot=True) ##, bot=cbotflag) ## got multiple values for keyword argument 'bot'
                        status = 'Infobox'

                    sitedict = {'site': 'commonswiki', 'title': 'Category:' + commonscat}
                    try:
                        item.setSitelink(sitedict, bot=wdbotflag, summary='#pwb Add sitelink')
                        status = 'Commons'
                        ## Run copy_label for item number
                    except pywikibot.exceptions.OtherPageSaveError as error:
                        # Get unique Q-numbers, skip duplicates (order not guaranteed)
                        commonscat = ''
                        itmlist = set(QSUFFRE.findall(str(error)))
                        if len(itmlist) > 1:
                            itmlist.remove(qnumber)
                            pywikibot.error('Conflicting category statement {}, {}'
                                            .format(qnumber, itmlist))
                            status = 'DupCat'	    # Conflicting category statement
                            errcount += 1
                            exitstat = max(exitstat, 10)

                if commonscat and COMMCATPROP not in item.claims:
                    claim = pywikibot.Claim(repo, COMMCATPROP)
                    claim.setTarget(commonscat)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)

# (14) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 130)

        except pywikibot.exceptions.MaxlagTimeoutError as error:  # Attempt error recovery
            pywikibot.error('Error updating %s, %s' % (qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 13)
            deltasecs = int((datetime.now() - now).total_seconds())	# Calculate technical error penalty
            if deltasecs >= 30: 	# Technical error; for transactional errors there is no wait time increase
                errsleep += errwaitfactor * min(maxdelay, deltasecs)
                # Technical errors get additional penalty wait
				# Consecutive technical errors accumulate the wait time, until the first successful transaction
				# We limit the delay to a multitude of maxdelay seconds
            if errsleep > 0:    	# Allow the servers to catch up; slowdown the transaction rate
                pywikibot.error('%d seconds maxlag wait' % (errsleep))
                time.sleep(errsleep)

        except pywikibot.exceptions.OtherPageSaveError as error:  # Page save error
            pywikibot.error('Error updating %s, %s' % (qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 20)

        except Exception as error:  # other exception to be used
            pywikibot.error('Error updating %s, %s' % (qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 30)
            if exitfatal:           # Stop on first error
                raise

        """
    The transaction was either executed correctly, or an error occurred.
    Possibly already a system error message was issued.
    We will report the results here, as much as we can, one line per item.
        """

# Get the elapsed time in seconds and the timestamp in string format
        prevnow = now	        	# Transaction status reporting
        now = datetime.now()	    # Refresh the timestamp to time the following transaction

        if verbose or status not in ['OK']:		# Print transaction results
            isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Only needed to format output
            totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
            pywikibot.info('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, qnumber, objectname, commonscat, alias, nationality, descr[mainlang]))


def show_help_text():
# Show program help and exit (only show head text)
    helptxt = HELPRE.search(codedoc)
    if helptxt:
        pywikibot.info(helptxt.group(0))	# Show helptext
    sys.exit(1)         # Must stop


def show_prog_version():
# Show program version
    pywikibot.info('{}, {}, {}, {}'.format(modnm, pgmid, pgmlic, creator))


def get_next_param():
    """
    Get the next command parameter, and handle any qualifiers
    """

    global showcode
    global errwaitfactor
    global exitfatal
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter

    if cpar.startswith('-c'):	# code check
        showcode = True
        print('Show generated code')
    elif cpar.startswith('-e'):	# error stat
        errorstat = False
        print('Disable error statistics')
    elif cpar.startswith('-h'):	# help
        show_help_text()
    elif cpar.startswith('-m'):	# fast mode
        errwaitfactor = 1
        print('Setting fast mode')
    elif cpar.startswith('-p'):	# proceed after fatal error
        exitfatal = False
        print('Setting proceed after fatal error')
    elif cpar.startswith('-q'):	# quiet mode
        verbose = False
        print('Setting quiet mode')
    elif cpar.startswith('-v'):	# verbose mode
        verbose = True
        print('Setting verbose mode')
    elif cpar.startswith('-V'):	# Version
        show_prog_version()
    elif cpar.startswith('-'):	# unrecognized qualifier (fatal error)
        fatal_error(4, 'Unrecognized qualifier; use -h for help')
    return cpar		# Return the parameter or the qualifier to the caller


# Main program entry

if verbose:
    show_prog_version()	    	# Print the module name

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
except:
    shell = False
    pywikibot.warning('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

HELPRE = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
PROPRE = re.compile(r'P[0-9]+')             # P-number
QSUFFRE = re.compile(r'Q[0-9]+')            # Q-number
ROMANRE = re.compile(r'^[a-z .,"()\'åáàâäāæǣçéèêëėíìîïıńñŋóòôöœøřśßúùûüýÿĳ-]{2,}$', flags=re.IGNORECASE)  # Roman alphabet

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

inpar = '-'
while sys.argv and inpar.startswith('-'):
    inpar = get_next_param()

# Get all claims from parameter list

while sys.argv:
    propty = PROPRE.findall(inpar.upper())[0]
    target[propty] = QSUFFRE.findall(sys.argv.pop(0).upper())[0]
    inpar = sys.argv.pop(0)

if not inpar.startswith('-'):
    propty = PROPRE.findall(inpar.upper())[0]
    target[propty] = QSUFFRE.findall(sys.argv.pop(0).upper())[0]

# Print preferences
pywikibot.log('Main language:\t%s' % mainlang)
pywikibot.log('Maximum delay:\t%d s' % maxdelay)
pywikibot.log('Show code:\t%s' % showcode)
pywikibot.log('Verbose mode:\t%s' % verbose)
pywikibot.log('Exit on fatal error:\t%s' % exitfatal)
pywikibot.log('Error wait factor:\t%d' % errwaitfactor)

# Connect to database
site = pywikibot.Site('commons')
site.login()
cbotflag = 'bot' in pywikibot.User(site, site.user()).groups()

# This script requires a bot flag
repo = site.data_repository()
repo.login()
wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

# Get description
descr = get_item_label_dict(LASTNAMEINSTANCE)
#for val in sorted(descr):
#    pywikibot.debug('{}\t{}'.format(val, descr[val]))

# Compile the statements
targetx={}
for propty in target:
    proptyx = pywikibot.PropertyPage(repo, propty)
    targetx[propty] = get_item_page(target[propty])
    pywikibot.info('Statement {}:{} ({}:{})'
                   .format(get_item_header(proptyx.labels), get_item_header(targetx[propty].labels),
                           propty, target[propty]))

# Item pages
affix_namex = get_item_page(AFFIXLASTNAMEINSTANCE)
toponym_namex = get_item_page(TOPONYMLASTNAMEINSTANCE)

for name_prefix in name_prefix_list:
    name_prefix_list[name_prefix] = get_item_page(name_prefix_list[name_prefix])

# Get list of item numbers
inputfile = sys.stdin.read()
itemlist = sorted(set(inputfile.splitlines()))
pywikibot.debug(itemlist)

wd_proc_all_items()	    # Execute all items for one language

"""
    Print all sitelinks (base addresses)
    PAWS is using tokens (passwords can't be used because Python scripts are public)
    Shell is using passwords (from user-password.py file)
"""
for site in sorted(pywikibot._sites.values()):
    if site.username():
        pywikibot.debug('{}\t{}\t{}\t{}'
                        .format(site, site.username(), site.is_oauth_token_available(), site.logged_in()))

sys.exit(exitstat)
