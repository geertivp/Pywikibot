#!/usr/bin/python3

# The helptext is displayed with -h
codedoc = """
Update a property.

Return status:

    The following status is returned to the shell:

    0 Normal termination
    1 Help requested (-h)
    2 Ctrl-c pressed, program interrupted
    3 Invalid or missing parameter
    20 General error

Author:

	Geert Van Pamel, 2021-03-27, GNU General Public License v3.0, User:Geertivp

Documentation:

    https://www.mediawiki.org/wiki/Manual:Pywikibot/Wikidata
    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb

"""

# List the required modules
import logging          # Error logging
import os               # Operating system: getenv
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import unidecode        # Unicode
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)
import pywikibot		# API interface to Wikidata
from datetime import datetime	    # now, strftime, delta time, total_seconds

# Global technical parameters
modnm = 'Pywikibot update_property' # Module name (using the Pywikibot package)
pgmid = '2022-03-27 (gvp)'	        # Program ID and version

"""
    Static definitions
"""

# Functional configuration flags

# Technical configuration flags
# Defaults: transparent and safe
debug = False		# Can be activated with -d (errors and configuration changes are always shown)
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
minsucrate = 70.0   # Minimum success rate per target language (the script is stopped below this threshold)

main_languages = ['nl', 'fr', 'en', 'de', 'es', 'it']
veto_languages = {'el', 'th'}     # Languages that are not updated (to avoid anomalies)

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
    logger.error(errtext)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        logger.error('Proceed after fatal error')


def wd_proc_all_properties():
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
    if verbose:
        print('\nProcessing %d statements' % (len(proptylist)), file=sys.stderr)

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all properties in the list
    for pnumber in proptylist:	# Main loop for all DISTINCT properties
      if status == 'Stop':	# Ctrl-c pressed -> stop in a proper way
        break

      if pnumber > 'P':
        logger.debug(pnumber)
        transcount += 1	# New transaction
        status = 'OK'
        label = ''
        alias = ''
        descr = ''

        try:			    # Error trapping (prevents premature exit on transaction error)
            propty = pywikibot.PropertyPage(repo, pnumber)
            propty.get()

            for lang in main_languages:
                if lang in propty.labels:
                    label = propty.labels[lang]
                    break

            for lang in main_languages:
                if lang in propty.descriptions:
                    descr = propty.descriptions[lang]
                    break

            for lang in main_languages:
                if lang in propty.aliases:
                    alias = propty.aliases[lang][0]
                    break

# (3) Remove duplicate aliases
            for lang in propty.labels:
                if lang not in veto_languages and lang in propty.aliases:   # Avoid anomalies
                    while propty.labels[lang] in propty.aliases[lang]:      # Remove redundant aliases
                        propty.aliases[lang].remove(propty.labels[lang])

# (4) Now store the changes
            propty.editAliases( propty.aliases, summary=transcmt)

# Update reverse property labels
            if 'P7087' in propty.claims:
                item = propty.claims['P7087'][0].getTarget()
                logger.error('Updating %s' % (item.getID()))
                for lang in propty.labels:          # Merge labels
                    if lang not in item.labels:
                        item.labels[lang] = propty.labels[lang]
                    elif unidecode.unidecode(propty.labels[lang].lower()) == unidecode.unidecode(item.labels[lang].lower()):    # Ignore accents
                        pass
                    elif lang not in item.aliases:
                        item.aliases[lang] = [propty.labels[lang]]
                    elif propty.labels[lang] not in item.aliases[lang]:
                        item.aliases[lang].append(propty.labels[lang])

                for lang in item.labels:    # Remove redundant aliases
                    if lang in item.aliases:
                        while item.labels[lang] in item.aliases[lang]:
                            item.aliases[lang].remove(item.labels[lang])

                item.editEntity( {'labels': item.labels, 'aliases': item.aliases}, summary=transcmt)

        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.NoPageError as error:        # This works
            logger.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.MaxlagTimeoutError as error:  # Attempt error recovery
            logger.error('Error updating %s, %s' % (pnumber, error))
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
    We will report the results here, as much as we can, one line per propty.
        """

# Get the elapsed time in seconds and the timestamp in string format
        prevnow = now	        	# Transaction status reporting
        now = datetime.now()	    # Refresh the timestamp to time the following transaction

        if verbose or status not in ['OK']:		# Print transaction results
            isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Only needed to format output
            totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
            print('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, pnumber, label, alias, descr))


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

    global showcode
    global debug
    global errwaitfactor
    global exitfatal
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter
    if debug:
        print('Parameter %s' % cpar)

    if cpar.startswith('-c'):	# code check
        showcode = True
        print('Show generated code')
    elif cpar.startswith('-d'):	# debug mode
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
logger = logging.getLogger('update_property')

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
humsqlre = re.compile(r'\s*#.*\n')          # Human readable query, remove all comments including LF
comsqlre = re.compile(r'\s+')		        # Computer readable query, remove duplicate whitespace
urlbre = re.compile(r'[^\[\]]+')	        # Remove URL square brackets (keep the article page name)
suffre = re.compile(r'\s*[(]')		        # Remove () and , suffix (keep only the base label)
langre = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes
propre = re.compile(r'P[0-9]+')             # P-number
qsuffre = re.compile(r'Q[0-9]+')            # Q-number

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
    print('Show code:\t%s' % showcode)
    print('Verbose mode:\t%s' % verbose)
    print('Debug mode:\t%s' % debug)
    print('Exit on fatal error:\t%s' % exitfatal)
    print('Error wait factor:\t%d' % errwaitfactor)

# Get list of propty numbers
inputfile = sys.stdin.read()
proptylist = sorted(set(propre.findall(inputfile)))
if debug:
    print(proptylist)

# Connect to database
transcmt = 'Pwb update property'	    	    # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()

wd_proc_all_properties()	# Execute all properties for one language

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

"""



"""
# Einde van de miserie
