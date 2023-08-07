#!/usr/bin/python3

codedoc = """
copy_label.py - Amend Wikikdata, Wikimedia Commons, and Wikipedia; autocorrect, and register missing statements.

This is a complex script, updating at the same time Wikidata, Wikimedia Commons, and Wikipedia.

It takes advantage of the integration and the interrelations amongst those platforms.

Wikidata:

It performs quality checks and amends missing data and claims.

* Correct Norwegian language mismatches (no-nb language mapping mismatch between Wikipedia and Wikidata).
* Wikipedia site links are merged as aliases.
* Copy human labels to other languages
* Add missing Wikidata statements
* Symmetric "Equal to" statements are added.
    * "Not-equal to" statements are generated when there are homonyms detected.
    * Reflexive "Not-equal to" statements are removed.
    * Symmetric "Not-equal to" statements are added.
* Person's native language and languages used are completed.
* Redundant aliases are removed.
* Any alias for which there is no label are moved to label.
* Unregistered Wikipedia site links for which there exist language labels are added to Wikidata.
* Unrecognized Unicodes are not processed.
* Non-western encoded languages are skipped (but Wikipedia sitelinks are processed).
* Automatic case matching (language specific first captital handling like e.g. in German).

Wikimedia Commons:

It takes advantage of P18 to generate SDC P180 depict statements.
It generates Commonscat statements both in Wikidata, Wikimedia Commons, and Wikipedia.

* Register missing Wikimedia Commons Categories
* A {{Wikidata Infobox}} is added to Commons Category pages
* Add missing Wikimedia Commons SDC P180 depict statements for Wikidata media file statements

Wikipedia:

Based on metadata in Wikidata, it automatically updates Wikipedia.

* Add infoboxes
* Add a first image (based on P18 and related statements in Wikidata).
* Add Appendix (references)
* Add Wikipedia Authority control templates for humans
* Add DEFAULTSORT for humans (lastname, firstname)
* Amend Wikipedia pages for all languages with Commonscat templates

Parameters:

    P1: source language code (default: LANGUAGE, LC_ALL, LANG environment variables)
    P2...: additional language codes for site-link check and label replication
        Take care to only include Western (Roman) languages.

    stdin: list of Q-numbers to process (extracted via regular expression)
        Duplicate and incompatible instances are ignored.

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

    Western languags are "whitelisted".
    Non-Western languages and countries are "blacklisted" to avoid erronuous updates
    (due to e.g. East European language conventions).

    The following Q-numbers are (partially) ignored when copying labels: (sitelinks are processed)

        Duplicate Q-numbers
        Subclasses are ignored
        Some instances are excluded
        Items having non-roman language labels, descriptions or aliases

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

    This script should normally not stack dump, unless a severe (network or server) error occurs.
    Any error will be returned into the return status, and the error description.
    It has intelligent error handling with self-healing code when possible.
    Wikidata run-time errors and timeouts are properly handled and reported.
    Processing typically continues after a 60s retry/timeout.
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

    Install Pywikibot client software
    See https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Principles:

    Use data instead of code.
    Use Wikidata data instead of hard-coding.
    Only use hard-coding if there is no other solution.
    Use a clear and simple data model.
    Use standard properties and statements.
    Be universal, with respect of local conventions.
    Be independant of language.
    Augment data quality.
    Use standard coding.

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

Error handling:

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

    Example queries:

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

    # Uses 50% less elapsed time
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

Known problems:

    WARNING: API error badtoken: Invalid CSRF token.

        Restart the script.

    Remote end closed connection without response

        Restart the script.

    Wikidata requires a bot flag.

    Some Wikipedia platforms require a bot flag. Others are more flexible.

    You might require repeat mode (-r) to update Wikipedia.

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
pgmid = '2023-08-07 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

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
exitstat = 0            # (default) Exit status
errwaitfactor = 4	    # Extra delay after error; best to keep the default value (maximum delay of 4 x 150 = 600 s = 10 min)
maxdelay = 150		    # Maximum error delay in seconds (overruling any extreme long processing delays)

# Wikidata transaction comment
BOTFLAG = True          # Should be False for non-bot accounts

# Language settings
ENLANG = 'en'
enlang_list = [ENLANG]

transcmt = '#pwb Copy label'

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

# Namespaces
# https://www.mediawiki.org/wiki/Help:Namespaces
# https://nl.wikipedia.org.org/w/api.php?action=query&meta=siteinfo&siprop=namespaces&formatversion=2
MAINNAMESPACE = 0
FILENAMESPACE = 6
TEMPLATENAMESPACE = 10
CATEGORYNAMESPACE = 14

# Properties
VIDEOPROP = 'P10'
MAPPROP = 'P15'
CTRYPROP = 'P17'
IMAGEPROP = 'P18'
FATHERPROP = 'P22'
MOTHERPROP = 'P25'
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
QUALIFYFROMPROP = 'P642'
OPERDTPROP = 'P729'
SERVRETDTPROP = 'P730'
LASTNAMEPROP = 'P734'
FIRSTNAMEPROP = 'P735'
MAINCATPROP = 'P910'
VOYAGEBANPROP = 'P948'
COMMGALPROP = 'P935'
VOICERECPROP = 'P990'
PDFPROP = 'P996'
JURISDICTPROP = 'P1001'
CAMERALOCATIONPROP = 'P1259'
BUSINESSPARTNERPROP = 'P1327'
LANGKNOWPROP = 'P1412'
GRAVEPROP = 'P1442'
COMMCREATPROP = 'P1472'
NATIVENAMEPROP = 'P1559'
COMMINSTPROP = 'P1612'
PLACENAMEPROP = 'P1766'
PLAQUEPROP = 'P1801'
NOTEQTOPROP = 'P1889'
COLLAGEPROP = 'P2716'
ICONPROP = 'P2910'
WORKINGLANGPROP = 'P2936'
PARTITUREPROP = 'P3030'
DESIGNPLANPROP = 'P3311'
SIBLINGPROP = 'P3373'
NIGHTVIEWPROP = 'P3451'
PANORAMAPROP = 'P4640'
WINTERVIEWPROP = 'P5252'
DIAGRAMPROP = 'P5555'
INTERIORPROP = 'P5775'
VERSOPROP = 'P7417'
RECTOPROP = 'P7418'
FRAMEWORKPROP = 'P7420'
VIEWPROP = 'P8517'
AERIALVIEWPROP = 'P8592'
PARENTPROP = 'P8810'
FAVICONPROP = 'P8972'
OBJECTLOCATIONPROP = 'P9149'
COLORWORKPROP = 'P10093'

# List of media properties
media_props = {
    AERIALVIEWPROP,
    COATOFARMSPROP,
    COLLAGEPROP,
    COLORWORKPROP,
    DESIGNPLANPROP,
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
    PANORAMAPROP,
    PARTITUREPROP,
    PDFPROP,
    PLACENAMEPROP,
    PLAQUEPROP,
    RECTOPROP,
    SIGNATUREPROP,
    VERSOPROP,
    VIDEOPROP,
    VIEWPROP,
    VOICERECPROP,
    VOYAGEBANPROP,
    WINTERVIEWPROP,
}

# To generate SDC depicts 'of' qualifier
# for indirect media file references.
depict_item_type = {
    COATOFARMSPROP: 'Q14659',
    COLLAGEPROP: 'Q170593',
    DESIGNPLANPROP: 'Q611203',
    FAVICONPROP: 'Q2130',
    FLAGPROP: 'Q14660',
    GRAVEPROP: 'Q173387',
    ICONPROP: 'Q138754',
    LOCATORMAPPROP: 'Q6664848',
    LOGOPROP: 'Q1886349',
    MAPPROP: 'Q2298569',
    PANORAMAPROP: 'Q658252',
    PLACENAMEPROP: 'Q55498668',
    PLAQUEPROP: 'Q721747',
    SIGNATUREPROP: 'Q188675',
    VIDEOPROP: 'Q98069877',
    VOICERECPROP: 'Q53702817',
    VOYAGEBANPROP: 'Q22920576',
}

# List of conflicting properties
conflicting_statement = {
    EQTOPROP: NOTEQTOPROP,
}

# Mandatory relationships
mandatory_relation = {  # Get list via P1696 (could we possibly generate this dictionary dynamically?)
    # Symmetric
    BUSINESSPARTNERPROP: BUSINESSPARTNERPROP,
    BORDERPEERPROP: BORDERPEERPROP,
    EQTOPROP: EQTOPROP,
    MARIAGEPARTNERPROP: MARIAGEPARTNERPROP,
    NOTEQTOPROP: NOTEQTOPROP,
    PARTNERPROP: PARTNERPROP,
    SIBLINGPROP: SIBLINGPROP,

    # Reciproque
    CHILDPROP: FATHERPROP, FATHERPROP: CHILDPROP,
    CHILDPROP: MOTHERPROP, MOTHERPROP: CHILDPROP,
    CHILDPROP: PARENTPROP, PARENTPROP: CHILDPROP,

    CONTAINSPROP: PARTOFPROP, PARTOFPROP: CONTAINSPROP,
    MAINCATPROP: MAINSUBJECTPROP, MAINSUBJECTPROP: MAINCATPROP,
}

# Instances
HUMANINSTANCE = 'Q5'
ESPERANTOLANGINSTANCE = 'Q143'
WIKIMEDIACATINSTANCE = 'Q4167836'

copydesc_item_list = {
    WIKIMEDIACATINSTANCE,       # https://www.wikidata.org/wiki/Q121065933
}

# human, last name, male first name, female first name, neutral first name, affixed family name, family, personage
human_type_list = {HUMANINSTANCE, 'Q101352', 'Q12308941', 'Q11879590', 'Q3409032', 'Q66480858', 'Q8436', 'Q95074'}

# last name, affixed family name, compound, toponiem
lastname_type_list = {'Q101352', 'Q66480858', 'Q60558422', 'Q17143070'}

# Add labels for all those (Roman) languages
# Do not add Central European languages like cs, hu, pl, sk, etc. because of special language rules
# Not Hungarian, Czech, Polish, Slovak, etc
all_languages = ['af', 'an', 'ast', 'ca', 'cy', 'da', 'de', 'en', 'es', 'fr', 'ga', 'gl', 'io', 'it', 'jut', 'nb', 'nl', 'nn', 'pms', 'pt', 'sc', 'sco', 'sje', 'sl', 'sq', 'sv']

# Filter the extension of nat_languages
lang_type_list = {'Q1288568', 'Q33742', 'Q34770'}        # levende taal, natuurlijke taal, taal

# Initial list of natural languages (others will be added automatically)
nat_languages = {'Q150', 'Q188', 'Q652', 'Q1321', 'Q1860', 'Q7411'}

# Languages using uppercase nouns
## Check if we can inherit this set from namespace or language properties??
upper_pref_lang = {'als', 'atj', 'bar', 'bat-smg', 'bjn', 'co?', 'dag', 'de', 'de-at', 'de-ch', 'diq', 'eu?', 'ext', 'fiu-vro', 'frp', 'ffr?', 'gcr', 'gsw', 'ha', 'hif?', 'ht', 'ik?', 'kaa?', 'kab', 'kbp?', 'ksh', 'lb', 'lfn?', 'lg', 'lld', 'mwl', 'nan', 'nds', 'nds-nl?', 'om?', 'pdc?', 'pfl', 'rmy', 'rup', 'sgs', 'shi', 'sn', 'tum', 'vec', 'vmf', 'vro', 'wo?'}

# Avoid risk for non-roman languages
veto_countries = {'Q148', 'Q159', 'Q15180'}

# Veto languages
# Skip non-standard character encoding; see also ROMANRE (other name rules)
# see https://en.wikipedia.org/wiki/Wikipedia:Naming_conventions_(Cyrillic)
veto_languages = {'aeb', 'aeb-arab', 'aeb-latn', 'ar', 'arc', 'arq', 'ary', 'arz', 'bcc', 'be' ,'be-tarask', 'bg', 'bn', 'bgn', 'bqi', 'cs', 'ckb', 'cv', 'dv', 'el', 'fa', 'fi', 'gan', 'gan-hans', 'gan-hant', 'glk', 'gu', 'he', 'hi', 'hu', 'hy', 'ja', 'ka', 'khw', 'kk', 'kk-arab', 'kk-cn', 'kk-cyrl', 'kk-kz', 'kk-latn', 'kk-tr', 'ko', 'ks', 'ks-arab', 'ks-deva', 'ku', 'ku-arab', 'ku-latn', 'ko', 'ko-kp', 'lki', 'lrc', 'lzh', 'luz', 'mhr', 'mk', 'ml', 'mn', 'mzn', 'ne', 'new', 'or', 'os', 'ota', 'pl', 'pnb', 'ps', 'ro', 'ru', 'rue', 'sd', 'sdh', 'sh', 'sk', 'sr', 'sr-ec', 'ta', 'te', 'tg', 'tg-cyrl', 'tg-latn', 'th', 'ug', 'ug-arab', 'ug-latn', 'uk', 'ur', 'vep', 'vi', 'yi', 'yue', 'zg-tw', 'zh', 'zh-cn', 'zh-hans', 'zh-hant', 'zh-hk', 'zh-mo', 'zh-my', 'zh-sg', 'zh-tw'}

# Lookup table for language qnumbers (static update)
# How could we build this automatically?
lang_qnumbers = {'aeb':'Q56240', 'aeb-arab':'Q64362981', 'aeb-latn':'Q64362982', 'ar':'Q13955', 'arc':'Q28602', 'arq':'Q56499', 'ary':'Q56426', 'arz':'Q29919', 'bcc':'Q12634001', 'be':'Q9091', 'be-tarask':'Q8937989', 'bg':'Q7918', 'bn':'Q9610', 'bgn':'Q12645561', 'bqi':'Q257829', 'cs':'Q9056', 'ckb':'Q36811', 'cv':'Q33348', 'da':'Q9035', 'de':'Q188', 'dv':'Q32656', 'el':'Q9129', 'en':'Q1860', 'es':'Q1321', 'fa':'Q9168', 'fi':'Q1412', 'fr':'Q150', 'gan':'Q33475', 'gan-hans':'Q64427344', 'gan-hant':'Q64427346', 'gl':'Q9307', 'glk':'Q33657', 'gu':'Q5137', 'he':'Q9288', 'hi':'Q1568', 'hu':'Q9067', 'hy':'Q8785', 'it':'Q652', 'ja':'Q5287', 'ka':'Q8108', 'khw':'Q938216', 'kk':'Q9252', 'kk-arab':'Q90681452', 'kk-cn':'Q64427349', 'kk-cyrl':'Q90681280', 'kk-kz':'Q64427350', 'kk-latn':'Q64362993', 'kk-tr':'Q64427352', 'ko':'Q9176', 'ko-kp':'Q18784', 'ks':'Q33552', 'ks-arab':'Q64362994', 'ks-deva':'Q64362995', 'ku':'Q36368', 'ku-arab':'Q3678406', 'ku-latn':'Q64362997', 'lki':'Q18784', 'lrc':'Q19933293', 'lzh':'Q37041', 'luz':'Q12952748', 'mhr':'Q12952748', 'mk':'Q9296', 'ml':'Q36236', 'mn':'Q9246', 'mzn':'Q13356', 'ne':'Q33823', 'new':'Q33979', 'nl':'Q7411', 'no':'Q9043', 'or':'Q33810', 'os':'Q33968', 'ota':'Q36730', 'pl':'Q809', 'pnb':'Q1389492', 'ps':'Q58680', 'pt':'Q5146', 'ro':'Q7913', 'ru':'Q7737', 'rue':'Q26245', 'sd':'Q33997', 'sdh':'Q1496597', 'sh':'Q9301', 'sk':'Q9058', 'sl':'Q9063', 'sr':'Q9299', 'sr-ec':'Q21161942', 'sv':'Q9027', 'ta':'Q5885', 'te':'Q8097', 'tg':'Q9260', 'tg-cyrl':'Q64363004', 'tg-latn':'Q64363005', 'th':'Q9217', 'ug':'Q13263', 'ug-arab':'Q2374532', 'ug-latn':'Q986283', 'uk':'Q8798', 'ur':'Q1617', 'vep':'Q32747', 'vi':'Q9199', 'yi':'Q8641', 'yue':'Q9186', 'zh':'Q7850', 'zh-cn':'Q24841726', 'zh-hant':'Q18130932', 'zh-hans':'Q13414913', 'zh-hk':'Q100148307', 'zh-mo':'Q64427357', 'zh-my':'Q13646143', 'zh-sg':'Q1048980', 'zh-tw':'Q4380827'}

# Automatically augmented from veto_languages using lang_qnumbers mapping
veto_languages_id = {'Q7737', 'Q8798'}

# Accepted language scripts (e.g. Latin)
script_whitelist = {'Q8229'}

# Skip not yet fully described Wikipedia family members
new_wikis = {'altwiki', 'amiwiki', 'anpwiki', 'arywiki', 'avkwiki', 'guwwiki', 'kcgwiki', 'lldwiki', 'madwiki', 'mniwiki', 'pwnwiki', 'shiwiki', 'skrwiki', 'taywiki'}

# Avoid duplicate Commonscat templates (Commonscat included from templates)
veto_commonscat = {'fawiki', 'huwiki', 'nowiki', 'plwiki', 'ukwiki'}

# Infobox without Wikidata functionality (to avoid empty emptyboxes)
veto_infobox = {'enwiki', 'jawiki', 'kowiki', 'plwiki', 'shwiki', 'trwiki', 'warwiki', 'zhwiki'}

# List of languages wanting to use <references/>
veto_references = {'cswiki', 'itwiki', 'nowiki', 'svwiki'}

# List of Wikipedia's that do not support bot updates (for different reasons)
veto_sitelinks = {
    # Requires CAPTCHA => blocking bot scripts (?)
    'eswiki', 'fawiki', 'jawiki', 'ptwiki', 'ruwiki', 'simplewiki', 'ttwiki', 'viwiki', 'wuuwiki', 'zhwiki',

    # Blocked (requires mandatory bot flag)
    'itwiki',       # https://it.wikipedia.org/wiki/Special:Log/block?page=User:GeertivpBot
    'slwiki',       # Requires wikibot flag
    'svwiki',       # Infobox

    # To request a proactive bot flag
    'enwiki',

    # Bot approval pending
    #'fiwiki',
    # https://fi.wikipedia.org/wiki/Käyttäjä:GeertivpBot
    # https://meta.wikimedia.org/wiki/User_talk:Geertivp#c-01miki10-20230714212500-Please_request_a_bot_flag_%40_fiwiki

    # Unblocked (after issue was fixed)
    #'nowiki',      # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot

    # Unidentified problem

    #'be-taraskwiki',   # instantiated using different code "be-x-old" ??

    # Non-issues (temporary or specific problems)

    # 'cswiki',
    # WARNING: Add Commonscat Fremantle Highway (ship, 2013) to cswiki
    # ERROR: Error processing Q121093616, Edit to page [[cs:MV Fremantle Highway]] failed:
    # Editing restricted by {{bots}}, {{nobots}} or site's equivalent of {{in use}} template
    # https://cs.wikipedia.org/wiki/MV_Fremantle_Highway
    # {{Pracuje se|2 dní}}
    # Page is protected against (bot) updates. We can ignore this temporary restriction.
    # https://cs.wikipedia.org/wiki/Speciální:Příspěvky/GeertivpBot
}

# List of recognized infoboxes
sitelink_dict_list = [
# Required to be in sequence
    'Q6249834',         # infoboxlist[0] Infobox person (to generate Infobox template on Wikipedia)
    'Q17534637',        # infoboxlist[1] Infobox person Wikidata (overrule)

# Not required to be in sequence
# ... other infoboxes to be added...

# Human
    'Q5615832',         # Infobox author
    'Q5616161',         # Infobox musical artist
    'Q5624818',         # Infobox scientist
    'Q5914426',         # Infobox artist
    'Q5929832',         # Infobox military person
    'Q6424841',         # Infobox politician
    'Q14358369',        # Infobox actor

# Non-human
    'Q5747491',         # Taxobox
    'Q6055178',         # Infobox park
    'Q6630855',         # Infobox food

    'Q5896997',         # Infobox world heritage
    'Q5906647',         # Infobox building

    'Q6190581',         # Infobox organization
    'Q5901151',         # Infobox sport

    'Q6434929',         # Multiple image
    'Q13553651',        # Infobox (overrule)

# Shouldn't we add these to all non-human Wikipedia pages missing an Infobox?
    'Q5626735',         # Infobox generic

# Redundant language codes rue, sv; .update() overrules => which one to give preference?
# https://favtutor.com/blogs/merge-dictionaries-python
    'Q20702632',        # Databox (nl) => seems to work pretty well... {{#invoke:Databox|databox}}
    'Q42054995',        # Universal infobox
]

# Allows to extract GEO coordinates
location_target = [
    ('Camera location', CAMERALOCATIONPROP),    # Geolocation of camera view point
    ('Object location', OBJECTLOCATIONPROP),    # Geolocation of object
]


def fatal_error(errcode, errtext):
    """
    A fatal error has occurred.
    We will print the error message, and exit with an error code.
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


def get_property_label(propx) -> str:
    """
    Get the label of a property.

    :param propx: property (string or property)
    :return property label (string)
    Except: undefined property
    """

    if isinstance(propx, str):
        propty = pywikibot.PropertyPage(repo, propx)
    else:
        propty = propx

    # Return preferred label
    for lang in main_languages:
        if lang in propty.labels:
            return propty.labels[lang]

    # Return any other label
    for lang in propty.labels:
        return propty.labels[lang]
    return '-'


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


def get_item_label_dict(qnumber) -> {}:
    """
    Get the Wikipedia labels in all languages for a Qnumber.
    :param qnumber: list number
    :return: capitalized label dict (index by ISO language code)

    Example of usage:
        Image namespace name (Q478798).
    """
    labeldict = {}
    item = get_item_page(qnumber)
    # Get target labels
    for lang in item.labels:
        #if 'x_' not in lang:     # Ignore special languages
            labeldict[lang] = item.labels[lang][0].upper() + item.labels[lang][1:]
    return labeldict


def get_wikipedia_sitelink_template_dict(qnumber) -> {}:
    """
    Get the Wikipedia template names in all languages for a Qnumber.
    :param qnumber: sitelink list
    :return: template dict (index by sitelang)
    Example of usage:
        Generate {{Commonscat}} statements for Q48029.
    """
    sitedict = {}
    item = get_item_page(qnumber)
    # Get target sitelinks
    for sitelang in item.sitelinks:
        if 'x_' not in sitelang:     # Ignore special languages
            try:
                sitelink = item.sitelinks[sitelang]
                if (str(sitelink.site.family) == 'wikipedia'
                        and sitelink.namespace == TEMPLATENAMESPACE):
                    sitedict[sitelang] = sitelink.title
            except:
                pass    # Incomplete definition
    return sitedict


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
                         os.getenv('LANG', ENLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang]

    # Cleanup language list
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)

    # Make sure that at least 'en' is available
    if ENLANG not in main_languages:
        main_languages.append(ENLANG)

    return main_languages


def get_prop_val_object_label(item, proplist) -> str:
    """Get property value
    :param item: Wikidata item
    :param proplist: Search list of properties
    :return: concatenated list of value labels (first match)
    """
    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:
            for seq in item.claims[prop]:
                val = seq.getTarget()
                ## Except NoneType ??
                item_prop_val += get_item_header(val.labels) + '/'
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


def get_sdc_item(sdc_data) -> pywikibot.ItemPage:
    """
    Get the item from the SDC statement.
    """
    # Get item
    qnumber = sdc_data['datavalue']['value']['id']
    item = get_item_page(qnumber)
    return item


def is_foreign_lang(lang_list) -> bool:
    """ Check if foreign language"""
    isforeign = False
    for seq in lang_list:
        if not ROMANRE.search(seq):
            isforeign = True
            break
    return isforeign


def is_veto_lang_label(lang_list) -> bool:
    """
    Check if language is blacklisted
    """
    isveto = False
    for seq in lang_list:
        if (seq.getTarget().language in veto_languages_id
                or not ROMANRE.search(seq.getTarget().text)):
            isveto = True
            break
    return isveto


def is_veto_script(script_list) -> str:
    """
    Check if script is in veto list
    :param script_list: script claims
    :return non-matching script or empty string
    """
    for seq in script_list:
        # Nonroman script
        try:
            val = seq.getTarget().getID()
            if val not in script_whitelist:
                return val
        except:
            pass    # Ignore NoneType error
    return ''


def item_is_in_list(statement_list, itemlist) -> str:
    """
    Verify if statement list contains at least one item from the itemlist
    :param statement_list:  Statement list
    :param itemlist:        List of values
    return: Matching or empty string
    """
    for seq in statement_list:
        try:
            val = seq.getTarget().getID()
            if val in itemlist:
                return val
        except:
            pass    # Ignore NoneType error
    return ''


def item_not_in_list(statement_list, itemlist) -> str:
    """
    Verify if any statement target is not in the itemlist
    :param statement_list:  Statement list
    :param itemlist:        List of values
    return: Non-matching item or empty string
    """
    for seq in statement_list:
        try:
            val = seq.getTarget().getID()
            if val not in itemlist:
                return val
        except:
            pass    # Ignore NoneType error
    return ''


def add_missing_SDC_depicts(item):
    """
    Add missing Wikimedia Commons SDC P180 depict statements

    :param item: Wikidata item to process
    """

    """
Structure of the Wikimedia Commons structured data statements:

{"entities":{"M17372639":{"pageid":17372639,"ns":6,"title":"File:Brugs Kerkhof Guido Gezelle.jpg","lastrevid":772271921,"modified":"2023-06-08T13:47:37Z","type":"mediainfo","id":"M17372639","labels":{},"descriptions":{},"statements":{"P571":[{"mainsnak":{"snaktype":"value","property":"P571","hash":"135ee2f61e09ee2bb8b4328db588d6edd29a3615","datavalue":{"value":{"time":"+2011-10-26T00:00:00Z","timezone":0,"before":0,"after":0,"precision":11,"calendarmodel":"http://www.wikidata.org/entity/Q1985727"},"type":"time"}},"type":"statement","id":"M17372639$26191E8E-D341-4AFE-BF73-132613446366","rank":"normal"}],"P6216":[{"mainsnak":{"snaktype":"value","property":"P6216","hash":"5570347fdc76d2a80732f51ea10ee4b144a084e0","datavalue":{"value":{"entity-type":"item","numeric-id":50423863,"id":"Q50423863"},"type":"wikibase-entityid"}},"type":"statement","id":"M17372639$042DC9C2-0F7E-482D-A696-0AB727037795","rank":"normal"}],"P275":[{"mainsnak":{"snaktype":"value","property":"P275","hash":"a35b4558d66c92eacbe2f569697ffb1934e0316e","datavalue":{"value":{"entity-type":"item","numeric-id":14946043,"id":"Q14946043"},"type":"wikibase-entityid"}},"type":"statement","id":"M17372639$C3B253E5-D127-40FA-B558-4C1544D1FA73","rank":"normal"}],"P7482":[{"mainsnak":{"snaktype":"value","property":"P7482","hash":"83568a288a8b8b4714a68e7239d8406833762864","datavalue":{"value":{"entity-type":"item","numeric-id":66458942,"id":"Q66458942"},"type":"wikibase-entityid"}},"type":"statement","id":"M17372639$F9CE62D8-A7EE-48FC-BC8C-502BFD476D2B","rank":"normal"}],"P170":[{"mainsnak":{"snaktype":"somevalue","property":"P170","hash":"d3550e860f988c6675fff913440993f58f5c40c5"},"type":"statement","qualifiers":{"P3831":[{"snaktype":"value","property":"P3831","hash":"c5e04952fd00011abf931be1b701f93d9e6fa5d7","datavalue":{"value":{"entity-type":"item","numeric-id":33231,"id":"Q33231"},"type":"wikibase-entityid"}}],"P2093":[{"snaktype":"value","property":"P2093","hash":"e0c0197e220178aa7d77a49cc3226a463b153f83","datavalue":{"value":"Zeisterre","type":"string"}}],"P4174":[{"snaktype":"value","property":"P4174","hash":"2b9891905fac0e237e7575adfde698e2a63e7cd8","datavalue":{"value":"Zeisterre","type":"string"}}],"P2699":[{"snaktype":"value","property":"P2699","hash":"af85c0e2a655a09324c402e4452ec2ef2abc9ea8","datavalue":{"value":"http://commons.wikimedia.org/wiki/User:Zeisterre","type":"string"}}]},"qualifiers-order":["P3831","P2093","P4174","P2699"],"id":"M17372639$234DD68C-428C-41E5-A098-9364961A6BC0","rank":"normal"}],"P180":[{"mainsnak":{"snaktype":"value","property":"P180","hash":"b3c128d5850ce0706e694afc00aa2fb5ccac7daa","datavalue":{"value":{"entity-type":"item","numeric-id":173387,"id":"Q173387"},"type":"wikibase-entityid"}},"type":"statement","qualifiers":{"P642":[{"snaktype":"value","property":"P642","hash":"13ca233362287df2f52077d460ebef58a666c855","datavalue":{"value":{"entity-type":"item","numeric-id":336977,"id":"Q336977"},"type":"wikibase-entityid"}}]},"qualifiers-order":["P642"],"id":"M17372639$b8185896-4eab-2715-5606-388898d07071","rank":"normal"}]}}}}
    """

    # Prepare the static part of the SDC P180 depict statement
    # The numeric value needs to be added at runtime
    depict_statement = {
        'claims': [{
            'type': 'statement',
            'mainsnak': {
                'snaktype': 'value',
                'property': DEPICTSPROP,
                'datavalue': {
                    'type': 'wikibase-entityid',
                    'value': {
                        'entity-type': 'item',
                        # id, numeric-id (dynamic part)
                    }
                }
            }
        }]
    }

    # Find all media files for the item
    for prop in media_props:
        qnumber = item.getID()
        # Representation of
        if prop in depict_item_type:
            qnumber = depict_item_type[prop]

        if prop in item.claims:
            for seq in item.claims[prop]:
                # Reinitialise the depict statement (reset previous loop updates)
                depict_missing = True
                depict_statement['claims'][0]['rank'] = 'preferred'     # Because it comes from a Wikidata P18 or comparable statement
                if 'qualifiers' in depict_statement['claims'][0]:       # Compound depict statement
                    del(depict_statement['claims'][0]['qualifiers'])
                    del(depict_statement['claims'][0]['qualifiers-order'])

                # Get SDC media file info
                media_page = seq.getTarget()
                media_name = media_page.title()
                media_identifier = 'M' + str(media_page.pageid)
                sdc_request = site.simple_request(action='wbgetentities', ids=media_identifier)
                commons_item = sdc_request.submit()
                sdc_data = commons_item.get('entities').get(media_identifier)
                sdc_statements = sdc_data.get('statements')

                if sdc_statements:
                    # Get location from metadata
                    for seq in location_target:
                        location_coord = sdc_statements.get(seq[1])
                        if location_coord:
                            pywikibot.info('{}: {},{}/{}'.format(seq[0],
                                    location_coord[0]['mainsnak']['datavalue']['value']['latitude'],
                                    location_coord[0]['mainsnak']['datavalue']['value']['longitude'],
                                    location_coord[0]['mainsnak']['datavalue']['value']['altitude']))

                    # Get any depict statement
                    depict_list = sdc_statements.get(DEPICTSPROP)
                    if depict_list:
                        for depict in depict_list:
                            # Only allow for a single preferred rank -> need to verify all instances
                            ##print(depict)
                            if depict['rank'] == 'preferred':
                                # Default preferred
                                depict_statement['claims'][0]['rank'] = 'normal'
                            if qnumber == get_sdc_item(depict['mainsnak']).getID():
                                depict_missing = False

                """
https://commons.wikimedia.org/wiki/Special:EntityData/M82236232.json
"P180":[{"mainsnak":{"snaktype":"value","property":"P180","hash":"7282af9508eed4a6f6ebc2e92db7368ecdbb61ab","datavalue":{"value":{"entity-type":"item","numeric-id":22668172,"id":"Q22668172"},"type":"wikibase-entityid"}},"type":"statement","id":"M82236232$e1491557-469c-7672-92d6-6e490f7403bf","rank":"normal"}],
                """
                if depict_missing:
                    # Add the SDC depict statements for this item
                    depict_statement['claims'][0]['mainsnak']['datavalue']['value']['id'] = qnumber
                    depict_statement['claims'][0]['mainsnak']['datavalue']['value']['numeric-id'] = int(qnumber[1:])
                    transcmt = 'Add SDC depicts {} ({})'.format(get_item_header(item.labels), qnumber)

                    # "Representation of" mode
                    if prop in depict_item_type:
                        # Set secondary status
                        depict_statement['claims'][0]['rank'] = 'normal'
                        """
Need to add qualifier
https://commons.wikimedia.org/wiki/Special:EntityData/M17372639.json
"qualifiers":{"P642":[{"snaktype":"value","property":"P642","hash":"13ca233362287df2f52077d460ebef58a666c855","datavalue":{"value":{"entity-type":"item","numeric-id":336977,"id":"Q336977"},"type":"wikibase-entityid"}}]},"qualifiers-order":["P642"],"id":"M17372639$b8185896-4eab-2715-5606-388898d07071","rank":"normal"}]}
                        """
                        # Build the depict qualifier
                        depict_statement['claims'][0]['qualifiers-order'] = [QUALIFYFROMPROP]
                        depict_statement['claims'][0]['qualifiers'] = {}
                        depict_statement['claims'][0]['qualifiers'][QUALIFYFROMPROP] = [{
                            'snaktype': 'value',
                            'property': QUALIFYFROMPROP,
                            'datavalue': {
                                'type': 'wikibase-entityid',
                                'value': {
                                    'entity-type': 'item',
                                    'id': item.getID(),
                                    'numeric-id': int(item.getID()[1:])
                                }
                            }
                        }]

                        transcmt += ' of {} ({})'.format(get_item_header(item.labels), item.getID())

                    # Now store the depict statement
                    pywikibot.debug(depict_statement)
                    sdc_payload = {
                        'action': 'wbeditentity',
                        'format': 'json',
                        'id': media_identifier,
                        'data': json.dumps(depict_statement, separators=(',', ':')),
                        'token': csrf_token,
                        'summary': '#pwb ' + transcmt + ' statement',
                        'bot': BOTFLAG,
                    }

                    sdc_request = site.simple_request(**sdc_payload)
                    try:
                        sdc_request.submit()
                        pywikibot.warning('{} to {} {}'
                                          .format(transcmt, media_identifier, media_name))
                    except Exception as error:
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
    pywikibot.warning('Processing {:d} statements'.format(len(item_list)))

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
            item = get_item_page(qnumber)
            qnumber = item.getID()

            # Instance type could be missing
            try:
                primary_inst_item = get_item_page(item.claims[INSTANCEPROP][0].getTarget())
                item_instance = primary_inst_item.getID()
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
                elif item_is_in_list(item.claims[NATIONALITYPROP], veto_countries):         # nationality blacklist (languages)
                    status = 'Country'
                elif not ROMANRE.search(label) or mainlang in item.aliases and is_foreign_lang(item.aliases[mainlang]):
                    status = 'Language'
                elif NATIVENAMEPROP in item.claims and is_veto_lang_label(item.claims[NATIVENAMEPROP]):             # name in native language
                    status = 'Language'
                elif NATIVELANGPROP in item.claims and item_is_in_list(item.claims[NATIVELANGPROP], veto_languages_id):     # native language
                    status = 'Language'
                elif LANGKNOWPROP in item.claims and item_is_in_list(item.claims[LANGKNOWPROP], veto_languages_id): # language knowledge
                    status = 'Language'
                elif FOREIGNSCRIPTPROP in item.claims and is_veto_script(item.claims[FOREIGNSCRIPTPROP]):           # foreign script system
                    status = 'Script'
                elif NOBLENAMEPROP in item.claims:  # Noble names are exceptions
                    status = 'Noble'
                elif item_instance in human_type_list:
                    label = get_canon_name(label)
            else:
                status = 'No label'         # Missing label

            if not (item_instance in human_type_list or forcecopy):   # Force label copy
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
                    if item_instance in human_type_list:
                        baselabel = get_canon_name(baselabel)

                    # Wikipedia lemmas are in leading uppercase
                    # Wikidata lemmas are in lowercase, unless:
                    if (item_instance in human_type_list
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

                    pywikibot.debug('Page {}:{}:{}'.format(lang,
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
                        pywikibot.info(pagedesc)##
                        itemdesc = pagedesc[1]
                        itemdesc = itemdesc[0].lower() + itemdesc[1:]   ## Always lowercase?
                        item.descriptions[ENLANG] = itemdesc

            # Replicate labels from the instance label
            if (item_instance
                    and (repldesc or len(item.claims[INSTANCEPROP]) == 1
                        and item_instance in copydesc_item_list)):
                for lang in primary_inst_item.labels:
                    if overrule or lang not in item.descriptions:
                        item.descriptions[lang] = primary_inst_item.labels[lang].replace(':', ' ')

            if status in {'OK', 'Nationality'} and label and uselabels:      ## and ' ' in label.find ??
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
                    # This section would need to contain a complicated recursive error handling algorithm.
                    # SetSitelinks nor editEntity can't be used because it stops at the first error, and we need more control.
                    ## Two or more sitelinks can have conflicting Qnumbers. Add mutual "Not Equal" claims via the exception section...
                    # Sitelink pages might not be available (quick escape via except pass; an error message is printed).
                    if lang in item.labels:
                        sitedict = {'site': sitelang, 'title': item.labels[lang]}
                        try:
                            # Try to add a sitelink now
                            item.setSitelink(sitedict, bot=BOTFLAG, summary='#pwb Add sitelink')
                            status = 'Sitelink'
                        except pywikibot.exceptions.OtherPageSaveError as error:
                            # Get unique Q-numbers, skip duplicates (order not guaranteed)
                            itmlist = set(QSUFFRE.findall(str(error)))
                            if len(itmlist) > 1:
                                itmlist.remove(qnumber)
                                pywikibot.error('Conflicting sitelink statement {} {}:{}, {}'
                                                .format(qnumber, lang, item.labels[lang], itmlist))
                                status = 'DupLink'	    # Conflicting sitelink statement
                                errcount += 1
                                exitstat = max(exitstat, 10)

                    if sitelang not in item.sitelinks and lang in item.aliases:
                        # If the sitelink is still missing, try to add a sitelink from the aliases
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

            maincat_item = ''
            # Add inverse statement
            if MAINCATPROP in item.claims:
                maincat_item = get_item_page(item.claims[MAINCATPROP][0].getTarget())

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
            elif maincat_item and COMMCATPROP in maincat_item.claims:
                commonscat = maincat_item.claims[COMMCATPROP][0].getTarget()
            elif COMMGALPROP in item.claims:                # Commons gallery page
                commonscat = item.claims[COMMGALPROP][0].getTarget()
            elif COMMCREATPROP in item.claims:              # Commons creator page
                commonscat = item.claims[COMMCREATPROP][0].getTarget()
            elif COMMINSTPROP in item.claims:               # Commons institution page
                commonscat = item.claims[COMMINSTPROP][0].getTarget()
            elif item_instance in lastname_type_list:
                commonscat = label + ' (surname)'
            elif enlang_list[0] in item.labels:             # English label might possibly be used as Commons category
                commonscat = item.labels[enlang_list[0]]
            elif mainlang in item.labels:                   # Otherwise the native label
                commonscat = item.labels[mainlang]

            if commonscat and 'commonswiki' not in item.sitelinks:
                # Try to create a Wikimedia Commons Category page
                sitedict = {'site': 'commonswiki', 'title': 'Category:' + commonscat}
                try:
                    item.setSitelink(sitedict, bot=BOTFLAG, summary='#pwb Add sitelink')
                    status = 'Commons'
                except pywikibot.exceptions.OtherPageSaveError as error:
                    # Revoke the Commonscat
                    commonscat = ''
                    itmlist = set(QSUFFRE.findall(str(error)))
                    if len(itmlist) > 1:
                        # Get unique Q-numbers, skip duplicates (order not guaranteed)
                        itmlist.remove(qnumber)
                        pywikibot.error('Conflicting category statement {}, {}'
                                        .format(qnumber, itmlist))
                        status = 'DupCat'	    # Conflicting category statement
                        errcount += 1
                        exitstat = max(exitstat, 10)

            if commonscat:
                # Amend EN label from the Commons Category
                item_name_canon = unidecode.unidecode(commonscat).casefold()
                baselabel = commonscat
                # Lowercase first character
                if noun_in_lower:
                    baselabel = baselabel[0].lower() + baselabel[1:]

                # Add Commons category
                if COMMCATPROP not in item.claims:
                    claim = pywikibot.Claim(repo, COMMCATPROP)
                    claim.setTarget(commonscat)
                    item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                    status = 'Update'

                page = pywikibot.Category(site, commonscat)
                # Avoid duplicates and Category redirect
                if not page.text:
                    pywikibot.warning('Empty Wikimedia Commons category page: {}'
                                      .format(commonscat))
                else:
                    inserttext = ''
                    pageupdated = '#pwb Add'

                    if not WDINFOBOXRE.search(page.text):
                        # Add Wikidata Infobox to Wikimedia Commons Category
                        inserttext += '{{Wikidata Infobox}}\n'
                        pageupdated += ' Wikidata Infobox'
                        pywikibot.warning('Add {} to {}'.format('Wikidata Infobox', 'Wikimedia Commons'))

                    if inserttext != '':
                        page.text = inserttext + re.sub(r'[ \t\r\f\v]+$', '', page.text, flags=re.MULTILINE)
                        page.save(pageupdated)
                        status = 'Update'

            # Add missing Commonscat statements to Wikipedia via queue
            # Wikipedia should have no more than 1 transaction per minute (when not having bot account)
            for sitelang in item.sitelinks:
                # Get target sitelink
                if (sitelang in commonscatlist[0]
                        and sitelang not in new_wikis
                        and item.sitelinks[sitelang].namespace == MAINNAMESPACE):
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

# Now process any claims

# (12) Replicate Moedertaal -> Taalbeheersing
            if NATIVELANGPROP in item.claims:
                target = get_item_page(item.claims[NATIVELANGPROP][0].getTarget())
                nat_languages.add(target.getID())           # Add a natural language

                if (LANGKNOWPROP not in item.claims
                        or not item_is_in_list(item.claims[LANGKNOWPROP], [target.getID()])):
                    # Add another language
                    claim = pywikibot.Claim(repo, LANGKNOWPROP)
                    claim.setTarget(target)
                    item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                    pywikibot.warning('Add {} ({}) {} ({})'
                                      .format(get_property_label(LANGKNOWPROP), LANGKNOWPROP,
                                              get_item_header(target.labels), target.getID()))
                    status = 'Update'

# (13) Replicate Taalbeheersing -> Moedertaal
            if item_instance in human_type_list:
                primary_lang_prop = NATIVELANGPROP
            else:
                primary_lang_prop = WORKINGLANGPROP

            if (primary_lang_prop not in item.claims
                    and LANGKNOWPROP in item.claims
                    # If person knows only one single language, we might consider it as a mother tongue
                    and len(item.claims[LANGKNOWPROP]) == 1):
                target = get_item_page(item.claims[LANGKNOWPROP][0].getTarget())

                # Add missing natural language
                if (target.getID() not in nat_languages
                        and target.getID() != ESPERANTOLANGINSTANCE     # Filter non-natural languages like Esperanto
                        and INSTANCEPROP in target.claims
                        and not item_not_in_list(target.claims[INSTANCEPROP], lang_type_list)):
                    nat_languages.add(target.getID())

                # Add one single mother tongue (natural languages)
                if target.getID() in nat_languages:
                    claim = pywikibot.Claim(repo, primary_lang_prop)
                    claim.setTarget(target)
                    item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                    pywikibot.warning('Add {} ({}) {} ({})'
                                      .format(get_property_label(primary_lang_prop), primary_lang_prop,
                                              get_item_header(target.labels), target.getID()))
                    status = 'Update'

            # Single native name considered as mother tongue
            if (item_instance in human_type_list
                    and NATIVELANGPROP not in item.claims
                    and NATIVENAMEPROP in item.claims
                    and len(item.claims[NATIVENAMEPROP]) == 1):
                # Get native language from name
                mothlang = get_item_page(item.claims[NATIVENAMEPROP][0].getTarget()).language
                if mothlang in lang_qnumbers:
                    nat_languages.add(lang_qnumbers[mothlang])       # Add a natural language
                    claim = pywikibot.Claim(repo, NATIVELANGPROP)
                    claim.setTarget(get_item_page(lang_qnumbers[mothlang]))
                    item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                    pywikibot.warning('Add {} ({}) {} ({})'
                                      .format(get_property_label(NATIVELANGPROP), NATIVELANGPROP,
                                              mothlang, lang_qnumbers[mothlang]))
                    status = 'Update'
                else:
                    pywikibot.error('Unknown native language {}'.format(mothlang))

# (14) Handle conflicting statements
            if SUBCLASSPROP not in item.claims:

                # Identify forbidden statements
                for propty in conflicting_statement:
                    if propty in item.claims and conflicting_statement[propty] in item.claims:
                        conf_item_list = set()
                        for seq in item.claims[conflicting_statement[propty]]:
                            conf_item_list.add(seq.getTarget().getID())
                        conf_item = item_is_in_list(item.claims[propty], conf_item_list)
                        if conf_item:
                            pywikibot.error('{} {} possible conflict with {}:{} statement'
                                            .format(qnumber, propty, conflicting_statement[propty], conf_item))

# (15) Add symmetric and reciproque statements
                # Identify mandatory statements
                for propty in mandatory_relation:
                    if propty in item.claims:
                        for seq in item.claims[propty]:
                            sitem = seq.getTarget()
                            if (sitem and (mandatory_relation[propty] not in sitem.claims
                                           or not item_is_in_list(sitem.claims[mandatory_relation[propty]], [qnumber]))):
                                propty_label = get_property_label(mandatory_relation[propty])
                                claim = pywikibot.Claim(repo, mandatory_relation[propty])
                                claim.setTarget(item)
                                sitem.addClaim(claim, bot=BOTFLAG, summary=transcmt + ' Add {} ({})'
                                                  .format(propty_label, mandatory_relation[propty]))
                                pywikibot.warning('Add relationship {} ({}) {} ({}) to {} ({})'
                                                  .format(propty_label, mandatory_relation[propty],
                                                          get_item_header(item.labels), qnumber,
                                                          get_item_header(sitem.labels), sitem.getID()))
                                status = 'Update'
            elif INSTANCEPROP in item.claims:
                pywikibot.info('Both instance ({}) or subclass ({}) property for item {}'
                               .format(INSTANCEPROP, SUBCLASSPROP, qnumber))

# (16) Add missing Wikimedia Commons SDC depicts statement
            add_missing_SDC_depicts(item)

# (17) Items has possibly been updated - Refresh item data
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
                    infobox_template = '{{.*Infobox|{{Wikidata|{{Persondata|{{Multiple image|{{Databox'
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

                    # Add one missing image on the Wikipedia page
                    if IMAGEPROP in item.claims and lang in item.labels:
                        # Get the first image from Wikidata
                        image_page = item.claims[IMAGEPROP][0].getTarget()
                        image_name = image_page.title()
                        file_name = image_name.split(':', 1)
                        image_name = sitelink.site.namespace(FILENAMESPACE) + ':' + file_name[1]

                        image_alias = r'|\[\[File:|\[\[Image:|</gallery>'
                        if lang in image_namespace:
                            image_alias += r'|\[\[' + image_namespace[lang] + ':'

                        # Only add a first image
                        if (not re.search(r'\[\[' + sitelink.site.namespace(FILENAMESPACE) + ':'
                                            + image_alias
                                            + '|' + infobox_template
                                            + '|' + file_name[1].replace('(', '\(').replace(')', '\)'),
                                          page.text, flags=re.IGNORECASE)):

                            # Add 'upright' if height > 1.5 * width
                            image_flag = 'thumb'
                            try:
                                file_info = image_page.latest_file_info.__dict__
                                file_height = file_info['height']
                                file_width = file_info['width']
                                if file_height > file_width * 1.44:
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
                            pageupdated += ' image #WPWP #WPWPBE'
                            pywikibot.warning('Add {} to {} {}'
                                              .format(image_name, sitelang, item.labels[lang]))

                    inserttext = ''
                    refreplace = re.search('<references />|<references/>',
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

                    # No Commonscat for Interproject links
                    for ibox in [1, 2]:
                        if sitelang in authoritylist[ibox]:
                            skip_commonscat += '|{{' + authoritylist[ibox][sitelang]

                    commonscattemplate = commonscatlist[0][sitelang]
                    wpcommonscat = addcommonscat[3]
                    # Add a Commons Category
                    if (wpcommonscat
                            # Avoid duplicate Commons cat with human Infoboxes
                            and not (sitelang in veto_commonscat
                                     and item_instance == HUMANINSTANCE)
                            and not re.search(skip_commonscat + '|Category:' + wpcommonscat.replace('(', '\(').replace(')', '\)'),
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
                            and not re.search(r'\[\[' + wpcattemplate + ':' + wpcatpage.replace('(', '\(').replace(')', '\)') +
                                              r'|\[\[Category:' + wpcatpage.replace('(', '\(').replace(')', '\)'),
                                              page.text, flags=re.IGNORECASE)):
                        page.text += '\n[[' + wpcattemplate + ':' + wpcatpage + ']]'
                        pageupdated += ' [[:{}:{}]]'.format(wpcattemplate, wpcatpage)
                        pywikibot.warning('Add {}:{} to {}'
                                          .format(wpcattemplate, wpcatpage, sitelang))

                    # Locate the first Category
                    # https://www.wikidata.org/wiki/Property:P373
                    # https://www.wikidata.org/wiki/Q4167836
                    catsearch = re.search(r'\[\[' + sitelink.site.namespace(CATEGORYNAMESPACE) +
                                          r':|\[\[Category:|' + default_sort_template,
                                          page.text, flags=re.IGNORECASE)
                    if catsearch and item_instance == HUMANINSTANCE:
                        skip_defaultsort = ''
                        if sitelang in authoritylist[3]:
                            skip_defaultsort = '|{{' + authoritylist[3][sitelang]

                        try:
                            lastname = item.claims[LASTNAMEPROP][0].getTarget().labels[lang]
                            firstname = item.claims[FIRSTNAMEPROP][0].getTarget().labels[lang]
                            sortorder = lastname + ', ' + firstname
                            sortorderstrip = lastname.replace(' ', '') + ', ' + firstname.replace(' ', '')
                            if not re.search(default_sort_template + skip_defaultsort +
                                             '|' + sortorder + '|' + sortorderstrip + '|' + sortorderstrip.replace(' ', '') +
                                             '|' + unidecode.unidecode(sortorder) +
                                             '|' + unidecode.unidecode(sortorderstrip) +
                                             '|' + unidecode.unidecode(sortorderstrip).replace(' ', ''),
                                             page.text, flags=re.IGNORECASE):
                                # Add DEFAULTSORT for human
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
                            # Trim trailing spaces
                            page.text = re.sub(r'[ \t\r\f\v]+$', '', page.text, flags=re.MULTILINE)
                            page.save(pageupdated)
                            lastwpedit = datetime.now()
                        except Exception as error:  # other exception to be used
                            pywikibot.error('Error processing {}, {}'.format(qnumber, error))

# (19) Error handling
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

# (20) Get the elapsed time in seconds and the timestamp in string format
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
    pywikibot.info('No shell available')	    # Most probably running on PAWS Jupyter

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
ROMANRE = re.compile(r'^[a-z .,"()\'åáàâäāæǣçéèêëėíìîïıńñŋóòôöœøřśßúùûüýÿĳ-]{2,}$', flags=re.IGNORECASE)     # Roman alphabet
SITELINKRE = re.compile(r'^[a-z]{2,3}wiki$')        # Verify for valid Wikipedia language codes
SHORTDESCRE = re.compile(r'{{Short description\|(.*)}}', flags=re.IGNORECASE)
WDINFOBOXRE = re.compile(r'{{Wikidata infobox|{{Category|{{Cat disambig', flags=re.IGNORECASE)		    # Wikidata infobox
default_sort_template = r'{{DEFAULTSORT:|{{SORTUJ:|{{AAKKOSTUS:|{{DEFAŬLTORDIGO:'
DEFAULTSORTRE = re.compile(default_sort_template, flags=re.IGNORECASE)		    ## not used...

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

if mainlang not in main_languages:
    main_languages.insert(0, mainlang)

# Build veto languages ID
for lang in veto_languages:
    if lang in lang_qnumbers:   # comment to check completeness
        veto_languages_id.add(lang_qnumbers[lang])

# Add additional languages from parameters
while sys.argv:
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

# Connect to databases
site = pywikibot.Site('commons')
site.login()            # Must login
repo = site.data_repository()
csrf_token = site.tokens['csrf']    # Token needed to update SDC

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

# Setup language lookup tables in the sequence of a Wikipedia page

# Load list of infoboxes automatically (first 2 must be in sequence)
dictnr = 0
infoboxlist = {}
for item_dict in sitelink_dict_list:
    infoboxlist[dictnr] = get_wikipedia_sitelink_template_dict(item_dict)
    dictnr += 1

# Swap and merge Wikidata boxes (index 0 and 1)
for sitelang in infoboxlist[1]:
    if sitelang in infoboxlist[0]:
        swapinfobox = infoboxlist[0][sitelang]
        infoboxlist[0][sitelang] = infoboxlist[1][sitelang]
        infoboxlist[1][sitelang] = swapinfobox
    else:
        infoboxlist[0][sitelang] = infoboxlist[1][sitelang]

# Disallow empty boxes (where no Wikidata statements are implemented)
infoboxlist[dictnr] = {}
for sitelang in veto_infobox:
    infoboxlist[dictnr][sitelang] = infoboxlist[0][sitelang]
    del(infoboxlist[0][sitelang])

dictnr += 1
infoboxlist[dictnr] = {             # Manual exclusions
    'azwiki': 'Rəqs',               # No Wikidata
    'bswiki': 'Infokutija',         # Multiple templates
    'euwiki': 'Biografia',          # Multiple templates
    'fiwiki': 'Kirjailija',
    'fywiki': 'Artyst',             # https://fy.wikipedia.org/w/index.php?title=Kees_van_Kooten&diff=1114402&oldid=1114401&diffmode=source
    'ruwiki': 'Однофамильцы',       # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=prev&oldid=129491499&diffmode=source
    'srwiki': 'Infokutija',         # Multiple templates
    'ukwiki': 'Unibox',             # https://uk.wikipedia.org/w/index.php?title=Сюанський_папір&diff=39931612&oldid=37227693
    'xmfwiki': 'ინფოდაფა მენცარი',     # https://xmf.wikipedia.org/w/index.php?title=კეტრინ_ჯონსონი&diff=194620&oldid=194619&diffmode=source
    'yiwiki': 'אנפירער',            # https://yi.wikipedia.org/w/index.php?title=אדאלף_היטלער&diff=588334&oldid=588333&diffmode=source
}

dictnr += 1
infoboxlist[dictnr] = {
    'euwiki': '.+ infotaula',       # Regex wildcard
    'srwiki': 'Glumac-lat',         # Multiple templates
    'ukwiki': 'Кулінарна страва',
}

dictnr += 1
pywikibot.info('{:d} Wikipedia infoboxes loaded'.format(dictnr))

# Wikimedia Image aliases in the local language
image_namespace = get_item_label_dict('Q478798')

# Manual overrule
image_namespace['hr'] = 'Datoteka'
#for lang in image_namespace:
    #print(lang, image_namespace[lang])

referencelist = {}
referencelist[0] = get_wikipedia_sitelink_template_dict('Q5462890')       # Replace <references /> by References
referencelist[1] = get_wikipedia_sitelink_template_dict('Q10991260')      # Appendix

for sitelang in referencelist[1]:
    if sitelang in referencelist[0]:
        swapinfobox = referencelist[0][sitelang]
        referencelist[0][sitelang] = referencelist[1][sitelang]
        referencelist[1][sitelang] = swapinfobox
    else:
        referencelist[0][sitelang] = referencelist[1][sitelang]

for sitelang in veto_references:
    del(referencelist[0][sitelang])                         # Keep <references />

# List of authority control
authoritylist = {}

# Specific index 0
authoritylist[0] = get_wikipedia_sitelink_template_dict('Q3907614')       # Add Authority control

# No Commonscat for Interproject links
# Specific index 1
authoritylist[1] = get_wikipedia_sitelink_template_dict('Q5830969')       # Interproject template
authoritylist[1]['euwiki'] = 'Bizialdia'                    # No commonscat
authoritylist[1]['lvwiki'] = 'Sisterlinks-inline'           # No commonscat (Q26098003)

# No Commonscat for Interproject links
# Specific index 2
authoritylist[2] = {                                        # Manual exclusions
    'eswiki': 'Control de autoridades',
}

# Lifetime template; skip adding DEFAULTSORT
# Specific index 3
authoritylist[3] = get_wikipedia_sitelink_template_dict('Q6171224')

# Other exclustions
authoritylist[4] = {                                        # Manual exclusions
    'bewiki': 'Бібліяінфармацыя',
    'frwiki': 'Bases',           # Liens = Autorité + Bases
    'ruwiki': 'BC',              # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=129492269&oldid=129491434&diffmode=source
}

authoritylist[5] = {}                                       # Exeptional manual exclusions
authoritylist[5]['frwiki'] = authoritylist[0]['frwiki']
authoritylist[0]['frwiki'] = 'Liens'    # Enforce frwiki

# Get the Commonscat template names
commonscatlist = {}
commonscatlist[0] = get_wikipedia_sitelink_template_dict('Q48029')        # Commonscat
# Overrule
commonscatlist[0]['fiwiki'] = 'Commonscat-rivi'

# Veto sites
for sitelang in veto_sitelinks:
    del(commonscatlist[0][sitelang])

# Manual exclusions
commonscatlist[1] = {
'arzwiki': 'لينكات مشاريع شقيقه',   # https://arz.wikipedia.org/w/index.php?title=روجر_رافيل&diff=8088053&oldid=8088052&diffmode=source
'bewiki': 'Пісьменнік',
'hywiki': 'Տեղեկաքարտ Խաչքար',  # Q26042874
'itwiki': 'Interprogetto',      # https://it.wikipedia.org/w/index.php?title=Palazzo_dei_Principi-Vescovi_di_Liegi&diff=132888315&oldid=132888272&diffmode=source
'nowiki': 'Offisielle lenker',  # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot
'ruwiki': 'BC',                 # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=129492269&oldid=129491434&diffmode=source
'ukwiki': 'універсальна картка',
}

# Manual exclusions
commonscatlist[2] = {
'hywiki': 'Տեղեկաքարտ Խաչքար',  # Q26042874
'nowiki': 'Offisielt nettsted', # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot (redirect)
}

# Get the portal template list
portallist = {}
portallist[0] = get_wikipedia_sitelink_template_dict('Q5153')             # Portal
portallist[1] = get_wikipedia_sitelink_template_dict('Q5030944')          # Navbox

# Manual exclusions
portallist[2] = {
'nlwiki':'Portaal',
}

pywikibot.info('Wikipedia templates loaded')

commonscatqueue = []        # FIFO list
lastwpedit = datetime.now() + timedelta(seconds=-15)

# Get unique list of item numbers
inputfile = sys.stdin.read()
item_list = sorted(set(QSUFFRE.findall(inputfile)))
pywikibot.debug(item_list)
# Execute all items
wd_proc_all_items()

while repeatmode:
    pywikibot.info('\nEnd of list')
    inputfile = sys.stdin.read()
    item_list = sorted(set(QSUFFRE.findall(inputfile)))
    pywikibot.debug(item_list)
    wd_proc_all_items()

# Print list of natural languages
for qnumber in nat_languages:
    try:
        item = get_item_page(qnumber)
        qnumber = item.getID()
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
