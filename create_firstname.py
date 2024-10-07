#!/usr/bin/python3

codedoc = """
Create a new firstname

Parameters:

    P1: gender

    stdin: the list of firstnames

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
	2 Ctrl-c pressed, program interrupted (multiple Ctrl-c are required when in language update mode)
    3 Invalid or missing parameter
    13 Maxlag error
    20 General error

Prequisites:

    Install Pywikibot client software; see https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial

    pip install cologne-phonetics
    pip install jellyfish
    pip install phonetisch

Author:

	Geert Van Pamel, 2021-01-06, MIT License, User:Geertivp

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string

Known problems:

    Duplicates can possibly be created due to augmented replication delays.

"""

# List the required modules
import cologne_phonetics
import jellyfish        # soundex
import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import urllib.parse     # URL encoding/decoding (e.g. Wikidata Query URL)

from datetime import datetime	# now, strftime, delta time, total_seconds
from phonetisch import caverphone
from pywikibot.data import api

# Global variables
modnm = 'Pywikibot create_firstname'    # Module name (using the Pywikibot package)
pgmid = '2024-10-07 (gvp)'	    # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

"""
    Static definitions
"""

# Technical configuration flags
MAINLANG = 'en:mul'

# Defaults: transparent and safe
errorstat = True    # Show error statistics (disable with -e)
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
readonly = False    # Dry-run
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

# Wikidata transaction comment
transcmt = '#pwb Create firstname'	    # Wikidata transaction comment

INSTANCEPROP = 'P31'
COMMCATPROP = 'P373'
NATIVELANGLABELPROP = 'P1705'
CAVERPHONPROP = 'P3880'
SOUNDEXPROP = 'P3878'
KOLNPHONPROP = 'P3879'


def fatal_error(errcode, errtext):
    """
    A fatal error has occurred; we will print the error messaga, and exit with an error code
    """
    global exitstat

    exitstat = max(exitstat, errcode)
    pywikibot.critical(errtext)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        pywikibot.warning('Proceed after fatal error')


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


def wd_proc_all_items():
    """
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

# Avoid that the user is waiting for a response while the data is being queried
    if verbose:
        pywikibot.info('Processing %d statements' % (len(itemlist)))

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for newitem in itemlist:	# Main loop for all DISTINCT items
      if  status == 'Stop':	    # Ctrl-c pressed -> stop in a proper way
        break

      objectname = ' '.join(newitem.split())
      if QSUFFRE.search(objectname):
        status = 'Skip'
        errcount += 1
        exitstat = max(exitstat, 3)
        pywikibot.error('Bad name: %s' % (objectname))
      elif objectname > "'":
        transcount += 1	# New transaction
        status = 'OK'
        label = {}
        alias = []
        commonscat = '' # Commons category
        nationality = ''
        qnumber = ''    # In case or error

        try:			# Error trapping (prevents premature exit on transaction error)

            # Check if item already exists
            params = {'action': 'wbsearchentities',
                      'format': 'json',
                      'language': mainlang,
                      'type': 'item',
                      'search': objectname}
            request = api.Request(site=repo, parameters=params)
            result = request.submit()

            pywikibot.debug(result)
            instance = None
            if 'search' in result:
                for row in result['search']:
                    item = pywikibot.ItemPage(repo, row['id'])
                    try:
                        item.get()
                    except pywikibot.exceptions.IsRedirectPageError:
                        # Resolve a single redirect error
                        item = item.getRedirectTarget()
                        pywikibot.warning('Item {} redirects to {}'.format(row['id'], item.getID()))

                    if INSTANCEPROP in item.claims:
                        for seq in item.claims[INSTANCEPROP]:       # Get instance
                            instance = seq.getTarget()
                            if instance.getID() in [target[INSTANCEPROP], 'Q3409032']:
                                for lang in item.labels:
                                    if objectname == item.labels[lang]:     ##accent fallback??
                                        status = 'Update'
                                        break
                                if status == 'Update':
                                    break
                                for lang in item.aliases:
                                    if objectname in item.aliases[lang]:    ##accent fallback??
                                        status = 'Update'
                                        break
                                if status == 'Update':
                                    break
                        if status == 'Update':
                            break

            if instance and instance.getID() == 'Q3409032':
                status = 'Gender'
                errcount += 1
                exitstat = max(exitstat, 3)
                pywikibot.error('Non-gender firstname {} ({}) exists'
                                .format(objectname, item.getID()))
            elif status == 'Update':
                # Update item labels
                qnumber = item.getID()
                lang = 'mul'
                if lang not in item.labels:
                    item.labels[lang] = objectname
                elif objectname == item.labels[lang]:
                    pass
                elif lang not in item.aliases:
                    item.aliases[lang] = [objectname]
                elif objectname not in item.aliases[lang]:
                    item.aliases[lang].append(objectname)

                """
                # https://phabricator.wikimedia.org/T303677
                # Add description
                for lang in descr:
                    if lang not in item.descriptions:
                        item.descriptions[lang] = descr[lang]
                """
                # Remove redundant aliases
                # Should also enforce mul labels
                for lang in item.labels:
                    if lang in item.aliases:
                        while item.labels[lang] in item.aliases[lang]:
                            item.aliases[lang].remove(item.labels[lang])

                item.editEntity( {'labels': item.labels}, summary=transcmt)
            elif not ROMANRE.search(objectname):
                status = 'Skip'
                errcount += 1
                exitstat = max(exitstat, 3)
                pywikibot.error('Bad name: {}'.format(objectname))
            elif len(objectname.split() > 1):
                status = 'Skip'
                errcount += 1
                exitstat = max(exitstat, 3)
                pywikibot.error('Multipe firstnames: {}'.format(objectname))
            elif status == 'OK':
                # Create item
                label['mul'] = objectname

                try:
                    item = pywikibot.ItemPage(repo)
                    item.editEntity( {'labels': label}, summary=transcmt)
                    qnumber = item.getID()
                    pywikibot.warning('Created firstname {} ({})'
                                      .format(objectname, qnumber))

                except pywikibot.exceptions.OtherPageSaveError as error:
                    pywikibot.error('Error creating {}, {}'.format(objectname, error))
                    status = 'Error'	        # Handle any generic error
                    errcount += 1
                    exitstat = max(exitstat, 10)

            if status in ['OK', 'Update']:
                # Add missing claims
                for propty in targetx:
                    propstatus = 'OK'
                    if propty in item.claims:
                        for seq in item.claims[propty]:
                            val = seq.getTarget().getID()
                            if val == target[propty]:
                                propstatus = 'Skip'
                                break
                            else:
                                propstatus = 'other'
                                pywikibot.warning('Possible conflicting statement {}:{} - {} for {}'
                                                  .format(propty, target[propty], val.getID(), qnumber))

                    if propstatus == 'OK':
                        claim = pywikibot.Claim(repo, propty)
                        claim.setTarget(targetx[propty])
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                        # Should confirm

                # Label in official language
                if NATIVELANGLABELPROP not in item.claims:
                    claim = pywikibot.Claim(repo, NATIVELANGLABELPROP)
                    claim.setTarget(pywikibot.WbMonolingualText(text=objectname, language='mul'))
                    item.addClaim(claim, summary=transcmt)
                    pywikibot.warning('Adding native name: {}'.format(objectname))

                if SOUNDEXPROP not in item.claims:
                    soundex = jellyfish.soundex(objectname)
                    claim = pywikibot.Claim(repo, SOUNDEXPROP)
                    claim.setTarget(soundex)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning('Adding soundex: {}'.format(soundex))

                if KOLNPHONPROP not in item.claims:
                    colnphon = cologne_phonetics.encode(objectname)[0][1]
                    claim = pywikibot.Claim(repo, KOLNPHONPROP)
                    claim.setTarget(colnphon)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning('Adding Köhl phonetic: {}'.format(colnphon))

                if CAVERPHONPROP not in item.claims:
                    caverphon = caverphone.encode_word(objectname)
                    claim = pywikibot.Claim(repo, CAVERPHONPROP)
                    claim.setTarget(caverphon)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning('Adding caverphone: {}'.format(caverphon))

                commonscat = objectname + ' (given name)'
                if 'commonswiki' in item.sitelinks:
                    sitelink = item.sitelinks['commonswiki']
                    commonscat = sitelink.title
                    colonloc = commonscat.find(':')
                    if colonloc >= 0:
                        commonscat = commonscat[colonloc + 1:]
                else:
                    # Create commonscat
                    page = pywikibot.Category(site, commonscat)
                    if cbotflag and not page.text:
                        pageupdated = transcmt + ' Add Wikidata Infobox'
                        page.text = '{{Wikidata Infobox}}'
                        pywikibot.warning('Add {} template to Commons {}'
                                          .format('Wikidata Infobox', page.title()))
                        page.save(summary=pageupdated, minor=True, bot=True) ##, bot=cbotflag) ## got multiple values for keyword argument 'bot'
                        status = 'Infobox'

                    sitedict = {'site': 'commonswiki', 'title': 'Category:' + commonscat}
                    try:
                        item.setSitelink(sitedict, bot=wdbotflag, summary='#pwb Add sitelink')
                        status = 'Commons'
                        ## Run copy_label for item number
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

                if commonscat and COMMCATPROP not in item.claims:
                    claim = pywikibot.Claim(repo, COMMCATPROP)
                    claim.setTarget(commonscat)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)

# (14) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 2)

        except pywikibot.exceptions.MaxlagTimeoutError as error:  # Attempt error recovery
            pywikibot.error('Error updating %s, %s' % (qnumber, error))
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
                pywikibot.error('%d seconds maxlag wait' % (errsleep))
                time.sleep(errsleep)

        except Exception as error:  # other exception to be used
            pywikibot.error('Error processing %s, %s' % (qnumber, error))
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
            pywikibot.info('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, qnumber, objectname, commonscat, alias, nationality, descr[mainlang]))


def show_help_text():
# Show program help and exit (only show head text)
    helptxt = helpre.search(codedoc)
    if helptxt:
        pywikibot.info(helptxt.group(0))	# Show helptext
    sys.exit(9)         # Must stop


def show_prog_version():
# Show program version
    pywikibot.info('{}, {}, {}, {}'.format(modnm, pgmid, pgmlic, creator))


def get_next_param():
    """
    Get the next command parameter, and handle any qualifiers
    """

    global errwaitfactor
    global exitfatal
    global readonly
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter

    if cpar.startswith('-e'):	# error stat
        errorstat = False
        pywikibot.info('Disable error statistics')
    elif cpar.startswith('-h'):	# help
        show_help_text()
    elif cpar.startswith('-m'):	# fast mode
        errwaitfactor = 1
        pywikibot.info('Setting fast mode')
    elif cpar.startswith('-p'):	# proceed after fatal error
        exitfatal = False
        pywikibot.info('Setting proceed after fatal error')
    elif cpar.startswith('-q'):	# quiet mode
        verbose = False
        pywikibot.info('Setting quiet mode')
    elif cpar.startswith('-r'):	# readonly mode
        readonly = True
        pywikibot.info('Setting readonly mode')
    elif cpar.startswith('-v'):	# verbose mode
        verbose = True
        pywikibot.info('Setting verbose mode')
    elif cpar.startswith('-V'):	# Version
        show_prog_version()
    elif cpar.startswith('-'):	# unrecognized qualifier (fatal error)
        fatal_error(4, 'Unrecognized qualifier; use -h for help')
    return cpar		# Return the parameter or the qualifier to the caller


if verbose:
    show_prog_version()	    	# Print the module name

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
except:
    shell = False
    pywikibot.warning('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""

helpre = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
humsqlre = re.compile(r'\s*#.*\n')          # Human readable query, remove all comments including LF
comsqlre = re.compile(r'\s+')		        # Computer readable query, remove duplicate whitespace
urlbre = re.compile(r'[^\[\]]+')	        # Remove URL square brackets (keep the article page name)
suffre = re.compile(r'\s*[(,]')		        # Remove () and , suffix (keep only the base label)
langre = re.compile(r'^[a-z]{2,3}$')        # Verify for valid ISO 639-1 language codes
QSUFFRE = re.compile(r'[Qq][0-9]+')         # Q-number

gender = '-'
while sys.argv and gender.startswith('-'):
    gender = get_next_param()

# Get all claims from parameter list
target={INSTANCEPROP:'Q12308941', 'P282':'Q8229'}
targetx={}

if gender[:1] in 'fvw':
    target[INSTANCEPROP] = 'Q11879590'  # Female
    descr = {'af':'vroulike voornaam', 'ast':'nome femenín', 'bar':'Weiwanam', 'br':"anv merc'hed", 'bs':'žensko ime', 'ca':'prenom femení', 'cs':'ženské rodné jméno', 'cy': 'enw personol benywaidd', 'da': 'pigenavn', 'de': 'weiblicher Vorname', 'en': 'female given name', 'eo':'virina persona nomo', 'es': 'nombre femenino', 'et':'naisenimi', 'eu':'emakumezko izen', 'fr': 'prénom féminin', 'fy':'famkesnamme', 'gl':'nome feminino', 'gsw':'wyblige Vorname', 'hr':'žensko ime', 'hsb':'žónske předmjeno', 'hu':'női utónév', 'id':'nama perempuan feminin', 'is':'kvenmannsnafn', 'it': 'prenome femminile', 'la':'praenomen femininum', 'lb':'weibleche Virnumm', 'lt':'moteriškas vardas', 'lv':'sieviešu personvārds', 'nb': 'kvinnenavn', 'nl': 'vrouwelijke voornaam', 'nn':'kvinnenamn', 'pl':'imię żeńskie', 'pt': 'nome próprio feminino', 'sc': 'female gien name', 'scn':'nomu di battìu fimmininu', 'sco':'female gien name', 'sk':'ženské krstné meno', 'sl':'žensko osebno ime', 'sq':'emër femëror', 'sv': 'kvinnonamn', 'tr':'kadın adı'}
elif gender[:1] in 'hm':
    target[INSTANCEPROP] = 'Q12308941'  # Male
    descr = {'af':'manlike voornaam', 'ast':'nome masculín', 'bar':'Mannanam', 'br':'anv paotr', 'bs':'muško ime', 'ca': 'prenom masculí', 'cs':'mužské křestní jméno', 'cy': 'enw personol gwrywaidd', 'da': 'drengenavn', 'de': 'männlicher Vorname', 'en': 'male given name', 'eo':'vira persona nomo', 'es': 'nombre masculino', 'et':'mehenimi', 'eu':'gizonezko izena', 'fr': 'prénom masculin', 'fy':'Jongesnamme', 'ga': 'ainm firinscneach', 'gl':'nome masculino', 'gsw':'männlige Vorname', 'hr':'muško ime', 'hsb':'muske předmjeno', 'hu':'férfi keresztnév', 'id':'nama laki-laki', 'is':'mannsnafn', 'it': 'prenome maschile', 'la':'praenomen masculinum', 'lb':'männleche Virnumm', 'lt':'vyriškas vardas', 'lv':'vīriešu vārds', 'nb': 'mannsnavn', 'nl': 'mannelijke voornaam', 'nn':'mannsnamn', 'pap':'di prome nomber maskulino', 'pl':'imię męskie', 'pt': 'prenome próprio masculino', 'sc': 'male first name', 'sco': 'male first name', 'scn':'nomu di battìu masculinu', 'sq':'emër mashkullor', 'sk':'mužské meno', 'sl':'moško osebno ime', 'sv': 'mansnamn', 'sw':'jina la mwanaume', 'tr':'erkek ismidir'}
elif gender[:1] in 'x':
    target[INSTANCEPROP] = 'Q3409032'   # Other Q202444
    descr = {'af':'voornaam', 'ast':'nome ambiguu', 'bs':'muško i žensko ime', 'ca': 'prenom ambigu', 'cs':'obourodé jméno', 'da': 'kønneutral fornavn', 'de': 'geschlechtsneutraler Vorname', 'en': 'unisex given name', 'eo':'seksneŭtrala persona nomo', 'es': 'nombre ambiguo', 'eu':'izen unisex', 'fr': 'prénom épicène', 'gl':'nome propio unisex', 'gsw':'gschlächtsneutrale Vorname', 'hu':'uniszex utónév', 'it': 'prenome sia maschile che femminile', 'la':'praenomen sine indicio sexus', 'lb':'geschlechtsneutrale Virnumm', 'nb': 'kjønnsnøytralt navn', 'nl': 'genderneutrale voornaam', 'pl':'imię bezpłciowe', 'pt': 'nome unissex', 'sc': 'unisex name', 'scn':'nomu di battìu masculinu e fimmininu', 'sco':'unisex name', 'sk':'rodovo neutrálne meno', 'sl':'obojespolno osebno ime', 'sv': 'könsneutralt förnamn', 'tr':'	eşeysiz ön ad'}
else:
    fatal_error(3, 'Unknown gender')

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

# Print preferences
pywikibot.log('Main language:\t%s' % mainlang)
pywikibot.log('Maximum delay:\t%d s' % maxdelay)
pywikibot.log('Minimum success rate:\t%f%%' % minsucrate)
pywikibot.log('Verbose mode:\t%s' % verbose)
pywikibot.log('Readonly mode:\t%s' % readonly)
pywikibot.log('Exit on fatal error:\t%s' % exitfatal)
pywikibot.log('Error wait factor:\t%d' % errwaitfactor)

# Connect to databases
site = pywikibot.Site('commons')
site.login()
cbotflag = 'bot' in pywikibot.User(site, site.user()).groups()

# This script requires a bot flag
repo = site.data_repository()
repo.login()
wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

for propty in target:
    proptyx = pywikibot.PropertyPage(repo, propty)
    targetx[propty] = pywikibot.ItemPage(repo, target[propty])
    pywikibot.info('Statement {}:{} ({}:{})'
                   .format(proptyx.labels[mainlang], targetx[propty].labels[mainlang],
                           propty, target[propty]))

# Get language descriptions
val = pywikibot.ItemPage(repo, target[INSTANCEPROP])       # Get instance labels
for lang in descr:
    try:
        descr[lang] = val.labels[lang]              # Get language labels
    except:
        pass

# Get list of item numbers
inputfile = sys.stdin.read()
itemlist = sorted(set(inputfile.splitlines()))
pywikibot.debug(itemlist)

wd_proc_all_items()	# Execute all items for one language

"""
    Print all sitelinks (base addresses)
    PAWS is using tokens (passwords can't be used because Python scripts are public)
    Shell is using passwords (from user-password.py file)
"""
for site in sorted(pywikibot._sites.values()):
    if site.username():
        pywikibot.debug('{}\t{}\t{}\t{}'
                        .format(site, site.username(), site.is_oauth_token_available(), site.logged_in()))

sys.exit(exitstat)
