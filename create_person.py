#!/usr/bin/python3

codedoc = """
Create a person; it allows to set a list of claims, if not already registered

Parameters:

    P1: gender (m/f/x/q/M/F)
    
    P2,P3...: optional additional claims (possibility to overrule default claims)

    Default claims that can be overruled: e.g. P27 Q31 (nationality:BE).
    Use value - to skip a default claim (like e.g. P27 - "nationality none")

Qualifiers:

    -c: Forced creation of new item (overrule homonym issue)

stdin:

    List of persons, in the following format:

    With a comma: lastname,firstname
        Preferred => automatically register firstname and lastname to the item

    Plain name: firstname(s) lastname
        Fallback format.
        Only possible when there are only two names (not combined firstnames, nor multi-part lastnames)

Functionality:

    Add author statements to publications

Return status:

    The following status is returned to the shell:

	0 Normal termination
	1 Help requested (-h)
    3 Invalid or missing parameter
    13 Maxlag error
    20 General error
    130 Ctrl-c pressed, program interrupted

Author:

	Geert Van Pamel, 2021-01-08, MIT License, User:Geertivp

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

    Duplicates can possibly be created with augmented replication delays.
    Do not run this script repeatedly for the same person.

"""

# List the required modules
import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import time		    	# sleep
import unidecode        # Unicode

from datetime import datetime	# now, strftime, delta time, total_seconds
from pywikibot.data import api

# Global variables
modnm = 'Pywikibot create_person'   # Module name (using the Pywikibot package)
pgmid = '2024-10-07 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

# Technical configuration flags
MAINLANG = 'en:mul'

# Defaults: be transparent and safe
errorstat = True    # Show error statistics (disable with -e)
exitfatal = True	# Exit on fatal error (can be disabled with -p; please take care)
readonly = False    # Dry-run
shell = True		# Shell available (command line parameters are available; automatically overruled by PAWS)
showcode = False	# Show the generated SPARQL code (activate with -c)
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

# Properties
GENREPROP = 'P21'
NATIONALITYPROP = 'P27'
INSTANCEPROP = 'P31'
AUTHORPROP = 'P50'
EDITORPROP = 'P98'
PROFESSIONPROP = 'P106'
ILLUSTRATORPROP = 'P110'
PUBLISHERPROP = 'P123'
ISBNPROP = 'P212'
OCLDIDPROP = 'P243'
REFPROP = 'P248'
SUBCLASSPROP = 'P279'
EDITIONLANGPROP = 'P407'
WIKILANGPROP = 'P424'
PUBYEARPROP = 'P577'
WRITTENWORKPROP = 'P629'
LASTNAMEPROP = 'P734'
FIRSTNAMEPROP = 'P735'
EDITIONPROP = 'P747'
REFDATEPROP = 'P813'
MAINSUBPROP = 'P921'
ISBN10PROP = 'P957'
DEWCLASIDPROP = 'P1036'
EDITIONTITLEPROP = 'P1476'
SEQNRPROP = 'P1545'
EDITIONSUBTITLEPROP = 'P1680'
ORIGNAMEPROP = 'P1932'
AUTHORNAMEPROP = 'P2093'
FASTIDPROP = 'P2163'
PREFACEBYPROP = 'P2679'
AFTERWORDBYPROP = 'P2680'
OCLCWORKIDPROP = 'P5331'
LIBCONGCLASSPROP = 'P8360'

# Instances
AFFIXLASTNAMEINSTANCE = 'Q66480858'
AUTHORINSTANCE = 'Q482980'
LASTNAMEINSTANCE = 'Q101352'
TOPONYMLASTNAMEINSTANCE = 'Q17143070'
WRITERINSTANCE = 'Q36180'

all_languages = ['mul']  # Add labels for all those languages

author_prop_list = [AUTHORPROP, EDITORPROP, ILLUSTRATORPROP, PREFACEBYPROP, AFTERWORDBYPROP]

author_profession = {
AUTHORINSTANCE,
WRITERINSTANCE,
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


def item_is_in_list(statement_list, itemlist):
    """
    Verify if statement list contains at least one item from the itemlist
    param: statement_list: Statement list
    param: itemlist:      List of values
    return: First matching, or empty string
    """
    for seq in statement_list:
        try:
            isinlist = seq.getTarget().getID()
            if isinlist in itemlist:
                return isinlist
        except:
            pass    # Ignore NoneType error
    return ''


def item_has_label(item, label):
    """
    Verify if the item has a label

    Parameters:

        item: Item
        label: Item label (string)

    Returns:

        Matching string
    """
    label = unidecode.unidecode(label).casefold()
    for lang in item.labels:
        if unidecode.unidecode(item.labels[lang]).casefold() == label:
            return item.labels[lang]

    for lang in item.aliases:
        for seq in item.aliases[lang]:
            if unidecode.unidecode(seq).casefold() == label:
                return seq
    return ''


def get_item_list(item_name: str, instance_id) -> list:
    """Get list of items by name, belonging to an instance (list)

    :param item_name: Item name (string; case sensitive)
    :param instance_id: Instance ID (set, or list)
    :return: List of items (Q-numbers)

    See https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    """
    pywikibot.debug('Search label: {}'.format(item_name.encode('utf-8')))
    item_list = set()                   # Empty set
    params = {'action': 'wbsearchentities',
              'search': item_name,      # Get item list from label
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
        # Loop though items
        for row in result['search']:
            ##print(row)
            item = get_item_page(row['id'])

            # Matching instance, strict equal comparison
            # Remark that most items have a proper instance
            if SUBCLASSPROP not in item.claims and (
                    INSTANCEPROP not in item.claims
                    or item_is_in_list(item.claims[INSTANCEPROP], instance_id)):
                # Search all languages both for labels and aliases
                for lang in item.labels:
                    if item_name == item.labels[lang]:
                        item_list.add(item.getID())     # Label match
                        break
                for lang in item.aliases:
                    for seq in item.aliases[lang]:
                        if item_name == seq:
                            item_list.add(item.getID()) # Alias match
                            break
    pywikibot.log(item_list)
    # Convert set to list; keep sort order (best matches first)
    return list(item_list)


def get_item_with_prop_value (prop: str, propval: str) -> list:
    """Get list of items that have a property/value statement

    :param prop: Property ID (string)
    :param propval: Property value (string; case insensitieve)
    :return: List of items (Q-numbers)

    See https://www.mediawiki.org/wiki/API:Search
    """
    pywikibot.debug('Search statement: ' + prop + ':' + propval)
    item_name_canon = unidecode.unidecode(propval).casefold()
    item_list = set()                   # Empty set
    params = {'action': 'query',        # Statement search
              'list': 'search',
              'srsearch': prop + ':' + propval,
              'srwhat': 'text',
              'format': 'json',
              'srlimit': 50}            # Should be reasonable value
    request = api.Request(site=repo, parameters=params)
    result = request.submit()
    # https://www.wikidata.org/w/api.php?action=query&list=search&srwhat=text&srsearch=P212:978-94-028-1317-3

    if 'query' in result and 'search' in result['query']:
        # Loop though items
        for row in result['query']['search']:
            qnumber = row['title']
            item = get_item_page(qnumber)

            if prop in item.claims:
                for seq in item.claims[prop]:
                    if unidecode.unidecode(seq.getTarget()).casefold() == item_name_canon:
                        item_list.add(item.getID()) # Found match
                        break
    # Convert set to list
    return sorted(item_list)


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
                except:     # Skip unlabeled items
                    pass
            break
    return item_prop_val


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
    pywikibot.info('Processing %d statements' % (len(itemlist)))

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
      name = newitem.split(',')
      if len(name) == 2:
          # Reorder lastname, firstname
          # Remove multiple spaces
          firstname = ' '.join(name[1].split())
          lastname = ' '.join(name[0].split())
          if not firstname:
            objectname = lastname
          elif not lastname:
            objectname = firstname
          else:
            objectname = firstname + ' ' + lastname
      elif len(name) == 1:
          # Only spaces
          name = newitem.split()
          if len(name) == 2:
              firstname = name[0].replace('_', ' ')
              lastname = name[1].replace('_', ' ')
              objectname = firstname + ' ' + lastname
          else:
              objectname = ' '.join(name)
      else:
          pywikibot.error('Bad name: {}'.format(name))

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
        alias = []
        descr = {}
        commonscat = '' # Commons category
        nationality = ''
        qnumber = ''    # In case or error

        try:			# Error trapping (prevents premature exit on transaction error)
            # Get all matching items
            name_list = get_item_list(objectname, [target[INSTANCEPROP]])

            ## Known problem: item without INSTANCEPROP can cause duplicates
            if not name_list or showcode:
                # Create new item
                label['mul'] = objectname

                try:
                    item = pywikibot.ItemPage(repo)             # Create item
                    item.editEntity( {'labels': label}, summary=transcmt)
                    qnumber = item.getID()
                    pywikibot.warning('Created person {} ({})'
                                      .format(objectname, qnumber))
                except pywikibot.exceptions.OtherPageSaveError as error:
                    pywikibot.error('Error creating %s, %s' % (objectname, error))
                    status = 'Error'	    # Handle any generic error
                    errcount += 1
                    exitstat = max(exitstat, 10)
            elif len(name_list) == 1:
                status = 'Update'              # Update item
                item = get_item_page(name_list[0])
                qnumber = item.getID()

                for lang in all_languages:
                    if lang not in item.labels:
                        item.labels[lang] = objectname
                    elif item.labels[lang] == objectname:
                        pass
                    elif lang not in item.aliases:
                        item.aliases[lang] = [objectname]
                    elif objectname not in item.aliases[lang]:
                        item.aliases[lang].append(objectname)    # Merge aliases

                # Remove duplicate labels
                for lang in item.labels:
                    if lang in item.aliases:
                        while item.labels[lang] in item.aliases[lang]:
                            item.aliases[lang].remove(item.labels[lang])

                item.editEntity( {'labels': item.labels, 'aliases': item.aliases}, summary=transcmt)
                pywikibot.info('Found person {} ({})'
                                  .format(objectname, qnumber))
            else:
                status = 'Ambiguous'            # Item is not unique
                pywikibot.error('Ambiguous person name {} {}'.format(objectname, name_list))

# Register claims
            if status in ['OK', 'Update']:
                for propty in targetx:           # Verify if value is already registered
                    propstatus = 'OK'
                    # Property is already registered
                    if propty in item.claims:
                        for seq in item.claims[propty]:
                            val = seq.getTarget()
                            if val == targetx[propty]:
                                propstatus = 'Skip'
                            else:
                                propstatus = 'other'
                                pywikibot.warning('Possible conflicting statement {}:{} - {} for {}'
                                                  .format(propty, target[propty], val.getID(), qnumber))

                    if propstatus == 'OK':      # Claim is missing, so add it now
                        claim = pywikibot.Claim(repo, propty)
                        claim.setTarget(targetx[propty])
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                        pywikibot.warning('Adding statement {}:{} ({}:{}) to {} ({})'
                                          .format(get_property_label(propty), get_item_header(targetx[propty].labels),
                                                  propty, target[propty], objectname, qnumber))

# Assign first name and last name
                name_target = [('first name', FIRSTNAMEPROP, firstname),
                               ('last name', LASTNAMEPROP, lastname)]

                for seq in name_target:
                    if seq[2] and seq[1] not in item.claims:
                        name_list = get_item_list(seq[2], propreqinst[seq[1]])
                        if len(name_list) == 1:
                            claim = pywikibot.Claim(repo, seq[1])
                            claim.setTarget(pywikibot.ItemPage(repo, name_list[0]))
                            item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                            pywikibot.warning('Add {}:{} ({}:{}) to {} ({})'
                                              .format(seq[0], seq[2], seq[1], name_list[0],
                                                      objectname, qnumber))
                        elif name_list:
                            pywikibot.error('Ambiguous {} {} {}'.format(seq[0], seq[2], name_list))
                        else:
                            pywikibot.error('Unknown {} {}'.format(seq[0], seq[2]))

                # Search all works where the person is author (as text)
                work_list = get_item_with_prop_value(AUTHORNAMEPROP, objectname)

                if work_list and not showcode:
                    # Having written books implies that the profession is author
                    if (PROFESSIONPROP not in item.claims
                            or not item_is_in_list(item.claims[PROFESSIONPROP], author_profession)):
                        claim = pywikibot.Claim(repo, PROFESSIONPROP)
                        claim.setTarget(target_author)
                        item.addClaim(claim, bot=wdbotflag,
                                      summary='{} ({}->{}:{})'
                                              .format(transcmt, AUTHORNAMEPROP, PROFESSIONPROP, AUTHORINSTANCE))
                        pywikibot.warning('Add profession:author ({}:{}) to {} ({})'
                                          .format(PROFESSIONPROP, AUTHORINSTANCE, objectname, qnumber))

                    ##authortoadd = True##
                    for work in work_list:
                        # Update all works to include the author as item number
                        workitem = get_item_page(work)
                        work = workitem.getID()

                        # Get the first work title
                        for lang in workitem.labels:
                            pywikibot.info('({}) {}:{}'.format(work, lang, workitem.labels[lang]))
                            break

                        # Reuse sequence number if available
                        author_seq = ''
                        author_source = []
                        for claim in workitem.claims[AUTHORNAMEPROP]:
                            if objectname == claim.getTarget():
                                author_source = claim.getSources()
                                if SEQNRPROP in claim.qualifiers:
                                    author_seq = claim.qualifiers[SEQNRPROP][0].getTarget()
                                break

                        """
Q98217518 en:Cumulative surgical morbidity in patients with multiple cerebellar and medullary hemangioblastomas
Claim.fromJSON(DataSite("wikidata", "wikidata"), {'mainsnak': {'snaktype': 'value', 'property': 'P2093', 'datatype': 'string', 'datavalue': {'value': 'Christine Steiert', 'type': 'string'}}, 'type': 'statement', 'id': 'Q98217518$8554D611-ED01-4763-A05F-732BE98A254B', 'rank': 'normal', 'qualifiers': {'P1545': [{'snaktype': 'value', 'property': 'P1545', 'datatype': 'string', 'datavalue': {'value': '2', 'type': 'string'}, 'hash': '7241753c62a310cf84895620ea82250dcea65835'}]}, 'qualifiers-order': ['P1545'], 'references': [{'snaks': {'P248': [{'snaktype': 'value', 'property': 'P248', 'datatype': 'wikibase-item', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 5412157}, 'type': 'wikibase-entityid'}}], 'P698': [{'snaktype': 'value', 'property': 'P698', 'datatype': 'external-id', 'datavalue': {'value': '32758916', 'type': 'string'}}], 'P854': [{'snaktype': 'value', 'property': 'P854', 'datatype': 'url', 'datavalue': {'value': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:32758916%20AND%20SRC:MED&resulttype=core&format=json', 'type': 'string'}}], 'P813': [{'snaktype': 'value', 'property': 'P813', 'datatype': 'time', 'datavalue': {'value': {'time': '+00000002020-08-10T00:00:00Z', 'precision': 11, 'after': 0, 'before': 0, 'timezone': 0, 'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'}, 'type': 'time'}}]}, 'snaks-order': ['P248', 'P698', 'P854', 'P813'], 'hash': 'a784119ff1a495da77d16ea495ef682bd031b78f'}]})

[OrderedDict([('P248', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P248', 'datatype': 'wikibase-item', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 5412157}, 'type': 'wikibase-entityid'}, 'hash': '34fcf5326193945785486d2488cfa4312ff09ddf'})]), ('P932', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P932', 'datatype': 'external-id', 'datavalue': {'value': '9102569', 'type': 'string'}, 'hash': '34fcf5326193945785486d2488cfa4312ff09ddf'})]), ('P854', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P854', 'datatype': 'url', 'datavalue': {'value': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=PMCID:PMC9102569&resulttype=core&format=json', 'type': 'string'}, 'hash': '34fcf5326193945785486d2488cfa4312ff09ddf'})]), ('P813', [Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P813', 'datatype': 'time', 'datavalue': {'value': {'time': '+00000002022-06-08T00:00:00Z', 'precision': 11, 'after': 0, 'before': 0, 'timezone': 0, 'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'}, 'type': 'time'}, 'hash': '34fcf5326193945785486d2488cfa4312ff09ddf'})])])]

volgnummer: Claim.fromJSON(DataSite("wikidata", "wikidata"), {'snaktype': 'value', 'property': 'P1545', 'datatype': 'string', 'datavalue': {'value': '2', 'type': 'string'}, 'hash': '7241753c62a310cf84895620ea82250dcea65835'})
                        """
                        # Possibly found as author?
                        # Possibly found as editor?
                        # Possibly found as illustrator/photographer?
                        authortoadd = True
                        for prop in workitem.claims:
                            if prop in author_prop_list:
                                for claim in workitem.claims[prop]:
                                    book_author = claim.getTarget()
                                    if book_author.getID() == qnumber:
                                        authortoadd = False
                                        break
                                    elif item_has_label(book_author, objectname):
                                        authortoadd = False
                                        pywikibot.warning('has conflicting author ({}) {} ({})'
                                                          .format(prop, objectname, book_author.getID()))
                                        break

                        if authortoadd:
                            # Only add the author if not already done so
                            itemlabel = get_item_header(item.labels)
                            claim = pywikibot.Claim(repo, AUTHORPROP)
                            claim.setTarget(item)
                            workitem.addClaim(claim, bot=wdbotflag, summary=transcmt)
                            pywikibot.warning('Add author:{} ({}:{})'
                                              .format(itemlabel, AUTHORPROP, qnumber))

                            if author_seq:
                                # Add sequence number
                                qualifier = pywikibot.Claim(repo, SEQNRPROP)
                                qualifier.setTarget(author_seq)
                                claim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt)

                            if objectname != itemlabel:
                                # Add alternative name
                                qualifier = pywikibot.Claim(repo, ORIGNAMEPROP)
                                qualifier.setTarget(objectname)
                                claim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt)
                                pywikibot.warning('Add {}:{} ({}:{})'
                                                  .format(get_property_label(ORIGNAMEPROP), objectname,
                                                          ORIGNAMEPROP, qnumber))

                            # Include references, when applicable
                            if author_source:
                                # Not all refences should be duplicated...
                                # Maybe better at item instance... (?)
                                for prop in author_source[0]:
                                    pywikibot.info('{} ({})\t{}'.format(
                                            get_property_label(prop), prop,
                                            author_source[0][prop][0].toJSON()['datavalue']['value']))
                """
###Need to reconstruct the source, otherwise AttributeError: 'str' object has no attribute 'on_item'
                            if author_source[0]:
                                claim.addSources(author_source[0], bot=wdbotflag, summary=transcmt)
                """
                # Get nationality
                nationality = get_prop_val_object_label(item, [NATIONALITYPROP])

# (14) Error handling
        except KeyboardInterrupt:
            status = 'Stop'	# Ctrl-c trap; process next language, if any
            exitstat = max(exitstat, 130)

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
            pywikibot.info('%d\t%s\t%f\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (transcount, isotime, totsecs, status, qnumber, objectname, commonscat, alias, nationality, descr))


def show_help_text():
# Show program help and exit (only show head text)
    helptxt = HELPRE.search(codedoc)
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

    global showcode
    global errwaitfactor
    global exitfatal
    global fallback
    global readonly
    global verbose

    cpar = sys.argv.pop(0)	    # Get next command parameter

    if cpar.startswith('-c'):	# code check
        showcode = True
        print('Show generated code')
    elif cpar.startswith('-e'):	# error stat
        errorstat = False
        print('Disable error statistics')
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
    elif cpar.startswith('-r'):	# readonly mode
        readonly = True
        print('Setting readonly mode')
    elif cpar.startswith('-v'):	# verbose mode
        verbose = True
        print('Setting verbose mode')
    elif cpar.startswith('-V'):	# Version
        show_prog_version()
    elif cpar.startswith('-'):	# unrecognized qualifier (fatal error)
        fatal_error(4, 'Unrecognized qualifier; use -h for help')
    return cpar		# Return the parameter or the qualifier to the caller


# Main program entry
if verbose:
    show_prog_version()	    	# Print the module name

try:
    pgmnm = sys.argv.pop(0)	    # Get the name of the executable
    pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
except:
    shell = False
    pywikibot.info('No shell available')	# Most probably running on PAWS Jupyter

"""
    Start main program logic
    Precompile the Regular expressions, once (for efficiency reasons; they will be used in loops)
"""
HELPRE = re.compile(r'^(.*\n)+\nDocumentation:\n\n(.+\n)+')  # Help text
PROPRE = re.compile(r'P[0-9]+')             # P-number
QSUFFRE = re.compile(r'Q[0-9]+')            # Q-number
ROMANRE = re.compile(r'^[a-z .,"()\'åáàâäāæǣçéèêëėíìîïıńñŋóòôöœøřśßúùûüýÿĳ-]{2,}$', flags=re.IGNORECASE)  # Roman alphabet

target = {
    INSTANCEPROP: 'Q5',
    GENREPROP: 'Q6581097',      # Template value; will be overruled via parameter P1
    NATIONALITYPROP: 'Q31',     # BE: Can be overruled
}

propreqinst = {
    FIRSTNAMEPROP: {'Q12308941', 'Q3409032', 'Q202444'},    # Firstname (will be overruled, based on P1)
    LASTNAMEPROP: {LASTNAMEINSTANCE, TOPONYMLASTNAMEINSTANCE, 'Q60558422', AFFIXLASTNAMEINSTANCE},      # Lastname, toponiem, compound, affixed
}

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

gender = '-'
while sys.argv and gender.startswith('-'):
    gender = get_next_param()

if gender[:1] in 'fvw':     # female
    target[GENREPROP] = 'Q6581072'
    propreqinst[FIRSTNAMEPROP] = {'Q11879590', 'Q3409032', 'Q202444'}
elif gender[:1] in 'hm':    # male
    target[GENREPROP] = 'Q6581097'
    propreqinst[FIRSTNAMEPROP] = {'Q12308941', 'Q3409032', 'Q202444'}
elif gender[:1] == 'ix':    # intersex
    target[GENREPROP] = 'Q1097630'
    propreqinst[FIRSTNAMEPROP] = {'Q12308941', 'Q11879590', 'Q3409032', 'Q202444'}
elif gender[:1] == 'nq':    # non-binary
    target[GENREPROP] = 'Q48270'
    propreqinst[FIRSTNAMEPROP] = {'Q3409032', 'Q202444'}
elif gender[:1] in 'FVW':   # trans-woman
    target[GENREPROP] = 'Q1052281'
    propreqinst[FIRSTNAMEPROP] = {'Q11879590', 'Q3409032', 'Q202444'}
elif gender[:1] in 'HM':    # trans-man
    target[GENREPROP] = 'Q2449503'
    propreqinst[FIRSTNAMEPROP] = {'Q12308941', 'Q3409032', 'Q202444'}
else:
    fatal_error(3, 'Unknown gender')

# Set all claims in parameter list
while sys.argv:
    inpar = sys.argv.pop(0).upper()
    inprop = PROPRE.findall(inpar)[0]
    if ':-' in inpar:
        target[inprop] = '-'
    else:
        if ':Q' not in inpar:
            inpar = sys.argv.pop(0).upper()
        try:
            target[inprop] = QSUFFRE.findall(inpar)[0]
        except IndexError:
            target[inprop] = '-'

# Print preferences
pywikibot.log('Main language:\t%s' % mainlang)
pywikibot.log('Maximum delay:\t%d s' % maxdelay)
pywikibot.log('Show code:\t%s' % showcode)
pywikibot.log('Verbose mode:\t%s' % verbose)
pywikibot.log('Readonly mode:\t%s' % readonly)
pywikibot.log('Exit on fatal error:\t%s' % exitfatal)
pywikibot.log('Error wait factor:\t%d' % errwaitfactor)

# Connect to database
transcmt = '#pwb Create person'	    	    # Wikidata transaction comment
repo = pywikibot.Site('wikidata')  # Login to Wikibase instance
repo.login()            # Must login

# This script requires a bot flag
wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

# Prebuilt targets
target_author = pywikibot.ItemPage(repo, AUTHORINSTANCE)

targetx={}
for propty in target:
    if target[propty] != '-':
        proptyx = pywikibot.PropertyPage(repo, propty)
        targetx[propty] = pywikibot.ItemPage(repo, target[propty])
        pywikibot.info('Statement {}:{} ({}:{})'
                       .format(get_property_label(propty), get_item_header(targetx[propty].labels),
                               propty, target[propty]))

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
