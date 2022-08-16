#!/home/geertivp/pwb/bin/python3

codedoc = """
Pywikibot script to get ISBN data from a digital library,
and create or amend the related Wikidata item for edition (with external ID P212).

Use digital libraries to get ISBN data in JSON format, and integrate the results into Wikidata.

Parameters:

    All parameters are optional:

        P1:         digital library (default goob "-")

            bnf     Catalogue General (France)
            bol     Bol.com
            dnb     Deutsche National Library
            goob    Google Books
            kb      National Library of the Netherlands
            loc     Library of Congress US
            mcues   Ministerio de Cultura (Spain)
            openl   OpenLibrary.org
            porbase urn.porbase.org Portugal
            sbn     Servizio Bibliotecario Nazionale
            wiki    wikipedia.org
            worldcat    WorldCat

        P2:         ISO 639-1 language code
                Default LANG; e.g. en, nl, fr, de, es, it, etc.

        P3 P4...:   P/Q pairs to add additional claims (repeated)
                e.g. P921 Q107643461 (main subject: database management linked to P2163 Fast ID)

    stdin: ISBN numbers (International standard book number)
        Free text (e.g. Wikipedia references list, or publication list) is accepted.
        Identification is done via an ISBN regex expression.

Functionality:

    * The ISBN number is used as a primary key (no duplicates allowed)
        The data update is not performed when no unique match
    * Statements are added or merged incrementally; existing data is not overwritten.
    * Authors and publishers are searched to get their item number (ambiguous items are skipped)
    * Book title and subtitle are separated with '.', ':', or '-'
    * This script can be run incrementally with the same parameters
        Caveat: Take into account the Wikidata Query database replication delay.
        Wait for minimum 5 minutes to avoid creating duplicate objects.

Data quality:

    * Use https://query.wikidata.org/querybuilder/ to identify P212 duplicates
        Merge duplicate items before running the script again.

Examples:

    # Default library (Google Books), language (LANG), no additional statements
    ./create_isbn_edition.py
    9789042925564

    # Wikimedia, language Dutch, main subject: database management
    ./create_isbn_edition.py wiki en P921 Q107643461
    978-0-596-10089-6

Return status:

    The following status codes are returned to the shell:

        3   Invalid or missing parameter
        12  Item does not exist

Standard ISBN properties:

    P31:Q3331189:   instance of edition
    P50:    author
    P123:   publisher
    P212:   canonical ISBN number (lookup via Wikidata Query)
    P407:   language of work (Qnumber linked to ISO 639-1 language code)
    P577:   date of publication (year)
    P1476:  book title
    P1680:  subtitle

Other ISBN properties:

    P291:   place of publication
    P921:   main subject (inverse lookup from external Fast ID P2163)
    P1104:  number of pages

Qualifiers:

    P1545:  (author) sequence number

External identifiers:

    P213:   ISNI ID
    P243:   OCLC ID
    P496:   ORCID iD
    P675:   Google Books-identificatiecode
    P1036:  Dewey Decimal Classification
    P2163:  Fast ID (inverse lookup via Wikidata Query) -> P921: main subject
    P5331:  OCLC work ID

Author:

    Geert Van Pamel, 2022-08-04, GNU General Public License v3.0, User:Geertivp

Documentation:

    https://www.geeksforgeeks.org/searching-books-with-python/
    https://www.freecodecamp.org/news/python-json-how-to-convert-a-string-to-json/
    https://pypi.org/project/isbnlib/
    https://www.wikidata.org/wiki/Property:P212
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Books
    WikiProject Books:  https://www.wikidata.org/wiki/Q21831105
    https://www.wikidata.org/wiki/Wikidata:List_of_properties/work
    https://www.wikidata.org/wiki/Template:Book_properties
    https://www.wikidata.org/wiki/Template:Bibliographic_properties
    http://classify.oclc.org/classify2/ClassifyDemo
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData
    WikiCite:   https://www.wikidata.org/wiki/Q21831105
    https://www.wikidata.org/wiki/Help:Sources
    https://www.wikidata.org/wiki/Q22696135
    https://meta.wikimedia.org/wiki/Community_Wishlist_Survey_2021/Wikidata/Bibliographical_references/sources_for_wikidataitems
    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_qualifiers
    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html
    https://doc.wikimedia.org/pywikibot/master/
    https://docs.python.org/3/howto/logging.html
    https://wikitech.wikimedia.org/wiki/Portal:Toolforge
    http://www.isbn.org/standards/home/isbn/international/hyphenation-instructions.asp

Prerequisites:

    pywikibot

    Install the following ISBN lib packages:
    https://pypi.org/search/?q=isbnlib_

        pip install isbnlib (mandatory)
        
        (optional)
        pip install isbnlib-bol
        pip install isbnlib-bnf
        pip install isbnlib-dnb
        pip install isbnlib-kb
        pip install isbnlib-loc
        pip install isbnlib-worldcat2
        etc.

Restrictions:

    * Better use the ISO 639-1 language code parameter as a default
        The language code is not always available from the digital library.
    * SPARQL queries run on a replicated database
        Possible important replication delay; wait 5 minutes before retry -- otherwise risk for creating duplicates.

Known problems:

    * Unknown ISBN, e.g. 9789400012820
    * No ISBN data available for an edition either causes no output (goob = Google Books), or an error message (wiki, openl)
        The script is taking care of both
    * Only 6 ISBN attributes are listed by the webservice(s)
        missing are e.g.: place of publication, number of pages
    * Not all ISBN atttributes have data (authos, publisher, date of publication, language)
    * The script uses multiple webservice calls (script might take time, but it is automated)
    * Need to amend ISBN items that have no author, publisher, or other required data (which additional services to use?)
    * How to add still more digital libraries?
        * Does the KBR has a public ISBN service (Koninklijke Bibliotheek van België)?

To do:

    * Add source reference (digital library instance)

Algorithm:

    Get parameters
    Validate parameters
    Get ISBN data
    Convert ISBN data
    Get additional data
    Register ISBN data into Wikidata (create or amend items or claims)

Environment:

    The python script can run on the following platforms:
    
        Linux client
        Google Chromebook (Linux container)
        Toolforge Portal
        PAWS

    LANG: ISO 639-1 language code

Source code:

    https://github.com/geertivp/Pywikibot/blob/main/create_isbn_edition.py

Applications:

    Generate a book reference
        Example: {{Cite Q|Q63413107}}
        See also:
            https://meta.wikimedia.org/wiki/WikiCite
            https://www.wikidata.org/wiki/Q22321052
            https://www.mediawiki.org/wiki/Global_templates
            https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData

Wikidata Query:

    List of editions about musicians - https://w.wiki/5aaz

Related projects:

    https://phabricator.wikimedia.org/T314942 (this script)
    
    (other projects)
    https://phabricator.wikimedia.org/T282719
    https://phabricator.wikimedia.org/T214802
    https://phabricator.wikimedia.org/T208134
    https://phabricator.wikimedia.org/T138911
    https://phabricator.wikimedia.org/T20814
    https://en.wikipedia.org/wiki/User:Citation_bot
    https://meta.wikimedia.org/wiki/Community_Wishlist_Survey_2021/Wikidata/Bibliographical_references/sources_for_wikidataitems

Other systems:

    https://en.wikipedia.org/wiki/bibliographic_database
    https://www.titelbank.nl/pls/ttb/f?p=103:4012:::NO::P4012_TTEL_ID:3496019&cs=19BB8084860E3314502A1F777F875FE61

"""

import logging          # Error logging
import os               # Operating system
import re		    	# Regular expressions (very handy!)
import sys              # System calls
import unidecode        # Unicode
import pywikibot		# API interface to Wikidata
from isbnlib import *   # ISBN data
from pywikibot import pagegenerators as pg # Wikidata Query interface
from pywikibot.data import api

# Initialisation
debug = True            # Show debugging information
verbose = True          # Verbose mode

booklib = 'goob'        # Default digital library
isbnre = re.compile(r'[0-9-]{13,}')         # ISBN number: 13 digits with optional dashes (-)
propre = re.compile(r'P[0-9]+')             # Wikidata P-number
qsuffre = re.compile(r'Q[0-9]+')            # Wikidata Q-number

# Other statements are added via command line parameters
target = {
'P31':'Q3331189',                           # Is an instance of an edition
}

# Statement property and instance validation rules
propreqinst = {
'P407':{'Q34770', 'Q33742', 'Q1288568'},    # (living, natural) language
# Add here more validation rules
}

mainlang = os.getenv('LANG', 'en')[:2]      # Default description language

# Connect to database
transcmt = '#pwb Create ISBN edition'	    	        # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()                  # Required for wikidata object access (item, property, statement)


def is_in_list(statement_list, checklist):
    """
Verify if statement list contains at least one item from the checklist

Parameters:

    statement_list: Statement list

    checklist:      List of values (string)

Returns:

    Boolean (True when match)
    """

    for seq in statement_list:
        if seq.getTarget().getID() in checklist:
            isinlist = True
            break
    else:
        isinlist = False
    return isinlist


def get_item_list(item_name, instance_id):
    """
Get list of items by name, belonging to an instance (list)

Parameters:

    item_name:      Item name (string; case sensitive)

    instance_id:    Instance ID (string, set, or list)

Returns:

    Set of items (Q-numbers)
    """

    item_list = set()       # Empty set
    params = {'action': 'wbsearchentities', 'format': 'json', 'type': 'item', 'strictlanguage': False,
              'language': mainlang,       # All languages are searched, but labels are in native language
              'search': item_name}        # Get item list from label
    request = api.Request(site=wikidata_site, parameters=params)
    result = request.submit()

    if 'search' in result:
        for res in result['search']:
            item = pywikibot.ItemPage(repo, res['id'])
            item.get(get_redirect = True)
            if 'P31' in item.claims:
                for seq in item.claims['P31']:       # Loop through instances
                    if seq.getTarget().getID() in instance_id:  # Matching instance
                        for lang in item.labels:                # Search all languages
                            if unidecode.unidecode(item_name.lower()) == unidecode.unidecode(item.labels[lang].lower()):    # Ignore label case and accents
                                item_list.add(item.getID())     # Label math
                        for lang in item.aliases:
                            if item_name in item.aliases[lang]: # Case sensitive for aliases
                                item_list.add(item.getID())     # Alias match
    return item_list


def amend_isbn_edition(isbn_number):
    """
Amend ISBN registration.

Parameters:

    isbn_number:    ISBN number

Result:

    Amend Wikidata, depending on the data obtained from the digital library.
    """
    global proptyx

    isbn_number = isbn_number.strip()
    if isbn_number == '':
        return 3    # Do nothing when the ISBN number is missing
        
    # Validate ISBN data
    if verbose:
        print()
    try:
        isbn_data = meta(isbn_number, service=booklib)
        logger.info(isbn_data)
        # {'ISBN-13': '9789042925564', 'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. Aspecten Uit De Industriele Geschiedenis Van Leuven', 'Authors': ['A. Cresens'], 'Publisher': 'Peeters Pub & Booksellers', 'Year': '2012', 'Language': 'nl'}
    except Exception as error:
        # When the book is unknown the function returns
        logger.error(error)
        #raise ValueError(error)
        return 3

    if len(isbn_data) < 6:
        logger.error('Unknown or incomplete digital library registration for %s' % isbn_number)
        return 3

    # Show the raw results
    if verbose:
        for i in isbn_data:
            print('%s:\t%s' % (i, isbn_data[i]))

    # Get the book language from the ISBN book reference
    booklang = mainlang         # Default language
    if isbn_data['Language'] != '':
        booklang = isbn_data['Language'].strip()
        lang_list = list(get_item_list(booklang, propreqinst['P407']))
        if len(lang_list) == 1:
            target['P407'] = lang_list[0]
        elif len(lang_list) == 0:
            logger.warning('Unknown language %s' % booklang)
            return 3
        else:
            logger.warning('Ambiguous language %s' % booklang)
            return 3

    # Get formatted ISBN number
    isbn_number = isbn_data['ISBN-13']  # Numeric format
    isbn_fmtd = mask(isbn_number)       # Canonical format
    if verbose:
        print()
    print(isbn_fmtd)                    # First one

    # Get (sub)title when there is a dot
    titles = isbn_data['Title'].split('.')          # goob is using a '.'
    for i in ':-':
        if len(titles) == 1:
            titles = isbn_data['Title'].split(i)    # Extract subtitle
    objectname = titles[0].strip()
    subtitle = ''
    if len(titles) > 1:
        subtitle = titles[1].strip()

    # Print book titles
    if debug:
        print(objectname, file=sys.stderr)
        print(subtitle, file=sys.stderr)                # Optional
        for i in range(2,len(titles)):                  # Print subsequent subtitles, when available
            print(titles[i].strip(), file=sys.stderr)   # Not stored in Wikidata...

    # Search the ISBN number in Wikidata both canonical and numeric
    isbn_query = ("""# Get ISBN number
SELECT ?item WHERE {
  VALUES ?isbn_number {
    "%s"
    "%s"
  }
  ?item wdt:P212 ?isbn_number.
}
""" % (isbn_fmtd, isbn_number))      # P212 should have canonical hyphenated format

    logger.info(isbn_query)
    generator = pg.WikidataSPARQLPageGenerator(isbn_query, site=wikidata_site)

    rescnt = 0
    for item in generator:	                # Main loop for all DISTINCT items
        rescnt += 1
        qnumber = item.getID()
        logger.warning('Found item: %s' % qnumber)

    # Create or amend the item
    if rescnt == 1:
        item.get(get_redirect=True)         # Update item
    elif rescnt == 0:
        label = {}
        label[booklang] = objectname
        item = pywikibot.ItemPage(repo)     # Create item
        item.editEntity({'labels': label}, summary=transcmt)
        qnumber = item.getID()
        logger.warning('Creating item: %s' % qnumber)
    else:
        logger.critical('Ambiguous ISBN number %s' % isbn_fmtd)
        return 3

    # Add all P/Q values
    # Make sure that labels are known in the native language
    if debug:
        print(target, file=sys.stderr)

    # Register statements
    for propty in target:
        if propty not in item.claims:
            if propty not in proptyx:
                proptyx[propty] = pywikibot.PropertyPage(repo, propty)
            targetx[propty] = pywikibot.ItemPage(repo, target[propty])

            try:
                logger.warning('Add %s (%s): %s (%s)' % (proptyx[propty].labels[booklang], propty, targetx[propty].labels[booklang], target[propty]))
            except:
                logger.warning('Add %s:%s' % (propty, target[propty]))

            claim = pywikibot.Claim(repo, propty)
            claim.setTarget(targetx[propty])
            item.addClaim(claim, bot=True, summary=transcmt)

    # Set formatted ISBN number
    if 'P212' not in item.claims:
        logger.warning('Add ISBN number (P212): %s' % (isbn_fmtd))
        claim = pywikibot.Claim(repo, 'P212')
        claim.setTarget(isbn_fmtd)
        item.addClaim(claim, bot=True, summary=transcmt)

    # Title
    if 'P1476' not in item.claims:
        logger.warning('Add Title (P1476): %s' % (objectname))
        claim = pywikibot.Claim(repo, 'P1476')
        claim.setTarget(pywikibot.WbMonolingualText(text=objectname, language=booklang))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Subtitle
    if subtitle != '' and 'P1680' not in item.claims:
        logger.warning('Add Subtitle (P1680): %s' % (subtitle))
        claim = pywikibot.Claim(repo, 'P1680')
        claim.setTarget(pywikibot.WbMonolingualText(text=subtitle, language=booklang))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Date of publication
    pub_year = isbn_data['Year']
    if pub_year != '' and 'P577' not in item.claims:
        logger.warning('Add Year of publication (P577): %s' % (isbn_data['Year']))
        claim = pywikibot.Claim(repo, 'P577')
        claim.setTarget(pywikibot.WbTime(year=int(pub_year), precision='year'))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Get the author list
    author_cnt = 0
    for author_name in isbn_data['Authors']:
        author_name = author_name.strip()
        if author_name != '':
            author_cnt += 1
            author_list = list(get_item_list(author_name, 'Q5'))

            if len(author_list) == 1:
                add_author = True
                if 'P50' in item.claims:
                    for seq in item.claims['P50']:
                        if seq.getTarget().getID() == author_list[0]:
                            add_author = False
                            break

                if add_author:
                    logger.warning('Add author %d (P50): %s (%s)' % (author_cnt, author_name, author_list[0]))
                    claim = pywikibot.Claim(repo, 'P50')
                    claim.setTarget(pywikibot.ItemPage(repo, author_list[0]))
                    item.addClaim(claim, bot=True, summary=transcmt)

                    qualifier = pywikibot.Claim(repo, 'P1545')
                    qualifier.setTarget(str(author_cnt))
                    claim.addQualifier(qualifier, summary=transcmt)
            elif len(author_list) == 0:
                logger.warning('Unknown author %s' % author_name)
            else:
                logger.warning('Ambiguous author %s' % author_name)

    # Get the publisher
    publisher_name = isbn_data['Publisher'].strip()
    if publisher_name != '':
        publisher_list = list(get_item_list(publisher_name, 'Q2085381'))

        if len(publisher_list) == 1:
            if 'P123' not in item.claims:
                logger.warning('Add publisher (P123): %s (%s)' % (publisher_name, publisher_list[0]))
                claim = pywikibot.Claim(repo, 'P123')
                claim.setTarget(pywikibot.ItemPage(repo, publisher_list[0]))
                item.addClaim(claim, bot=True, summary=transcmt)
        elif len(publisher_list) == 0:
            logger.warning('Unknown publisher %s' % publisher_name)
        else:
            logger.warning('Ambiguous publisher %s' % publisher_name)

    # Get addional data from the digital library
    isbn_cover = cover(isbn_number)
    isbn_editions = editions(isbn_number, service='merge')
    isbn_doi = doi(isbn_number)
    isbn_info = info(isbn_number)

    if verbose:
        print()
        print(isbn_info)
        print(isbn_doi)
        print(isbn_editions)

    # Book cover images
    for i in isbn_cover:
        print('%s:\t%s' % (i, isbn_cover[i]))

    # Handle ISBN classification
    isbn_classify = classify(isbn_number)
    if debug:
        print(isbn_classify, file=sys.stderr)

    # ./create_isbn_edition.py '978-3-8376-5645-9' - de P407 Q188
    # Q113460204
    # {'owi': '11103651812', 'oclc': '1260160983', 'lcc': 'TK5105.8882', 'ddc': '300', 'fast': {'1175035': 'Wikis (Computer science)', '1795979': 'Wikipedia', '1122877': 'Social sciences'}}

    # OCLC work ID
    if 'owi' in isbn_classify and 'P5331' not in item.claims:
        logger.warning('Add OCLC work ID (P5331): %s' % (isbn_classify['owi']))
        claim = pywikibot.Claim(repo, 'P5331')
        claim.setTarget(isbn_classify['owi'])
        item.addClaim(claim, bot=True, summary=transcmt)

    # Set the OCLC id
    if 'oclc' in isbn_classify and 'P243' not in item.claims:
        logger.warning('Add OCLC ID (P243): %s' % (isbn_classify['oclc']))
        claim = pywikibot.Claim(repo, 'P243')
        claim.setTarget(isbn_classify['oclc'])
        item.addClaim(claim, bot=True, summary=transcmt)

    # Library of Congress Classification (works and editions)
    if 'lcc' in isbn_classify and 'P8360' not in item.claims:
        logger.warning('Add Library of Congress Classification for edition (P8360): %s' % (isbn_classify['lcc']))
        claim = pywikibot.Claim(repo, 'P8360')
        claim.setTarget(isbn_classify['lcc'])
        item.addClaim(claim, bot=True, summary=transcmt)

    # Dewey Decimale Classificatie
    if 'ddc' in isbn_classify and 'P1036' not in item.claims:
        logger.warning('Add Dewey Decimale Classificatie (P1036): %s' % (isbn_classify['ddc']))
        claim = pywikibot.Claim(repo, 'P1036')
        claim.setTarget(isbn_classify['ddc'])
        item.addClaim(claim, bot=True, summary=transcmt)

    # Register Fast ID using P921 (main subject) through P2163 (Fast ID)
    # https://www.wikidata.org/wiki/Q3294867
    # https://nl.wikipedia.org/wiki/Faceted_Application_of_Subject_Terminology
    # https://www.oclc.org/research/areas/data-science/fast.html
    # https://www.oclc.org/content/dam/oclc/fast/FAST-quick-start-guide-2022.pdf

    if 'fast' in isbn_classify:
        for fast_id in isbn_classify['fast']:

            # Get the main subject
            main_subject_query = ("""# Search the main subject
SELECT ?item WHERE {
  ?item wdt:P2163 "%s".
}
""" % (fast_id))

            logger.info(main_subject_query)
            generator = pg.WikidataSPARQLPageGenerator(main_subject_query, site=wikidata_site)

            rescnt = 0
            for main_subject in generator:	            # Main loop for all DISTINCT items
                rescnt += 1
                qmain_subject = main_subject.getID()
                try:
                    main_subject_label = main_subject.labels[booklang]
                    logger.info('Found main subject %s (%s) for Fast ID %s' % (main_subject_label, qmain_subject, fast_id))
                except:
                    main_subject_label = ''
                    logger.info('Found main subject (%s) for Fast ID %s' % (qmain_subject, fast_id))
                    logger.error('Missing label for item %s' % qmain_subject)

            # Create or amend P921 statement
            if rescnt == 0:
                logger.error('Main subject not found for Fast ID %s' % (fast_id))
            elif rescnt == 1:
                add_main_subject = True
                if 'P921' in item.claims:               # Check for duplicates
                    for seq in item.claims['P921']:
                        if seq.getTarget().getID() == qmain_subject:
                            add_main_subject = False
                            break

                if add_main_subject:
                    logger.warning('Add main subject (P921) %s (%s)' % (main_subject_label, qmain_subject))
                    claim = pywikibot.Claim(repo, 'P921')
                    claim.setTarget(main_subject)
                    item.addClaim(claim, bot=True, summary=transcmt)
                else:
                    logger.info('Skipping main subject %s (%s)' % (main_subject_label, qmain_subject))
            else:
                logger.error('Ambiguous main subject for Fast ID %s' % (fast_id))

    # Book description
    isbn_description = desc(isbn_number)
    print()
    print(isbn_description)

    # Currently does not work (service not available)
    try:
        bibtex_metadata = doi2tex(isbn_doi)
        print(bibtex_metadata)
    except Exception as error:
        logger.error(error)     # Data not available

    return 0


# Error logging
logger = logging.getLogger('create_isbn_edition')
#logging.basicConfig(level=logging.DEBUG)       # Uncomment for debugging
##logger.setLevel(logging.DEBUG)

pgmnm = sys.argv.pop(0)
logger.debug('%s %s' % (pgmnm, '2022-08-16 (gvp)'))

# Get optional parameters

# Get the digital library
if len(sys.argv) > 0:
    booklib = sys.argv.pop(0)
    if booklib == '-':
        booklib = 'goob'

# Get the native language
# The language code is only required when P/Q parameters are added, or different from the LANG code
if len(sys.argv) > 0:
    mainlang = sys.argv.pop(0)

# Get additional P/Q parameters
while len(sys.argv) > 0:
    inpar = propre.findall(sys.argv.pop(0).upper())[0]
    target[inpar] = qsuffre.findall(sys.argv.pop(0).upper())[0]

# Validate P/Q list
proptyx={}
targetx={}

# Validate the propery/instance pair
for propty in target:
    if propty not in proptyx:
        proptyx[propty] = pywikibot.PropertyPage(repo, propty)
    targetx[propty] = pywikibot.ItemPage(repo, target[propty])
    targetx[propty].get(get_redirect=True)
    if propty in propreqinst and ('P31' not in targetx[propty].claims or not is_in_list(targetx[propty].claims['P31'], propreqinst[propty])):
        logger.critical('%s (%s) is not a language' % (targetx[propty].labels[mainlang], target[propty]))
        sys.exit(12)

# Get list of item numbers
inputfile = sys.stdin.read()            # Typically the Appendix list of references of e.g. a Wikipedia page containing ISBN numbers
itemlist = sorted(set(isbnre.findall(inputfile)))   # Extract all ISBN numbers

for isbn_number in itemlist:            # Process the next edition
    amend_isbn_edition(isbn_number)
