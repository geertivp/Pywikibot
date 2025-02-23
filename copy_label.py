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
* Add a first image (based on P18 or similar properties in Wikidata).
* Add Appendix (references)
* Add Wikipedia Authority control templates for humans
* Add DEFAULTSORT for humans (lastname, firstname)
* Amend Wikipedia pages for all languages with Commonscat templates
* Add Wikipedia categories

Parameters:

    P1: source language ISO code (default: LANGUAGE, LC_ALL, LANG environment variables)
    P2...: additional language codes for site-link check and label replication
        Take care to only include Western (Roman) languages.

    stdin: list of Q-numbers to process (extracted via regular expression)
        Duplicate and incompatible instances or subclases are ignored.

Flags:

    -c	Force copy (bypass instance validation restriction)
    -h	Show help
    -i  Copy instance labels to item descriptions
    -l	Disable language labels update
    -p 	Proceed after error
    -q	Quiet mode
    -s  Single modus
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

    Inconsitent data can lead to (other bot generated) inconsistent updates.

        We should do the maximum to detect and report such inconsistencies.

Debugging:

    https://docs.python.org/3/library/pdb.html
    https://www.geeksforgeeks.org/python-debugger-python-pdb/

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
from pywikibot.data import api

# Global variables
modnm = 'Pywikibot copy_label'      # Module name (using the Pywikibot package)
pgmid = '2025-01-19 (gvp)'	        # Program ID and version
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
newfunctions = False    # New functions
repeatmode = True       # Repeat mode
repldesc = False        # Replicate instance description labels
uselabels = False       # Use the language labels (disable with -l)
                        # Labels are no longer duplicated by default; use 'mul' language instead
                        # https://phabricator.wikimedia.org/T303677

# Technical configuration flags
errorstat = True        # Show error statistics (disable with -e)
exitfatal = False	    # Exit on fatal error (can be disabled with -p; please take care)
shell = True		    # Shell available (command line parameters are available; automatically overruled by PAWS)

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
transcmt = '#pwb Copy label'

# Language settings
ENLANG = 'en'
MULANG = 'mul'
MAINLANG = 'en:mul'     # mul can have non-Romain alphabeths; EN was tradional default value
enlang_list = [ENLANG, 'en-gb', 'en-us', 'en-ca']

PREFERRED_RANK = 'preferred'
NORMAL_RANK = 'normal'

# Namespaces
# https://www.mediawiki.org/wiki/Help:Namespaces
# https://nl.wikipedia.org.org/w/api.php?action=query&meta=siteinfo&siprop=namespaces&formatversion=2
MAINNAMESPACE = 0
FILENAMESPACE = 6
TEMPLATENAMESPACE = 10
CATEGORYNAMESPACE = 14

# Properties
VIDEOPROP = 'P10'
ROADMAPPROP = 'P15'
COUNTRYPROP = 'P17'
IMAGEPROP = 'P18'
FATHERPROP = 'P22'
MOTHERPROP = 'P25'
MARIAGEPARTNERPROP = 'P26'
NATIONALITYPROP = 'P27'
INSTANCEPROP = 'P31'
AMBTPROP = 'P39'
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
PREVIOUSPROP = 'P155'
NEXTPROP = 'P156'
CEOPROP = 'P169'
MAKERPROP = 'P170'
DEPICTSPROP = 'P180'
PROMOTORPROP = 'P184'
PROMOVENDUSPROP = 'P185'
LOCATORMAPPROP = 'P242'
SUBCLASSPROP = 'P279'
FOREIGNSCRIPTPROP = 'P282'
MAINSUBJECTCATPROP = 'P301'
PARTOFPROP = 'P361'
MEDIALANGPROP = 'P364'
COMMONSCATPROP = 'P373'
EDITIONLANGPROP = 'P407'
WIKIMEDIALANGCDPROP = 'P424'
PARTNERPROP = 'P451'
ALMOSTEQTOPROP = 'P460'
INVERSEPROP = 'P461'
MEMBEROFPROP = 'P463'
CHAIRPROP = 'P488'
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
QUALIFYFROMPROP = 'P642'            ## https://www.wikidata.org/wiki/Wikidata:WikiProject_Deprecate_P642
ORGANISEDBYPROP = 'P664'
OPERATINGDATEPROP = 'P729'
SERVICEENDDATEPROP = 'P730'
LASTNAMEPROP = 'P734'
FIRSTNAMEPROP = 'P735'
PSEUDONYMPROP = 'P742'
RELEVANTWORKPROP = 'P800'
##SUBJECTOFPROP = 'P'               ## Does not exist
SUBJECTOFSTATEMENTPROP = 'P805'     ## Wrong inverse of MAINSUBJECTOFWORKPROP
MAINCATEGORYPROP = 'P910'
MAINSUBJECTOFWORKPROP = 'P921'      ## Wrong inverse of SUBJECTOFSTATEMENTPROP
VOYAGEBANPROP = 'P948'
COMMONSGALLARYPROP = 'P935'
VOICERECORDPROP = 'P990'
SCANPROP = 'P996'
JURISDICTIONPROP = 'P1001'
DIRECTORPROP = 'P1037'
CAMERALOCATIONPROP = 'P1259'
EARLYTIMEPROP = 'P1319'
LATETIMEPROP = 'P1326'
BUSINESSPARTNERPROP = 'P1327'
REPLACESPROP = 'P1365'
REPLACEDBYPROP = 'P1366'
LANGKNOWPROP = 'P1412'
MAINSUBJECTTEMPLATEPROP = 'P1423'
GRAVEPROP = 'P1442'
NICKNAMEPROP = 'P1449'
COMMONSCREATORPROP = 'P1472'
EDITIONTITLEPROP = 'P1476'
BIRTHNAMEPROP = 'P1477'
USEDBYPROP = 'P1535'
ITEMCHARPROP = 'P1552'                  ## See also P1963
NATIVENAMEPROP = 'P1559'
COMMONSINSTPROP = 'P1612'
MAINSUBJECTPROP = 'P1629'
WIKIDATAPROP = 'P1687'
ORIGNAMELABELPROP = 'P1705'
CATEGORYRELTDTOLISTPROP = 'P1753'
LISTRELTDTOCATEGORYPROP = 'P1754'
PLACENAMEPROP = 'P1766'
ARTISTNAMEPROP = 'P1787'
PLAQUEPROP = 'P1801'
HASPROPERTYPROP = 'P1830'
NOTEQTOPROP = 'P1889'
INSTANCEPROPLISTPROP = 'P1963'          ## See also P1552
USESPROP = 'P2283'
MARIEDNAMEPROP = 'P2562'
COLLAGEPROP = 'P2716'
ICONPROP = 'P2910'
WORKINGLANGPROP = 'P2936'
PARTITUREPROP = 'P3030'
FLOORPLANPROP = 'P3311'
KEYRELATIONPROP = 'P3342'
SIBLINGPROP = 'P3373'
NIGHTVIEWPROP = 'P3451'
OBJECTROLEPROP = 'P3831'
PANORAMAPROP = 'P4640'
WINTERVIEWPROP = 'P5252'
DIAGRAMPROP = 'P5555'
INTERIORPROP = 'P5775'
RELTDIMAGEPROP = 'P6802'
VERSOPROP = 'P7417'
RECTOPROP = 'P7418'
FRAMEWORKPROP = 'P7420'
DEPICTFORMATPROP = 'P7984'
VIEWFROMPROP = 'P8517'
AERIALVIEWPROP = 'P8592'
PARENTPROP = 'P8810'
FAVICONPROP = 'P8972'
OBJECTLOCATIONPROP = 'P9149'
COLORWORKPROP = 'P10093'
REPRESENTATIONTYPEPROP = 'P12692'

# Instances
HUMANINSTANCE = {'Q5', 'Q15632617'}     # (fictive) human
ESPERANTOLANGINSTANCE = 'Q143'
PERSONPORTRAITINSTANCE = 'Q134307'
CORRESPONDENTINSTANCE = 'Q3589290'
WIKIMEDIACATINSTANCE = 'Q4167836'
WIKIMEDIAPROJECTINSTANCE = 'Q14204246'

# Language independent
alternative_person_names_props = [ARTISTNAMEPROP, PSEUDONYMPROP]

# Allows to extract GEO coordinates
location_target = [
    ('Camera location', CAMERALOCATIONPROP),    # Geolocation of camera view point
    ('Object location', OBJECTLOCATIONPROP),    # Geolocation of object (precedence)
]

# Time related properties
time_props = {
    TIMEPROP,
    STARTDATEPROP, ENDDATEPROP,
    EARLYTIMEPROP, LATETIMEPROP,
}

# List of media properties (audio, image, video)
# To generate compound SDC depict statements
# for indirect media file references
# using 'of' qualifier
depict_item_type = {
    AERIALVIEWPROP: 'Q56240104',
    COATOFARMSPROP: 'Q14659',
    COLLAGEPROP: 'Q170593',     #'Q22669857',
    COLORWORKPROP: 'Q109592922',
    FLOORPLANPROP: 'Q18965',
    DIAGRAMPROP: 'Q959962',
    FAVICONPROP: 'Q2130',
    FLAGPROP: 'Q14660',
    FRAMEWORKPROP: '',          # xxx
    GRAVEPROP: 'Q173387',
    ICONPROP: 'Q138754',
    IMAGEPROP: '',              # Has to be handled in software: 'Q592312', 'Q125191' Q134307
    INTERIORPROP: 'Q2998430',
    LOCATORMAPPROP: 'Q6664848',
    LOGOPROP: 'Q1886349',
    ROADMAPPROP: 'Q2298569',
    NIGHTVIEWPROP: 'Q28333482',
    PANORAMAPROP: 'Q658252',
    PARTITUREPROP: 'Q187947',
    SCANPROP: '',                # xxx
    PLACENAMEPROP: 'Q55498668',
    PLAQUEPROP: 'Q721747',
    ##RECTOPROP: 'Q9305022',
    RELTDIMAGEPROP: 'Q131816513',
    SIGNATUREPROP: 'Q188675',
    ##VERSOPROP: 'Q9368452',
    VIDEOPROP: 'Q98069877',
    VIEWFROMPROP: 'Q2075301',
    VOICERECORDPROP: 'Q53702817',
    VOYAGEBANPROP: 'Q22920576',
    WINTERVIEWPROP: 'Q54819662',
    'P10544': 'Q1519903',       # uithangbord
    'P11101': 'Q1979154',       # model
    'P11702': 'Q6031215',       # informatiepaneel
    'P1543': 'Q168346',         # monogram
    'P158': 'Q162919',          # zegel
    'P1846': 'Q97378230',       # verspreidingsgebied
    'P2713': 'Q12139782',       # dwarsdoorsnede
    'P3383': 'Q374821',         # filmposter
    'P367': 'Q645745',          # astronomisch symbool
    'P443': 'Q184377',          # uitspraak
    'P5962': 'Q1668447',        # zeilteken
    'P6718': 'Q193977',         # videoclip
    'P7415': 'Q80071',          # symbool
    'P7457': 'Q1373131',        # handtekening van maker
    'P8224': 'Q2196961',        # molecuulmodel
    'P8667': 'Q96279156',       # tweelingstadbord
    'P8766': 'Q34941835',       # rang insigne
    'P9906': 'Q1640824',        # inscriptie
}

# List of conflicting properties
conflicting_statement = {
    ALMOSTEQTOPROP: NOTEQTOPROP,
    EDITIONLANGPROP: MEDIALANGPROP,
    # others to be added
}

# Define mandatory relationships
# Get list via P1696 (could we possibly generate this dictionary dynamically?)
# https://www.wikidata.org/wiki/Property:P1696 (inverse property)
# https://www.wikidata.org/wiki/Property:P7087 (inverse label)
mandatory_relation = {
    # Symmetric
    BUSINESSPARTNERPROP: BUSINESSPARTNERPROP,
    BORDERPEERPROP: BORDERPEERPROP,
    ALMOSTEQTOPROP: ALMOSTEQTOPROP,
    MARIAGEPARTNERPROP: MARIAGEPARTNERPROP,
    NOTEQTOPROP: NOTEQTOPROP,
    PARTNERPROP: PARTNERPROP,
    SIBLINGPROP: SIBLINGPROP,
    INVERSEPROP: INVERSEPROP,

    # Inverse bidirectional
    CATEGORYRELTDTOLISTPROP: LISTRELTDTOCATEGORYPROP,
    CONTAINSPROP: PARTOFPROP,       # exclude MEMBEROFPROP
    HASPROPERTYPROP: PROPERTYOFPROP,
    MAINCATEGORYPROP: MAINSUBJECTCATPROP,
    ## MAINSUBJECTOFWORKPROP: SUBJECTOFPROP,
    ##MAKERPROP: RELEVANTWORKPROP,  ## See also RELTDIMAGEPROP + ambiguity https://www.wikidata.org/wiki/Property:P800#P1629
    MANAGEITEMPROP: OPERATORPROP,
    NEXTPROP: PREVIOUSPROP,
    ##ORGANISEDBYPROP: ,    # has inverse label
    REPLACESPROP: REPLACEDBYPROP,
    PROMOTORPROP: PROMOVENDUSPROP,
    ##RELTDIMAGEPROP:
    USESPROP: USEDBYPROP,

    # Inverse unidirectional (mind the 1:M relationship)
    FATHERPROP: CHILDPROP,
    MOTHERPROP: CHILDPROP,
    PARENTPROP: CHILDPROP,
    WIKIDATAPROP: MAINSUBJECTPROP,
    # others to be added
}

# Exceptions: statements that are not bidirectional
# Example: Beatles contains John Lennon, and John Lennon is member of The Beatles (instead of part of)
likewise_relation = {
    CONTAINSPROP: {MEMBEROFPROP},
}

# List of missing statements
missing_statement = {
    COMMONSCREATORPROP: COMMONSCATPROP,     # Commons creator requires commonscat
    COMMONSINSTPROP: COMMONSCATPROP,        # Commons institution requires commonscat
    # others to be added
}

# Add labels for all those (Roman) languages
# Do not add Central European languages like cs, hu, pl, sk, etc. because of special language rules
# Not Hungarian, Czech, Polish, Slovak, etc
# We should have kind of a fallback mechanism to avoid duplicating labels
# Languages with - should have special treatment with + 'wiki'
all_languages = {'af', 'an', 'ast', 'ca', 'cy', 'da', 'de', 'en', 'es', 'fr', 'ga', 'gl', 'io', 'it', 'jut', 'nb', 'nl', 'nn', 'pms', 'pt', 'sc', 'sco', 'sje', 'sl', 'sq', 'sv'}

# List of artificial languages
artificial_languages = {ESPERANTOLANGINSTANCE}

# Allow to copy the description from the instance
copydesc_item_list = {
    WIKIMEDIACATINSTANCE,       # https://www.wikidata.org/wiki/Q121065933
    WIKIMEDIAPROJECTINSTANCE,   # https://www.wikidata.org/wiki/Q14734922
}

# All types of human names:
# human, fictional human, personage,
# last name, male first name, female first name, neutral first name, affixed family name, family
human_type_list = {'Q5', 'Q15632617', 'Q95074',
    'Q101352', 'Q12308941', 'Q11879590', 'Q3409032', 'Q66480858', 'Q8436'}

# Specific sequence to be aligned with sitelink_dict_list
instance_types_by_category = [
    HUMANINSTANCE,          # Human (is list!)
    {'Q185187', 'Q38720'},  # Mills
    # others to be added
]

# Filter the extension of nat_languages
lang_type_list = {'Q1288568', 'Q33742', 'Q34770'}        # levende taal, natuurlijke taal, taal

# Lookup table for language qnumbers (static list)
# This default list is updated via get_dict_using_statement_value
# Search items for statement P31:Q1288568 (or P31:Q33742?)
lang_qnumbers = {'aeb': 'Q56240', 'aeb-arab': 'Q64362981', 'aeb-latn': 'Q64362982', 'ar': 'Q13955', 'arc': 'Q28602', 'arq': 'Q56499', 'ary': 'Q56426', 'azb': 'Q3449805', 'arz': 'Q29919', 'bcc': 'Q12634001', 'be': 'Q9091', 'be-tarask': 'Q8937989', 'bg': 'Q7918', 'bn': 'Q9610', 'bgn': 'Q12645561', 'bqi': 'Q257829', 'bs': 'Q9303', 'cs': 'Q9056', 'ckb': 'Q36811', 'cv': 'Q33348', 'da': 'Q9035', 'de': 'Q188', 'dv': 'Q32656', 'el': 'Q9129', 'en': 'Q1860', 'es': 'Q1321', 'et': 'Q9072', 'fa': 'Q9168', 'fi': 'Q1412', 'fr': 'Q150', 'gan': 'Q33475', 'gan-hans': 'Q64427344', 'gan-hant': 'Q64427346', 'gl': 'Q9307', 'glk': 'Q33657', 'gu': 'Q5137', 'he': 'Q9288', 'hi': 'Q1568', 'hu': 'Q9067', 'hy': 'Q8785', 'it': 'Q652', 'ja': 'Q5287', 'ka': 'Q8108', 'khw': 'Q938216', 'kk': 'Q9252', 'kk-arab': 'Q90681452', 'kk-cn': 'Q64427349', 'kk-cyrl': 'Q90681280', 'kk-kz': 'Q64427350', 'kk-latn': 'Q64362993', 'kk-tr': 'Q64427352', 'ko': 'Q9176', 'ko-kp': 'Q18784', 'ks': 'Q33552', 'ks-arab': 'Q64362994', 'ks-deva': 'Q64362995', 'ku': 'Q36368', 'ku-arab': 'Q3678406', 'ku-latn': 'Q64362997', 'lki': 'Q56483', 'lrc': 'Q19933293', 'lzh': 'Q37041', 'luz': 'Q12952748', 'mhr': 'Q12952748', 'mk': 'Q9296', 'ml': 'Q36236', 'mn': 'Q9246', 'mzn': 'Q13356', 'ne': 'Q33823', 'new': 'Q33979', 'nl': 'Q7411', 'no': 'Q9043', 'or': 'Q33810', 'os': 'Q33968', 'ota': 'Q36730', 'pl': 'Q809', 'pnb': 'Q1389492', 'ps': 'Q58680', 'pt': 'Q5146', 'ro': 'Q7913', 'ru': 'Q7737', 'rue': 'Q26245', 'sd': 'Q33997', 'sdh': 'Q1496597', 'sh': 'Q9301', 'sk': 'Q9058', 'sl': 'Q9063', 'sr': 'Q9299', 'sr-ec': 'Q21161942', 'sv': 'Q9027', 'ta': 'Q5885', 'te': 'Q8097', 'tg': 'Q9260', 'tg-cyrl': 'Q64363004', 'tg-latn': 'Q64363005', 'th': 'Q9217', 'ug': 'Q13263', 'ug-arab': 'Q2374532', 'ug-latn': 'Q986283', 'uk': 'Q8798', 'ur': 'Q1617', 'vep': 'Q32747', 'vi': 'Q9199', 'yi': 'Q8641', 'yue': 'Q7033959', 'zh': 'Q7850', 'zh-cn': 'Q24841726', 'zh-hant': 'Q18130932', 'zh-hans': 'Q13414913', 'zh-hk': 'Q100148307', 'zh-mo': 'Q64427357', 'zh-my': 'Q13646143', 'zh-sg': 'Q1048980', 'zh-tw': 'Q4380827', 'trv': 'Q716686', 'dag': 'Q32238', 'tay': 'Q715766', 'tw': 'Q36850', 'ami': 'Q35132', 'rkt': 'Q3241618', 'ctg': 'Q33173', 'nb': 'Q25167', 'hno': 'Q382273', 'guw': 'Q3111668', 'moe': 'Q13351', 'an': 'Q8765', 'xsy': 'Q716695', 'sma': 'Q13293', 'pwn': 'Q715755', 'gsw-fr': 'Q8786', 'ff': 'Q33454', 'nn': 'Q25164', 'ig': 'Q33578', 'agq': 'Q34737', 'ilo': 'Q35936', 'bnn': 'Q56505', 'ha': 'Q56475', 'als': 'Q387066', 'atj': 'Q56590', 'yo': 'Q34311', 'wa': 'Q34219', 'hsb': 'Q13248', 'sg': 'Q33954', 'se': 'Q33947', 'lb': 'Q9051', 'br': 'Q12107', 'bzs': 'Q3436689', 'so': 'Q13275', 'smj': 'Q56322', 'fon': 'Q33291', 'ak': 'Q28026', 'hil': 'Q35978', 'lkt': 'Q33537', 'si': 'Q13267', 'pdt': 'Q1751432', 'pyu': 'Q716690', 'cy': 'Q9309', 'ssf': 'Q676492', 'as': 'Q29401', 'lt': 'Q9083', 'mr': 'Q1571', 'ast': 'Q29507', 'ce': 'Q33350', 'hyw': 'Q180945', 'ady': 'Q27776', 'kn': 'Q33673', 'ht': 'Q33491', 'tl': 'Q34057', 'sat': 'Q33965', 'hr': 'Q6654', 'lv': 'Q9078', 'ceb': 'Q33239', 'szy': 'Q718269', 'ms': 'Q9237', 'kab': 'Q35853', 'nap': 'Q33845', 'gaa': 'Q33287', 'eu': 'Q8752', 'fy': 'Q27175', 'jv': 'Q33549', 'scn': 'Q33973', 'id': 'Q9240', 'mai': 'Q36109', 'sq': 'Q8748', 'vec': 'Q32724', 'ki': 'Q33587', 'is': 'Q294', 'sw': 'Q7838', 'ban': 'Q33070', 'mt': 'Q9166', 'ga': 'Q9142', 'vls': 'Q100103', 'oc': 'Q14185', 'pap': 'Q33856', 'bar': 'Q29540', 'sco': 'Q14549', 'ba': 'Q13389', 'nan': 'Q36495', 'tt': 'Q25285', 'mni': 'Q33868', 'loz': 'Q33628', 'uz': 'Q9264', 'cbk-zam': 'Q33281', 'af': 'Q14196', 'hoc': 'Q33270', 'pcd': 'Q34024', 'az': 'Q9292', 'kv': 'Q36126', 'la': 'Q397', 'pag': 'Q33879', 'ky': 'Q9255', 'wo': 'Q34257', 'lg': 'Q33368', 'za': 'Q13216', 'bxr': 'Q33120', 'mi': 'Q36451', 'am': 'Q28244', 'rif': 'Q34174', 'wym': 'Q56485', 'qu': 'Q5218', 'zu': 'Q10179', 'tr': 'Q256', 'ca': 'Q7026', 'bo': 'Q34271', 'mnc': 'Q33638', 'dsb': 'Q13286', 'st': 'Q34340', 'skr': 'Q33902', 'bfi': 'Q33000', 'cr': 'Q33390', 'frr': 'Q28224', 'udm': 'Q13238', 'nds': 'Q25433', 'urh': 'Q36663', 'ltg': 'Q36212', 'li': 'Q102172', 'km': 'Q9205', 'xh': 'Q13218', 'bcl': 'Q33284', 'wls': 'Q36979', 'rw': 'Q33573', 'tn': 'Q34137', 'shi': 'Q34152', 'fo': 'Q25258', 'myv': 'Q29952', 'tu': 'Q56240', 'yav': 'Q12953315', 'kum': 'Q36209', 'cho': 'Q32979', 'tk': 'Q9267', 'ext': 'Q30007', 'sms': 'Q13271', 'iu': 'Q29921', 'rm': 'Q13199', 'rmy': 'Q13201', 'sei': 'Q36583', 'ase': 'Q14759', 'ksh': 'Q32145', 'pa': 'Q58635', 'gd': 'Q9314', 'ydg': 'Q34179', 'bm': 'Q33243', 'krj': 'Q33720', 'kj': 'Q1405077', 'ee': 'Q30005', 'eo': 'Q143', 'vro': 'Q32762', 'my': 'Q9228', 've': 'Q32704', 'dua': 'Q33013', 'mh': 'Q36280', 'sah': 'Q34299', 'co': 'Q33111', 'mg': 'Q7930', 'chr': 'Q33388', 'lus': 'Q36147', 'zea': 'Q237409', 'mus': 'Q523014', 'szl': 'Q30319', 'yap': 'Q34029', 'lij': 'Q36106', 'kl': 'Q25355', 'mic': 'Q13321', 'efi': 'Q35377', 'shy': 'Q33274', 'sc': 'Q33976', 'dty': 'Q18415595', 'lmo': 'Q33754', 'ln': 'Q36217', 'inh': 'Q33509', 'bfq': 'Q33205', 'wal': 'Q36943', 'su': 'Q34002', 'war': 'Q34279', 'xmf': 'Q13359', 'srq': 'Q3027953', 'umu': 'Q56547', 'kbd': 'Q33522', 'diq': 'Q10199', 'min': 'Q13324', 'uun': 'Q36435', 'yoi': 'Q34243', 'srn': 'Q33989', 'brx': 'Q33223', 'tsg': 'Q34142', 'csb': 'Q33690', 'nrf-gg': 'Q56428', 'ng': 'Q33900', 'tum': 'Q34138', 'kea': 'Q35963', 'kjh': 'Q33575', 'krl': 'Q33557', 'aoc': 'Q10729616', 'rcf': 'Q13198', 'kcg': 'Q3912765', 'fkv': 'Q165795', 'hak': 'Q33375', 'ccp': 'Q32952', 'nso': 'Q33890', 'kw': 'Q25289', 'pis': 'Q36699', 'lad': 'Q36196', 'quc': 'Q36494', 'fit': 'Q13357', 'cps': 'Q2937525', 'yai': 'Q34247', 'ik': 'Q27183', 'bh': 'Q33268', 'ab': 'Q5111', 'kbp': 'Q35475', 'sli': 'Q152965', 'fur': 'Q33441', 'mwl': 'Q13330', 'gv': 'Q12175', 'fa-af': 'Q178440', 'rwr': 'Q65455884', 'mo': 'Q36392', 'wen': 'Q25442', 'ovd': 'Q254950', 'dz': 'Q33081', 'fj': 'Q33295', 'nv': 'Q13310', 'sjd': 'Q33656', 'ts': 'Q34327', 'lzz': 'Q1160372', 'dru': 'Q49232', 'awa': 'Q29579', 'pms': 'Q15085', 'akz': 'Q1815020', 'ch': 'Q33262', 'bsa': 'Q56648', 'ay': 'Q4627', 'tly': 'Q34318', 'haw': 'Q33569', 'alt': 'Q1991779', 'sjm': 'Q3287253', 'ryu': 'Q34233', 'bal': 'Q33049', 'bla': 'Q33060', 'krx': 'Q35704', 'din': 'Q56466', 'tcy': 'Q34251', 'kjg': 'Q33335', 'anp': 'Q28378', 'yum': 'Q3573199', 'lag': 'Q584983', 'mfe': 'Q33661', 'tsk': 'Q11159532', 'oj': 'Q33875', 'bss': 'Q34806', 'chy': 'Q33265', 'kr': 'Q36094', 'hz': 'Q33315', 'ses': 'Q35655', 'olo': 'Q36584', 'acm': 'Q56232', 'lex': 'Q6695015', 'mis-x-Q8047534': 'Q8047534', 'lbe': 'Q36206', 'nui': 'Q36459', 'liv': 'Q33698', 'kut': 'Q33434', 'kbg': 'Q12952626', 'lo': 'Q9211', 'tsu': 'Q716681', 'aa': 'Q27811', 'lvk': 'Q770547', 'egl': 'Q1057898', 'av': 'Q29561', 'akl': 'Q8773', 'tyv': 'Q34119', 'rn': 'Q33583', 'bug': 'Q33190', 'frp': 'Q15087', 'wbl': 'Q34208', 'pjt': 'Q2982063', 'smn': 'Q33462', 'rup': 'Q29316', 'sid': 'Q33786', 'ty': 'Q34128', 'ny': 'Q33273', 'fuf': 'Q3915357', 'arn': 'Q33730', 'na': 'Q13307', 'mdf': 'Q13343', 'yec': 'Q1365342', 'crh': 'Q33357', 'kha': 'Q33584', 'gil': 'Q30898', 'gn': 'Q35876', 'abq': 'Q27567', 'om': 'Q33864', 'cak': 'Q35115', 'shn': 'Q56482', 'ckv': 'Q716627', 'sn': 'Q34004', 'hai': 'Q33303', 'ckt': 'Q33170', 'ti': 'Q34124', 'tvl': 'Q34055', 'nsk': 'Q1704302', 'bzg': 'Q716615', 'sm': 'Q34011', 'gag': 'Q33457', 'tvn': 'Q7689158', 'zun': 'Q10188', 'adx': 'Q56509', 'ii': 'Q34235', 'ttm': 'Q20822', 'pko': 'Q36323', 'nqo': 'Q18546266', 'cgc': 'Q6346422', 'kri': 'Q35744', 'mnw': 'Q13349', 'yrk': 'Q36452', 'sth': 'Q36705', 'tce': 'Q31091048', 'lld': 'Q36202', 'khg': 'Q56601', 'krc': 'Q33714', 'mwv': 'Q13365', 'nog': 'Q33871', 'guc': 'Q891085', 'pfl': 'Q23014', 'tru': 'Q34040', 'ie': 'Q35850', 'io': 'Q35224',
'ace': 'Q27683',
'bew': 'Q33014',
'bho': 'Q33268',
'bjn': 'Q33151',
'btm': 'Q2891049',
'dga': 'Q3044307',
'dtp': 'Q85970302',
'kg': 'Q33702',
'jbo': 'Q36350',
'map-bms': 'Q33219',
'nds-nl': 'Q516137',
'eml': 'Q242648',
'igl': 'Q35513',
'gor': 'Q56358',
'gsw': 'Q8786',
'lzh': 'Q37041',
'vo': 'Q36986',
'rup': 'Q29316',
'sgs': 'Q35086',
'zgh': 'Q7598268',
#'ang': '',
#'avk': '',
#'bbc': '',
#'bdr': '',
#'bew': '',
#'bi': '',
#'blk': '',
#'bpy': '',
#'btm': '',
#'cbk': '',
#'cdo': '',
#'dga': '',
#'dtp': '',
#'cu': '',
#'gcr': '',
#'fon': '',
#'goh': '',
#'gom': '',
#'got': '',
#'gsw': '',
#'hif': '',
#'ia': '',
#'iba': '',
#'igl': '',
#'jam': '',
#'kaa': '',
#'kge': '',
#'koi': '',
#'kus': '',
#'lez': '',
#'lfn': '',
#'lzh': '',
#'man': '',
#'mrj': '',
#'nah': '',
#'nia': '',
#'nov': '',
#'nr': '',
#'nrm': '',
#'pam': '',
#'pdc': '',
#'pih': '',
#'roa-tara': '',
#'rsk': '',
#'rup': '',
#'sa': '',
#'sgs': '',
#'stq': '',
#'tet': '',
#'tdd': '',
#'tpi': '',
#'vro': '',
#'yue': '',
#'zgh': '',
}

# last name, affixed family name, compound, toponiem
lastname_type_list = {'Q101352', 'Q66480858', 'Q60558422', 'Q17143070'}

# Initial list of natural languages
# Filled from the lang_qnumbers list above
# Others will be added automatically during script execution
nat_languages = {'Q150', 'Q188', 'Q652', 'Q1321', 'Q1860', 'Q7411'}

# Accepted language scripts (e.g. Latin)
script_whitelist = {'Q8229'}

# Disabled wikis, ignored for processing
unset_wikis = {
    'cbkwiki',          # Bot only site
    'zh_yuewiki',       # obsolete
}

# Languages using uppercase nouns
## Check if we could inherit this set from namespace or language properties??
upper_pref_lang = {'als', 'atj', 'bar', 'bat-smg', 'bjn', 'co?', 'dag', 'de', 'de-at', 'de-ch', 'diq', 'eu?', 'ext', 'fiu-vro', 'frp', 'ffr?', 'gcr', 'gsw', 'ha', 'hif?', 'ht', 'ik?', 'kaa?', 'kab', 'kbp?', 'ksh', 'lb', 'lfn?', 'lg', 'lld', 'mwl', 'nan', 'nds', 'nds-nl?', 'om?', 'pdc?', 'pfl', 'rmy', 'rup', 'sgs', 'shi', 'sn', 'tum', 'vec', 'vmf', 'vro', 'wo?'}

# Keeps the space before <ref>
veto_spacebeforeref = {'mlwiki', 'sqwiki'}

# Do not add authority templates
veto_authority = {
    'dewiki',       # https://de.wikipedia.org/wiki/Benutzer_Diskussion:GeertivpBot#Einf%C3%BCgung_Commons_/_Sort
    'frwiki',       # https://fr.wikipedia.org/w/index.php?title=Anne-Sophie_Duwez&diff=next&oldid=202016775
    'plwiki',       # https://meta.wikimedia.org/wiki/User_talk:Geertivp#Blocked_your_bot_on_plwiki
}

# Avoid duplicate Commonscat templates (Commonscat automatically included from templates)
veto_commonscat = {'azwiki', 'bawiki', 'fawiki',
    'huwiki',       # https://hu.wikipedia.org/w/index.php?title=Hernyóselyemfa&diff=26750576&oldid=26750556
                    # https://hu.wikipedia.org/w/index.php?title=Plakett&diff=next&oldid=26747356 (Wrong Commonscat placement)
    'hywiki', 'nowiki',
    'plwiki',       # https://pl.wikipedia.org/w/index.php?title=Ratusz_Staromiejski_w_Toruniu&diff=72386115&oldid=71744843 (Duplicate Commonscat)
    'pmswiki',
    'skwiki',       # https://meta.wikimedia.org/wiki/User_talk:Geertivp#c-Teslaton-20241026152600-GeertivpBot_on_skwiki
    'ukwiki',
    'urwiki',       # Bad placement https://ur.wikipedia.org/w/index.php?title=دھوپ&diff=5656446&oldid=5302302
    'zeawiki',
}

# Avoid risk for non-roman languages or rules
veto_countries = {
    'Q148',         # China
    'Q159',         # Sovjet-Union
    'Q15180',       # Russia
    'Q16663125',    # Kazahstan
    ## Other countries to add
}

# Veto DEFAULTSORT conversion
veto_defaultsort = {
    'nnwiki',
    #'plwiki',      # ['SORTUJ', 'DOMYŚLNIESORTUJ', 'DEFAULTSORT:', 'DEFAULTSORTKEY:', 'DEFAULTCATEGORYSORT:']
    'trwiki',       # WARNING: API error abusefilter-disallowed: abusefilter-sortname: no DEFAULTSORT statements at all
}

# Infobox without Wikidata functionality (to avoid empty emptyboxes)
veto_infobox = {
    'afwiki', 'azbwiki', 'enwiki', 'hrwiki',
    'idwiki',       # https://id.wikipedia.org/w/index.php?title=Chris_Wright_%28eksekutif_energi%29&diff=26538965&oldid=26538951
    'iswiki', 'jawiki',
    'kgwiki',       # https://kg.wikipedia.org/w/index.php?title=Rachel_Reeves&diff=next&oldid=45956 (LUA syntax error)
    'kowiki', 'kuwiki', 'mkwiki', 'mlwiki', 'mrwiki', 'ndswiki', 'plwiki', 'scowiki', 'shwiki', 'sqwiki', 'trwiki',
    'swwiki',       # https://sw.wikipedia.org/w/index.php?title=Paul_Ryan&diff=1361906&oldid=1361905
    'ugwiki',       # https://ug.wikipedia.org/w/index.php?title=مايك_پومپىئو&diff=169937&oldid=169936
    'urwiki',       # Empty infobox https://ur.wikipedia.org/wiki/تبادلۂ_خیال_صارف:Geertivp
    'viwiki',       # https://vi.wikipedia.org/w/index.php?title=Qu%E1%BA%A3ng_tr%C6%B0%E1%BB%9Dng&diff=next&oldid=71017209
    'xhwiki',       # https://xh.wikipedia.org/w/index.php?title=Justine_Musk&diff=37842&oldid=37841
    'warwiki', 'yowiki', 'zhwiki',
    'zuwiki',       # https://zu.wikipedia.org/w/index.php?title=U-Elon_Musk&diff=110777&oldid=110776
}

# Veto languages
# Skip non-standard character encoding; see also ROMANRE (other name rules)
# see https://en.wikipedia.org/wiki/Wikipedia:Naming_conventions_(Cyrillic)
# Not to be confused with veto_sitelinks and unset_wikis
### Should it be - or _ ??
veto_languages = {'aeb', 'aeb-arab', 'aeb-latn', 'ar', 'arc', 'arq', 'ary', 'arz', 'bcc', 'be' ,'be-tarask', 'bg', 'bn', 'bgn', 'bqi', 'cs', 'ckb', 'cv', 'dv', 'el', 'fa', 'fi', 'gan', 'gan-hans', 'gan-hant', 'glk', 'gu', 'he', 'hi', 'hu', 'hy', 'ja', 'ka', 'khw', 'kk', 'kk-arab', 'kk-cn', 'kk-cyrl', 'kk-kz', 'kk-latn', 'kk-tr', 'ko', 'ks', 'ks-arab', 'ks-deva', 'ku', 'ku-arab', 'ku-latn', 'ko', 'ko-kp', 'lki', 'lrc', 'lzh', 'luz', 'mhr', 'mk', 'ml', 'mn', 'mzn', 'ne', 'new', 'no', 'or', 'os', 'ota', 'pl', 'pnb', 'ps', 'ro', 'ru', 'rue', 'sd', 'sdh', 'sh', 'sk', 'sr', 'sr-ec', 'ta', 'te', 'tg', 'tg-cyrl', 'tg-latn', 'th', 'ug', 'ug-arab', 'ug-latn', 'uk', 'ur', 'vep', 'vi', 'yi', 'yue', 'zg-tw', 'zh', 'zh-cn', 'zh-hans', 'zh-hant', 'zh-hk', 'zh-mo', 'zh-my', 'zh-sg', 'zh-tw', 'zh-yue'}

# Automatically augmented from veto_languages using lang_qnumbers mapping
veto_languages_id = {'Q7737', 'Q8798'}

# List of languages wanting to use the <references /> tag
# https://no.wikipedia.org/w/index.php?title=Suzanne_Ciani&diff=next&oldid=23671158
veto_references = {'bgwiki', 'cswiki', 'fywiki', 'itwiki', 'nowiki', 'svwiki'}

# List of Wikipedia's that do not support bot updates (for different reasons)
veto_sitelinks = {
    # Requires CAPTCHA => blocking bot scripts (?)
    'cawiki', 'ckbwiki', 'eswiki', 'fawiki', 'jawiki', 'ptwiki', 'ruwiki', 'simplewiki', 'ttwiki', 'viwiki', 'wuuwiki', 'zhwiki',

    # Blocked (requires mandatory bot flag)
    'arwiki',       # https://ar.wikipedia.org/wiki/%D9%86%D9%82%D8%A7%D8%B4_%D8%A7%D9%84%D9%85%D8%B3%D8%AA%D8%AE%D8%AF%D9%85:GeertivpBot
    'dawiki',       # https://da.wikipedia.org/w/index.php?title=Speciel:Loglister/block&page=User%3AGeertivpBot
    'elwiki',       # Requires wikibot flag
    'itwiki',       # https://it.wikipedia.org/wiki/Special:Log/block?page=User:GeertivpBot
    'plwiki',       # https://meta.wikimedia.org/wiki/User_talk:Geertivp#c-Msz2001-20240802153000-Blocked_your_bot_on_plwiki
    'rowiki',       # https://ro.wikipedia.org/w/index.php?title=Special:Jurnal/block&page=User%3AGeertivpBot
    'slwiki',       # Requires wikibot flag
    'svwiki',       # Infobox
    'yuewiki',      # https://zh-yue.wikipedia.org/w/index.php?title=Special:日誌&logid=499083
    'zh_yuewiki',   # https://zh-yue.wikipedia.org/w/index.php?title=Special:日誌/block&page=User%3AGeertivpBot

    # Unblocked (after an issue was fixed)
    #'nowiki',      # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot

    # Have to proactively request a bot flag
    'dewiki',       # https://de.wikipedia.org/w/index.php?title=Spezial:Logbuch/block&page=User%3AGeertivpBot
                    # https://de.wikipedia.org/wiki/Benutzer_Diskussion:GeertivpBot#c-Aspiriniks-20231231204800-Geertivp-20230830114600
                    # https://de.wikipedia.org/wiki/Wikipedia:Administratoren/Notizen#Benutzer:GeertivpBot
    'enwiki',
    'iswiki',       # https://is.wikipedia.org/w/index.php?title=Kerfissíða:Aðgerðaskrár/block&page=User%3AGeertivpBot
    'kuwiki',       # https://ku.wikipedia.org/wiki/Got%C3%BBb%C3%AAja_bikarh%C3%AAner:GeertivpBot
                    # https://meta.wikimedia.org/wiki/User_talk:Geertivp#Bot_edits
    'nnwiki',       # https://nn.wikipedia.org/wiki/Brukardiskusjon:GeertivpBot#c-Ranveig-20241017095400-Needless
    'srwiki',       # https://meta.wikimedia.org/wiki/User_talk:Geertivp#Bot_edits
    'ukwiki',       # https://uk.wikipedia.org/wiki/%D0%9E%D0%B1%D0%B3%D0%BE%D0%B2%D0%BE%D1%80%D0%B5%D0%BD%D0%BD%D1%8F_%D0%BA%D0%BE%D1%80%D0%B8%D1%81%D1%82%D1%83%D0%B2%D0%B0%D1%87%D0%B0:Geertivp#Requests_for_bot_flag
    'vepwiki',      # https://meta.wikimedia.org/wiki/User_talk:Geertivp#Bot_edits

    # Bot approval pending
    # https://meta.wikimedia.org/wiki/User_talk:Geertivp#c-01miki10-20230714212500-Please_request_a_bot_flag_%40_fiwiki
    'fiwiki',       # https://fi.wikipedia.org/wiki/Käyttäjä:GeertivpBot
                    # https://fi.wikipedia.org/wiki/Keskustelu_k%C3%A4ytt%C3%A4j%C3%A4st%C3%A4:GeertivpBot

    # Temporary problem waiting for a code change
    #'lbwiki',

    # Unidentified problem
    ##'idwiki',       # https://id.wikipedia.org/w/index.php?title=Lodok&diff=23851618&oldid=21326440 (suspected update)

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

# List of recognized infoboxes
# Using this list, language templates infoboxlist[x] are automatically generated
sitelink_dict_list = [
# Required to be in strict sequence
# See also instance_types_by_category (2 elements)
    'Q6249834',         # infoboxlist[0] Infobox person (to generate Infobox template on Wikipedia), 39 s, 68 s
    'Q13383928',        # infoboxlist[1] Infobox Infobox windmills https://www.wikidata.org/wiki/Special:EntityPage/Q47517487
    ## Caveat: when adding elements, also extend instance_types_by_category

# Commonscat included - strict sequence
    'Q47517487',        # infoboxlist[2] Wikidata infobox
    'Q17534637',        # infoboxlist[3] Infobox person Wikidata (overrule)

    ## Caveat: strict sequence
    # Keep the list builtin_commonscat alligned!

    # plwiki specific
    # No Commonscat for Infobox buildings
    'Q5906647',         # infoboxlist[4] Infobox building (no Commonscat)
    'Q5914710',         # infoboxlist[5] Infobox kerk https://pl.wikipedia.org/w/index.php?title=Kościół_Wszystkich_Świętych_w_Popowicach&diff=next&oldid=72386014
    'Q6232685',         # infoboxlist[6] Infobox museum https://pl.wikipedia.org/w/index.php?title=Państwowe_Muzeum_Archeologiczne_w_Warszawie&diff=72386107&oldid=72386102
    'Q5637640',         # infoboxlist[7] Infobox brug https://pl.wikipedia.org/w/index.php?title=Most_Cestiusza&diff=72386127&oldid=72386123
    'Q5683132',         # infoboxlist[8] Infobox plaats https://pl.wikipedia.org/w/index.php?title=Sudisławl&diff=72393065&oldid=72393057
    'Q52496',           # infoboxlist[9] Takson infobox https://pl.wikipedia.org/w/index.php?title=Puchowiec_wspania%C5%82y&diff=next&oldid=72393064
    'Q5898006',         # infoboxlist[10] Infobox station https://pl.wikipedia.org/w/index.php?title=Catania_Centrale&diff=72368114&oldid=72368090
    'Q11009165',        # infoboxlist[11] Infobox administrative territorial entity https://pl.wikipedia.org/w/index.php?title=Saint-Pierre-Brouck&oldid=prev&diff=70559731

    # huwiki specific
    # No Commonscat for Infobox buildings
    'Q10805532',        # infoboxlist[12] Infobox kasteel

    # bawiki specific
    'Q42054995',        # infoboxlist[13] Universal infobox https://ba.wikipedia.org/w/index.php?title=Суздаль_кремле&diff=1266396&oldid=1266389

    # Human
    'Q5615832',         # infoboxlist[14] Infobox author, 21 s, 22 s; https://tg.wikipedia.org/w/index.php?title=Дейл_Карнегӣ&diff=1404168&oldid=1392239

# Not required to be in sequence
# ... other infoboxes can be appended...
    'Q5616161',         # Infobox musical artist, 4 s
    'Q5616966',         # Infobox football biography
    'Q5624818',         # Infobox scientist, 2 s
    'Q5626285',         # Infobox monarch
    'Q5871779',         # Infobox filmmaker
    'Q5904762',         # Infobox sportsperson
    'Q5914426',         # Infobox artist, 1 s
    'Q5929832',         # Infobox military person
    'Q6424841',         # Infobox politician
    'Q6583638',         # Infobox cyclist, 1 s
    'Q8086987',         # Infobox skier
    'Q14358369',        # Infobox actor
    'Q14458505',        # Infobox journalist

    'Q26165786',        # Infobox author alias, uzwiki
    'Q14359870',        # Infobox theatrical figure

# Non-human
    'Q6500619',         # Infobox kanaal https://be.wikipedia.org/w/index.php?title=Канал_Грыбаедава&diff=4653375&oldid=4267949
                        # https://www.wikidata.org/w/index.php?title=Q6500619&diff=2044488075&oldid=2016131484
    'Q5621344',         # Infobox airline https://cy.wikipedia.org/w/index.php?title=Loc&diff=12130558&oldid=12130342
    'Q5747491',         # Taxobox begin
    'Q5896997',         # Infobox world heritage
    'Q5900171',         # Infobox monument
    'Q5901151',         # Infobox sport
    'Q6055178',         # Infobox park
    'Q6175815',         # Geobox
    'Q6190581',         # Infobox organization
    'Q6434929',         # Multiple image, 9 s
    'Q6630855',         # Infobox food, 3 s
    'Q10581765',        # Infobox monastery https://hy.wikipedia.org/w/index.php?title=Սոլովեցի_մենաստան&diff=8940982&oldid=7102219
                        # https://be.wikipedia.org/w/index.php?title=Салавецкі_манастыр&diff=4653373&oldid=4474521
    'Q10730006',        # Infobox sports team
    'Q13553651',        # Infobox (overrule)
    'Q14449650',        # Speciesbox https://ml.wikipedia.org/w/index.php?title=കോറിഡാലിസ്_സോളിഡ&diff=4011546&oldid=4011544
    'Q25843199',        # Infobox https://sh.wikipedia.org/w/index.php?title=Katedrala_u_Vicenzi&diff=41752634&oldid=40904062

    # others to be added

### Shouldn't we add these to all non-human Wikipedia pages missing an Infobox?
    'Q5626735',         # Infobox generic, 12 s

# Redundant language codes rue, sv; .update() overrules => which one to give preference?
# https://favtutor.com/blogs/merge-dictionaries-python
    'Q20702632',        # Databox (nl; still experimental) => seems to work pretty well... {{#invoke:Databox|databox}}, 1 s
]

## Caveat: Keep the sitelink_dict_list alligned!
builtin_commonscat = {
    'plwiki': [4, 5, 6, 7, 8, 9, 10, 11],
    'huwiki': [12],     # https://hu.wikipedia.org/w/index.php?title=Kreml_%28Szuzdal%29&diff=26750589&oldid=26750577
    'bawiki': [13],
    'tgwiki': [14],
}


def get_canon_name(baselabel) -> str:
    """
    Get standardised name

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


def get_item_header(header):
    """
    Get the item header (label, description, alias, or dict element in user language)

    :param header: item labels, descriptions, or aliases, or any dict (dict)
    :return: label, description, or alias in the first available language (string, list)

    The language is in ISO code format.
    """

    if not header:
        return '-'
    else:
        # Return preferred label
        for lang in main_languages:
            if lang in header:
                return header[lang]

        # Return any other label
        for lang in header:
            return header[lang]
    return '-'


def get_item_header_langlist(header, langlist):
    """
    Get the item header (label, description, alias in user language)

    :param header: item label, description, or alias language list (string or list)
    :param langlist: language code list
    :return: label, description, or alias in the first available language (string)
    """

    # Try to get any explicit language code
    for lang in langlist:
        if lang in header:
            return header[lang]
    return None


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

    return get_item_header(propty.labels)


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
        except Exception as error:
            pywikibot.error('{} ({}), {}'.format(item, qnumber, error))      # Site error
            item = None
    else:
        item = qnumber
        qnumber = item.getID()

    # Resolve redirect pages
    while item and item.isRedirectPage():
        ## Should fix the sitelinks
        item = item.getRedirectTarget()
        label = get_item_header(item.labels)
        pywikibot.warning('Item {} ({}) redirects to {}'
                          .format(label, qnumber, item.getID()))
        qnumber = item.getID()

    return item


def get_item_label_dict(qnumber) -> {}:
    """
    Get all Wikipedia labels in all languages for a Qnumber.

    :param qnumber: list number
    :return: label dict set(including aliases; index by ISO language code)

    Example of usage:
        Image namespace name (Q478798).
    """
    # Get the timestamp to time the following transaction
    prevnow = datetime.now()
    labeldict = {}
    item = get_item_page(qnumber)

    # Get item labels (we assume there is always a label)
    for lang in item.labels:
        labeldict[lang] = [item.labels[lang]]

    # Append list of aliases in sequence after the main label
    for lang in item.aliases:
        for val in item.aliases[lang]:
            try:
                if val not in labeldict[lang]:
                    labeldict[lang].append(val)
            except:
                # Alias without item label
                labeldict[lang] = [val]

    # Refresh the timestamp to time this transaction
    now = datetime.now()
    isotime = now.strftime("%Y-%m-%d %H:%M:%S")     # Needed to format output
    pywikibot.log('{}\tLoading item labels for {} ({}) took {:d} seconds'
                  .format(isotime, get_item_header(labeldict)[0], qnumber,
                          int((now - prevnow).total_seconds())))
    return labeldict


def get_dict_using_statement_value(prop: str, propval: str, key: str) -> {}:
    """
    Get list of items that have a property/value statement

    :param prop: Property ID (string)
    :param propval: Property value (Q-number string)
    :param key: Property key (Q-number string)
    :return: dict of items (Q-numbers)

    Example: Get list of living languages:

        https://www.wikidata.org/w/api.php?action=query&list=search&srwhat=text&srsearch=P31:Q1288568
        https://www.wikidata.org/w/index.php?search=P31:Q1288568

    See https://www.mediawiki.org/wiki/API:Search

    Known problems:

        This algorithm should be recoded.
        Why does it take such a long time to load the list?
        Maybe swap prop and key?
        Maybe only use Key?
    """
    # Start of transaction
    prevnow = datetime.now()
    deltanow = prevnow
    pywikibot.log('Search statement: {}:{} to get {} language table'
                  .format(prop, propval, key))
    item_list = {}                      # Empty dict
    params = {'action': 'query',        # Statement search
              'list': 'search',
              'srsearch': prop + ':' + propval,
              'srwhat': 'text',
              'format': 'json',         # Important
              'srlimit': 'max'}         # Should be reasonable value
    request = api.Request(site=repo, parameters=params)
    result = request.submit()


    if 'query' in result and 'search' in result['query']:
        # Loop though items
        for row in result['query']['search']:
            qnumber = row['title']
            item = get_item_page(qnumber)

            try:
                if key in item.claims and prop in item.claims:
                    for claim in item.claims[prop]:
                        if claim.getTarget().getID() == propval:
                            for lc in item.claims[key]:
                                wmlangcd = lc.getTarget()
                                if not wmlangcd:
                                    # Ignore unregistered value
                                    # https://www.wikidata.org/wiki/Q67093214#P424
                                    pass
                                elif item.getID() not in item_list:
                                    # Real value
                                    item_list[item.getID()] = wmlangcd
                                elif len(item_list[item.getID()]) > len(wmlangcd):
                                    # Subvalues
                                    pywikibot.error('Language code {} different from {} for {}'
                                                    .format(item_list[item.getID()], wmlangcd, item.getID()))
                                    item_list[item.getID()] = wmlangcd
                                elif item_list[item.getID()] != wmlangcd:
                                    # Ambigous values
                                    pywikibot.error('Language code {} different from {} for {}'
                                                    .format(wmlangcd, item_list[item.getID()], item.getID()))
                            now = datetime.now()	        # Refresh the timestamp to time the following transaction
                            pywikibot.log('Language {} {} took {:d} seconds'
                                          .format(wmlangcd, item.getID(), int((now - deltanow).total_seconds())))
                            deltanow = now
                            break
            except Exception as error:
                # Fails for https://www.wikidata.org/wiki/Q652 (Italian)
                # Why?
                # https://codelookup.toolforge.org/it
                # WARNING: [[wikidata:Q652]] (Q652), 'p7829'
                # https://www.wikidata.org/wiki/Special:Log?page=Property:P7829
                # https://www.wikidata.org/wiki/Q652#P7829 (Temporary problem: the property was removed but the statement was still in cache...)
                # Purged the item now... cache problem that existed since previous week...
                pywikibot.warning('{} ({}), {}'.format(item, qnumber, error))      # Site error
                #pdb.set_trace()

    # Refresh the timestamp to time the current transaction
    now = datetime.now()
    isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Needed to format output
    pywikibot.log('{}\tLoading language codes took {:d} seconds for {:d} items'
                  .format(isotime, int((now - prevnow).total_seconds()), len(item_list)))

    # Convert set to list
    pywikibot.log(item_list)
    return item_list


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
    global unset_wikis

    # Start of transaction
    prevnow = datetime.now()
    sitedict = {}
    item = get_item_page(qnumber)

    # Get target sitelinks
    for sitelang in item.sitelinks:
        # Fast skip non-Wikipedia sites
        # Ignore special languages
        if (sitelang[-4:] == 'wiki'
                and '_x_' not in sitelang
                and sitelang not in unset_wikis):
            try:
                # Get template title
                sitelink = item.sitelinks[sitelang]
                if (sitelink.namespace == TEMPLATENAMESPACE
                        and str(sitelink.site.family) == 'wikipedia'):
                    sitedict[sitelang] = sitelink.title
            except Exception as error:
                # WARNING: Language 'sgs' does not exist in family wikipedia
                pywikibot.warning(error)
                unset_wikis.add(sitelang)
                #pdb.set_trace()

    # Refresh the timestamp to time the current transaction
    now = datetime.now()
    isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Needed to format output
    pywikibot.log('{}\tLoading {} ({}) took {:d} seconds for {:d} items'
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
                         os.getenv('LANG', MAINLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang]

    # Cleanup language list
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)

    for lang in MAINLANG.split(':'):
        if lang not in main_languages:
            main_languages.append(lang)

    return main_languages


def get_prop_val_object_label(item, proplist) -> str:
    """
    Get property value label

    :param item: Wikidata item
    :param proplist: Search list of properties
    :return: concatenated list of value labels
    """
    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:
            for claim in item.claims[prop]:
                val = claim.getTarget()
                try:
                    item_prop_val += get_item_header(val.labels) + '/'
                except Exception as error:
                    pywikibot.error(error)      # Site error
            break
    return item_prop_val


def get_prop_val_year(item, proplist) -> str:
    """
    Get death date (normally only one)

    :param item: Wikidata item
    :param proplist: Search list of date properties
    :return: first matching date
    """
    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:
            for claim in item.claims[prop]:
                val = claim.getTarget()
                try:
                    item_prop_val += str(val.year) + '/'
                except Exception as error:
                    pywikibot.error(error)      # Site error
            break
    return item_prop_val


def get_sdc_item(sdc_data) -> pywikibot.ItemPage:
    """
    Get the item from the SDC statement.

    :param sdc_data: SDC item number
    :return:
    """
    # Get item
    item = None
    try:
        qnumber = sdc_data['datavalue']['value']['id']
        item = get_item_page(qnumber)
    except Exception as error:
        pywikibot.error(error)
        pywikibot.info(sdc_data)
        # CRITICAL: Exiting due to uncaught exception KeyError: 'datavalue'
    return item


def is_foreign_lang_label(lang_list) -> str:
    """
    Check if foreign language
    """
    for val in lang_list:
        if not ROMANRE.search(val):
            return val
    return ''


def is_veto_lang_label(lang_list) -> bool:
    """
    Check if language is blacklisted
    """
    for claim in lang_list:
        val = claim.getTarget()
        if (val.language in veto_languages
                or not ROMANRE.search(val.text)):
            return True
    return False


def is_veto_script(script_list) -> str:
    """
    Check if script is in veto list

    :param script_list: script claims
    :return non-matching script or empty string
    """
    for claim in script_list:
        # Nonroman script
        try:
            val = claim.getTarget().getID()
            if val not in script_whitelist:
                return val
        except Exception as error:
            pywikibot.error(error)      # Site error (e.g. missing data value)
    return ''


def item_is_in_list(statement_list, itemlist) -> str:
    """Verify if statement list contains at least one item from the itemlist

    :param statement_list:  Statement list
    :param itemlist:        List of values
    :return: Matching or empty string
    """
    for claim in statement_list:
        try:
            val = claim.getTarget()
            if isinstance(val, pywikibot.page._wikibase.ItemPage):
                val = val.getID()
            ###elif: possible other data types
            if val in itemlist:
                return val
        except Exception as error:
            pywikibot.error(error)      # Site error (e.g. missing data value)
    return ''


def matching_claims(statement_list1, statement_list2):
    """Verify if statement lists are matching

    :param statement_list1:  Statement list
    :param statement_list2:  Reference statement list
    :return: Matching item
    """
    for claim in statement_list1:
        try:
            val = claim.getTarget()
            for claimref in statement_list2:
                if val == claimref.getTarget():
                    return val
        except Exception as error:
            pywikibot.error(error)      # Site error (e.g. missing data value)
    return None


def item_not_in_list(statement_list, itemlist) -> str:
    """
    Verify if any statement target is not in the itemlist

    :param statement_list:  Statement list
    :param itemlist:        List of values
    :return: Non-matching item or empty string
    """
    for claim in statement_list:
        try:
            val = claim.getTarget().getID()
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
                        'numeric-id': int(item.getID()[1:]),
                        'id': item.getID(),
                    }
                }
            }
        }]
    }

    item_label = get_item_header(item.labels)

    if SUBCLASSPROP in item.claims:
        ## We need other logic for subclasses
        # https://commons.wikimedia.org/wiki/File:Oudenaarde_Tacambaroplein_oorlogsmonument_-_228469_-_onroerenderfgoed.jpg
        # https://www.wikidata.org/wiki/Q3381576
        # https://www.wikidata.org/wiki/Q91079944
        # Could photography genre generate genre statement when having instance genre?
        pywikibot.warning('Not adding depict statements for item {} ({}) having subclass ()'
                          .format(item_label, item.getID(), SUBCLASSPROP))
    elif INSTANCEPROP not in item.claims:
        pywikibot.warning('Instance statement (P31) missing for item {} ({})'
                          .format(item_label, item.getID()))
    else:
        # Find all media files for the item
        for prop in item.claims:
            if prop in depict_item_type:
                # Reinitialise the depict statement (reset previous loop updates)
                if (depict_item_type[prop] or prop == IMAGEPROP
                        and item_is_in_list(item.claims[INSTANCEPROP], HUMANINSTANCE)):
                    # Compound depict REPRESENTATIONTYPEPROP
                    # Build the depict qualifier
                    # https://commons.wikimedia.org/wiki/Commons:Bots/Requests/GeertivpBot#GeertivpBot_(overleg_%C2%B7_bijdragen)

                    if depict_item_type[prop]:
                        qnumber = depict_item_type[prop]
                    else:
                        qnumber = PERSONPORTRAITINSTANCE    # Portrait of person

                    item_desc = get_item_header(get_item_page(qnumber).labels)
                    """
    Need to add qualifier (deprecated property!)
    https://commons.wikimedia.org/wiki/Special:EntityData/M17372639.json
    "qualifiers":{"P642":[{"snaktype":"value","property":"P642","hash":"13ca233362287df2f52077d460ebef58a666c855","datavalue":{"value":{"entity-type":"item","numeric-id":336977,"id":"Q336977"},"type":"wikibase-entityid"}}]},"qualifiers-order":["P642"],"id":"M17372639$b8185896-4eab-2715-5606-388898d07071","rank":"normal"}]}
                    """
                    depict_statement['claims'][0]['qualifiers-order'] = [REPRESENTATIONTYPEPROP]
                    depict_statement['claims'][0]['qualifiers'] = {}
                    depict_statement['claims'][0]['qualifiers'][REPRESENTATIONTYPEPROP] = [{
                        'snaktype': 'value',
                        'property': REPRESENTATIONTYPEPROP,
                        'datavalue': {
                            'type': 'wikibase-entityid',
                            'value': {
                                'entity-type': 'item',
                                'numeric-id': int(qnumber[1:]),
                                'id': qnumber,
                            }
                        }
                    }]

                    depictsdescr = 'Add SDC depicts {} (P180:{}) {}:{} ({}:{})'.format(
                                        item_label, item.getID(),
                                        representationtypelabel, item_desc,
                                        REPRESENTATIONTYPEPROP, qnumber)
                    depictsfmtd = 'Add SDC depicts [[d:{1}|{0}]] ({1}) [[d:Property:{4}|{2}]]:[[d:{5}|{3}]] ({4}:{5})'.format(
                                        item_label, item.getID(),
                                        representationtypelabel, item_desc,
                                        REPRESENTATIONTYPEPROP, qnumber)
                else:
                    # Simple depicts
                    qnumber = item.getID()
                    if 'qualifiers' in depict_statement['claims'][0]:       # Compound depict statement
                        del(depict_statement['claims'][0]['qualifiers'])
                        del(depict_statement['claims'][0]['qualifiers-order'])
                    depictsdescr = 'Add SDC depicts {} (P180:{})'.format(item_label, qnumber)
                    depictsfmtd = 'Add SDC depicts [[d:{1}|{0}]] ({1})'.format(item_label, qnumber)

                for claim in item.claims[prop]:
                    # Verify if there is a missing depict statement for any of the media files
                    depict_missing = True

                    if depict_item_type[prop]:
                        depict_statement['claims'][0]['rank'] = NORMAL_RANK
                    else:
                        # Set preferred rank because it comes from a Wikidata P18 or comparable statement
                        depict_statement['claims'][0]['rank'] = PREFERRED_RANK

                    # Get SDC media file info
                    media_page = claim.getTarget()
                    media_name = media_page.title()
                    # https://commons.wikimedia.org/entity/M63763537
                    media_identifier = 'M' + str(media_page.pageid)
                    sdc_request = site.simple_request(action='wbgetentities', ids=media_identifier)
                    commons_item = sdc_request.submit()
                    sdc_data = commons_item.get('entities').get(media_identifier)
                    sdc_statements = sdc_data.get('statements')

                    if sdc_statements:
                        # Show location from metadata
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
                                if depict['rank'] == PREFERRED_RANK:
                                    depict_statement['claims'][0]['rank'] = NORMAL_RANK
                                sitem = get_sdc_item(depict['mainsnak'])
                                if not sitem:
                                    pass
                                elif sitem.getID() == item.getID():
                                    depict_missing = False
                                elif sitem.getID() == qnumber:
                                    depict_missing = False
                                    # Maybe might need to update DEPICTFORMATPROP qualifier for existing depicts...

                    """
https://commons.wikimedia.org/wiki/Special:EntityData/M82236232.json
"P180":[{"mainsnak":{"snaktype":"value","property":"P180","hash":"7282af9508eed4a6f6ebc2e92db7368ecdbb61ab","datavalue":{"value":{"entity-type":"item","numeric-id":22668172,"id":"Q22668172"},"type":"wikibase-entityid"}},"type":"statement","id":"M82236232$e1491557-469c-7672-92d6-6e490f7403bf","rank":"normal"}],
                    """
                    # Should update REPRESENTATIONTYPEPROP qualifier for existing depicts...
                    if depict_missing:
                        # Add the SDC depict statements for this item
                        pywikibot.debug(depict_statement)
                        commons_token = site.tokens['csrf']
                        ### Could we add a reference to Wikidata?
                        sdc_payload = {
                            'action': 'wbeditentity',
                            'format': 'json',
                            'id': media_identifier,
                            'data': json.dumps(depict_statement, separators=(',', ':')),
                            'token': commons_token,
                            'summary': transcmt + ' ' + depictsfmtd + ' statement',
                            'bot': cbotflag,
                        }

                        sdc_request = site.simple_request(**sdc_payload)
                        try:
                            sdc_request.submit()
                            pywikibot.warning('{} to {} ({}) entity/{} {}'
                                              .format(depictsdescr,
                                                      get_property_label(prop), prop,
                                                      media_identifier, media_name))
                        except Exception as error:
                            # permissiondenied: You do not have the permissions needed to carry out this action for Q15616276
                            # https://commons.wikimedia.org/wiki/Commons:Auto-protected_files/wikipedia/bn
                            pywikibot.error('{}, {}'.format(depictsdescr, error))
                            pywikibot.info(sdc_request)
                            if exitfatal:               # Stop on first error
                                raise


def add_item_statement(item, propty, sitem, reference):
    """
    Add missing statement to item

    :param item: main item
    :param propty: property (string)
    :param sitem: item or value to assign (item, string, ... ; data type depending on propty)
    :param reference: reference statement
    :return: Claim if updated
    """
    ##pdb.set_trace()
    claim_added = None
    qnumber = item.getID()
    ### Need to fix sqnumber type
    if isinstance(sitem, pywikibot.page._wikibase.ItemPage):
        # Item
        sqnumber = sitem.getID()
        slabel = get_item_header(sitem.labels)
    ##elif re.QSUFFRE(sitem):
        #sitem = pywikibot.ItemPage(repo, sitem)
        #sqnumber = sitem.getID()
        #slabel = get_item_header(sitem.labels)
    ##elif: handle possible other data types
    else:
        # Value
        sqnumber = sitem
        slabel = sitem

    # Do not add duplicate statements
    if (propty not in item.claims
            or not item_is_in_list(item.claims[propty], [sqnumber])):
        claim = pywikibot.Claim(repo, propty)
        claim.setTarget(sitem)
        propty_label = get_property_label(propty)
        item.addClaim(claim, bot=wdbotflag, summary=transcmt + ' Add {} ({})'
                          .format(propty_label, propty))
        claim_added = claim

        try:
            primary_inst_item = get_item_page(item.claims[INSTANCEPROP][0].getTarget())
            instance_label = get_item_header(primary_inst_item.labels)
            item_instance = primary_inst_item.getID()
        except:
            instance_label = '-'
            item_instance = None

        pywikibot.warning('Add {}:{} ({}:{}) to {} ({}) {} ({})'
                          .format(propty_label, slabel,
                                  propty, sqnumber, instance_label, item_instance,
                                  get_item_header(item.labels), qnumber))

        ## Add the reference statement
        if reference:
            try:
                ## Remove hash from reference (needs to be recoded)
                pdb.set_trace()
                for refseq in reference:
                    del(refseq[1]['hash'])
                """
[OrderedDict([('P854', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P854', 'datatype': 'url', 'datavalue': {'value': 'http://www.riotinto.com/documents/RT_Annual_Report_2015.pdf', 'type': 'string'}, 'hash': '3211cb7a1ec81d884c43fadc172577a73e51ac28'})])])]

[OrderedDict([('P854', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P854', 'datatype': 'url', 'datavalue': {'value': 'http://www.riotinto.com/ar2014/pdfs/rio-tinto_2014-annual-report.pdf', 'type': 'string'}, 'hash': '0d0f2416004c4c85e842a42febcc26a5a40326d6'})])])]

                """
                claim.addSources(reference, summary=transcmt + ' Add reference')
                pywikibot.warning('Add reference {}'.format(reference))
            except Exception as error:  # other exception to be used
                # Invalid JSON
                pywikibot.error('Error processing {}, {}'.format(qnumber, error))
                pywikibot.info(reference)
    else:
        # If missing reference, also add one
        for claim in item.claims[propty]:
            """
[OrderedDict([('P3452', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P3452', 'datatype': 'wikibase-item', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 15864}, 'type': 'wikibase-entityid'}, 'hash': '1781c38b5e52a087980b31675bfba3708d40d3c5'})])])]

[OrderedDict([('P854', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P854', 'datatype': 'url', 'datavalue': {'value': 'https://www.nytimes.com/1969/03/22/archives/mitt-romney-marries-ann-davies.html', 'type': 'string'}, 'hash': 'f2a30e913832e670cf4a39b05890d5de59bb333c'})])])]

[OrderedDict([('P143', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P143', 'datatype': 'wikibase-item', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 328}, 'type': 'wikibase-entityid'}, 'hash': 'fa278ebfc458360e5aed63d5058cca83c46134f1'})])])]

https://www.geeksforgeeks.org/ordereddict-in-python/

[OrderedDict([('P854', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P854', 'datatype': 'url', 'datavalue': {'value': 'http://www.cbsnews.com/news/facebooks-mark-zuckerberg-marries-priscilla-chan/', 'type': 'string'}, 'hash': '8780de76ecf140bd7722065c6b888975115bf510'})]), ('P123', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P123', 'datatype': 'wikibase-item', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 861764}, 'type': 'wikibase-entityid'}, 'hash': '8780de76ecf140bd7722065c6b888975115bf510'})]), ('P1476', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P1476', 'datatype': 'monolingualtext', 'datavalue': {'value': {'text': "Facebook's Mark Zuckerberg marries Priscilla Chan", 'language': 'en'}, 'type': 'monolingualtext'}, 'hash': '8780de76ecf140bd7722065c6b888975115bf510'})]), ('P1683', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P1683', 'datatype': 'monolingualtext', 'datavalue': {'value': {'text': "This photo provided by Facebook shows the social network's co-founder and CEO Mark Zuckerberg and Priscilla Chan at their wedding ceremony in Palo Alto, Calif., Saturday, May 19, 2012.", 'language': 'en'}, 'type': 'monolingualtext'}, 'hash': '8780de76ecf140bd7722065c6b888975115bf510'})]), ('P577', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P577', 'datatype': 'time', 'datavalue': {'value': {'time': '+00000002012-05-22T00:00:00Z', 'precision': 11, 'after': 0, 'before': 0, 'timezone': 0, 'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'}, 'type': 'time'}, 'hash': '8780de76ecf140bd7722065c6b888975115bf510'})])])]

[OrderedDict([('P813', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P813', 'datatype': 'time', 'datavalue': {'value': {'time': '+00000002018-12-01T00:00:00Z', 'precision': 11, 'after': 0, 'before': 0, 'timezone': 0, 'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'}, 'type': 'time'}, 'hash': '79cf2c8b5840d10d87884eafdbd1e9ca5bdfed07'})])])]

            """
            ## Needs to be recoded
            if reference and not claim.getSources() and claim.getTarget().getID() == sqnumber:  ### Need to fix sqnumber type detection...
                try:
                    ## Remove hash from reference
                    pdb.set_trace()
                    for refseq in reference:
                        del(refseq[1]['hash'])
                    claim.addSources(reference, summary=transcmt + ' Add reference')
                    pywikibot.warning('Add reference {}'.format(reference))
                except Exception as error:  # other exception to be used
                    # Invalid JSON
                    pywikibot.error('Error processing {}, {}'.format(qnumber, error))
                    pywikibot.info(reference)

    return claim_added


def wd_proc_all_items():
    """
    Main module logic
    """

    global commonscatqueue
    global exitstat
    global lastwpedit
    global nat_languages
    global transcount
    global unset_wikis

# Loop initialisation
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
        pywikibot.info('')
        transcount += 1

        status = 'OK'
        alias = ''
        descr = ''
        commonscat = ''     # Commons category
        nationality = ''
        label = ''
        birthday = ''
        deathday = ''
        mainwikipediapage = ''

        try:		        # Error trapping (prevents premature exit on transaction error)
            item = get_item_page(qnumber)
            qnumber = item.getID()

            # Instance type could be missing
            # Only get first instance
            # Redundant instances are ignored
            try:
                primary_inst_item = get_item_page(item.claims[INSTANCEPROP][0].getTarget())
                item_instance = primary_inst_item.getID()

                # Show missing statements for item
                if INSTANCEPROPLISTPROP in primary_inst_item.claims:
                    ###pdb.set_trace()
                    for claim in primary_inst_item.claims[INSTANCEPROPLISTPROP]:
                        proptyx = claim.getTarget()
                        propty = proptyx.getID()       # Comparison requires property as string
                        if False and propty not in item.claims:
                            pywikibot.warning('Missing statement {} ({})'
                                              .format(get_item_header(proptyx.labels), propty))
            except:
                item_instance = ''

            label = get_item_header(item.labels)      # Get label
            nationality = get_prop_val_object_label(item,   [NATIONALITYPROP, COUNTRYPROP, COUNTRYORIGPROP, JURISDICTIONPROP])  # nationality
            birthday    = get_prop_val_year(item,     [BIRTHDATEPROP, FOUNDINGDATEPROP, STARTDATEPROP, OPERATINGDATEPROP])      # birth date (normally only one)
            deathday    = get_prop_val_year(item,     [DEATHDATEPROP, DISSOLVDATEPROP, ENDDATEPROP, SERVICEENDDATEPROP])        # death date (normally only one)

            if label == '-':
                status = 'No label'         # Missing label
            else:
                # Remove redundant trailing writing direction
                while len(label) > 0 and label[len(label)-1] in {'\u200e', '\u200f'}:
                    label=label[:len(label)-1]
                # Replace alternative space character
                label = label.replace('\u00a0', ' ').strip()

                label = get_canon_name(label)

                if not (item_instance in human_type_list or forcecopy):   # Force label copy
                    status = 'Item'                         # Non-human item
                elif (NATIONALITYPROP in item.claims
                        and item_is_in_list(item.claims[NATIONALITYPROP], veto_countries)):     # nationality blacklist (languages)
                    status = 'Country'
                elif (    not ROMANRE.search(label)
                        or (mainlang in item.aliases
                            and is_foreign_lang_label(item.aliases[mainlang]))
                        or (NATIVENAMEPROP in item.claims
                            and is_veto_lang_label(item.claims[NATIVENAMEPROP]))        # name in native language
                        or (NATIVELANGPROP in item.claims
                            and item_is_in_list(item.claims[NATIVELANGPROP], veto_languages_id)) # native language
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

# (1) Fix the "no" Wikidata issue
            # "no" is Wikipedia id, "nd" is Wikidata id
            # Move any Wikidata no label to nb, and possibly to aliases
            # https://www.wikidata.org/wiki/User_talk:GeertivpBot/2023#Don't_use_'no'_label
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
                    for claim in item.aliases['no']:
                        if claim and claim not in item.aliases['nb']:
                            item.aliases['nb'].append(claim)
                else:
                    item.aliases['nb'] = item.aliases['no']
                item.aliases['no'] = []

            # Move no descriptions to nb, else remove
            if 'no' in item.descriptions:
                if 'nb' not in item.descriptions:
                    item.descriptions['nb'] = item.descriptions['no']
                item.descriptions['no'] = ''

# (2) Merge sitelinks (gets priority above default value)
            noun_in_lower = False
            # Get target sitelink
            for sitelang in item.sitelinks:
                # Process only known Wikipedia links (skip other projects)
                # Fast skip non-Wikipedia sites
                if (sitelang[-4:] == 'wiki'
                        and '_x_' not in sitelang
                        and sitelang not in unset_wikis):
                    try:
                        # Get template title
                        sitelink = item.sitelinks[sitelang]
                        wm_family = str(sitelink.site.family)
                    except Exception as error:
                        pywikibot.warning(error)      # Site error
                        unset_wikis.add(sitelang)
                        wm_family = ''

                    # Only main namespace
                    if wm_family == 'wikipedia':
                        # See https://www.wikidata.org/wiki/User_talk:GeertivpBot#Don%27t_use_%27no%27_label
                        lang = sitelink.site.lang
                        if lang == 'bh':    # Canonic language names
                            lang = 'bho'
                        elif lang == 'no':
                            lang = 'nb'

                        # https://www.wikidata.org/w/index.php?title=Q2250303&diff=prev&oldid=2041641711
                        baselabel = get_canon_name(sitelink.title)

                        ## Fix language caps
                        # Wikipedia lemmas are in leading uppercase
                        # Wikidata lemmas are in lowercase, unless:
                        if (item_instance in human_type_list
                                or lang in veto_languages
                                or not ROMANRE.search(baselabel)
                                or not ROMANRE.search(label)):
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

                        if sitelink.namespace != MAINNAMESPACE:
                            baselabel = sitelink.site.namespace(sitelink.namespace) + ':' + baselabel
                        pywikibot.debug('Page {}:{}'.format(lang, baselabel))
                        item_name_canon = unidecode.unidecode(baselabel).casefold()

                        # Register new label if not already present
                        if (sitelink.namespace not in {MAINNAMESPACE, CATEGORYNAMESPACE, TEMPLATENAMESPACE}
                                # Only handle main namespace
                                # mul label already registered; do not replicate language label
                                # https://www.wikidata.org/wiki/Help:Default_values_for_labels_and_aliases
                                or MULANG in item.labels and item.labels[MULANG] == baselabel):
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
                            for claim in item.aliases[lang]:
                                if item_name_canon == unidecode.unidecode(claim).casefold():
                                    break
                            else:
                                item.aliases[lang].append(baselabel)    # Merge aliases

# (3) Replicate instance descriptions
            # Get description from the EN Wikipedia
            # To our opinion the wp.en Short description template is useless;
            # it should copy the description from Wikidata instead...
            # anyway we can store the value in Wikidata if it is available in WP and missing in WD
            if ENLANG not in item.descriptions and ENLANG in item.sitelinks:    ## enlang_list ?
                sitelink = item.sitelinks[ENLANG]
                page = pywikibot.Page(sitelink.site, sitelink.title, sitelink.namespace)
                if sitelink.namespace == MAINNAMESPACE and page.text:
                    pagedesc = SHORTDESCRE.search(page.text)
                    if pagedesc:
                        pywikibot.info(pagedesc)
                        itemdesc = pagedesc[1]
                        itemdesc = itemdesc[0].lower() + itemdesc[1:]   ## Always lowercase?
                        item.descriptions[ENLANG] = itemdesc

            # Replicate labels from the instance label as descriptions
            # Avoid redundant descriptions
            # https://phabricator.wikimedia.org/T303677
            if (False and item_instance
                    and (repldesc or len(item.claims[INSTANCEPROP]) == 1
                        and item_instance in copydesc_item_list)):
                for lang in primary_inst_item.labels:
                    if overrule or lang not in item.descriptions:
                        item.descriptions[lang] = primary_inst_item.labels[lang].replace(':', ' ')

            # Add the label for missing languages
            ###pdb.set_trace()
            if (label and (status in {'OK', 'Nationality'}
                    or item_instance == WIKIMEDIACATINSTANCE)):
                if lead_lower:
                   # Lowercase first character
                   label = label[0].lower() + label[1:]
                elif lead_upper:
                   # Uppercase first character
                   label = label[0].upper() + label[1:]

                if not uselabels:
                    # Only update mul lang
                    if MULANG not in item.labels:
                        if ORIGNAMELABELPROP in item.claims:
                            baselabel = item.claims[ORIGNAMELABELPROP][0].getTarget()
                            if baselabel.language == MULANG:
                                item.labels[MULANG] = baselabel.text
                            else:
                                item.labels[MULANG] = label
                        else:
                            item.labels[MULANG] = label

                    if MULANG not in item.aliases and mainlang in item.aliases:
                        item.aliases[MULANG] = item.aliases[mainlang]
                        ##item.aliases[mainlang] = []
                else:
                    # Except if labels should be copied
                    # Ignore accents
                    # Skip non-Roman languages
                    item_label_canon = unidecode.unidecode(label).casefold()

# (4) Add missing aliases for labels
                    for lang in item.labels:
                        if lang in veto_languages:
                            pass
                        elif item_label_canon == unidecode.unidecode(item.labels[lang]).casefold():
                            pass
                        elif lang not in item.aliases:
                            item.aliases[lang] = [label]
                        else:
                            for claim in item.aliases[lang]:
                                if (item_label_canon == unidecode.unidecode(claim).casefold()
                                        or not ROMANRE.search(claim)):
                                    break
                            else:
                                item.aliases[lang].append(label)    # Merge aliases

# (4) Add missing labels or aliases for aliases
                    for lang in item.aliases:
                        if lang in veto_languages:
                            pass
                        elif lang not in item.labels:
                            item.labels[lang] = label
                        elif item_label_canon == unidecode.unidecode(item.labels[lang]).casefold():
                            pass
                        elif lang not in item.aliases:
                            item.aliases[lang] = [label]
                        else:
                            for claim in item.aliases[lang]:
                                if (item_label_canon == unidecode.unidecode(claim).casefold()
                                        or not ROMANRE.search(claim)):
                                    break
                            else:
                                item.aliases[lang].append(label)        # Merge aliases

# (5) Add missing labels or aliases for descriptions
                    for lang in item.descriptions:
                        if lang not in veto_languages and ROMANRE.search(item.descriptions[lang]):
                            if lang not in item.labels:
                                item.labels[lang] = label
                            elif item_label_canon == unidecode.unidecode(item.labels[lang]).casefold():
                                pass
                            elif lang not in item.aliases:
                                item.aliases[lang] = [label]
                            else:
                                for claim in item.aliases[lang]:
                                    if (item_label_canon == unidecode.unidecode(claim).casefold()
                                            or not ROMANRE.search(claim)):
                                        break
                                else:
                                    item.aliases[lang].append(label)    # Merge aliases

# (6) Merge labels for missing Latin languages
                    for lang in all_languages:
                        if lang not in item.labels:
                            item.labels[lang] = label
                        elif item_label_canon == unidecode.unidecode(item.labels[lang]).casefold():
                            pass
                        elif lang not in item.aliases:
                            item.aliases[lang] = [label]
                        else:
                            for claim in item.aliases[lang]:
                                if (item_label_canon == unidecode.unidecode(claim).casefold()
                                        or not ROMANRE.search(claim)):
                                    break
                            else:
                                item.aliases[lang].append(label)    # Merge aliases

# Single native person name can be considered as mother tongue (native language)
            for propty in [BIRTHNAMEPROP, NATIVENAMEPROP, MARIEDNAMEPROP, NICKNAMEPROP]:
                if propty in item.claims:
                    # Get single native language from name
                    for claim in item.claims[propty]:
                        baselabel = claim.getTarget()
                        natname = baselabel.text            # Avoid error "Object of type WbMonolingualText is not JSON serializable"
                        lang = baselabel.language

                        # Get main language
                        if lang not in lang_qnumbers and '-' in lang:
                            langid = lang.split('-')[0]
                            pywikibot.error('Unknown language {}, use {} instead'
                                            .format(lang, langid))
                            lang = langid

                        if lang == MULANG:
                            # Not a native language
                            # https://www.wikidata.org/wiki/Help:Default_values_for_labels_and_aliases
                            pass
                        elif lang in lang_qnumbers:
                            langid = lang_qnumbers[lang]
                            nat_languages.add(langid)       # Add a natural language
                            # Add the name as an alias
                            # Add native language
                            if (item_instance in HUMANINSTANCE
                                    and len(item.claims[propty]) == 1
                                    and NATIVELANGPROP not in item.claims
                                    and add_item_statement(item, NATIVELANGPROP, get_item_page(langid), None)):
                                status = 'Update'
                        else:
                            # We can set mul language
                            pywikibot.error('Unknown language {}, use {} instead'
                                            .format(lang, MULANG))
                            lang = MULANG

                        if MULANG in item.labels and item.labels[MULANG] == natname:
                            pass
                        elif lang not in item.labels:
                            item.labels[lang] = natname
                        elif item.labels[lang] == natname:
                            pass
                        elif lang not in item.aliases:
                             item.aliases[lang] = [natname]
                        elif natname not in item.aliases:
                            item.aliases[lang].append(natname)

# Add pseudonyms to the mul aliases
            for propty in alternative_person_names_props:
                if propty in item.claims:
                    for claim in item.claims[propty]:
                        baselabel = claim.getTarget()
                        # https://www.wikidata.org/wiki/Help:Default_values_for_labels_and_aliases

                        # Lanuage independant name
                        lang = MULANG
                        if lang not in item.labels:
                            item.labels[lang] = baselabel
                        elif item.labels[lang] == baselabel:
                            pass
                        elif lang not in item.aliases:
                            item.aliases[lang] = [baselabel]
                        elif baselabel not in item.aliases[lang]:
                            item.aliases[lang].append(baselabel)    # Merge aliases

# Replicate publication title
            for propty in {EDITIONTITLEPROP}:
                if propty in item.claims:
                    for claim in item.claims[propty]:
                        baselabel = claim.getTarget()
                        # We ignore the language of publication; we assign the mul language, when missing
                        if MULANG not in item.labels:
                            item.labels[MULANG] = baselabel.text
                            status = 'Update'

# (7) Move first alias to any missing label
            """
            ## Disable because of mul language
            for lang in item.aliases:
                if (lang not in item.labels
                        and lang in all_languages
                        and lang in item.descriptions
                        and ROMANRE.search(item.descriptions[lang])):
                    for claim in item.aliases[lang]:
                        if ROMANRE.search(claim):
                            pywikibot.log('Move {} alias {} to label'.format(lang, claim))
                            item.labels[lang] = claim                 # Move single alias
                            item.aliases[lang].remove(claim)
                            break
            """

# (10) Remove duplicate aliases for all languages: for each label remove all equal aliases
            for lang in item.labels:
                if lang in item.aliases:
                    while item.labels[lang] in item.aliases[lang]:
                        item.aliases[lang].remove(item.labels[lang])

            """
            ## Not yet agreed by community...
            for lang in item.labels:
                if lang != MULANG and item.labels[lang] == label:
                    item.labels[lang] = ''
            """

            """
            ## Bad idea
            ### Potential problem with missing mul label
            for lang in item.aliases:
                while item.labels[MULANG] in item.aliases[lang]:
                    item.aliases[lang].remove(item.labels[MULANG])
            """

# (8) Add missing Wikipedia sitelinks
            for lang in main_languages:
                sitelang = lang + 'wiki'
                if lang == MULANG:
                    # Skip default language
                    continue
                elif lang == 'bho':
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
                            item.setSitelink(sitedict, bot=wdbotflag, summary=transcmt + ' Add sitelink')
                            pywikibot.warning('Creating sitelink {}:{} ({})'
                                              .format(lang, item.labels[lang], qnumber))
                            status = 'Sitelink'
                            ###item.sitelinks[sitelang] =   # "in memory" item is not automatically updated
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

                    # If the sitelink is still missing, try to add a sitelink from the aliases
                    if sitelang not in item.sitelinks and lang in item.aliases:
                        for claim in item.aliases[lang]:
                            sitedict = {'site': sitelang, 'title': claim}
                            try:
                                item.setSitelink(sitedict, bot=wdbotflag, summary=transcmt + ' Add sitelink')
                                pywikibot.warning('Creating sitelink {}:{} ({})'
                                                  .format(lang, claim, qnumber))
                                status = 'Sitelink'
                                ###item.sitelink
                                break
                            except pywikibot.exceptions.OtherPageSaveError as error:
                                # Get unique Q-numbers, skip duplicates (order not guaranteed)
                                aitmlist = set(QSUFFRE.findall(str(error)))
                                if len(aitmlist) > 0:
                                    aitmlist.remove(qnumber)

                                if len(aitmlist) > 0:
                                    itmlist.update(aitmlist)
                                    pywikibot.info('Sitelink {}:{} ({}) conflicting with {}'
                                                   .format(lang, claim, qnumber, aitmlist))
                                    status = 'DupLink'	    # Conflicting sitelink statement
                                    errcount += 1
                                    exitstat = max(exitstat, 10)

                    # Create symmetric Not Equal statements
                    # Requires matching instances
                    # Inverse statement will be executed below
                    ## WARNING: entity-schema datatype is not supported yet.
                    if INSTANCEPROP not in item.claims:
                        pywikibot.info('Missing instance ({}) for {}'
                                       .format(INSTANCEPROP, qnumber))
                    else:
                        # Add missing not equal statements
                        for sqnumber in itmlist:
                            relitem = get_item_page(sqnumber)
                            if INSTANCEPROP not in relitem.claims:
                                pywikibot.info('Missing instance ({}) for {}'.format(INSTANCEPROP, sqnumber))
                            elif matching_claims(item.claims[INSTANCEPROP], relitem.claims[INSTANCEPROP]):
                                add_item_statement(item, NOTEQTOPROP, relitem, None)
                                add_item_statement(relitem, NOTEQTOPROP, item, None)
                            else:
                                pywikibot.info('Nonmatching instances: {} ({}) is {} ({}) - {} ({}) is {} ({})'
                                               .format(get_item_header(item.labels), qnumber,
                                                       get_item_header(item.claims[INSTANCEPROP][0].getTarget().labels),
                                                       item.claims[INSTANCEPROP][0].getTarget().getID(),
                                                       get_item_header(relitem.labels), sqnumber,
                                                       get_item_header(relitem.claims[INSTANCEPROP][0].getTarget().labels),
                                                       relitem.claims[INSTANCEPROP][0].getTarget().getID()))

                # Get Wikipedia page
                if sitelang in item.sitelinks and not mainwikipediapage:
                    mainwikipediapage = item.sitelinks[sitelang].site.lang + ':' + item.sitelinks[sitelang].title

            maincat_item = ''
            # Add inverse statement
            if MAINCATEGORYPROP in item.claims:
                maincat_item = get_item_page(item.claims[MAINCATEGORYPROP][0].getTarget())

# (9) Set Commons Category sitelinks
            # Search for candidate Commons Category
            enlabel = get_item_header_langlist(item.labels, enlang_list)
            if COMMONSCATPROP in item.claims:                   # Get candidate category
                commonscat = item.claims[COMMONSCATPROP][0].getTarget() # Only take first value
            elif 'commonswiki' in item.sitelinks:               # Commons sitelink exists
                sitelink = item.sitelinks['commonswiki']
                if sitelink.namespace in {MAINNAMESPACE, CATEGORYNAMESPACE}:
                    commonscat = sitelink.title
            elif maincat_item and COMMONSCATPROP in maincat_item.claims:
                commonscat = maincat_item.claims[COMMONSCATPROP][0].getTarget()
            elif COMMONSGALLARYPROP in item.claims:             # Commons gallery page
                commonscat = item.claims[COMMONSGALLARYPROP][0].getTarget()
            elif COMMONSINSTPROP in item.claims:                # Commons institution page
                commonscat = item.claims[COMMONSINSTPROP][0].getTarget()
            elif COMMONSCREATORPROP in item.claims:             # Commons creator page
                commonscat = item.claims[COMMONSCREATORPROP][0].getTarget()
            elif item_instance in lastname_type_list:
                commonscat = label + ' (surname)'
            elif enlabel:                               # English label might possibly be used as Commons category
                commonscat = enlabel
            elif mainlang in item.labels:               # Otherwise the native label
                commonscat = item.labels[mainlang]

            if commonscat:
                # https://www.wikidata.org/w/index.php?title=Q209351&diff=2044505169&oldid=1988298469
                page = pywikibot.Category(site, commonscat)
                if not page.text:
                    # Category page does not exist (yet)
                    pywikibot.warning('Empty Wikimedia Commons category [[Category:{}]]'
                                      .format(commonscat))
                    commonscat = ''
                elif COMMONSCATREDIRECTRE.search(page.text):
                    # Should only assign real Category pages
                    pywikibot.warning('Redirect Wikimedia Commons category [[Category:{}]]'
                                      .format(commonscat))
                    commonscat = ''
                elif 'commonswiki' not in item.sitelinks:
                    # Try to create a missing Wikimedia Commons Category sitelink
                    try:
                        sitedict = {'site': 'commonswiki', 'title': page.title()}
                        item.setSitelink(sitedict, bot=wdbotflag, summary=transcmt + ' Add sitelink')
                        status = 'Commons'
                    except pywikibot.exceptions.OtherPageSaveError as error:
                        # Category already assigned to other item
                        # Get unique Q-numbers, skip duplicates (order is not guaranteed)
                        itmlist = set(QSUFFRE.findall(str(error)))
                        if len(itmlist) > 0:
                            itmlist.remove(qnumber)

                        # Silently pass if no conflicting Category page
                        if len(itmlist) > 0:
                            # Category was not assigned due to ambiguity
                            pywikibot.info('Category {} ({}) conflicting with {}'
                                           .format(commonscat, qnumber, itmlist))
                            status = 'DupCat'	    # Conflicting category statement
                            errcount += 1
                            exitstat = max(exitstat, 10)

                            # Generate missing not equal to statements
                            if INSTANCEPROP in item.claims:
                                for sqnumber in itmlist:
                                    relitem = get_item_page(sqnumber)
                                    # Create symmetric Not Equal statements
                                    # Inverse statement will be executed below
                                    if (INSTANCEPROP in relitem.claims
                                            and matching_claims(item.claims[INSTANCEPROP], relitem.claims[INSTANCEPROP])):
                                        add_item_statement(item, NOTEQTOPROP, relitem, None)
                                        add_item_statement(relitem, NOTEQTOPROP, item, None)
                        commonscat = ''

                if commonscat:
                    # Add Wikidata Infobox to Wikimedia Commons Category
                    # Requires a Wikimedia Commons botflag
                    if cbotflag and not WDINFOBOXRE.search(page.text):
                        #### https://commons.wikimedia.org/wiki/Commons:Bots/Requests/GeertivpBot#GeertivpBot_(overleg_%C2%B7_bijdragen)
                        # Avoid duplicates and Category redirect
                        pageupdated = transcmt + ' Add Wikidata Infobox'
                        # Trim trailing spaces
                        page.text = '{{Wikidata Infobox}}\n' + re.sub(r'[ \t\r\f\v]+$', '', page.text, flags=re.MULTILINE)
                        pywikibot.warning('Add {} template to Commons {}'
                                          .format('Wikidata Infobox', page.title()))
                        page.save(summary=pageupdated, minor=True)  # No real content added
                        # https://doc.wikimedia.org/pywikibot/stable/api_ref/pywikibot.page.html
                        # https://m.mediawiki.org/wiki/Manual:Pywikibot/Cookbook/Saving_a_single_page
                        # https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.page.html#page.BasePage.save
                        status = 'Commons'

                    # Add Commons category
                    if add_item_statement(item, COMMONSCATPROP, commonscat, None):
                        status = 'Cat'

            # Add missing Commonscat statements to Wikipedia via queue
            # Wikipedia should have no more than 1 transaction per minute (when not having bot account)
            for sitelang in item.sitelinks:
                # Get target sitelink, provided it is in the main namespace of Wikipedia
                if (sitelang[-4:] == 'wiki' # Only Wikipedia
                        and '_x_' not in sitelang
                        and sitelang not in unset_wikis
                        and sitelang not in veto_sitelinks):
                    try:
                        sitelink = item.sitelinks[sitelang]

                        if (sitelink.namespace in {MAINNAMESPACE, CATEGORYNAMESPACE}
                                and str(sitelink.site.family) == 'wikipedia'):
                            lang = sitelink.site.lang

                            if not mainwikipediapage:
                                mainwikipediapage = lang + ':' + sitelink.title

                            if lang == 'bh':    # Canonic language names
                                lang = 'bho'
                            elif lang == 'no':  # Wikipedia
                                lang = 'nb'     # Wikidata

                            wpcatpage = ''
                            if not maincat_item:
                                pass
                            elif sitelang in maincat_item.sitelinks:
                                # Wikipedia category does exist
                                wpcatpage = maincat_item.sitelinks[sitelang].title
                            elif lang in maincat_item.labels:
                                # Possibly unexisting Wikipedia category
                                # Omit prefix (Category:)
                                wpcatpage = maincat_item.labels[lang][maincat_item.labels[lang].find(':') + 1:]

                            # Push the record for delayed processing
                            commonscatqueue.append((item, sitelang, item_instance, commonscat, wpcatpage))

                            # Add a natural language
                            langid = lang_qnumbers[lang]
                            nat_languages.add(langid)
                    except KeyError as error:
                        # Language not known, please register language code in lang_qnumbers
                        pywikibot.warning('Unregistered item number for language {} for {} ({})'
                                          .format(error, label, qnumber))
                    except Exception as error:
                        pywikibot.warning(error)      # Site error
                        unset_wikis.add(sitelang)

# (11) Now store the header changes
            try:
                item.editEntity({'labels': item.labels,
                                 'descriptions': item.descriptions,
                                 'aliases': item.aliases}, summary=transcmt, bot=wdbotflag)
                pywikibot.debug(item.labels)
            except pywikibot.exceptions.OtherPageSaveError as error:    # Page Save Error (multiple reasons)
                # WARNING: API error not-recognized-language: The supplied language code "ak" was not recognized.
                # ERROR: Error saving entity Q4916, Edit to page [[wikidata:Q4916]] failed:
                # not-recognized-language: The supplied language code "ak" was not recognized.
                pywikibot.error('Error saving entity {}, {}'.format(qnumber, error))
                pdb.set_trace()
                status = 'SaveErr'
                errcount += 1
                exitstat = max(exitstat, 14)
                if exitfatal:   # Stop on first error
                    raise       # This error might hide more data quality problems

# Now process any claims

# (12) Replicate Moedertaal -> Taalbeheersing
            # Add language used from mother language
            # Not only for persons, also for people
            # Multiple mother tongues are possible
            # All mother tongues are natural languages
            if NATIVELANGPROP in item.claims:
                if item_instance in HUMANINSTANCE:
                    for claim in item.claims[NATIVELANGPROP]:
                        target = get_item_page(claim.getTarget())
                        nat_languages.add(target.getID())           # Add a natural language

                        if add_item_statement(item, LANGKNOWPROP, target, None):
                            status = 'Update'
                else:
                    status = 'Error'
                    pywikibot.error('{} is only supported for humans, not for {} ({}) with instance ({})'
                                    .format(NATIVELANGPROP, label, qnumber, item_instance))

# (13) Replicate Taalbeheersing -> Moedertaal
            # If person knows only one single language, we might consider it as a mother tongue
            if LANGKNOWPROP not in item.claims:
                pass
            elif item_instance not in HUMANINSTANCE:
                status = 'Error'
                pywikibot.error('{} is only supported for humans, not for {} ({}) with instance ({})'
                                .format(LANGKNOWPROP, label, qnumber, item_instance))
            elif (NATIVELANGPROP not in item.claims
                    and len(item.claims[LANGKNOWPROP]) == 1):
                target = get_item_page(item.claims[LANGKNOWPROP][0].getTarget())
                langid = target.getID()

                # Add missing natural language
                if (langid not in nat_languages
                        and INSTANCEPROP in target.claims
                        and not item_not_in_list(target.claims[INSTANCEPROP], lang_type_list)
                        and langid not in artificial_languages):      # Filter non-natural languages like Esperanto
                    nat_languages.add(langid)

                # Add one single mother tongue (natural languages)
                if langid not in nat_languages:
                    status = 'Error'
                    pywikibot.error('Unknown language {}'.format(langid))
                elif add_item_statement(item, NATIVELANGPROP, target, None):
                    status = 'Update'

            # What can we do with language used?
            # Countries, regios, events, organisations
            # https://www.wikidata.org/w/index.php?title=Wikidata%3AProperty_proposal%2Flanguage_used&diff=2203230193&oldid=351418037
            if WORKINGLANGPROP in item.claims:
                for claim in item.claims[WORKINGLANGPROP]:
                    target = get_item_page(claim.getTarget())
                    nat_languages.add(target.getID())           # Add a natural language

# (14) Handle missing statements
            for propty in missing_statement:
                if propty in item.claims and missing_statement[propty] not in item.claims:
                    # Can't automatically repair; only give error message
                    pywikibot.error('Statement {} ({}) required for property {} ({}) in item {} ({})'
                                    .format(get_property_label(missing_statement[propty]), missing_statement[propty],
                                            get_property_label(propty), propty,
                                            label, qnumber))

# Add reciproque statements for CEO, and chair
            for propty in ambt_list:
                if propty in item.claims:
                    for claim in item.claims[propty]:
                        val = claim.getTarget()
                        addedclaim = add_item_statement(val, AMBTPROP, ambt_list[propty], None)
                        if addedclaim:
                            qualifier = pywikibot.Claim(repo, QUALIFYFROMPROP)  ## Possibly obsolete??
                            qualifier.setTarget(item)
                            addedclaim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt + ' Qualifier of')

# (14) Handle conflicting statements
            doubtfull_items = set()
            if SUBCLASSPROP not in item.claims:
                # Identify forbidden statements
                for propty in conflicting_statement:
                    if propty in item.claims and conflicting_statement[propty] in item.claims:
                        item_list_1 = {claim.getTarget().getID()
                                       for claim in item.claims[propty]}
                        item_list_2 = {claim.getTarget().getID()
                                       for claim in item.claims[conflicting_statement[propty]]}
                        conf_item = item_list_1 & item_list_2
                        if conf_item:
                            # Can't decide which one is wrong...
                            doubtfull_items.update(conf_item)
                            pywikibot.warning('Item {} has possible conflict amongst property {}/{} ({}/{}) with {}'
                                              .format(qnumber,
                                                      get_property_label(propty),
                                                      get_property_label(conflicting_statement[propty]),
                                                      propty, conflicting_statement[propty], conf_item))
            elif INSTANCEPROP in item.claims:
                pywikibot.info('Both instance ({}) and subclass ({}) property for item {} ({})'
                               .format(INSTANCEPROP, SUBCLASSPROP, label, qnumber))

# (15) Identify mandatory statements
            for propty in mandatory_relation:
                if propty in item.claims:
                    for claim in item.claims[propty]:
                        sitem = claim.getTarget()
                        # Add symmetric and reciproque bidirectional statements
                        if (sitem and (mandatory_relation[propty] != propty
                                        # Beatles Q1299 contains versus John Lennon Q1203 member of
                                        and (propty not in likewise_relation or not property_is_in_list(sitem.claims, likewise_relation[propty]))
                                    or INSTANCEPROP in item.claims
                                        and INSTANCEPROP in sitem.claims
                                        and item.claims[INSTANCEPROP] == sitem.claims[INSTANCEPROP])
                                        ## Prevent conflictual assignments
                                        and sitem not in doubtfull_items
                                and add_item_statement(sitem, mandatory_relation[propty], item, claim.getSources())):
                            status = 'Update'

                if (mandatory_relation[propty] in item.claims
                        and mandatory_relation[propty] not in {propty, CHILDPROP, MAINSUBJECTPROP}):
                    # Reciproque unidirectional
                    for claim in item.claims[mandatory_relation[propty]]:
                        sitem = claim.getTarget()
                        if sitem and add_item_statement(sitem, propty, item, claim.getSources()):
                            status = 'Update'

# (16) Add symmetric relevant person statements
            ### Need more finetuning...
            if KEYRELATIONPROP in item.claims:
                # https://www.wikidata.org/wiki/Q336977#P3342 (correspondents of Guido Gezelle)
                for claim in item.claims[KEYRELATIONPROP]:
                    if (OBJECTROLEPROP in claim.qualifiers
                            # Correspondent
                            and claim.qualifiers[OBJECTROLEPROP][0].getTarget().getID() == CORRESPONDENTINSTANCE
                            and (KEYRELATIONPROP not in claim.getTarget().claims
                                 or not item_is_in_list(claim.getTarget().claims[KEYRELATIONPROP], [qnumber]))):

                        ### It is not sure that the relationship is symmetric
                        if False:
                            claim = pywikibot.Claim(repo, KEYRELATIONPROP)
                            claim.setTarget(item)
                            claim.getTarget().addClaim(claim, bot=wdbotflag, summary=transcmt + ' Add symmetric statement')
                            for qual in claim.qualifiers:
                                # Dates can be assymetric, so don't copy them
                                if qual not in time_props:
                                    qualifier = pywikibot.Claim(repo, qual)
                                    qualifier.setTarget(claim.qualifiers[qual][0].getTarget())
                                    claim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt + ' Add symmetric statement')
                                ### Reuse the reference?
                        else:
                            pywikibot.info('Possible missing symmetric statement {}:{} {} ({}) to {} ({})'
                                           .format(KEYRELATIONPROP, CORRESPONDENTINSTANCE,
                                                   get_item_header(item.labels), qnumber,
                                                   get_item_header(claim.getTarget().labels), claim.getTarget().getID()))

# (17) Add missing Wikimedia Commons SDC depicts statement
            #### https://commons.wikimedia.org/wiki/Commons:Bots/Requests/GeertivpBot#GeertivpBot_(overleg_%C2%B7_bijdragen)
            if cbotflag or newfunctions: add_missing_sdc_depicts(item)

# (18) Items has possibly been updated - Refresh item data
            label = get_item_header(item.labels)            # Get label (refresh label)
            descr = get_item_header(item.descriptions)      # Get description
            alias = get_item_header(item.aliases)           # Get alias

# (19) Asynchronous update Wikipedia pages
            # Queued update for Wikipedia Commonscat
            # Aim for 1 non-bot Wikipedia transaction per minute
            # It will not always be the same Wikipedia language
            while (commonscatqueue
                    and (datetime.now() - lastwpedit).total_seconds() > 30.0):
                # Get next record to process
                addcommonscat = commonscatqueue.pop()

                # Reconstruct the item data
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
                    wptemplatenamespace = sitelink.site.namespace(TEMPLATENAMESPACE)
                    if wptemplatenamespace != homewikitemplatenm:
                        wptemplatenamespace += ' (' + homewikitemplatenm + ')'
                    pageupdated = transcmt + ' Add'
                    item_instance = addcommonscat[2]

                    # Build template infobox list regular expression
                    infobox_template = '{{[^{]*Infobox|{{Wikidata|{{Persondata|{{Multiple image|{{Databox'

                    if sitelink.namespace == MAINNAMESPACE:
                        # Add language aliases
                        if lang in infobox_localname:
                            for val in infobox_localname[lang]:
                                if val not in infobox_template:
                                    infobox_template += '|{{[^{]*' + val

                        for ibox in range(len(infoboxlist)):
                            if sitelang in infoboxlist[ibox]:
                                infobox_template += '|{{' + infoboxlist[ibox][sitelang]

                        ## Add imagetemplatelist ??

##Infobox conditioneel maken -- te weinig of te veel statements

                        # Add an item-specific Wikidata infobox
                        len_specific_infoboxes = len(instance_types_by_category)
                        for ibox in range(len_specific_infoboxes):
                            if (sitelang in infoboxlist[ibox]     ## Hardcoded
                                    and item_instance in instance_types_by_category[ibox]
                                    and not re.search(infobox_template,
                                                      page.text, flags=re.IGNORECASE)):
                                addinfobox = infoboxlist[ibox][sitelang]
                                page.text = '{{' + addinfobox + '}}\n' + page.text
                                pageupdated += ' ' + addinfobox
                                if (mainlangwiki in infoboxlist[ibox]
                                        and infoboxlist[ibox][mainlangwiki] != addinfobox):
                                    addinfobox += ' (' + infoboxlist[ibox][mainlangwiki] + ')'
                                pywikibot.warning('Add {} {} to {}'
                                                  .format(wptemplatenamespace, addinfobox, sitelang))
                                break

                        # Add general Wikidata infobox, if there was no specific one
                        ## Depends on len(instance_types_by_category)
                        if (sitelang in infoboxlist[len_specific_infoboxes]
                                and not re.search(infobox_template,
                                                  page.text, flags=re.IGNORECASE)):
                            addinfobox = infoboxlist[len_specific_infoboxes][sitelang]
                            page.text = '{{' + addinfobox + '}}\n' + page.text
                            pageupdated += ' ' + addinfobox
                            if (mainlangwiki in infoboxlist[len_specific_infoboxes]
                                    and infoboxlist[len_specific_infoboxes][mainlangwiki] != addinfobox):
                                addinfobox += ' (' + infoboxlist[len_specific_infoboxes][mainlangwiki] + ')'
                            pywikibot.warning('Add {} {} to {}'
                                              .format(wptemplatenamespace, addinfobox, sitelang))

                    # Add one P18 missing image on the Wikipedia page
                    # https://doc.wikimedia.org/pywikibot/stable/api_ref/pywikibot.site.html#pywikibot.site._apisite.APISite.namespace
                    # Could we have other image or video properties?
                    # Could we have sound/video files?
                    # Could be applied in any namespace where items have Wikidata media files
                    if IMAGEPROP in item.claims and lang in item.labels:
                        # Get the first image from Wikidata
                        image_page = item.claims[IMAGEPROP][0].getTarget()
                        image_name = image_page.title()
                        file_name = image_name.split(':', 1)
                        wpfilenamespace = sitelink.site.namespace(FILENAMESPACE)
                        image_name = wpfilenamespace + ':' + file_name[1]
                        file_name_re = file_name[1].replace('(', r'\(').replace(')', r'\)')

                        file_template = r'\[\[' + wpfilenamespace + r':|\[\[File:|\[\[Image:|<gallery|</gallery>'

                        # Add language aliases
                        if lang in file_localname:
                            for val in file_localname[lang]:
                                if val not in file_template:
                                    file_template += r'|\[\[' + val + ':'

                        # Only add a first image, no image when there is an infobox
                        if not re.search(file_template
                                         + '|' + infobox_template  # Maybe this restriction is too hard
                                         # no File: because of possible Infobox parameter and gallery with automatic Wikidata image
                                         + '|' + file_name_re,
                                         page.text, flags=re.IGNORECASE):

                            # Determine local thumb name
                            # https://phabricator.wikimedia.org/T354230
                            image_flag = sitelink.site.getmagicwords('img_thumbnail')[0]

                            # Add translated 'upright' if height > 1.44 * width
                            try:
                                file_info = image_page.latest_file_info.__dict__
                                file_height = file_info['height']
                                file_width = file_info['width']
                                if file_height > file_width * 1.44:
                                    image_flag += '|' + sitelink.site.getmagicwords('img_upright')[0]
                            except:
                                pass    # Image size missing or incomplete

                            # Bots are not eligible, but it helps to track updates
                            pageupdated += ' image #WPWP #WPWPBE'
                            # Required: item language label
                            image_thumb = '[[{}|{}|{}]]'.format(image_name, image_flag, item.labels[lang])

                            # Verify header offset
                            headsearch = PAGEHEADRE.search(page.text)
                            if headsearch and re.search(infobox_template,
                                                        page.text, flags=re.IGNORECASE):
                                # Insert the picture after first head two, to allow for future infobox on top of the page
                                headoffset = headsearch.end()
                                page.text = page.text[:headoffset] + '\n' + image_thumb + page.text[headoffset:]
                            else:
                                # Put image top of page
                                page.text = image_thumb + '\n' + page.text
                            pywikibot.warning('Add media {} to {} {}:{}'
                                              .format(image_name, sitelang, lang, sitelink.title))

                    # Templates processing in normal order
                    inserttext = ''
                    referencetext = ''
                    authoritytext = ''
                    commonstext = ''
                    categorytext = ''

                    reftemplate = '<references/>'
                    # </references> must be first in order to avoid placement of redundant reference template
                    find_reference = '</references>|<references/>|<references />'

                    for ibox in range(len(referencelist)):
                        if sitelang in referencelist[ibox]:
                            # Take last reference template
                            reftemplate = '{{' + referencelist[ibox][sitelang] + '}}'
                            # Requires template terminator
                            find_reference += '|{{' + referencelist[ibox][sitelang].replace('|', r'\|') + '[^{]*}}'

                    # Add reference template
                    refreplace = re.search(find_reference, page.text, flags=re.IGNORECASE)
                    if (refreplace and reftemplate != '<references/>'
                                and refreplace.group(0).startswith('<references')
                                and sitelang not in veto_references     # Replace <references/> or add missing {{References}}
                            or not refreplace and REFTAGRE.search(page.text)):      # Missing references tag
                        referencetext = reftemplate
                        pageupdated += ' ' + reftemplate
                        if (mainlangwiki in referencelist[ibox]
                                and '{{' + referencelist[ibox][mainlangwiki] + '}}' != reftemplate):
                            reftemplate += ' (' + referencelist[ibox][mainlangwiki] + ')'
                        pywikibot.warning('Add {} {} to {}'
                                          .format(wptemplatenamespace, reftemplate, sitelang))

                    # Add an Authority control template for humans (+ other entities?)
                    if (item_instance in HUMANINSTANCE
                            and sitelang in authoritylist[0]):
                        skip_authority = '{{Authority control'

                        for ibox in range(len(authoritylist)):
                            if sitelang in authoritylist[ibox]:
                                skip_authority += '|{{' + authoritylist[ibox][sitelang]

                        if not re.search(skip_authority,
                                         page.text, flags=re.IGNORECASE):
                            authoritytemplate = authoritylist[0][sitelang]
                            authoritytext += '{{' + authoritytemplate + '}}'
                            pageupdated += ' ' + authoritytemplate
                            if mainlangwiki in authoritylist[0] and authoritylist[0][mainlangwiki] != authoritytemplate:
                                authoritytemplate += ' (' + authoritylist[0][mainlangwiki] + ')'
                            pywikibot.warning('Add {} {} to {}'
                                              .format(wptemplatenamespace, authoritytemplate, sitelang))

                    # Build portal template list regular expression
                    portal_template = '{{Portal|{{Navbox'
                    for ibox in range(len(portallist)):
                        if sitelang in portallist[ibox]:
                            portal_template += '|{{' + portallist[ibox][sitelang]

                    # To locate insert position
                    for ibox in range(3):
                        if sitelang in authoritylist[ibox]:
                            portal_template += '|{{' + authoritylist[ibox][sitelang]

                    # Prepare Commons Category logic
                    skip_commonscat = '{{Commons|' + portal_template
                    for ibox in range(len(commonscatlist)):
                        if sitelang in commonscatlist[ibox]:
                            skip_commonscat += '|{{' + commonscatlist[ibox][sitelang].split('|')[0]

                    # No Commonscat for Interproject links
                    for ibox in {1, 2}:
                        if sitelang in authoritylist[ibox]:
                            skip_commonscat += '|{{' + authoritylist[ibox][sitelang]

                    # No Commonscat for Infobox buildings
                    # Avoid duplicate Commons cat with human Infoboxes
                    skip_infobox_commonscat = ''
                    if sitelang in builtin_commonscat:
                        for ibox in builtin_commonscat[sitelang]:
                             if sitelang in infoboxlist[ibox]:
                                skip_infobox_commonscat += r'|{{' + infoboxlist[ibox][sitelang]

                    wpcommonscat = addcommonscat[3]
                    # Deactivate parentesis regex
                    wpcommonscat_re = wpcommonscat.replace('(', r'\(').replace(')', r'\)')

                    # Add Commonscat
                    if (wpcommonscat and sitelang in commonscatlist[0]
                            # Avoid complicated rules and exceptions
                            and sitelang not in veto_commonscat
                            # Commonscat already present
                            # Commons Category is only in English
                            and not re.search(skip_commonscat + skip_infobox_commonscat
                                              + r'|\[\[Category:' + wpcommonscat_re,
                                              page.text, flags=re.IGNORECASE)):

                        # Special section for Deutsch style Wikipedias
                        if (sitelang in commonssection
                                and not re.search(r'==\s*' + commonssection[sitelang] + r'\s*==',
                                                  page.text, flags=re.IGNORECASE)):
                            commonstext = '== ' + commonssection[sitelang] + ' ==\n'

                        # Add missing Commons Category
                        commonscatparam = commonscatlist[0][sitelang]
                        commonscatparamlist = commonscatparam.split('|')
                        if len(commonscatparamlist) > 1:
                            commonstext += '{{' + commonscatparam + wpcommonscat + '}}'
                        elif sitelink.title == wpcommonscat:
                            commonstext += '{{' + commonscatparam + '}}'
                        else:
                            commonstext += '{{' + commonscatparam + '|' + wpcommonscat + '}}'

                        commonscattemplate = commonscatparamlist[0]
                        pageupdated += ' [[c:Category:{1}|{0} {1}]]'.format(commonscattemplate, wpcommonscat)
                        if mainlangwiki in commonscatlist[0] and commonscatlist[0][mainlangwiki] != commonscattemplate:
                            commonscattemplate += ' (' + commonscatlist[0][mainlangwiki] + ')'
                        pywikibot.warning('Add {} {} {} to {}:{}'
                                          .format(wptemplatenamespace, commonscattemplate,
                                                  wpcommonscat, lang, sitelink.title))

                    sort_words = sitelink.site.getmagicwords('defaultsort')
                    # UK sort_words
                    # ['СТАНДАРТНЕ_СОРТУВАННЯ:_КЛЮЧ_СОРТУВАННЯ', 'СОРТИРОВКА_ПО_УМОЛЧАНИЮ', 'КЛЮЧ_СОРТИРОВКИ', 'DEFAULTSORT:', 'DEFAULTSORTKEY:', 'DEFAULTCATEGORYSORT:']

                    # Get sortwords
                    sort_word = sort_words[0]
                    if sort_word[-1] != ':':
                        sort_word += ':'

                    sort_template = '{{DEFAULTSORT:'
                    for val in sort_words:
                        if val[-1] != ':':
                            val += ':'
                        sort_template += '|{{' + val

                    if item_instance in HUMANINSTANCE and sitelang not in veto_defaultsort:
                        try:
                            # Only use DEFAULTSORT when having one single lastname
                            if (len(item.claims[LASTNAMEPROP]) == 1
                                    # In exceptional cases the name could be completely wrong (e.g. artist name versus official name)
                                    and not property_is_in_list(item.claims, alternative_person_names_props)):
                                ## Do we skip spaces or reorder lastnames when sorting?? Could be different amongst cultures, e.g. Nederland versus Vlaanderen with "van"
                                lastname = item.claims[LASTNAMEPROP][0].getTarget().labels[lang]

                                # Concatenate all firstnames
                                firstname = ''
                                for claim in item.claims[FIRSTNAMEPROP]:
                                    firstname += ' ' + claim.getTarget().labels[lang]
                                sortorder = lastname + ',' + firstname

                                skip_defaultsort = ''
                                if sitelang in authoritylist[3]:
                                    skip_defaultsort = '|{{' + authoritylist[3][sitelang]

                                if not re.search(sort_template + skip_defaultsort,
                                                 page.text, flags=re.IGNORECASE):
                                    categorytext = '{{' + sort_word + sortorder + '}}'
                                    pageupdated += ' ' + sort_word
                                    if 'DEFAULTSORT:' != sort_word:
                                        sort_word += ' (DEFAULTSORT) '
                                    pywikibot.warning('Add {} {}{} to {}'
                                                      .format(wptemplatenamespace, sort_word,
                                                              sortorder, sitelang))
                        except:
                            pass    # No firstname, or no lastname

                    # Add Wikipedia category, if it exists
                    wpcatpage = addcommonscat[4]
                    wpcatnamespace = sitelink.site.namespace(CATEGORYNAMESPACE)
                    wpcatpage_re = wpcatpage.replace('(', r'\(').replace(')', r'\)')
                    if (wpcatpage
                            # Wikipedia category must exist
                            and pywikibot.Category(sitelink.site, wpcatpage).text
                            and not re.search(r'\[\[' + wpcatnamespace + ':' + wpcatpage_re +
                                                r'|\[\[Category:' + wpcatpage_re,
                                              page.text, flags=re.IGNORECASE)):
                        # Good example: https://no.wikipedia.org/w/index.php?title=Port&diff=24164542&oldid=22515556
                        # Problem with category alias: https://za.wikipedia.org/w/index.php?title=Conghcueng&diff=41881&oldid=41498
                        if categorytext:
                            categorytext += '\n'
                        categorytext += '[[' + wpcatnamespace + ':' + wpcatpage + ']]'
                        pageupdated += ' [[:{}:{}]]'.format(wpcatnamespace, wpcatpage)
                        pywikibot.warning('Add {}:{} ({}) to {}:{}'
                                          .format(wpcatnamespace, wpcatpage,
                                                  'Category',       ## Should be mainlang
                                                  sitelang, sitelink.title))

                    # Save page when updated
                    if pageupdated == transcmt + ' Add':
                        pass                # Nothing changed
                    elif pageupdated == transcmt + ' Add ' + referencetext:
                        # Ignore changes, if only a reference template was added
                        pywikibot.warning('Skipping trivial changes for {}:{} ({})'
                                          .format(lang, get_item_header(item.labels), item.getID()))
                    else:
                        # Insert commonscat text for Deutsch
                        if sitelang not in commonssection:
                            pass                # Not for most Wikipedia languages
                        elif inserttext and commonstext:
                            inserttext += '\n' + commonstext
                        elif commonstext:
                            inserttext = commonstext

                        # Insert reference text for most Wikipedia languages
                        if sitelang in commonssection:
                            pass                # Not for for Deutsch
                        elif inserttext and referencetext:
                            inserttext = referencetext + '\n' + inserttext
                        elif referencetext:
                            inserttext = referencetext

                        # Insert authority text
                        if inserttext and authoritytext:
                            inserttext += '\n' + authoritytext
                        elif authoritytext:
                            inserttext = authoritytext

                        if inserttext:
                            # Portal template has precedence on first Category
                            navsearch = re.search(portal_template, page.text, flags=re.IGNORECASE)

                            # Insert the text at the best location
                            if (reftemplate != '<references/>' and refreplace and refreplace.group(0).startswith('<references')
                                    and sitelang not in veto_references):
                                # Replace <references/>
                                page.text = page.text[:refreplace.start()] + inserttext + page.text[refreplace.end():]
                                inserttext = ''
                            elif refreplace:
                                # Insert after references
                                page.text = page.text[:refreplace.end()] + '\n' + inserttext + page.text[refreplace.end():]
                                inserttext = ''
                            elif navsearch:
                                # Insert before navigation box
                                page.text = page.text[:navsearch.start()] + inserttext + '\n' + page.text[navsearch.start():]
                                inserttext = ''

                        # Insert reference text for Deutsch
                        if sitelang not in commonssection:
                            pass                # Not for most Wikipedia languages
                        elif inserttext and referencetext:
                            inserttext += '\n' + referencetext
                        elif referencetext:
                            inserttext = referencetext

                        # Insert commonscat text for most Wikipedia languages
                        if sitelang in commonssection:
                            pass
                        elif inserttext and commonstext:
                            inserttext += '\n' + commonstext
                        elif commonstext:
                            inserttext = commonstext

                        # Now possibly insert text for category, possibly remaining insert text
                        if inserttext and categorytext:
                            inserttext += '\n' + categorytext
                        elif categorytext:
                            inserttext = categorytext

                        if inserttext:
                            # Locate the first Category
                            # https://www.wikidata.org/wiki/Property:P373
                            # https://www.wikidata.org/wiki/Q4167836
                            catsearch = re.search(skip_commonscat + sort_template
                                                  + r'|\[\[' + wpcatnamespace
                                                  + r':|\[\[Category:',
                                                  page.text, flags=re.IGNORECASE)
                            if catsearch:
                                # Insert DEFAULTSORT and/or category
                                page.text = page.text[:catsearch.start()] + inserttext + '\n' + page.text[catsearch.start():]
                            else:
                                # Append DEFAULTSORT and/or category
                                page.text += '\n' + inserttext

                        # Cosmetic changes should only be done as side-effect of larger update

                        ### Problem with DEFAULTSORT not addded if status == 'Update' ??

                        # We do't change the DEFAULTSORT word
                        if False and sort_word != 'DEFAULTSORT:':   ## disabled
                            page.text = re.sub(r'{{DEFAULTSORT:', '{{' + sort_word, page.text)

                        # Trim trailing spaces (keep one -> parameter lists)
                        # Keep =space
                        # https://be.wikipedia.org/w/index.php?title=Канал_Грыбаедава&diff=next&oldid=4653417
                        page.text = re.sub(r' [ \t\r\f\v]+$', ' ', page.text, flags=re.MULTILINE)

                        # Remove redundant empty lines
                        page.text = re.sub(r'\n\n+', '\n\n', page.text)

                        # Remove useless code (bug in Visual editor)
                        page.text = re.sub(r'<nowiki/>', '', page.text)

                        if NOWIKIRE.search(page.text):
                            pywikibot.warning('<nowiki> tag found')

                        # Remove redundant spaces
                        page.text = re.sub(r'[.] +', '. ', page.text)               # Merge spaces after dot
                        page.text = re.sub(r' +</ref>', '</ref> ', page.text)       # No spaces before /ref
                        page.text = re.sub(r'</ref> +', '</ref> ', page.text)       # Single spaces after references
                        page.text = re.sub(r'</ref> [.]', '</ref>.', page.text)     # No trailing space after reference

                        page.text = re.sub(r'<ref> +', '<ref>', page.text)          # No spaces after ref
                        page.text = re.sub(r' +<ref>', ' <ref>', page.text)         # Single space before ref
                        if sitelang not in veto_spacebeforeref:
                            page.text = re.sub(r' <ref>', '<ref>', page.text)       # No space before ref

                        try:
                            # We can save not the updates
                            pywikibot.warning('Saving {}:{} ({})'
                                              .format(lang, get_item_header(item.labels), item.getID()))
                            page.save(summary=pageupdated)      # Bot flag is automatic
                            lastwpedit = datetime.now()
                        except Exception as error:
                            # Ignore Wikipedia errors
                            pywikibot.error('Error saving Wikipedia page {}:{} ({}), {}'
                                            .format(lang, get_item_header(item.labels), item.getID(), error))

# (20) Error handling
        except KeyboardInterrupt:
            pdb.set_trace()
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 130)

        except AttributeError as error:
            pywikibot.error(error)      # NoneType error
            pdb.set_trace()
            # https://www.wikidata.org/wiki/Q17382244#P2562
            status = 'NoneType'
            errcount += 1
            exitstat = max(exitstat, 12)

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

        except pywikibot.exceptions.UnknownSiteError as error:
            pywikibot.warning(error)      # Site error
            unset_wikis.add(sitelang)
            ##pdb.set_trace()
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
            ###raise
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

        if True or status not in {'OK'}:		# Print transaction results
            isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Needed to format output
            totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
            pywikibot.info('{:d}\t{}\t{:.3f}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'
                           .format(transcount, isotime, totsecs, status,
                                   qnumber, label, mainwikipediapage,
                                   commonscat, alias, nationality, birthday, deathday, descr))


def show_help_text():
    """Show program help and exit (only show head text)"""
    helptxt = HELPRE.search(codedoc)
    if helptxt:
        pywikibot.info(helptxt[0])	# Show helptext
    sys.exit(1)                     # Must stop


def get_next_param():
    """Get the next command parameter, and handle any qualifiers
    """

    global forcecopy
    global errwaitfactor
    global exitfatal
    global lead_lower
    global lead_upper
    global newfunctions
    global overrule
    global repldesc
    global repeatmode
    global uselabels

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
    elif cpar.startswith('-s'):	# single mode
        repeatmode = False
        print('Setting repeat mode')
    elif cpar.startswith('-u'):	# leading lowercase
        lead_lower = True
        print('Setting leading lowercase')
    elif cpar.startswith('-x'):	# experimental functions
        newfunctions = True
        print('Activate experimental functions')
    elif cpar.startswith('-U'):	# leading uppercase
        lead_upper = True
        print('Setting leading uppercase')
    elif cpar.startswith('-'):	# unrecognized qualifier (fatal error)
        pywikibot.critical('Unrecognized qualifier; use -h for help')
        sys.exit(4)
    return cpar		# Return the parameter or the qualifier to the caller


# Main program entry
now = datetime.now()	    # Refresh the timestamp to time the following transaction
try:
    pgmnm = sys.argv.pop(0)	        # Get the name of the executable
    pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
except:
    shell = False
    pywikibot.info('{}, {}, {}, {} ({})'
                   .format(modnm, pgmid, pgmlic, creator, 'No shell available'))

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

HELPRE = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
LANGRE = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes
NAMEREVRE = re.compile(r',(\s*.*)*$')	    # Reverse lastname, firstname
NOWIKIRE = re.compile(r'<nowiki>')  	    # Reverse lastname, firstname
PSUFFRE = re.compile(r'\s*\(.*\)$')		    # Remove trailing () suffix (keep only the base label)
PAGEHEADRE = re.compile(r'(==.+==)')        # Page headers with templates
QSUFFRE = re.compile(r'Q[0-9]+')            # Q-number
REFTAGRE = re.compile(r'<ref>(.+)</ref>')   # Require reference tag
ROMANRE = re.compile(r'^[a-z/0-9() .,"\'åáàâäāæǣçéèêëėíìîïıńñŋóòôöœøřśßúùûüýÿĳ-]{2,}$', flags=re.IGNORECASE)        # Roman alphabet
SHORTDESCRE = re.compile(r'{{Short description\|(.+)}}', flags=re.IGNORECASE)

# Commons Category + Wikidata infobox
COMMONSCATREDIRECTRE = re.compile(r'{{Category|{{Cat disambig|{{Catredir|Cat-redirect', flags=re.IGNORECASE)    # Including: Category redirect
WDINFOBOXRE = re.compile(r'{{Wikidata infobox', flags=re.IGNORECASE)

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

mainlangwiki = mainlang + 'wiki'
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

# Print preferences
pywikibot.log('Languages:\t{} {}'.format(mainlang, main_languages))
pywikibot.log('Maximum delay:\t{:d} s'.format(maxdelay))
pywikibot.log('Use labels:\t{}'.format(uselabels))
pywikibot.log('Instance descriptions:\t{}'.format(repldesc))
pywikibot.log('Force copy:\t{}'.format(forcecopy))
pywikibot.log('Exit on fatal error:\t{}'.format(exitfatal))
pywikibot.log('Error wait factor:\t{:d}'.format(errwaitfactor))

# Connect to databases
site = pywikibot.Site('commons')
site.login()
cbotflag = 'bot' in pywikibot.User(site, site.user()).groups()

# This script requires a bot flag
repo = site.data_repository()
repo.login()
wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

# Get local template namespace name
homewiki = pywikibot.Site(mainlang, 'wikipedia')
homewiki.login()
homewikibotflag = 'bot' in pywikibot.User(homewiki, homewiki.user()).groups()

# List of official function items
ambt_list = {
    CEOPROP: pywikibot.ItemPage(repo, 'Q484876'),
    CHAIRPROP: pywikibot.ItemPage(repo, 'Q1255921'),
    DIRECTORPROP: pywikibot.ItemPage(repo, 'Q1162163'),
}

# Get Wikimedia labels in the local language
pywikibot.info('Loading local language labels')
infobox_localname = get_item_label_dict('Q15515987')    # Infobox

# https://ast.wikipedia.org/w/index.php?title=Conventu&diff=4106220&oldid=3704719
### https://www.wikidata.org/w/index.php?title=Q82753&diff=2044443528&oldid=2012500870
file_localname = get_item_label_dict('Q82753')          # File

representationtypelabel = get_property_label(REPRESENTATIONTYPEPROP)
homewikitemplatenm = homewiki.namespace(TEMPLATENAMESPACE)

"""
pywikibot.info('Loading living language code mapping')
### We should probably reverste P1 and P3 (or omit P1 ??)
qnumbers_lang = get_dict_using_statement_value(INSTANCEPROP, 'Q1288568', WIKIMEDIALANGCDPROP)
#qnumbers_lang = {'Q716686': 'trv', 'Q32238': 'dag', 'Q715766': 'tay', 'Q8641': 'yi', 'Q36850': 'tw', 'Q35132': 'ami', 'Q3241618': 'rkt', 'Q33173': 'ctg', 'Q25167': 'nb', 'Q382273': 'hno', 'Q36163': 'ku', 'Q3111668': 'guw', 'Q13351': 'moe', 'Q8765': 'an', 'Q716695': 'xsy', 'Q13293': 'sma', 'Q715755': 'pwn', 'Q8786': 'gsw-fr', 'Q29919': 'arz', 'Q33454': 'ff', 'Q25164': 'nn', 'Q56426': 'ary', 'Q33578': 'ig', 'Q34737': 'agq', 'Q35936': 'ilo', 'Q56505': 'bnn', 'Q56475': 'ha', 'Q33810': 'or', 'Q387066': 'als', 'Q56590': 'atj', 'Q34311': 'yo', 'Q34219': 'wa', 'Q36510': 'el', 'Q13248': 'hsb', 'Q33954': 'sg', 'Q9307': 'gl', 'Q33947': 'se', 'Q9051': 'lb', 'Q12107': 'br', 'Q3436689': 'bzs', 'Q13275': 'so', 'Q8097': 'te', 'Q56322': 'smj', 'Q33291': 'fon', 'Q28026': 'ak', 'Q35978': 'hil', 'Q5137': 'gu', 'Q33537': 'lkt', 'Q13267': 'si', 'Q1751432': 'pdt', 'Q716690': 'pyu', 'Q36236': 'ml', 'Q9309': 'cy', 'Q9296': 'mk', 'Q33823': 'ne', 'Q676492': 'ssf', 'Q9260': 'tg', 'Q29401': 'as', 'Q9083': 'lt', 'Q1571': 'mr', 'Q7033959': 'yue', 'Q29507': 'ast', 'Q33350': 'ce', 'Q9063': 'sl', 'Q180945': 'hyw', 'Q9072': 'et', 'Q27776': 'ady', 'Q7918': 'bg', 'Q9058': 'sk', 'Q33673': 'kn', 'Q33491': 'ht', 'Q34057': 'tl', 'Q9217': 'th', 'Q33965': 'sat', 'Q6654': 'hr', 'Q9078': 'lv', 'Q1617': 'ur', 'Q33239': 'ceb', 'Q718269': 'szy', 'Q9091': 'be', 'Q9237': 'ms', 'Q9199': 'vi', 'Q9056': 'cs', 'Q35853': 'kab', 'Q33845': 'nap', 'Q9043': 'no', 'Q33287': 'gaa', 'Q8752': 'eu', 'Q9301': 'sh', 'Q27175': 'fy', 'Q8108': 'ka', 'Q33549': 'jv', 'Q33973': 'scn', 'Q9240': 'id', 'Q36109': 'mai', 'Q8748': 'sq', 'Q32724': 'vec', 'Q33587': 'ki', 'Q294': 'is', 'Q7838': 'sw', 'Q33070': 'ban', 'Q9166': 'mt', 'Q5885': 'ta', 'Q9142': 'ga', 'Q56483': 'lki', 'Q9246': 'mn', 'Q100103': 'vls', 'Q14185': 'oc', 'Q8785': 'hy', 'Q33856': 'pap', 'Q29540': 'bar', 'Q14549': 'sco', 'Q13389': 'ba', 'Q36495': 'nan', 'Q25285': 'tt', 'Q33475': 'gan', 'Q33868': 'mni', 'Q809': 'pl', 'Q33628': 'loz', 'Q7913': 'ro', 'Q9264': 'uz', 'Q1568': 'hi', 'Q9067': 'hu', 'Q33281': 'cbk-zam', 'Q14196': 'af', 'Q33270': 'hoc', 'Q34024': 'pcd', 'Q9292': 'az', 'Q9610': 'bn', 'Q9035': 'da', 'Q36126': 'kv', 'Q36368': 'ku', 'Q33879': 'pag', 'Q9255': 'ky', 'Q34257': 'wo', 'Q33368': 'lg', 'Q13216': 'za', 'Q33120': 'bxr', 'Q36451': 'mi', 'Q28244': 'am', 'Q34174': 'rif', 'Q9027': 'sv', 'Q56485': 'wym', 'Q5218': 'qu', 'Q10179': 'zu', 'Q8798': 'uk', 'Q33997': 'sd', 'Q256': 'tr', 'Q7026': 'ca', 'Q34271': 'bo', 'Q9176': 'ko', 'Q33638': 'mnc', 'Q9252': 'kk', 'Q13286': 'dsb', 'Q34340': 'st', 'Q33902': 'skr', 'Q33000': 'bfi', 'Q33390': 'cr', 'Q7850': 'zh', 'Q33348': 'cv', 'Q28224': 'frr', 'Q13238': 'udm', 'Q36811': 'ckb', 'Q25433': 'nds', 'Q36663': 'urh', 'Q36212': 'ltg', 'Q9168': 'fa', 'Q9288': 'he', 'Q102172': 'li', 'Q9205': 'km', 'Q13218': 'xh', 'Q1412': 'fi', 'Q33284': 'bcl', 'Q36979': 'wls', 'Q33573': 'rw', 'Q34137': 'tn', 'Q34152': 'shi', 'Q25258': 'fo', 'Q29952': 'myv', 'Q56240': 'tu', 'Q12953315': 'yav', 'Q36209': 'kum', 'Q32979': 'cho', 'Q9267': 'tk', 'Q30007': 'ext', 'Q13271': 'sms', 'Q29921': 'iu', 'Q13199': 'rm', 'Q13201': 'rmy', 'Q36583': 'sei', 'Q14759': 'ase', 'Q32145': 'ksh', 'Q5146': 'pt', 'Q58635': 'pa', 'Q9314': 'gd', 'Q34179': 'ydg', 'Q33243': 'bm', 'Q7411': 'nl', 'Q9129': 'el', 'Q33720': 'krj', 'Q1405077': 'kj', 'Q30005': 'ee', 'Q143': 'eo', 'Q32762': 'vro', 'Q9228': 'my', 'Q32704': 've', 'Q33013': 'dua', 'Q36280': 'mh', 'Q34299': 'sah', 'Q33111': 'co', 'Q7930': 'mg', 'Q33388': 'chr', 'Q36147': 'lus', 'Q237409': 'zea', 'Q523014': 'mus', 'Q652': 'it', 'Q33657': 'glk', 'Q30319': 'szl', 'Q34029': 'yap', 'Q36106': 'lij', 'Q25355': 'kl', 'Q13321': 'mic', 'Q35377': 'efi', 'Q33274': 'shy', 'Q33976': 'sc', 'Q18415595': 'dty', 'Q33754': 'lmo', 'Q36217': 'ln', 'Q56499': 'arq', 'Q33509': 'inh', 'Q33205': 'bfq', 'Q36943': 'wal', 'Q34002': 'su', 'Q34279': 'war', 'Q13359': 'xmf', 'Q3027953': 'srq', 'Q56547': 'umu', 'Q33522': 'kbd', 'Q10199': 'diq', 'Q13324': 'min', 'Q36435': 'uun', 'Q34243': 'yoi', 'Q33989': 'srn', 'Q33223': 'brx', 'Q13955': 'ar', 'Q5287': 'ja', 'Q150': 'fr', 'Q34142': 'tsg', 'Q33690': 'csb', 'Q257829': 'bqi', 'Q33552': 'ks', 'Q26245': 'rue', 'Q56428': 'nrf-gg', 'Q33900': 'ng', 'Q34138': 'tum', 'Q35963': 'kea', 'Q33575': 'kjh', 'Q33557': 'krl', 'Q10729616': 'aoc', 'Q13198': 'rcf', 'Q3912765': 'kcg', 'Q165795': 'fkv', 'Q33375': 'hak', 'Q32952': 'ccp', 'Q33890': 'nso', 'Q25289': 'kw', 'Q36699': 'pis', 'Q36196': 'lad', 'Q36494': 'quc', 'Q13357': 'fit', 'Q2937525': 'cps', 'Q34247': 'yai', 'Q27183': 'ik', 'Q33268': 'bh', 'Q1321': 'es', 'Q7737': 'ru', 'Q938216': 'khw', 'Q5111': 'ab', 'Q188': 'de', 'Q35475': 'kbp', 'Q58680': 'ps', 'Q152965': 'sli', 'Q33441': 'fur', 'Q13330': 'mwl', 'Q32747': 'vep', 'Q12175': 'gv', 'Q33968': 'os', 'Q178440': 'fa-af', 'Q65455884': 'rwr', 'Q36392': 'mo', 'Q25442': 'wen', 'Q254950': 'ovd', 'Q33081': 'dz', 'Q33295': 'fj', 'Q13310': 'nv', 'Q33656': 'sjd', 'Q34327': 'ts', 'Q1160372': 'lzz', 'Q49232': 'dru', 'Q29579': 'awa', 'Q15085': 'pms', 'Q1815020': 'akz', 'Q13263': 'ug', 'Q33262': 'ch', 'Q56648': 'bsa', 'Q4627': 'ay', 'Q34318': 'tly', 'Q33569': 'haw', 'Q1991779': 'alt', 'Q3287253': 'sjm', 'Q34233': 'ryu', 'Q33049': 'bal', 'Q33060': 'bla', 'Q35704': 'krx', 'Q56466': 'din', 'Q34251': 'tcy', 'Q33335': 'kjg', 'Q28378': 'anp', 'Q3573199': 'yum', 'Q584983': 'lag', 'Q33661': 'mfe', 'Q11159532': 'tsk', 'Q33875': 'oj', 'Q34806': 'bss', 'Q33265': 'chy', 'Q36094': 'kr', 'Q33315': 'hz', 'Q35655': 'ses', 'Q36584': 'olo', 'Q56232': 'acm', 'Q6695015': 'lex', 'Q8047534': 'mis-x-Q8047534', 'Q36206': 'lbe', 'Q36459': 'nui', 'Q33698': 'liv', 'Q33434': 'kut', 'Q12952626': 'kbg', 'Q9211': 'lo', 'Q716681': 'tsu', 'Q27811': 'aa', 'Q770547': 'lvk', 'Q1057898': 'egl', 'Q29561': 'av', 'Q8773': 'akl', 'Q34119': 'tyv', 'Q33583': 'rn', 'Q33190': 'bug', 'Q15087': 'frp', 'Q34208': 'wbl', 'Q2982063': 'pjt', 'Q33462': 'smn', 'Q29316': 'rup', 'Q13356': 'mzn', 'Q33786': 'sid', 'Q34128': 'ty', 'Q33273': 'ny', 'Q3915357': 'fuf', 'Q33730': 'arn', 'Q13307': 'na', 'Q13343': 'mdf', 'Q1365342': 'yec', 'Q33357': 'crh', 'Q33584': 'kha', 'Q30898': 'gil', 'Q35876': 'gn', 'Q27567': 'abq', 'Q33864': 'om', 'Q35115': 'cak', 'Q56482': 'shn', 'Q716627': 'ckv', 'Q34004': 'sn', 'Q33303': 'hai', 'Q33170': 'ckt', 'Q34124': 'ti', 'Q34055': 'tvl', 'Q1704302': 'nsk', 'Q33979': 'new', 'Q716615': 'bzg', 'Q34011': 'sm', 'Q33457': 'gag', 'Q1860': 'en', 'Q7689158': 'tvn', 'Q10188': 'zun', 'Q56509': 'adx', 'Q34235': 'ii', 'Q20822': 'ttm', 'Q36323': 'pko', 'Q18546266': 'nqo', 'Q6346422': 'cgc', 'Q35744': 'kri', 'Q13349': 'mnw', 'Q36452': 'yrk', 'Q36705': 'sth', 'Q31091048': 'tce', 'Q36202': 'lld', 'Q56601': 'khg', 'Q33714': 'krc', 'Q13365': 'mwv', 'Q33871': 'nog', 'Q891085': 'guc', 'Q32656': 'dv', 'Q12952748': 'luz', 'Q23014': 'pfl', 'Q34040': 'tru'}

# Transpose and merge/overrule
for qnumber in qnumbers_lang:
    lang_qnumbers[qnumbers_lang[qnumber]] = qnumber
pywikibot.log(lang_qnumbers)
"""

# Build list of natural languages
for lang in lang_qnumbers:
    nat_languages.add(lang_qnumbers[lang])

# Build veto languages ID
##main_languages_id = [lang_qnumbers[lang] for lang in main_languages]
for lang in veto_languages:
    if lang in lang_qnumbers:   # comment to check completeness
        veto_languages_id.add(lang_qnumbers[lang])

# Load list of infoboxes automatically (first 4 must be in strict sequence)
dictnr = 0
infoboxlist = {}
for item_dict in sitelink_dict_list:
    infoboxlist[dictnr] = get_wikipedia_sitelink_template_dict(item_dict)
    dictnr += 1

# Manual corrections

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

# Disallow general Wikidata infoboxes with problems
dictnr += 1
infoboxlist[dictnr] = {}
for sitelang in veto_infobox:
    if sitelang in infoboxlist[3]:
        infoboxlist[dictnr][sitelang] = infoboxlist[3][sitelang]
        del(infoboxlist[3][sitelang])

# Manual exclusions
dictnr += 1
infoboxlist[dictnr] = {
    'altwiki': 'Кӧл',               # Infobox https://alt.wikipedia.org/w/index.php?title=Гейзер_кӧл&action=history
    'arzwiki': 'صندوق معلومات كاتب',
    'astwiki': 'Persona',
    'avkwiki': 'Suterotik2',
    'azwiki': 'Rəqs',               # No Wikidata
    'bswiki': 'Infokutija',         # Multiple templates
    'euwiki': 'Biografia',          # Multiple templates
    'fiwiki': 'Kirjailija',
    'fywiki': 'Artyst',             # https://fy.wikipedia.org/w/index.php?title=Kees_van_Kooten&diff=1114402&oldid=1114401&diffmode=source
    'ruwiki': 'Однофамильцы',       # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=prev&oldid=129491499&diffmode=source
    'srwiki': 'Infokutija',         # Multiple templates
    'tgwiki': 'Варақаи футболбоз',  # https://tg.wikipedia.org/w/index.php?title=Михаил_Шишкин_%28футболбоз%29&diff=1414806&oldid=1414805
    'ukwiki': 'Unibox',             # https://uk.wikipedia.org/w/index.php?title=Сюанський_папір&diff=39931612&oldid=37227693
    'uzwiki': 'Shaxsiyat',          # https://uz.wikipedia.org/w/index.php?title=Peter_Thiel&diff=3990073&oldid=3990069
    'xmfwiki': 'ინფოდაფა მენცარი',     # https://xmf.wikipedia.org/w/index.php?title=კეტრინ_ჯონსონი&diff=194620&oldid=194619&diffmode=source
    'yiwiki': 'אנפירער',            # https://yi.wikipedia.org/w/index.php?title=אדאלף_היטלער&diff=588334&oldid=588333&diffmode=source
}

dictnr += 1
infoboxlist[dictnr] = {
    'altwiki': 'Озеро',             # Infobox alias https://alt.wikipedia.org/w/index.php?title=Гейзер_кӧл&action=history
    'arzwiki': 'معلومات كنيسة',     # https://arz.wikipedia.org/w/index.php?title=كنيسه_سانت_كليمنت_(فولكيستون_اند_هيث,_المملكه_المتحده)&diff=prev&oldid=8920530
    'euwiki': '[^{]+ infotaula',       # Regex wildcard
    'srwiki': 'Glumac-lat',         # Multiple templates
    'ukwiki': 'Кулінарна страва',
}

dictnr += 1
infoboxlist[dictnr] = {
    'arzwiki': 'معلومات مبنى',      # https://arz.wikipedia.org/w/index.php?title=برج_تورون_المايل&diff=8922695&oldid=8922688
    'srwiki': 'Скијаш',             # Alias for Q8086987 Infobox skier
}

dictnr += 1
infoboxlist[dictnr] = {
    'arzwiki': 'معلومات رياضي',    # https://arz.wikipedia.org/w/index.php?title=جيلبيرت_ديسميت&diff=10206314&oldid=10206311
}

dictnr += 1
pywikibot.info('{:d} Wikipedia infoboxes loaded'.format(dictnr))

# Reference template lists; highest ranked gets priority
referencelist = {}                  # Replace <references /> by References
referencelist[0] = get_wikipedia_sitelink_template_dict('Q5462890')     # References, 32 s
referencelist[1] = get_wikipedia_sitelink_template_dict('Q10991260')    # Appendix
referencelist[2] = {                # Manual overrides
'nlwiki': 'Appendix|refs',
'nnwiki': 'Reflist'
}

# Mandatory commonscat section
# Conditionally insert "== Weblinks ==" for dewiki commonscat
commonssection = {
    'dewiki': 'Weblinks',       # https://de.wikipedia.org/wiki/Wikipedia:Formatvorlage_Biografie
    'lbwiki': 'Um Spaweck',     # https://lb.wikipedia.org/w/index.php?title=Joseph_Jongen&diff=2489919&oldid=2489918
}

# List of authority control
authoritylist = {}

# Index 0..2 is used for searching navigation box and portal

# Specific index 0
# Add authority infobox
authoritylist[0] = get_wikipedia_sitelink_template_dict('Q3907614')     # Add Authority control, 1s

# Specific index 1
# No Commonscat for Interproject links
authoritylist[1] = get_wikipedia_sitelink_template_dict('Q5830969')     # Interproject template, 4 s
authoritylist[1]['euwiki']  = 'Autoritate kontrola'          # https://eu.wikipedia.org/w/index.php?title=Westgate_(Canterbury)&diff=prev&oldid=9518658

# Specific index 2
# No Commonscat
authoritylist[2] = {            # Manual exclusions
    'astwiki': 'NF',
    'eswiki': 'Control de autoridades',
    'euwiki': 'Bizialdia',
    'lmowiki': 'Interproget',  # Alias 'Interprogett'
    'lvwiki': 'Sisterlinks-inline',           # Q26098003
    'mdfwiki': 'Ломань',        # Q6249834
}
# Specific index 3
# Lifetime template; skip adding DEFAULTSORT
authoritylist[3] = get_wikipedia_sitelink_template_dict('Q6171224')     # Livetime, 1 s

# Manual exclusions (mainly aliases)
authoritylist[4] = {
    'arzwiki': 'ضبط استنادي',   # alias for [0]
    'bewiki': 'Бібліяінфармацыя',
    'frwiki': 'Bases',          # Liens = Autorité + Bases
    'ruwiki': 'BC',             # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=129492269&oldid=129491434&diffmode=source
    'tgwiki': 'ПБ',             # alias https://tg.wikipedia.org/w/index.php?title=Дейл_Карнегӣ&diff=1404168&oldid=1392239
    'ukwiki': 'Нормативний контроль',   # https://uk.wikipedia.org/w/index.php?title=Пітер_Тіль&diff=41204517&oldid=41204504
}

# Exeptional manual exclusions
authoritylist[5] = {}
for sitelang in veto_authority:
    authoritylist[5][sitelang] = authoritylist[0][sitelang]
    del(authoritylist[0][sitelang])

# No Authority with References
authoritylist[5]['nlwiki'] = referencelist[0]['nlwiki']

# Overrule Authority templates
# Enforce frwiki == Liens externes ==
### Ereg Replace {{Bases}} or {{Autorité}} by {{Liens}}
# or by '' when {{Liens}} is already there
authoritylist[0]['frwiki'] = 'Liens'

# Get the Commonscat template names
commonscatlist = {}
commonscatlist[0] = get_wikipedia_sitelink_template_dict('Q48029')      # Commonscat, 7 s
commonscatlist[1] = get_wikipedia_sitelink_template_dict('Q5462387')    # Commons
commonscatlist[2] = get_wikipedia_sitelink_template_dict('Q5830425')    # Commons category-inline

# Manual exclusions
commonscatlist[3] = {
    'arzwiki': 'لينكات مشاريع شقيقه',   # https://arz.wikipedia.org/w/index.php?title=روجر_رافيل&diff=8088053&oldid=8088052&diffmode=source
    'astwiki': 'Enllaces',
    'bewiki': 'Пісьменнік',
    'bgwiki': 'Личност',            # Q6249834 Personality infobox has a builtin Commonscat
    'hywiki': 'Տեղեկաքարտ Խաչքար',  # Q26042874
    'itwiki': 'Interprogetto',      # https://it.wikipedia.org/w/index.php?title=Palazzo_dei_Principi-Vescovi_di_Liegi&diff=132888315&oldid=132888272&diffmode=source
    'nowiki': 'Offisielle lenker',  # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot
    'ruwiki': 'BC',                 # https://ru.wikipedia.org/w/index.php?title=Верлинден%2C_Аннелис&diff=129492269&oldid=129491434&diffmode=source
    'ukwiki': 'універсальна картка',
    'urwiki': 'زمرہ کومنز',         # https://ur.wikipedia.org/w/index.php?title=درخت&diff=5654151&oldid=5653922
}

# Other manual exclusions
commonscatlist[4] = {
    'hywiki': 'Տեղեկաքարտ Խաչքար',  # Q26042874
    'nowiki': 'Offisielt nettsted', # https://no.wikipedia.org/wiki/Brukerdiskusjon:GeertivpBot (redirect)
    'urwiki': 'زمرہ العام',         # https://ur.wikipedia.org/w/index.php?title=درخت&diff=5654151&oldid=5653922
    'cewiki': 'НБМ-Росси',          # Infobox https://ce.wikipedia.org/w/index.php?title=Акташ_%28Республика_Алтай%29&diff=10106442&oldid=10106441
}

# Overrule Commonscat templates
commonscatlist[3]['frwiki'] = commonscatlist[0]['frwiki']
commonscatlist[0]['frwiki'] = 'Autres projets|commons=Category:'

# Get the portal template list
portallist = {}
portallist[0] = get_wikipedia_sitelink_template_dict('Q5153')       # Portal, 1 s
portallist[1] = get_wikipedia_sitelink_template_dict('Q5030944')    # Navbox, 2 s

# Manual inclusions
portallist[2] = {
    'nlwiki': 'Portaal',
}

portallist[3] = {
    'nlwiki': 'Navigatie',
}

# Templates with autopicture from Wikidata
imagetemplatelist = {}

pywikibot.info('Wikipedia templates loaded')

commonscatqueue = []        # FIFO list
transcount = 0	    	    # Total transaction counter
prevnow = now	        	# Transaction status reporting
now = datetime.now()	    # Refresh the timestamp to time the following transaction
lastwpedit = now + timedelta(seconds=-30)       # In principle 1 Wikipedia edit per minute
totsecs = int((now - prevnow).total_seconds())	# Elapsed time for this transaction
pywikibot.info('{:d} seconds to initialise\nReady for processing'.format(totsecs))

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
