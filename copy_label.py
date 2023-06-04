#!/usr/bin/python3

codedoc = """
copy_label.py - Copy Wikikdata language labels to other languages, autocorrect, and register extra statements.

* Norwegian language mismatches are fixed (no-nb language mapping mismatch betweek Wikipedia and Wikidata).
* Wikipedia site links are merged as aliases.
* Copy human labels to other languages
* Add missing Wikidata statements
* Symmetric "Equal to" statements are added.
* "Not-equal to" statements are generated when there are homonyms detected.
* Reflexive "Not-equal to" statements are removed.
* Symmetric "Not-equal to" statements are added.
* Person's native language and languages used completed.
* Redundant aliases are removed.
* Aliases for which there is no label are moved to label.
* Unrecognized Unicodes are not processed.
* Non-western encoded languages are skipped (but Wikipedia sitelinks are processed).
* Automatic case matching (language specific first captital handling like e.g. in German).
* Unregistered Wikipedia site links for which there exist language labels are added to Wikidata.
* Register missing Wikimedia Commons Categories
* {{Wikidata Infobox}} is added to Commons Category pages
* Register Wikipedia sitelinks
* Add missing Wikimedia Commons SDC P180 depict statements for Wikidata media file statements
* Amend Wikipedia pages for all languages with Commonscat templates
    * Add infoboxes
    * Add images to Wikipedia pages
    * Add Wikipedia Commonscat templates
    * Add Wikipedia Authority control templates for humans
    * Add DEFAULTSORT for humans

Parameters:

    P1: source language code (default: LANGUAGE, LC_ALL, LANG environment variables)
    P2... additional language codes for site-link check and label replication
        Take care to only include Western (Roman) languages.

    stdin: list of Q-numbers to process (extracted via regular expression;
        duplicate and incompatible instances are ignored.

Flags:

    -c	Force copy (bypass instance validation restriction)
    -d	Debug mode
    -h	Show help
    -i  Copy instance labels to item descriptions
    -l	Disable language labels update
    -p 	Proceed after error
    -q	Quiet mode
    -r  Repeat modus
    -t  Test modus (read only check)

Filters:

    Western languags are "whitelisted"
    Some non-Western languages are "blacklisted" to avoid erronuous updates
    (due to East European conventions).

    The following Q-numbers are (partially) ignored when copying labels: (sitelinks are processed)

        Duplicate Q-numbers
        Bad instances (only Q5 and related are accepted; subclasses are ignored)
        Having non-roman language labels or descriptions

Return status:

    The following status codes are returned to the shell:

    0   Normal termination
    1   Help requested (-h)
    3   Invalid or missing parameter
    10  Homonym
    11  Redirect
    12  Item does not exist
    14  No revision ID
    20  General error (Maxlag error, network error)
    130 Ctrl-c pressed, program interrupted

Error handling:

    This script should normally not stack dump, unless a severe (network) error happens.
    Any error will be reflected into the return status.
    It has intelligent error handling with self-healing code when possible.
    Wikidata run-time errors and timeouts are properly handled and reported.
    Processing typically continues after 60s retry/timeout.
    Data quality ensurance:
        It does not create duplicate statements.
        It does not create contradictory statements.
        It does not break constraints.
        It does not overrule statements.

Volume processing:

    For high volumes a Bot account is required; the maximum speed is 1 transaction/second.
    The Wikidata user is responsible to adhere to:
        https://www.wikidata.org/wiki/Wikidata:Bots
        https://www.wikidata.org/wiki/Wikidata:Creating_a_bot
        https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py
    For non-bot accounts maximum 1-4 transactions per minute.

Responsibilities:

    The person running this script is sole responsible for any erronuous updates the script is performing.
    This script is offered to the user as best-effort.
    The author does not accept any responsibility for any bugs in the script.
    Bugs should be reported to the author, in order to ameliorate the script.

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Author:

	Geert Van Pamel, 2021-01-30, MIT License, User:Geertivp

Documentation:

    https://doc.wikimedia.org/pywikibot/stable/api_ref/pywikibot.html
    https://doc.wikimedia.org/pywikibot/stable/api_ref/pywikibot.page.html
    https://www.wikidata.org/wiki/Wikidata:Wikidata_curricula/Activities/Pywikibot/Missing_label_in_target_language
    https://www.mediawiki.org/wiki/Manual:Pywikibot/Wikidata
    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string
    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html
    https://docs.python.org/3/library/datetime.html
    https://docs.python.org/3/library/re.html
    https://byabbe.se/2020/09/15/writing-structured-data-on-commons-with-python

Known problems:

    pywikibot.exceptions.OtherPageSaveError
    WARNING: API error failed-save: The save has failed.
    Error processing Q752115, Edit to page [[wikidata:Q752115]] failed:

        1/ There already exist a Wikipedia article with the same name linked to another item.
        This automatically adds a missing "not equal to" statement https://www.wikidata.org/wiki/Property:P1889

        2/ There exist another language label with an identical description.

        3/ Conflicting Commons Category page

        4/ Conflicting sitelink

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

    SELECT DISTINCT ?item WHERE {
    ?item wdt:P6104 ?wikiproject.
    ?wikiproject wdt:P31 wd:Q16695773;
    wdt:P664 wd:Q18398868.
    }

Testing and debugging:

    Unexisting item: Q41360837

Similer projects:

    Add Names as labels: https://www.wikidata.org/wiki/Q21640602

"""

# List the required modules
import json             # json data structures
import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import unidecode        # Unicode
from datetime import datetime	    # now, strftime, delta time, total_seconds
from datetime import timedelta

# Global variables
modnm = 'Pywikibot copy_label'      # Module name (using the Pywikibot package)
pgmid = '2023-06-01 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

# Wikidata transaction comment
BOTFLAG = True          # Should be False for non-bot accounts
transcmt = '#pwb Copy label'

# Instances
HUMANINSTANCE = 'Q5'                # Could be set or list
ESPERANTOLANGINSTANCE = 'Q143'

# Properties
VIDEOPROP = 'P10'
MAPPROP = 'P15'
CTRYPROP = 'P17'
IMAGEPROP = 'P18'
FATHERPROP = 'P22'
MARIAGEPARTNERPROP = 'P26'
NATIONALITYPROP = 'P27'
INSTANCEPROP = 'P31'
CHILDPROP = 'P40'
FLAGPROP = 'P41'
BORDERPEERPROP = 'P47'
AUDIOPROP = 'P51'
COATOFARMSPROP = 'P94'
NOBLENAMEPROP = 'P97'
NATIVELANGPROP = 'P103'
SIGNATUREPROP = 'P109'
LOGOPROP = 'P154'
DEPICTSPROP = 'P180'
LOCATORMAPPROP = 'P242'
SUBCLASSPROP = 'P279'
FOREIGNSCRIPTPROP = 'P282'
MAINSUBJECTPROP = 'P301'
PARTOFPROP = 'P361'
COMMCATPROP = 'P373'
PARTNERPROP = 'P451'
EQTOPROP = 'P460'
CTRYORIGPROP = 'P495'
BIRTHDTPROP = 'P569'
DEATHDTPROP = 'P570'
CONTAINSPROP = 'P527'
FOUNDDTPROP = 'P571'
DISSOLVDTPROP = 'P576'
STARTDTPROP = 'P580'
ENDDTPROP = 'P582'
OPERDTPROP = 'P729'
SERVRETDTPROP = 'P730'
LASTNAMEPROP = 'P734'
FIRSTNAMEPROP = 'P735'
MAINCATPROP = 'P910'
VOYAGEBANPROP = 'P948'
COMMGALPROP = 'P935'
PDFPROP = 'P996'
JURISDICTPROP = 'P1001'
BUSINESSPARTNERPROP = 'P1327'
LANGKNOWPROP = 'P1412'
GRAVEPROP = 'P1442'
COMMCREATPROP = 'P1472'
NATIVENAMEPROP = 'P1559'
COMMINSTPROP = 'P1612'
PLACENAMEPROP = 'P1766'
PLAQUEPROP = 'P1801'
NOTEQTOPROP = 'P1889'
ICONPROP = 'P2910'
PARTITUREPROP = 'P3030'
NIGHTVIEWPROP = 'P3451'
WINTERVIEWPROP = 'P5252'
DIAGRAMPROP = 'P5555'
INTERIORPROP = 'P5775'
VERSOPROP = 'P7417'
RECTOPROP = 'P7418'
FRAMEWORKPROP = 'P7420'
VIEWPROP = 'P8517'
AERIALVIEWPROP = 'P8592'
FAVICONPROP = 'P8972'
COLORWORKPROP = 'P10093'

# Namespaces
# https://www.mediawiki.org/wiki/Help:Namespaces
# https://nl.wikipedia.org.org/w/api.php?action=query&meta=siteinfo&siprop=namespaces&formatversion=2
MAINNAMESPACE = 0
FILENAMESPACE = 6
CATEGORYNAMESPACE = 14

media_props = {
    AERIALVIEWPROP,
    COATOFARMSPROP,
    COLORWORKPROP,
    DIAGRAMPROP,
    FAVICONPROP,
    FLAGPROP,
    FRAMEWORKPROP,
    GRAVEPROP,
    ICONPROP,
    IMAGEPROP,
    INTERIORPROP,
    LOCATORMAPPROP,
    LOGOPROP,
    MAPPROP,
    NIGHTVIEWPROP,
    PARTITUREPROP,
    PDFPROP,
    PLACENAMEPROP,
    PLAQUEPROP,
    RECTOPROP,
#    SIGNATUREPROP,
    VERSOPROP,
    VIDEOPROP,
    VIEWPROP,
    VOYAGEBANPROP,
    WINTERVIEWPROP,
}

conflicting_statement = {
    EQTOPROP: NOTEQTOPROP,
}

mandatory_relation = {  # via P1696
    # Symmetric
    BUSINESSPARTNERPROP: BUSINESSPARTNERPROP,
    BORDERPEERPROP: BORDERPEERPROP,
    EQTOPROP: EQTOPROP,
    MARIAGEPARTNERPROP: MARIAGEPARTNERPROP,
    NOTEQTOPROP: NOTEQTOPROP,
    PARTNERPROP: PARTNERPROP,

    # Reciproque
    CHILDPROP: FATHERPROP, FATHERPROP: CHILDPROP,
    CONTAINSPROP: PARTOFPROP, PARTOFPROP: CONTAINSPROP,
    MAINCATPROP: MAINSUBJECTPROP, MAINSUBJECTPROP: MAINCATPROP,
}

# Prepare the static part of the SDC P180 depict statement
# The numeric value needs to be added at runtime
depict_statement = {
    'claims': [{
        'type': 'statement',
        'rank': 'preferred',    # Because it comes from a Wikidata P18 statement
        'mainsnak': {
            'snaktype': 'value',
            'property': DEPICTSPROP,
            'datavalue': {
                'type': 'wikibase-entityid',
                'value': {
                    'entity-type': 'item',
                    # 'numeric-id',
                    # 'id' are dynamically added
                }
            }
        }
    }]
}

"""
    Static definitions
"""

# Functional configuration flags
# Restrictions: cannot disable both labels and wikipedia. We need at least one of the options.
repldesc = False        # Replicate instance description labels
uselabels = True	    # Use the language labels (disable with -l)

# Technical configuration flags
# Defaults: transparent and safe
errorstat = True        # Show error statistics (disable with -e)
exitfatal = True	    # Exit on fatal error (can be disabled with -p; please take care)
forcecopy = False	    # Force copy
lead_lower = False      # Leading lowercase
lead_upper = False      # Leading uppercase
overrule = False        # Overrule
repeatmode = False      # Repeat mode
readonly = False        # Dry-run
shell = True		    # Shell available (command line parameters are available; automatically overruled by PAWS)
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

# Language settings
ENLANG = 'en'
enlang_list = [ENLANG]

# human, last name, male first name, female first name, neutral first name, affixed family name, family, personage
human_list = {HUMANINSTANCE, 'Q101352', 'Q12308941', 'Q11879590', 'Q3409032', 'Q66480858', 'Q8436', 'Q95074'}

# last name, affixed family name, compound, toponiem
lastname_list = {'Q101352', 'Q66480858', 'Q60558422', 'Q17143070'}

# Add labels for all those (Roman) languages
# Do not add Central European languages like cs, hu, pl, sk, etc. because of special language rules
# Not Hungarian, Czech, Polish, Slovak, etc
all_languages = {'af', 'an', 'ast', 'ca', 'cy', 'da', 'de', 'en', 'es', 'fr', 'ga', 'gl', 'io', 'it', 'jut', 'nb', 'nl', 'nn', 'pms', 'pt', 'sc', 'sco', 'sje', 'sl', 'sq', 'sv'}

# Default natural languages for mother tongue (others will be added automatically)
nat_languages = {'Q1321', 'Q150', 'Q1860', 'Q188', 'Q652', 'Q7411'}

# levende taal, natuurlijke taal, taal => amend list of nat_languages
lang_item = {'Q1288568', 'Q33742', 'Q34770'}

# Languages using uppercase nouns
## Check if we can inherit namespace or language properties??
upper_pref_lang = {'als', 'atj', 'bar', 'bat-smg', 'bjn', 'co?', 'dag', 'de', 'de-at', 'de-ch', 'diq', 'eu?', 'ext', 'fiu-vro', 'frp', 'ffr?', 'gcr', 'gsw', 'ha', 'hif?', 'ht', 'ik?', 'kaa?', 'kab', 'kbp?', 'ksh', 'lb', 'lfn?', 'lg', 'lld', 'mwl', 'nan', 'nds', 'nds-nl?', 'om?', 'pdc?', 'pfl', 'rmy', 'rup', 'sgs', 'shi', 'sn', 'tum', 'vec', 'vmf', 'vro', 'wo?'}

# Skip not yet described Wikipedia family members
new_wikis = {'altwiki', 'amiwiki', 'anpwiki', 'arywiki', 'avkwiki', 'guwwiki', 'kcgwiki', 'lldwiki', 'madwiki', 'mniwiki', 'pwnwiki','shiwiki', 'skrwiki', 'taywiki'}

# Risk for non-roman languages
veto_countries = {'Q148', 'Q159', 'Q15180' }

# Veto languages
# Skip non-standard character encoding; see also ROMANRE (other name rules)
# see https://en.wikipedia.org/wiki/Wikipedia:Naming_conventions_(Cyrillic)
veto_languages = {'aeb', 'aeb-arab', 'aeb-latn', 'ar', 'arc', 'arq', 'ary', 'arz', 'bcc', 'be' ,'be-tarask', 'bg', 'bn', 'bgn', 'bqi', 'cs', 'ckb', 'cv', 'dv', 'el', 'fa', 'fi', 'gan', 'gan-hans', 'gan-hant', 'glk', 'gu', 'he', 'hi', 'hu', 'hy', 'ja', 'ka', 'khw', 'kk', 'kk-arab', 'kk-cn', 'kk-cyrl', 'kk-kz', 'kk-latn', 'kk-tr', 'ko', 'ks', 'ks-arab', 'ks-deva', 'ku', 'ku-arab', 'ku-latn', 'ko', 'ko-kp', 'lki', 'lrc', 'lzh', 'luz', 'mhr', 'mk', 'ml', 'mn', 'mzn', 'ne', 'new', 'or', 'os', 'ota', 'pl', 'pnb', 'ps', 'ro', 'ru', 'rue', 'sd', 'sdh', 'sh', 'sk', 'sr', 'sr-ec', 'ta', 'te', 'tg', 'tg-cyrl', 'tg-latn', 'th', 'ug', 'ug-arab', 'ug-latn', 'uk', 'ur', 'vep', 'vi', 'yi', 'yue', 'zg-tw', 'zh', 'zh-cn', 'zh-hans', 'zh-hant', 'zh-hk', 'zh-mo', 'zh-my', 'zh-sg', 'zh-tw'}

veto_sitelinks = {
#'nowiki',   # Blocked https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot
'slwiki',   # Requires wikibot flag
'ptwiki', 'ruwiki', 'ttwiki', 'wuuwiki',  # Requires CAPTCHA
#'be-taraskwiki',                # instantiated using different code "be-x-old"
}

# Lookup table for language qnumbers
lang_qnumbers = {'aeb':'Q56240', 'ar':'Q13955', 'arc':'Q28602', 'arq':'Q56499', 'ary':'Q56426', 'arz':'Q29919', 'bcc':'Q12634001', 'be':'Q9091', 'be-tarask':'Q8937989', 'bg':'Q7918', 'bn':'Q9610', 'bgn':'Q12645561', 'bqi':'Q257829', 'cs':'Q9056', 'ckb':'Q36811', 'cv':'Q33348', 'da':'Q9035', 'de':'Q188', 'dv':'Q32656', 'el':'Q9129', 'en':'Q1860', 'es':'Q1321', 'fa':'Q9168', 'fi':'Q1412', 'fr':'Q150', 'gan':'Q33475', 'gan-hans':'Q64427344', 'gan-hant':'Q64427346', 'gl':'Q9307', 'glk':'Q33657', 'gu':'Q5137', 'he':'Q9288', 'hi':'Q1568', 'hu':'Q9067', 'hy':'Q8785', 'it':'Q652', 'ja':'Q5287', 'ka':'Q8108', 'khw':'Q938216', 'kk':'Q9252', 'kk-arab':'Q90681452', 'kk-cn':'Q64427349', 'kk-cyrl':'Q90681280', 'kk-kz':'Q64427350', 'kk-tr':'Q64427352', 'ko':'Q9176', 'ko-kp':'Q18784', 'ks':'Q33552', 'ku':'Q36368', 'lki':'Q18784', 'lrc':'Q19933293', 'lzh':'Q37041', 'luz':'Q12952748', 'mhr':'Q12952748', 'mk':'Q9296', 'ml':'Q36236', 'mn':'Q9246', 'mzn':'Q13356', 'ne':'Q33823', 'new':'Q33979', 'nl':'Q7411', 'no':'Q9043', 'or':'Q33810', 'os':'Q33968', 'ota':'Q36730', 'pl':'Q809', 'pnb':'Q1389492', 'ps':'Q58680', 'pt':'Q5146', 'ro':'Q7913', 'ru':'Q7737', 'rue':'Q26245', 'sd':'Q33997', 'sdh':'Q1496597', 'sh':'Q9301', 'sk':'Q9058', 'sl':'Q9063', 'sr':'Q9299', 'sv':'Q9027', 'ta':'Q5885', 'te':'Q8097', 'tg':'Q9260', 'th':'Q9217', 'ug':'Q13263', 'uk':'Q8798', 'ur':'Q1617', 'vep':'Q32747', 'vi':'Q9199', 'yi':'Q8641', 'yue':'Q9186', 'zh':'Q7850', 'zh-cn':'Q24841726', 'zh-hant':'Q18130932', 'zh-hk':'Q100148307', 'zh-mo':'Q64427357', 'zh-my':'Q13646143', 'zh-sg':'Q1048980', 'zh-tw':'Q4380827'}

# Automatically built from veto_languages and lang_qnumbers
veto_languages_id = {'Q7737', 'Q8798'}

# Accepted language scripts (e.g. Latin)
script_whitelist = {'Q8229'}

# To be set in user-config.py (which parameters is PAWS using?)
"""
    maxlag = 5          # avoid overloading the servers
    max_retries = 4     # avoid overloading the servers
    maxthrottle = 60    # ?
    noisysleep = 60.0   # avoid the majority/all of the confusing sleep messages (noisy sleep)
    put_throttle = 1    # maximum transaction speed (bot account required)
    retry_max = 320     # avoid overloading the servers
    retry_wait = 30     # avoid overloading the servers
"""


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


def get_canon_name(baselabel) -> str:
    """Get standardised name
    :param baselabel: input label
    :return cononical label

    Algorithm:
        remove () suffix
        reverse , name parts
    """
    suffix = PSUFFRE.search(baselabel)  	        # Remove () suffix, if any
    if suffix:
        baselabel = baselabel[:suffix.start()]  # Get canonical form

    colonloc = baselabel.find(':')
    commaloc = NAMEREVRE.search(baselabel)

    # Reorder "lastname, firstname" and concatenate with space
    if colonloc < 0 and commaloc:
        baselabel = baselabel[commaloc.start() + 1:] + ' ' + baselabel[:commaloc.start()]
        baselabel = baselabel.replace(',',' ')  # Multiple ,
    baselabel = ' '.join(baselabel.split()) # Remove redundant spaces
    return baselabel


def get_item_label(item) -> str:
    """
    Get the item label.
    """
    label = ''
    for lang in main_languages:
        if lang in item.labels:
            label = item.labels[lang]
            break
    return label


def get_item(qnumber):
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
            label = get_item_label(item)
            pywikibot.warning('Item {} ({}) redirects to {}'
                              .format(label, qnumber, item.getID()))
    else:
        item = qnumber

    while item.isRedirectPage():
        ## Should fix the sitelinks
        item = item.getRedirectTarget()

    return item


def get_item_header(header) -> str:
    """
    Get the item header (label, description, alias in user language)

    :param: item label, description, or alias language list
    :return: label, description, or alias in the first available language
    """
    header_value = ''
    for lang in label_languages:
        if lang in header:
            header_value = header[lang]
            break
    return header_value


def get_item_label_dict(qnumber) -> {}:
    """
    Get the Wikipedia labels in all languages for a Qnumber.
    :param qnumber: label list
    :return: label list
    Example of usage:
        Image namespace name.
    """
    labeldict = {}
    item = pywikibot.ItemPage(repo, qnumber)
    # Get target labels
    for lang in item.labels:
        labeldict[lang] = item.labels[lang]
    return labeldict


def get_item_sitelink_dict(qnumber) -> {}:
    """
    Get the Wikipedia template names in all languages for a Qnumber.
    :param qnumber: sitelink list
    :return: sitelink list
    Example of usage:
        Generate {{Commonscat}} statements for Q48029.
    """
    sitedict = {}
    item = pywikibot.ItemPage(repo, qnumber)
    # Get target sitelinks
    for sitelang in item.sitelinks:
        if '_' not in sitelang:
            try:
                sitelink = item.sitelinks[sitelang]
                if str(sitelink.site.family) == 'wikipedia':
                    sitedict[sitelang] = sitelink.title
            except:
                pass
    return sitedict


def get_sdc_item(sdc_data):
    """
    Get the item from the SDC statement.
    """
    qnumber = sdc_data['datavalue']['value']['id']

    # Get item
    item = get_item(qnumber)
    if item.getID() != qnumber:
        ## Retroactively update the SDC statement for redirect
        qnumber = item.getID()   ## Python doesn't know call by reference...
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


def get_prop_val(item, proplist) -> str:
    """Get property value
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
    return item_prop_val


def get_prop_val_object_label(item, proplist) -> str:
    """Get property value
    :param item: Wikidata item
    :param proplist: Search list of properties
    :return: concatenated list of value labels
    """
    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:
            for seq in item.claims[prop]:
                val = seq.getTarget()
                try:
                    item_prop_val += val.labels[mainlang] + '/'
                except:     # Skip unlabeled items
                    pass
            break
    return item_prop_val


def get_prop_val_year(item, proplist) -> str:
    """Get death date (normally only one)
    :param item: Wikidata item
    :param proplist: Search list of date properties
    :return: first matching date
    """
    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:
            for seq in item.claims[prop]:
                val = seq.getTarget()
                try:
                    item_prop_val += str(val.year) + '/'
                except:     # Skip bad dates
                    pass
            break
    return item_prop_val


def is_foreign_lang(lang_list) -> bool:
    """ Check if foreign language"""
    isforeign = False
    for seq in lang_list:
        if not ROMANRE.search(seq):
            isforeign = True
            break
    return isforeign


def is_in_list(statement_list, checklist) -> bool:
    """
    Verify if statement list contains at least one item from the checklist
    param: statement_list: Statement list
    param: checklist:      List of values (string)
    return: Boolean (True when match)
    """
    isinlist = False
    for seq in statement_list:
        try:
            if seq.getTarget().getID() in checklist:
                isinlist = True
                break
        except:
            pass    # Ignore NoneType error
    return isinlist


def is_veto_lang_label(lang_list) -> bool:
    """
    Check if lanuage is blacklisted
    """
    isveto = False
    for seq in lang_list:
        if (seq.getTarget().language in veto_languages_id
                or not ROMANRE.search(seq.getTarget().text)):
            isveto = True
            break
    return isveto


def is_veto_script(script_list) -> bool:
    """
    Check if script is in veto list
    """
    isveto = False
    for seq in script_list:
        # Nonroman script
        try:
            if seq.getTarget().getID() not in script_whitelist:
                isveto = True
                break
        except:
            pass    # Ignore NoneType error
    return isveto


def add_missing_depicts(item):
    """
    Add missing SDC depict statements
    """
    # Find all media files for the item
    qnumber = item.getID()
    for prop in media_props:
        if prop in item.claims:
            for seq in item.claims[prop]:
                depict_missing = True
                media_page = seq.getTarget()
                media_name = media_page.title()
                media_identifier = 'M' + str(media_page.pageid)
                sdc_request = site.simple_request(action='wbgetentities', ids=media_identifier)
                commons_item = sdc_request.submit()
                sdc_data = commons_item.get('entities').get(media_identifier)
                sdc_statements = sdc_data.get('statements')
                # Verify if there is already a depict statement
                if sdc_statements:
                    depict_list = sdc_statements.get(DEPICTSPROP)
                    if depict_list:
                        for depict in depict_list:
                            if qnumber == get_sdc_item(depict['mainsnak']).getID():
                                depict_missing = False
                                break

                """
https://commons.wikimedia.org/wiki/Special:EntityData/M82236232.json
"P180":[{"mainsnak":{"snaktype":"value","property":"P180","hash":"7282af9508eed4a6f6ebc2e92db7368ecdbb61ab","datavalue":{"value":{"entity-type":"item","numeric-id":22668172,"id":"Q22668172"},"type":"wikibase-entityid"}},"type":"statement","id":"M82236232$e1491557-469c-7672-92d6-6e490f7403bf","rank":"normal"}],

"P180":[{"mainsnak":{"snaktype":"value","property":"P180","datavalue":{"value":{"entity-type":"item","numeric-id":22668172,"id":"Q22668172"},"type":"wikibase-entityid"}},"type":"statement","rank":"normal"}],
                """
                if depict_missing:
                    # Add the SDC depict statements for this item
                    depict_statement['claims'][0]['mainsnak']['datavalue']['value']['numeric-id'] = int(qnumber[1:])
                    depict_statement['claims'][0]['mainsnak']['datavalue']['value']['id'] = qnumber

                    sdc_payload = {
                        'action': 'wbeditentity',
                        'format': 'json',
                        'id': media_identifier,
                        'data': json.dumps(depict_statement, separators=(',', ':')),
                        'token': csrf_token,
                        'summary': '#pwb Add depicts statement',
                        'bot': BOTFLAG,
                    }

                    sdc_request = site.simple_request(**sdc_payload)
                    try:
                        sdc_request.submit()
                        pywikibot.warning('Add SDC depicts {} to {} {}'
                                          .format(qnumber, media_identifier, media_name))
                    except pywikibot.data.api.APIError as error:
                        pywikibot.error(format(error))
                        pywikibot.info(sdc_request)


def wd_proc_all_items():
    """
    Module logic
    """

    global exitstat
    global commonscatqueue
    global lastwpedit

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    statcount = 0           # Statement count
    pictcount = 0	    	# Picture count
    safecount = 0	    	# Safe transaction
    errcount = 0	    	# Error counter
    errsleep = 0	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    pywikibot.warning('\nProcessing {:d} statements'.format(len(item_list)))

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for qnumber in item_list:	# Main loop for all DISTINCT items
      if status == 'Stop':	# Ctrl-c pressed -> stop in a proper way
        break

      if qnumber > 'Q':     # Allows a restart
        pywikibot.log('Processing {}'.format(qnumber)) 	# New transaction
        transcount += 1

        status = 'OK'
        alias = ''
        descr = ''
        commonscat = ''     # Commons category
        nationality = ''
        label = ''
        birthday = ''
        deathday = ''

        try:		        # Error trapping (prevents premature exit on transaction error)
            item = pywikibot.ItemPage(repo, qnumber)

            try:
                item.get()
            except pywikibot.exceptions.IsRedirectPageError:
                # Resolve a single redirect error
                item = item.getRedirectTarget()
                pywikibot.warning('Item {} redirects to {}'.format(qnumber, item.getID()))
                qnumber = item.getID()

            # Instance type could be missing
            try:
                instprop = item.claims[INSTANCEPROP][0].getTarget()
                item_instance = instprop.getID()
            except:
                item_instance = ''

            label = get_item_header(item.labels)            # Get label

            nationality = get_prop_val_object_label(item,   [NATIONALITYPROP, CTRYPROP, CTRYORIGPROP, JURISDICTPROP])    # nationality
            birthday    = get_prop_val_year(item,           [BIRTHDTPROP, FOUNDDTPROP, STARTDTPROP, OPERDTPROP])    # birth date (normally only one)
            deathday    = get_prop_val_year(item,           [DEATHDTPROP, DISSOLVDTPROP, ENDDTPROP, SERVRETDTPROP]) # death date (normally only one)

            # Cleanup the label
            if label:
                # Remove redundant trailing writing direction
                while len(label) > 0 and label[len(label)-1] in [ '\u200e', '\u200f']:
                    label=label[:len(label)-1]
                # Replace alternative space character
                label = label.replace('\u00a0', ' ').strip()

                if NATIONALITYPROP not in item.claims:  # Missing nationality (old names)
                    status = 'Nationality'
                elif is_in_list(item.claims[NATIONALITYPROP], veto_countries):         # nationality blacklist (languages)
                    status = 'Country'
                elif not ROMANRE.search(label) or mainlang in item.aliases and is_foreign_lang(item.aliases[mainlang]):
                    status = 'Language'
                elif NATIVENAMEPROP in item.claims and is_veto_lang_label(item.claims[NATIVENAMEPROP]):         # name in native language
                    status = 'Language'
                elif NATIVELANGPROP in item.claims and is_in_list(item.claims[NATIVELANGPROP], veto_languages_id):     # native language
                    status = 'Language'
                elif LANGKNOWPROP in item.claims and is_in_list(item.claims[LANGKNOWPROP], veto_languages_id):  # language knowledge
                    status = 'Language'
                elif FOREIGNSCRIPTPROP in item.claims and is_veto_script(item.claims[FOREIGNSCRIPTPROP]):       # foreign script system
                    status = 'Script'
                elif NOBLENAMEPROP in item.claims:  # Noble names are exceptions
                    status = 'Noble'
                elif item_instance in human_list:
                    label = get_canon_name(label)
            else:
                status = 'No label'         # Missing label

            if not (item_instance in human_list or forcecopy):   # Force label copy
                status = 'Item'             # Non-human item

# (1) Fix the "no" issue
            # Move no label to nb, and possibly to aliases
            if 'no' in item.labels:
                if 'nb' not in item.labels:
                    item.labels['nb'] = item.labels['no']
                if 'nb' not in item.aliases:
                    item.aliases['nb'] = [item.labels['no']]
                elif item.labels['no'] not in item.aliases['nb']:
                    item.aliases['nb'].append(item.labels['no'])
                item.labels['no'] = ''

            # Move no aliases to nb
            if 'no' in item.aliases:
                if 'nb' in item.aliases:
                    for seq in item.aliases['no']:
                        if seq and seq not in item.aliases['nb']:
                            item.aliases['nb'].append(seq)
                else:
                    item.aliases['nb'] = item.aliases['no']
                item.aliases['no'] = []

            # Move no descriptions to nb
            if 'no' in item.descriptions:
                if 'nb' not in item.descriptions:
                    item.descriptions['nb'] = item.descriptions['no']
                item.descriptions['no'] = ''

# (2) Merge sitelinks (gets priority above default value)
            noun_in_lower = False
            # Get target sitelink
            for sitelang in item.sitelinks:
                # Process only known Wikipedia links (skip other projects)
                sitelink = item.sitelinks[sitelang]
                if (sitelang not in new_wikis
                        and str(sitelink.site.family) == 'wikipedia'):
                    lang = sitelink.site.lang
                    baselabel = sitelink.title
                    ## language caps

                    # See https://www.wikidata.org/wiki/User_talk:GeertivpBot#Don%27t_use_%27no%27_label
                    if lang == 'bh':    # Canonic language names
                        lang = 'bho'
                    elif lang == 'no':
                        lang = 'nb'

                    # Only clean human names
                    if item_instance in human_list:
                        baselabel = get_canon_name(baselabel)

                    # Wikipedia lemmas are in leading uppercase
                    # Wikidata lemmas are in lowercase, unless:
                    if (item_instance in human_list
                            or lang in veto_languages
                            or not ROMANRE.search(baselabel)
                            or not ROMANRE.search(label)
                            or sitelink.namespace != MAINNAMESPACE):
                        # Keep case sensitive or Non-Roman characters
                        pass
                    elif (lead_lower
                            or SUBCLASSPROP in item.claims
                            or lang in item.labels and item.labels[lang][0].islower()
                            or lang in item.aliases and item.aliases[lang][0][0].islower()
                            or len(label) > 0 and label[0].islower()):
                        # Subclasses in lowercase
                        # Lowercase first character
                        noun_in_lower = True
                        baselabel = baselabel[0].lower() + baselabel[1:]
                    elif (lead_upper
                            or lang in item.labels and item.labels[lang][0].isupper()
                            or lang in item.aliases and item.aliases[lang][0][0].isupper()
                            or len(label) > 0 and label[0].isupper()
                            or lang in upper_pref_lang):
                        # Uppercase first character
                        pass
                    elif len(label) > 0 and label[0].islower():
                        # Lowercase first character
                        noun_in_lower = True
                        baselabel = baselabel[0].lower() + baselabel[1:]

                    pywikibot.debug('Page {}:{}:{}'
                                    .format(lang,
                                            sitelink.site.namespace(sitelink.namespace),
                                            baselabel))

                    # Register new label if not already present
                    item_name_canon = unidecode.unidecode(baselabel).casefold()
                    if sitelink.namespace != MAINNAMESPACE:
                        # Only handle main namespace
                        pass
                    elif lang not in item.labels:
                         # Missing label
                        item.labels[lang] = baselabel
                    elif item_name_canon == unidecode.unidecode(item.labels[lang]).casefold():
                        # Ignore accents
                        pass
                    elif lang not in item.aliases:
                        # Assign single alias
                        item.aliases[lang] = [baselabel]
                    else:
                        for seq in item.aliases[lang]:
                            if item_name_canon == unidecode.unidecode(seq).casefold():
                                break
                        else:
                            # Merge aliases
                            item.aliases[lang].append(baselabel)

# (3) Replicate instance descriptions
            # Get description from the EN Wikipedia
            # To our opinion the wp.en Short description template is useless;
            # it should copy the description from Wikidata instead...
            # anyway we can store the value in Wikidata if it is available in WP and missing in WD
            if (ENLANG in item.sitelinks
                    and ENLANG not in item.descriptions):
                sitelink = item.sitelinks[ENLANG]
                page = pywikibot.Page(sitelink.site, sitelink.title, sitelink.namespace)
                if sitelink.namespace == MAINNAMESPACE and page.text:
                    pagedesc = SHORTDESCRE.search(page.text)
                    if pagedesc:
                        itemdesc = pagedesc[1]
                        itemdesc = itemdesc[0].lower() + itemdesc[1:]   ## Always lowercase?
                        item.descriptions[ENLANG] = itemdesc

            # Replicate from the Property label
            if repldesc and item_instance:
                for lang in instprop.labels:
                    if overrule or lang not in item.descriptions:
                        item.descriptions[lang] = instprop.labels[lang].replace(':', ' ')

            if status == 'OK' and label and uselabels:      ## and ' ' in label.find ??
                if lead_lower:
                   # Lowercase first character
                   label = label[0].lower() + label[1:]
                elif lead_upper:
                   # Uppercase first character
                   label = label[0].upper() + label[1:]

                # Ignore accents
                # Skip non-Roman languages
                item_label_canon = unidecode.unidecode(label).casefold()

# (4) Add missing aliases for labels
                for lang in item.labels:
                    if lang not in veto_languages and ROMANRE.search(item.labels[lang]):
                        if unidecode.unidecode(item.labels[lang]).casefold() != item_label_canon:
                            if lang not in item.aliases:
                                item.aliases[lang] = [label]
                            elif label not in item.aliases[lang]:
                                item.aliases[lang].append(label)        # Merge aliases

# (5) Add missing labels or aliases for descriptions
                for lang in item.descriptions:
                    if lang not in veto_languages and ROMANRE.search(item.descriptions[lang]):
                        if lang not in item.labels:
                            item.labels[lang] = label
                        elif unidecode.unidecode(item.labels[lang]).casefold() != item_label_canon:
                            if lang not in item.aliases:
                                item.aliases[lang] = [label]
                            elif label not in item.aliases[lang]:
                                item.aliases[lang].append(label)        # Merge aliases

# (6) Merge labels for Latin languages
                for lang in all_languages:
                    if lang not in item.labels:
                        item.labels[lang] = label
                    elif unidecode.unidecode(item.labels[lang]).casefold() != item_label_canon:
                        if lang not in item.aliases:
                            item.aliases[lang] = [label]
                        elif label not in item.aliases[lang]:
                            item.aliases[lang].append(label)            # Merge aliases

# (7) Move first alias to any missing label
            for lang in item.aliases:
                if (lang not in item.labels
                        and lang in all_languages
                        and lang in item.descriptions
                        and ROMANRE.search(item.descriptions[lang])):
                    for seq in item.aliases[lang]:
                        if ROMANRE.search(seq):
                            pywikibot.log('Move {} alias {} to label'.format((lang, seq)))
                            item.labels[lang] = seq                     # Move single alias
                            item.aliases[lang].remove(seq)
                            break

# (8) Add missing Wikipedia sitelinks
            for lang in main_languages:
                sitelang = lang + 'wiki'
                if lang == 'bho':
                    sitelang = 'bhwiki'
                elif lang == 'nb':
                    sitelang = 'nowiki'

                # Add missing sitelinks
                if sitelang not in item.sitelinks:
                    # This section contains a complicated recursive error handling algorithm.
                    # SetSitelinks nor editEntity can't be used because it stops at the first error, and we need more control.
                    # Two or more sitelinks can have conflicting Qnumbers. Add mutual "Not Equal" claims via the exception section...
                    # Sitelink pages might not be available (quick escape via except pass; error message is printed).
                    if lang in item.labels:
                        sitedict = {'site': sitelang, 'title': item.labels[lang]}
                        try:
                            item.setSitelink(sitedict, bot=BOTFLAG, summary='#pwb Add sitelink')
                            status = 'Sitelink'
                        except pywikibot.exceptions.OtherPageSaveError as error:
                            # Get unique Q-numbers, skip duplicates (order not guaranteed)
                            itmlist = set(QSUFFRE.findall(str(error)))
                            if len(itmlist) > 1:
                                itmlist.remove(qnumber)
                                pywikibot.error('Conflicting sitelink statement {} {}:{}, {}'
                                                .format(qnumber, sitelang, item.labels[lang], itmlist))
                                status = 'DupLink'	    # Conflicting sitelink statement
                                errcount += 1
                                exitstat = max(exitstat, 10)

                    if sitelang not in item.sitelinks and lang in item.aliases:
                        for seq in item.aliases[lang]:
                            sitedict = {'site': sitelang, 'title': seq}
                            try:
                                item.setSitelink(sitedict, bot=BOTFLAG, summary='#pwb Add sitelink')
                                status = 'Sitelink'
                                break
                            except pywikibot.exceptions.OtherPageSaveError as error:
                                # Get unique Q-numbers, skip duplicates (order not guaranteed)
                                itmlist = set(QSUFFRE.findall(str(error)))
                                if len(itmlist) > 1:
                                    itmlist.remove(qnumber)
                                    pywikibot.error('Conflicting sitelink statement {} {}:{}, {}'
                                                    .format(qnumber, sitelang, seq, itmlist))
                                    status = 'DupLink'	    # Conflicting sitelink statement
                                    errcount += 1
                                    exitstat = max(exitstat, 10)

            maincat_item = '';
            # Add inverse statement
            if MAINCATPROP in item.claims:
                maincat_item = get_item(item.claims[MAINCATPROP][0].getTarget())

# (9) Set Commons Category sitelinks
            # Search for candidate Commons Category
            if COMMCATPROP in item.claims:                  # Get candidate category
                commonscat = item.claims[COMMCATPROP][0].getTarget() # Only take first value
            elif 'commonswiki' in item.sitelinks:           # Commons sitelink exists
                sitelink = item.sitelinks['commonswiki']
                commonscat = sitelink.title
                colonloc = commonscat.find(':')
                if colonloc >= 0:
                    commonscat = commonscat[colonloc + 1:]
            elif maincat_item and COMMCATPROP in maincat_item:
                commonscat = maincat_item.claims[COMMCATPROP][0].getTarget()
            elif COMMGALPROP in item.claims:                # Commons gallery page
                commonscat = item.claims[COMMGALPROP][0].getTarget()
            elif COMMCREATPROP in item.claims:              # Commons creator page
                commonscat = item.claims[COMMCREATPROP][0].getTarget()
            elif COMMINSTPROP in item.claims:               # Commons institution page
                commonscat = item.claims[COMMINSTPROP][0].getTarget()
            elif item_instance in lastname_list:
                commonscat = label + ' (surname)'
            elif enlang_list[0] in item.labels:             # English label might possibly be used as Commons category
                commonscat = item.labels[enlang_list[0]]
            elif mainlang in item.labels:                   # Otherwise the native label
                commonscat = item.labels[mainlang]

            # Try to create a Wikimedia Commons Category page
            if commonscat and 'commonswiki' not in item.sitelinks:
                sitedict = {'site': 'commonswiki', 'title': 'Category:' + commonscat}
                try:
                    item.setSitelink(sitedict, bot=BOTFLAG, summary='#pwb Add sitelink')
                    status = 'Commons'
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

            if commonscat:
                # Amend EN label from Commons Category
                item_name_canon = unidecode.unidecode(commonscat).casefold()
                baselabel = commonscat
                # Lowercase first character
                if noun_in_lower:
                    baselabel = baselabel[0].lower() + baselabel[1:]

                for lang in enlang_list:
                    # Add a missing EN label
                    if lang not in item.labels:
                        item.labels[lang] = baselabel
                    elif item_name_canon == unidecode.unidecode(item.labels[lang]).casefold():    # Ignore accents
                        pass
                    elif lang not in item.aliases:
                        item.aliases[lang] = [baselabel]       # Assign single alias
                    else:
                        for seq in item.aliases[lang]:
                            if item_name_canon == unidecode.unidecode(seq).casefold():
                                break
                        else:
                            item.aliases[lang].append(baselabel)    # Merge aliases

                # Add Commons category
                if COMMCATPROP not in item.claims:
                    claim = pywikibot.Claim(repo, COMMCATPROP)
                    claim.setTarget(commonscat)
                    item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                    status = 'Update'

                # Add Wikidata Infobox
                page = pywikibot.Category(site, commonscat)
                # Avoid duplicates and Category redirect
                if not page.text:
                    pywikibot.warning('Empty Wikimedia Commons category page: {}'
                                      .format(commonscat))
                elif not WDINFOBOX.search(page.text):
                    page.text = '{{Wikidata Infobox}}\n' + page.text
                    page.save('#pwb Add Wikidata Infobox')
                    status = 'Update'

            # Add missing Commonscat statements to Wikipedia
            for sitelang in item.sitelinks:
                # Get target sitelink
                if (sitelang in commonscatlist[0]
                        and sitelang not in new_wikis
                        and item.sitelinks[sitelang].namespace == MAINNAMESPACE):
                    # Wikipedia should only have 4 transactions per minute (no bot account)
                    wpcatpage = ''
                    if maincat_item and sitelang in maincat_item.sitelinks:
                        wpcatpage = maincat_item.sitelinks[sitelang].title
                    commonscatqueue.append((item, sitelang, item_instance, commonscat, wpcatpage))

# (10) Remove duplicate aliases for all languages: for each label remove all equal aliases
            for lang in item.labels:
                if lang in item.aliases:
                    while item.labels[lang] in item.aliases[lang]:      # Remove redundant aliases
                        item.aliases[lang].remove(item.labels[lang])

# (11) Now store the header changes
            try:
                pywikibot.debug(item.labels)
                item.editEntity({'labels': item.labels,
                                 'descriptions': item.descriptions,
                                 'aliases': item.aliases}, summary=transcmt)
            except pywikibot.exceptions.OtherPageSaveError as error:    # Duplicate description
                pywikibot.error('Error saving entity {}, {}'.format(qnumber, error))
                status = 'DupDescr'
                errcount += 1
                exitstat = max(exitstat, 14)
                #raise      # This error might hide more data quality problems

# (12) Replicate Moedertaal -> Taalbeheersing
            if NATIVELANGPROP in item.claims:
                target = get_item(item.claims[NATIVELANGPROP][0].getTarget())
                nat_languages.add(target.getID())           # Add a natural language

                personlang = set()
                if LANGKNOWPROP in item.claims:
                    for seq in item.claims[LANGKNOWPROP]:   # Get all person languages
                        personlang.add(get_item(seq.getTarget()).getID())
                    pywikibot.log('Person languages: {} {}'
                                  .format(target.getID(), personlang))

                if target.getID() not in personlang:        # Add another value?
                    pywikibot.warning('Add {}:{}'.format(LANGKNOWPROP, target.getID()))
                    claim = pywikibot.Claim(repo, LANGKNOWPROP)
                    claim.setTarget(target)
                    item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                    status = 'Update'

# (13) Replicate Taalbeheersing -> Moedertaal
            if (NATIVELANGPROP not in item.claims
                    and LANGKNOWPROP in item.claims
                    and len(item.claims[LANGKNOWPROP]) == 1):
                target = get_item(item.claims[LANGKNOWPROP][0].getTarget())

                # Add natural language
                if target.getID() not in nat_languages and target.getID() != ESPERANTOLANGINSTANCE:
                    if INSTANCEPROP in target.claims:
                        for seq in target.claims[INSTANCEPROP]: # Get all languages types
                            if seq.getTarget().getID() not in lang_item:
                                break                           # We only want natural languages
                        else:
                            nat_languages.add(target.getID())   # Add a natural language

                # Add one single mother tongue (filter non-natural languages like Esperanto)
                if target.getID() in nat_languages:
                    pywikibot.warning('Add {}:{}'.format(NATIVELANGPROP, target.getID()))
                    claim = pywikibot.Claim(repo, NATIVELANGPROP)
                    claim.setTarget(target)
                    item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                    status = 'Update'
                elif (NATIVENAMEPROP in item.claims
                        and len(item.claims[NATIVENAMEPROP]) == 1):
                    # Name in native language
                    mothlang = item.claims[NATIVENAMEPROP][0].getTarget().language
                    if mothlang in lang_qnumbers:
                        nat_languages.add(lang_qnumbers[mothlang])       # Add a natural language

                        pywikibot.warning('Add {}:{}'.format(NATIVELANGPROP, mothlang))
                        claim = pywikibot.Claim(repo, NATIVELANGPROP)
                        claim.setTarget(pywikibot.ItemPage(repo, lang_qnumbers[mothlang]))
                        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                        status = 'Update'
                    else:
                        pywikibot.error('Unknown language {}'.format(mothlang))

# (14) Conflicting statements
            if SUBCLASSPROP not in item.claims:
                for propty in conflicting_statement:
                    if propty in item.claims and conflicting_statement[propty] in item.claims:
                        pywikibot.error('{} {} conflicts with {} statement'
                                        .format(item.getID(), propty, conflicting_statement[propty]))

# (15) Add symmetric and reciproque statements
                for propty in mandatory_relation:
                    if propty in item.claims:
                        for seq in item.claims[propty]:
                            sitem = seq.getTarget()

                            if mandatory_relation[propty] not in sitem.claims:
                                claim = pywikibot.Claim(repo, mandatory_relation[propty])
                                claim.setTarget(item)
                                sitem.addClaim(claim, bot=BOTFLAG,
                                               summary=transcmt + ' Add required ' + mandatory_relation[propty])
                                status = 'Update'

# (16) Add missing SDC depicts statement
            add_missing_depicts(item)

# (17) Items has possibly be updated - Refresh item data
            label = get_item_header(item.labels)            # Get label (refresh label)
            descr = get_item_header(item.descriptions)      # Get description
            alias = get_item_header(item.aliases)           # Get alias

# (18) Update Wikipedia pages
            # Queued update for Commonscat (have less than 4 non-bot Wikipedia transactions per minute)
            while commonscatqueue and (datetime.now() - lastwpedit).total_seconds() > 15.0:
                addcommonscat = commonscatqueue.pop()
                # Reconstruct an earlier item data
                item = addcommonscat[0]
                sitelang = addcommonscat[1]
                sitelink = item.sitelinks[sitelang]

                lang = sitelink.site.lang
                if lang == 'bh':    # Canonic language names
                    lang = 'bho'
                elif lang == 'no':
                    lang = 'nb'

                page = pywikibot.Page(sitelink.site, sitelink.title, sitelink.namespace)
                while page.isRedirectPage():
                    ## Should fix the sitelinks
                    page = page.getRedirectTarget()

                if page.text:
                    # https://doc.wikimedia.org/pywikibot/stable/api_ref/pywikibot.site.html#pywikibot.site._apisite.APISite.namespace
                    pageupdated = '#pwb Add'
                    item_instance = addcommonscat[2]

                    # Build template list regular expression
                    infobox_template = '{{Infobox|{{Wikidata|{{Persondata|{{Multiple image|{{Databox'
                    for ibox in range(len(infoboxlist)):
                        if sitelang in infoboxlist[ibox]:
                            infobox_template += '|{{' + infoboxlist[ibox][sitelang]

                    # Add person Wikidata infobox
                    if (item_instance == HUMANINSTANCE
                            and sitelang in infoboxlist[0]
                            and not re.search(infobox_template,
                                              page.text, flags=re.IGNORECASE)):
                        personinfobox = infoboxlist[0][sitelang]
                        page.text = '{{' + personinfobox + '}}\n' + page.text
                        pageupdated += ' ' + personinfobox
                        pywikibot.warning('Add {} to {}'.format(personinfobox, sitelang))

                    # Add missing image on Wikipedia page
                    if IMAGEPROP in item.claims and lang in item.labels:
                        # Get the first image from Wikidata
                        image_page = item.claims[IMAGEPROP][0].getTarget()
                        image_name = image_page.title()
                        file_name = image_name.split(':', 1)
                        image_name = sitelink.site.namespace(FILENAMESPACE) + ':' + file_name[1]

                        image_alias = '|\[\[File:|\[\[Image:|</gallery>'
                        if lang in image_namespace:
                            image_alias += '|\[\[' + image_namespace[lang] + ':'

                        if (not re.search(r'\[\[' + sitelink.site.namespace(FILENAMESPACE) + ':'
                                            + image_alias
                                            + '|' + infobox_template
                                            + '|' + file_name[1],
                                          page.text, flags=re.IGNORECASE)):

                            # Add 'upright' if height > 1.5 * width
                            image_flag = 'thumb'
                            try:
                                file_info = image_page.latest_file_info.__dict__
                                file_height = file_info['height']
                                file_width = file_info['width']
                                if file_height >= file_width * 1.5:
                                    image_flag += '|upright'
                            except:
                                pass

                            # Required: item language label
                            image_thumb = '[[{}|{}|{}]]'.format(image_name, image_flag, item.labels[lang])
                            # Header offset
                            headsearch = PAGEHEADRE.search(page.text)
                            if headsearch:
                                headoffset = headsearch.end()
                                page.text = page.text[:headoffset] + '\n' + image_thumb + page.text[headoffset:]
                            else:
                                page.text = image_thumb + '\n' + page.text
                            pageupdated += ' image #WPWP'
                            pywikibot.warning('Add {} to {}, {}'
                                              .format(image_name, sitelang, item.labels[lang]))

                    inserttext = ''
                    refreplace = re.search(r'<references />|<references/>',
                                           page.text, flags=re.IGNORECASE)
                    if refreplace and sitelang in referencelist[0]:
                        reftemplate = referencelist[0][sitelang]
                        inserttext = '{{' + reftemplate + '}}'
                        pageupdated += ' ' + reftemplate
                        pywikibot.warning('Add {} to {}'.format(reftemplate, sitelang))

                    # Add an Authority control template for humans
                    if (item_instance == HUMANINSTANCE
                            and sitelang in authoritylist[0]):
                        skip_authority = '{{Authority control'
                        for ibox in range(len(authoritylist)):
                            if sitelang in authoritylist[ibox]:
                                skip_authority += '|{{' + authoritylist[ibox][sitelang]

                        if not re.search(skip_authority,
                                         page.text, flags=re.IGNORECASE):
                            authoritytemplate = authoritylist[0][sitelang]
                            if inserttext:
                                inserttext += '\n'
                            inserttext += '{{' + authoritytemplate + '}}'
                            pageupdated += ' ' + authoritytemplate
                            pywikibot.warning('Add {} to {}'.format(authoritytemplate, sitelang))

                    # Add missing Commonscat
                    skip_commonscat = '{{Commons'
                    for ibox in range(len(commonscatlist)):
                        if sitelang in commonscatlist[ibox]:
                            skip_commonscat += '|{{' + commonscatlist[ibox][sitelang]

                    # Interproject links
                    if sitelang in authoritylist[1]:
                        skip_commonscat += '|{{' + authoritylist[1][sitelang]

                    commonscattemplate = commonscatlist[0][sitelang]
                    wpcommonscat = addcommonscat[3]
                    # We assume that noteable humans have a Commons Category
                    if (wpcommonscat
                            and not re.search(skip_commonscat + '|Category:' + wpcommonscat,
                                              page.text, flags=re.IGNORECASE)):
                        if inserttext:
                            inserttext += '\n'
                        if sitelink.title == wpcommonscat:
                            inserttext += '{{' + commonscattemplate + '}}'
                        else:
                            inserttext += '{{' + commonscattemplate + '|' + wpcommonscat + '}}'
                        pageupdated += ' [[c:Category:{1}|{0} {1}]]'.format(commonscattemplate, wpcommonscat)
                        pywikibot.warning('Add {} {} to {}'
                                          .format(commonscattemplate, wpcommonscat, sitelang))

                    # Append Wikipedia category
                    wpcatpage = addcommonscat[4]
                    wpcattemplate = sitelink.site.namespace(CATEGORYNAMESPACE)
                    if (wpcatpage
                            and not re.search(r'\[\[' + wpcattemplate + ':' + wpcatpage
                                                + '|\[\[Category:' + wpcatpage,
                                              page.text, flags=re.IGNORECASE)):
                        page.text += '\n[[' + wpcattemplate + ':' + wpcatpage + ']]'
                        pageupdated += ' [[:{}:{}]]'.format(wpcattemplate, wpcatpage)
                        pywikibot.warning('Add {}:{} to {}'
                                          .format(wpcattemplate, wpcatpage, sitelang))

                    # Locate the first Category
                    # https://www.wikidata.org/wiki/Property:P373
                    # https://www.wikidata.org/wiki/Q4167836
                    catsearch = re.search(r'\[\[' + sitelink.site.namespace(CATEGORYNAMESPACE) + ':|\[\[Category:|{{DEFAULTSORT:',
                                          page.text, flags=re.IGNORECASE)
                    if catsearch and item_instance == HUMANINSTANCE:
                        # Add DEFAULTSORT for human
                        try:
                            lastname = item.claims[LASTNAMEPROP][0].getTarget().labels[lang]
                            firstname = item.claims[FIRSTNAMEPROP][0].getTarget().labels[lang]
                            sortorder = lastname + ', ' + firstname
                            sortorderstrip = lastname.replace(' ', '') + ', ' + firstname.replace(' ', '')
                            if not re.search(r'{{DEFAULTSORT:|' + sortorder
                                                + '|' + sortorderstrip + '|' + sortorderstrip.replace(' ', ''),
                                             page.text, flags=re.IGNORECASE):
                                catoffset = catsearch.start()
                                page.text = page.text[:catoffset] + '{{DEFAULTSORT:' + sortorder + '}}\n' + page.text[catoffset:]
                                pageupdated += ' DEFAULTSORT'
                                pywikibot.warning('Add {}:{} to {}'
                                                  .format('DEFAULTSORT', sortorder, sitelang))
                        except:
                            pass    # No firstname, and no lastname

                    # Save page when updated
                    if pageupdated != '#pwb Add':
                        #pywikibot.warning('Instance: {}'.format(item_instance))
                        if inserttext:
                            # Build template list regular expression
                            portal_template = '{{Portal|{{Navbox'
                            for ibox in range(len(portallist)):
                                if sitelang in portallist[ibox]:
                                    portal_template += '|{{' + portallist[ibox][sitelang]

                            # Portal template has precedence on first Category
                            navsearch = re.search(portal_template,
                                                  page.text, flags=re.IGNORECASE)
                            if not navsearch:
                                navsearch = catsearch

                            # Insert the text at the best location
                            if refreplace:
                                page.text = page.text[:refreplace.start()] + inserttext + page.text[refreplace.end():]
                            elif navsearch:
                                page.text = page.text[:navsearch.start()] + inserttext + '\n' + page.text[navsearch.start():]
                            else:
                                # Append the text
                                page.text += '\n' + inserttext

                        # Save page updates
                        try:
                            page.save(pageupdated)
                            lastwpedit = datetime.now()
                        except Exception as error:  # other exception to be used
                            pywikibot.error('Error processing {}, {}'.format(qnumber, error))

# (17) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 130)

        except pywikibot.exceptions.NoPageError as error:           # Item not found
            pywikibot.error(error)
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except AttributeError as error:           # NoneType error
            pywikibot.error(error)
            status = 'NoneType'
            errcount += 1
            exitstat = max(exitstat, 12)
            #raise

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
            if exitfatal:           # Stop on first error
                raise

        """
        The transaction was either executed correctly, or an error occurred.
        Possibly already a system error message was issued.
        We will report the results here, as much as we can, one line per item.
        """

# (18) Get the elapsed time in seconds and the timestamp in string format
        prevnow = now	        	# Transaction status reporting
        now = datetime.now()	    # Refresh the timestamp to time the following transaction

        if verbose or status not in ['OK']:		# Print transaction results
            isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Needed to format output
            totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
            pywikibot.info('{:d}\t{}\t{:f}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'
                           .format(transcount, isotime, totsecs, status, qnumber, label,
                                   commonscat, alias, nationality, birthday, deathday, descr))


def show_help_text():
    """Show program help and exit (only show head text)"""
    helptxt = HELPRE.search(codedoc)
    if helptxt:
        pywikibot.info(helptxt[0])	# Show helptext
    sys.exit(1)                     # Must stop


def show_prog_version():
    """Show program version"""
    pywikibot.info('{}, {}, {}, {}'.format(modnm, pgmid, pgmlic, creator))


def get_next_param():
    """Get the next command parameter, and handle any qualifiers
    """

    global forcecopy
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
    pywikibot.debug('Parameter {}'.format(cpar))

    if cpar.startswith('-c'):	# force copy
        forcecopy = True
        print('Force copy')
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
try:
    if verbose:
        pgmnm = sys.argv.pop(0)	        # Get the name of the executable
        pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
    else:
        show_prog_version()	    	    # Print the module name
except:
    shell = False
    pywikibot.log('No shell available')	    # Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

HELPRE = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
LANGRE = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes
NAMEREVRE = re.compile(r',(\s*.*)*$')	    # Reverse lastname, firstname
PSUFFRE = re.compile(r'\s*[(].*[)]$')		# Remove trailing () suffix (keep only the base label)
PAGEHEADRE = re.compile(r'(==.*==)')        # Page headers with templates
QSUFFRE = re.compile(r'Q[0-9]+')            # Q-numbers
ROMANRE = re.compile(r'^[a-z .,"()\'åáàâäæǣçéèêëíìîïńñóòôöœøśßúùûüýÿĳ-]{2,}$', flags=re.IGNORECASE)     # Roman alphabet
SITELINKRE = re.compile(r'^[a-z]{2,3}wiki$')        # Verify for valid Wikipedia language codes
SHORTDESCRE = re.compile(r'{{Short description\|(.*)}}', flags=re.IGNORECASE)
WDINFOBOX = re.compile(r'{{Wikidata infobox|{{Category|{{Cat disambig', flags=re.IGNORECASE)		    # Wikidata infobox

inlang = '-'
while sys.argv and inlang.startswith('-'):
    inlang = get_next_param().lower()

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]
if LANGRE.search(inlang):
    mainlang = inlang
else:
    inlang = mainlang

for lang in veto_languages:                 # Align veto languages
    if lang in lang_qnumbers:
        veto_languages_id.add(lang_qnumbers[lang])

# Add more languages
while sys.argv:
    if inlang not in veto_languages:
        if inlang not in main_languages:
            main_languages.append(inlang)
        all_languages.add(inlang)
    inlang = get_next_param().lower()

if inlang not in veto_languages:
    if inlang not in main_languages:
        main_languages.append(inlang)
    all_languages.add(inlang)

# Add English as fallback language
label_languages = main_languages
for lang in enlang_list:
    if lang not in label_languages:
        label_languages.append(lang)

# Connect to databases
site = pywikibot.Site('commons')
repo = site.data_repository()
csrf_token = site.tokens['csrf']

# Print preferences
pywikibot.log('Main languages:\t{} {}'.format(mainlang, main_languages))
pywikibot.log('Maximum delay:\t{:d} s'.format(maxdelay))
pywikibot.log('Use labels:\t{}'.format(uselabels))
pywikibot.log('Instance descriptions:\t{}'.format(repldesc))
pywikibot.log('Force copy:\t{}'.format(forcecopy))
pywikibot.log('Verbose mode:\t{}'.format(verbose))
pywikibot.log('Readonly mode:\t{}'.format(readonly))
pywikibot.log('Exit on fatal error:\t{}'.format(exitfatal))
pywikibot.log('Error wait factor:\t{:d}'.format(errwaitfactor))

# Build list of infoboxes
infoboxlist = {}
infoboxlist[0] = get_item_sitelink_dict('Q6249834')         # Infobox person
# Disallow empty boxes
del(infoboxlist[0]['enwiki'])

infoboxlist[1] = get_item_sitelink_dict('Q17534637')        # Infobox person Wikidata (overrule)
# Disallow empty boxes
del(infoboxlist[1]['enwiki'])

# Swap and merge Wikidata boxes
for sitelang in infoboxlist[1]:
    if sitelang in infoboxlist[0]:
        swapinfobox = infoboxlist[0][sitelang]
        infoboxlist[0][sitelang] = infoboxlist[1][sitelang]
        infoboxlist[1][sitelang] = swapinfobox
    else:
        infoboxlist[0][sitelang] = infoboxlist[1][sitelang]
infoboxlist[2] = get_item_sitelink_dict('Q5626735')         # Infobox generic
infoboxlist[3] = get_item_sitelink_dict('Q13553651')        # Infobox (overrule)
infoboxlist[4] = get_item_sitelink_dict('Q5624818')         # Infobox scientist
infoboxlist[5] = get_item_sitelink_dict('Q6434929')         # Multiple image
infoboxlist[6] = get_item_sitelink_dict('Q20702632')        # Databox
infoboxlist[7] = get_item_sitelink_dict('Q5616161')         # Infobox musical artist
infoboxlist[8] = get_item_sitelink_dict('Q5747491')         # Taxobox
infoboxlist[9] = {                                          # Manual exclusions
'fywiki':'Artyst',          # https://fy.wikipedia.org/w/index.php?title=Kees_van_Kooten&diff=1114402&oldid=1114401&diffmode=source
'ruwiki':'Однофамильцы',    # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=prev&oldid=129491499&diffmode=source
'xmfwiki':'ინფოდაფა მენცარი',  # https://xmf.wikipedia.org/w/index.php?title=კეტრინ_ჯონსონი&diff=194620&oldid=194619&diffmode=source
'yiwiki':'אנפירער',         # https://yi.wikipedia.org/w/index.php?title=אדאלף_היטלער&diff=588334&oldid=588333&diffmode=source
}

# Wikimedia Image aliases in local language
image_namespace = get_item_label_dict('Q478798')
image_namespace['azb'] = 'تصویر'    # Manual overrule

referencelist = {}
referencelist[0] = get_item_sitelink_dict('Q5462890')       # References <references />
del(commonscatlist[0]['svwiki'])

referencelist[1] = get_item_sitelink_dict('Q10991260')      # Appendix
for sitelang in referencelist[1]:
    if sitelang in referencelist[0]:
        swapinfobox = referencelist[0][sitelang]
        referencelist[0][sitelang] = referencelist[1][sitelang]
        referencelist[1][sitelang] = swapinfobox
    else:
        referencelist[0][sitelang] = referencelist[1][sitelang]

# List of authority control
authoritylist = {}
authoritylist[0] = get_item_sitelink_dict('Q3907614')       # Authority control
authoritylist[1] = get_item_sitelink_dict('Q5830969')       # Interproject template
authoritylist[2] = get_item_sitelink_dict('Q6171224')       # Lifetime template
authoritylist[2]['frwiki'] = authoritylist[0]['frwiki']     # Manual overrules
authoritylist[0]['frwiki'] = 'Liens'
authoritylist[3] = {                                        # Manual exclusions
'frwiki':'Bases',           # Liens = Autorité + Bases
'ruwiki':'BC',              # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=129492269&oldid=129491434&diffmode=source
}

# Get the Commonscat template names
commonscatlist = {}
commonscatlist[0] = get_item_sitelink_dict('Q48029')        # Commonscat
# Remove banned Wikipedia languages
for sitelang in veto_sitelinks:
    del(commonscatlist[0][sitelang])                        # Veto sites
commonscatlist[1] = {                                       # Manual exclusions
'arzwiki':'لينكات مشاريع شقيقه',   # https://arz.wikipedia.org/w/index.php?title=روجر_رافيل&diff=8088053&oldid=8088052&diffmode=source
'itwiki':'Interprogetto',   # https://it.wikipedia.org/w/index.php?title=Palazzo_dei_Principi-Vescovi_di_Liegi&diff=132888315&oldid=132888272&diffmode=source
'nowiki':'Offisielle lenker',  # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot
'plwiki':'Biogram infobox', # https://pl.wikipedia.org/w/index.php?title=Tinne_Van_der_Straeten&diff=70065360&oldid=70065349&diffmode=source
'ruwiki':'BC',              # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=129492269&oldid=129491434&diffmode=source
}

commonscatlist[2] = {                                       # Manual exclusions
'nowiki':'Offisielt nettsted',  # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot (redirect)
}

# Get the portal template list
portallist = {}
portallist[0] = get_item_sitelink_dict('Q5153')             # Portal
portallist[1] = get_item_sitelink_dict('Q5030944')          # Navbox
portallist[2] = {
'nlwiki':'Portaal',
}

commonscatqueue = []
lastwpedit = datetime.now() + timedelta(seconds=-15)

# Get unique list of item numbers
inputfile = sys.stdin.read()
item_list = sorted(set(QSUFFRE.findall(inputfile)))
pywikibot.debug(item_list)
# Execute all items for one language
wd_proc_all_items()

while repeatmode:
    print('\nEnd of list')
    inputfile = sys.stdin.read()
    item_list = sorted(set(QSUFFRE.findall(inputfile)))
    pywikibot.debug(item_list)
    wd_proc_all_items()

# Print list of natural languages
for qnumber in nat_languages:
    try:
        item = pywikibot.ItemPage(repo, qnumber)
        pywikibot.log('{} ({})'.format(item.labels[mainlang], qnumber))
    except:
        pywikibot.log('({})'.format(qnumber))
"""
    Print all sitelinks (base addresses)
    PAWS is using tokens (passwords can't be used because Python scripts are public)
    Shell is using passwords (from user-password.py file)
"""
for site in sorted(pywikibot._sites.values()):
    if site.username():
        pywikibot.debug('{} {} {} {}'
                        .format(site, site.username(),
                                site.is_oauth_token_available(), site.logged_in()))

sys.exit(exitstat)
