#!/usr/bin/python3

codedoc = """
copy_label.py - Amend Wikikdata, Wikimedia Commons, and Wikipedia; autocorrect, and register missing statements.

This is a complex script, updating at the same time Wikidata, Wikimedia Commons, and Wikipedia.

It takes advantage of the integration and the interrelations amongst those platforms.

It takes care of local languages; avoiding hard-coding, reading configuration data from Wikidata.

It completely works multi-lingual. It avoids problems with non-roman languages or conventions of central-European languages.

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

It derives SDC P180 depict statements from P18 and related Wikidata statements.
It generates Commonscat statements both in Wikidata, Wikimedia Commons, and Wikipedia.

* Register missing Wikimedia Commons Categories
* A {{Wikidata Infobox}} is added to Commons Category pages

Wikipedia:

Based on metadata in Wikidata, it automatically updates Wikipedia.

* Add infoboxes
* Add a first image (based on P18 in Wikidata).
* Add Appendix (references)
* Add Wikipedia Authority control templates for humans
* Add DEFAULTSORT for humans (lastname, firstname)
* Amend Wikipedia pages for all languages with Commonscat templates
* Add Wikipedia categories

Parameters:

    P1: source language code (default: LANGUAGE, LC_ALL, LANG environment variables)
    P2...: additional language codes for site-link check and label replication
        Take care to only include Western (Roman) languages.

    stdin: list of Q-numbers to process (extracted via regular expression)
        Duplicate and incompatible instances or subclases are ignored.

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
    Non-Western languages and some countries are "blacklisted" to avoid erronuous updates
    (due to e.g. East European languistic conventions).

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
    For non-bot accounts there is a maximum of 1 transaction per minute.

Responsibilities:

    The person running this script is the sole responsible for any erronuous updates the script is performing.
    This script is offered to the user as best-effort.
    The author does not accept any responsibility for any bugs in the script.
    Bugs should be reported to the author, to be able to ameliorate the script.

Prequisites:

    Install Pywikibot client software
    See https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

Principles:

    Use data instead of code.
    Use Wikidata data instead of hard-coding.
    Only use hard-coding if there is no other solution.
    Use a clear and simple data model.
    Keep the logic and code simple.
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
    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.site.html
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
    https://doc.wikimedia.org/pywikibot/master/_modules/cosmetic_changes.html#CosmeticChangesToolkit.translateMagicWords
    https://www.mediawiki.org/wiki/Help:Magic_words

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
import pdb              # Python debugger
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import unidecode        # Unicode
from datetime import datetime	    # now, strftime, delta time, total_seconds
from datetime import timedelta

# Global variables
modnm = 'Pywikibot copy_label'      # Module name (using the Pywikibot package)
pgmid = '2023-12-30 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

"""
    Static definitions
"""
# Functional configuration flags
# Restrictions: cannot disable both labels and wikipedia. We need at least one of the options.
# Defaults: transparent and safe
forcecopy = False	    # Force copy
lead_lower = False      # Leading lowercase
lead_upper = False      # Leading uppercase
overrule = False        # Overrule
repeatmode = False      # Repeat mode
repldesc = False        # Replicate instance description labels
uselabels = True	    # Use the language labels (disable with -l)

# Technical configuration flags
errorstat = True        # Show error statistics (disable with -e)
exitfatal = True	    # Exit on fatal error (can be disabled with -p; please take care)
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

# Wikidata transaction comment
BOTFLAG = True          # Should be False for non-bot accounts
transcmt = '#pwb Copy label'

# Language settings
ENLANG = 'en'
enlang_list = [ENLANG]

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
COUNTRYPROP = 'P17'
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
MANAGEITEMPROP = 'P121'
PROPERTYOFPROP = 'P127'
OPERATORPROP = 'P137'
LOGOPROP = 'P154'
DEPICTSPROP = 'P180'
PROMOTORPROP = 'P184'
PROMOVENDUSPROP = 'P185'
LOCATORMAPPROP = 'P242'
SUBCLASSPROP = 'P279'
FOREIGNSCRIPTPROP = 'P282'
MAINSUBJECTPROP = 'P301'
PARTOFPROP = 'P361'
COMMONSCATPROP = 'P373'
PARTNERPROP = 'P451'
EQTOPROP = 'P460'
COUNTRYORIGPROP = 'P495'
BIRTHDATEPROP = 'P569'
DEATHDATEPROP = 'P570'
CONTAINSPROP = 'P527'
FOUNDINGDATEPROP = 'P571'
DISSOLVDATEPROP = 'P576'
STARTDATEPROP = 'P580'
ENDDATEPROP = 'P582'
TIMEPROP = 'P585'
"""
P585 {
    "after": 0,
    "before": 0,
    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
    "precision": 11,
    "time": "+00000001879-06-19T00:00:00Z",
    "timezone": 0
}
"""
QUALIFYFROMPROP = 'P642'
OPERATINGDATEPROP = 'P729'
SERVICEENDDATEPROP = 'P730'
LASTNAMEPROP = 'P734'
FIRSTNAMEPROP = 'P735'
PSEUDONYMPROP = 'P742'
MAINCATEGORYPROP = 'P910'
VOYAGEBANPROP = 'P948'
COMMONSGALLARYPROP = 'P935'
VOICERECORDPROP = 'P990'
PDFPROP = 'P996'
JURISDICTIONPROP = 'P1001'
CAMERALOCATIONPROP = 'P1259'
EARLYTIMEPROP = 'P1319'
LATETIMEPROP = 'P1326'
BUSINESSPARTNERPROP = 'P1327'
REPLACESPROP = 'P1365'
REPLACEDBYPROP = 'P1366'
LANGKNOWPROP = 'P1412'
GRAVEPROP = 'P1442'
COMMONSCREATORPROP = 'P1472'
NATIVENAMEPROP = 'P1559'
COMMONSINSTPROP = 'P1612'
CATEGORYRELTDTOLISTPROP = 'P1753'
LISTRELTDTOCATEGORYPROP = 'P1754'
PLACENAMEPROP = 'P1766'
ARTISTNAMEPROP = 'P1787'
PLAQUEPROP = 'P1801'
HASPROPERTYPROP = 'P1830'
NOTEQTOPROP = 'P1889'
COLLAGEPROP = 'P2716'
ICONPROP = 'P2910'
WORKINGLANGPROP = 'P2936'
PARTITUREPROP = 'P3030'
DESIGNPLANPROP = 'P3311'
KEYRELATIONPROP = 'P3342'
SIBLINGPROP = 'P3373'
NIGHTVIEWPROP = 'P3451'
OBJECTROLEPROP = 'P3831'
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

alternative_person_names_props = {ARTISTNAMEPROP, PSEUDONYMPROP}

# List of media properties (audio, image, video)
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
    VOICERECORDPROP,
    VOYAGEBANPROP,
    WINTERVIEWPROP,
}

time_props = {
    TIMEPROP,
    STARTDATEPROP, ENDDATEPROP,
    EARLYTIMEPROP, LATETIMEPROP,
 }

# To generate compound SDC depict statements
# for indirect media file references
# using 'of' qualifier
depict_item_type = {
    AERIALVIEWPROP: 'Q1153655',
    COATOFARMSPROP: 'Q14659',
    COLLAGEPROP: 'Q170593',
    DESIGNPLANPROP: 'Q611203',
    DIAGRAMPROP: 'Q959962',
    FAVICONPROP: 'Q2130',
    FLAGPROP: 'Q14660',
    GRAVEPROP: 'Q173387',
    ICONPROP: 'Q138754',
    #IMAGEPROP
    INTERIORPROP: 'Q2998430',
    LOCATORMAPPROP: 'Q6664848',
    LOGOPROP: 'Q1886349',
    MAPPROP: 'Q2298569',
    NIGHTVIEWPROP: 'Q5353651',
    PANORAMAPROP: 'Q658252',
    PARTITUREPROP: 'Q187947',
    PLACENAMEPROP: 'Q55498668',
    PLAQUEPROP: 'Q721747',
    RECTOPROP: 'Q9305022',
    SIGNATUREPROP: 'Q188675',
    VERSOPROP: 'Q9368452',
    VIDEOPROP: 'Q98069877',
    VOICERECORDPROP: 'Q53702817',
    VOYAGEBANPROP: 'Q22920576',
    WINTERVIEWPROP: 'Q54819662',
}

# List of conflicting properties
conflicting_statement = {
    EQTOPROP: NOTEQTOPROP,
    # others to be added
}

# Mandatory relationships
# Get list via P1696 (could we possibly generate this dictionary dynamically?)
# https://www.wikidata.org/wiki/Property:P1696 (inverse property)
# https://www.wikidata.org/wiki/Property:P7087 (inverse label)
mandatory_relation = {
    # Symmetric
    BUSINESSPARTNERPROP: BUSINESSPARTNERPROP,
    BORDERPEERPROP: BORDERPEERPROP,
    EQTOPROP: EQTOPROP,
    MARIAGEPARTNERPROP: MARIAGEPARTNERPROP,
    NOTEQTOPROP: NOTEQTOPROP,
    PARTNERPROP: PARTNERPROP,
    SIBLINGPROP: SIBLINGPROP,

    # Reciproque bidirectional
    CATEGORYRELTDTOLISTPROP: LISTRELTDTOCATEGORYPROP, LISTRELTDTOCATEGORYPROP: CATEGORYRELTDTOLISTPROP,
    CONTAINSPROP: PARTOFPROP, PARTOFPROP: CONTAINSPROP,
    MAINCATEGORYPROP: MAINSUBJECTPROP, MAINSUBJECTPROP: MAINCATEGORYPROP,
    MANAGEITEMPROP: OPERATORPROP, OPERATORPROP: MANAGEITEMPROP,
    REPLACESPROP: REPLACEDBYPROP, REPLACEDBYPROP: REPLACESPROP,
    PROMOTORPROP: PROMOVENDUSPROP, PROMOVENDUSPROP:PROMOTORPROP,
    PROPERTYOFPROP: HASPROPERTYPROP, HASPROPERTYPROP: PROPERTYOFPROP,

    # Reciproque unidirectional (mind the 1:M relationship)
    FATHERPROP: CHILDPROP,  #CHILDPROP: FATHERPROP,
    MOTHERPROP: CHILDPROP,  #CHILDPROP: MOTHERPROP,
    PARENTPROP: CHILDPROP,  #CHILDPROP: PARENTPROP,
    # others to be added
}

# Instances
HUMANINSTANCE = 'Q5'
ESPERANTOLANGINSTANCE = 'Q143'
CORRESPONDENTINSTANCE = 'Q3589290'
WIKIMEDIACATINSTANCE = 'Q4167836'
WIKIMEDIAPROJECTINSTANCE = 'Q14204246'

# Allow to copy the description from one instance to another
copydesc_item_list = {
    WIKIMEDIACATINSTANCE,       # https://www.wikidata.org/wiki/Q121065933
    WIKIMEDIAPROJECTINSTANCE,   # https://www.wikidata.org/wiki/Q14734922
}

# human, last name, male first name, female first name, neutral first name, affixed family name, family, personage
human_type_list = {HUMANINSTANCE, 'Q101352', 'Q12308941', 'Q11879590', 'Q3409032', 'Q66480858', 'Q8436', 'Q95074'}

# last name, affixed family name, compound, toponiem
lastname_type_list = {'Q101352', 'Q66480858', 'Q60558422', 'Q17143070'}

# Add labels for all those (Roman) languages
# Do not add Central European languages like cs, hu, pl, sk, etc. because of special language rules
# Not Hungarian, Czech, Polish, Slovak, etc
all_languages = {'af', 'an', 'ast', 'ca', 'cy', 'da', 'de', 'en', 'es', 'fr', 'ga', 'gl', 'io', 'it', 'jut', 'nb', 'nl', 'nn', 'pms', 'pt', 'sc', 'sco', 'sje', 'sl', 'sq', 'sv'}

# Filter the extension of nat_languages
lang_type_list = {'Q1288568', 'Q33742', 'Q34770'}        # levende taal, natuurlijke taal, taal

# Artificial languages
artificial_languages = {ESPERANTOLANGINSTANCE}

# Initial list of natural languages
# Others will be added automatically during script execution
nat_languages = {'Q150', 'Q188', 'Q652', 'Q1321', 'Q1860', 'Q7411'}

# Languages using uppercase nouns
## Check if we can inherit this set from namespace or language properties??
upper_pref_lang = {'als', 'atj', 'bar', 'bat-smg', 'bjn', 'co?', 'dag', 'de', 'de-at', 'de-ch', 'diq', 'eu?', 'ext', 'fiu-vro', 'frp', 'ffr?', 'gcr', 'gsw', 'ha', 'hif?', 'ht', 'ik?', 'kaa?', 'kab', 'kbp?', 'ksh', 'lb', 'lfn?', 'lg', 'lld', 'mwl', 'nan', 'nds', 'nds-nl?', 'om?', 'pdc?', 'pfl', 'rmy', 'rup', 'sgs', 'shi', 'sn', 'tum', 'vec', 'vmf', 'vro', 'wo?'}

# Avoid risk for non-roman languages or rules
veto_countries = {
    'Q148', 'Q159', 'Q15180',   # China, Russia
}

# Veto languages
# Skip non-standard character encoding; see also ROMANRE (other name rules)
# see https://en.wikipedia.org/wiki/Wikipedia:Naming_conventions_(Cyrillic)
veto_languages = {'aeb', 'aeb-arab', 'aeb-latn', 'ar', 'arc', 'arq', 'ary', 'arz', 'bcc', 'be' ,'be-tarask', 'bg', 'bn', 'bgn', 'bqi', 'cs', 'ckb', 'cv', 'dv', 'el', 'fa', 'fi', 'gan', 'gan-hans', 'gan-hant', 'glk', 'gu', 'he', 'hi', 'hu', 'hy', 'ja', 'ka', 'khw', 'kk', 'kk-arab', 'kk-cn', 'kk-cyrl', 'kk-kz', 'kk-latn', 'kk-tr', 'ko', 'ks', 'ks-arab', 'ks-deva', 'ku', 'ku-arab', 'ku-latn', 'ko', 'ko-kp', 'lki', 'lrc', 'lzh', 'luz', 'mhr', 'mk', 'ml', 'mn', 'mzn', 'ne', 'new', 'no', 'or', 'os', 'ota', 'pl', 'pnb', 'ps', 'ro', 'ru', 'rue', 'sd', 'sdh', 'sh', 'sk', 'sr', 'sr-ec', 'ta', 'te', 'tg', 'tg-cyrl', 'tg-latn', 'th', 'ug', 'ug-arab', 'ug-latn', 'uk', 'ur', 'vep', 'vi', 'yi', 'yue', 'zg-tw', 'zh', 'zh-cn', 'zh-hans', 'zh-hant', 'zh-hk', 'zh-mo', 'zh-my', 'zh-sg', 'zh-tw'}

# Lookup table for language qnumbers (static update)
# How could we build this automatically?
lang_qnumbers = {'aeb':'Q56240', 'aeb-arab':'Q64362981', 'aeb-latn':'Q64362982', 'ar':'Q13955', 'arc':'Q28602', 'arq':'Q56499', 'ary':'Q56426', 'arz':'Q29919', 'bcc':'Q12634001', 'be':'Q9091', 'be-tarask':'Q8937989', 'bg':'Q7918', 'bn':'Q9610', 'bgn':'Q12645561', 'bqi':'Q257829', 'cs':'Q9056', 'ckb':'Q36811', 'cv':'Q33348', 'da':'Q9035', 'de':'Q188', 'dv':'Q32656', 'el':'Q9129', 'en':'Q1860', 'es':'Q1321', 'fa':'Q9168', 'fi':'Q1412', 'fr':'Q150', 'gan':'Q33475', 'gan-hans':'Q64427344', 'gan-hant':'Q64427346', 'gl':'Q9307', 'glk':'Q33657', 'gu':'Q5137', 'he':'Q9288', 'hi':'Q1568', 'hu':'Q9067', 'hy':'Q8785', 'it':'Q652', 'ja':'Q5287', 'ka':'Q8108', 'khw':'Q938216', 'kk':'Q9252', 'kk-arab':'Q90681452', 'kk-cn':'Q64427349', 'kk-cyrl':'Q90681280', 'kk-kz':'Q64427350', 'kk-latn':'Q64362993', 'kk-tr':'Q64427352', 'ko':'Q9176', 'ko-kp':'Q18784', 'ks':'Q33552', 'ks-arab':'Q64362994', 'ks-deva':'Q64362995', 'ku':'Q36368', 'ku-arab':'Q3678406', 'ku-latn':'Q64362997', 'lki':'Q18784', 'lrc':'Q19933293', 'lzh':'Q37041', 'luz':'Q12952748', 'mhr':'Q12952748', 'mk':'Q9296', 'ml':'Q36236', 'mn':'Q9246', 'mzn':'Q13356', 'ne':'Q33823', 'new':'Q33979', 'nl':'Q7411', 'no':'Q9043', 'or':'Q33810', 'os':'Q33968', 'ota':'Q36730', 'pl':'Q809', 'pnb':'Q1389492', 'ps':'Q58680', 'pt':'Q5146', 'ro':'Q7913', 'ru':'Q7737', 'rue':'Q26245', 'sd':'Q33997', 'sdh':'Q1496597', 'sh':'Q9301', 'sk':'Q9058', 'sl':'Q9063', 'sr':'Q9299', 'sr-ec':'Q21161942', 'sv':'Q9027', 'ta':'Q5885', 'te':'Q8097', 'tg':'Q9260', 'tg-cyrl':'Q64363004', 'tg-latn':'Q64363005', 'th':'Q9217', 'ug':'Q13263', 'ug-arab':'Q2374532', 'ug-latn':'Q986283', 'uk':'Q8798', 'ur':'Q1617', 'vep':'Q32747', 'vi':'Q9199', 'yi':'Q8641', 'yue':'Q9186', 'zh':'Q7850', 'zh-cn':'Q24841726', 'zh-hant':'Q18130932', 'zh-hans':'Q13414913', 'zh-hk':'Q100148307', 'zh-mo':'Q64427357', 'zh-my':'Q13646143', 'zh-sg':'Q1048980', 'zh-tw':'Q4380827'}

# Automatically augmented from veto_languages using lang_qnumbers mapping
veto_languages_id = {'Q7737', 'Q8798'}

# Accepted language scripts (e.g. Latin)
script_whitelist = {'Q8229'}

# Infobox without Wikidata functionality (to avoid empty emptyboxes)
veto_infobox = {'afwiki', 'enwiki', 'hrwiki', 'idwiki', 'iswiki', 'jawiki', 'kowiki', 'mrwiki', 'plwiki', 'shwiki', 'trwiki', 'warwiki', 'yowiki', 'zhwiki'}

# List of languages wanting to use the <references /> tag
veto_references = {'bgwiki', 'cswiki', 'fywiki', 'itwiki', 'nowiki', 'svwiki'}

# Avoid duplicate Commonscat templates (Commonscat automatically included from templates)
veto_commonscat = {'azwiki', 'fawiki', 'huwiki', 'hywiki', 'nowiki', 'plwiki', 'ukwiki', 'zeawiki'}

# Veto DEFAULTSORT conversion
veto_defaultsort = {
    'nnwiki',
    #'plwiki',      # ['SORTUJ', 'DOMYŚLNIESORTUJ', 'DEFAULTSORT:', 'DEFAULTSORTKEY:', 'DEFAULTCATEGORYSORT:']
    'trwiki',       # WARNING: API error abusefilter-disallowed: abusefilter-sortname: no DEFAULTSORT statements at all
}

# List of Wikipedia's that do not support bot updates (for different reasons)
veto_sitelinks = {
    # Requires CAPTCHA => blocking bot scripts (?)
    'eswiki', 'fawiki', 'jawiki', 'ptwiki', 'ruwiki', 'simplewiki', 'ttwiki', 'viwiki', 'wuuwiki', 'zhwiki',

    # Blocked (requires mandatory bot flag)
    'iswiki',       # https://is.wikipedia.org/w/index.php?title=Kerfissíða:Aðgerðaskrár/block&page=User%3AGeertivpBot
    'itwiki',       # https://it.wikipedia.org/wiki/Special:Log/block?page=User:GeertivpBot
    'slwiki',       # Requires wikibot flag
    'svwiki',       # Infobox
    'zh_yuewiki',   ## seems not to work? https://zh-yue.wikipedia.org/w/index.php?title=Special:日誌/block&page=User%3AGeertivpBot

    # To proactively request a bot flag before updating statements
    'enwiki',

    # Bot approval pending
    #'fiwiki',
    # https://fi.wikipedia.org/wiki/Käyttäjä:GeertivpBot
    # https://meta.wikimedia.org/wiki/User_talk:Geertivp#c-01miki10-20230714212500-Please_request_a_bot_flag_%40_fiwiki

    # Unblocked (after an issue was fixed)
    #'nowiki',      # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot

    # Unidentified problem

    #'be_taraskwiki',   # instantiated using different code "be-x-old" ??

    # Non-issues (temporary or specific problems)

    # 'cswiki',
    # WARNING: Add Commonscat Fremantle Highway (ship, 2013) to cswiki
    # ERROR: Error processing Q121093616, Edit to page [[cs:MV Fremantle Highway]] failed:
    # Editing restricted by {{bots}}, {{nobots}} or site's equivalent of {{in use}} template
    # https://cs.wikipedia.org/wiki/MV_Fremantle_Highway
    # {{Pracuje se|2 dní}}
    # Page is protected against (bot) updates. We can ignore this temporary restriction.
    # https://cs.wikipedia.org/wiki/Speciální:Příspěvky/GeertivpBot

    # others to be added
}

# Specific sequence to be aligned with sitelink_dict_list
instance_types = [
    {HUMANINSTANCE},        # Human
    {'Q185187', 'Q38720'},  # Mills
]

# List of recognized infoboxes
# Using this list, language templates are automatically generated
sitelink_dict_list = [
# Required to be in strict sequence
# See also instance_types (2 elements)
    'Q6249834',         # infoboxlist[0] Infobox person (to generate Infobox template on Wikipedia), 39 s, 68 s
    'Q13383928',        # infoboxlist[1] Infobox Infobox windmill

# Strict sequence numbering
    'Q47517487',        # infoboxlist[2] Wikidata infobox
    'Q17534637',        # infoboxlist[3] Infobox person Wikidata (overrule)

# Not required to be in sequence
# ... other infoboxes to be added...

# Human
    'Q5615832',         # Infobox author, 21 s, 22 s
    'Q5616161',         # Infobox musical artist, 4 s
    'Q5616966',         # Infobox football biography
    'Q5624818',         # Infobox scientist, 2 s
    'Q5626285',         # Infobox monarch
    'Q5904762',         # Infobox sportsperson
    'Q5914426',         # Infobox artist, 1 s
    'Q5929832',         # Infobox military person
    'Q6424841',         # Infobox politician
    'Q6583638',         # Infobox cyclist, 1 s
    'Q14358369',        # Infobox actor
    'Q14458505',        # Infobox journalist

# Non-human
    'Q52496',           # Taxobox, 8 s
    'Q5683132',         # Infobox place, 10 s
    'Q5747491',         # Taxobox begin
    'Q6055178',         # Infobox park
    'Q6630855',         # Infobox food, 3 s
    'Q5896997',         # Infobox world heritage
    'Q5906647',         # Infobox building

    'Q5901151',         # Infobox sport
    'Q6190581',         # Infobox organization

    'Q6434929',         # Multiple image, 9 s
    'Q13553651',        # Infobox (overrule)
    # others to be added

# Shouldn't we add these to all non-human Wikipedia pages missing an Infobox?
    'Q5626735',         # Infobox generic, 12 s

# Redundant language codes rue, sv; .update() overrules => which one to give preference?
# https://favtutor.com/blogs/merge-dictionaries-python
    'Q20702632',        # Databox (nl; still experimental) => seems to work pretty well... {{#invoke:Databox|databox}}, 1 s
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
        baselabel = baselabel[:suffix.start()]      # Get canonical form

    colonloc = baselabel.find(':')
    commaloc = NAMEREVRE.search(baselabel)

    # Reorder "lastname, firstname" and concatenate with space
    if colonloc < 0 and commaloc:
        baselabel = baselabel[commaloc.start() + 1:] + ' ' + baselabel[:commaloc.start()]
        baselabel = baselabel.replace(',', ' ')     # Multiple ,
    baselabel = ' '.join(baselabel.split())         # Remove redundant spaces
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
    :return: label dict set(including aliases; index by ISO language code)

    Example of usage:
        Image namespace name (Q478798).
    """
    prevnow = datetime.now()	    # Refresh the timestamp to time the following transaction
    labeldict = {}
    item = get_item_page(qnumber)
    # Get target labels
    for lang in item.labels:
        labeldict[lang] = set()
        labeldict[lang].add(item.labels[lang])
        if lang in item.aliases:
            for val in item.aliases[lang]:
                labeldict[lang].add(val)
    now = datetime.now()	        # Refresh the timestamp to time the following transaction
    isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Needed to format output
    pywikibot.info('{}\tLoading item labels {} ({}) took {:d} seconds'
                   .format(isotime, get_item_header(item.labels), qnumber, int((prevnow - now).total_seconds())))
    return labeldict


def get_wikipedia_sitelink_template_dict(qnumber) -> {}:
    """
    Get the Wikipedia template names in all languages for a Qnumber.
    :param qnumber: sitelink list
    :return: template dict (index by sitelang)

    Functionality:
        Filter for Wikipedia and the template namespace.

    Example of usage:
        Generate {{Commonscat}} statements for Q48029.

    """

    # Optimisation: allow for fast shortcuts for known/ignored Wikipedias
    global new_wikis
    global valid_wikis

    prevnow = datetime.now()	    # Start of transaction
    sitedict = {}
    item = get_item_page(qnumber)
    # Get target sitelinks
    for sitelang in item.sitelinks:
        # Fast skip non-Wikipedia sites
        if sitelang[-4:] == 'wiki' and '_x_' not in sitelang and sitelang not in new_wikis:    # Ignore special languages
            try:
                # Get template title
                sitelink = item.sitelinks[sitelang]
                if (sitelink.namespace == TEMPLATENAMESPACE
                        and (sitelang in valid_wikis
                            or str(sitelink.site.family) == 'wikipedia')):
                    sitedict[sitelang] = sitelink.title
                    valid_wikis.add(sitelang)
            except Exception as error:
                new_wikis.add(sitelang)
                pywikibot.error(error)      # Site error
                #pdb.set_trace()

    now = datetime.now()	        # Refresh the timestamp to time the following transaction
    isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Needed to format output
    pywikibot.info('{}\tLoading {} ({}) took {:d} seconds for {:d} items'
                   .format(isotime, get_item_header(item.labels), qnumber,
                           int((now - prevnow).total_seconds()), len(sitedict)))
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


def get_prop_val_str(item, proplist) -> str:
    ## not used... could be removed
    """Get property value string
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
    """Get property value label
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
                    item_prop_val += get_item_header(val.labels) + '/'
                except Exception as error:
                    pywikibot.error(error)      # Site error
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
                except Exception as error:
                    pywikibot.error(error)      # Site error
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


def is_foreign_lang(lang_list) -> str:
    """ Check if foreign language"""
    for val in lang_list:
        if not ROMANRE.search(val):
            return val
    return ''


def is_veto_lang_label(lang_list) -> bool:
    """
    Check if language is blacklisted
    """
    isveto = False
    for seq in lang_list:
        val = seq.getTarget()
        if (val.language not in main_languages
                or val.language in veto_languages
                or not ROMANRE.search(val.text)):
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
        except Exception as error:
            pywikibot.error(error)      # Site error
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
        except Exception as error:
            pywikibot.error(error)      # Site error
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
        except Exception as error:
            pywikibot.error(error)      # Site error
    return ''


def property_is_in_list(statement_list, proplist) -> str:
    """
    Verify if a property is used for a statement

    :param statement_list: Statement list
    :param proplist:       List of properties (string)
    :return: Matching property
    """
    for prop in proplist:
        if prop in statement_list:
            return prop
    return ''


def add_missing_sdc_depicts(item):
    """
    Add missing Wikimedia Commons SDC P180 depict statements

    :param item: Wikidata item to process

    Algorithm:

        Loop through the Wikidata statements of the item
        and find e.g. P18 statements
        that don't have an equivalent SDC P180 statement.
    """

    """
Structure of the Wikimedia Commons structured data statements:

{"entities":{"M17372639":{"pageid":17372639,"ns":6,"title":"File:Brugs Kerkhof Guido Gezelle.jpg","lastrevid":772271921,"modified":"2023-06-08T13:47:37Z","type":"mediainfo","id":"M17372639","labels":{},"descriptions":{},"statements":{"P571":[{"mainsnak":{"snaktype":"value","property":"P571","hash":"135ee2f61e09ee2bb8b4328db588d6edd29a3615","datavalue":{"value":{"time":"+2011-10-26T00:00:00Z","timezone":0,"before":0,"after":0,"precision":11,"calendarmodel":"http://www.wikidata.org/entity/Q1985727"},"type":"time"}},"type":"statement","id":"M17372639$26191E8E-D341-4AFE-BF73-132613446366","rank":"normal"}],"P6216":[{"mainsnak":{"snaktype":"value","property":"P6216","hash":"5570347fdc76d2a80732f51ea10ee4b144a084e0","datavalue":{"value":{"entity-type":"item","numeric-id":50423863,"id":"Q50423863"},"type":"wikibase-entityid"}},"type":"statement","id":"M17372639$042DC9C2-0F7E-482D-A696-0AB727037795","rank":"normal"}],"P275":[{"mainsnak":{"snaktype":"value","property":"P275","hash":"a35b4558d66c92eacbe2f569697ffb1934e0316e","datavalue":{"value":{"entity-type":"item","numeric-id":14946043,"id":"Q14946043"},"type":"wikibase-entityid"}},"type":"statement","id":"M17372639$C3B253E5-D127-40FA-B558-4C1544D1FA73","rank":"normal"}],"P7482":[{"mainsnak":{"snaktype":"value","property":"P7482","hash":"83568a288a8b8b4714a68e7239d8406833762864","datavalue":{"value":{"entity-type":"item","numeric-id":66458942,"id":"Q66458942"},"type":"wikibase-entityid"}},"type":"statement","id":"M17372639$F9CE62D8-A7EE-48FC-BC8C-502BFD476D2B","rank":"normal"}],"P170":[{"mainsnak":{"snaktype":"somevalue","property":"P170","hash":"d3550e860f988c6675fff913440993f58f5c40c5"},"type":"statement","qualifiers":{"P3831":[{"snaktype":"value","property":"P3831","hash":"c5e04952fd00011abf931be1b701f93d9e6fa5d7","datavalue":{"value":{"entity-type":"item","numeric-id":33231,"id":"Q33231"},"type":"wikibase-entityid"}}],"P2093":[{"snaktype":"value","property":"P2093","hash":"e0c0197e220178aa7d77a49cc3226a463b153f83","datavalue":{"value":"Zeisterre","type":"string"}}],"P4174":[{"snaktype":"value","property":"P4174","hash":"2b9891905fac0e237e7575adfde698e2a63e7cd8","datavalue":{"value":"Zeisterre","type":"string"}}],"P2699":[{"snaktype":"value","property":"P2699","hash":"af85c0e2a655a09324c402e4452ec2ef2abc9ea8","datavalue":{"value":"http://commons.wikimedia.org/wiki/User:Zeisterre","type":"string"}}]},"qualifiers-order":["P3831","P2093","P4174","P2699"],"id":"M17372639$234DD68C-428C-41E5-A098-9364961A6BC0","rank":"normal"}],"P180":[{"mainsnak":{"snaktype":"value","property":"P180","hash":"b3c128d5850ce0706e694afc00aa2fb5ccac7daa","datavalue":{"value":{"entity-type":"item","numeric-id":173387,"id":"Q173387"},"type":"wikibase-entityid"}},"type":"statement","qualifiers":{"P642":[{"snaktype":"value","property":"P642","hash":"13ca233362287df2f52077d460ebef58a666c855","datavalue":{"value":{"entity-type":"item","numeric-id":336977,"id":"Q336977"},"type":"wikibase-entityid"}}]},"qualifiers-order":["P642"],"id":"M17372639$b8185896-4eab-2715-5606-388898d07071","rank":"normal"}]}}}}
    """

    # Prepare the static part of the SDC P180 depict statement
    # The numeric values needs to be added at runtime based on the item number.
    depict_statement = {
        'claims': [{
            'type': 'statement',
            'mainsnak': {
                'snaktype': 'value',
                'property': DEPICTSPROP,    ## other property for subclasses?
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

    if SUBCLASSPROP in item.claims:
        ## We need other logic for subclasses
        # https://commons.wikimedia.org/wiki/File:Oudenaarde_Tacambaroplein_oorlogsmonument_-_228469_-_onroerenderfgoed.jpg
        # https://www.wikidata.org/wiki/Q3381576
        # https://www.wikidata.org/wiki/Q91079944
        # Could photography genre generate genre statement when having instance genre?
        pywikibot.warning('Not adding depict statements for subclass ({}) item'
                          .format(SUBCLASSPROP))
    else:
        # Find all media files for the item
        for prop in item.claims:
            if prop in media_props:
                # Reinitialise the depict statement (reset previous loop updates)
                if prop in depict_item_type:
                    # Set compound depict
                    qnumber = depict_item_type[prop]
                    item_desc = get_item_header(get_item_page(qnumber).labels)
                    """
    Need to add qualifier
    https://commons.wikimedia.org/wiki/Special:EntityData/M17372639.json
    "qualifiers":{"P642":[{"snaktype":"value","property":"P642","hash":"13ca233362287df2f52077d460ebef58a666c855","datavalue":{"value":{"entity-type":"item","numeric-id":336977,"id":"Q336977"},"type":"wikibase-entityid"}}]},"qualifiers-order":["P642"],"id":"M17372639$b8185896-4eab-2715-5606-388898d07071","rank":"normal"}]}
                    """
                    # Build the depict qualifier
                    depict_statement['claims'][0]['rank'] = 'normal'
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

                    depictsdescr = 'Add SDC depicts {} ({}) of {} ({})'.format(item_desc, qnumber, get_item_header(item.labels), item.getID())
                else:
                    # Set simple depicts
                    qnumber = item.getID()
                    item_desc = get_item_header(item.labels)
                    if 'qualifiers' in depict_statement['claims'][0]:       # Compound depict statement
                        del(depict_statement['claims'][0]['qualifiers'])
                        del(depict_statement['claims'][0]['qualifiers-order'])
                    depictsdescr = 'Add SDC depicts {} ({})'.format(item_desc, qnumber)

                depict_statement['claims'][0]['mainsnak']['datavalue']['value']['id'] = qnumber
                depict_statement['claims'][0]['mainsnak']['datavalue']['value']['numeric-id'] = int(qnumber[1:])

                for seq in item.claims[prop]:
                    # Verify if there is a depict statement
                    depict_missing = True

                    if prop not in depict_item_type:
                        # Set preferred rank because it comes from a Wikidata P18 or comparable statement
                        depict_statement['claims'][0]['rank'] = 'preferred'

                    # Get SDC media file info
                    media_page = seq.getTarget()
                    media_name = media_page.title()
                    # https://commons.wikimedia.org/entity/M63763537
                    media_identifier = 'M' + str(media_page.pageid)
                    sdc_request = site.simple_request(action='wbgetentities', ids=media_identifier)
                    commons_item = sdc_request.submit()
                    sdc_data = commons_item.get('entities').get(media_identifier)
                    sdc_statements = sdc_data.get('statements')

                    if sdc_statements:
                        # Get location from metadata
                        for val in location_target:
                            location_coord = sdc_statements.get(val[1])
                            if location_coord:
                                pywikibot.info('{}: {},{}/{}'.format(val[0],
                                        location_coord[0]['mainsnak']['datavalue']['value']['latitude'],
                                        location_coord[0]['mainsnak']['datavalue']['value']['longitude'],
                                        location_coord[0]['mainsnak']['datavalue']['value']['altitude']))

                        # Get any depict statement
                        depict_list = sdc_statements.get(DEPICTSPROP)   ## other property for subclasses?
                        if depict_list:
                            for depict in depict_list:
                                # Only allow for a single preferred rank -> need to verify all instances
                                if depict['rank'] == 'preferred':
                                    depict_statement['claims'][0]['rank'] = 'normal'
                                if qnumber == get_sdc_item(depict['mainsnak']).getID():
                                    depict_missing = False

                    """
https://commons.wikimedia.org/wiki/Special:EntityData/M82236232.json
"P180":[{"mainsnak":{"snaktype":"value","property":"P180","hash":"7282af9508eed4a6f6ebc2e92db7368ecdbb61ab","datavalue":{"value":{"entity-type":"item","numeric-id":22668172,"id":"Q22668172"},"type":"wikibase-entityid"}},"type":"statement","id":"M82236232$e1491557-469c-7672-92d6-6e490f7403bf","rank":"normal"}],
                    """
                    if depict_missing:
                        # Add the SDC depict statements for this item
                        pywikibot.debug(depict_statement)
                        commons_token = site.tokens['csrf']
                        sdc_payload = {
                            'action': 'wbeditentity',
                            'format': 'json',
                            'id': media_identifier,
                            'data': json.dumps(depict_statement, separators=(',', ':')),
                            'token': commons_token,
                            'summary': transcmt + ' ' + depictsdescr + ' statement',
                            'bot': BOTFLAG,
                        }

                        sdc_request = site.simple_request(**sdc_payload)
                        try:
                            sdc_request.submit()
                            pywikibot.warning('{} to {} ({}) {} {}'
                                              .format(depictsdescr, get_property_label(prop), prop, media_identifier, media_name))
                        except Exception as error:
                            pywikibot.error(error)
                            pywikibot.info(sdc_request)
                            pdb.set_trace()


def add_item_statement(item, propty, sitem):
    """
    Add statement to item

    :param item: main item
    :param propty: property
    :param sitem: item to assign
    :return: True if updated
    """
    updated = False
    qnumber = item.getID()
    sqnumber = sitem.getID()
    if (propty not in item.claims
            or not item_is_in_list(item.claims[propty], [sqnumber])):
        propty_label = get_property_label(propty)
        claim = pywikibot.Claim(repo, propty)
        claim.setTarget(sitem)
        item.addClaim(claim, bot=BOTFLAG, summary=transcmt + ' Add {} ({})'
                          .format(propty_label, propty))
        pywikibot.warning('Add {} ({}) {} ({}) to {} ({})'
                          .format(propty_label, propty,
                                  get_item_header(sitem.labels), sqnumber,
                                  get_item_header(item.labels), qnumber))
        updated = True
    return updated


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
    pywikibot.debug(item_list)
    pywikibot.info('Processing {:d} statements'.format(len(item_list)))

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

            label = get_item_header(item.labels)      # Get label
            nationality = get_prop_val_object_label(item,   [NATIONALITYPROP, COUNTRYPROP, COUNTRYORIGPROP, JURISDICTIONPROP])    # nationality
            birthday    = get_prop_val_year(item,     [BIRTHDATEPROP, FOUNDINGDATEPROP, STARTDATEPROP, OPERATINGDATEPROP])    # birth date (normally only one)
            deathday    = get_prop_val_year(item,     [DEATHDATEPROP, DISSOLVDATEPROP, ENDDATEPROP, SERVICEENDDATEPROP]) # death date (normally only one)

            # Cleanup the label
            if label != '-':
                # Remove redundant trailing writing direction
                while len(label) > 0 and label[len(label)-1] in [ '\u200e', '\u200f']:
                    label=label[:len(label)-1]
                # Replace alternative space character
                label = label.replace('\u00a0', ' ').strip()

                if item_instance in human_type_list:
                    label = get_canon_name(label)

                if (    not ROMANRE.search(label)
                        or (mainlang in item.aliases
                            and is_foreign_lang(item.aliases[mainlang]))
                        or (NATIVENAMEPROP in item.claims
                            and is_veto_lang_label(item.claims[NATIVENAMEPROP]))        # name in native language
                        or (NATIVELANGPROP in item.claims
                            and item_is_in_list(item.claims[NATIVELANGPROP], veto_languages_id))     # native language
                        or (LANGKNOWPROP in item.claims
                            and item_is_in_list(item.claims[LANGKNOWPROP], veto_languages_id))): # language knowledge
                    status = 'Language'
                elif (FOREIGNSCRIPTPROP in item.claims
                        and is_veto_script(item.claims[FOREIGNSCRIPTPROP])):            # foreign script system
                    status = 'Script'
                elif NOBLENAMEPROP in item.claims:          # Noble names are exceptions
                    status = 'Noble'
                elif NATIONALITYPROP not in item.claims:    # Missing nationality (old names)
                    status = 'Nationality'
                elif item_is_in_list(item.claims[NATIONALITYPROP], veto_countries):     # nationality blacklist (languages)
                    status = 'Country'
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
                try:
                    sitelink = item.sitelinks[sitelang]
                    wm_family = str(sitelink.site.family)
                except Exception as error:
                    # CRITICAL: Exiting due to uncaught exception UnknownSiteError: Language 'gsw' does not exist in family wikipedia for Q4022
                    wm_family = ''
                    ##new_wikis.add(sitelang)   # Would require Global
                    pywikibot.error(error)      # Site error

                if (wm_family == 'wikipedia'):
                    # See https://www.wikidata.org/wiki/User_talk:GeertivpBot#Don%27t_use_%27no%27_label
                    lang = sitelink.site.lang
                    if lang == 'bh':    # Canonic language names
                        lang = 'bho'
                    elif lang == 'no':
                        lang = 'nb'

                    # Only clean human names
                    baselabel = sitelink.title
                    if item_instance in human_type_list:
                        baselabel = get_canon_name(baselabel)

                    ## Fix language caps
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
                        pywikibot.info(pagedesc)
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

# (6) Merge labels for missing Latin languages
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
                    # Sitelink pages might not be available (quick escape via except pass; an error message is printed).
                    itmlist = set()
                    if lang in item.labels:
                        sitedict = {'site': sitelang, 'title': item.labels[lang]}
                        try:
                            # Try to add a sitelink now
                            item.setSitelink(sitedict, bot=BOTFLAG, summary=transcmt + ' Add sitelink')
                            status = 'Sitelink'
                        except pywikibot.exceptions.OtherPageSaveError as error:
                            # Two or more sitelinks can have conflicting Qnumbers.
                            # Get unique Q-numbers, skip duplicates (order not guaranteed)
                            itmlist = set(QSUFFRE.findall(str(error)))
                            if len(itmlist) > 0:
                                itmlist.remove(qnumber)

                            if len(itmlist) > 0:
                                pywikibot.info('Sitelink {}:{} ({}) conflicting with {}'
                                               .format(lang, item.labels[lang], qnumber, itmlist))
                                status = 'DupLink'	    # Conflicting sitelink statement
                                errcount += 1
                                exitstat = max(exitstat, 10)

                    if sitelang not in item.sitelinks and lang in item.aliases:
                        # If the sitelink is still missing, try to add a sitelink from the aliases
                        for seq in item.aliases[lang]:
                            sitedict = {'site': sitelang, 'title': seq}
                            try:
                                item.setSitelink(sitedict, bot=BOTFLAG, summary=transcmt + ' Add sitelink')
                                status = 'Sitelink'
                                break
                            except pywikibot.exceptions.OtherPageSaveError as error:
                                # Get unique Q-numbers, skip duplicates (order not guaranteed)
                                aitmlist = set(QSUFFRE.findall(str(error)))
                                if len(aitmlist) > 0:
                                    aitmlist.remove(qnumber)

                                if len(aitmlist) > 0:
                                    pywikibot.info('Sitelink {}:{} ({}) conflicting with {}'
                                                   .format(lang, seq, qnumber, aitmlist))
                                    itmlist = itmlist.union(aitmlist)
                                    status = 'DupLink'	    # Conflicting sitelink statement
                                    errcount += 1
                                    exitstat = max(exitstat, 10)

                    # Create symmetric Not Equal statements
                    # Inverse statement will be executed below
                    if INSTANCEPROP in item.claims:
                        for sqnumber in itmlist:
                            relitem = get_item_page(sqnumber)
                            if (INSTANCEPROP in relitem.claims
                                    and item.claims[INSTANCEPROP] == relitem.claims[INSTANCEPROP]):
                                add_item_statement(item, NOTEQTOPROP, relitem)

            maincat_item = ''
            # Add inverse statement
            if MAINCATEGORYPROP in item.claims:
                maincat_item = get_item_page(item.claims[MAINCATEGORYPROP][0].getTarget())

# (9) Set Commons Category sitelinks
            # Search for candidate Commons Category
            if COMMONSCATPROP in item.claims:                  # Get candidate category
                commonscat = item.claims[COMMONSCATPROP][0].getTarget() # Only take first value
            elif 'commonswiki' in item.sitelinks:           # Commons sitelink exists
                sitelink = item.sitelinks['commonswiki']
                commonscat = sitelink.title[sitelink.title.find(':') + 1:]
            elif maincat_item and COMMONSCATPROP in maincat_item.claims:
                commonscat = maincat_item.claims[COMMONSCATPROP][0].getTarget()
            elif COMMONSGALLARYPROP in item.claims:                # Commons gallery page
                commonscat = item.claims[COMMONSGALLARYPROP][0].getTarget()
            elif COMMONSCREATORPROP in item.claims:              # Commons creator page
                commonscat = item.claims[COMMONSCREATORPROP][0].getTarget()
            elif COMMONSINSTPROP in item.claims:               # Commons institution page
                commonscat = item.claims[COMMONSINSTPROP][0].getTarget()
            elif item_instance in lastname_type_list:
                commonscat = label + ' (surname)'
            elif enlang_list[0] in item.labels:             # English label might possibly be used as Commons category
                commonscat = item.labels[enlang_list[0]]
            elif mainlang in item.labels:                   # Otherwise the native label
                commonscat = item.labels[mainlang]

            if commonscat and 'commonswiki' not in item.sitelinks:
                # Try to create a Wikimedia Commons Category page link
                sitedict = {'site': 'commonswiki', 'title': 'Category:' + commonscat}
                try:
                    item.setSitelink(sitedict, bot=BOTFLAG, summary=transcmt + ' Add sitelink')
                    status = 'Commons'
                except pywikibot.exceptions.OtherPageSaveError as error:
                    # Get unique Q-numbers, skip duplicates (order not guaranteed)
                    itmlist = set(QSUFFRE.findall(str(error)))
                    if len(itmlist) > 0:
                        itmlist.remove(qnumber)

                    if len(itmlist) > 0:
                        pywikibot.info('Category {} ({}) conflicting with {}'
                                       .format(commonscat, qnumber, itmlist))
                        status = 'DupCat'	    # Conflicting category statement
                        errcount += 1
                        exitstat = max(exitstat, 10)

                        # Create symmetric Not Equal statements
                        # Inverse statement will be executed below
                        if INSTANCEPROP in item.claims:
                            for sqnumber in itmlist:
                                relitem = get_item_page(sqnumber)
                                if (INSTANCEPROP in relitem.claims
                                        and item.claims[INSTANCEPROP] == relitem.claims[INSTANCEPROP]):
                                    add_item_statement(item, NOTEQTOPROP, relitem)
                    # Revoke the Commonscat
                    commonscat = ''

            if commonscat:
                # Amend EN label from the Commons Category
                item_name_canon = unidecode.unidecode(commonscat).casefold()
                baselabel = commonscat
                # Lowercase first character
                if noun_in_lower:
                    baselabel = baselabel[0].lower() + baselabel[1:]

                # Add Commons category
                if COMMONSCATPROP not in item.claims:
                    claim = pywikibot.Claim(repo, COMMONSCATPROP)
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
                    pageupdated = transcmt + ' Add'

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
                # Get target sitelink, provided it is in Wikipedia
                if (sitelang in valid_wikis
                        and item.sitelinks[sitelang].namespace == MAINNAMESPACE):
                    wpcatpage = ''
                    sitelink = item.sitelinks[sitelang]

                    lang = sitelink.site.lang
                    if lang == 'bh':    # Canonic language names
                        lang = 'bho'
                    elif lang == 'no':
                        lang = 'nb'

                    if not maincat_item:
                        pass
                    elif sitelang in maincat_item.sitelinks:
                        # Wikipedia category does exist
                        wpcatpage = maincat_item.sitelinks[sitelang].title
                    elif lang in maincat_item.labels:
                        # Possibly unexisting Wikipedia category
                        wpcatpage = maincat_item.labels[lang][maincat_item.labels[lang].find(':') + 1:]
                    commonscatqueue.append((item, sitelang, item_instance, commonscat, wpcatpage))
                    ### Problem with SORTORDER not addded if status == 'Update' ??

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
                pdb.set_trace()
                #raise      # This error might hide more data quality problems

# Now process any claims

# (12) Replicate Moedertaal -> Taalbeheersing
            if NATIVELANGPROP in item.claims:
                target = get_item_page(item.claims[NATIVELANGPROP][0].getTarget())
                nat_languages.add(target.getID())           # Add a natural language

                if add_item_statement(item, LANGKNOWPROP, target):
                    status = 'Update'

# (13) Replicate Taalbeheersing -> Moedertaal
            if item_instance == HUMANINSTANCE:
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
                        and target.getID() not in artificial_languages      # Filter non-natural languages like Esperanto
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
            if (item_instance == HUMANINSTANCE
                    and NATIVELANGPROP not in item.claims
                    and NATIVENAMEPROP in item.claims
                    and len(item.claims[NATIVENAMEPROP]) == 1):
                # Get native language from name
                mothlang = item.claims[NATIVENAMEPROP][0].getTarget().language
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

            elif INSTANCEPROP in item.claims:
                pywikibot.info('Both instance ({}) and subclass ({}) property for item {}'
                               .format(INSTANCEPROP, SUBCLASSPROP, qnumber))

# (15) Add symmetric and reciproque statements
            # Identify mandatory statements
            for propty in mandatory_relation:
                if propty in item.claims:
                    for seq in item.claims[propty]:
                        sitem = seq.getTarget()
                        if sitem and add_item_statement(sitem, mandatory_relation[propty], item):
                            status = 'Update'

# (16) Add symmetric relevant person statements
            ### Need more finetuning...
            if KEYRELATIONPROP in item.claims:
                # https://www.wikidata.org/wiki/Q336977#P3342 (correspondents of Guido Gezelle)
                for seq in item.claims[KEYRELATIONPROP]:
                    if (OBJECTROLEPROP in seq.qualifiers
                            # Correspondent
                            and seq.qualifiers[OBJECTROLEPROP][0].getTarget().getID() == CORRESPONDENTINSTANCE
                            and (KEYRELATIONPROP not in seq.getTarget().claims
                                 or not item_is_in_list(seq.getTarget().claims[KEYRELATIONPROP], [qnumber]))):
                        if False:
                            ### It is not sure that the relationship is symmetric
                            claim = pywikibot.Claim(repo, KEYRELATIONPROP)
                            claim.setTarget(item)
                            seq.getTarget().addClaim(claim, bot=BOTFLAG, summary=transcmt + ' Add symmetric statement')
                            for qual in seq.qualifiers:
                                # Dates can be assymetric, so don't copy them
                                if qual not in time_props:
                                    qualifier = pywikibot.Claim(repo, qual)
                                    qualifier.setTarget(seq.qualifiers[qual][0].getTarget())
                                    claim.addQualifier(qualifier, summary=transcmt + ' Add symmetric statement')
                                ### Reuse the reference?
                        else:
                            pywikibot.info('Possible missing symmetric statement {}:{} {} ({}) to {} ({})'
                                              .format(KEYRELATIONPROP, CORRESPONDENTINSTANCE,
                                                      get_item_header(item.labels), qnumber,
                                                      get_item_header(seq.getTarget().labels), seq.getTarget().getID()))

# (17) Add missing Wikimedia Commons SDC depicts statement
            add_missing_sdc_depicts(item)

# (18) Items has possibly been updated - Refresh item data
            label = get_item_header(item.labels)            # Get label (refresh label)
            descr = get_item_header(item.descriptions)      # Get description
            alias = get_item_header(item.aliases)           # Get alias

# (19) Update Wikipedia pages
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
                    pageupdated = transcmt + ' Add'
                    item_instance = addcommonscat[2]

                    # Build template infobox list regular expression
                    infobox_template = '{{.*Infobox|{{Wikidata|{{Persondata|{{Multiple image|{{Databox'
                    if lang in infobox_localname:
                        for val in infobox_localname[lang]:
                            infobox_template += '|{{.*' + val

                    for ibox in range(len(infoboxlist)):
                        if sitelang in infoboxlist[ibox]:
                            infobox_template += '|{{' + infoboxlist[ibox][sitelang]

                    # Add an item-specific Wikidata infobox
                    for ibox in [0, 1]:     ## Hardcoded
                        if (sitelang in infoboxlist[ibox]
                                and item_instance in instance_types[ibox]
                                and not re.search(infobox_template,
                                                  page.text, flags=re.IGNORECASE)):
                            addinfobox = infoboxlist[ibox][sitelang]
                            page.text = '{{' + addinfobox + '}}\n' + page.text
                            pageupdated += ' ' + addinfobox
                            pywikibot.warning('Add {} to {}'.format(addinfobox, sitelang))
                            break

                    # Add general Wikidata infobox
                    if (sitelang in infoboxlist[2]
                            and not re.search(infobox_template,
                                              page.text, flags=re.IGNORECASE)):
                        addinfobox = infoboxlist[2][sitelang]
                        page.text = '{{' + addinfobox + '}}\n' + page.text
                        pageupdated += ' ' + addinfobox
                        pywikibot.warning('Add {} to {}'.format(addinfobox, sitelang))

                    # Add one P18 missing image on the Wikipedia page
                    # https://doc.wikimedia.org/pywikibot/stable/api_ref/pywikibot.site.html#pywikibot.site._apisite.APISite.namespace
                    # Could we have other image or video properties?
                    # Could we have sound files?
                    if IMAGEPROP in item.claims and lang in item.labels:
                        # Get the first image from Wikidata
                        image_page = item.claims[IMAGEPROP][0].getTarget()
                        image_name = image_page.title()
                        file_name = image_name.split(':', 1)
                        wpfilenamespace = sitelink.site.namespace(FILENAMESPACE)
                        image_name = wpfilenamespace + ':' + file_name[1]
                        file_name_re = file_name[1].replace('(', r'\(').replace(')', r'\)')

                        # Only add a first image
                        if (not re.search(r'\[\[' + wpfilenamespace
                                            + r':|\[\[File:|\[\[Image:|<gallery|</gallery>|'
                                            + infobox_template
                                            # no File: because of possible Infobox parameter
                                            + '|' + file_name_re,
                                          page.text, flags=re.IGNORECASE)):

                            # Add 'upright' if height > 1.44 * width
                            image_flag = 'thumb'
                            try:
                                file_info = image_page.latest_file_info.__dict__
                                file_height = file_info['height']
                                file_width = file_info['width']
                                if file_height > file_width * 1.44:
                                    image_flag += '|' + sitelink.site.getmagicwords('img_upright')[0]
                            except:
                                pass    # Image size missing

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

                    # Add reference template
                    inserttext = ''
                    reftemplate = ''
                    find_reference = '<references />|<references/>'
                    if sitelang in referencelist[0]:
                        reftemplate = referencelist[0][sitelang]
                        find_reference += '|{{' + reftemplate + '}}'    # Requires template terminator

                    refreplace = re.search(find_reference, page.text, flags=re.IGNORECASE)
                    if (refreplace and refreplace.group(0).startswith('<references')
                            and reftemplate and sitelang not in veto_references):
                        inserttext = '{{' + reftemplate + '}}'
                        pageupdated += ' ' + reftemplate
                        pywikibot.warning('Add {} to {}'.format(reftemplate, sitelang))

                    # Add an Authority control template for humans
                    if (item_instance == HUMANINSTANCE and sitelang in authoritylist[0]):
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

                    # Prepare Commons Category logic
                    skip_commonscat = '{{Commons'
                    for ibox in range(len(commonscatlist)):
                        if sitelang in commonscatlist[ibox]:
                            skip_commonscat += '|{{' + commonscatlist[ibox][sitelang]

                    # No Commonscat for Interproject links
                    for ibox in [1, 2]:
                        if sitelang in authoritylist[ibox]:
                            skip_commonscat += '|{{' + authoritylist[ibox][sitelang]

                    categorytext = ''
                    wpcommonscat = addcommonscat[3]
                    wpcommonscat_re = wpcommonscat.replace('(', r'\(').replace(')', r'\)')
                    if (wpcommonscat and sitelang in commonscatlist[0]
                            # Avoid duplicate Commons cat with human Infoboxes
                            and not (item_instance == HUMANINSTANCE         ## Only for humans with infoboxes or authority
                                     and sitelang in veto_commonscat)       # Other exceptions to avoid being too restrictive
                            and not re.search(skip_commonscat +             # Commons Category is only in English
                                                r'|\[\[Category:' + wpcommonscat_re,
                                              page.text, flags=re.IGNORECASE)):
                        commonscattemplate = commonscatlist[0][sitelang]
                        # Add missing Commons Category
                        if (COMMONSCATPROP in item.claims or sitelink.title == wpcommonscat):
                            categorytext = '{{' + commonscattemplate + '}}'
                        else:
                            categorytext = '{{' + commonscattemplate + '|' + wpcommonscat + '}}'
                        pageupdated += ' [[c:Category:{1}|{0} {1}]]'.format(commonscattemplate, wpcommonscat)
                        pywikibot.warning('Add {} {} to {}'
                                          .format(commonscattemplate, wpcommonscat, sitelang))

                    sort_words = sitelink.site.getmagicwords('defaultsort')
                    # UK sort_words
                    # ['СТАНДАРТНЕ_СОРТУВАННЯ:_КЛЮЧ_СОРТУВАННЯ', 'СОРТИРОВКА_ПО_УМОЛЧАНИЮ', 'КЛЮЧ_СОРТИРОВКИ', 'DEFAULTSORT:', 'DEFAULTSORTKEY:', 'DEFAULTCATEGORYSORT:']

                    # Ignore invalid sortwords
                    sort_word = sort_words[0]
                    if sort_word[-1] != ':':
                        sort_word += ':'

                    sort_template = '|{{DEFAULTSORT:'
                    for val in sort_words:
                        sort_template += '|{{' + val

                    if item_instance == HUMANINSTANCE and sitelang not in veto_defaultsort:
                        try:
                            # In exceptional cases the name is completely wrong (e.g. artist name versus official name)
                            if (len(item.claims[LASTNAMEPROP]) < 2
                                    and len(item.claims[FIRSTNAMEPROP]) < 2
                                    and not property_is_in_list(item.claims, alternative_person_names_props)):
                                lastname = item.claims[LASTNAMEPROP][0].getTarget().labels[lang]
                                firstname = item.claims[FIRSTNAMEPROP][0].getTarget().labels[lang]
                                sortorder = lastname + ', ' + firstname
                                skip_defaultsort = ''
                                if sitelang in authoritylist[3]:
                                    skip_defaultsort = '|{{' + authoritylist[3][sitelang]
                                if not re.search(sort_template[1:] + skip_defaultsort,
                                                 page.text, flags=re.IGNORECASE):
                                    if categorytext:
                                        categorytext += '\n'
                                    categorytext += '{{' + sort_word + sortorder + '}}'
                                    pageupdated += ' ' + sort_word
                                    pywikibot.warning('Add {}{} to {}'
                                                      .format(sort_word, sortorder, sitelang))
                        except:
                            pass    # No firstname, or no lastname

                    # Add Wikipedia category
                    wpcatpage = addcommonscat[4]
                    wpcatnamespace = sitelink.site.namespace(CATEGORYNAMESPACE)
                    wpcatpage_re = wpcatpage.replace('(', r'\(').replace(')', r'\)')
                    if (wpcatpage   # Should exist because of category Wikipedia language sitelink
                            and not re.search(r'\[\[' + wpcatnamespace + ':' + wpcatpage_re +
                                                r'|\[\[Category:' + wpcatpage_re,
                                              page.text, flags=re.IGNORECASE)):
                        if categorytext:
                            categorytext += '\n'
                        categorytext += '[[' + wpcatnamespace + ':' + wpcatpage + ']]'
                        pageupdated += ' [[:{}:{}]]'.format(wpcatnamespace, wpcatpage)
                        pywikibot.warning('Add {}:{} to {}:{}'
                                          .format(wpcatnamespace, wpcatpage, sitelang, sitelink.title))

                    # Save page when updated
                    if pageupdated != transcmt + ' Add':
                        # Insert reference text
                        if inserttext:
                            # Build template list regular expression
                            portal_template = '{{Portal|{{Navbox'
                            for ibox in range(len(portallist)):
                                if sitelang in portallist[ibox]:
                                    portal_template += '|{{' + portallist[ibox][sitelang]

                            for ibox in range(3):
                                if sitelang in authoritylist[ibox]:
                                    portal_template += '|{{' + authoritylist[ibox][sitelang]

                            # Portal template has precedence on first Category
                            navsearch = re.search(portal_template,
                                                  page.text, flags=re.IGNORECASE)

                            # Insert the text at the best location
                            if (refreplace and refreplace.group(0).startswith('<references')
                                    and reftemplate and sitelang not in veto_references):
                                page.text = page.text[:refreplace.start()] + inserttext + page.text[refreplace.end():]
                                inserttext = ''
                            elif refreplace:
                                page.text = page.text[:refreplace.end()] + '\n' + inserttext + page.text[refreplace.end():]
                                inserttext = ''
                            elif navsearch:
                                page.text = page.text[:navsearch.start()] + inserttext + '\n' + page.text[navsearch.start():]
                                inserttext = ''

                        # Now possibly insert text for category, possibly remaining insert text
                        if inserttext and categorytext:
                            inserttext += '\n' + categorytext
                        elif categorytext:
                            inserttext = categorytext

                        if inserttext:
                            # Locate the first Category
                            # https://www.wikidata.org/wiki/Property:P373
                            # https://www.wikidata.org/wiki/Q4167836
                            catsearch = re.search(r'\[\[' + wpcatnamespace +
                                                  r':|\[\[Category:' + sort_template,
                                                  page.text, flags=re.IGNORECASE)
                            if catsearch:
                                page.text = page.text[:catsearch.start()] + inserttext + '\n' + page.text[catsearch.start():]
                            else:
                                # Append the text
                                page.text += '\n' + inserttext

                        # Save page updates
                        # Cosmetic changes should only be done as side-effect of larger update
                        try:
                            if False and sort_word != 'DEFAULTSORT:':
                                page.text = re.sub(r'{{DEFAULTSORT:', '{{' + sort_word, page.text)

                            # Trim trailing spaces
                            page.text = re.sub(r'[ \t\r\f\v]+$', '', page.text, flags=re.MULTILINE)

                            # Remove double spaces
                            page.text = re.sub(r'[.] [ ]+', '. ', page.text)

                            # Remove redundant empty lines
                            page.text = re.sub(r'\n\n+', '\n\n', page.text)

                            page.save(pageupdated)
                            lastwpedit = datetime.now()
                        except Exception as error:  # other exception to be used
                            pywikibot.error('Error processing {}, {}'.format(qnumber, error))

# (20) Error handling
        except KeyboardInterrupt:
            pdb.set_trace()
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 130)

        except pywikibot.exceptions.NoPageError as error:
            pywikibot.error(error)      # Item not found
            status = 'Not found'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.IsRedirectPageError as error:
            pywikibot.error(error)      # Statement target is redirect
            status = 'Warning'
            errcount += 1
            exitstat = max(exitstat, 12)

        except AttributeError as error:
            pywikibot.error(error)      # NoneType error
            status = 'NoneType'
            errcount += 1
            exitstat = max(exitstat, 12)

        except pywikibot.exceptions.UnknownSiteError as error:
            pywikibot.error(error)      # Site error
            pdb.set_trace()
            status = 'BadSite'
            errcount += 1
            exitstat = max(exitstat, 12)
            #raise

        except pywikibot.exceptions.MaxlagTimeoutError as error:    # Attempt error recovery
            pywikibot.error('Error updating {}, {}'.format(qnumber, error))
            status = 'Maxlag'	        # System overloaded; need to wait
            errcount += 1
            exitstat = max(exitstat, 20)
            deltasecs = int((datetime.now() - now).total_seconds())	# Calculate technical error penalty
            if deltasecs >= 30: 	    # Technical error; for transactional errors there is no wait time increase
                errsleep += errwaitfactor * min(maxdelay, deltasecs)
                # Technical errors get additional penalty wait
				# Consecutive technical errors accumulate the wait time, until the first successful transaction
				# We limit the delay to a multitude of maxdelay seconds
            if errsleep > 0:    	    # Allow the servers to catch up; slowdown the transaction rate
                pywikibot.error('{:d} seconds maxlag wait'.format(errsleep))
                time.sleep(errsleep)

        except Exception as error:      # other exception to be used
            pywikibot.error('Error processing {}, {}'.format(qnumber, error))
            pdb.set_trace()
            status = 'Error'	        # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 20)
            if exitfatal:               # Stop on first error
                raise

        """
        The transaction was either executed correctly, or an error occurred.
        Possibly already a system error message was issued.
        We will report the results here, as much as we can, one line per item.
        """

# (21) Get the elapsed time in seconds and the timestamp in string format
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
now = datetime.now()	    # Refresh the timestamp to time the following transaction
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
PSUFFRE = re.compile(r'\s*\(.*\)$')		# Remove trailing () suffix (keep only the base label)
PAGEHEADRE = re.compile(r'(==.*==)')        # Page headers with templates
QSUFFRE = re.compile(r'Q[0-9]+')            # Q-numbers
ROMANRE = re.compile(r'^[a-z .,"()\'åáàâäāæǣçéèêëėíìîïıńñŋóòôöœøřśßúùûüýÿĳ-]{2,}$', flags=re.IGNORECASE)     # Roman alphabet
SHORTDESCRE = re.compile(r'{{Short description\|(.*)}}', flags=re.IGNORECASE)
WDINFOBOXRE = re.compile(r'{{Wikidata infobox|{{Category|{{Cat disambig', flags=re.IGNORECASE)		    # Wikidata infobox

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

# Add additional languages from parameters
while sys.argv:
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

# Build veto languages ID
##main_languages_id = [lang_qnumbers[lang] for lang in main_languages]
for lang in veto_languages:
    if lang in lang_qnumbers:   # comment to check completeness
        veto_languages_id.add(lang_qnumbers[lang])

# Connect to databases
site = pywikibot.Site('commons')
site.login()            # Must login
repo = site.data_repository()

# Print preferences
pywikibot.log('Main languages:\t{} {}'.format(mainlang, main_languages))
pywikibot.log('Maximum delay:\t{:d} s'.format(maxdelay))
pywikibot.log('Use labels:\t{}'.format(uselabels))
pywikibot.log('Instance descriptions:\t{}'.format(repldesc))
pywikibot.log('Force copy:\t{}'.format(forcecopy))
pywikibot.log('Verbose mode:\t{}'.format(verbose))
pywikibot.log('Exit on fatal error:\t{}'.format(exitfatal))
pywikibot.log('Error wait factor:\t{:d}'.format(errwaitfactor))

# Setup language lookup tables in the sequence of a Wikipedia page
pywikibot.info('Loading templates')
new_wikis = set()
valid_wikis = set()

# Get Wikimedia labels in the local language
infobox_localname = get_item_label_dict('Q15515987')    # Infobox

# Load list of infoboxes automatically (first 4 must be in strict sequence)
dictnr = 0
infoboxlist = {}
for item_dict in sitelink_dict_list:
    infoboxlist[dictnr] = get_wikipedia_sitelink_template_dict(item_dict)
    dictnr += 1

# Manual corrections
# Prevent to generate a duplicate infobox
# https://id.wikipedia.org/w/index.php?title=Institut_Pendidikan_Politik_Nasional&diff=25083987&oldid=25083986
del(infoboxlist[2]['idwiki'])

# Swap and merge Wikidata boxes (index 0 and 3)
for sitelang in infoboxlist[3]:
    if sitelang in infoboxlist[0]:
        swapinfobox = infoboxlist[0][sitelang]
        infoboxlist[0][sitelang] = infoboxlist[3][sitelang]
        infoboxlist[3][sitelang] = swapinfobox
    else:
        infoboxlist[0][sitelang] = infoboxlist[3][sitelang]
        ###del(infoboxlist[3][sitelang])    # RuntimeError: dictionary changed size during iteration

# Disallow empty boxes (where no Wikidata statements are implemented)
infoboxlist[dictnr] = {}
for sitelang in veto_infobox:
    infoboxlist[dictnr][sitelang] = infoboxlist[0][sitelang]
    del(infoboxlist[0][sitelang])

# Manual exclusions
dictnr += 1
infoboxlist[dictnr] = {
    'arzwiki': 'صندوق معلومات كاتب',
    'astwiki': 'Persona',
    'azwiki': 'Rəqs',               # No Wikidata
    'bswiki': 'Infokutija',         # Multiple templates
    'euwiki': 'Biografia',          # Multiple templates
    'fiwiki': 'Kirjailija',
    'fywiki': 'Artyst',             # https://fy.wikipedia.org/w/index.php?title=Kees_van_Kooten&diff=1114402&oldid=1114401&diffmode=source
    'ruwiki': 'Однофамильцы',       # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=prev&oldid=129491499&diffmode=source
    'srwiki': 'Infokutija',         # Multiple templates
    'ukwiki': 'Unibox',             # https://uk.wikipedia.org/w/index.php?title=Сюанський_папір&diff=39931612&oldid=37227693
    'uzwiki': 'Shaxsiyat',          # https://uz.wikipedia.org/w/index.php?title=Peter_Thiel&diff=3990073&oldid=3990069
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

# References
referencelist = {}
referencelist[0] = get_wikipedia_sitelink_template_dict('Q5462890')       # Replace <references /> by References, 32 s
referencelist[1] = get_wikipedia_sitelink_template_dict('Q10991260')      # Appendix

for sitelang in referencelist[1]:
    if sitelang in referencelist[0]:
        swapinfobox = referencelist[0][sitelang]
        referencelist[0][sitelang] = referencelist[1][sitelang]
        referencelist[1][sitelang] = swapinfobox
    else:
        referencelist[0][sitelang] = referencelist[1][sitelang]
        ###del(referencelist[1][sitelang])    # RuntimeError: dictionary changed size during iteration

# List of authority control
authoritylist = {}

# Specific index 0
# Index 0..2 is used for searching navigation box
authoritylist[0] = get_wikipedia_sitelink_template_dict('Q3907614')       # Add Authority control, 1s

# Specific index 1
# No Commonscat for Interproject links
authoritylist[1] = get_wikipedia_sitelink_template_dict('Q5830969')       # Interproject template, 4 s

# Specific index 2
# No Commonscat
authoritylist[2] = {            # Manual exclusions
    'astwiki': 'NF',
    'eswiki': 'Control de autoridades',
    'euwiki': 'Bizialdia',
    'lvwiki': 'Sisterlinks-inline',           # Q26098003
    'mdfwiki': 'Ломань',        # Q6249834
}

# Specific index 3
# Lifetime template; skip adding DEFAULTSORT
authoritylist[3] = get_wikipedia_sitelink_template_dict('Q6171224')     # Livetime, 1 s

# Manual exclusions
authoritylist[4] = {
    'arzwiki': 'ضبط استنادي',   # alias for [0]
    'bewiki': 'Бібліяінфармацыя',
    'frwiki': 'Bases',          # Liens = Autorité + Bases
    'ruwiki': 'BC',             # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=129492269&oldid=129491434&diffmode=source
    'ukwiki': 'Нормативний контроль',   # https://uk.wikipedia.org/w/index.php?title=Пітер_Тіль&diff=41204517&oldid=41204504
}

# Exeptional manual exclusions
authoritylist[5] = {}
authoritylist[5]['frwiki'] = authoritylist[0]['frwiki']     # Autorité
authoritylist[0]['frwiki'] = 'Liens'    # Enforce frwiki

# Get the Commonscat template names
commonscatlist = {}
commonscatlist[0] = get_wikipedia_sitelink_template_dict('Q48029')      # Commonscat, 7 s
commonscatlist[1] = get_wikipedia_sitelink_template_dict('Q5830425')    # Commons category-inline

# Manual exclusions
commonscatlist[2] = {
    'arzwiki': 'لينكات مشاريع شقيقه',   # https://arz.wikipedia.org/w/index.php?title=روجر_رافيل&diff=8088053&oldid=8088052&diffmode=source
    'astwiki': 'Enllaces',
    'bewiki': 'Пісьменнік',
    'bgwiki': 'Личност',            # Q6249834 Personality infobox has a builtin Commonscat
    'hywiki': 'Տեղեկաքարտ Խաչքար',  # Q26042874
    'itwiki': 'Interprogetto',      # https://it.wikipedia.org/w/index.php?title=Palazzo_dei_Principi-Vescovi_di_Liegi&diff=132888315&oldid=132888272&diffmode=source
    'nowiki': 'Offisielle lenker',  # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot
    'ruwiki': 'BC',                 # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=129492269&oldid=129491434&diffmode=source
    'ukwiki': 'універсальна картка',
}

# Other manual exclusions
commonscatlist[3] = {
    'hywiki': 'Տեղեկաքարտ Խաչքար',  # Q26042874
    'nowiki': 'Offisielt nettsted', # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot (redirect)
}

# Get the portal template list
portallist = {}
portallist[0] = get_wikipedia_sitelink_template_dict('Q5153')       # Portal, 1 s
portallist[1] = get_wikipedia_sitelink_template_dict('Q5030944')    # Navbox, 2 s

# Manual inclusions
portallist[2] = {
    'nlwiki':'Portaal',
}

portallist[3] = {
    'nlwiki':'Navigatie',
}

pywikibot.info('Wikipedia templates loaded')

# Veto sites
for sitelang in veto_sitelinks:
    if sitelang in valid_wikis:
        valid_wikis.remove(sitelang)

prevnow = now	        	# Transaction status reporting
now = datetime.now()	    # Refresh the timestamp to time the following transaction
totsecs = int((now - prevnow).total_seconds())	# Elapsed time for this transaction
pywikibot.info('{:d} seconds to initialise'.format(totsecs))
lastwpedit = now + timedelta(seconds=-15)
commonscatqueue = []        # FIFO list

# Get unique list of item numbers
inputfile = sys.stdin.read()
item_list = sorted(set(QSUFFRE.findall(inputfile)))
# Execute all items
wd_proc_all_items()

while repeatmode:
    pywikibot.info('\nEnd of list')
    inputfile = sys.stdin.read()
    item_list = sorted(set(QSUFFRE.findall(inputfile)))
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
