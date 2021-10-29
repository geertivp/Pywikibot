#!/usr/bin/python3

# The helptext is displayed with -h
codedoc = """
Add statements to a list of items.


Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Parameters:

    P1: Property
    P2: Value
    etc.

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
	2 Ctrl-c pressed, program interrupted
	3 Invalid or missing parameter
    20 General error

Documentation:

https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string

Author:

	Geert Van Pamel, 2021-01-30, GNU General Public License v3.0, User:Geertivp

"""


# List the required modules
import os               # Operating system: getenv
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)

import pywikibot		# API interface to Wikidata
from datetime import datetime	# now, strftime, delta time, total_seconds
from sortedcontainers import SortedDict

# Global technical parameters
modnm = 'Pywikibot add_statement'    # Module name (using the Pywikibot package)
pgmid = '2021-10-29 (gvp)'	         # Program ID and version

"""
    Static definitions
"""

# Functional configuration flags
# Restrictions: cannot disable both labels and wikipedia. We need at least one of the options.
usealias = True     # Allow using the language aliases (disable with -s)
fallback = True		# Allow for English fallback (could possibly be embarassing for local languages; disable with -t)
notability = True	# Notability requirements (disable with -n; this is not encouraged, unless for "no"-cleanup)
safemode = False	# Avoid label/description homonym conflicts (can be activated with -x when needed)
uselabels = True	# Use the language labels (disable with -l)
wikipedia = True	# Allow using Wikipedia article names (best, because Wikipedia is multilingual; disable with -w)

# Technical configuration flags
# Defaults: transparent and safe
debug = False		# Can be activated with -d (errors and configuration changes are always shown)
errorstat = True    # Show error statistics (disable with -e)
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
readonly = False    # Dry-run
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
    print(errtext)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        print('Proceed after fatal error')


def wd_proc_all_items():
    """
    """

    global exitstat

# Print preferences
    if verbose or debug:
        print('\nUse labels:\t%s' % uselabels)
        print('Avoid homonym:\t%s' % safemode)
        print('Use aliases:\t%s' % usealias)
        print('Fallback on English:\t%s' % fallback)
        print('Use Wikipedia:\t%s' % wikipedia)
        print('Notability:\t%s' % notability)

        print('\nShow code:\t%s' % showcode)
        print('Verbose mode:\t%s' % verbose)
        print('Debug mode:\t%s' % debug)
        print('Readonly mode:\t%s' % readonly)
        print('Exit on fatal error:\t%s' % exitfatal)
        print('Error wait factor:\t%d' % errwaitfactor)

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    statcount = 0           # Statement count
    notecount = 0	    	# Notability count
    pictcount = 0	    	# Picture count
    unotecount = 0	    	# Notability problem
    safecount = 0	    	# Safe transaction
    errcount = 0	    	# Error counter
    errsleep = 0	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    if verbose:
        print('\nProcessing statements')

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for qnumber in itemlist:	# Main loop for all DISTINCT items

## alow removing conflicts
      if status != 'Stop':	# Ctrl-c pressed -> stop in a proper way

        transcount += 1	# New transaction
        status = 'OK'
        alias = ''
        descr = ''
        commonscat = '' # Commons category
        nationality = ''
        label = ''

        try:			# Error trapping (prevents premature exit on transaction error)

            item = pywikibot.ItemPage(repo, qnumber)
            item.get(get_redirect = True)
            
            if mainlang in item.labels:
                label = item.labels[mainlang]
            else:
                status = 'Nolabel'

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]

# Get Commons category/creator
            if 'P373' in item.claims:       # Wikimedia Commons Category
                commonscat = item.claims['P373'][0].getTarget()
            elif 'P1472' in item.claims:    # Wikimedia Commons Creator
                commonscat = item.claims['P1472'][0].getTarget()

# Merge claims
            for propty in target:
                status = 'OK'
                if propty in item.claims:
                    for seq in item.claims[propty]:
                        val = seq.getTarget().getID()
                        if val == target[propty]:
                            status = 'Skip'
                            break

# Claim is missing, so add it now
                if status == 'OK':
                    claim = pywikibot.Claim(repo, propty)
                    claim.setTarget(pywikibot.ItemPage(repo, target[propty]))
                    item.addClaim(claim, bot=True, summary=transcmt)

        except KeyboardInterrupt:
            """
    Error handling section
            """

            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except Exception as error:           # Attempt error recovery
            print('Error updating %s,' % (qnumber), format(error))
            if exitfatal:           # Stop on first error
                raise
            status = 'Error'	    # Handle any generic error
            exitstat = max(exitstat, 20)
            deltasecs = int((datetime.now() - now).total_seconds())	# Calculate technical error penalty
            if deltasecs >= 30: 	# Technical error; for transactional errors there is no wait time increase
                errsleep += errwaitfactor * min(maxdelay, deltasecs)
                # Technical errors get additional penalty wait
				# Consecutive technical errors accumulate the wait time, until the first successful transaction
				# We limit the delay to a multitude of maxdelay seconds
            if errsleep > 0:    	# Allow the servers to catch up; slowdown the transaction rate
                print('%d seconds maxlag wait' % errsleep)
                time.sleep(errsleep)

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
            print('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), label, commonscat, alias, nationality, descr))


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
    global fallback
    global notability
    global readonly
    global safemode
    global usealias
    global uselabels
    global verbose
    global wikipedia

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
    elif cpar.startswith('-l'):	# language labels
        if not wikipedia:
            fatal_error(4, 'Conflicting qualifiers -l -w')
        uselabels = False
        print('Disable label reuse')
    elif cpar.startswith('-m'):	# fast mode
        errwaitfactor = 1
        print('Setting fast mode')
    elif cpar.startswith('-n'):	# notability
        notability = False
        print('Disable notability mode')
    elif cpar.startswith('-p'):	# proceed after fatal error
        exitfatal = False
        print('Setting proceed after fatal error')
    elif cpar.startswith('-q'):	# quiet mode
        verbose = False
        print('Setting quiet mode')
    elif cpar.startswith('-r'):	# readonly mode
        readonly = True
        print('Setting readonly mode')
    elif cpar.startswith('-s'):	# alias (synonym) usage
        usealias = False
        print('Disable alias reuse')
    elif cpar.startswith('-t'):	# translation required (no English)
        fallback = False
        print('Disable translation fallback')
    elif cpar.startswith('-v'):	# verbose mode
        verbose = True
        print('Setting verbose mode')
    elif cpar.startswith('-V'):	# Version
        show_prog_version()
    elif cpar.startswith('-w'):	# disallow Wikipedia
        if not uselabels:
            fatal_error(4, 'Conflicting qualifiers -l -w')
        wikipedia = False
        print('Disable Wikipedia reuse')
    elif cpar.startswith('-x'):	# safe mode
        safemode = True
        print('Setting safe mode')
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
        print('%s version %s' % (pgmnm, pgmid)) # Physical program
except:
    shell = False
    print('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

helpre = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+\n')  # Help text
humsqlre = re.compile(r'\s*#.*\n')          # Human readable query, remove all comments including LF
comsqlre = re.compile(r'\s+')		        # Computer readable query, remove duplicate whitespace
urlbre = re.compile(r'[^\[\]]+')	        # Remove URL square brackets (keep the article page name)
suffre = re.compile(r'\s*[(]')		        # Remove () and , suffix (keep only the base label)
langre = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes
sitelinkre = re.compile(r'^[a-z]{2,3}wiki$')        # Verify for valid Wikipedia language codes
romanre = re.compile(r'^[a-z ."\'åáàâăäãāæǣčçéèêěëēíìîïłñņóòôöőðøšßúùûüữủýž-]{2,}$', flags=re.IGNORECASE)  # Roman alphabet
propre = re.compile(r'P[0-9]+')             # P-number
qsuffre = re.compile(r'Q[0-9]+')             # Q-number

inpar = '-'
while len(sys.argv) > 0 and inpar.startswith('-'):
    inpar = get_next_param().upper()

# Global parameters
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
    
if verbose or debug:
    print('Main language:\t%s' % mainlang)
    print('Maximum delay:\t%d s' % maxdelay)
    print('Minimum success rate:\t%f%%' % minsucrate)

# Get list of item numbers
inputfile = sys.stdin.read()
itemlist = sorted(set(qsuffre.findall(inputfile)))
if debug:
    print(itemlist)

# Connect to database
transcmt = 'Pwb add statement'	    	    # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()

# Get all claims from parameter list
target=SortedDict()
while len(sys.argv) > 1:
    inpar = propre.findall(inpar.upper())[0]
    target.setdefault(inpar, qsuffre.findall(sys.argv.pop(0).upper())[0])
    inpar = sys.argv.pop(0)

inpar = propre.findall(inpar.upper())[0]
target.setdefault(inpar, qsuffre.findall(sys.argv.pop(0).upper())[0])

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

# Einde van de miserie
"""



"""