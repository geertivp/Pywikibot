#!/usr/bin/python3

"""Pywikibot client to load ISBN linked data into Wikidata.

Pywikibot script to get ISBN data from a digital library,
and create or amend the related Wikidata item for edition
(with the P212, ISBN number, as unique external ID).

Use digital libraries to get ISBN data in JSON format,
and integrate the results into Wikidata.

Then the resulting item number can be used
e.g. to generate Wikipedia references using template Cite_Q.

Parameters:

    All parameters are optional.

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
                e.g. P921 Q107643461
                (main subject: database management linked to P2163 Fast ID)

    stdin: ISBN numbers (International standard book number; version 10 or 13)

        Free text (e.g. Wikipedia references list,
        or publication list) is accepted.
        Identification is done via an ISBN regex expression.

Functionality:

    * Both ISBN-10 and ISBN-13 numbers are accepted.
    * Only ISBN-13 numbers are stored.
        ISBN-10 numbers are only used for identification purposes.
    * The ISBN number is used as a primary key
        (no 2 items can have the same P212 ISBN number).
        The item update is not performed when there is no unique match.
        Only editions are updated or created.
    * Individual statements are added or merged incrementally;
        existing data is not overwritten.
    * Authors and publishers are searched to get their item number
        (unknown of ambiguous items are skipped).
    * Book title and subtitle are separated with either
        '.', ':', or '-' (in that order)
    * This script can be run incrementally with the same parameters.
        Caveat: Wikidata queries run on a replicated database.
        Take into account the Wikidata Query database replication delay.
        Wait for minimum 5 minutes to avoid creating duplicate objects.

Examples:

    # Default library (Google Books), language (LANG), no additional statements
    ./create_isbn_edition.py <<EOF
    9789042925564
    EOF

    # Wikimedia, language English, main subject: database management
    ./create_isbn_edition.py wiki en P921 Q107643461 <<EOF
    978-0-596-10089-6
    EOF

Data quality:

    * A written work should not have an ISBN number (P212).
    * ISBN numbers (P212) are only assigned to editions.
    * For P629 (edition of) amend "is an Q47461344 (written work) instance"
            and "inverse P747 (work has edition)" statements
    * Use https://query.wikidata.org/querybuilder/ to identify P212 duplicates
        Merge duplicate items before running the script again.
    * The following properties should only be used for written works
        P5331:  OCLC work ID (editions should only have P243)
        P8383:  Goodreads-identificatiecode for work
            (editions should only have P2969).

Return status:

    The following status codes are returned to the shell:

        3   Invalid or missing parameter
        12  Item does not exist

Standard ISBN properties for editions:

    P31:Q3331189:   instance of edition
    P50:    author
    P123:   publisher
    P212:   canonical ISBN number (searchable via Wikidata Query)
    P407:   language of work (Qnumber linked to ISO 639-1 language code)
    P577:   date of publication (year)
    P1476:  book title
    P1680:  subtitle

Other ISBN properties:

    P921:   main subject (inverse lookup from external Fast ID P2163)
    P629:   work for edition
    P747:   edition of work

Qualifiers:

    P248:   Source
    P813:   Retrieval data
    P1545:  (author) sequence number

External identifiers:

    P213:   ISNI ID
    P243:   OCLC ID
    P496:   ORCID iD
    P675:   Google Books-identificatiecode
    P1036:  Dewey Decimal Classification
    P2163:  Fast ID (inverse lookup via Wikidata Query) -> P921: main subject
    P2969:  Goodreads-identificatiecode

    (only for written works)
    P5331:  OCLC work ID (editions should only have P243)
    P8383:  Goodreads-identificatiecode for work (editions should only have P2969)

Unavailable properties:

    P291:   place of publication
    P1104:  number of pages

Author:

    Geert Van Pamel, 2022-08-04, MIT License, User:Geertivp

Documentation:

    https://en.wikipedia.org/wiki/ISBN
    https://pypi.org/project/isbnlib/
    https://buildmedia.readthedocs.org/media/pdf/isbnlib/v3.4.5/isbnlib.pdf
    https://www.wikidata.org/wiki/Property:P212
    http://www.isbn.org/standards/home/isbn/international/hyphenation-instructions.asp
    https://isbntools.readthedocs.io/en/latest/info.html
    https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

    https://www.wikidata.org/wiki/Wikidata:WikiProject_Books
    https://www.wikidata.org/wiki/Q21831105 (WikiProject Books)
    https://www.wikidata.org/wiki/Wikidata:List_of_properties/work
    https://www.wikidata.org/wiki/Template:Book_properties
    https://www.wikidata.org/wiki/Template:Bibliographic_properties
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData
    https://www.wikidata.org/wiki/Help:Sources
    https://www.wikidata.org/wiki/Q22696135 (Wikidata references module)

    https://www.geeksforgeeks.org/searching-books-with-python/
    http://classify.oclc.org/classify2/ClassifyDemo

    https://doc.wikimedia.org/pywikibot/master/
    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html
    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_statements
    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_qualifiers
    https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_sources

    https://docs.python.org/3/howto/logging.html
    https://www.freecodecamp.org/news/python-json-how-to-convert-a-string-to-json/
    https://wikitech.wikimedia.org/wiki/Portal:Toolforge

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
        Possible important replication delay; wait 5 minutes before retry
            -- otherwise risk for creating duplicates.
    * Publisher unknown:
        * Missing P31:Q2085381 statement
        * Missing alias (or case sensitive)
    * Unknown author: First create author as a person

Known problems:

    * Unknown ISBN, e.g. 9789400012820
    * No ISBN data available for an edition either causes no output
        (goob = Google Books), or an error message (wiki, openl).
        The script is taking care of both.
    * Only 6 ISBN attributes are listed by the webservice(s)
        missing are e.g.: place of publication, number of pages
    * Not all ISBN atttributes have all required data
        (authors, publisher, date of publication, language can be missing at the digital library).
    * The script uses multiple webservice calls (script might take time, but it is automated)
    * Need to amend ISBN items that have no author, publisher, or other required data
        * You could use another digital library?
        * Which other services to use?
    * How to add still more digital libraries?
        * Does the KBR has a public ISBN service (Koninklijke Bibliotheek van België)?
    * Filter for work properties:
        https://www.wikidata.org/wiki/Q63413107
        ['9781282557246', '9786612557248', '9781847196057', '9781847196040']
        P5331: OCLC identification code for work 793965595 (should only have P243)
        P8383: Goodreads identification code for work 13957943 (should only have P2969)

To do:

    * Webservice on toolforge.org

Algorithm:

    Get parameters
    Validate parameters
    Get ISBN data
    Convert ISBN data
        Reverse names when Lastname, Firstname
    Get additional data
    Register ISBN data into Wikidata
        Add source reference when creating the item
            (digital library instance, retrieval date)
        create or amend items or claims
            Number the authors in order of appearence
            Check data consistency

Environment:

    The python script can run on the following platforms:

        Linux client
        Google Chromebook (Linux container)
        Toolforge Portal
        PAWS

    LANG: default ISO 639-1 language code

Source code:

    https://github.com/geertivp/Pywikibot/blob/main/create_isbn_edition.py
    https://gerrit.wikimedia.org/r/c/pywikibot/core/+/826631
    https://phabricator.wikimedia.org/T314942

Applications:

    Generate a book reference
        Example: {{Cite Q|Q63413107}} (wp.en)

    See also:
        https://meta.wikimedia.org/wiki/WikiCite
        https://www.wikidata.org/wiki/Q21831105 (WikiCite)
        https://www.wikidata.org/wiki/Q22321052 (Cite_Q)
        https://www.mediawiki.org/wiki/Global_templates
        https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData
        https://phabricator.wikimedia.org/tag/wikicite/
        https://meta.wikimedia.org/wiki/WikiCite
        https://meta.wikimedia.org/wiki/WikiCite/Shared_Citations
        https://www.wikidata.org/wiki/Q36524 (Authority control)
        https://meta.wikimedia.org/wiki/Community_Wishlist_Survey_2021/Wikidata/Bibliographical_references/sources_for_wikidataitems

Wikidata Query:

    List of editions about musicians:           https://w.wiki/5aaz
    List of editions having an ISBN number:     https://w.wiki/5akq

Related projects:

    https://phabricator.wikimedia.org/T282719
    https://phabricator.wikimedia.org/T214802
    https://phabricator.wikimedia.org/T208134
    https://phabricator.wikimedia.org/T138911
    https://phabricator.wikimedia.org/T20814
    https://en.wikipedia.org/wiki/User:Citation_bot
    https://zenodo.org/record/55004#.YvwO4hTP1D8

Other systems:

    https://en.wikipedia.org/wiki/bibliographic_database
    https://www.titelbank.nl/pls/ttb/f?p=103:4012:::NO::P4012_TTEL_ID:3496019&cs=19BB8084860E3314502A1F777F875FE61

"""

import isbnlib          # ISBN library
import logging          # Error logging
import os               # Operating system
import re               # Regular expressions (very handy!)
import sys              # System calls
import unidecode        # Unicode

from datetime import date, datetime	    # now, strftime, delta time, total_seconds

import pywikibot        # API interface to Wikidata
from pywikibot import pagegenerators as pg  # Wikidata Query interface
from pywikibot.data import api

# Initialisation
debug = True            # Show debugging information
verbose = True          # Verbose mode

booklib = 'goob'        # Default digital library
ISBNRE = re.compile(r'[0-9-]{10,17}')       # ISBN number: 10 or 13 digits with optional dashes (-)
NAMEREVRE = re.compile(r',(\s*.*)*$')	    # Reverse lastname, firstname
PROPRE = re.compile(r'P[0-9]+')             # Wikidata P-number
QSUFFRE = re.compile(r'Q[0-9]+')            # Wikidata Q-number
SUFFRE = re.compile(r'\s*[(].*[)]$')		# Remove trailing () suffix (keep only the base label)

# Source of digital library
bib_source = {
    'bnf': 'Q193563',
    'bol': 'Q609913',
    'dnb': 'Q27302',
    'goob': 'Q206033',
    'kb': 'Q1526131',
    #'kbr': 'Q383931',
    'loc': 'Q131454',
    'mcues': 'Q750403',
    'openl': 'Q1201876',
    'porbase': 'Q51882885',
    'sbn': 'Q576951',
    'wiki': 'Q64692275',
    'worldcat': 'Q76630151',
}

# Remap obsolete language codes
langcode = {
    'fre': 'fr',
    'iw': 'he',
}

# Other statements are added via command line parameters
target = {
    'P31': 'Q3331189',                      # Is an instance of an edition
}

# Statement property and instance validation rules
propreqinst = {
    'P50': {'Q5'},                                  # Author requires human
    'P123': {'Q2085381', 'Q1114515', 'Q1320047', 'Q479716'},   # Publisher requires publisher
    'P407': {'Q34770', 'Q33742', 'Q1288568'},       # Edition language requires at least one of (living, natural) language
}

# Default description language
mainlang = os.getenv('LANG', 'en').split('_')[0]

# Wikidata transaction comment
transcmt = '#pwb Create ISBN edition'


def is_in_item_list(statement_list, itemlist) -> bool:
    """Verify if statement list contains at least one item from the itemlist.

    :param statement_list: Statement list of items
    :param itemlist: List of items (string)
    :return: True when match, False otherwise
    """
    for seq in statement_list:
        if seq.getTarget().getID() in itemlist:
            isinlist = True
            break
    else:
        isinlist = False
    return isinlist


def is_in_value_list(statement_list, valuelist) -> bool:
    """Verify if statement list contains at least one value from the valuelist.

    :param statement_list: Statement list of values
    :param valuelist: List of values (string)
    :return: True when match, False otherwise
    """
    for seq in statement_list:
        if seq.getTarget() in valuelist:
            isinlist = True
            break
    else:
        isinlist = False
    return isinlist


def get_canon_name(baselabel) -> str:
    """Get standardised name

    :param baselabel: input label
    :return cononical label
    
    Algorithm:
        remove () suffix
        reverse , name parts
    """
    suffix = SUFFRE.search(baselabel)  	        # Remove () suffix, if any
    if suffix:
        baselabel = baselabel[:suffix.start()]  # Get canonical form

    colonloc = baselabel.find(':')
    commaloc = NAMEREVRE.search(baselabel)
    
    # Reorder "lastname, firstname" and concatenate with space
    if colonloc < 0 and commaloc:
        baselabel = baselabel[commaloc.start() + 1:] + ' ' + baselabel[:commaloc.start()]
        baselabel = baselabel.replace(',',' ')  # Remove remaining ,

    # Remove redundant spaces
    baselabel = ' '.join(baselabel.split())
    return baselabel


def get_item_list(item_name: str, instance_id) -> list:
    """Get list of items by name, belonging to an instance (list)

    :param item_name: Item name (string; case sensitive)
    :param instance_id: Instance ID (string, set, or list)
    :return: List of items (Q-numbers)
    """
    item_list = set()       # Empty set
    params = {'action': 'wbsearchentities',
              'format': 'json',
              'type': 'item',
              'strictlanguage': False,
              'language': mainlang,       # All languages are searched, but labels are in native language
              'search': item_name}        # Get item list from label
    request = api.Request(site=repo, parameters=params)
    result = request.submit()

    if 'search' in result:
        for res in result['search']:
            item = pywikibot.ItemPage(repo, res['id'])
            item.get(get_redirect=True)
            if 'P31' in item.claims:
                for seq in item.claims['P31']:       # Loop through instances
                    if seq.getTarget().getID() in instance_id:  # Matching instance
                        for lang in item.labels:                # Search all languages
                            if unidecode.unidecode(item_name.lower()) == unidecode.unidecode(item.labels[lang].lower()):    # Ignore label case and accents
                                item_list.add(item.getID())     # Label match
                        for lang in item.aliases:
                            if item_name in item.aliases[lang]: # Case sensitive for aliases
                                item_list.add(item.getID())     # Alias match
    # Convert set to list
    return list(item_list)


def amend_isbn_edition(isbn_number) -> int:
    """Amend the ISBN registration in Wikidata.
    
    It is registering the ISBN-13 data via P212,
    depending on the data obtained from the chosen digital library.

    :param isbn_number: ISBN number
        (string; 10 or 13 digits with optional hyphens)
    :result: Status (int)
    """
    global proptyx
    # targetx is not global (language specific editions)

    isbn_number = isbn_number.strip()
    if not isbn_number:
        return 3    # Do nothing when the ISBN number is missing

    # Validate ISBN data
    if verbose:
        print()

    try:
        isbn_data = isbnlib.meta(isbn_number, service=booklib)
        logger.info(isbn_data)
        # {'ISBN-13': '9789042925564', 'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. Aspecten Uit De Industriele Geschiedenis Van Leuven', 'Authors': ['A. Cresens'], 'Publisher': 'Peeters Pub & Booksellers', 'Year': '2012', 'Language': 'nl'}
    except Exception as error:
        # When the book is unknown the function returns
        logger.error(error)
        #raise ValueError(error)
        return 3

    #print(isbn_data)
    if len(isbn_data) < 6:
        logger.error('Unknown or incomplete digital library registration for %s' % isbn_number)
        return 3

    # Show the raw results
    if verbose:
        for i in isbn_data:
            print('%s:\t%s' % (i, isbn_data[i]))

    # Get the book language from the ISBN book reference
    booklang = mainlang         # Default language
    if isbn_data['Language']:
        booklang = isbn_data['Language'].strip()

        # Replace obsolete codes
        if booklang in langcode:
            booklang = langcode[booklang]

        # Get Wikidata language code
        lang_list = get_item_list(booklang, propreqinst['P407'])
        if len(lang_list) == 1:
            target['P407'] = lang_list[0]
        elif lang_list:
            logger.warning('Ambiguous language %s' % booklang)
            return 3
        else:
            logger.warning('Unknown language %s' % booklang)
            return 3

        # Get short language code
        if len(booklang) > 3:
            lang = pywikibot.ItemPage(repo, lang_list[0])
            lang.get(get_redirect=True)
            if 'P424' in lang.claims:
                booklang = lang.claims['P424'][0].getTarget()

    # Get formatted ISBN number
    isbn_number = isbn_data['ISBN-13']  # Numeric format
    isbn_fmtd = isbnlib.mask(isbn_number)       # Canonical format
    if verbose:
        print()
    print(isbn_fmtd)                    # First one

    # Get (sub)title when there is a dot
    titles = isbn_data['Title'].split('. ')          # goob is using a '.'
    if len(titles) == 1:
        titles = isbn_data['Title'].split(': ')      # Extract subtitle
    if len(titles) == 1:
        titles = isbn_data['Title'].split(' - ')     # Extract subtitle
    objectname = titles[0].strip()
    subtitle = ''
    if len(titles) > 1:
        subtitle = titles[1].strip()

    # Print book titles
    if debug:
        print(objectname, file=sys.stderr)
        print(subtitle, file=sys.stderr)                     # Optional
        for i in range(2,len(titles)):      # Print subsequent subtitles, when available
            print(titles[i].strip(), file=sys.stderr)        # Not stored in Wikidata...

    # Search the ISBN number in Wikidata both canonical and numeric
    isbn_query = ("""# Get ISBN number
SELECT ?item WHERE {
  VALUES ?isbn_number {
    "%s"
    "%s"
  }
  ?item wdt:P212 ?isbn_number.
}
""" % (isbn_fmtd, isbn_number))             # P212 should have canonical hyphenated format

    # Search the item having the ISBN number
    logger.info(isbn_query)
    generator = pg.WikidataSPARQLPageGenerator(isbn_query, site=repo)

    rescnt = 0
    for item in generator:	                # Main loop for all DISTINCT items
        rescnt += 1
        qnumber = item.getID()
        logger.warning('Found item: %s' % qnumber)

    # Create or amend the item
    if rescnt == 0:
        label = {}
        label[booklang] = objectname
        item = pywikibot.ItemPage(repo)     # Create item
        item.editEntity({'labels': label}, summary=transcmt)
        qnumber = item.getID()
        logger.warning('Creating item: %s' % qnumber)

        # Register source and retrieval date
        if booklib in bib_source:
            claim = pywikibot.Claim(repo, 'P31')
            claim.setTarget(targetx['P31'])
            item.addClaim(claim, bot=True, summary=transcmt)

            # Set source reference
            ref = pywikibot.Claim(repo, 'P248')
            ref.setTarget(bib_source[booklib])

            # Set retrieval date
            retrieved = pywikibot.Claim(repo, 'P813')
            retrieved.setTarget(date_ref)

            claim.addSources([ref, retrieved], summary=transcmt)
    elif rescnt == 1:
        item.get(get_redirect=True)         # Update item
        if 'P31' in item.claims and not is_in_item_list(item.claims['P31'], target['P31']):
            logger.error('Item %s is not an edition' % qnumber)
            return 3
    else:
        logger.error('Ambiguous ISBN number %s' % isbn_fmtd)
        return 3

    # Add all P/Q values
    # Make sure that labels are known in the native language
    logger.debug(target)

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
    #elif: update formatted ISBN

    # Title
    if 'P1476' not in item.claims:
        logger.warning('Add Title (P1476): %s' % (objectname))
        claim = pywikibot.Claim(repo, 'P1476')
        claim.setTarget(pywikibot.WbMonolingualText(text=objectname, language=booklang))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Subtitle
    if subtitle and 'P1680' not in item.claims:
        logger.warning('Add Subtitle (P1680): %s' % (subtitle))
        claim = pywikibot.Claim(repo, 'P1680')
        claim.setTarget(pywikibot.WbMonolingualText(text=subtitle, language=booklang))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Date of publication
    pub_year = isbn_data['Year']
    if pub_year and 'P577' not in item.claims:
        logger.warning('Add Year of publication (P577): %s' % (isbn_data['Year']))
        claim = pywikibot.Claim(repo, 'P577')
        claim.setTarget(pywikibot.WbTime(year=int(pub_year), precision='year'))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Get the author list
    author_cnt = 0
    for author_name in isbn_data['Authors']:
        author_name = author_name.strip()
        if author_name:
            author_cnt += 1

            # Reorder "lastname, firstname" and concatenate with space
            author_name = get_canon_name(author_name)
            author_list = get_item_list(author_name, propreqinst['P50'])

            if len(author_list) == 1:
                if 'P50' not in item.claims or not is_in_item_list(item.claims['P50'], author_list):
                    logger.warning('Add author %d (P50): %s (%s)' % (author_cnt, author_name, author_list[0]))
                    claim = pywikibot.Claim(repo, 'P50')
                    claim.setTarget(pywikibot.ItemPage(repo, author_list[0]))
                    item.addClaim(claim, bot=True, summary=transcmt)

                    qualifier = pywikibot.Claim(repo, 'P1545')      # Sequence number
                    qualifier.setTarget(str(author_cnt))
                    claim.addQualifier(qualifier, summary=transcmt)
            elif author_list:
                logger.warning('Ambiguous author: %s' % author_name)
            else:
                logger.warning('Unknown author: %s' % author_name)

    # Get the publisher
    publisher_name = isbn_data['Publisher'].strip()
    if publisher_name:
        publisher_list = get_item_list(publisher_name, propreqinst['P123'])

        if len(publisher_list) == 1:
            if 'P123' not in item.claims:
                logger.warning('Add publisher (P123): %s (%s)' % (publisher_name, publisher_list[0]))
                claim = pywikibot.Claim(repo, 'P123')
                claim.setTarget(pywikibot.ItemPage(repo, publisher_list[0]))
                item.addClaim(claim, bot=True, summary=transcmt)
        elif publisher_list:
            logger.warning('Ambiguous publisher: %s' % publisher_name)
        else:
            logger.warning('Unknown publisher: %s' % publisher_name)

    # Get addional data from the digital library
    isbn_cover = isbnlib.cover(isbn_number)
    isbn_editions = isbnlib.editions(isbn_number, service='merge')
    isbn_doi = isbnlib.doi(isbn_number)
    isbn_info = isbnlib.info(isbn_number)

    if verbose:
        print()
        print(isbn_info)
        print(isbn_doi)
        print(isbn_editions)

    # Book cover images
    for i in isbn_cover:
        print('%s:\t%s' % (i, isbn_cover[i]))

    # Handle ISBN classification
    isbn_classify = isbnlib.classify(isbn_number)
    if debug:
        for i in isbn_classify:
            print('%s:\t%s' % (i, isbn_classify[i]), file=sys.stderr)

    # ./create_isbn_edition.py '978-3-8376-5645-9' - de P407 Q188
    # Q113460204
    # {'owi': '11103651812', 'oclc': '1260160983', 'lcc': 'TK5105.8882', 'ddc': '300', 'fast': {'1175035': 'Wikis (Computer science)', '1795979': 'Wikipedia', '1122877': 'Social sciences'}}

    # Set the OCLC ID
    if 'oclc' in isbn_classify and 'P243' not in item.claims:
        logger.warning('Add OCLC ID (P243): %s' % (isbn_classify['oclc']))
        claim = pywikibot.Claim(repo, 'P243')
        claim.setTarget(isbn_classify['oclc'])
        item.addClaim(claim, bot=True, summary=transcmt)

    # Amend Written work relationship
    if 'P629' in item.claims:
        # Enhance data quality for Written work
        for seq in item.claims['P629']:
            if 'P31' not in seq.getTarget().claims or not is_in_item_list(seq.getTarget().claims['P31'], 'Q47461344'):
                claim = pywikibot.Claim(repo, 'P31')
                claim.setTarget('Q47461344')
                seq.getTarget().addClaim(claim, bot=True, summary=transcmt)

            if 'P212' in seq.getTarget().claims:
                logger.error('Written work %s must not have an ISBN number' % (seq.getTarget().getID()))

        # Check is inverse relationship "edition of" exists
        work = item.claims['P629'][0].getTarget()
        if len(item.claims['P629']) > 1:
            logger.error('Written work %s is not unique' % (work.getID()))
        elif 'P747' not in work.claims or not is_in_item_list(work.claims['P747'], qnumber):
            claim = pywikibot.Claim(repo, 'P747')
            claim.setTarget(qnumber)
            work.addClaim(claim, bot=True, summary=transcmt)

    # OCLC ID and OCLC Work ID should not be both assigned
    # Move OCLC Work ID to work if possible
    if 'P243' in item.claims and 'P5331' in item.claims:
        # Check if OCLC Work is available
        oclcwork = item.claims['P5331'][0]      # OCLC Work ID should be unique
        oclcworkid = oclcwork.getTarget()       # Get the OCLC Work ID from the edition
        work = item.claims['P629'][0].getTarget()

        # Keep OCLC Work ID in edition if ambiguous
        if len(item.claims['P5331']) > 1:
            logger.error('OCLC Work ID %s is not unique; not moving' % (work.getID()))
        elif 'P629' in item.claims:
            # Edition should belong to only one single work
            # There doesn't exist a moveClaim method?
            logger.warning('Move OCLC Work ID %s to work %s' % (oclcworkid, work.getID()))

            # Keep OCLC Work ID in edition if mismatch or ambiguity
            if len(item.claims['P629']) > 1:
                logger.error('Written Work %s is not unique; not moving' % (work.getID()))
            elif 'P5331' not in work.claims:
                claim = pywikibot.Claim(repo, 'P5331')
                claim.setTarget(oclcworkid)
                work.addClaim(claim, bot=True, summary='#pwb Move OCLC Work ID')

                # OCLC Work ID does not belong to edition
                item.removeClaims(oclcwork, bot=True, summary='#pwb Move OCLC Work ID')
            elif is_in_value_list(work.claims['P5331'], oclcworkid):
                # OCLC Work ID does not belong to edition
                item.removeClaims(oclcwork, bot=True, summary='#pwb Move OCLC Work ID')
            else:
                logger.warning('OCLC Work ID mismatch %s - %s; not moving' % (oclcworkid, work.claims['P5331'][0].getTarget()))
        else:
            logger.error('OCLC Work ID %s conflicts with OCLC ID %s and no work available' % (oclcworkid, item.claims['P243'][0].getTarget()))

    # OCLC work ID should not be registered for editions, only for works
    if 'owi' not in isbn_classify:
        pass
    elif 'P629' in item.claims:
        # Get the work related to the edition
        # Edition should only have one single work
        work = item.claims['P629'][0].getTarget()

        # Assign the OCLC work ID if missing in work
        if 'P5331' not in work.claims or not is_in_value_list(work.claims['P5331'], isbn_classify['owi']):
            logger.warning('Add OCLC work ID (P5331): %s to work %s' % (isbn_classify['owi'], work.getID()))
            claim = pywikibot.Claim(repo, 'P5331')
            claim.setTarget(isbn_classify['owi'])
            work.addClaim(claim, bot=True, summary=transcmt)
    elif 'P243' in item.claims:
        logger.warning('OCLC Work ID %s ignored because of OCLC ID %s and no work available' % (isbn_classify['owi'], item.claims['P243'][0].getTarget()))
    elif 'P5331' not in item.claims or not is_in_value_list(item.claims['P5331'], isbn_classify['owi']):
        # Assign the OCLC work ID only if there is no work, and no OCLC ID for edition
        logger.warning('Add OCLC work ID (P5331): %s to edition (no written work and no OCLC ID)' % (isbn_classify['owi']))
        claim = pywikibot.Claim(repo, 'P5331')
        claim.setTarget(isbn_classify['owi'])
        item.addClaim(claim, bot=True, summary=transcmt)

    # Reverse logic for moving OCLC ID and P212 (ISBN) from work to edition is more difficult because of 1:M relationship...

    # Same logic as for OCLC (work) ID

    # Goodreads-identificatiecode (P2969)

    # Goodreads-identificatiecode for work (P8383) should not be registered for editions; should rather use P2969

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

    # Authority control identifier from WorldCat's “FAST Linked Data” authority file (external ID P2163)
    # Corresponding to P921 (Wikidata main subject)
    if 'fast' in isbn_classify:
        for fast_id in isbn_classify['fast']:

            # Get the main subject item number
            main_subject_query = ("""# Search the main subject
SELECT ?item WHERE {
  ?item wdt:P2163 "%s".
}
""" % (fast_id))

            # Get main subject from FAST ID
            logger.info(main_subject_query)
            generator = pg.WikidataSPARQLPageGenerator(main_subject_query, site=repo)

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
                logger.error('Main subject not found for Fast ID %s - %s' % (fast_id, isbn_classify['fast'][fast_id]))
            elif rescnt == 1:
                if 'P921' not in item.claims or not is_in_item_list(item.claims['P921'], qmain_subject):
                    logger.warning('Add main subject (P921) %s (%s)' % (main_subject_label, qmain_subject))
                    claim = pywikibot.Claim(repo, 'P921')
                    claim.setTarget(main_subject)
                    item.addClaim(claim, bot=True, summary=transcmt)    # Add main subject
                else:
                    logger.info('Skipping main subject %s (%s)' % (main_subject_label, qmain_subject))
            else:
                logger.error('Ambiguous main subject for Fast ID %s - %s' % (fast_id, isbn_classify['fast'][fast_id]))

    # Book description
    isbn_description = isbnlib.desc(isbn_number)
    if isbn_description:
        print()
        print(isbn_description)

    # Currently does not work (service not available)
    try:
        logger.warning('BibTex unavailable')
        return 0
        bibtex_metadata = isbnlib.doi2tex(isbn_doi)
        print(bibtex_metadata)
    except Exception as error:
        logger.error(error)     # Data not available
    return 0


# Error logging
logger = logging.getLogger('create_isbn_edition')
#logging.basicConfig(level=logging.DEBUG)       # Uncomment for debugging
##logger.setLevel(logging.DEBUG)

# Get all program parameters
pgmnm = sys.argv.pop(0)
logger.debug('%s %s' % (pgmnm, '2022-09-05 (gvp)'))

# Get optional parameters

# Get the digital library
if sys.argv:
    booklib = sys.argv.pop(0)
    if booklib == '-':
        booklib = 'goob'

# Get the native language
# The language code is only required when P/Q parameters are added, or different from the LANG code
if sys.argv:
    mainlang = sys.argv.pop(0)

# Get additional P/Q parameters
while sys.argv:
    inpar = PROPRE.findall(sys.argv.pop(0).upper())[0]
    target[inpar] = QSUFFRE.findall(sys.argv.pop(0).upper())[0]

# Connect to databases
repo = pywikibot.Site('wikidata')           # Required for wikidata object access (item, property, statement)

# Get today's date
today = date.today()
date_ref = pywikibot.WbTime(year=int(today.strftime('%Y')),
                            month=int(today.strftime('%m')),
                            day=int(today.strftime('%d')),
                            precision='day')

# Get ItemPage for digital library sources
for src in bib_source:
    bib_source[src] = pywikibot.ItemPage(repo, bib_source[src])

# Validate P/Q list
proptyx={}
targetx={}

# Validate the propery/instance pair
for propty in target:
    if propty not in proptyx:
        proptyx[propty] = pywikibot.PropertyPage(repo, propty)
    targetx[propty] = pywikibot.ItemPage(repo, target[propty])
    targetx[propty].get(get_redirect=True)
    if propty in propreqinst and ('P31' not in targetx[propty].claims or not is_in_item_list(targetx[propty].claims['P31'], propreqinst[propty])):
        logger.critical('%s (%s) is not a language' % (targetx[propty].labels[mainlang], target[propty]))
        sys.exit(12)

# Get list of item numbers
inputfile = sys.stdin.read()            # Typically the Appendix list of references of e.g. a Wikipedia page containing ISBN numbers
itemlist = sorted(set(ISBNRE.findall(inputfile)))   # Extract all ISBN numbers

for isbn_number in itemlist:            # Process the next edition
    amend_isbn_edition(isbn_number)
