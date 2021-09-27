#!/usr/bin/python3

# This helptext is displayed with -h
codedoc = """
copy_label.py - Copy a Wikikdata language label to other languages. Quite some logic is contained in this script.

Wikipedia site links are merged as aliases.
Unregistered Wikipedia site links for which there exist language labels are added to Wikidata.
"Not-equal to" statements are generated when there are homonyms detected.
Reflexive "Not-equal to" statements are removed.
Norwegian language mismatches are fixed (no-nb language mapping mismatch betweek Wikipedia and Wikidata).
Person's native language and languages used are completed.
Redundant aliases are removed.
Aliases for which there is no label are moved to label.
Unrecognized Unicodes are not processed.
Automatic case matching (language specific first captital handling like e.g. in German).
Non-western encoded languages are skipped (but Wikipedia sitelinks are processed).

Parameters:

    P1: source language code (default LANG environment variable)
    P2... additional languages for site-link check and label replication
        Take care to only include Western (Roman) languages.

    stdin: list of Q-numbers to process (extracted via regular expression; duplicates and bad instances are removed)

Flags:

    -c	Force copy (ignore instance validation restriction)
    -d	Debug mode
    -h	Show help
    -l	Disable language labels update
    -p 	Proceed after error
    -q	Quiet mode

Filters:

    Some non-Western languages are "blacklisted" to avoid erronuous updates.

    The following Q-numbers are ignored:

        Duplicate Q-numbers
        Bad instances (only Q5 and related are accepted)
        Having non-roman language labels or descriptions

Notes:

    This tool can process more items than inititially provided (add sitelink "not equal to" homonym error handling and recursive logic).

Return status:

    The following status codes are returned to the shell:

    0 Normal termination
    1 Help requested (-h)
    2 Ctrl-c pressed, program interrupted
    3 Invalid or missing parameter
    10 Homonym
    11 Redirect
    12 Item does not exist
    13 Homonym (label)
    20 General error (Maxlag error, network error)

Error handling:

    This script should normally not stack dump, unless a severe (network) error happens.
    Any error will be reflected into the return status.
    It has intelligent error handling with self-healing code when possible.
    Wikidata run-time errors and timeouts are properly handled and resported.
    Processing typically continues after 60s retry/timeout.
    Data quality ensurance:
        It does not create duplicate statements.
        It does not create contradictory statements.
        It does not break constraints.

Volume processing:

    For high volumes a Bot account is required; the maximum speed is 1 transaction/second.
    The Wikidata user is responsible to adhere to:
        https://www.wikidata.org/wiki/Wikidata:Bots
        https://www.wikidata.org/wiki/Wikidata:Creating_a_bot
        https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py

Responsibilities:

    The person running this script is sole responsible for any erronuous updates the script is performing.
    This script is offered to the user as best-effort.
    The author does not accept any responsibility for any bugs in the script.
    Bugs should be reported to the author, in order to ameliorate the script.

Author:

	Geert Van Pamel, 2021-01-30, GNU General Public License v3.0, User:Geertivp

Documentation:

https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
https://www.mediawiki.org/wiki/Wikibase/API
https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string

Known problems:

    WARNING: API error failed-save: The save has failed.

        1/ There already exist a Wikipedia article with the same name linked to another item.
        This automatically adds a missing "not equal to" statement https://www.wikidata.org/wiki/Property:P1889

        2/ There exist another language label with an identical description.

Example query to replicate person names:

    This script has as stdin (standard input) a list of Q-numbers (which are obtained via a regular expression).

    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31 wd:Q5;
        wdt:P27 wd:Q31; # Q29999
        rdfs:label ?itemLabel.
      FILTER((LANG(?itemLabel)) = "nl")
      MINUS {
        ?item rdfs:label ?lang_label.
        FILTER((LANG(?lang_label)) = "da")
      }
    }
    ORDER BY (?itemLabel)

    # Uses 50% less elaapsed time
    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31 wd:Q5;
        wdt:P27 wd:Q29999;
        rdfs:label ?itemLabel.
      FILTER((LANG(?itemLabel)) = "nl")
      FILTER(NOT EXISTS {
        ?item rdfs:label ?lang_label.
        FILTER(LANG(?lang_label) = "da")
      })
    }
    ORDER BY (?itemLabel)

    # Get all items linked to WMBE WikiProjects that have missing labels
    SELECT distinct ?item WHERE {
      ?item wdt:P31 wd:Q5;
        wdt:P6104 ?wikiproject.
      ?wikiproject wdt:P31 wd:Q16695773;
        wdt:P664 wd:Q18398868.
      MINUS {
        ?item rdfs:label ?label.
        FILTER((LANG(?label)) = "da")
      }
    }

    SELECT DISTINCT ?item ?itemLabel WHERE {
      ?item wdt:P31 wd:Q5;
        rdfs:label ?itemLabel;
        wdt:P6104 ?wikiproject.
      FILTER((LANG(?itemLabel)) = "nl")
      MINUS {
        ?item rdfs:label ?label.
        FILTER((LANG(?label)) = "da")
      }
    }
    ORDER BY (?itemLabel)

"""

# List the required modules
import os               # Operating system: getenv
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)

import pywikibot		# API interface to Wikidata
from datetime import datetime	    # now, strftime, delta time, total_seconds

# Global technical parameters
modnm = 'Pywikibot copy_label'      # Module name (using the Pywikibot package)
pgmid = '2021-09-22 (gvp)'	        # Program ID and version

"""
    Static definitions
"""

# Functional configuration flags
# Restrictions: cannot disable both labels and wikipedia. We need at least one of the options.
usealias = True         # Allow using the language aliases (disable with -s)
fallback = True		    # Allow for English fallback (could possibly be embarassing for local languages; disable with -t)
notability = True	    # Notability requirements (disable with -n; this is not encouraged, unless for "no"-cleanup)
safemode = False	    # Avoid label/description homonym conflicts (can be activated with -x when needed)
uselabels = True	    # Use the language labels (disable with -l)
wikipedia = True	    # Allow using Wikipedia article names (best, because Wikipedia is multilingual; disable with -w)

# Technical configuration flags
# Defaults: transparent and safe
debug = False		    # Can be activated with -d (errors and configuration changes are always shown)
errorstat = True        # Show error statistics (disable with -e)
exitfatal = True	    # Exit on fatal error (can be disabled with -p; please take care)
readonly = False        # Dry-run
shell = True		    # Shell available (command line parameters are available; automatically overruled by PAWS)
forcecopy = False	    # Force copy
verbose = True	    	# Can be set with -q or -v (better keep verbose to monitor the bot progress)

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

# Language settings

all_languages = ['ast', 'ca', 'cy', 'da', 'de', 'en', 'es', 'fi', 'fr', 'ga', 'it', 'nb', 'nl', 'pt', 'pt-br', 'ro', 'sc', 'sq', 'sv']  # Add labels
upper_pref_lang = ['an', 'atj', 'bar', 'bjn', 'co', 'crh', 'de', 'de-ch', 'ext', 'frp', 'gcr', 'gsw', 'kab', 'ksh', 'lb', 'lg', 'lld', 'lt', 'mwl', 'nan', 'nds', 'nds-nl', 'pfl', 'rmy', 'rup', 'sgs', 'shi', 'tum', 'vec', 'vro', 'zu' ]      # Languages using uppercase nouns
new_wikis = ['altwiki', 'arywiki', 'avkwiki', 'lldwiki', 'madwiki', 'mniwiki', 'shiwiki', 'skrwiki', 'taywiki']       # Not yet described as Wikipedia family (skip)
veto_languages = ['vep']    # Skip non-standard encoding; see also romanre

# To be set in user-config.py (what parameters is PAWS using?)
"""
    maxthrottle = 60    # ?
    put_throttle = 1    # maximum transaction speed (bot account required)
    noisysleep = 60.0   # avoid the majority/all of the confusing sleep messages (noisy sleep)
    maxlag = 5          # avoid overloading the servers
    max_retries = 4     # avoid overloading the servers
    retry_wait = 30     # avoid overloading the servers
    retry_max = 320     # avoid overloading the servers
"""


def fatal_error(errcode, errtext):
    """
    A fatal error has occurred; we will print the error messaga, and exit with an error code.
    If really needed you could use the -p flag to force continue processing (not advised).
    """
    global exitstat

    exitstat = max(exitstat, errcode)
    print(errtext, file=sys.stderr)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        print('Proceed after fatal error', file=sys.stderr)


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
        Module logic
    """

    global exitstat

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    statcount = 0           # Statement count
    notecount = 0	    	# Notability count
    pictcount = 0	    	# Picture count
    unotecount = 0	    	# Notability problem
    safecount = 0	    	# Safe transaction
    errcount = 0	    	# Error counter
    errsleep = 0	    	# Technical error penalty (sleep delay in seconds)
    hdone = []              # Avoid recursion loops

# Avoid that the user is waiting for a response while the data is being queried
    if verbose:
        print('\nProcessing %d statements' % (len(itemlist)), file=sys.stderr)

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for qnumber in itemlist:	# Main loop for all DISTINCT items
      hdone.append(qnumber)

## alow removing conflicts
      if status == 'Stop':	# Ctrl-c pressed -> stop in a proper way
        break

      if qnumber > '':      # Allows a restart
        transcount += 1 	# New transaction
        status = 'OK'
        alias = ''
        descr = ''
        commonscat = ''     # Commons category
        nationality = ''
        label = ''
        origlabel = ''
        birthday = ''
        deathday = ''

        try:		    	# Error trapping (prevents premature exit on transaction error)
            item = pywikibot.ItemPage(repo, qnumber)
            item.get(get_redirect=True)

            try:                        # Instance type could be missing
                inst = item.claims['P31'][0].getTarget().getID()
            except:
                inst = ''

            if mainlang in item.labels:
                origlabel = item.labels[mainlang]
                while len(origlabel) > 0 and origlabel[len(origlabel)-1] in [ '\u200e', '\u200f']:  # Remove trailing writing direction
                    origlabel=origlabel[:len(origlabel)-1]
                origlabel = origlabel.replace('\u00a0', ' ').strip()
                if romanre.search(origlabel) and ('P282' not in item.claims or item.claims['P282'][0].getTarget().getID() == 'Q8229'):
                    label = get_canon_name(origlabel)
                else:
                    if verbose:
                        origlabelHex = ['%x' % ord(c) for c in origlabel]
                        print('Bad label: %s' % (origlabelHex))
                    status = 'Bad label'    # Foreign character set (non-Latin script)
            else:
                status = 'No label'         # Foreign character set (non-Latin script)

            if 'P31' not in item.claims or inst not in [ 'Q5', 'Q202444', 'Q101352' ] and not forcecopy:   # Force label copy
                status = 'Bad instance'     # Non-human item

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]

# Get Commons category/creator
            if 'P373' in item.claims:       # Wikimedia Commons Category
                commonscat = item.claims['P373'][0].getTarget()
            elif 'P1472' in item.claims:    # Wikimedia Commons Creator
                commonscat = item.claims['P1472'][0].getTarget()

            if 'P27' in item.claims:
                for seq in item.claims['P27']:      # Get nationality
                    val = seq.getTarget()
                    try:                    # Catch empty value
                        val.get()           # To get the label
                        nationality += val.labels[mainlang] + '/'
                    except:
                        pass

            if 'P569' in item.claims:       # Get birth date (normally only one)
                val = item.claims['P569'][0].getTarget()
                try:
                    birthday = val.year
                except:
                    pass

            if 'P570' in item.claims:       # Get death date (normally only one)
                val = item.claims['P570'][0].getTarget()
                try:
                    deathday = val.year
                except:
                    pass

# (1) Merge sitelinks (gets priority above default value)
            for sitelang in item.sitelinks:     # Get target sitelink
                if sitelinkre.search(sitelang) and sitelang not in new_wikis: # Process only Wikipedia links (skip other projects)
                    # See https://www.wikidata.org/wiki/User_talk:GeertivpBot#Don%27t_use_%27no%27_label
                    if sitelang == 'bhwiki':    # Language name exceptions
                        lang = 'bho'
                    elif sitelang == 'nowiki':
                        lang = 'nb'
                    else:
                        lang = sitelang[:-4]

                    sitelink = item.sitelinks[sitelang]
                    linklabel = urlbre.search(str(sitelink))	# Output URL superseeds source label
                    baselabel = get_canon_name(linklabel.group(0))

                    if len(label) > 0 and label[0] >= 'a' and label[0] <= 'z' and lang not in upper_pref_lang:      # Lowercase first character
                        baselabel = baselabel[0].lower() + baselabel[1:]

                    if baselabel.find(':') < 0 and lang not in veto_languages:   # Ignore exotic languages; only handle main namespace
                        if lang not in item.labels:
                            item.labels[lang] = baselabel
                        elif lang not in item.aliases:
                            item.aliases[lang] = [baselabel]
                        elif baselabel not in item.aliases[lang]:
                            item.aliases[lang].append(baselabel)    # Merge aliases

# (2) Fix "no" issue
            if 'no' in item.aliases:
                if 'nb' in item.aliases:
                    for seq in item.aliases['no']:
                        if seq != '' and seq not in item.aliases['nb']:
                            item.aliases['nb'].append(seq)
                else:
                    item.aliases['nb'] = item.aliases['no']
                item.aliases['no'] = []

            if 'no' in item.descriptions:
                if 'nb' not in item.descriptions:
                    item.descriptions['nb'] = item.descriptions['no']
                item.descriptions['no'] = ''

            if 'no' in item.labels: # Merge no label into nb
                if 'nb' not in item.labels:
                    item.labels['nb'] = item.labels['no']
                if 'nb' not in item.aliases:
                    item.aliases['nb'] = [item.labels['no']]
                elif item.labels['no'] not in item.aliases['nb']:
                    item.aliases['nb'].append(item.labels['no'])
                item.labels['no'] = ''

            if uselabels and status == 'OK':        ## and label.find(' ') > 0 ??

# (3) Add missing aliases for labels
                for lang in item.labels:
                    if lang not in veto_languages and romanre.search(item.labels[lang]):    # Skip non-Roman languages
                        if item.labels[lang] != label:
                            if lang not in item.aliases:
                                item.aliases[lang] = [label]
                            elif label not in item.aliases[lang]:
                                item.aliases[lang].append(label)    # Merge aliases

# (4) Add missing labels or aliases for descriptions
                for lang in item.descriptions:
                    if lang not in veto_languages and romanre.search(item.descriptions[lang]):    # Skip non-Roman languages
                        if lang not in item.labels:
                            item.labels[lang] = label
                        elif item.labels[lang] != label:
                            if lang not in item.aliases:
                                item.aliases[lang] = [label]
                            elif label not in item.aliases[lang]:
                                item.aliases[lang].append(label)    # Merge aliases

# (5) Merge labels for Latin languages
                for lang in all_languages:
                    if lang not in item.labels:
                        item.labels[lang] = label
                    elif item.labels[lang] != label:
                        if lang not in item.aliases:
                            item.aliases[lang] = [label]
                        elif label not in item.aliases[lang]:
                            item.aliases[lang].append(label)    # Merge aliases

# (6) Remove duplicate aliases for all languages: for each label remove all equal aliases
            for lang in item.labels:
                if lang in item.aliases:
                    while item.labels[lang] in item.aliases[lang]:  # Remove redundant aliases
                        item.aliases[lang].remove(item.labels[lang])

# (7) Now store the changes
            item.editEntity( {'labels': item.labels, 'descriptions': item.descriptions, 'aliases': item.aliases}, summary=transcmt)

# (8) Replicate Moedertaal -> Taalbeheersing
            if 'P103' in item.claims:
                target = item.claims['P103'][0].getTarget()
                if 'P1412' not in item.claims:
                    print('Add P1412:%s' % (target.getID()), file=sys.stderr)
                    claim = pywikibot.Claim(repo, 'P1412')
                    claim.setTarget(target)
                    item.addClaim(claim, bot=True, summary=transcmt)
                else:
#                    print(item.claims['P1412'], file=sys.stderr)
                    personlang = []
                    for seq in item.claims['P1412']:        # Get all person languages
                        personlang.append(seq.getTarget().getID())
#                    print(target.getID(), personlang, file=sys.stderr)
                    if target.getID() not in personlang:    # Add another value?
                        print('Add P1412:%s' % (target.getID()), file=sys.stderr)
                        claim = pywikibot.Claim(repo, 'P1412')
                        claim.setTarget(target)
                        item.addClaim(claim, bot=True, summary=transcmt)

# (9) Replicate Taalbeheersing -> Moedertaal
            if 'P1412' in item.claims and len(item.claims['P1412']) == 1:
                target = item.claims['P1412'][0].getTarget()
                if 'P103' not in item.claims:   # Typically one single mother tongue
                    print('Add P103:%s' % (target.getID()), file=sys.stderr)
                    claim = pywikibot.Claim(repo, 'P103')
                    claim.setTarget(target)
                    item.addClaim(claim, bot=True, summary=transcmt)

# (10) Add missing Wikipedia sitelinks
            notequal = []               # Algorithm copied from set_homonym_property.py
            if 'P1889' in item.claims:
                for seq in item.claims['P1889']:       # Get all "different from" items
                    if seq.getTarget().getID() == qnumber:
                        item.removeClaims(seq, summary='remove reflexive claim')
                    else:
                        notequal.append(seq.getTarget().getID())

            for lang in main_languages:
                if lang == 'bho':
                    sitelang = 'bhwiki'
                elif lang == 'nb':
                    sitelang = 'nowiki'
                else:
                    sitelang = lang + 'wiki'

                if lang in item.labels and sitelang not in item.sitelinks:  # Add missing sitelink
                    sitedict = {'site': sitelang, 'title': item.labels[lang]}

                    try:        # sitelink pages might not be available (escape via except pass; error message is printed)
                        item.setSitelink(sitedict, summary=u'Add sitelink') # setSitelinks can't be used because it stops at the first error
                    except pywikibot.exceptions.OtherPageSaveError as error:    # Two sitelinks can have different conflicting Qnumbers. Add Not Equal claims in the exception section...
                        exitstat = max(exitstat, 10)
                        errmesg = format(error)             # Get formatted error including all parameters (Q-numbers)
                        if debug:
                            print('Error updating %s,' % (qnumber), errmesg, file=sys.stderr)
                        itmlist = qsuffre.findall(errmesg)    # Get all Q-numbers -- Keep parameter order, skip duplicates later
                        if len(itmlist) > 1:                # Homonym error if more than 1 Q-number
                            print('Homonym', lang, itmlist, file=sys.stderr) # Can be false positive due to redirect

                            for hnumber in itmlist:         # Generate P1889 statements
                                if hnumber not in hdone:    # Skip duplicates, including the subject item number

                                    hitem = pywikibot.ItemPage(repo, hnumber)
                                    hitem.get(get_redirect=True)    # Get the item

                                    try:                    # Instance type could be missing
                                        hinst = hitem.claims['P31'][0].getTarget().getID()
                                    except:
                                        hinst = ''

                                    if inst == hinst:       # Conflicting items should be of same instance
                                        itemlist.append(hnumber)        # recursively process not equal item
                                        if hnumber not in notequal:     # Add missing "different from" statement
                                            claim = pywikibot.Claim(repo, 'P1889')
                                            claim.setTarget(hitem)
                                            item.addClaim(claim, bot=True, summary=transcmt)

                                        hnotequal = []
                                        if 'P1889' in hitem.claims:
                                            for seq in hitem.claims['P1889']:       # Get all "different from" homonym items
                                                if seq.getTarget().getID() == hnumber:
                                                    hitem.removeClaims(seq, summary='remove reflexive claim')
                                                else:
                                                    hnotequal.append(seq.getTarget().getID())

                                        if qnumber not in hnotequal:  # Add reverse missing "different from" statement
                                            claim = pywikibot.Claim(repo, 'P1889')
                                            claim.setTarget(item)
                                            hitem.addClaim(claim, bot=True, summary=transcmt)

                                    hdone.append(hnumber)   # Avoid processing duplicates

                    except:
                        pass    # Ignore all other errors, e.g. Sitelink page does not exist (error message is printed)

# (11) Error handling
        except KeyboardInterrupt:
            """
    Error handling section
            """

            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.IsRedirectPage:
            status = 'Redirect'
            errcount += 1
            exitstat = max(exitstat, 11)
            #print(qnumber, 'is a redirect page', file=sys.stderr)

        except pywikibot.exceptions.NoPage:
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.OtherPageSaveError as error:    # Conflicting label and description...
            # Add birth and death date to the description manually
            # Possibly also add P1889 (not equal to)
            status = 'Homonym'
            errcount += 1
            exitstat = max(exitstat, 13)
# No error message is shown here
#            errmesg = format(error)             # Get formatted error including all parameters
#            print('Error updating %s,' % (qnumber), errmesg, file=sys.stderr)

        except Exception as error:           # Attempt error recovery
            print('Error updating %s,' % (qnumber), format(error), file=sys.stderr)
            if exitfatal:           # Stop on first error
                raise
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
                print('%d seconds maxlag wait' % (errsleep), file=sys.stderr)
                time.sleep(errsleep)

        """
    The transaction was either executed correctly, or an error occurred.
    Possibly already a system error message was issued.
    We will report the results here, as much as we can, one line per item.
        """

# (12) Get the elapsed time in seconds and the timestamp in string format
        prevnow = now	        	# Transaction status reporting
        now = datetime.now()	    # Refresh the timestamp to time the following transaction

        if verbose or status not in ['OK']:		# Print transaction results
            isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Needed to format output
            totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
            print('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), origlabel, commonscat, alias, nationality, birthday, deathday, descr))


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

    global forcecopy
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

    if cpar.startswith('-c'):	# force copy
        forcecopy = True
        print('Force copy')
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

comsqlre = re.compile(r'\s+')		        # Computer readable query, remove duplicate whitespace
helpre = re.compile(r'^(.*\n)+\nDocumentation:\n\n.+\n')  # Help text
humsqlre = re.compile(r'\s*#.*\n')          # Human readable query, remove all comments including LF
langre = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes
namerevre = re.compile(r',(\s*[A-Z][a-z]+)+$')	# Reverse lastname, firstname
qsuffre = re.compile(r'Q[0-9]+')             # Q-numbers
romanre = re.compile(r'^[a-z .,"()\'åáàâăäãāąæǣćčçéèêěĕëēėęəǧğíìîïīłńñňņóòôöőõðœøřśšşșßțúùûüữủūůýÿžż-]{2,}$', flags=re.IGNORECASE)  # Roman alphabet
sitelinkre = re.compile(r'^[a-z]{2,3}wiki$')        # Verify for valid Wikipedia language codes
suffre = re.compile(r'\s*[(].*[)]$')		# Remove trailing () suffix (keep only the base label)
urlbre = re.compile(r'[^\[\]]+')	        # Remove URL square brackets (keep the article page name)

inlang = '-'
while len(sys.argv) > 0 and inlang.startswith('-'):
    inlang = get_next_param().lower()

# Global parameters
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
if langre.search(inlang):
    mainlang = inlang
else:
    inlang = mainlang

# Add languages
main_languages = [mainlang]     # Add sitelinks
while len(sys.argv) > 0:
    if inlang not in veto_languages:
        if inlang not in main_languages:
            main_languages.append(inlang)
        if inlang not in all_languages:
            all_languages.append(inlang)
    inlang = get_next_param().lower()

if inlang not in veto_languages:
    if inlang not in main_languages:
        main_languages.append(inlang)
    if inlang not in all_languages:
        all_languages.append(inlang)

# Print preferences
if verbose or debug:
    print('Main languages:\t%s %s' % (mainlang, main_languages), file=sys.stderr)
    print('Maximum delay:\t%d s' % maxdelay, file=sys.stderr)
    print('Minimum success rate:\t%f%%' % minsucrate, file=sys.stderr)

    print('\nUse labels:\t%s' % uselabels, file=sys.stderr)
    print('Avoid homonym:\t%s' % safemode, file=sys.stderr)
    print('Use aliases:\t%s' % usealias, file=sys.stderr)
    print('Fallback on English:\t%s' % fallback, file=sys.stderr)
    print('Use Wikipedia:\t%s' % wikipedia, file=sys.stderr)
    print('Notability:\t%s' % notability, file=sys.stderr)

    print('\nForce copy:\t%s' % forcecopy, file=sys.stderr)
    print('Verbose mode:\t%s' % verbose, file=sys.stderr)
    print('Debug mode:\t%s' % debug, file=sys.stderr)
    print('Readonly mode:\t%s' % readonly, file=sys.stderr)
    print('Exit on fatal error:\t%s' % exitfatal, file=sys.stderr)
    print('Error wait factor:\t%d' % errwaitfactor, file=sys.stderr)

# Connect to database
transcmt = 'Pwb copy label'	    	    # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()

# Get unique list of item numbers
inputfile = sys.stdin.read()
itemlist = sorted(set(qsuffre.findall(inputfile)))
if debug:
    print(itemlist)

wd_proc_all_items()	# Execute all items

"""
    Print all sitelinks (base addresses)
    PAWS is using tokens (passwords can't be used because Python scripts are public)
    Shell is using passwords (from user-password.py file)
"""
if debug:
    for site in sorted(pywikibot._sites.values()):
        if site.username():
            print(site, site.username(), site.is_oauth_token_available(), site.logged_in(), file=sys.stderr)

sys.exit(exitstat)

# Einde van de miserie
"""
To be further investigated and resolved:

WARNING: /users/geertvp/pywikibot/pywikibot/tools/__init__.py:1797: UserWarning: Site wikisource:mul instantiated using different code "wa"
  return obj(*__args, **__kw)
8	2021-09-20 21:43:35	5.388472	OK	Q17715704	Georges Édouard		['Georges Edouard']	Belgique/	1902	1970	écrivain wallon


WARNING: wikibase-sense datatype is not supported yet.


"""