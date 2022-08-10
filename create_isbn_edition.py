#!/home/geertivp/pwb/bin/python3

codedoc = """
Pywikibot script to get ISBN data and create or amend the Wikidata item for edition (P212)

Use digital libraries to get ISBN data in JSON format, and integrate it into Wikidata.

Parameters:

    Optional:

        P1:         library (goob openl wiki) - default goob "-"
        P2:         language code (default LANG)
        P3 P4...:   P/Q pairs for additional claims (repeated)

    stdin: ISBN numbers (International standard book number); one per line

Examples:

    ./create_isbn_edition.py                        # Default library and language
    9789042925564

    ./create_isbn_edition.py wiki nl P407 Q7411     # Language Dutch
    9789042925564

Return status:

    The following status codes are returned to the shell:

        3   Invalid or missing parameter
        12  Item does not exist

Standard ISBN properties:

    P31:Q3331189:   instance of edition
    P407:   language of work
    P577:   date of publication (year)
    P1476:  book title
    P1680:  subtitle

Other ISBN properties:

    P50:    author (case sensitive)
    P123:   publisher (case sensitive)
    P291:   place of publication
    P921:   main subject (inverse lookup from P2163: Fast ID)
    P1104:  number of pages

Qualifiers:

    P1545:  Sequence number

External identifiers:

    P212:   canonical ISBN number (lookup via Wikidata Query)
    P213:   ISNI ID
    P243:   OCLC ID
    P675:   Google Books-identificatiecode
    P1036:  Dewey Decimal Classification
    P2163:  Fast ID (inverse lookup via Wikidata Query) -> P921: main subject
    P5331:  OCLC work ID

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

Prerequisites:

    pywikibot
    pip install isbnlib

Restrictions:

    * Better use the language code parameter (the language code is not always available from the digital library)

Known problems:

    * Not all ISBN attributes are listed by the webservice(s)
    * Multiple webservice calls (script might take time, but it is automated)
    * Amend ISBN items that have no author, publisher, or other data (which service to use?)

Algorithm:

    Get parameters
    Validate parameters
    Get ISBN data
    Convert ISBN data
    Get additional data
    Register ISBN data into Wikidata

Environment:

    The python script can run on:
    
        Linux client
        Google Chromebook (Linux container)
        Toolforge Portal
        PAWS

Author: Geert Van Pamel, 2022-08-04, GNU General Public License v3.0, User:Geertivp

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
booklib = 'goob'
propre = re.compile(r'P[0-9]+')             # P-number
qsuffre = re.compile(r'Q[0-9]+')            # Q-number

# Other statements are added via command line parameters
target = {'P31':'Q3331189',                 # Is an instance of edition
}

# Statement and instance validation rules
propreqinst = {'P407':{'Q34770', 'Q33742', 'Q1288568'},      # (living, natural) language
}

mainlang = os.getenv('LANG', 'nl')[:2]      # Default description language

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
Get list of items by name

Parameters:

    item_name:      Item name (string; case sensitive)
    instance_id:    Instance ID (string, set, or list)

Returns:

    Set of items        
    """

    item_list = set()
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
                for seq in item.claims['P31']:       # Instance
                    if seq.getTarget().getID() in instance_id:
                        for lang in item.labels:
                            if unidecode.unidecode(item_name.lower()) == unidecode.unidecode(item.labels[lang].lower()):
                                item_list.add(item.getID())
                        for lang in item.aliases:
                            if item_name in item.aliases[lang]: # Case sensitive
                                item_list.add(item.getID())
    return item_list


def amend_isbn_edition(isbn_number):
    """
Amend ISBN registration.

Parameters:

    isbn_number:    ISBN number
    """

    # Validate ISBN data
    try:
        isbn_data = meta(isbn_number, service=booklib)
        #print(isbn_data)
        # {'ISBN-13': '9789042925564', 'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. Aspecten Uit De Industriele Geschiedenis Van Leuven', 'Authors': ['A. Cresens'], 'Publisher': 'Peeters Pub & Booksellers', 'Year': '2012', 'Language': 'nl'}
    except Exception as error:
        # When the book is unknown the program stops
        logger.error(error)
        #raise ValueError(error)
        return 3

    if len(isbn_data) < 6:
        if len(isbn_data) > 0:
            logger.error('Incomplete digital library registration for %s' % isbn_number)
        return 3

    # Show the raw results
    for i in isbn_data:
        print('%s:\t%s' % (i, isbn_data[i]))

    # Get the language from the ISBN book reference
    if isbn_data['Language'] != '':
        mainlang = isbn_data['Language']

    lang_list = list(get_item_list(mainlang, propreqinst['P407']))
    if len(lang_list) == 1:
        target['P407'] = lang_list[0]
    elif len(lang_list) == 0:
        logger.warning('Unknown language %s' % mainlang)
        return 3
    else:
        logger.warning('Ambiguous language %s' % mainlang)
        return 3

    # Get formatted ISBN number
    isbn_number = isbn_data['ISBN-13']  # Numeric format
    isbn_fmtd = mask(isbn_number)       # Canonical format
    print()
    print(isbn_fmtd)                    # First one

    # Get (sub)title when there is a dot
    titles = isbn_data['Title'].split('.')
    objectname = titles[0].strip()
    subtitle = ''
    if len(titles) > 1:
        subtitle = titles[1].strip()

    # Print book titles
    print(objectname)
    print(subtitle)                     # Optional
    for i in range(2,len(titles)):      # Print subsequent subtitles, when available
        print(titles[i].strip())

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
        label[mainlang] = objectname
        item = pywikibot.ItemPage(repo)     # Create item
        item.editEntity({'labels': label}, summary=transcmt)
        qnumber = item.getID()
        logger.warning('Creating item: %s' % qnumber)
    else:
        logger.critical('Ambiguous ISBN number %s' % isbn_fmtd)
        return 3

    # Add all P/Q values
    # Make sure that labels are known in the native language
    print(target)
    for propty in target:
        if propty not in item.claims:
            try:
                logger.warning('Add %s (%s): %s (%s)' % (proptyx[propty].labels[mainlang], propty, targetx[propty].labels[mainlang], target[propty]))
            except:
                pass

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
        claim.setTarget(pywikibot.WbMonolingualText(text=objectname, language=mainlang))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Subtitle
    if subtitle != '' and 'P1680' not in item.claims:
        logger.warning('Add Subtitle (P1680): %s' % (subtitle))
        claim = pywikibot.Claim(repo, 'P1680')
        claim.setTarget(pywikibot.WbMonolingualText(text=subtitle, language=mainlang))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Date of publication
    if 'P577' not in item.claims:
        logger.warning('Add Year of publication (P577): %s' % (isbn_data['Year']))
        claim = pywikibot.Claim(repo, 'P577')
        claim.setTarget(pywikibot.WbTime(year=int(isbn_data['Year']), precision='year'))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Get the author list
    author_cnt = 0
    for author_name in isbn_data['Authors']:
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
    publisher_name = isbn_data['Publisher']
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
    isbn_editions = editions(isbn_number)
    isbn_doi = doi(isbn_number)
    isbn_info = info(isbn_number)

    print()
    print(isbn_info)
    print(isbn_doi)
    print(isbn_editions)

    # Book cover images
    for i in isbn_cover:
        print('%s:\t%s' % (i, isbn_cover[i]))

    # Handle ISBN classification

    isbn_classify = classify(isbn_number)
    print(isbn_classify)

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

            generator = pg.WikidataSPARQLPageGenerator(main_subject_query, site=wikidata_site)

            rescnt = 0
            for main_subject in generator:	            # Main loop for all DISTINCT items
                rescnt += 1
                qmain_subject = main_subject.getID()
                try:
                    main_subject_label = main_subject.labels[mainlang]
                    logger.warning('Found main subject %s (%s) for Fast ID %s' % (main_subject_label, qmain_subject, fast_id))
                except:
                    logger.warning('Found main subject (%s) for Fast ID %s' % (qmain_subject, fast_id))
                    logger.error('Missing label for item %s' % qmain_subject)

            # Create or amend P921 statement
            if rescnt == 0:
                logger.error('Main subject not found for Fast ID %s' % (fast_id))
            elif rescnt == 1:
                add_main_subject = True
                if 'P921' in item.claims:
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
#logging.basicConfig(level=logging.DEBUG)
##logger.setLevel(logging.DEBUG)

pgmnm = sys.argv.pop(0)
logger.debug('%s %s' % (pgmnm, '2022-08-09 (gvp)'))

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
inputfile = sys.stdin.read()
itemlist = sorted(set(inputfile.split('\n')))

for isbn_number in itemlist:
    amend_isbn_edition(isbn_number)
