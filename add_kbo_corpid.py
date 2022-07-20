#!/usr/bin/python3

# The helptext is displayed with -h
codedoc = """
Add a missing Corporate Id based on the KBO enterprise number.

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
	2 Ctrl-c pressed, program interrupted
	3 Invalid or missing parameter
    12 Item does not exist
    20 General error

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
import logging          # Error logging
import os               # Operating system: getenv
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)
import pywikibot		# API interface to Wikidata
from datetime import datetime	    # now, strftime, delta time, total_seconds
from pywikibot import pagegenerators as pg # Wikidata Query interface

# Global technical parameters
modnm = 'Pywikibot add_kbo_corpid'  # Module name (using the Pywikibot package)
pgmid = '2022-06-21 (gvp)'	        # Program ID and version

"""
    Static definitions
"""

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


def fatal_error(errcode, errtext):
    """
    A fatal error has occurred; we will print the error messaga, and exit with an error code
    """
    global exitstat

    exitstat = max(exitstat, errcode)
    logger.critical(errtext)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        logger.error('Proceed after fatal error')


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
        print('\nProcessing KBO statements')

    generator = pg.WikidataSPARQLPageGenerator(querytxt, site=wikidata_site)

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for item in generator:	# Main loop for all DISTINCT items

## alow removing conflicts
      if status != 'Stop':	# Ctrl-c pressed -> stop in a proper way

        transcount += 1	# New transaction
        status = 'Fail'
        alias = ''
        descr = ''
        commonscat = '' # Commons category
        nationality = ''
        label = ''

        try:			# Error trapping (prevents premature exit on transaction error)
            item.get(get_redirect=True)
            
            if mainlang in item.labels:
                label = item.labels[mainlang]

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]

            if 'P3376' in item.claims and 'P1320' not in item.claims:   # Runtime check required (statement could have been deleted)
                for seq in item.claims['P3376']:        # Search for a valid Belgian enterprise number
                    kbo_number = seq.getTarget()

                    valid_kbo = False
                    if 'P582' in seq.qualifiers:        # Should not have an end-date
                        continue
                    elif kbonumre.search(kbo_number):   # 10 digits
                        valid_kbo = True
                    elif kbosnumre.search(kbo_number):  # 9 digits getting leading 0
                        kbo_number = '0' + kbo_number
                        valid_kbo = True
                        
                        claim = pywikibot.Claim(repo, 'P3376')   # Fix the 10-digit format
                        claim.setTarget(kbo_number)
                        item.addClaim(claim, bot=True, summary=transcmt)
                        item.removeClaims(seq, bot=True, summary=transcmt)
                    elif kbolnumre.search(kbo_number):  # 3x3 digits with dots
                        kbo_number = kbo_number[0:4] + kbo_number[5:8] + kbo_number[9:12]
                        valid_kbo = True
                        
                        claim = pywikibot.Claim(repo, 'P3376')   # Fix the 10-digit format
                        claim.setTarget(kbo_number)
                        item.addClaim(claim, bot=True, summary=transcmt)
                        item.removeClaims(seq, bot=True, summary=transcmt)

                    if valid_kbo:           # Add missing Corporate ID
                        claim = pywikibot.Claim(repo, 'P1320')
                        claim.setTarget('be/' + kbo_number)
                        item.addClaim(claim, bot=True, summary=transcmt)
                        status = 'Update'
                        break

            if 'P17' not in item.claims:                # Mandatory country BE, because having Belgian enterprise number
                claim = pywikibot.Claim(repo, 'P17')
                claim.setTarget(pywikibot.ItemPage(repo, 'Q31'))
                item.addClaim(claim, bot=True, summary=transcmt)

        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.NoPageError as error:           # Item does not exist
            logger.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.MaxlagTimeoutError as error:    # Attempt error recovery
            logger.error('Error updating %s, %s' % (qnumber, error))
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
                logger.error('%d seconds maxlag wait' % (errsleep))
                time.sleep(errsleep)

        except Exception as error:  # other exception to be used
            logger.error(error)
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
            print('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), kbo_number, label, commonscat, alias, nationality, descr))


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
        print('\nProcessing corpID statements')

    generator = pg.WikidataSPARQLPageGenerator(querytxt, site=wikidata_site)

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for item in generator:	# Main loop for all DISTINCT items

## alow removing conflicts
      if status != 'Stop':	# Ctrl-c pressed -> stop in a proper way

        transcount += 1	# New transaction
        status = 'Fail'
        alias = ''
        descr = ''
        commonscat = '' # Commons category
        nationality = ''
        label = ''

        try:			# Error trapping (prevents premature exit on transaction error)
            item.get(get_redirect=True)
            
            if mainlang in item.labels:
                label = item.labels[mainlang]

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]

            if 'P1320' in item.claims and 'P3376' not in item.claims:   # Runtime check required (statement could have been deleted)
                for seq in item.claims['P1320']:        # Search for a valid Belgian enterprise number
                    kbo_number = seq.getTarget()

                    valid_kbo = False
                    if 'P582' in seq.qualifiers:        # Should not have an end-date
                        continue
                    elif corpidnumre.search(kbo_number):   # 10 digits
                        kbo_number = kbo_number[3:]
                        valid_kbo = True

                    if valid_kbo:           # Add missing Corporate ID
                        claim = pywikibot.Claim(repo, 'P3376')
                        claim.setTarget(kbo_number)
                        item.addClaim(claim, bot=True, summary=transcmt)
                        status = 'Update'
                        break

            if 'P17' not in item.claims:                # Mandatory country BE, because having Belgian enterprise number
                claim = pywikibot.Claim(repo, 'P17')
                claim.setTarget(pywikibot.ItemPage(repo, 'Q31'))
                item.addClaim(claim, bot=True, summary=transcmt)

        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.NoPageError as error:           # Item does not exist
            logger.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.MaxlagTimeoutError as error:    # Attempt error recovery
            logger.error('Error updating %s, %s' % (qnumber, error))
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
                logger.error('%d seconds maxlag wait' % (errsleep))
                time.sleep(errsleep)

        except Exception as error:  # other exception to be used
            logger.error(error)
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
            print('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), kbo_number, label, commonscat, alias, nationality, descr))


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
        print('\nProcessing TVA statements')

    generator = pg.WikidataSPARQLPageGenerator(querytxt, site=wikidata_site)

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for item in generator:	# Main loop for all DISTINCT items

## alow removing conflicts
      if status != 'Stop':	# Ctrl-c pressed -> stop in a proper way

        transcount += 1	# New transaction
        status = 'Fail'
        alias = ''
        descr = ''
        commonscat = '' # Commons category
        nationality = ''
        label = ''

        try:			# Error trapping (prevents premature exit on transaction error)
            item.get(get_redirect=True)
            
            if mainlang in item.labels:
                label = item.labels[mainlang]

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]

            if 'P3608' in item.claims and 'P3376' not in item.claims:   # Runtime check required (statement could have been deleted)
                for seq in item.claims['P3608']:        # Search for a valid Belgian enterprise number
                    kbo_number = seq.getTarget()

                    valid_kbo = False
                    if 'P582' in seq.qualifiers:        # Should not have an end-date
                        continue
                    elif betvanumre.search(kbo_number):   # 10 digits
                        kbo_number = kbo_number[2:]
                        valid_kbo = True

                    if valid_kbo:           # Add missing Corporate ID
                        claim = pywikibot.Claim(repo, 'P3376')
                        claim.setTarget(kbo_number)
                        item.addClaim(claim, bot=True, summary=transcmt)
                        status = 'Update'
                        break

            if 'P17' not in item.claims:                # Mandatory country BE, because having Belgian enterprise number
                claim = pywikibot.Claim(repo, 'P17')
                claim.setTarget(pywikibot.ItemPage(repo, 'Q31'))
                item.addClaim(claim, bot=True, summary=transcmt)

        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.NoPageError as error:           # Item does not exist
            logger.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.MaxlagTimeoutError as error:    # Attempt error recovery
            logger.error('Error updating %s, %s' % (qnumber, error))
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
                logger.error('%d seconds maxlag wait' % (errsleep))
                time.sleep(errsleep)

        except Exception as error:  # other exception to be used
            logger.error(error)
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
            print('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), kbo_number, label, commonscat, alias, nationality, descr))


def show_help_text():
# Show program help and exit (only show head text)
    helptxt = helpre.search(codedoc)
    if helptxt:
        print(helptxt.group(0))	# Show helptext
    sys.exit(1)         # Must stop


def show_prog_version():
# Show program version
    print('%s version %s' % (modnm, pgmid))


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
logger = logging.getLogger('add_kbo_corpid')

if verbose:
    show_prog_version()	    	# Print the module name

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    if debug:
        print('%s version %s' % (pgmnm, pgmid)) # Physical program
except:
    shell = False
    print('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

helpre = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
kbonumre = re.compile(r'^0[0-9]{9}$')       # Belgian enterprise number
kbolnumre = re.compile(r'^0[0-9]{3}\.[0-9]{3}\.[0-9]{3}$')       # Belgian enterprise number (long)
kbosnumre = re.compile(r'^[0-9]{9}$')       # Belgian enterprise number (short)
betvanumre = re.compile(r'^BE0[0-9]{9}$')       # Belgian TVA number
corpidnumre = re.compile(r'^be/0[0-9]{9}$')       # Belgian TVA number
langre = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes

inlang = '-'
while len(sys.argv) > 0 and inlang.startswith('-'):
    inlang = get_next_param().lower()

# Global parameters
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
if langre.search(inlang):
    mainlang = inlang
    
if verbose or debug:
    print('Main language:\t%s' % mainlang)
    print('Maximum delay:\t%d s' % maxdelay)
    print('Minimum success rate:\t%f%%' % minsucrate)
    print('Verbose mode:\t%s' % verbose)
    print('Debug mode:\t%s' % debug)
    print('Readonly mode:\t%s' % readonly)
    print('Exit on fatal error:\t%s' % exitfatal)
    print('Error wait factor:\t%d' % errwaitfactor)

# Connect to database
transcmt = '#pwb Add kbo corpid'	    	    # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()

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

# Einde van de miserie
"""


"""
