#!/usr/bin/python3

# The helptext is displayed with -h
codedoc = """
Add an alias.

Parameters:

    stdin: list of Q-numbers and aliases separated by commas

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
	2 Ctrl-c pressed, program interrupted
	3 Invalid or missing parameter
    20 General error

Author:

	Geert Van Pamel, 2021-01-23, GNU General Public License v3.0, User:Geertivp

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string

Known problems:

"""

# List the required modules
import logging          # Error logging
import os               # Operating system: getenv
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)

import pywikibot		# API interface to Wikidata
from datetime import datetime	# now, strftime, delta time, total_seconds
from pywikibot.data import api

# Global technical parameters
modnm = 'Pywikibot add_alias'   # Module name (using the Pywikibot package)
pgmid = '2021-12-01 (gvp)'	    # Program ID and version

"""
    Static definitions
"""

# Functional configuration flags

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
    logger.error(errtext)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        logger.error('Proceed after fatal error')


def get_canon_name(baselabel):
# Get standardised name:
#   remove () suffix
#   reverse , name parts

    suffix = suffre.search(baselabel)  	        # Remove () suffix, if any
    if suffix:
        baselabel = baselabel[:suffix.start()]  # Get canonical form

    colonloc = baselabel.find(':')
    commaloc = namerevre.search(baselabel)
    if colonloc < 0 and commaloc:          # Reorder "lastname, firstname" and concatenate with space
        baselabel = baselabel[commaloc.start() + 1:].strip() + ' ' + baselabel[:commaloc.start()].strip()
    return baselabel


def wd_proc_all_items():
    """
    """

    global exitstat

# Print preferences
    if verbose or debug:
        print('Verbose mode:\t%s' % verbose)
        print('Debug mode:\t%s' % debug)
        print('Exit on fatal error:\t%s' % exitfatal)
        print('Error wait factor:\t%d' % errwaitfactor)

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    statcount = 0           # Statement count
    pictcount = 0	    	# Picture count
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
    for newitem in itemlist:	# Main loop for all DISTINCT items
      print(newitem)
      name = newitem.split(',')
      print(name)
## alow removing conflicts
      if newitem != '' and status != 'Stop':	# Ctrl-c pressed -> stop in a proper way

        qnumber = name[0]
        del name[0]
        transcount += 1	# New transaction
        status = 'OK'
        label = ''
        origlabel = ''
        alias = {}
        if name:
            alias = {'nl': name, 'de': name, 'en': name, 'es': name, 'fr': name, 'it': name}
        descr = ''
        commonscat = '' # Commons category
        nationality = ''

        try:			# Error trapping (prevents premature exit on transaction error)

            item = pywikibot.ItemPage(repo, qnumber)
            item.get(get_redirect = True)

            if mainlang in item.labels:
                origlabel = item.labels[mainlang]
                if romanre.search(origlabel) and ('P282' not in item.claims or item.claims['P282'][0].getTarget().getID() == 'Q8229'):
                    label = get_canon_name(origlabel)
                else:
                    status = 'No label'     # Foreign character set (non-Latin script)
            else:
                status = 'No label'     # Foreign character set (non-Latin script)

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]
            elif 'en' in item.descriptions:
                descr = item.descriptions['en']

# Get Commons category/creator
            if 'P373' in item.claims:       # Wikimedia Commons Category
                commonscat = item.claims['P373'][0].getTarget()
            elif 'P1472' in item.claims:    # Wikimedia Commons Creator
                commonscat = item.claims['P1472'][0].getTarget()

            for seq in name:
                if seq != '':
# (1) Merge aliases having labels
                    for lang in item.labels:
                        # Skip non-Roman languages
                        if romanre.search(item.labels[lang]):
                            # Add aliases
                            if seq != item.labels[lang]:
                                if lang not in item.aliases:
                                    item.aliases[lang] = [seq]
                                elif seq not in item.aliases[lang]:
                                    item.aliases[lang].append(seq)

# (2) Merge aliases having descriptions
                    for lang in item.descriptions:
                        # Skip non-Roman languages
                        if romanre.search(item.descriptions[lang]):
                            # Add aliases
                            if lang not in item.labels or seq != item.labels[lang]:
                                if lang not in item.aliases:
                                    item.aliases[lang] = [seq]
                                elif seq not in item.aliases[lang]:
                                    item.aliases[lang].append(seq)

# (3) Merge missing aliases
                    for lang in item.aliases:
                        if lang not in item.labels or seq != item.labels[lang]:
                            if seq not in item.aliases[lang]:
                                item.aliases[lang].append(seq)

# (4) Merge missing aliases
                    for lang in alias:
                        if lang not in item.labels or seq != item.labels[lang]:
                            if lang not in item.aliases:
                                item.aliases[lang] = [seq]
                            elif seq not in item.aliases[lang]:
                                item.aliases[lang].append(seq)

# (5) Remove duplicate aliases
            for lang in item.labels:
                if lang in item.aliases:
                    while item.labels[lang] in item.aliases[lang]:  # Remove redundant aliases
                        item.aliases[lang].remove(item.labels[lang])

# (5) Now store the changes
            item.editEntity( {'labels': item.labels, 'aliases': item.aliases}, summary=transcmt)

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]
            elif 'en' in item.aliases:
                alias  = item.aliases['en']

# (6) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.NoPageError as error:        # This works
            logger.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.MaxlagTimeoutError as error:  # Attempt error recovery
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
            logger.error('Error processing %s, %s' % (qnumber, error))
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
            print('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), origlabel, commonscat, alias, nationality, descr))


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
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter
    if debug:
        print('Parameter %s' % cpar)

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
# First identify the program
logger = logging.getLogger('add_alias')

if verbose:
    show_prog_version()	    	# Print the module name

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    if debug:
        print('%s version %s' % (pgmnm, pgmid)) # Physical program
except:
    shell = False
    logger.error('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

comsqlre = re.compile(r'\s+')		        # Computer readable query, remove duplicate whitespace
helpre = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
humsqlre = re.compile(r'\s*#.*\n')          # Human readable query, remove all comments including LF
langre = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes
namerevre = re.compile(r',(\s*[A-Z][a-z]+)+$')	# Reverse lastname, firstname
qsuffre = re.compile(r'Q[0-9]+')             # Q-number
romanre = re.compile(r'^[a-z .,"()\'åáàâǎăäãāąæǣćčçéèêěĕëēėęəģǧğġíìîïīłńñňņóòôöőõōðœøřśšşșßțúùûüữủūůűýÿžż-]{2,}$', flags=re.IGNORECASE)  # Roman alphabet
sitelinkre = re.compile(r'^[a-z]{2,3}wiki$')        # Verify for valid Wikipedia language codes
suffre = re.compile(r'\s*[(].*[)]$')		# Remove trailing () suffix (keep only the base label)
urlbre = re.compile(r'[^\[\]]+')	        # Remove URL square brackets (keep the article page name)

outlang = '-'
while len(sys.argv) > 0 and outlang.startswith('-'):
    outlang = get_next_param().lower()

# Global parameters
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
if verbose or debug:
    print('Main language:\t%s' % mainlang)
    print('Maximum delay:\t%d s' % maxdelay)
    print('Minimum success rate:\t%f%%' % minsucrate)

# Get list of item numbers
inputfile = sys.stdin.read()
itemlist = sorted(set(inputfile.split('\n')))
if debug:
    print(itemlist)

# Connect to database
transcmt = 'Pwb add alias'	    	    # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()

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