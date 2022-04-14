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

    stdin: list of Q-numbers to process (extracted via regular expression; duplicates and incompatible instances are removed)

Flags:

    -c	Force copy (bypass instance validation restriction)
    -d	Debug mode
    -h	Show help
    -i  Copy instance labels to item descriptions
    -l	Disable language labels update
    -p 	Proceed after error
    -q	Quiet mode
    -r  Repeat modus
    -t  Test modus

Filters:

    Some non-Western languages are "blacklisted" to avoid erronuous updates.

    The following Q-numbers are (partially) ignored when copying labels: (sitelinks are processed)

        Duplicate Q-numbers
        Bad instances (only Q5 and related are accepted)
        Having non-roman language labels or descriptions

Notes:

    This tool can process more items than inititially provided (sitelink "not equal to" homonym error handling, reciproque statements, recursive logic).

Return status:

    The following status codes are returned to the shell:

    0 Normal termination
    1 Help requested (-h)
    2 Ctrl-c pressed, program interrupted
    3 Invalid or missing parameter
    10 Homonym
    11 Redirect
    12 Item does not exist
    14 No revision ID
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

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Author:

	Geert Van Pamel, 2021-01-30, GNU General Public License v3.0, User:Geertivp

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Wikidata_curricula/Activities/Pywikibot/Missing_label_in_target_language
    https://www.mediawiki.org/wiki/Manual:Pywikibot/Wikidata
    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string
    https://docs.python.org/3/library/logging.html
    https://docs.python.org/3/howto/logging-cookbook.html

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

Testing and debugging:

    Unexisting item: Q41360837

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
modnm = 'Pywikibot copy_label'      # Module name (using the Pywikibot package)
pgmid = '2022-04-12 (gvp)'	        # Program ID and version

"""
    Static definitions
"""

# Functional configuration flags
# Restrictions: cannot disable both labels and wikipedia. We need at least one of the options.
repldesc = False        # Replicate instance description labels
uselabels = True	    # Use the language labels (disable with -l)

# Technical configuration flags
# Defaults: transparent and safe
debug = False		    # Can be activated with -d (errors and configuration changes are always shown)
errorstat = True        # Show error statistics (disable with -e)
exitfatal = True	    # Exit on fatal error (can be disabled with -p; please take care)
lead_lower = False      # Leading lowercase
lead_upper = False      # Leading uppercase
overrule = False        # Overrule
repeatmode = False      # Repeat mode
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
human_list = {'Q5', 'Q101352', 'Q12308941', 'Q11879590', 'Q3409032', 'Q95074'} # human, last name, male first name, female first name, neutral first name, personage
# Do not add Central European languages like cs, hu, pl, sk, etc. because of special language rules
# Not in Hungarian, Czech, Polish, Slovak, etc
all_languages = {'af', 'an', 'ast', 'ca', 'cy', 'da', 'de', 'de-at', 'de-ch', 'en', 'es', 'fi', 'fr', 'ga', 'gl', 'io', 'it', 'jut', 'nb', 'nl', 'nn', 'pms', 'pt', 'pt-br', 'ro', 'sc', 'sco', 'sje', 'sq', 'sv'}  # Add labels for all those languages
nat_languages = {'Q1321', 'Q150', 'Q1860', 'Q188', 'Q652', 'Q7411'}    # Default natural languages for mother tongue (others will be added)
taal_item = {'Q1288568', 'Q33742', 'Q34770'}           # levende taal, natuurlijke taal, taal => amend list of nat_languages
upper_pref_lang = {'atj', 'bar', 'bjn', 'co', 'de', 'de-at', 'de-ch', 'ext', 'frp', 'gcr', 'gsw', 'ht', 'kab', 'ksh', 'lb', 'lg', 'lld', 'mwl', 'nan', 'nds', 'nds-nl', 'pfl', 'rmy', 'rup', 'sgs', 'shi', 'sn', 'tum', 'vec', 'vro'}       # Languages using uppercase nouns
new_wikis = {'altwiki', 'amiwiki', 'arywiki', 'avkwiki', 'lldwiki', 'madwiki', 'mniwiki', 'pwnwiki','shiwiki', 'skrwiki', 'taywiki'}       # Not yet described as Wikipedia family (to be skipped)
veto_countries = {'Q148', 'Q159', 'Q15180' }     # Risk for non-roman languages
veto_languages = {'aeb', 'aeb-arab', 'aeb-latn', 'ar', 'arc', 'arq', 'ary', 'arz', 'bcc', 'be' ,'be-tarask', 'bg', 'bn', 'bgn', 'bqi', 'cs', 'ckb', 'cv', 'dv', 'el', 'fa', 'gan', 'gan-hans', 'gan-hant', 'glk', 'gu', 'he', 'hi', 'hu', 'hy', 'ja', 'ka', 'khw', 'kk', 'kk-arab', 'kk-cn', 'kk-cyrl', 'kk-kz', 'kk-latn', 'kk-tr', 'ko', 'ks', 'ks-arab', 'ks-deva', 'ku', 'ku-arab', 'ku-latn', 'ko', 'ko-kp', 'lki', 'lrc', 'lzh', 'luz', 'mhr', 'mk', 'ml', 'mn', 'mzn', 'ne', 'new', 'or', 'os', 'ota', 'pl', 'pnb', 'ps', 'ru', 'rue', 'sd', 'sdh', 'sh', 'sk', 'sr', 'sr-ec', 'ta', 'te', 'tg', 'tg-cyrl', 'tg-latn', 'th', 'ug', 'ug-arab', 'ug-latn', 'uk', 'ur', 'vep', 'vi', 'yi', 'yue', 'zg-tw', 'zh', 'zh-cn', 'zh-hans', 'zh-hant', 'zh-hk', 'zh-mo', 'zh-my', 'zh-sg', 'zh-tw'} # Skip non-standard character encoding; see also romanre (other name rules)
veto_languages_id = {'Q7737', 'Q8798'}                  # Automatically built from veto_languages and lang_qnumbers
# bcc missing
lang_qnumbers = {'aeb':'Q56240', 'ar':'Q13955', 'arc':'Q28602', 'arq':'Q56499', 'ary':'Q56426', 'arz':'Q29919', 'be':'Q9091', 'be-tarask':'Q8937989', 'bg':'Q7918', 'bn':'Q9610', 'bgn':'Q12645561', 'bqi':'Q257829', 'cs':'Q9056', 'ckb':'Q36811', 'cv':'Q33348', 'da':'Q9035', 'de':'Q188', 'dv':'Q32656', 'el':'Q9129', 'en':'Q1860', 'es':'Q1321', 'fa':'Q9168', 'fi':'Q1412', 'fr':'Q150', 'gan':'Q33475', 'gan-hans':'Q64427344', 'gan-hant':'Q64427346', 'glk':'Q33657', 'gu':'Q5137', 'he':'Q9288', 'hi':'Q1568', 'hu':'Q9067', 'hy':'Q8785', 'it':'Q652', 'ja':'Q5287', 'ka':'Q8108', 'khw':'Q938216', 'kk':'Q9252', 'kk-arab':'Q90681452', 'kk-cn':'Q64427349', 'kk-cyrl':'Q90681280', 'kk-kz':'Q64427350', 'kk-tr':'Q64427352', 'ko':'Q9176', 'ko-kp':'Q18784', 'ks':'Q33552', 'ku':'Q36368', 'lki':'Q18784', 'lrc':'Q19933293', 'lzh':'Q37041', 'luz':'Q12952748', 'mhr':'Q12952748', 'mk':'Q9296', 'ml':'Q36236', 'mn':'Q9246', 'mzn':'Q13356', 'ne':'Q33823', 'new':'Q33979', 'nl':'Q7411', 'no':'Q9043', 'or':'Q33810', 'os':'Q33968', 'ota':'Q36730', 'pl':'Q809', 'pnb':'Q1389492', 'ps':'Q58680', 'pt':'Q5146', 'ro':'Q7913', 'ru':'Q7737', 'rue':'Q26245', 'sd':'Q33997', 'sdh':'Q1496597', 'sh':'Q9301', 'sk':'Q9058', 'sr':'Q9299', 'sv':'Q9027', 'ta':'Q5885', 'te':'Q8097', 'tg':'Q9260', 'th':'Q9217', 'ug':'Q13263', 'uk':'Q8798', 'ur':'Q1617', 'vep':'Q32747', 'vi':'Q9199', 'yi':'Q8641', 'yue':'Q9186', 'zh':'Q7850', 'zh-cn':'Q24841726', 'zh-hant':'Q18130932', 'zh-hk':'Q100148307', 'zh-mo':'Q64427357', 'zh-my':'Q13646143', 'zh-sg':'Q1048980', 'zh-tw':'Q4380827'}   # Lookup table qnumbers

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
    if colonloc < 0 and commaloc:               # Reorder "lastname, firstname" and concatenate with space
        baselabel = baselabel[commaloc.start() + 1:] + ' ' + baselabel[:commaloc.start()]
        baselabel = baselabel.replace(',',' ')  # Multiple ,
    baselabel = ' '.join(baselabel.split()) # Remove redundant spaces
    return baselabel


def get_prop_val(item, proplist):

    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:         # Get property value
            for seq in item.claims[prop]:
                item_prop_val += seq.getTarget() + '/'
            break
    return item_prop_val


def get_prop_val_object_label(item, proplist):

    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:         # Get property value
            for seq in item.claims[prop]:
                val = seq.getTarget()
                try:
                    item_prop_val += val.labels[mainlang] + '/' # Skip unlabeled items
                except:
                    pass
            break
    return item_prop_val


def get_prop_val_year(item, proplist):

    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:       # Get death date (normally only one)
            for seq in item.claims[prop]:
                val = seq.getTarget()
                try:
                    item_prop_val += str(val.year) + '/' # Skip bad dates
                except:
                    pass
            break
    return item_prop_val


def is_foreign_lang(lang_list):
    isforeign = True

    for seq in lang_list:
        if not romanre.search(seq):
            break
    else:
        isforeign = False
    return isforeign


def is_in_list(statement_list, check_list):
    isinlist = True

    for seq in statement_list:
        if seq.getTarget().getID() in check_list:
            break
    else:
        isinlist = False
    return isinlist


def is_veto_lang_label(lang_list):
    isveto = True

    for seq in lang_list:
        if not romanre.search(seq.getTarget().text) or seq.getTarget().language in veto_languages_id:
            break
    else:
        isveto = False
    return isveto


def is_veto_script(script_list):
    isveto = True

    for seq in script_list:
        if str(seq.getTarget()) != 'None' and seq.getTarget().getID() != 'Q8229':    # Nonroman script
            break
    else:
        isveto = False
    return isveto


def wd_proc_all_items():
    """
    Module logic
    """

    global exitstat

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    statcount = 0           # Statement count
    pictcount = 0	    	# Picture count
    safecount = 0	    	# Safe transaction
    errcount = 0	    	# Error counter
    errsleep = 0	    	# Technical error penalty (sleep delay in seconds)
    hdone = set()           # Avoid recursion loops

# Avoid that the user is waiting for a response while the data is being queried
    if verbose:
        print('\nProcessing %d statements' % (len(itemlist)), file=sys.stderr)

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for qnumber in itemlist:	# Main loop for all DISTINCT items
      if status == 'Stop':	# Ctrl-c pressed -> stop in a proper way
        break

      if qnumber > 'Q':     # Allows a restart
        transcount += 1 	# New transaction
        status = 'OK'
        alias = ''
        descr = ''
        commonscat = ''     # Commons category
        nationality = ''
        label = ''
        birthday = ''
        deathday = ''

# Skip recursive duplicates (can be added after the initial list was sorted)
        if qnumber in hdone:
            continue

        logger.debug(qnumber)
        hdone.add(qnumber)

        try:		    	    # Error trapping (prevents premature exit on transaction error)
            item = pywikibot.ItemPage(repo, qnumber)
            item.get(get_redirect = True)       # Required?

            try:                # Instance type could be missing
                instprop = item.claims['P31'][0].getTarget()
                inst = instprop.getID()
            except:
                inst = ''

# Get the item label
            if mainlang in item.labels:
                # Cleanup the label
                label = item.labels[mainlang]
                while len(label) > 0 and label[len(label)-1] in [ '\u200e', '\u200f']:      # Remove trailing writing direction
                    label=label[:len(label)-1]
                label = label.replace('\u00a0', ' ').strip()    # Replace alternative space character

                if not romanre.search(label) or mainlang in item.aliases and is_foreign_lang(item.aliases[mainlang]):
                    status = 'Language'
                elif 'P103' in item.claims and is_in_list(item.claims['P103'], veto_languages_id):     # native language
                    status = 'Language'
                elif 'P1412' in item.claims and is_in_list(item.claims['P1412'], veto_languages_id):   # language knowledge
                    status = 'Language'
                elif 'P1559' in item.claims and is_veto_lang_label(item.claims['P1559']):   # name in native language
                    status = 'Language'
                elif 'P27' in item.claims and is_in_list(item.claims['P27'], veto_countries):          # nationality languages
                    status = 'Country'
                elif 'P282' in item.claims and is_veto_script(item.claims['P282']):         # foreign script
                    status = 'Script'
                elif 'P97' in item.claims:  # Noble names are exceptions
                    status = 'Noble'
                elif inst in human_list:
                    label = get_canon_name(label)
            else:
                status = 'No label'         # Missing label

            if inst not in human_list and not forcecopy :   # Force label copy
                status = 'Item'             # Non-human item

            if mainlang in item.descriptions:
                descr = item.descriptions[mainlang]

            if mainlang in item.aliases:
                alias  = item.aliases[mainlang]

# Get Commons category/creator
            commonscat  = get_prop_val(item,                ['P373', 'P1472', 'P1612'])         # Wikimedia Commons Category, Creator, Institution
            nationality = get_prop_val_object_label(item,   ['P27', 'P17', 'P495', 'P1001'])    # nationality
            birthday    = get_prop_val_year(item,           ['P569', 'P571', 'P580', 'P729'])   # birth date (normally only one)
            deathday    = get_prop_val_year(item,           ['P570', 'P576', 'P582', 'P730'])   # death date (normally only one)

# (1) Fix "no" issue
            if 'no' in item.labels:         # Move no label to nb, and possibly to aliases
                if 'nb' not in item.labels:
                    item.labels['nb'] = item.labels['no']
                if 'nb' not in item.aliases:
                    item.aliases['nb'] = [item.labels['no']]
                elif item.labels['no'] not in item.aliases['nb']:
                    item.aliases['nb'].append(item.labels['no'])
                item.labels['no'] = ''

            if 'no' in item.aliases:        # Move no aliases to nb
                if 'nb' in item.aliases:
                    for seq in item.aliases['no']:
                        if seq != '' and seq not in item.aliases['nb']:
                            item.aliases['nb'].append(seq)
                else:
                    item.aliases['nb'] = item.aliases['no']
                item.aliases['no'] = []

            if 'no' in item.descriptions:   # Move no descriptions to nb
                if 'nb' not in item.descriptions:
                    item.descriptions['nb'] = item.descriptions['no']
                item.descriptions['no'] = ''

# (2) Merge sitelinks (gets priority above default value)
            for sitelang in item.sitelinks:     # Get target sitelink
                if sitelinkre.search(sitelang) and sitelang not in new_wikis: # Process only known Wikipedia links (skip other projects)
                    # See https://www.wikidata.org/wiki/User_talk:GeertivpBot#Don%27t_use_%27no%27_label
                    if sitelang == 'bhwiki':    # Canonic language names
                        lang = 'bho'
                    elif sitelang == 'nowiki':
                        lang = 'nb'
                    else:
                        lang = sitelang[:-4]

                    sitelink = item.sitelinks[sitelang]
                    linklabel = urlbre.search(str(sitelink))	# Output URL superseeds source label
                    baselabel = linklabel.group(0)
                    if inst in human_list:                      # Only cleanup human names
                        baselabel = get_canon_name(baselabel)

                    if lang in veto_languages or not romanre.search(label):  # Non-Roman characters
                        pass
                    elif (lang in item.labels and item.labels[lang][0].islower()) or (len(label) > 0 and label[0].islower() and lang not in upper_pref_lang):
                        baselabel = baselabel[0].lower() + baselabel[1:]      # Lowercase first character

                    if baselabel.find(':') >= 0:   # Only handle main namespace
                        pass
                    elif lang not in item.labels:
                        item.labels[lang] = baselabel
                    elif unidecode.unidecode(baselabel.lower()) == unidecode.unidecode(item.labels[lang].lower()):    # Ignore accents
                        pass
                    elif lang not in item.aliases:
                        item.aliases[lang] = [baselabel]
                    elif baselabel not in item.aliases[lang]:
                        item.aliases[lang].append(baselabel)    # Merge aliases

# (3) Replicate instance descriptions from the Property label
            if repldesc and inst != '':
                for lang in instprop.labels:
                    if overrule or lang not in item.descriptions:
                        item.descriptions[lang] = instprop.labels[lang].replace(':', ' ')

            if uselabels and status == 'OK' and label != '':        ## and label.find(' ') > 0 ??
                if lead_lower:
                   label = label[0].lower() + label[1:]      # Lowercase first character
                elif lead_upper:
                   label = label[0].upper() + label[1:]      # Uppercase first character

# (4) Add missing aliases for labels
                for lang in item.labels:
                    if lang not in veto_languages and romanre.search(item.labels[lang]):    # Skip non-Roman languages
                        if unidecode.unidecode(item.labels[lang].lower()) != unidecode.unidecode(label.lower()):  # Also ignore accents
                            if lang not in item.aliases:
                                item.aliases[lang] = [label]
                            elif label not in item.aliases[lang]:
                                item.aliases[lang].append(label)        # Merge aliases

# (5) Add missing labels or aliases for descriptions
                for lang in item.descriptions:
                    if lang not in veto_languages and romanre.search(item.descriptions[lang]):    # Skip non-Roman languages
                        if lang not in item.labels:
                            item.labels[lang] = label
                        elif unidecode.unidecode(item.labels[lang]).lower() != unidecode.unidecode(label).lower():# Also ignore accents
                            if lang not in item.aliases:
                                item.aliases[lang] = [label]
                            elif label not in item.aliases[lang]:
                                item.aliases[lang].append(label)        # Merge aliases

# (6) Merge labels for Latin languages
                for lang in all_languages:
                    if lang not in item.labels:
                        item.labels[lang] = label
                    elif unidecode.unidecode(item.labels[lang].lower()) != unidecode.unidecode(label.lower()):    # Also ignore accents
                        if lang not in item.aliases:
                            item.aliases[lang] = [label]
                        elif label not in item.aliases[lang]:
                            item.aliases[lang].append(label)            # Merge aliases

# (7) Move first alias to any missing label
            for lang in item.aliases:
                if lang not in item.labels and lang in all_languages and lang in item.descriptions and romanre.search(item.descriptions[lang]):
                    for seq in item.aliases[lang]:
                        if romanre.search(seq):   # Skip non-Roman languages
                            print('Move %s alias %s to label' % (lang, seq), file=sys.stderr)
                            item.labels[lang] = seq                     # Move single alias
                            item.aliases[lang].remove(seq)
                            break

# (8) Remove duplicate aliases for all languages: for each label remove all equal aliases
            for lang in item.labels:
                if lang in item.aliases:
                    while item.labels[lang] in item.aliases[lang]:      # Remove redundant aliases
                        item.aliases[lang].remove(item.labels[lang])

# (9) Now store the changes
            try:
                item.editEntity( {'labels': item.labels, 'descriptions': item.descriptions, 'aliases': item.aliases}, summary=transcmt)

            except pywikibot.exceptions.OtherPageSaveError as error:    # Duplicate description
                #logger.error(error)
                status = 'DupDescr'
                errcount += 1
                exitstat = max(exitstat, 14)

# (10) Replicate Moedertaal -> Taalbeheersing
            if 'P103' in item.claims:
                target = item.claims['P103'][0].getTarget()
                nat_languages.add(target.getID())       # Add a natural language

                personlang = set()
                if 'P1412' in item.claims:
                    for seq in item.claims['P1412']:        # Get all person languages
                        personlang.add(seq.getTarget().getID())
                    logger.debug('Person languages: %s %s' % (target.getID(), personlang))

                if target.getID() not in personlang:        # Add another value?
                    print('Add P1412:%s' % (target.getID()), file=sys.stderr)
                    claim = pywikibot.Claim(repo, 'P1412')
                    claim.setTarget(target)
                    item.addClaim(claim, bot=True, summary=transcmt)
                    status = 'Update'

# (11) Replicate Taalbeheersing -> Moedertaal
            if 'P103' not in item.claims and 'P1412' in item.claims and len(item.claims['P1412']) == 1:
                target = item.claims['P1412'][0].getTarget()
                if target.getID() not in nat_languages:         # Add natural language
                    target.get(get_redirect = True)
                    if 'P31' in target.claims:
                        for seq in target.claims['P31']:        # Get all languages types
                            if seq.getTarget().getID() not in taal_item:
                                break                           # We only want natural languages
                        else:
                            nat_languages.add(target.getID())   # Add a natural language

                if target.getID() in nat_languages:     # Add one single mother tongue (filter non-natural languages like Esperanto)
                    print('Add P103:%s' % (target.getID()), file=sys.stderr)
                    claim = pywikibot.Claim(repo, 'P103')
                    claim.setTarget(target)
                    item.addClaim(claim, bot=True, summary=transcmt)
                    status = 'Update'
                elif 'P1559' in item.claims and len(item.claims['P1559']) == 1:     # name in native language
                    mothlang=item.claims['P1559'][0].getTarget().language
                    if mothlang in lang_qnumbers:
                        nat_languages.add(lang_qnumbers[mothlang])       # Add a natural language

                        print('Add P103:%s' % (mothlang), file=sys.stderr)
                        claim = pywikibot.Claim(repo, 'P103')
                        claim.setTarget(pywikibot.ItemPage(repo, lang_qnumbers[mothlang]))
                        item.addClaim(claim, bot=True, summary=transcmt)
                        status = 'Update'
                    else:
                        logger.error('Unknown language %s' % mothlang)

# (12) Set symmetric P1889 property - different from
            notequal = set()              # Algorithm copied from set_homonym_property.py
            if 'P1889' in item.claims:
                for seq in item.claims['P1889']:        # Get all "different from" items
                    hitem = seq.getTarget()
                    hnumber = hitem.getID()
                    if hnumber not in hdone and 'P279' not in item.claims:    # Omit subclasses and duplicates, including the subject item number
                        itemlist.append(hnumber)        # recursively process not equal item

                    if hnumber == qnumber:              # Remove reflexive relationship
                        item.removeClaims(seq, bot=True, summary='remove reflexive claim')
                        status = 'Update'
                    else:
                        notequal.add(hnumber)

                        hnotequal = set()
                        if 'P1889' in hitem.claims:
                            for hseq in hitem.claims['P1889']:       # Get all "different from" homonym items
                                if hseq.getTarget().getID() == hnumber:
                                    hitem.removeClaims(hseq, bot=True, summary='remove reflexive claim')
                                    status = 'Update'
                                else:
                                    hnotequal.add(hseq.getTarget().getID())

                        if qnumber not in hnotequal and item.claims['P31'][0].getTarget().getID() == hitem.claims['P31'][0].getTarget().getID():    ## match other indexes??
                            claim = pywikibot.Claim(repo, 'P1889')        # Add missing reverse "different from" statement
                            claim.setTarget(item)
                            hitem.addClaim(claim, bot=True, summary=transcmt)
                            status = 'Update'

# Set symmetric P460 property - naar verluidt hetzelfde als
            if 'P460' in item.claims:
                if 'P1889' in item.claims:
                    logger.error('P460 and P1889 conflict')

                sitem = item.claims['P460'][0].getTarget()
                if 'P460' not in sitem.claims:
                    claim = pywikibot.Claim(repo, 'P460')
                    claim.setTarget(item)
                    sitem.addClaim(claim, bot=True, summary=transcmt)
                    status = 'Update'

# (13) Add missing Wikipedia sitelinks
            for lang in main_languages:
                if lang == 'bho':
                    sitelang = 'bhwiki'
                elif lang == 'nb':
                    sitelang = 'nowiki'
                else:
                    sitelang = lang + 'wiki'

                if lang in item.labels and sitelang not in item.sitelinks:  # Add missing sitelink
                    sitedict = {'site': sitelang, 'title': item.labels[lang]}

                    try:
                        # This section contains a complicated recursive error handling algorithm
                        # setSitelinks nor editEntity can't be used because it stops at the first error, and we need more control
                        # Two or more sitelinks can have conflicting Qnumbers. Add mutual "Not Equal" claims via the exception section...
                        # sitelink pages might not be available (quick escape via except pass; error message is printed)
                        item.setSitelink(sitedict, summary=u'Add sitelink')
                        status = 'Update'
                    except pywikibot.exceptions.OtherPageSaveError as error:
                        itmlist = set(qsuffre.findall(str(error)))    # Get unique Q-numbers, skip duplicates later (order not guaranteed)
                        if len(itmlist) > 1:                # Homonym error if more than 1 Q-number
                            status = 'Homonym'	    # Handle any generic error
                            errcount += 1
                            exitstat = max(exitstat, 10)
                            #logger.debug('Error updating %s, %s' % (qnumber, error))
                            print('Homonym', lang, itmlist, file=sys.stderr) # Can be false positive due to redirect

                            for hnumber in itmlist:         # Generate P1889 statements
                                if hnumber not in hdone:    # Skip duplicates, including the subject item number
                                    itemlist.append(hnumber)            # recursively process not equal item
                                    hitem = pywikibot.ItemPage(repo, hnumber)
                                    hitem.get(get_redirect = True)      # Get the item

                                    try:                    # Instance type could be missing
                                        hinst = hitem.claims['P31'][0].getTarget().getID()
                                    except:
                                        hinst = ''

                                    if inst == hinst:       # Conflicting items should be of same instance / what if there is no instance?
                                        if hnumber not in notequal:     # Add missing "different from" statement
                                            claim = pywikibot.Claim(repo, 'P1889')
                                            claim.setTarget(hitem)
                                            item.addClaim(claim, bot=True, summary=transcmt)
                                            status = 'Update'

                                        hnotequal = set()
                                        if 'P1889' in hitem.claims:
                                            for hseq in hitem.claims['P1889']:       # Get all "different from" homonym items
                                                if hseq.getTarget().getID() == hnumber:
                                                    hitem.removeClaims(hseq, bot=True, summary='remove reflexive claim')
                                                    status = 'Update'
                                                else:
                                                    hnotequal.add(hseq.getTarget().getID())

                                        if qnumber not in hnotequal:  # Add reverse missing "different from" statement
                                            claim = pywikibot.Claim(repo, 'P1889')
                                            claim.setTarget(item)
                                            hitem.addClaim(claim, bot=True, summary=transcmt)
                                            status = 'Update'

# (14) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.NoPageError as error:           # Item not found
            logger.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except AttributeError as error:           # NoneType error
            logger.error(error)
            status = 'NoneType'
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

# (15) Get the elapsed time in seconds and the timestamp in string format
        prevnow = now	        	# Transaction status reporting
        now = datetime.now()	    # Refresh the timestamp to time the following transaction

        if verbose or status not in ['OK']:		# Print transaction results
            isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Needed to format output
            totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
            print('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, item.getID(), label, commonscat, alias, nationality, birthday, deathday, descr))


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
    global lead_lower
    global lead_upper
    global overrule
    global repldesc
    global repeatmode
    global readonly
    global uselabels
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter
    if debug:
        print('Parameter %s' % cpar)

    if cpar.startswith('-c'):	# force copy
        forcecopy = True
        print('Force copy')
    elif cpar.startswith('-d'):	# debug mode
        logger.isEnabledFor(logging.DEBUG)  ## This seems not to work?
        debug = True
        print('Setting debug mode')
    elif cpar.startswith('-e'):	# error stat
        errorstat = False
        print('Disable error statistics')
    elif cpar.startswith('-h'):	# help
        show_help_text()
    elif cpar.startswith('-i'):	# replicate instance description labels
        repldesc = True
    elif cpar.startswith('-l'):	# language labels
        uselabels = False
        print('Disable label reuse')
    elif cpar.startswith('-m'):	# fast mode
        errwaitfactor = 1
        print('Setting fast mode')
    elif cpar.startswith('-o'):	# overrule
        overrule = True
    elif cpar.startswith('-p'):	# proceed after fatal error
        exitfatal = False
        print('Setting proceed after fatal error')
    elif cpar.startswith('-q'):	# quiet mode
        verbose = False
        print('Setting quiet mode')
    elif cpar.startswith('-r'):	# repeat mode
        repeatmode = True 
        print('Setting repeat mode')
    elif cpar.startswith('-t'):	# readonly mode
        readonly = True
        print('Setting readonly mode')
    elif cpar.startswith('-u'):	# leading lowercase
        lead_lower = True
        print('Setting leading lowercase')
    elif cpar.startswith('-U'):	# leading uppercase
        lead_upper = True
        print('Setting leading uppercase')
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
logger = logging.getLogger('copy_label')

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
namerevre = re.compile(r',(\s*.*)*$')	    # Reverse lastname, firstname
qsuffre = re.compile(r'Q[0-9]+')            # Q-numbers
romanre = re.compile(r'^[a-z .,"()\'åáàâǎăäãāąæǣćčçéèêěĕëēėęəģǧğġíìîïīķłńñňņóòôöőõōðœøřśšşșßțúùûüữủūůűýÿĳžż-]{2,}$', flags=re.IGNORECASE)  # Roman alphabet
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
            all_languages.add(inlang)
    inlang = get_next_param().lower()

if inlang not in veto_languages:
    if inlang not in main_languages:
        main_languages.append(inlang)
    if inlang not in all_languages:
        all_languages.add(inlang)

# Connect to database
transcmt = 'Pwb copy label'	    	    # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()

for lang in veto_languages:
    if lang in lang_qnumbers and lang_qnumbers[lang] not in veto_languages_id:
        veto_languages_id.add(lang_qnumbers[lang])

# Print preferences
print('Main languages:\t%s %s' % (mainlang, main_languages), file=sys.stderr)

if verbose or debug:
    print('Maximum delay:\t%d s' % maxdelay, file=sys.stderr)
    print('Minimum success rate:\t%f%%' % minsucrate, file=sys.stderr)
    print('Use labels:\t%s' % uselabels, file=sys.stderr)
    print('Instance descriptions:\t%s' % repldesc, file=sys.stderr)
    print('Force copy:\t%s' % forcecopy, file=sys.stderr)
    print('Verbose mode:\t%s' % verbose, file=sys.stderr)
    print('Debug mode:\t%s' % debug, file=sys.stderr)
    print('Readonly mode:\t%s' % readonly, file=sys.stderr)
    print('Exit on fatal error:\t%s' % exitfatal, file=sys.stderr)
    print('Error wait factor:\t%d' % errwaitfactor, file=sys.stderr)

# Get unique list of item numbers
inputfile = sys.stdin.read()
itemlist = sorted(set(qsuffre.findall(inputfile)))
if debug:
    print(itemlist, file=sys.stderr)

wd_proc_all_items()	# Execute all items

while repeatmode:
    print('\nEnd of list')
    # Get list of item numbers
    inputfile = sys.stdin.read()
    itemlist = sorted(set(qsuffre.findall(inputfile)))
    if debug:
        print(itemlist, file=sys.stderr)
    wd_proc_all_items()	# Execute all items for one language

# Print list of natural languages
if verbose:
    for qnumber in nat_languages:
        try:
            item = pywikibot.ItemPage(repo, qnumber)
            print('%s (%s)' % (item.labels[mainlang], qnumber))
        except:
            print('(%s)' % (qnumber))
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

"""
To be further investigated and resolved:

WARNING: /users/geertvp/pywikibot/pywikibot/tools/__init__.py:1797: UserWarning: Site wikisource:mul instantiated using different code "wa"
  return obj(*__args, **__kw)
8	2021-09-20 21:43:35	5.388472	OK	Q17715704	Georges Édouard		['Georges Edouard']	Belgique/	1902	1970	écrivain wallon


WARNING: wikibase-sense datatype is not supported yet.


https://www.wikidata.org/w/index.php?title=Q102390700&type=revision&diff=1524932663&oldid=1524749677

beschrijving (label)

pywikibot.exceptions.InvalidTitle: '\x1b[200~Nevejansan' contains illegal char(s) '\x1b'
CRITICAL: Exiting due to uncaught exception <class 'pywikibot.exceptions.InvalidTitle'>

"""
# Einde van de miserie
