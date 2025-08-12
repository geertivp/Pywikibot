#!/usr/bin/python3

codedoc = """
Create a new item

Parameters:

    List of P/Q pairs

    stdin:
        The (common) description in the local language (one line)
        The list of labels for the items to create (one line per item)

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
	2 Ctrl-c pressed, program interrupted (multiple Ctrl-c are required when in language update mode)
    3 Invalid or missing parameter
    10 Homonym
    13 Maxlag error
    20 General error

Author:

	Geert Van Pamel, 2021-12-30, MIT License, User:Geertivp

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string

"""

# List the required modules
import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)

from datetime import datetime	# now, strftime, delta time, total_seconds
from pywikibot.data import api

# Global variables
modnm = 'Pywikibot create_item'     # Module name (using the Pywikibot package)
pgmid = '2025-08-11 (gvp)'	    # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

# Technical configuration flags
MAINLANG = 'en:mul'

# Defaults: transparent and safe
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
shell = True		# Shell available (command line parameters are available; automatically overruled by PAWS)

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
transcmt = '#pwb Create item'

# Properties
INSTANCEPROP = 'P31'


def fatal_error(errcode, errtext):
    """
    A fatal error has occurred; we will print the error messaga, and exit with an error code
    """
    global exitstat

    exitstat = max(exitstat, errcode)
    pywikibot.critical(errtext)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        pywikibot.error('Proceed after fatal error')


def get_item_header(header):
    """Get the item header (label, description, alias in user language).

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


def get_property_label(propx) -> str:
    """Get the label of a property.

    :param propx: property (string or property)
    :return property label (string)
    Except: undefined property
    """

    if isinstance(propx, str):
        propty = pywikibot.PropertyPage(repo, propx)
    else:
        propty = propx

    return get_item_header(propty.labels)


def get_item_page(qnumber) -> pywikibot.ItemPage:
    """Get the item; handle redirects.
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
    """Get the list of preferred languages,
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
    pywikibot.info('\nProcessing statements')

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for newitem in itemlist:	# Main loop for all DISTINCT items
      if  status == 'Stop':	    # Ctrl-c pressed -> stop in a proper way
        break

      objectname = ' '.join(newitem.split()).strip()
      if QSUFFRE.search(objectname):
        status = 'Skip'
        errcount += 1
        exitstat = max(exitstat, 3)
        pywikibot.error('Bad name: {}'.format(objectname))
      elif objectname > "/":    # Skip bad labels
        status = 'OK'
        label = {}
        alias = []
        commonscat = '' # Commons category
        nationality = ''
        qnumber = ''    # In case or error
        transcount += 1	# New transaction

        try:			# Error trapping (prevents premature exit on transaction error)
            # Check if item already exists
            params = {'action': 'wbsearchentities',
                      'format': 'json',
                      'language': mainlang,
                      'type': 'item',
                      'search': objectname}
            request = api.Request(site=repo, parameters=params)
            result = request.submit()

            pywikibot.debug(result)
            if 'search' in result:
                for row in result['search']:
                    item = get_item_page(row['id'])

                    if INSTANCEPROP in item.claims:
                        for seq in item.claims[INSTANCEPROP]:       # Instance
                            instance = seq.getTarget()
                            if instance == targetx[INSTANCEPROP]:
                                for lang in item.labels:
                                    if objectname == item.labels[lang]:##accent fallback
                                        status = 'Update'
                                        break
                                if status == 'Update':
                                    break
                                for lang in item.aliases:
                                    if objectname in item.aliases[lang]:##accent fallback
                                        status = 'Update'
                                        break
                                if status == 'Update':
                                    break
                        if status == 'Update':
                            break

            if status == 'Update':
                # Update item
                qnumber = item.getID()
                for lang in descr:
                    if lang not in item.labels:
                        item.labels[lang] = objectname
                    elif objectname == item.labels[lang]:
                        pass
                    elif lang not in item.aliases:
                        item.aliases[lang] = [objectname]
                    elif objectname not in item.aliases[lang]:
                        item.aliases[lang].append(objectname)        # Merge aliases

                    if lang not in item.descriptions:   # Skip duplicate descr
                        item.descriptions[lang] = descr[lang]

                for lang in item.labels:
                    if lang in item.aliases:
                        while item.labels[lang] in item.aliases[lang]:  # Remove redundant aliases
                            item.aliases[lang].remove(item.labels[lang])

                item.editEntity( {'labels': item.labels, 'descriptions': item.descriptions, 'aliases': item.aliases}, summary=transcmt, bot=wdbotflag)

            elif status == 'OK':
                # Create new item
                item = pywikibot.ItemPage(repo)

                for lang in descr:
                    label[lang] = objectname

                try:
                    item.editEntity( {'labels': label, 'descriptions': descr}, summary=transcmt, bot=wdbotflag)
                    qnumber = item.getID()

                except pywikibot.exceptions.OtherPageSaveError as error:
                    pywikibot.error('Error creating %s, %s' % (objectname, error))
                    status = 'Error'	        # Handle any generic error
                    errcount += 1
                    exitstat = max(exitstat, 10)

            if status in ['OK', 'Update']:
                for propty in targetx:          # Verify if value is already registered
                    propstatus = 'OK'
                    if propty in item.claims:
                        for seq in item.claims[propty]:
                            val = seq.getTarget()
                            if val == targetx[propty]:
                                propstatus = 'Skip'
                                break
                            else:
                                propstatus = 'Other'
                                pywikibot.warning('Conflicting statement {}:{} ({}:{}) - {} ({}) for {}'
                                                  .format(get_property_label(propty), get_item_header(targetx[propty].labels),
                                                          propty, targetx[propty].getID(),
                                                          get_item_header(val.labels), val.getID(), qnumber))

                    if propstatus == 'OK':      # Claim is missing, so add it now
                        claim = pywikibot.Claim(repo, propty)
                        claim.setTarget(targetx[propty])
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)

# (14) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.MaxlagTimeoutError as error:  # Attempt error recovery
            pywikibot.error('Error updating %s, %s' % (qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 20)
            deltasecs = int((datetime.now() - now).total_seconds())	# Calculate technical error penalty
            if deltasecs >= 30: 	# Technical error; for transactional errors there is no wait time increase
                errsleep += errwaitfactor * min(maxdelay, deltasecs)
                # Technical errors get additional penalty wait
				# Consecutive technical errors accumulate the wait time, until the first successful transaction
				# We limit the delay to a multitude of maxdelay seconds
            if errsleep > 0:    	# Allow the servers to catch up; slowdown the transaction rate
                pywikibot.error('%d seconds maxlag wait' % (errsleep))
                time.sleep(errsleep)

        except Exception as error:  # other exception to be used
            pywikibot.error('Error updating %s, %s' % (qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 20)
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

        isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Only needed to format output
        totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
        pywikibot.info('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, qnumber, objectname, commonscat, alias, nationality, descr[mainlang]))


def show_help_text():
# Show program help and exit (only show head text)
    helptxt = HELPRE.search(codedoc)
    if helptxt:
        pywikibot.info(helptxt.group(0))	# Show helptext
    sys.exit(1)         # Must stop


def get_next_param():
    """
    Get the next command parameter, and handle any qualifiers
    """

    cpar = sys.argv.pop(0)	    # Get next command parameter

    if cpar.startswith('-h'):	# help
        show_help_text()
    elif cpar.startswith('-'):	# unrecognized qualifier (fatal error)
        fatal_error(4, 'Unrecognized qualifier; use -h for help')
    return cpar		# Return the parameter or the qualifier to the caller


"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""
HELPRE = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
PROPRE = re.compile(r'P[0-9]+')             # P-number
QSUFFRE = re.compile(r'Q[0-9]+')            # Q-number

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
except:
    shell = False
    pywikibot.info('{}, {}, {}, {} (No shell available)'.format(modnm, pgmid, pgmlic, creator))

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

inpar = '-'
while len(sys.argv) > 0 and inpar.startswith('-'):
    inpar = get_next_param()

try:
    # Connect to database
    repo = pywikibot.Site('wikidata')  # Login to Wikibase instance
    repo.login()            # Must login
    wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

    # Get all claims from parameter list
    targetx = {}

    while len(sys.argv) > 1:
        inpar = PROPRE.findall(inpar.upper())[0]
        targetx[inpar] = get_item_page(QSUFFRE.findall(sys.argv.pop(0).upper())[0])
        inpar = sys.argv.pop(0)

    if not inpar.startswith('-'):
        inpar = PROPRE.findall(inpar.upper())[0]
        targetx[inpar] = get_item_page(QSUFFRE.findall(sys.argv.pop(0).upper())[0])

except Exception as error:
    # Other exception to be used
    fatal_error(20, 'Data error, {}'.format(error))

# List the statements
for propty in targetx:
    proptyx = pywikibot.PropertyPage(repo, propty)
    pywikibot.info('Statement {}:{} ({}:{})'
                   .format(get_property_label(proptyx), get_item_header(targetx[propty].labels),
                           propty, targetx[propty].getID()))

if INSTANCEPROP not in targetx:
    fatal_error(3, 'Missing {} ({})'.format(get_property_label(INSTANCEPROP), INSTANCEPROP))

# Print preferences
pywikibot.log('Main language:\t%s' % mainlang)
pywikibot.log('Maximum delay:\t%d s' % maxdelay)
pywikibot.log('Exit on fatal error:\t%s' % exitfatal)
pywikibot.log('Error wait factor:\t%d' % errwaitfactor)

# Get list of item numbers
inputfile = sys.stdin.read()
itemlist = inputfile.splitlines()
descr = {mainlang: itemlist.pop(0)}
itemlist = sorted(set(itemlist))

pywikibot.debug(itemlist)

wd_proc_all_items()	# Execute all items for one language

"""
    Print all sitelinks (base addresses)
    PAWS is using tokens (passwords can't be used because Python scripts are public)
    Shell is using passwords (from user-password.py file)
"""
for site in sorted(pywikibot._sites.values()):
    if site.username():
        pywikibot.debug('{} {} {} {}'.format(site, site.username(), site.is_oauth_token_available(), site.logged_in()))

sys.exit(exitstat)

