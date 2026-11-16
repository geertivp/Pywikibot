#!/usr/bin/python3

codedoc = """
Create a new lastname

Parameters:

    P1, P2...: optional additional claims (possibility to overrule default claims)

    Examples:

        P1705 nl    label in oorspronkelijke taal

    stdin: the list of lastnames, one per line

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
    3 Invalid or missing parameter
    10 Homonym
    13 Maxlag error
    20 Page save error
    30 General error
    40 Function not implemented
    130 Ctrl-c pressed, program interrupted

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

    pip install cologne-phonetics
    pip install jellyfish
    pip install phonetisch

Fallback solution:

    sudo -s
    apt install python3-full
    python3 -m venv /opt/python

    /opt/python/bin/pip install cologne-phonetics

    /opt/python/bin/pwb create_lastname

Functionality:

    Only the mul-label is stored
    https://www.wikidata.org/wiki/Help:Default_values_for_labels_and_aliases

    Do not store obvious item descriptions
    https://phabricator.wikimedia.org/T303677

Author:

	Geert Van Pamel, 2021-01-06, MIT License, User:Geertivp

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string
    https://pypi.org/project/cologne-phonetics/
    https://github.com/maxwellium/cologne-phonetic
    https://maxwellium.github.io/cologne-phonetic/
    https://en.wikipedia.org/wiki/Cologne_phonetics

Known problems:

    Duplicates could possibly be created due to augmented replication delays.

"""

import cologne_phonetics
import jellyfish        # soundex
import os               # Operating system: getenv
import pdb              # Python debugger
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import unidecode        # Unicode

from datetime import datetime	    # now, strftime, delta time, total_seconds
from phonetisch import caverphone   ## Bug in library (lowercases)
from pywikibot.data import api

# Global variables
modnm = 'Pywikibot create_lastname'     # Module name (using the Pywikibot package)
pgmid = '2026-03-28 (gvp)'	    # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

# Technical configuration flags
# Defaults: transparent and safe
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
shell = True		# Shell available (command line parameters are available; automatically overruled by PAWS)
createmode = False	# Show the generated SPARQL code (activate with -c)

# Technical parameters

"""
    Default error penalty wait factor (can be overruled with -f).
    Larger values ensure that maxlag errors are avoided, but temporarily delay processing.
    It is advised not to overrule this value.
"""
exitstat = 0        # (default) Exit status
errwaitfactor = 4	# Extra delay after error; best to keep the default value (maximum delay of 4 x 150 = 600 s = 10 min)
maxdelay = 150		# Maximum error delay in seconds (overruling any extreme long processing delays)

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

# Wikidata transaction comment
transcmt = '#pwb Create lastname'	    # Wikidata transaction comment

# Functional configuration flags
MULANG = 'mul'
MAINLANG = 'en:mul'

# Properties
INSTANCEPROP = 'P31'
SUBCLASSPROP = 'P279'
SCRIPTPROP = 'P282'
COMMONSCATPROP = 'P373'
LASTNAMEPROP = 'P734'
NATIVELANGLABELPROP = 'P1705'
CAVERPHONEPROP = 'P3880'        # https://www.wikidata.org/wiki/Property_talk:P3880
SOUNDEXPROP = 'P3878'
KOLNPHONEPROP = 'P3879'
INFIXPROP = 'P7377'

# Instances
LATINSCRIPTINSTANCE = 'Q8229'
LASTNAMEINSTANCE = 'Q101352'                    # familienaam
DOUBLELASTNAMEINSTANCE = 'Q29042997'
LASTNAMESUBCLASSINSTANCE = 'Q121493679'         # achternaam
LASTNAMEHYPHNINSTANCE = 'Q106319018'            # hyphen
LASTNAMETOPONYMINSTANCE = 'Q17143070'           # toponym
LASTNAMECOMPOUNDINSTANCE = 'Q60558422'          # compound
LASTNAMEAFFIXINSTANCE = 'Q66480858'             # affix

lastname_instances = {LASTNAMEINSTANCE, DOUBLELASTNAMEINSTANCE, LASTNAMEAFFIXINSTANCE, LASTNAMECOMPOUNDINSTANCE, LASTNAMESUBCLASSINSTANCE, LASTNAMETOPONYMINSTANCE, LASTNAMEHYPHNINSTANCE}

# Validation rules
propreqinst = {
    LASTNAMEPROP: lastname_instances,
}


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

        # Return mul label when present
        if MULANG in header:
            return header[MULANG]

        # Return any other label (no specific order?)
        for lang in header:
            return header[lang]
    # No label present
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


def item_is_in_list(statement_list, itemlist):
    """
    Verify if statement list contains at least one item from the itemlist
    param: statement_list: Statement list
    param: itemlist:      List of values
    return: Matching or empty string
    """
    for seq in statement_list:
        try:
            isinlist = seq.getTarget().getID()
            if isinlist in itemlist:
                return isinlist
        except:
            pass    # Ignore NoneType error
    return ''


def get_item_list(item_name: str, instance_id) -> set():
    """Get list of items by name, belonging to an instance (list)

    :param item_name: Item name (string)
    :param instance_id: Instance ID (set, or list)
    :return: Set of items

    See https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    """
    item_name = item_name.strip()
    pywikibot.log('Search label: {} {}'.format(item_name.encode('utf-8'), instance_id))
    item_list = set()                   # Empty set
    params = {'action': 'wbsearchentities',
              'search': item_name,      # Get item list from label
              'type': 'item',
              'language': mainlang,     # Labels are in native language
              'uselang': mainlang,
              'strictlanguage': False,  # All languages are searched
              'format': 'json',
              'limit': 20}              # Should be reasonable value; could possibly be increased
    request = api.Request(site=repo, parameters=params)
    result = request.submit()
    pywikibot.debug(result)

    if 'search' in result:
        # Ignore accents and case
        item_name_canon = item_name
        for row in result['search']:                    # Loop though items
            ##print(row)
            item = get_item_page(row['id'])

            # Matching instance, strict equal comparison
            # Remark that most items have a proper instance
            if SUBCLASSPROP not in item.claims and (
                    INSTANCEPROP not in item.claims
                    or item_is_in_list(item.claims[INSTANCEPROP], instance_id)):
                # Search all languages
                for lang in item.labels:
                    if item_name_canon == item.labels[lang]:
                        item_list.add(item)     # Label match
                        break
                for lang in item.aliases:
                    for seq in item.aliases[lang]:
                        if item_name_canon == seq:
                            item_list.add(item) # Alias match
                            break
    pywikibot.log(item_list)
    # Convert set to list; keep sort order (best matches first)
    return list(item_list)


def wd_proc_all_items():
    """
    Main procedure
    """

    global exitstat

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    errcount = 0	    	# Error counter
    errsleep = 15	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    pywikibot.info('Processing %d statements' % (len(itemlist)))

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for newitem in itemlist:	# Main loop for all DISTINCT items
      if  status == 'Stop':	    # Ctrl-c pressed -> stop in a proper way
        break

      objectname = ' '.join(newitem.replace('_', ' ').split()).strip()
      if not objectname:
        continue
      elif not ROMANRE.search(objectname):
        status = 'Skip'
        errcount += 1
        exitstat = max(exitstat, 3)
        pywikibot.error('Bad name: {}'.format(objectname))
      else:
        transcount += 1	# New transaction
        status = 'OK'
        label = {}
        alias = []
        commonscat = '' # Commons category
        nationality = ''
        qnumber = ''    # In case or error

        try:
            # Get all matching items
            name_list = get_item_list(objectname, propreqinst[LASTNAMEPROP])
            ##pdb.set_trace()

            if len(name_list) == 1 and INSTANCEPROP not in name_list[0].claims:
                # Every item must have an instance, can't be overruled by -c
                status = 'Instance'
                pywikibot.error('Missing instance for {} ({}) -- please add instance manually and rerun'.format(
                                get_item_header(name_list[0].labels), name_list[0].getID()))
            elif len(name_list) == 1 and not createmode:
                # Update the lastname
                status = 'Update'
                item = name_list.pop()
                qnumber = item.getID()

                # Merge labels
                if MULANG not in item.labels:
                    item.labels[MULANG] = objectname              # Add language code
                elif objectname == item.labels[MULANG]:
                    pass
                elif MULANG not in item.aliases:
                    item.aliases[MULANG] = [objectname]           # Add alias
                elif objectname not in item.aliases[MULANG]:
                    item.aliases[MULANG].append(objectname)       # Merge aliases

                # Merge aliases
                if mainlang in item.aliases:
                    for seq in item.aliases[mainlang]:
                        if '(' not in seq:
                            if MULANG not in item.aliases:
                                item.aliases[MULANG] = [seq]
                            elif seq not in item.aliases[MULANG]:
                                item.aliases[MULANG].append(seq)

                # Enforce mul labels
                """
                ## Not yet agreed by community...
                for lang in item.labels:
                    if lang != MULANG and item.labels[lang] == objectname:
                        item.labels[lang] = ''
                """

                """
                ## Bad idea
                for lang in item.aliases:
                    while item.labels[MULANG] in item.aliases[lang]:
                        item.aliases[lang].remove(item.labels[MULANG])
                """

                # Remove redundant aliases
                for lang in item.labels:
                    if lang in item.aliases:
                        while item.labels[lang] in item.aliases[lang]:
                            item.aliases[lang].remove(item.labels[lang])

                item.editEntity({'labels': item.labels, 'aliases': item.aliases},
                                summary=transcmt, bot=wdbotflag)
            elif name_list and not createmode:
                status = 'Ambiguous'            # Item is not unique
                for item in name_list:
                    try:
                        item_instance = items.claims[INSTANCEPROP][0].getTarget()
                        item_type = get_item_header(item_instance.labels)
                    except:
                        item_instance = None
                        item_type = 'lastname'
                    pywikibot.error('{} {} ({}) {} ({})'.format(
                                        status, item_type, item_instance,
                                        get_item_header(item.labels), item.getID()))
            else:
                # Create the lastname, either because empty list, or -c qualifier
                label[MULANG] = objectname

                try:
                    item = pywikibot.ItemPage(repo)         # Create item
                    item.editLabels(labels=label, summary=transcmt, bot=wdbotflag)
                    qnumber = item.getID()
                    pywikibot.warning('Created lastname {} ({})'.format(objectname, qnumber))
                except pywikibot.exceptions.OtherPageSaveError as error:
                    pywikibot.error('Error creating {}, {}'.format(objectname, error))
                    status = 'Error'	    # Handle any generic error
                    errcount += 1
                    exitstat = max(exitstat, 10)

            if status in {'OK', 'Update'}:
                # Merge the statements
                # Set the language label
                targetx[NATIVELANGLABELPROP].text = objectname

                # Amend item if value is not already registered
                for propty in targetx:
                    if propty not in item.claims:
                        claim = pywikibot.Claim(repo, propty)
                        claim.setTarget(targetx[propty])
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                        # Should confirm?

                # Add the soundex codes
                # https://www.wikidata.org/wiki/Wikidata:Property_proposal/phonetic_algorithms
                soundcodes = {
                    ### Problem: bug in library? (lowercases)
                    ## https://www.wikidata.org/w/index.php?title=Q26736114&diff=2441443986&oldid=2441443920
                    ## https://phabricator.wikimedia.org/T414024
                    ##CAVERPHONEPROP: ['caverphone', caverphone.encode_word(objectname)],
                    KOLNPHONEPROP: ['Köhl phonetic', cologne_phonetics.encode(objectname)[0][1]],
                    SOUNDEXPROP: ['soundex', jellyfish.soundex(objectname)],
                    # Metaphone: https://www.wikidata.org/wiki/Q1925103
                }

                for soundcode in soundcodes:
                    if soundcode not in item.claims:
                        soundval = soundcodes[soundcode][1]
                        claim = pywikibot.Claim(repo, soundcode)
                        claim.setTarget(soundval)
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                        pywikibot.warning('Add {}: {}'.format(soundcodes[soundcode][0], soundval))

                # Search the affixes
                for name_prefix in name_prefix_list:
                    if objectname.startswith(name_prefix + ' '):
                        break
                else:
                    name_prefix = ''

                if name_prefix:
                    if not item_is_in_list(item.claims[INSTANCEPROP], [LASTNAMEAFFIXINSTANCE]):
                        claim = pywikibot.Claim(repo, INSTANCEPROP)
                        claim.setTarget(affix_namex)
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)

                    if INFIXPROP not in item.claims:
                        claim = pywikibot.Claim(repo, INFIXPROP)
                        claim.setTarget(name_prefix_list[name_prefix])
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)

                    # Need to verify on toponym first
                    if False and not item_is_in_list(item.claims[INSTANCEPROP], [LASTNAMETOPONYMINSTANCE]):
                        claim = pywikibot.Claim(repo, INSTANCEPROP)
                        claim.setTarget(toponym_namex)
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)

                # Try to assign Commons Category
                commonscat = objectname + ' (surname)'
                page = pywikibot.Category(site, commonscat)
                if not page.text:
                    # Category page does not exist (yet)
                    pywikibot.info('Empty Wikimedia Commons category page: {}'.format(commonscat))
                    commonscat = ''
                elif COMMONSCATREDIRECTRE.search(page.text) and not COMMONSCATTOCRE.search(page.text):
                    # Should only assign real Category pages
                    pywikibot.warning('Redirect Wikimedia Commons category page: {}'
                                      .format(commonscat))
                    commonscat = ''
                elif 'commonswiki' not in item.sitelinks:
                    # Try to create a Wikimedia Commons Category sitelink
                    try:
                        sitedict = {'site': 'commonswiki', 'title': page.title()}
                        item.setSitelink(sitedict, bot=wdbotflag, summary=transcmt + ' Add sitelink')
                        status = 'Commons'
                    except pywikibot.exceptions.OtherPageSaveError as error:
                        # Category already assigned to other item
                        # Get unique Q-numbers, skip duplicates (order not guaranteed)
                        itmlist = set(QSUFFRE.findall(str(error)))
                        if qnumber in itmlist:
                            itmlist.remove(qnumber)

                        # Silently pass if Category page does not exist
                        if itmlist:
                            # Category was not assigned due to ambiguity
                            pywikibot.info('Category:{} ({}) conflicting with {}'
                                           .format(commonscat, qnumber, itmlist))
                            status = 'DupCat'	    # Conflicting category statement
                            errcount += 1
                            exitstat = max(exitstat, 10)
                        commonscat = ''

                if commonscat:
                    if cbotflag and not WDINFOBOXRE.search(page.text):
                        # Add Wikidata Infobox to Wikimedia Commons Category
                        pageupdated = transcmt + ' Add Wikidata Infobox'
                        page.text = '{{Wikidata Infobox}}\n' + re.sub(r'[ \t\r\f\v]+$', '', page.text, flags=re.MULTILINE)
                        pywikibot.warning('Add {} template to Commons {}'
                                          .format('Wikidata Infobox', page.title()))
                        page.save(summary=pageupdated, minor=True)
                        status = 'Commons'

                    # Add missing category statement
                    if COMMONSCATPROP not in item.claims:
                        claim = pywikibot.Claim(repo, COMMONSCATPROP)
                        claim.setTarget(commonscat)
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)

# (14) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 130)

        except pywikibot.exceptions.MaxlagTimeoutError as error:  # Attempt error recovery
            deltasecs = int((datetime.now() - now).total_seconds())	# Calculate technical error penalty
            pywikibot.error('Error after {:d} seconds for {}, {}'.format(deltasecs, qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 13)
            ## Should we have a fatal error?
            sys.exit(exitstat)
            if deltasecs >= 30: 	# Technical error; for transactional errors there is no wait time increase
                errsleep += errwaitfactor * min(maxdelay, deltasecs)
                # Technical errors get additional penalty wait
				# Consecutive technical errors accumulate the wait time, until the first successful transaction
				# We limit the delay to a multitude of maxdelay seconds
            if errsleep > 0:    	# Allow the servers to catch up; slowdown the transaction rate
                pywikibot.error('{:d} seconds maxlag wait'.format(errsleep))
                time.sleep(errsleep)

        except pywikibot.exceptions.OtherPageSaveError as error:  # Page save error
            pywikibot.error('Error updating %s, %s' % (qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 20)
            ## Should we have a fatal error?
            sys.exit(exitstat)

        except Exception as error:  # other exception to be used
            pywikibot.error('Error updating %s, %s' % (qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 30)
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

        isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Only needed to format output
        totsecs = (now - prevnow).total_seconds()	# Elapsed time for this transaction
        pywikibot.info('{:d}\t{}\t{:.3f}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'
                       .format(transcount, isotime, totsecs, status, qnumber, objectname,
                               commonscat, alias, nationality, descr[mainlang]))


def show_help_text():
# Show program help and exit (only show head text)
    helptxt = HELPRE.search(codedoc)
    if helptxt:
        pywikibot.info(helptxt.group(0))	# Show helptext
    sys.exit(1)         # Must stop


def get_next_param():
    """
    Get the next command parameter, and handle any qualifiers
    """

    global createmode
    global errwaitfactor
    global exitfatal

    cpar = sys.argv.pop(0)	    # Get next command parameter

    if cpar.startswith('-c'):	# code check
        createmode = True
        print('Create mode')
    elif cpar.startswith('-h'):	# help
        show_help_text()
    elif cpar.startswith('-m'):	# fast mode
        errwaitfactor = 1
        print('Setting fast mode')
    elif cpar.startswith('-p'):	# proceed after fatal error
        exitfatal = False
        print('Setting proceed after fatal error')
    elif cpar.startswith('-'):	# unrecognized qualifier (fatal error)
        fatal_error(4, 'Unrecognized qualifier; use -h for help')
    return cpar		# Return the parameter or the qualifier to the caller


"""
    Start main program logic
"""
now = datetime.now()	# Start the main transaction timer

# Print the module name
pywikibot.info('{}, {}, {}, {}'.format(modnm, pgmid, pgmlic, creator))

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    pywikibot.info('{}'.format(pgmnm))
except:
    shell = False
    pywikibot.warning('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

HELPRE = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
PROPRE = re.compile(r'(P[0-9]+)')           # P-number
QSUFFRE = re.compile(r'(Q[0-9]+)')          # Q-number
ROMANRE = re.compile(r'^[a-z \'åáàâäāæǣçéèêëėíìîïıńñŋóòôöœøřśßúùûüýÿĳ-]{2,}$', flags=re.IGNORECASE)  # Roman alphabet

# Commons Category + Wikidata infobox
COMMONSCATREDIRECTRE = re.compile(r'{{Cat disambig|{{Catredir|Cat-redirect|{{Category', flags=re.IGNORECASE)    # Including: Category redirect
COMMONSCATTOCRE = re.compile(r'{{Category TOC', flags=re.IGNORECASE)    # Including: Category redirect
WDINFOBOXRE = re.compile(r'{{Wikidata infobox', flags=re.IGNORECASE)

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

# Will be translated to items at runtime
name_prefix_list = {
    ##'Al': 'Q37526065',
    'De': 'Q135906281',
    'de': 'Q11071485',
    'Van': 'Q69876093',
    'van': 'Q69872130',
    'Von': 'Q70084230',
    'von': 'Q69870160',
    ## should be extended
}

inpar = '-'
while sys.argv and inpar.startswith('-'):
    inpar = get_next_param()

# Print preferences
pywikibot.log('Main language:\t%s' % mainlang)
pywikibot.log('Maximum delay:\t%d s' % maxdelay)
pywikibot.log('Create mode:\t%s' % createmode)
pywikibot.log('Exit on fatal error:\t%s' % exitfatal)
pywikibot.log('Error wait factor:\t%d' % errwaitfactor)

try:
    # Connect to database
    init_phase = 'Login'
    site = pywikibot.Site('commons')
    site.login()
    cbotflag = 'bot' in pywikibot.User(site, site.user()).groups()

    # This script requires a bot flag
    repo = site.data_repository()
    repo.login()
    wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

    # Set base statements
    init_phase = 'Data'
    targetx = {
        INSTANCEPROP: get_item_page(LASTNAMEINSTANCE),
        SCRIPTPROP: get_item_page(LATINSCRIPTINSTANCE),
        NATIVELANGLABELPROP: pywikibot.WbMonolingualText(text='None', language=MULANG),
    }

    while sys.argv and not inpar.startswith('-'):
        # Get all claims from parameter list
        propty = PROPRE.findall(inpar.upper())[0]
        proptypage = pywikibot.PropertyPage(repo, propty)
        inpar = sys.argv.pop(0)
        if proptypage.type == 'wikibase-item':
            targetx[propty] = get_item_page(QSUFFRE.findall(inpar.upper())[0])
        elif proptypage.type == 'monolingualtext':
            ## Should get textual parameters as well (e.g. P1705)
            ## Default NATIVELANGLABELPROP MULANG
            targetx[propty] = pywikibot.WbMonolingualText(text='None', language=inpar)
        else:
            fatal_error(40, 'Property type {} not supported for {} ({})'
                           .format(proptypage.type, get_item_header(proptypage.labels), propty))

        if sys.argv:
            inpar = sys.argv.pop(0)

    # Show the (template) statements
    for propty in targetx:
        proptyx = pywikibot.PropertyPage(repo, propty)
        proptypage = pywikibot.PropertyPage(repo, propty)
        if proptypage.type == 'wikibase-item':
            pywikibot.info('Statement {} ({}) {} ({})'.format(
                           get_item_header(proptyx.labels), propty,
                           get_item_header(targetx[propty].labels), targetx[propty].getID()))
        elif proptypage.type == 'monolingualtext':
            pywikibot.info('Statement {} ({}) {} ({})'.format(
                           get_item_header(proptyx.labels), propty,
                           targetx[propty].text, targetx[propty].language))

    # Get language descriptions
    descr = {}
    instance_item = targetx[INSTANCEPROP]
    for lang in instance_item.labels:
        descr[lang] = instance_item.labels[lang]              # Get language labels

    # Item pages
    affix_namex = get_item_page(LASTNAMEAFFIXINSTANCE)
    toponym_namex = get_item_page(LASTNAMETOPONYMINSTANCE)

    # Get lastname prefix items
    for name_prefix in name_prefix_list:
        name_prefix_list[name_prefix] = get_item_page(name_prefix_list[name_prefix])

    deltasecs = int((datetime.now() - now).total_seconds())
    pywikibot.info('{:d} seconds to initialise'.format(deltasecs))

    # Get list of item numbers
    inputfile = sys.stdin.read()
    itemlist = sorted(set(inputfile.splitlines()))
    pywikibot.debug(itemlist)

    wd_proc_all_items()	    # Execute all items for one language

    """
        Print all sitelinks (base addresses)
        PAWS is using tokens (passwords can't be used because Python scripts are public)
        Shell is using passwords (from user-password.py file)
    """
    for site in sorted(pywikibot._sites.values()):
        if site.username():
            pywikibot.debug('{}\t{}\t{}\t{}'
                        .format(site, site.username(), site.is_oauth_token_available(), site.logged_in()))
except Exception as error:
    # Other exception to be used
    #raise
    fatal_error(20, '{} error, {}'.format(init_phase, error))

sys.exit(exitstat)

"""
