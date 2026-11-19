#!/usr/bin/python3

codedoc = """
Add statements to a list of items.

Parameters:

    P1 P2:... Property/value

    stdin:

        Item list (regex)

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
	3 Invalid or missing parameter
    20 General error
    130 Ctrl-c pressed, program interrupted

Examples:

    pwb add_statement P6104=Q137774267

Author:

	Geert Van Pamel, 2021-01-30, MIT License, User:Geertivp

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

"""

# List the required modules
import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)

from datetime import datetime	# now, strftime, delta time, total_seconds

# Global technical parameters
modnm = 'Pywikibot add_statement'   # Module name (using the Pywikibot package)
pgmid = '2026-06-06 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

"""
    Static definitions
"""

# Functional configuration flags
MAINLANG = 'en:mul'

INSTANCEPROP = 'P31'
SUBCLASSPROP = 'P279'
COMMCATPROP = 'P373'
COMMCREATPROP = 'P1472'
COMMINSTPROP = 'P1612'

commonscat_list = [
    COMMCATPROP,
    COMMCREATPROP,
    COMMINSTPROP,
]

# Technical configuration flags
# Defaults: transparent and safe
debug = False		# Can be activated with -d (errors and configuration changes are always shown)
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
shell = True		# Shell available (command line parameters are available; automatically overruled by PAWS)
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


def get_item_prop_val_str(item, proplist) -> str:
    """
    Get property value string

    :param item: Wikidata item
    :param proplist: Search list of properties
    :return: concatenated list of values
    """
    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:
            for seq in item.claims[prop]:
                item_prop_val += seq.getTarget() + '/'
            break
    return item_prop_val[:-1]


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
    errsleep = 15	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    pywikibot.info('\nProcessing {:d} statements'.format(len(itemlist)))

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for qnumber in itemlist:	# Main loop for all DISTINCT items

        if status == 'Stop':	# Ctrl-c pressed -> stop in a proper way
            break

        transcount += 1	# New transaction
        status = 'Skip'
        alias = ''
        descr = ''
        commonscat = '' # Commons category
        nationality = ''
        label = ''

        pywikibot.debug(qnumber)

        try:			# Error trapping (prevents premature exit on transaction error)
            item = get_item_page(qnumber)
            qnumber = item.getID()

            label = get_item_header(item.labels)
            descr = get_item_header(item.descriptions)
            alias = get_item_header(item.aliases)

# Get Commons category/creator
            commonscat = get_item_prop_val_str(item, commonscat_list) # Wikimedia Commons Category, Creator

# Merge claims
            if SUBCLASSPROP in item.claims:         # Only add statements for instances
                status = 'Subclass'
            else:
                for propty in target:               # Verify if value is already registered
                    propstatus = 'OK'
                    if propty in item.claims:
                        for seq in item.claims[propty]:
                            if seq.getTarget().getID() == target[propty]:
                                propstatus = 'Skip'
                                break

                    if propstatus == 'OK':          # Claim is missing, so add it now
                        claim = pywikibot.Claim(repo, propty)
                        claim.setTarget(targetx[propty])
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                        status = 'OK'
            try:
                # Get first instance
                primary_inst_item = get_item_page(item.claims[INSTANCEPROP][0].getTarget())
                instance_label = get_item_header(primary_inst_item.labels)
                item_instance = primary_inst_item.getID()
            except:
                instance_label = '-'
                item_instance = None

# (14) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 130)

        except pywikibot.exceptions.NoPageError as error:           # Item not found
            pywikibot.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.MaxlagTimeoutError as error:    # Attempt error recovery
            pywikibot.error('Error updating {}, {}'.format(qnumber, error))
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
                pywikibot.error('{:d} seconds maxlag wait'.format(errsleep))
                time.sleep(errsleep)

        except Exception as error:  # other exception to be used
            pywikibot.error('Error processing {}, {}'.format(qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 20)
            if False and exitfatal:           # Stop on first error
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
            pywikibot.info('{:d}\t{}\t{:.3f}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'
                           .format(transcount, isotime, totsecs, status, instance_label, qnumber, label,
                                   commonscat, alias, nationality, descr))


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

    global debug
    global errwaitfactor
    global exitfatal
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter
    pywikibot.log('Parameter {}'.format(cpar))

    if cpar.startswith('-d'):	# debug mode
        debug = True
        print('Setting debug mode')
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
    pywikibot.debug('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
except:
    shell = False
    pywikibot.info('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

HELPRE = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
PROPRE = re.compile(r'P[0-9]+')             # P-number
QSUFFRE = re.compile(r'Q[0-9]+')            # Q-number

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

inpar = '-'
while sys.argv and inpar.startswith('-'):
    inpar = get_next_param()

# Get all claims from parameter list
### We should not use the target list
target={}
proptyx={}

# Set all claims in parameter list
while sys.argv:
    inprop = PROPRE.findall(inpar.upper())[0]
    if ':-' in inpar:
        target[inprop] = '-'
        inpar = '-'
    else:
        if ':Q' not in inpar and '=' not in inpar:
            inpar = sys.argv.pop(0)
        try:
            target[inprop] = QSUFFRE.findall(inpar.upper())[0]
            inpar = '-'
        except IndexError:
            target[inprop] = '-'
            inpar = '-'

        if sys.argv:
            inpar = sys.argv.pop(0)

if inpar != '-':
    inprop = PROPRE.findall(inpar.upper())[0]
    if ':-' in inpar:
        target[inprop] = '-'
    else:
        if ':Q' not in inpar and '=' not in inpar:
            inpar = sys.argv.pop(0)
        try:
            target[inprop] = QSUFFRE.findall(inpar.upper())[0]
        except IndexError:
            target[inprop] = '-'

# Print preferences
pywikibot.log('Main language:\t%s' % mainlang)
pywikibot.log('Maximum delay:\t%d s' % maxdelay)
pywikibot.log('Verbose mode:\t%s' % verbose)
pywikibot.log('Debug mode:\t%s' % debug)
pywikibot.log('Exit on fatal error:\t%s' % exitfatal)
pywikibot.log('Error wait factor:\t%d' % errwaitfactor)

# Connect to database
transcmt = '#pwb Add statement'	    	    # Wikidata transaction comment
repo = pywikibot.Site('wikidata')  # Login to Wikibase instance
repo.login()
wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

targetx={}
for propty in target:
    if target[propty] != '-':
        if propty not in proptyx:
            proptyx[propty] = pywikibot.PropertyPage(repo, propty)
        targetx[propty] = get_item_page(target[propty])
        pywikibot.info('Add {}:{} ({}:{})'
                       .format(get_item_header(proptyx[propty].labels),
                               get_item_header(targetx[propty].labels),
                               propty, target[propty]))

# Get list of item numbers
inputfile = sys.stdin.read()
itemlist = sorted(set(QSUFFRE.findall(inputfile)))
pywikibot.debug(itemlist)

wd_proc_all_items()	# Execute all items for one language

"""
    Print all sitelinks (base addresses)
    PAWS is using tokens (passwords can't be used because Python scripts are public)
    Shell is using passwords (from user-password.py file)
"""
if debug:
    for site in sorted(pywikibot._sites.values()):
        if site.username():
            print(site, site.username(), site.is_oauth_token_available(), site.logged_in())

sys.exit(exitstat)
