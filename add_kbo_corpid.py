#!/usr/bin/python3

codedoc = """
Add a missing Corporate Id based on the KBO enterprise number.

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
	3 Invalid or missing parameter
    12 Item does not exist
    20 General error
    130 Ctrl-c pressed, program interrupted

Author:

	Geert Van Pamel, 2021-02-03, GNU General Public License v3.0, User:Geertivp

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string

"""

# List the required modules
import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)
from datetime import datetime	    # now, strftime, delta time, total_seconds
from pywikibot import pagegenerators as pg # Wikidata Query interface

# Global variables
modnm = 'Pywikibot add_kbo_corpid'  # Module name (using the Pywikibot package)
pgmid = '2023-07-27 (gvp)'	    # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

"""
    Static definitions
"""

BOTFLAG = True

# Functional configuration flags

# Technical configuration flags
# Defaults: transparent and safe
debug = False		# Can be activated with -d (errors and configuration changes are always shown)
errorstat = True    # Show error statistics (disable with -e)
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
readonly = False    # Dry-run
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
minsucrate = 80.0   # Minimum success rate per target language (the script is stopped below this threshold)

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

# Properties
CTRYPROP = 'P17'
ENDDTPROP = 'P582'
OPENCORPID = 'P1320'
KBONUMBER = 'P3376'
TVANUMBER = 'P3608'

# Instances
CTRYBELGIUM = 'Q31'

ENLANG = 'en'


def fatal_error(errcode, errtext):
    """
    A fatal error has occurred.
    We will print the error messaga, and exit with an error code.
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

    :param: item label, description, or alias language list
    :return: label, description, or alias in the first available language
    """
    header_value = '-'
    for lang in label_languages:
        if lang in header:
            header_value = header[lang]
            break
    return header_value


def get_item_page(qnumber):
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
    else:
        item = qnumber

    while item.isRedirectPage():
        ## Should fix the sitelinks
        item = item.getRedirectTarget()

    return item


def get_language_preferences() -> []:
    """
    Get the list of preferred languages,
    using environment variables LANG, LC_ALL, and LANGUAGE.
    Result:
        List of ISO 639-1 language codes
    Documentation:
        https://www.gnu.org/software/gettext/manual/html_node/Locale-Environment-Variables.html
    """
    mainlang = os.getenv('LANGUAGE',
                         os.getenv('LC_ALL',
                         os.getenv('LANG', ENLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang]

    # Cleanup language list
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)
    return main_languages


def wd_proc_all_items():
    """
    """

    global exitstat

    querytxt = """# Get all Belgian enterprises without a Corporate ID
SELECT DISTINCT ?item WHERE {
?item wdt:P3376 ?kbo_number.
MINUS { ?item wdt:P1320 ?enterprise_id. }
}
"""

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    errcount = 0	    	# Error counter
    errsleep = 0	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    if verbose:
        pywikibot.info('\nProcessing KBO-corpID statements')

    generator = pg.WikidataSPARQLPageGenerator(querytxt, site=repo)

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for item in generator:	# Main loop for all DISTINCT items

## alow removing conflicts
      if status != 'Stop':	# Ctrl-c pressed -> stop in a proper way

        transcount += 1	# New transaction
        valid_kbo = False
        status = 'Fail'
        alias = ''
        descr = ''
        commonscat = '' # Commons category
        nationality = ''
        label = ''
        kbo_number = ''

        try:			# Error trapping (prevents premature exit on transaction error)
            item = get_item_page(item.getID())
            qnumber = item.getID()

            if mainlang in item.labels:
                label = item.labels[mainlang]

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]

            if KBONUMBER in item.claims and OPENCORPID not in item.claims:   # Runtime check required (statement could have been deleted)
                for seq in item.claims[KBONUMBER]:        # Search for a valid Belgian enterprise number
                    kbo_number = seq.getTarget()

                    if ENDDTPROP in seq.qualifiers:        # Should not have an end-date
                        continue
                    elif KBONUMRE.search(kbo_number):   # 10 digits
                        valid_kbo = True
                    elif KBOSHORTNUMRE.search(kbo_number):  # 9 digits getting leading 0
                        kbo_number = '0' + kbo_number
                        valid_kbo = True

                        claim = pywikibot.Claim(repo, KBONUMBER)   # Fix the 10-digit format
                        claim.setTarget(kbo_number)
                        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                        item.removeClaims(seq, bot=BOTFLAG, summary=transcmt)
                    elif KBOLONGNUMRE.search(kbo_number):  # 3x3 digits with dots
                        kbo_number = kbo_number[0:4] + kbo_number[5:8] + kbo_number[9:12]
                        valid_kbo = True

                        claim = pywikibot.Claim(repo, KBONUMBER)   # Fix the 10-digit format
                        claim.setTarget(kbo_number)
                        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                        item.removeClaims(seq, bot=BOTFLAG, summary=transcmt)

                    if valid_kbo:           # Add missing Corporate ID
                        claim = pywikibot.Claim(repo, OPENCORPID)
                        claim.setTarget('be/' + kbo_number)
                        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                        status = 'Update'
                        break

            if CTRYPROP not in item.claims:                # Mandatory country BE, because having Belgian enterprise number
                claim = pywikibot.Claim(repo, CTRYPROP)
                claim.setTarget(pywikibot.ItemPage(repo, CTRYBELGIUM))
                item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.NoPageError as error:           # Item does not exist
            pywikibot.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.MaxlagTimeoutError as error:    # Attempt error recovery
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
            pywikibot.error(error)
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

        if verbose or status not in ['OK']:		# Print transaction results
            isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Only needed to format output
            totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
            pywikibot.info('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), kbo_number, label, commonscat, alias, nationality, descr))


def wd_search_all_corpid_numbers():
    """
    """

    global exitstat

    querytxt = """# Get all Belgian corpID numbers
SELECT DISTINCT ?item WHERE {
  ?item wdt:P1320 ?corpID.
  FILTER(STRSTARTS(?corpID, "be/"))
  MINUS { ?item wdt:P3376 ?kbo_number. }
}

"""

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    errcount = 0	    	# Error counter
    errsleep = 0	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    if verbose:
        pywikibot.info('\nProcessing corpID-KBO statements')

    generator = pg.WikidataSPARQLPageGenerator(querytxt, site=repo)

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for item in generator:	# Main loop for all DISTINCT items

## alow removing conflicts
      if status != 'Stop':	# Ctrl-c pressed -> stop in a proper way

        transcount += 1	# New transaction
        valid_kbo = False
        status = 'Fail'
        alias = ''
        descr = ''
        commonscat = '' # Commons category
        nationality = ''
        label = ''
        kbo_number = ''

        try:			# Error trapping (prevents premature exit on transaction error)
            item = get_item_page(item.getID())
            qnumber = item.getID()

            if mainlang in item.labels:
                label = item.labels[mainlang]

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]

            if OPENCORPID in item.claims and KBONUMBER not in item.claims:   # Runtime check required (statement could have been deleted)
                for seq in item.claims[OPENCORPID]:        # Search for a valid Belgian enterprise number
                    kbo_number = seq.getTarget()

                    if ENDDTPROP in seq.qualifiers:        # Should not have an end-date
                        continue
                    elif CORPIDNUMRE.search(kbo_number):   # 10 digits
                        kbo_number = kbo_number[3:]
                        valid_kbo = True

                    if valid_kbo:           # Add missing Corporate ID
                        claim = pywikibot.Claim(repo, KBONUMBER)
                        claim.setTarget(kbo_number)
                        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                        status = 'Update'
                        break

            if CTRYPROP not in item.claims:                # Mandatory country BE, because having Belgian enterprise number
                claim = pywikibot.Claim(repo, CTRYPROP)
                claim.setTarget(pywikibot.ItemPage(repo, CTRYBELGIUM))
                item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.NoPageError as error:           # Item does not exist
            pywikibot.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.MaxlagTimeoutError as error:    # Attempt error recovery
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
            pywikibot.error(error)
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

        if verbose or status not in ['OK']:		# Print transaction results
            isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Only needed to format output
            totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
            pywikibot.info('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), kbo_number, label, commonscat, alias, nationality, descr))


def wd_search_all_vta_numbers():
    """
    """

    global exitstat

    querytxt = """# Get all Belgian TVA numbers
SELECT DISTINCT ?item WHERE {
  ?item wdt:P3608 ?TVAnr.
  FILTER(STRSTARTS(?TVAnr, "BE0"))
  MINUS { ?item wdt:P3376 ?kbo_number. }
}
"""

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    errcount = 0	    	# Error counter
    errsleep = 0	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    if verbose:
        pywikibot.info('\nProcessing TVA-KBO statements')

    generator = pg.WikidataSPARQLPageGenerator(querytxt, site=repo)

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for item in generator:	# Main loop for all DISTINCT items

## alow removing conflicts
      if status != 'Stop':	# Ctrl-c pressed -> stop in a proper way

        transcount += 1	# New transaction
        valid_kbo = False
        status = 'Fail'
        alias = ''
        descr = ''
        commonscat = '' # Commons category
        nationality = ''
        label = ''
        kbo_number = ''

        try:			# Error trapping (prevents premature exit on transaction error)
            item = get_item_page(item.getID())
            qnumber = item.getID()

            if mainlang in item.labels:
                label = item.labels[mainlang]

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]

            if TVANUMBER in item.claims and KBONUMBER not in item.claims:   # Runtime check required (statement could have been deleted)
                for seq in item.claims[TVANUMBER]:        # Search for a valid Belgian enterprise number
                    kbo_number = seq.getTarget()

                    if ENDDTPROP in seq.qualifiers:        # Should not have an end-date
                        continue
                    elif BETVANUMRE.search(kbo_number):   # 10 digits
                        kbo_number = kbo_number[2:]
                        valid_kbo = True

                    if valid_kbo:           # Add missing Corporate ID
                        claim = pywikibot.Claim(repo, KBONUMBER)
                        claim.setTarget(kbo_number)
                        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                        status = 'Update'
                        break

            if CTRYPROP not in item.claims:                # Mandatory country BE, because having Belgian enterprise number
                claim = pywikibot.Claim(repo, CTRYPROP)
                claim.setTarget(pywikibot.ItemPage(repo, CTRYBELGIUM))
                item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.NoPageError as error:           # Item does not exist
            pywikibot.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.MaxlagTimeoutError as error:    # Attempt error recovery
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
            pywikibot.error(error)
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

        if verbose or status not in ['OK']:		# Print transaction results
            isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Only needed to format output
            totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
            pywikibot.info('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), kbo_number, label, commonscat, alias, nationality, descr))


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
    global readonly
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter
    if debug:
        print('Parameter %s' % cpar)

    if cpar.startswith('-d'):	# debug mode
        debug = True
        print('Setting debug mode')
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
    elif cpar.startswith('-r'):	# readonly mode
        readonly = True
        print('Setting readonly mode')
    elif cpar.startswith('-v'):	# verbose mode
        verbose = True
        print('Setting verbose mode')
    elif cpar.startswith('-V'):	# Version
        show_prog_version()
    elif cpar.startswith('-'):	# unrecognized qualifier (fatal error)
        fatal_error(4, 'Unrecognized qualifier; use -h for help')
    return cpar		# Return the parameter or the qualifier to the caller


# Main program entry
# First identify the program

if verbose:
    show_prog_version()	    	# Print the module name

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    if debug:
        pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
except:
    shell = False
    pywikibot.info('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

HELPRE = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
KBONUMRE = re.compile(r'^0[0-9]{9}$')       # Belgian enterprise number
KBOLONGNUMRE = re.compile(r'^0[0-9]{3}\.[0-9]{3}\.[0-9]{3}$')       # Belgian enterprise number (long)
KBOSHORTNUMRE = re.compile(r'^[0-9]{9}$')       # Belgian enterprise number (short)
BETVANUMRE = re.compile(r'^BE0[0-9]{9}$')       # Belgian TVA number
CORPIDNUMRE = re.compile(r'^be/0[0-9]{9}$')       # Belgian TVA number
LANGRE = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes

inlang = '-'
while len(sys.argv) > 0 and inlang.startswith('-'):
    inlang = get_next_param().lower()

# Global parameters

# Default description language
main_languages = get_language_preferences()
mainlang = main_languages[0]

if LANGRE.search(inlang):
    mainlang = inlang

pywikibot.log('Main language:\t%s' % mainlang)
pywikibot.log('Maximum delay:\t%d s' % maxdelay)
pywikibot.log('Minimum success rate:\t%f%%' % minsucrate)
pywikibot.log('Verbose mode:\t%s' % verbose)
pywikibot.log('Debug mode:\t%s' % debug)
pywikibot.log('Readonly mode:\t%s' % readonly)
pywikibot.log('Exit on fatal error:\t%s' % exitfatal)
pywikibot.log('Error wait factor:\t%d' % errwaitfactor)

# Connect to database
transcmt = '#pwb Add kbo corpid'	    	    # Wikidata transaction comment
repo = pywikibot.Site('wikidata')      # Login to Wikibase instance

wd_search_all_vta_numbers()     # Search all VTA numbers
wd_proc_all_items()	            # Execute all items for one language
wd_search_all_corpid_numbers()  # Search all BE corpID numbers

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
