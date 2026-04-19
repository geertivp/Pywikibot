#!/usr/bin/python3

codedoc = r"""
Create a person if not already registered and add a list of claims

Parameters:

    P1: gender (m/f/x/q/M/F) - mandatory

    P2,P3...: optional additional claims (possibility to overrule or skipping default claims)

    Default claims that can be overruled: e.g. P27 Q31 (nationality:BE).
    P27 nl for Koninkrijk der Nederlanden
    Use value - to drop a default claim (like e.g. P27 - "nationality none")

Qualifiers:

    -c: Forced creation of new item (overrule and resolve a homonym issue).
        Not equal to statements are automatically generated.

    -i: Overrule item number

stdin:

    List of persons, in the following format:

    With a comma: lastname,firstname(s)
        Preferred => automatically register firstnames and lastname to the item

    Plain name: firstname(s) lastname

        Fallback format:
        Use underscores, instead of spaces, to "aggregate" firstnames and lastname parts.
        Only possible when there are only two names (not combined firstnames, nor multi-part lastnames).

Functionality:

    Add firstname, lastname. Add gender.

    Add author statements as found from publications, using a matching author name. Case sensitive comparison is used.

    Only the mul-label is actively stored. Any other language labels remain untouched.
    https://www.wikidata.org/wiki/Help:Default_values_for_labels_and_aliases

    Do not store obvious item descriptions.
    https://phabricator.wikimedia.org/T303677

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
    3 Invalid or missing parameter
    13 Maxlag error
    20 General error
    130 Ctrl-c pressed, program interrupted

Examples:

    pwb create_person -i Q19002370 m p27 be
    Piet Stoffelen

Author:

	Geert Van Pamel, 2021-01-08, MIT License, User:Geertivp
    https://github.com/geertivp/Pywikibot/blob/main/create_person.py

Documentation:

    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://public.paws.wmcloud.org/47732266/03%20-%20Wikidata.ipynb
    https://stackoverflow.com/questions/36406862/check-whether-an-item-with-a-certain-label-and-description-already-exists-on-wik
    https://www.mediawiki.org/wiki/Wikibase/API
    https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    https://stackoverflow.com/questions/761804/how-do-i-trim-whitespace-from-a-string

Known problems:

    ERROR: Unknown lastname Bostyn
        First create lastname.
        Then rerun the script.

    ERROR: Unknown lastname Bostyn
        Server replication delay; lastname really was already created, but is not yet available (system is reading from cache?)
        Retry later.

    Duplicates can possibly be created when there are augmented replication delays.
    Do not immediately rerun this script repeatedly for the same person.

    Wrong author names
    Homomyms... fix manually, maybe you need to use -c to create a new name; maybe you need to move statements or update P50 statements.
    In a rare case you might need to merge duplicate items.

"""

# List the required modules
import os               # Operating system: getenv
import pdb              # Python debugger
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import unidecode        # Unicode

from datetime import datetime	# now, strftime, delta time, total_seconds
from pywikibot.data import api

# Global variables
modnm = 'Pywikibot create_person'   # Module name (using the Pywikibot package)
pgmid = '2026-04-19 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

# Technical configuration flags
ENLANG = 'en'
MULANG = 'mul'
MAINLANG = 'en:mul'
MAX_ITEMS = 'max'        # Maximum items to return after search (maximum: 5000)

# Defaults: be transparent and safe
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
shell = True		# Shell available (command line parameters are available; automatically overruled by PAWS)
createmode = False	# Forced creation (activate with -c)
verbose = True		# Can be set with -q or -v (better keep verbose to monitor the bot progress)

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
transcmt = '#pwb Create person'

# Properties
COUNTRYPROP = 'P17'
GENDERPROP = 'P21'
NATIONALITYPROP = 'P27'
INSTANCEPROP = 'P31'
AMBTPROP = 'P39'
AUTHORPROP = 'P50'
NOBLENAMEPROP = 'P97'
EDITORPROP = 'P98'
MEMPOLPARTYPROP = 'P102'
NATIVELANGPROP = 'P103'
PROFESSIONPROP = 'P106'
EMPLOYERPROP = 'P108'
ILLUSTRATORPROP = 'P110'
PUBLISHERPROP = 'P123'
ISBN13PROP = 'P212'
OCLDIDPROP = 'P243'
REFPROP = 'P248'
SUBCLASSPROP = 'P279'
PUBLOCATIONPROP = 'P291'
DOINUMBERPROP = 'P356'
COMMONSCATPROP = 'P373'
BIRTHDATEPROP = 'P569'
DEATHDATEPROP = 'P570'
EDITIONLANGPROP = 'P407'
WIKILANGPROP = 'P424'
COUNTRYORIGPROP = 'P495'
PUBYEARPROP = 'P577'
WRITTENWORKPROP = 'P629'
LASTNAMEPROP = 'P734'
FIRSTNAMEPROP = 'P735'
PSEUDONYMPROP = 'P742'
EDITIONPROP = 'P747'
REFDATEPROP = 'P813'
MAINSUBPROP = 'P921'
ISBN10PROP = 'P957'
JURISDICTIONPROP = 'P1001'
DEWCLASIDPROP = 'P1036'
NICKNAMEPROP = 'P1449'
EDITIONTITLEPROP = 'P1476'
BIRTHNAMEPROP = 'P1477'
SEQNRPROP = 'P1545'
NATIVENAMEPROP = 'P1559'
EDITIONSUBTITLEPROP = 'P1680'
ARTISTNAMEPROP = 'P1787'
NOTEQTOPROP = 'P1889'
ORIGNAMEPROP = 'P1932'
AUTHORNAMEPROP = 'P2093'
FASTIDPROP = 'P2163'
MARIEDNAMEPROP = 'P2562'
PREFACEBYPROP = 'P2679'
AFTERWORDBYPROP = 'P2680'
OCLCWORKIDPROP = 'P5331'
LIBCONGCLASSPROP = 'P8360'

author_prop_list = {AUTHORPROP, EDITORPROP, ILLUSTRATORPROP, PREFACEBYPROP, AFTERWORDBYPROP}

# Instances
DOUBLELASTNAMEINSTANCE = 'Q29042997'
LASTNAMEINSTANCE = 'Q101352'                    # familienaam
LASTNAMESUBCLASSINSTANCE = 'Q121493679'         # achternaam Q4116295
LASTNAMEHYPHNINSTANCE = 'Q106319018'            # hyphen
LASTNAMETOPONYMINSTANCE = 'Q17143070'           # toponym
LASTNAMECOMPOUNDINSTANCE = 'Q60558422'          # compound
LASTNAMEAFFIXINSTANCE = 'Q66480858'             # affix
# Q117209596

AUTHORINSTANCE = 'Q482980'
WRITERINSTANCE = 'Q36180'

author_profession = {
    AUTHORINSTANCE,
    WRITERINSTANCE,
    # possibly add other instances
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


def get_property_label(propx) -> str:
    """Get the label of a property.

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
    """Get the item; handle redirects.
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


def get_item_prop_val(item, proplist) -> str:
    """
    Get values from claims

    :param item: Wikidata item
    :param proplist: Search list of date properties
    :return: concatenated list of values
    """
    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:
            for claim in item.claims[prop]:
                val = claim.target
                try:
                    item_prop_val += val + ';'
                except Exception as error:
                    pywikibot.error(error)      # Site error
            break
    return item_prop_val[:-1]


def get_item_prop_val_label(item, proplist) -> str:
    """Get property value label.

    :param item: Wikidata item
    :param proplist: Search list of properties
    :return: concatenated list of first matching property value labels
    """
    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:
            for seq in item.claims[prop]:
                val = seq.target
                try:
                    ##pdb.set_trace()
                    if not val:
                        pass
                    elif isinstance(val, str):
                        item_prop_val += val + '/'
                    elif isinstance(val, pywikibot.ItemPage):
                        item_prop_val += get_item_header(val.labels) + '/'
                    elif isinstance(val, pywikibot.WbMonolingualText):
                        item_prop_val += val.text + '/'
                    elif isinstance(val, pywikibot.WbTime):
                        item_prop_val += str(val.year) + '/'
                    else:
                        pywikibot.error('{} not implemented'.format(type(val)))
                except:     # Skip unlabeled items
                    raise
            # Stop at first matching property
            if item_prop_val:
                item_prop_val[:-1]
                break
    return item_prop_val


def get_item_prop_val_object_label(item, proplist) -> str:
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
                val = claim.target     ## Might need get() and redirect logic
                try:
                    item_prop_val += get_item_header(val.labels) + '/'
                except Exception as error:
                    pywikibot.error(error)      # Site error
            break
    return item_prop_val[:-1]


def get_item_prop_val_year(item, proplist) -> str:
    """
    Get dates from claims

    :param item: Wikidata item
    :param proplist: Search list of date properties
    :return: list of dates
    """
    item_prop_val = ''
    for prop in proplist:
        if prop in item.claims:
            for claim in item.claims[prop]:
                val = claim.target
                try:
                    item_prop_val += str(val.year) + '/'
                except Exception as error:
                    pywikibot.error(error)      # Site error
            break
    return item_prop_val[:-1]


def item_is_in_list(statement_list, itemlist):
    """Verify if statement list contains at least one item from the itemlist
    param: statement_list: Statement list
    param: itemlist:      List of values
    return: First matching, or empty string
    """
    for seq in statement_list:
        try:
            isinlist = seq.target.getID()
            if isinlist in itemlist:
                return isinlist
        except:
            pass    # Ignore NoneType error
    return ''


def item_has_label(item, label):
    """Verify if the item has a label or alias.

    :param item: Item
    :param label: Item label (string)
    :return: Matching string

    Unicode fallback and case insensitive.
    """
    label = unidecode.unidecode(label).casefold()
    for lang in item.labels:
        # ERROR: Error processing Q95278187, Page [[wikidata:Q134390554]] is a redirect page.
        if unidecode.unidecode(item.labels[lang]).casefold() == label:
            return item.labels[lang]

    for lang in item.aliases:
        for seq in item.aliases[lang]:
            if unidecode.unidecode(seq).casefold() == label:
                return seq
    return ''


def get_item_list(item_name: str, instance_id, subclass_allowed: bool, ignore_case: bool) -> set():
    """Get list of items by name, matching an instance list.

    :param item_name: Item name (string; case sensitive)
    :param instance_id: Instance ID (set, or list)
    :param subclass_allowed: accept subclass
    :return: Set of items

    See https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    """
    item_name = item_name.strip()
    pywikibot.log('Search label: {}'.format(item_name.encode('utf-8')))
    item_list = set()                   # Empty set
    params = {'action': 'wbsearchentities',
              'search': item_name,      # Get item list from label (Case insensitive search)
              'type': 'item',
              'language': mainlang,     # Labels are in native language
              'uselang': mainlang,
              'strictlanguage': False,  # All languages are searched
              'format': 'json',
              'limit': 20}              # Should be reasonable value
    request = api.Request(site=repo, parameters=params)
    result = request.submit()
    pywikibot.debug(result)

    if 'search' in result:
        # Case sensitive comparison (avoid false matches)
        # Some good matches could be missed, leading to possible duplicates
        search_name_canon = unidecode.unidecode(item_name)
        if ignore_case:
            search_name_canon = search_name_canon.casefold()
        # Loop though items
        for row in result['search']:
            item = get_item_page(row['id'])

            # Skip subclass items
            # Matching instance, strict equal comparison
            # Remark that most items have a proper instance
            # Missing instances can lead to wrong item assignment
            if (subclass_allowed or SUBCLASSPROP not in item.claims) and (
                    INSTANCEPROP not in item.claims
                    or item_is_in_list(item.claims[INSTANCEPROP], instance_id)):    ## Should we obtain subclass instances?
                # Search all languages both for labels and aliases
                # Filter flse positives (e.g. mixed firstname and lastname combinations)

                for lang in item.labels:
                    item_name_canon = unidecode.unidecode(item.labels[lang])
                    if ignore_case:             # Case sensitive label match
                        item_name_canon = item_name_canon.casefold()
                    if search_name_canon == item_name_canon:
                        item_list.add(item)     # Label match
                        break

                for lang in item.aliases:
                    for seq in item.aliases[lang]:
                        item_name_canon = unidecode.unidecode(seq)
                        if ignore_case:         # Case sensitive label match
                            item_name_canon = item_name_canon.casefold()
                        if search_name_canon == item_name_canon:
                            item_list.add(item) # Alias match
                            break
    pywikibot.debug(item_list)
    return item_list


def get_item_with_prop_value (prop: str, propval: str) -> set():
    """Get list of items that have a property/value statement.

    :param prop: Property ID (string)
    :param propval: Property value (string; case insensitieve)
    :return: List of items (Q-numbers)

    See https://www.mediawiki.org/wiki/API:Search
    """
    item_name_canon = unidecode.unidecode(propval).casefold()   # Ingnore case
    item_list = set()                   # Empty set
    # https://www.wikidata.org/w/api.php?action=query&list=search&srwhat=text&srsearch=P212:978-94-028-1317-3
    pywikibot.debug('Search statement: {}:{} ({})'
                    .format(prop, propval, item_name_canon))
    params = {'action': 'query',        # Statement search
              'list': 'search',
              'srnamespace': 0,
              'srsearch': prop + ':' + propval, # Nice that this works...
              'srwhat': 'text',
              'format': 'json',
              'srprop': 'size',         # Limit returned data
              'srlimit': MAX_ITEMS}     # Should be reasonable value
    # Caseless search
    request = api.Request(site=repo, parameters=params)
    result = request.submit()

    ##pdb.set_trace()
    if 'query' in result and 'search' in result['query']:
        num_items = len(result['query']['search'])
        if num_items:
            # Could possibly take a long time...
            # Includes false positives
            pywikibot.info('{} partial matching {} ({}), might take more time to load'
                           .format(num_items, get_property_label(prop), prop))

        # Filter potential items
        for row in result['query']['search']:
            qnumber = row['title']
            item = get_item_page(qnumber)

            # There are resembling items, with non-matching names
            # Only include valid items
            if prop in item.claims:
                for seq in item.claims[prop]:
                    # Ignore case and unicode
                    val = seq.target
                    if unidecode.unidecode(val).casefold() == item_name_canon:
                        item_list.add(item) # Found match
                        break
    return item_list


def get_language_preferences() -> []:
    """Get the list of preferred languages,
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


def unescape_string(inpar) -> str:
    for seq in '_+?':
        inpar = inpar.replace(seq, ' ')
    return inpar.strip()


def wd_proc_all_items():
    """
    """

    global exitstat

# Loop initialisation
    transcount = 0	    	# Total transaction counter
    errcount = 0	    	# Error counter
    errsleep = 15	    	# Technical error penalty (sleep delay in seconds)

# Avoid that the user is waiting for a response while the data is being queried
    pywikibot.info('Processing {:d} statements'.format(len(itemlist)))

# Transaction timing
    now = datetime.now()	# Start the main transaction timer
    status = 'Start'		# Force loop entry

# Process all items in the list
    for newitem in itemlist:	# Main loop for all DISTINCT items
      if  status == 'Stop':	    # Ctrl-c pressed -> stop in a proper way
        break

      firstname = ''
      lastname = ''
      objectname = ''

      if newitem[:4] == 'Sir ':
          # Move Sir label prefix to statement
          targetx[NOBLENAMEPROP] = get_item_page('Q209690')
          newitem = newitem[4:]

      # Trim item number or other suffix
      suffix = PSUFFRE.search(newitem)  	        # Remove () suffix, if any
      if suffix:
          newitem = newitem[:suffix.start()]      # Get canonical form

      # Process firstname and lastname
      #pdb.set_trace()
      name = newitem.split(',')
      if len(name) == 2:
          # Reorder lastname, firstname
          # Remove multiple spaces
          firstname = ' '.join(unescape_string(name[1]).split()).strip()
          lastname = ' '.join(unescape_string(name[0]).split()).strip()
          if not firstname:
            objectname = lastname
          elif not lastname:
            objectname = firstname
          else:
            objectname = firstname + ' ' + lastname
      elif len(name) == 1:
          name = newitem.split()
          if len(name) == 0:
              pass
          elif len(name) == 1:
              pywikibot.info('Abiguous name {}'.format(newitem))
          elif len(name) == 2:
              # One single spaces
              firstname = unescape_string(name[0])
              lastname = unescape_string(name[1])
              if '-' not in lastname:
                objectname = firstname + ' ' + lastname
          elif len(name) == 3:
              # We assume compound lastname
              firstname = unescape_string(name[0])
              lastname = unescape_string(name[1] + ' ' + name[2])
              if '-' not in lastname:
                objectname = firstname + ' ' + lastname
          elif '-' not in newitem:
              # More than one space
              objectname = ' '.join(name).strip()
              pywikibot.info('Please aggregate firstnames/lastname with _ {}'.format(objectname))
          else:
              # - in lastname
              pywikibot.error('Complex name {}'.format(newitem))
      else:
          # More than one comma
          pywikibot.error('Strange name {}'.format(newitem))

      if not objectname:
        pass
      elif not ROMANRE.search(objectname):
        status = 'Skip'
        errcount += 1
        exitstat = max(exitstat, 3)
        pywikibot.error('Bad name: {}'.format(objectname))
      else:
        transcount += 1	# New transaction
        status = 'OK'
        label = {}
        descr = ''
        alias = []
        commonscat = '' # Commons category
        nationality = ''
        qnumber = ''    # In case or error

        try:			# Error trapping (prevents premature exit on transaction error)
            # Get all matching items
            pywikibot.info('')
            ## Known problems:
            # Existing item without INSTANCEPROP can cause wrong item updates
            # Creation of duplicates with 3 names
            person_list = get_item_list(objectname, [targetx[INSTANCEPROP].getID()], False, False)

            if not person_list or createmode:
                # Create new item; only one single label
                label[MULANG] = objectname

                try:
                    item = pywikibot.ItemPage(repo)             # Create item
                    item.editLabels(labels=label, summary=transcmt, bot=wdbotflag)
                    qnumber = item.getID()
                    pywikibot.warning('Creating person {} ({})'.format(objectname, qnumber))

                    # Generate not equal statements (nil if unique)
                    for sitem in person_list:
                        sqnumber = sitem.getID()
                        slabel = get_item_header(sitem.labels)

                        # Because we have a new item, be can assign symmetric property
                        claim = pywikibot.Claim(repo, NOTEQTOPROP)
                        claim.setTarget(sitem)
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt +
                                            ' Add {} ({})'.format(neq_propty_label, NOTEQTOPROP))
                        pywikibot.warning('Add statement {}:{} ({}:{}) to {} ({})'.format(
                                            neq_propty_label, slabel,
                                            NOTEQTOPROP, sqnumber,
                                            objectname, qnumber))

                        # We repeat for the inverse direction
                        claim = pywikibot.Claim(repo, NOTEQTOPROP)
                        claim.setTarget(item)
                        sitem.addClaim(claim, bot=wdbotflag, summary=transcmt + ' Add {} ({})'
                                            .format(neq_propty_label, NOTEQTOPROP))
                        pywikibot.warning('Add statement {}:{} ({}:{}) to {} ({})'.format(
                                            neq_propty_label, objectname,
                                            NOTEQTOPROP, qnumber,
                                            slabel, sqnumber))

                except pywikibot.exceptions.OtherPageSaveError as error:
                    pywikibot.error('Error creating {}, {}'.format(objectname, error))
                    status = 'Error'	    # Handle any generic error
                    errcount += 1
                    exitstat = max(exitstat, 10)
            elif len(person_list) == 1 or itemnumber:
                # Unique person found
                status = 'Update'

                # Explicit item number
                if itemnumber:
                    qnumber = itemnumber
                    item = get_item_page(qnumber)
                else:
                    item = person_list.pop()
                    qnumber = item.getID()

                if INSTANCEPROP not in item.claims:
                    pywikibot.error('Item {} ({}) does not have instance (P31)'
                                    .format(objectname, qnumber))

                if MULANG not in item.labels:
                    item.labels[MULANG] = objectname
                elif item.labels[MULANG] == objectname:
                    pass
                elif MULANG not in item.aliases:
                    item.aliases[MULANG] = [objectname]
                elif objectname not in item.aliases[MULANG]:
                    item.aliases[MULANG].append(objectname)    # Merge aliases

                if FIRSTNAMEPROP in item.claims:
                    # Only if first name and last name are known
                    # https://www.wikidata.org/wiki/Q126913126
                    first_names = ''
                    sep = ''
                    # Concatenate all first names
                    # More complicated:
                    # need to take into account volgnummer for multiple firstnames
                    for seq in item.claims[FIRSTNAMEPROP]:  # Can't use join ?
                        val = seq.target
                        first_names += sep + get_item_header(val.labels)
                        sep = ' '
                        
                    if len(item.claims[FIRSTNAMEPROP]) > 1:
                        pywikibot.info('Multiple firstnames {}'.format(first_names))

                    last_name = ''
                    full_name = ''
                    if LASTNAMEPROP in item.claims and item.claims[LASTNAMEPROP][0].target:
                        last_name = get_item_header(item.claims[LASTNAMEPROP][0].target.labels)
                        full_name = first_names + ' ' + last_name

                    birth_name = ''
                    if BIRTHNAMEPROP in item.claims:
                        birth_name = item.claims[BIRTHNAMEPROP][0].target.text
                    elif len(item.claims[FIRSTNAMEPROP]) > 1:
                        # Unsure about sequence of firstnames...
                        pywikibot.info('Missing birth name {} {}'.format(first_names, last_name))

                    if full_name:
                        if MULANG not in item.labels:
                            item.labels[MULANG] = full_name
                        elif item.labels[MULANG] == full_name:
                            pass
                        elif MULANG not in item.aliases:
                            item.aliases[MULANG] = [full_name]
                        elif full_name not in item.aliases[MULANG]:
                            item.aliases[MULANG].append(full_name)    # Merge aliases
                        
                    if (full_name and birth_name and birth_name != full_name):
                        pywikibot.info('Full name different from birth name {} / {}'.format(full_name, birth_name))
                        if MULANG not in item.labels:
                            item.labels[MULANG] = birth_name
                        elif item.labels[MULANG] == birth_name:
                            pass
                        elif MULANG not in item.aliases:
                            item.aliases[MULANG] = [birth_name]
                        elif birth_name not in item.aliases[MULANG]:
                            item.aliases[MULANG].append(birth_name)    # Merge aliases

                # Remove duplicate labels
                for lang in item.labels:
                    if lang in item.aliases:
                        while item.labels[lang] in item.aliases[lang]:
                            item.aliases[lang].remove(item.labels[lang])

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

                # Don't copy aliases
                if False and MULANG not in item.aliases and mainlang in item.aliases:
                    item.aliases[MULANG] = item.aliases[mainlang]
                    ##item.aliases[mainlang] = []

                try:
                    person_label = ' '.join([get_item_prop_val_label(item, propty)
                                             for propty in [[INSTANCEPROP],
                                                            [NATIONALITYPROP],
                                                            [GENDERPROP],[PROFESSIONPROP, AMBTPROP],
                                                            [FIRSTNAMEPROP], [LASTNAMEPROP],
                                                            [BIRTHNAMEPROP, NATIVENAMEPROP, MARIEDNAMEPROP,
                                                             ARTISTNAMEPROP, PSEUDONYMPROP, NICKNAMEPROP, ORIGNAMEPROP],
                                                            [BIRTHDATEPROP], [DEATHDATEPROP],
                                                            [EMPLOYERPROP, MEMPOLPARTYPROP]]]).strip()

                    if not person_label:
                        person_label = 'person'

                    pywikibot.info('Found {} {} ({})'.format(person_label, objectname, qnumber))
                    ##item.editLabels(labels=item.labels, summary=transcmt, bot=wdbotflag)
                    #item.editDescriptions(descriptions=item.descriptions, summary=transcmt, bot=wdbotflag)
                    ##item.editAliases(aliases=item.aliases, summary=transcmt, bot=wdbotflag)
                    item.editEntity({'labels': item.labels, 'aliases': item.aliases},
                                    summary=transcmt, bot=wdbotflag)
                except Exception as error:  # other exception to be used
                    status = 'Error'
                    pywikibot.error(error)
                    #pdb.set_trace()
                    #raise
                    #pass    # *** Jump failed: can't jump out of an 'except' block
            else:
                status = 'Ambiguous'            # Item is not unique
                pywikibot.warning('Ambiguous person name {}'.format(objectname))
                for sitem in person_list:
                    try:
                        for rev in sitem.revisions(reverse = True, total = 1):   # Get the article creator (oldest revision)
                            wikiuser = pywikibot.User(repo, rev.user)

                        # https://www.mediawiki.org/wiki/API:Block#Python
                        # https://www.wikidata.org/wiki/User:PU5000
                        """
Revision({'revid': 1193057976, 'parentid': 0, 'user': 'MrProperLawAndOrder', 'userid': 4181270, 'timestamp': Timestamp(2020, 5, 29, 3, 45, 1), 'size': 1931, 'sha1': 'dd5cd653c6d5691f1967b153a213c861fa3c6658', 'roles': ['main'], 'slots': {'main': {'contentmodel': 'wikibase-item'}}, 'comment': '/* wbeditentity-create-item:0| */ #quickstatements', 'parsedcomment': '\u200e<span dir="auto"><span class="autocomment">Een nieuw item aangemaakt: </span></span> #quickstatements', 'tags': ['OAuth CID: 1351'], 'anon': False, 'minor': False, 'userhidden': False, 'commenthidden': False, 'text': None, 'contentmodel': 'wikibase-item'})
                        """

                        userprop = wikiuser.getprops()
                        """
for i in userprop: i, userprop[i]

('blockid', 18294)
('blockedby', 'Jasper Deng')
('blockedbyid', 3724)
('blockreason', 'Abusing [[Special:MyLanguage/Wikidata:Alternate accounts|multiple accounts]]: [[User:Tamawashi]]; globally banned user; CheckUser block')
('blockedtimestamp', '2020-06-17T19:10:22Z')
('blockexpiry', 'infinite')
('blocknocreate', '')
('blockedtimestampformatted', '17 jun 2020 21:10')
('gender', 'unknown')
                        """

                        if 'blockid' in userprop:
                            item_creation_info = 'created by {} on {:.10}, blocked since {:.10}'.format(rev.user, str(rev['timestamp']), str(userprop['blockedtimestamp']))
                        else:
                            item_creation_info = 'created by {} on {:.10}'.format(rev.user, str(rev['timestamp']))
                    except Exception as error:
                        pywikibot.error('Error processing {}, {}'.format(sitem.getID(), error))
                        item_creation_info = 'creator unknown (error)'

                    pywikibot.info('{} ({}), {}\t{}\t{}\t{}'.format(
                            get_item_header(sitem.labels), sitem.getID(),
                            item_creation_info,
                            get_item_prop_val_object_label(sitem, [NATIONALITYPROP]),
                            get_item_prop_val_year(sitem, [BIRTHDATEPROP]),
                            get_item_header(sitem.descriptions)))

# Register claims
            if status in ['OK', 'Update']:
                # Register missing statements
                for propty in targetx:
                    propstatus = 'OK'

                    # Property is already registered
                    if propty in item.claims:
                        for seq in item.claims[propty]:
                            val = seq.target
                            if val == targetx[propty]:
                                # Statement already registered
                                propstatus = 'Skip'
                                break
                            elif propty in {'P6104'}:
                                # Multiple values allowed
                                pywikibot.info('{} ({}) {} ({})'.format(
                                                  get_property_label(propty), propty,
                                                  get_item_header(val.labels), val.getID()))
                            else:
                                propstatus = 'Other'
                                pywikibot.warning('Conflicting statement {} ({}) {} ({}) - {} ({}) for {} ({})'.format(
                                                  get_property_label(propty), propty,
                                                  get_item_header(targetx[propty].labels), targetx[propty].getID(),
                                                  get_item_header(val.labels), val.getID(), objectname, qnumber))
                                break

                    # Claim is missing, so add it now
                    if propstatus == 'OK':
                        claim = pywikibot.Claim(repo, propty)
                        claim.setTarget(targetx[propty])
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                        pywikibot.warning('Add {} {} ({}:{}) to {} ({})'.format(
                                          get_property_label(propty), get_item_header(targetx[propty].labels),
                                          propty, targetx[propty].getID(), objectname, qnumber))

                # Assign firstname and lastname
                name_target = {
                    FIRSTNAMEPROP: ['firstname', firstname, True],  # Must split firstname
                    LASTNAMEPROP: ['lastname', lastname, False],    # Lastname can contain spaces
                }

                # https://www.wikidata.org/wiki/Q2019359 Willem Jan Neutelings
                for propty in name_target:
                    # Add missing firstname and lastname
                    nameval = name_target[propty]
                    if nameval[1]:
                        if nameval[2]:
                            # Split the sequence of firstnames
                            split_list = [val for val in nameval[1].split()]
                        else:
                            # Keep the lastname as one unit, even if there are spaces
                            split_list = [nameval[1]]

                        name_seq = 0
                        for val in split_list:
                            # Assign a sequence number for multiple first/last names
                            if len(split_list) > 1:
                                name_seq += 1
                            name_list = get_item_list(val, property_instances[propty][0],
                                                      property_instances[propty][1],
                                                      property_instances[propty][2])

                            if len(name_list) == 1:
                                sitem = name_list.pop()
                                if (propty not in item.claims
                                        or not item_is_in_list(item.claims[propty], [sitem.getID()])):
                                    # Unique name found
                                    ##pdb.set_trace()
                                    claim = pywikibot.Claim(repo, propty)
                                    claim.setTarget(sitem)
                                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                                    pywikibot.warning('Add {} {} ({}:{}) to {} ({})'.format(
                                                      nameval[0], val, propty, sitem.getID(),
                                                      objectname, qnumber))

                                    if name_seq and SEQNRPROP not in claim.qualifiers:
                                        # Add a sequence number
                                        qualifier = pywikibot.Claim(repo, SEQNRPROP)
                                        qualifier.setTarget(str(name_seq))
                                        claim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt)
                            elif name_list:
                                pywikibot.error('Ambiguous {} {}'.format(nameval[0], val))
                                for seq in name_list:
                                    # Expect only one single instance
                                    pywikibot.info('\t{} ({}) is {}'.format(
                                                   get_item_header(seq.labels), seq.getID(),
                                                   get_item_prop_val_object_label(seq, [INSTANCEPROP])))

                                # Expect only one single name
                                if propty in item.claims:
                                    seq = item.claims[propty][0].target
                                    pywikibot.info('\t{} ({}) is already registered as {}'.format(
                                                   get_item_header(seq.labels), seq.getID(),
                                                   get_item_prop_val_object_label(seq, [INSTANCEPROP])))
                            else:
                                pywikibot.error('Unknown {} {}'.format(nameval[0], val))

                # Search all works where the person is author (as text; case insensitive, unidecode)
                work_list = get_item_with_prop_value(AUTHORNAMEPROP, objectname)

                if not work_list:
                    pass
                elif person_list:
                    # Do not register author works when there are ambiguous names
                    # We can't easily discriminate amongst the authors with the same name.
                    pywikibot.info('{} works by homonym authors {} {}'.format(
                                   len(work_list), objectname,
                                   [sitem.getID() for sitem in person_list]))
                else:
                    # Unique author name
                    pywikibot.info('Author {} ({}) has {} works, now amending the works'
                                   .format(objectname, qnumber, len(work_list)))

                    # Update all works to include the author as item number
                    # Potential problem: homonyms; take care of field of work (P101)
                    # If not OK, immediately cancel the updates, and perform -c and manual corrections.
                    for workitem in work_list:
                        # Determine the title and the publication language
                        work_title = ''
                        lang = MULANG

                        # Get the first work title as a default
                        if ENLANG in workitem.labels:
                            work_title = workitem.labels[ENLANG]

                        if not work_title:
                            for lang in main_languages:
                                if lang in workitem.labels:
                                    work_title = workitem.labels[lang]
                                    break

                        # Title in any language, as a fallback
                        if not work_title:
                            for lang in workitem.labels:
                                work_title = workitem.labels[lang]
                                break

                        # Overrule language
                        if EDITIONLANGPROP in workitem.claims:
                            work_lang_item = workitem.claims[EDITIONLANGPROP][0].target
                            if WIKILANGPROP in work_lang_item.claims:
                                lang = work_lang_item.claims[WIKILANGPROP][0].target

                        # Overrule title
                        if EDITIONTITLEPROP in workitem.claims:
                            # We assume a single title
                            work_title_item = workitem.claims[EDITIONTITLEPROP][0].target   ### target versus getTarget() -- what is better??
                            work_title = work_title_item.text

                            if work_title_item.language != MULANG:
                                # Might be inconsistent with EDITIONLANGPROP
                                lang = work_title_item.language
                            elif lang != MULANG:
                                # Set work language
                                work_title_item.language = lang
                                workitem.claims[EDITIONTITLEPROP][0].changeTarget(
                                        work_title_item, bot=wdbotflag, summary=transcmt)
                                pywikibot.warning('Updating {} language for title of work'.format(lang))

                        # Show edition details
                        work_instance = get_item_prop_val_object_label(workitem, [INSTANCEPROP])
                        work_pub_publisher = get_item_prop_val_object_label(workitem, [PUBLISHERPROP])
                        work_pub_loc = get_item_prop_val_object_label(workitem, [PUBLOCATIONPROP])
                        work_pub_year = get_item_prop_val_year(workitem, [PUBYEARPROP])
                        work_pub_id = get_item_prop_val(workitem, [ISBN13PROP, DOINUMBERPROP])
                        pywikibot.info('\n({}) {} {}:{} ({}, {}, {}, {})'.format(
                                       workitem.getID(), work_instance, lang, work_title,
                                       work_pub_publisher, work_pub_loc, work_pub_year, work_pub_id))

                        if not work_title:
                            pywikibot.info('Missing title for work')
                        elif MULANG not in workitem.labels:
                            # Assign missing mul label
                            # https://www.wikidata.org/wiki/Help:Default_values_for_labels_and_aliases
                            workitem.labels[MULANG] = work_title

                            try:
                                workitem.editLabels(labels=workitem.labels, summary=transcmt, bot=wdbotflag)
                                pywikibot.warning('Adding title mul language for {} {}'.format(
                                                  work_instance, workitem.getID()))
                            except Exception as error:  # other exception to be used
                                ## e.g. Value longer than 240 bytes
                                pywikibot.error('Error processing {} {}, {}'.format(
                                                work_instance, workitem.getID(), error))
                        """
(Q86046161) en:A European Renal Best Practice (ERBP) position statement on the Kidney Disease: Improving Global Outcomes (KDIGO) clinical practice guideline for the management of blood pressure in non-dialysis-dependent chronic kidney disease: an endorsement with some caveats for real-life application
WARNING: API error modification-failed: Label must be no more than 250 characters long
ERROR: Error processing Q55232541, Edit to page [[wikidata:Q86046161]] failed:
modification-failed: Label must be no more than 250 characters long
[param: id=Q86046161&action=wbeditentity&bot=1&baserevid=1516782562&summary=%23pwb+Create+person&data=%7B%22labels%22%3A+%7B%22en%22%3A+%7B%22language%22%3A+%22en%22%2C+%22value%22%3A+%22A+European+Renal+Best+Practice+%28ERBP%29+position+statement+on+the+Kidney+Disease%3A+Improving+Global+Outcomes+%28KDIGO%29+clinical+practice+guideline+for+the+management+of+blood+pressure+in+non-dialysis-dependent+chronic+kidney+disease%3A+an+endorsement+with%22%7D%2C+%22nl%22%3A+%7B%22language%22%3A+%22nl%22%2C+%22value%22%3A+%22A+European+Renal+Best+Practice+%28ERBP%29+position+statement+on+the+Kidney+Disease%3A+Improving+Global+Outcomes+%28KDIGO%29+clinical+practice+guideline+for+the+management+of+blood+pressure+in+non-dialysis-dependent+chronic+kidney+disease%3A+an+endorsement+with%22%7D%2C+%22mul%22%3A+%7B%22language%22%3A+%22mul%22%2C+%22value%22%3A+%22A+European+Renal+Best+Practice+%28ERBP%29+position+statement+on+the+Kidney+Disease%3A+Improving+Global+Outcomes+%28KDIGO%29+clinical+practice+guideline+for+the+management+of+blood+pressure+in+non-dialysis-dependent+chronic+kidney+disease%3A+an+endorsement+with+some+caveats+for+real-life+application%22%7D%7D%7D&assert=user&maxlag=5&format=json&token=98ad04801795e31924cd80f28cff637e670fa004%2B%5C;
 messages: [{'name': 'wikibase-validator-label-too-long', 'parameters': ['250', 'A European Renal Best Practic...'], 'html': {'*': 'Het label mag niet meer dan 250 tekens lang zijn'}}];
 servedby: mw-api-ext.codfw.main-856cf9b745-gpwm7;
 help: See https://www.wikidata.org/w/api.php for API usage. Subscribe to the mediawiki-api-announce mailing list at &lt;https://lists.wikimedia.org/postorius/lists/mediawiki-api-announce.lists.wikimedia.org/&gt; for notice of API deprecations and breaking changes.]
                        """

                        # Go through the list of authors
                        # Reuse sequence number if available
                        # Try to reuse the reference
                        authortoadd = False
                        author_seq = ''
                        author_source = []
                        for claim in workitem.claims[AUTHORNAMEPROP]:
                            book_author_name = claim.target
                            if objectname == book_author_name:  # Case sensitive comparison
                                authortoadd = True
                                if SEQNRPROP in claim.qualifiers:
                                    author_seq = claim.qualifiers[SEQNRPROP][0].target
                                """
                                if claim.sources:
                                   #pdb.set_trace()
                                    ##for source in claim.sources: # Loop through sources on claim
                                    source = claim.sources[0]
                                    for value in source.values():  # Loop through source values on claim
                                        #print(value)
                                        #hash_value = value[1].pop('hash')   ## Strip hash
                                        #print(value)
                                        sources.append(value) # add it to the list
                                    #print(sources)
                                """
                                """
[Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P248', 'datatype': 'wikibase-item', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 28946522}, 'type': 'wikibase-entityid'}, 'hash': '6396cb3a98f87e9313469d693c6b95da7e14adb5'})]
[Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P854', 'datatype': 'url', 'datavalue': {'value': 'https://doi.org/10.1017%2FS026367510600010X', 'type': 'string'}, 'hash': '6396cb3a98f87e9313469d693c6b95da7e14adb5'})]

https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_sources
https://www.w3schools.com/python/gloss_python_remove_dictionary_items.asp
                                """
                                author_source = claim.getSources()

                                if False and author_source:
                                    # Include references, when applicable
                                    # Not all refences tags should be duplicated...
                                    """
[OrderedDict([('P248', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P248', 'datatype': 'wikibase-item', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 5412157}, 'type': 'wikibase-entityid'}, 'hash': '05c09aa976d67bbee50fa83c4ecd5d372e56555e'})]), ('P932', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P932', 'datatype': 'external-id', 'datavalue': {'value': '6733835', 'type': 'string'}, 'hash': '05c09aa976d67bbee50fa83c4ecd5d372e56555e'})]), ('P854', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P854', 'datatype': 'url', 'datavalue': {'value': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:31501474%20AND%20SRC:MED&resulttype=core&format=json', 'type': 'string'}, 'hash': '05c09aa976d67bbee50fa83c4ecd5d372e56555e'})]), ('P813', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P813', 'datatype': 'time', 'datavalue': {'value': {'time': '+00000002020-04-10T00:00:00Z', 'precision': 11, 'after': 0, 'before': 0, 'timezone': 0, 'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'}, 'type': 'time'}, 'hash': '05c09aa976d67bbee50fa83c4ecd5d372e56555e'})])])]

[OrderedDict([('P248', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P248', 'datatype': 'wikibase-item', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 5412157}, 'type': 'wikibase-entityid'}, 'hash': '76b91200d6800b4237a6bc755693bc5978029f76'})]), ('P698', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P698', 'datatype': 'external-id', 'datavalue': {'value': '33148311', 'type': 'string'}, 'hash': '76b91200d6800b4237a6bc755693bc5978029f76'})]), ('P854', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P854', 'datatype': 'url', 'datavalue': {'value': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:33148311%20AND%20SRC:MED&resulttype=core&format=json', 'type': 'string'}, 'hash': '76b91200d6800b4237a6bc755693bc5978029f76'})]), ('P813', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P813', 'datatype': 'time', 'datavalue': {'value': {'time': '+00000002020-11-06T00:00:00Z', 'precision': 11, 'after': 0, 'before': 0, 'timezone': 0, 'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'}, 'type': 'time'}, 'hash': '76b91200d6800b4237a6bc755693bc5978029f76'})])])]

[OrderedDict([('P248', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P248', 'datatype': 'wikibase-item', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 126285607}, 'type': 'wikibase-entityid'}, 'hash': '76dbb601d91e9f1443c9d6f52d818bd289d8f5cc'})])])]

                                    """
                                    ##pdb.set_trace()
                                    for refseq in author_source:
                                        del(refseq[1]['hash'])
                                        for prop in refseq:
                                            ref_value = refseq[prop][0].toJSON()['datavalue']['value']
                                            pywikibot.info('{} ({})\t{}'.format(
                                                           get_property_label(prop), prop, ref_value))
                                break
                            elif objectname.upper() == book_author_name.upper():  # Case insensitive comparison
                                pywikibot.info('Variant author name ({}) for {}'.format(
                                               ORIGNAMEPROP, book_author_name))

                        if not authortoadd:
                            ## Stefaan van Biesen possibly <> Stefaan Van Biesen (Case sensitive)
                            pywikibot.info('Unmatched author name {}'.format(objectname))
                        else:
                            # Possibly found as author?
                            # Possibly found as editor?
                            # Possibly found as illustrator/photographer?
                            profession_confirmed = True
                            for prop in author_prop_list:
                                if prop in workitem.claims:
                                    for claim in workitem.claims[prop]:
                                        book_author = claim.target
                                        update_redirect = False
                                        while book_author.isRedirectPage():
                                            update_redirect = True
                                            book_author = book_author.getRedirectTarget()

                                        if update_redirect:
                                            claim.changeTarget(item, bot=wdbotflag, summary=transcmt)
                                        
                                        if book_author.getID() == qnumber:
                                            # Match with ID; author already registered and profession confirmed
                                            authortoadd = False
                                            break
                                        elif item_has_label(book_author, objectname):
                                            # Other item number with same name...
                                            authortoadd = False
                                            # We only add profession when author is unique
                                            profession_confirmed = False
                                            pywikibot.warning('Author has conflicting ID ({}) {} ({})'.format(
                                                              prop, objectname, book_author.getID()))
                                            break

                            # Having written books implies that the profession is author
                            if profession_confirmed:
                                if (PROFESSIONPROP not in item.claims
                                        or not item_is_in_list(item.claims[PROFESSIONPROP], author_profession)):
                                    claim = pywikibot.Claim(repo, PROFESSIONPROP)
                                    claim.setTarget(target_author)
                                    item.addClaim(claim, bot=wdbotflag,
                                                  summary='{} ({}->{}:{})'.format(
                                                          transcmt, AUTHORNAMEPROP, PROFESSIONPROP, AUTHORINSTANCE))
                                    pywikibot.warning('Add profession author ({}:{}) to {} ({})'.format(
                                                      PROFESSIONPROP, AUTHORINSTANCE, objectname, qnumber))

                            if authortoadd:
                                if lang in item.labels:
                                    # Get author name based on work language
                                    itemlabel = item.labels[lang]
                                else:
                                    # Get any author name, preferred languages first
                                    itemlabel = get_item_header(item.labels)

                                # Only add the author if not already done so
                                claim = pywikibot.Claim(repo, AUTHORPROP)
                                claim.setTarget(item)
                                workitem.addClaim(claim, bot=wdbotflag, summary=transcmt)
                                pywikibot.warning('Add {} {} ({}:{})'.format(
                                                  author_name_label, itemlabel, AUTHORPROP, qnumber))

                                if objectname != itemlabel:
                                    # Add alternative name, when different from work author name
                                    qualifier = pywikibot.Claim(repo, ORIGNAMEPROP)
                                    qualifier.setTarget(objectname)
                                    claim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt)
                                    pywikibot.warning('Add {} ({}) for {} ({})'.format(
                                                      orig_name_label, ORIGNAMEPROP, objectname, qnumber))

                                if author_seq:
                                    # Add sequence number, if available
                                    qualifier = pywikibot.Claim(repo, SEQNRPROP)
                                    qualifier.setTarget(author_seq)
                                    claim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt)

                                if author_source:
                                    ## We could possibly move the reference and delete the named author?
                                    try:
                                        claim.addSources(author_source, summary=transcmt + ' Add references')
                                        pywikibot.warning('Add reference {}'.format(author_source))
                                    except Exception as error:  # other exception to be used
                                        # 'list' object has no attribute 'on_item'
                                        pywikibot.error('Error processing {}, {}'.format(qnumber, error))
                                        pywikibot.info(author_source)

                # Try to assign a Commons Category
                commonscat = objectname
                page = pywikibot.Category(site, commonscat)
                if not page.text:
                    # Category page does not exist (yet)
                    pywikibot.info('Empty Wikimedia Commons category page: {}'.format(commonscat))
                    commonscat = ''
                elif COMMONSCATREDIRECTRE.search(page.text):
                    # Should only assign real Category pages
                    pywikibot.warning('Redirect Wikimedia Commons category page: {}'.format(commonscat))
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
                            pywikibot.info('Category:{} ({}) conflicting with {}'.format(
                                           commonscat, qnumber, itmlist))
                            status = 'DupCat'	    # Conflicting category statement
                            errcount += 1
                            exitstat = max(exitstat, 10)
                        commonscat = ''

                if commonscat:
                    if cbotflag and not WDINFOBOXRE.search(page.text):
                        # Add Wikidata Infobox to Wikimedia Commons Category
                        pageupdated = transcmt + ' Add Wikidata Infobox'
                        page.text = '{{Wikidata Infobox}}\n' + re.sub(r'[ \t\r\f\v]+$', '', page.text, flags=re.MULTILINE)
                        pywikibot.warning('Add {} template to Commons {}'.format(
                                          'Wikidata Infobox', page.title()))
                        page.save(summary=pageupdated, minor=True)  # No real content added
                        status = 'Commons'

                    # Add missing category statement
                    if COMMONSCATPROP not in item.claims:
                        claim = pywikibot.Claim(repo, COMMONSCATPROP)
                        claim.setTarget(commonscat)
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)

                # Get nationality
                nationality = get_item_prop_val_object_label(item, [NATIONALITYPROP])
                alias = get_item_header(item.aliases)
                descr = get_item_header(item.descriptions)      # Get description

# (14) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 130)

        except pywikibot.exceptions.MaxlagTimeoutError as error:  # Attempt error recovery
            deltasecs = int((datetime.now() - now).total_seconds())	# Calculate technical error penalty
            pywikibot.error('Error after {:d} seconds for {}, {}'.format(deltasecs, qnumber, error))
            status = 'Error'	    # Handle any generic error
            errcount += 1
            exitstat = max(exitstat, 20)
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

        except pywikibot.exceptions.OtherPageSaveError as error:    # Attempt error recovery
            pywikibot.error('Waiting 30 seconds, {}'.format(error))
            time.sleep(30)

        except Exception as error:  # other exception to be used
            pywikibot.error('Error processing {}, {}'.format(qnumber, error))
            errcount += 1
            status = 'Error'	    # Handle any generic error
            exitstat = max(exitstat, 20)
            pdb.set_trace()
            raise
            pass

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
            pywikibot.info('{:d}\t{}\t{:.3f}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(
                           transcount, isotime, totsecs, instance_label, status,
                           qnumber, objectname, commonscat, alias, nationality, descr))


def show_help_text():
# Show program help and exit (only show head text)
    helptxt = HELPRE.search(codedoc)
    if helptxt:
        pywikibot.info(helptxt.group(0))	# Show helptext
    sys.exit(9)         # Must stop


def get_next_param():
    """
    Get the next command parameter, and handle any qualifiers
    """

    global createmode
    global errwaitfactor
    global exitfatal
    global fallback
    global itemnumber
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter

    if cpar.startswith('-c'):	# force create
        createmode = True
        print('Forced creation mode')
    elif cpar.startswith('-h'):	# help
        show_help_text()
    elif cpar.startswith('-i'):	# overrule item number
        itemnumber = sys.argv.pop(0)
        print('Select item number {}'.format(itemnumber))
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
    elif cpar.startswith('-'):	# unrecognized qualifier (fatal error)
        fatal_error(4, 'Unrecognized qualifier; use -h for help')
    return cpar		# Return the parameter or the qualifier to the caller


"""
    Start main program logic
"""
now = datetime.now()	# Start the main transaction timer

# Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
HELPRE = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
PROPRE = re.compile(r'P[0-9]+')             # P-number
PSUFFRE = re.compile(r'\s*[\[(].*[)\]].*$')		    # Remove trailing () suffix (keep only the base label)
QSUFFRE = re.compile(r'Q[0-9]+')            # Q-number
ROMANRE = re.compile(r'^[a-z .\'åáàâäāãæǣçéèêëėíìîïıńñŋóòôöœøřśßúùûüýÿĳ-]{2,}$', flags=re.IGNORECASE)  # Roman alphabet

# Commons Category + Wikidata infobox
COMMONSCATREDIRECTRE = re.compile(r'{{Category|{{Cat disambig|{{Catredir|{{Cat-redirect|{{Disambiguation', flags=re.IGNORECASE)    # Including: Category redirect
WDINFOBOXRE = re.compile(r'{{Wikidata infobox', flags=re.IGNORECASE)

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
except:
    shell = False
    pywikibot.info('{}, {}, {}, {} (No shell available)'.format(modnm, pgmid, pgmlic, creator))

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

# List allowed instances for properties
## Should we obtain subclass instances?
property_instances = {
    # Instance list
    # Boolean: subclass allowed
    # Boolean: ignore case
    FIRSTNAMEPROP: [{'Q12308941', 'Q3409032', 'Q202444'}, False, False],   # Firstname (will be overruled, based on P1)
    LASTNAMEPROP: [{LASTNAMEINSTANCE, DOUBLELASTNAMEINSTANCE, LASTNAMETOPONYMINSTANCE, LASTNAMECOMPOUNDINSTANCE, LASTNAMEAFFIXINSTANCE, LASTNAMEHYPHNINSTANCE}, False, False],      # Lastname, toponiem, compound, affixed, hyphen
    NATIONALITYPROP: [{'Q3624078', 'Q3024240'}, False, True],             # Nationality
    PROFESSIONPROP: [{'Q28640', 'Q88789639', 'Q12737077', 'Q66811410', 'Q3922583'}, True, True],
    'P6104': [{'Q16695773'}, False, True],
    ## Add other instances
}

itemnumber = None

gender = '-'
while sys.argv and gender.startswith('-'):
    gender = get_next_param()

try:
    # Connect to databases
    init_phase = 'Login'
    site = pywikibot.Site('commons')
    site.login()
    cbotflag = 'bot' in pywikibot.User(site, site.user()).groups()

    # This script requires a bot flag
    repo = site.data_repository()
    repo.login()            # Must login
    wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

    # Prebuild targets
    init_phase = 'Data'
    author_name_label = get_property_label(AUTHORPROP)
    neq_propty_label = get_property_label(NOTEQTOPROP)
    orig_name_label = get_property_label(ORIGNAMEPROP)

    target_author = get_item_page(AUTHORINSTANCE)

    targetx = {
        # Default values
        INSTANCEPROP: get_item_page('Q5'),           # Human
        GENDERPROP: get_item_page('Q6581097'),       # Template value; will be overruled via parameter P1
        NATIONALITYPROP: get_item_page('Q31'),       # default BE: Can be overruled, or disabled
        ## Other statements?
    }

    # Set gender parameters
    if gender[:1] in 'fvw':     # female
        targetx[GENDERPROP] = get_item_page('Q6581072')
        property_instances[FIRSTNAMEPROP][0] = {'Q11879590', 'Q3409032', 'Q202444'}
    elif gender[:1] in 'hm':    # male
        targetx[GENDERPROP] = get_item_page('Q6581097')
        property_instances[FIRSTNAMEPROP][0] = {'Q12308941', 'Q3409032', 'Q202444'}
    elif gender[:1] == 'ix':    # intersex
        targetx[GENDERPROP] = get_item_page('Q1097630')
        property_instances[FIRSTNAMEPROP][0] = {'Q12308941', 'Q11879590', 'Q3409032', 'Q202444'}
    elif gender[:1] == 'nq':    # non-binary
        targetx[GENDERPROP] = get_item_page('Q48270')
        property_instances[FIRSTNAMEPROP][0] = {'Q3409032', 'Q202444'}
    elif gender[:1] in 'FVW':   # trans-woman
        targetx[GENDERPROP] = get_item_page('Q1052281')
        property_instances[FIRSTNAMEPROP][0] = {'Q11879590', 'Q3409032', 'Q202444'}
    elif gender[:1] in 'HM':    # trans-man
        targetx[GENDERPROP] = get_item_page('Q2449503')
        property_instances[FIRSTNAMEPROP][0] = {'Q12308941', 'Q3409032', 'Q202444'}
    else:
        fatal_error(3, 'Unknown gender, {}'.format(gender[:1]))

    instance_label = get_item_header(targetx[INSTANCEPROP].labels)

    # Get all P/Q claims from parameter list
    while sys.argv:
        inpar = sys.argv.pop(0).upper()
        inprop = PROPRE.findall(inpar)[0]
        if ':-' in inpar:
            if inprop in targetx:
                del(targetx[inprop])
        else:
            if ':Q' not in inpar and '=' not in inpar:
                inpar = sys.argv.pop(0)
            inparQ = QSUFFRE.findall(inpar.upper())

            if inparQ:
                targetx[inprop] = get_item_page(inparQ[0])
            elif inpar == '-':
                if inprop in targetx:
                    del(targetx[inprop])
            elif inprop not in property_instances:
                fatal_error(20, 'Unknown instance for property {}'.format(inprop))
            # Should handle other data types then Q-number
            else:
                ##pdb.set_trace()
                # Get first Q-number from label (we assume good luck -> result is shown)
                inpar = unescape_string(inpar)
                targetx[inprop] = get_item_list(inpar, property_instances[inprop][0],
                                                property_instances[inprop][1],
                                                property_instances[inprop][2]).pop()
    # Print preferences
    pywikibot.log('Main language:\t%s' % mainlang)
    pywikibot.log('Maximum delay:\t%d s' % maxdelay)
    pywikibot.log('Show code:\t%s' % createmode)
    pywikibot.log('Verbose mode:\t%s' % verbose)
    pywikibot.log('Exit on fatal error:\t%s' % exitfatal)
    pywikibot.log('Error wait factor:\t%d' % errwaitfactor)

    # List the statements
    for propty in targetx:
        proptyx = pywikibot.PropertyPage(repo, propty)
        pywikibot.info('Statement {}:{} ({}:{})'.format(
                    get_property_label(proptyx), get_item_header(targetx[propty].labels),
                    propty, targetx[propty].getID()))

    deltasecs = int((datetime.now() - now).total_seconds())
    pywikibot.info('{:d} seconds to initialise'.format(deltasecs))

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
            pywikibot.debug('{}\t{}\t{}\t{}'.format(
                            site, site.username(),
                            site.is_oauth_token_available(), site.logged_in()))
except Exception as error:
    # Other exception to be used
    fatal_error(20, '{} error, {}'.format(init_phase, error))

sys.exit(exitstat)

