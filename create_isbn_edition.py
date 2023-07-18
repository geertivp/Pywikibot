#!/usr/bin/python3

"""Pywikibot client to load ISBN linked data into Wikidata.

Pywikibot script to get ISBN data from a digital library,
and create or amend the related Wikidata item for edition
(with the P212, ISBN number, as unique external ID).

Use digital libraries to get ISBN data in JSON format,
and integrate the results into Wikidata.

ISBN data should only be used for editions,
and not for written works.

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
        sbn     Servizio Bibliotecario Nazionale (Italy)
        wiki    wikipedia.org
        worldcat    WorldCat

    P2:         ISO 639-1 language code
                Default LANG; e.g. en, nl, fr, de, es, it, etc.

    P3 P4...:   P/Q pairs to add additional claims (repeated)
                e.g. P921 Q107643461 (main subject: database management
                linked to P2163 Fast ID 888037)

    stdin: list of ISBN numbers
                (International standard book number; version 10 or 13)

                Free text is accepted (e.g. Wikipedia references list,
                or publication list).
                Identification is done via an ISBN regex expression.

Functionality:

    * Both ISBN-10 and ISBN-13 numbers are accepted as input.
    * Only ISBN-13 numbers are stored.
        ISBN-10 numbers are only used for identification purposes;
        they are not stored.
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

Examples:

    # Default library (Google Books), language (LANG), no additional statements
    pwb create_isbn_edition <<EOF
    9789042925564
    EOF

    # Wikimedia, language English, main subject: database management
    pwb create_isbn_edition wiki en P921 Q107643461 <<EOF
    978-0-596-10089-6
    EOF

Data quality:

    * ISBN numbers (P212) are only assigned to editions.
    * A written work should not have an ISBN number (P212).
    * For targets of P629 (edition of) amend
        "is an Q47461344 (written work) instance"
        and "inverse P747 (work has edition)" statements
    * Use https://query.wikidata.org/querybuilder/ to identify P212 duplicates
        Merge duplicate items before running the script again.
    * The following properties should only be used for written works,
        not for editions:
            P5331:  OCLC work ID (editions should only have P243)
            P8383:  Goodreads-identificatiecode for work
                (editions should only have P2969).

Return status:

    The following status codes are returned to the shell:

    3   Invalid or missing parameter
    4   Library not installed
    12  Item does not exist
    20  Network error
    130 Ctrl-c pressed, program interrupted

Standard ISBN properties for editions:

    P31:Q3331189:   instance of edition (mandatory statement)
    P50:    author
    P123:   publisher
    P212:   canonical ISBN number (with dashes; searchable via Wikidata Query)
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
    P813:   Retrieval date
    P1545:  (author) sequence number

External identifiers:

    P243:   OCLC ID
    P1036:  Dewey Decimal Classification
    P2163:  Fast ID (inverse lookup via Wikidata Query) -> P921: main subject
    P2969:  Goodreads-identificatiecode

    (only for written works)
    P5331:  OCLC work ID (editions should only have P243)
    P8383:  Goodreads-identificatiecode for work (not yet implemented; editions should only have P2969)

    (not yet implemented)
    P213:   ISNI ID
    P496:   ORCID ID
    P675:   Google Books-identificatiecode

Unavailable properties:

    (not implemented by isbnlib)
    P98:    Editor
    P110:   Illustrator/photographer
    P291:   place of publication
    P1104:  number of pages
    :       format (hardcover, paperback)

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

    https://www.wikidata.org/wiki/Wikidata:List_of_properties/work
    https://www.wikidata.org/wiki/Template:Book_properties
    https://www.wikidata.org/wiki/Template:Bibliographic_properties
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData
    https://www.wikidata.org/wiki/Help:Sources
    https://www.wikidata.org/wiki/Q22696135 (Wikidata references module)

    https://www.geeksforgeeks.org/searching-books-with-python/
    http://classify.oclc.org/classify2/ClassifyDemo
    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html
    https://www.mediawiki.org/wiki/API:Search
    https://www.mediawiki.org/wiki/Wikibase/API

Prerequisites:

    pywikibot

    Install the following ISBN lib packages:
    https://pypi.org/search/?q=isbnlib

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
        The language code is not always available from the digital library;
        therefore we need a default.
    * Publisher unknown:
        * Missing P31:Q2085381 statement, missing subclass in script
        * Missing alias
        * Create publisher
    * Unknown author: create author as a person

Known problems:

    * Unknown ISBN, e.g. 9789400012820
    * Some digital libraries have more registrations than others
    * Some digital libraries have data quality problems
    * No ISBN data available for an edition either causes no output
        (goob = Google Books), or an error message (wiki, openl).
        The script is taking care of both.
    * Only 6 ISBN attributes are listed by the webservice(s)
        missing are e.g.: place of publication, number of pages
    * Not all ISBN atttributes have data values
        (authors, publisher, date of publication, language can be missing at the digital library).
    * The script uses multiple webservice calls (script might take time, but it is automated)
    * BibTex service is currently unavailable
    * Need to amend ISBN items that have no author, publisher, or other required data
        * You could use another digital library?
        * Which other services to use?
    * How to add still more digital libraries?
        * This would require an additional isbnlib module
        * Does the KBR has a public ISBN service (Koninklijke Bibliotheek van België)?
    * Filter for work properties:
        https://www.wikidata.org/wiki/Q63413107
        ['9781282557246', '9786612557248', '9781847196057', '9781847196040']
        P5331: OCLC identification code for work 793965595 (should only have P243)
        P8383: Goodreads identification code for work 13957943 (should only have P2969)
    * ERROR: an HTTP error has ocurred ((503) Service Unavailable)

To do:

    * Implement a webservice at toolforge.org, based on this shell script
        Have an input text box and an "Execute" button
        Then have a transaction log

Algorithm:

    Get parameters from shell
    Validate parameters
    Get ISBN data
    Convert ISBN data:
        Reverse names when Lastname, Firstname
    Get additional data
    Register ISBN data into Wikidata:
        Add source reference when creating the item:
            (digital library instance, retrieval date)
        Create or amend items or claims:
            Number the authors in order of appearence
            Check data consistency
            Correct data quality problems:
                OCLC Work ID for Written work
                Written work instance statement
                Inverse relationship written work -> edition
                Move/register OCLC work ID to/with written work
    Manually corrections:
        Create missing (referenced) items
            (authors, publishers, written works, main subject/FAST ID)
        Resolve ambiguous values

Environment:

    The python script can run on the following platforms:

        Linux client
        Google Chromebook (Linux container)
        Toolforge portal
        PAWS

    LANG: default ISO 639-1 language code

Source code:

    https://github.com/geertivp/Pywikibot/blob/main/create_isbn_edition.py
    https://gerrit.wikimedia.org/r/c/pywikibot/core/+/826631
    https://gerrit.wikimedia.org/r/c/pywikibot/core/+/826631/3/scripts/create_isbn_edition.py
    https://gerrit.wikimedia.org/r/plugins/gitiles/pywikibot/core/+/refs/heads/stable/scripts/create_isbn_edition.py
    https://phabricator.wikimedia.org/T314942

Applications:

    Generate a book reference
        Example: {{Cite Q|Q63413107}} (only available at wp.en)
        Use the Visual editor reference with Qnumber

    See also:
        https://www.wikidata.org/wiki/Wikidata:WikiProject_Books
        https://www.wikidata.org/wiki/Q21831105 (WikiProject Books)
        https://meta.wikimedia.org/wiki/WikiCite
        https://phabricator.wikimedia.org/tag/wikicite/
        https://www.wikidata.org/wiki/Q21831105 (WikiCite)
        https://www.wikidata.org/wiki/Q22321052 (Cite_Q)
        https://www.mediawiki.org/wiki/Global_templates
        https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData
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

    https://isbn.org/ISBN_converter
    https://en.wikipedia.org/wiki/bibliographic_database
    https://www.titelbank.nl/pls/ttb/f?p=103:4012:::NO::P4012_TTEL_ID:3496019&cs=19BB8084860E3314502A1F777F875FE61

"""

import isbnlib          # ISBN library
import os               # Operating system
import pywikibot        # API interface to Wikidata
import re               # Regular expressions (very handy!)
import sys              # System calls
import unidecode        # Unicode
from pywikibot.data import api
from datetime import date, datetime	        # now, strftime, delta time, total_seconds

# Global variables
modnm = 'Pywikibot create_isbn_edition'     # Module name (using the Pywikibot package)
pgmid = '2023-07-18 (gvp)'	                # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

ENLANG = 'en'

INSTANCEPROP = 'P31'
AUTHORPROP = 'P50'
EDITORPROP = 'P98'
ILLUSTRATORPROP = 'P110'
PUBLISHERPROP = 'P123'
ISBNPROP = 'P212'
OCLDIDPROP = 'P243'
REFPROP = 'P248'
EDITIONLANGPROP = 'P407'
WIKILANGPROP = 'P424'
PUBYEARPROP = 'P577'
WRITTENWORKPROP = 'P629'
EDITIONPROP = 'P747'
REFDATEPROP = 'P813'
MAINSUBPROP = 'P921'
ISBN10PROP = 'P957'
DEWCLASIDPROP = 'P1036'
EDITIONTITLEPROP = 'P1476'
SEQNRPROP = 'P1545'
EDITIONSUBTITLEPROP = 'P1680'
FASTIDPROP = 'P2163'
OCLCWORKIDPROP = 'P5331'
LIBCONGEDPROP = 'P8360'

# Constants
BOTFLAG = True

# Initialisation
booklib = 'wiki'        # Default digital library

exitfatal = True	    # Exit on fatal error (can be disabled with -p; please take care)
exitstat = 0            # (default) Exit status

# List of of digital libraries
bib_source = {
    'bnf': ('Q193563', 'Catalogue General (France)'),
    'bol': ('Q609913', 'Bol.Com'),
    'dnb': ('Q27302', 'Deutsche National Library'),
    'goob': ('Q206033', 'Google Books'),
    'kb': ('Q1526131', 'Koninklijke Bibliotheek (Nederland)'),
    #'kbr': ('Q383931', 'Koninklijke Bibliotheek (België)'),  # Not implemented in Belgium
    'loc': ('Q131454', 'Library of Congress US'),
    'mcues': ('Q750403', 'Ministerio de Cultura (Spain)'),
    'openl': ('Q1201876', 'OpenLibrary.org'),
    'porbase': ('Q51882885', 'Portugal (urn.porbase.org)'),
    'sbn': ('Q576951', 'Servizio Bibliotecario Nazionale (Italië)'),
    'wiki': ('Q64692275', 'Wikipedia.org'),
    'worldcat': ('Q76630151', 'WorldCat (worldcat2)'),
}

# Remap obsolete or non-standard language codes
langcode = {
    'dut': 'nl',
    'eng': 'en',
    'frans': 'fr',
    'fre': 'fr',
    'iw': 'he',
    'nld': 'nl',
}

# Instance validation rules
propreqinst = {
    AUTHORPROP: {'Q5'},                                 # Author requires human
    EDITIONLANGPROP: {'Q34770', 'Q33742', 'Q1288568'},  # Edition language requires at least one of (living, natural) language
    PUBLISHERPROP: {'Q2085381', 'Q1114515', 'Q1320047', 'Q479716'},   # Publisher requires type of publisher
    WRITTENWORKPROP: ['Q47461344', 'Q7725634'],         # Written work
}

# Statement property validation rules
propreqobjectprop = {
    MAINSUBPROP: FASTIDPROP,        # Main subject statement requires an object with FAST ID property
}

# Required statement for edition
# Other statements are added via command line parameters
target = {
    INSTANCEPROP: 'Q3331189',      # Is an instance of an edition
}

# Wikidata transaction comment
transcmt = '#pwb Create ISBN edition'

# ISBN number: 10 or 13 digits with optional dashes (-)
# or DOI number with 10-prefix
ISBNRE = re.compile(r'[0-9-–]{10,17}')
NAMEREVRE = re.compile(r',(\s*.*)*$')	    # Reverse lastname, firstname
PROPRE = re.compile(r'P[0-9]+')             # Wikidata P-number
QSUFFRE = re.compile(r'Q[0-9]+')            # Wikidata Q-number
SUFFRE = re.compile(r'\s*[(].*[)]$')		# Remove trailing () suffix (keep only the base label)


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


def get_language_preferences():
    """
    Get the list of preferred languages,
    using environment variables LANG, LC_ALL, and LANGUAGE.
    Result:
        List of ISO 639-1 language codes
    Documentation:
        https://www.gnu.org/software/gettext/manual/html_node/Locale-Environment-Variables.html
    """
    mainlang = os.getenv('LANGUAGE',
                         os.getenv('LC_ALL',
                         os.getenv('LANG', ENLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang]
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)
    return main_languages


def item_is_in_list(statement_list, itemlist):
    """
    Verify if statement list contains at least one item from the itemlist
    param: statement_list: Statement list
    param: itemlist:      List of values (string)
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
        baselabel = (baselabel[commaloc.start() + 1:]
                     + ' ' + baselabel[:commaloc.start()])
        baselabel = baselabel.replace(',',' ')  # Remove remaining ","

    # Remove redundant spaces
    baselabel = ' '.join(baselabel.split())
    return baselabel


def get_item_list(item_name: str, instance_id) -> list:
    """Get list of items by name, belonging to an instance (list)

    :param item_name: Item name (string)
    :param instance_id: Instance ID (string, set, or list)
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
              'limit': 20}
    request = api.Request(site=repo, parameters=params)
    result = request.submit()

    pywikibot.debug(result)

    if 'search' in result:
        # Ignore accents and case
        item_name_canon = unidecode.unidecode(item_name).lower()
        for row in result['search']:                    # Loop though items
            ##print(row)
            item = pywikibot.ItemPage(repo, row['id'])
            try:
                item.get()
            except pywikibot.exceptions.IsRedirectPageError:
                # Resolve a single redirect error
                item = item.getRedirectTarget()
                pywikibot.warning('Item {} redirects to {}'.format(row['id'], item.getID()))

            # Matching instance
            if INSTANCEPROP in item.claims and item_is_in_list(item.claims[INSTANCEPROP], instance_id):
                # Search all languages
                for lang in item.labels:
                    if item_name_canon == unidecode.unidecode(item.labels[lang]).lower():
                        item_list.add(item.getID())     # Label match
                        break
                for lang in item.aliases:
                    for seq in item.aliases[lang]:
                        if item_name_canon == unidecode.unidecode(seq).lower():
                            item_list.add(item.getID()) # Alias match
                            break
    # Convert set to list
    return list(item_list)


def get_item_with_prop_value (prop: str, propval: str) -> list:
    """Get list of items that have a property/value statement

    :param prop: Property ID (string)
    :param propval: Property value (string)
    :return: List of items (Q-numbers)

    See https://www.mediawiki.org/wiki/API:Search
    """
    pywikibot.debug('Search statement: {}:{}'.format(prop, propval))
    item_name_canon = unidecode.unidecode(propval).lower()
    item_list = set()                   # Empty set
    params = {'action': 'query',        # Statement search
              'list': 'search',
              'srsearch': prop + ':' + propval,
              'srwhat': 'text',
              'format': 'json',
              'srlimit': 10}
    request = api.Request(site=repo, parameters=params)
    result = request.submit()
    # https://www.wikidata.org/w/api.php?action=query&list=search&srwhat=text&srsearch=P212:978-94-028-1317-3

    if 'query' in result:
        if 'search' in result['query']:
            # Loop though items
            for row in result['query']['search']:
                item = pywikibot.ItemPage(repo, row['title'])
                try:
                    item.get()
                except pywikibot.exceptions.IsRedirectPageError:
                    # Resolve a single redirect error
                    item = item.getRedirectTarget()
                    pywikibot.warning('Item {} redirects to {}'.format(row['title'], item.getID()))

                if prop in item.claims:
                    for seq in item.claims[prop]:
                        if unidecode.unidecode(seq.getTarget()).lower() == item_name_canon:
                            item_list.add(item.getID()) # Found match
                            break
    # Convert set to list
    return list(item_list)


def amend_isbn_edition(isbn_number) -> int:
    """Amend the ISBN registration in Wikidata.

    It is registering the ISBN-13 data via P212,
    depending on the data obtained from the chosen digital library.

    :param isbn_number: ISBN number
        (string; 10 or 13 digits with optional hyphens)
    :result: Status (int)
        0:  Amended (found or created)
        1:  Not found
        2:  Ambiguous
        3:  Other error
    """
    global proptyx
    # targetx is not global (to allow for language specific editions)

    ##print(isbn_number)
    isbn_number = isbn_number.strip()
    if not isbn_number:
        return 3    # Do nothing when the ISBN number is missing

    # Validate ISBN data
    pywikibot.log('')

    # Some digital library services raise failure;
    try:
        isbn_data = isbnlib.meta(isbn_number, service=booklib)
        pywikibot.debug(isbn_data)
        # {'ISBN-13': '9789042925564', 'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. Aspecten Uit De Industriele Geschiedenis Van Leuven', 'Authors': ['A. Cresens'], 'Publisher': 'Peeters Pub & Booksellers', 'Year': '2012', 'Language': 'nl'}
    except isbnlib._exceptions.NotRecognizedServiceError as error:
        fatal_error(4, '{}\n\tpip install isbnlib-xxx'.format(error))
    except Exception as error:
        # When the book is unknown, the function returns
        pywikibot.error(error)
        #raise
        #raise ValueError(error)
        return 1

    # Others return an empty result
    if not isbn_data:
        pywikibot.error('Unknown ISBN book number {}'
                        .format(isbn_number))
        return 1

    # Show the raw results
    for seq in isbn_data:
        pywikibot.log('{}:\t{}'.format(seq, isbn_data[seq]))

    # Get the book language from the ISBN book number
    # Can overwrite the default language
    booklang = mainlang
    if isbn_data['Language']:
        booklang = isbn_data['Language'].strip().lower()

        # Replace obsolete or non-standard codes
        if booklang in langcode:
            booklang = langcode[booklang]

    # Get Wikidata language code
    lang_list = get_item_list(booklang, propreqinst[EDITIONLANGPROP])
    if len(lang_list) == 1:
        target[EDITIONLANGPROP] = lang_list[0]
    elif lang_list:
        pywikibot.error('Ambiguous language {}'.format(booklang))
        return 3
    else:
        pywikibot.error('Unknown language {}'.format(booklang))
        return 3

    # Get short Wikipedia language code
    if len(booklang) > 3:
        lang = pywikibot.ItemPage(repo, lang_list[0])
        try:
            lang.get()
        except pywikibot.exceptions.IsRedirectPageError:
            # Resolve a single redirect error
            lang = lang.getRedirectTarget()
            pywikibot.warning('Item {} redirects to {}'.format(lang_list[0], lang.getID()))

        if WIKILANGPROP in lang.claims:
            booklang = lang.claims[WIKILANGPROP][0].getTarget()

    pywikibot.debug(target)

    # Get formatted ISBN number
    isbn_number = isbn_data['ISBN-13']          # Numeric format
    isbn_fmtd = isbnlib.mask(isbn_number)       # Canonical format (with "-")
    isbn10_number = isbnlib.to_isbn10(isbn_number)  # Empty string for non-978 numbers
    pywikibot.log(isbn_fmtd)

    # Get (sub)title when there is a dot
    edition_title = isbn_data['Title'].strip()
    print(edition_title)
    titles = edition_title.split('|')           # kb is using '|'
    if len(titles) > 2:
        titles = [titles[0].strip()]
        edition_title = titles[0]               # Ambiguous subtitle; restore original value

    if len(titles) == 1:
        titles = edition_title.split(' - ')     # Extract subtitle
    if len(titles) == 1:
        titles = edition_title.split(': ')      # Extract subtitle
    if len(titles) == 1:
        titles = edition_title.split('. ')      # goob is using a '.'
    if len(titles) == 1:
        titles = edition_title.split(', ')      # Extract subtitle
    if len(titles) > 2:
        titles = [edition_title]                # Ambiguous subtitle; restore original value

    objectname = titles[0].strip()
    if len(titles) > 1:
        subtitle = titles[1].strip()            # Only main titles are stored in Wikidata...
        subtitle = subtitle[0].upper() + subtitle[1:]   # Upcase first character
    else:
        subtitle = ''                           # No subtitle

    # Print book titles
    for seq in titles:      # Print title and subtitle, when available
        pywikibot.log(seq)

    # Search the ISBN number both in canonical and numeric format
    qnumber_list = get_item_with_prop_value(ISBNPROP, isbn_fmtd)
    qnumber_list += get_item_with_prop_value(ISBNPROP, isbn_number)
    if isbn10_number:
        isbn10_fmtd = isbnlib.mask(isbn10_number)
        qnumber_list += get_item_with_prop_value(ISBN10PROP, isbn10_fmtd)
        qnumber_list += get_item_with_prop_value(ISBN10PROP, isbn10_number)
    qnumber_list = list(set(qnumber_list))      # Get unique values

    # Create or amend the item
    if len(qnumber_list) == 1:
        qnumber = qnumber_list[0]
        item = pywikibot.ItemPage(repo, qnumber)

        try:
            item.get()
        except pywikibot.exceptions.IsRedirectPageError:
            # Resolve a single redirect error (should normally not occur...)
            item = item.getRedirectTarget()
            pywikibot.warning('Item {} redirects to {}'.format(qnumber, item.getID()))
            qnumber = item.getID()

        # Update item only if edition, or instance is missing
        if (INSTANCEPROP in item.claims
                and not item_is_in_list(item.claims[INSTANCEPROP], target[INSTANCEPROP])):
            pywikibot.error('Item {} {} is not an edition; not updated'.format(qnumber, isbn_fmtd))
            return 3

        pywikibot.warning('Found item: {} ({}) {}'.format(isbn_fmtd, qnumber, objectname))

        # Add missing book label for book language
        if booklang not in item.labels:
            item.labels[booklang] = objectname
            item.editEntity({'labels': item.labels}, summary=transcmt)

    elif qnumber_list:
        # Do not update when ambiguous
        pywikibot.error('Ambiguous ISBN number {} not updated'.format(isbn_fmtd))
        pywikibot.debug(qnumber_list)
        return 2
    else:
        # Prepare creation of edition
        label = {}
        label[booklang] = objectname
        item = pywikibot.ItemPage(repo)         # Create item
        item.editEntity({'labels': label}, summary=transcmt)
        qnumber = item.getID()
        pywikibot.warning('Creating item: {} ({}) language {} ({}) {}'
                          .format(isbn_fmtd, qnumber, booklang, target[EDITIONLANGPROP], objectname))

    # Register missing statements
    for propty in target:
        if propty not in item.claims:
            if propty not in proptyx:
                proptyx[propty] = pywikibot.PropertyPage(repo, propty)
            # Target could get overwritten locally
            targetx[propty] = pywikibot.ItemPage(repo, target[propty])

            try:
                # Make sure that labels are known in the native language
                pywikibot.warning('Add {} ({}): {} ({})'
                                  .format(proptyx[propty].labels[booklang],
                                          propty,
                                          targetx[propty].labels[booklang],
                                          target[propty]))
            except:
                pywikibot.warning('Add {}:{}'.format(propty, target[propty]))

            claim = pywikibot.Claim(repo, propty)
            claim.setTarget(targetx[propty])
            item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

            # Set source reference
            if booklib in bib_sourcex:
                # A source reference can be only used once
                # Expected error: "The provided Claim instance is already used in an entity"
                # This error is sometimes raised without reason
                try:
                    claim.addSources([references, retrieved], summary=transcmt)
                except Exception as error:
                    pywikibot.error(error)

    # Set formatted ISBN-13 number
    if ISBNPROP not in item.claims:
        pywikibot.warning('Add ISBN number ({}): {}'.format(ISBNPROP, isbn_fmtd))
        claim = pywikibot.Claim(repo, ISBNPROP)
        claim.setTarget(isbn_fmtd)
        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
    else:
        # Update unformatted to formatted ISBN-13
        for seq in item.claims[ISBNPROP]:
            if seq.getTarget() == isbn_number:
                pywikibot.warning('Set formatted ISBN number ({}): {}'
                                  .format(ISBNPROP, isbn_fmtd))
                seq.changeTarget(isbn_fmtd, bot=BOTFLAG, summary=transcmt)

    # Update unformatted to formatted ISBN-10
    if ISBN10PROP in item.claims:
        for seq in item.claims[ISBN10PROP]:
            if seq.getTarget() == isbn10_number:
                pywikibot.warning('Set formatted ISBN-10 number ({}): {}'
                                  .format(ISBN10PROP, isbn10_fmtd))
                seq.changeTarget(isbn10_fmtd, bot=BOTFLAG, summary=transcmt)

    # Title
    if EDITIONTITLEPROP not in item.claims:
        pywikibot.warning('Add Title ({}): {}'.format(EDITIONTITLEPROP, objectname))
        claim = pywikibot.Claim(repo, EDITIONTITLEPROP)
        claim.setTarget(pywikibot.WbMonolingualText(text=objectname, language=booklang))
        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

    # Subtitle
    if subtitle and EDITIONSUBTITLEPROP not in item.claims:
        pywikibot.warning('Add Subtitle ({}): {}'.format(EDITIONSUBTITLEPROP, subtitle))
        claim = pywikibot.Claim(repo, EDITIONSUBTITLEPROP)
        claim.setTarget(pywikibot.WbMonolingualText(text=subtitle, language=booklang))
        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

    # Date of publication
    pub_year = isbn_data['Year']
    if pub_year and PUBYEARPROP not in item.claims:
        pywikibot.warning('Add Year of publication ({}): {}'
                          .format(PUBYEARPROP, isbn_data['Year']))
        claim = pywikibot.Claim(repo, PUBYEARPROP)
        claim.setTarget(pywikibot.WbTime(year=int(pub_year), precision='year'))
        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

    # Set the author list
    author_cnt = 0
    for author_name in isbn_data['Authors']:
        author_name = author_name.strip()
        if author_name:
            author_cnt += 1

            # Reorder "lastname, firstname" and concatenate with space
            author_name = get_canon_name(author_name)
            author_list = get_item_list(author_name, propreqinst[AUTHORPROP])

            if len(author_list) == 1:
                authortoadd = True

                # Possibly found as author?
                # Possibly found as editor?
                # Possibly found as illustrator/photographer?
                for prop in (AUTHORPROP, EDITORPROP, ILLUSTRATORPROP):
                    if prop in item.claims:
                        for claim in item.claims[prop]:
                            book_author = claim.getTarget()
                            if book_author.getID() == author_list[0]:
                                # Add sequence number
                                if SEQNRPROP not in claim.qualifiers:
                                    qualifier = pywikibot.Claim(repo, SEQNRPROP)
                                    qualifier.setTarget(str(author_cnt))
                                    claim.addQualifier(qualifier, summary=transcmt)
                                authortoadd = False
                                break
                            elif item_has_label(book_author, author_name):
                                pywikibot.warning('Edition has conflicting author ({}) {} ({})'
                                                  .format(prop, author_name, book_author.getID()))
                                authortoadd = False
                                break

                if authortoadd:
                    pywikibot.warning('Add author {:d} ({}): {} ({})'
                                      .format(author_cnt, AUTHORPROP, author_name, author_list[0]))
                    claim = pywikibot.Claim(repo, AUTHORPROP)
                    claim.setTarget(pywikibot.ItemPage(repo, author_list[0]))
                    item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

                    # Add sequence number
                    qualifier = pywikibot.Claim(repo, SEQNRPROP)
                    qualifier.setTarget(str(author_cnt))
                    claim.addQualifier(qualifier, summary=transcmt)
            elif author_list:
                pywikibot.error('Ambiguous author: {}'.format(author_name))
            else:
                pywikibot.error('Unknown author: {}'.format(author_name))

    # Set the publisher
    publisher_name = isbn_data['Publisher'].strip()
    if publisher_name:
        publisher_list = get_item_list(get_canon_name(publisher_name), propreqinst[PUBLISHERPROP])

        if len(publisher_list) == 1:
            if (PUBLISHERPROP not in item.claims
                    or not item_is_in_list(item.claims[PUBLISHERPROP], publisher_list)):
                pywikibot.warning('Add publisher ({}): {} ({})'
                                  .format(PUBLISHERPROP, publisher_name, publisher_list[0]))
                claim = pywikibot.Claim(repo, PUBLISHERPROP)
                claim.setTarget(pywikibot.ItemPage(repo, publisher_list[0]))
                item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
        elif publisher_list:
            pywikibot.error('Ambiguous publisher: {}'.format(publisher_name))
        else:
            pywikibot.error('Unknown publisher: {}'.format(publisher_name))

    # Amend Written work relationship (one to many relationship)
    if WRITTENWORKPROP in item.claims:
        work = item.claims[WRITTENWORKPROP][0].getTarget()
        if len(item.claims[WRITTENWORKPROP]) > 1:    # Many to many (error)
            pywikibot.error('Written work {} is not unique'.format(work.getID()))
        else:
            # Enhance data quality for Written work
            if ISBNPROP in work.claims:
                pywikibot.error('Written work {} must not have an ISBN number'
                                .format(work.getID()))

            # Add written work instance
            if (INSTANCEPROP not in work.claims
                    or not item_is_in_list(work.claims[INSTANCEPROP], propreqinst[WRITTENWORKPROP])):
                pywikibot.warning('Add Written work instance ({}) {} for written work {}'
                                  .format(INSTANCEPROP, propreqinst[WRITTENWORKPROP][0], work.getID()))
                claim = pywikibot.Claim(repo, INSTANCEPROP)
                claim.setTarget(pywikibot.ItemPage(repo, propreqinst[WRITTENWORKPROP][0]))
                work.addClaim(claim, bot=BOTFLAG, summary=transcmt)

            # Check if inverse relationship to "edition of" exists
            if (EDITIONPROP not in work.claims
                    or not item_is_in_list(work.claims[EDITIONPROP], qnumber)):
                pywikibot.warning('Add edition statement ({}) {} to work {}'
                                  .format(EDITIONPROP, qnumber, work.getID()))
                claim = pywikibot.Claim(repo, EDITIONPROP)
                claim.setTarget(item)
                work.addClaim(claim, bot=BOTFLAG, summary=transcmt)

    # Get addional data from the digital library
    isbn_classify = isbnlib.classify(isbn_number)
    isbn_cover = isbnlib.cover(isbn_number)
    isbn_doi = isbnlib.doi(isbn_number)
    isbn_editions = isbnlib.editions(isbn_number, service='merge')
    isbn_info = isbnlib.info(isbn_number)

    pywikibot.log(isbn_info)
    pywikibot.log(isbn_doi)
    pywikibot.log(isbn_editions)

    # Book cover images
    for seq in isbn_cover:
        pywikibot.log('{}:\t{}'.format(seq, isbn_cover[seq]))

    # Handle ISBN classification
    for seq in isbn_classify:
        pywikibot.debug('{}:\t{}'.format(seq, isbn_classify[seq]))

    # ./create_isbn_edition.py '978-3-8376-5645-9' - de P407 Q188
    # Q113460204
    # {'owi': '11103651812', 'oclc': '1260160983', 'lcc': 'TK5105.8882', 'ddc': '300', 'fast': {'1175035': 'Wikis (Computer science)', '1795979': 'Wikipedia', '1122877': 'Social sciences'}}

    # We need to first set the OCLC ID
    # Because OCLC Work ID can be in conflict for edition
    if 'oclc' in isbn_classify and OCLDIDPROP not in item.claims:
        pywikibot.warning('Add OCLC ID ({}): {}'.format(OCLDIDPROP, isbn_classify['oclc']))
        claim = pywikibot.Claim(repo, OCLDIDPROP)
        claim.setTarget(isbn_classify['oclc'])
        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

    # OCLC ID and OCLC Work ID should not be both assigned
    # Move OCLC Work ID to work if possible
    if OCLDIDPROP in item.claims and OCLCWORKIDPROP in item.claims:
        # Check if OCLC Work is available
        oclcwork = item.claims[OCLCWORKIDPROP][0]      # OCLC Work ID should be unique
        oclcworkid = oclcwork.getTarget()       # Get the OCLC Work ID from the edition

        # Keep OCLC Work ID in edition if ambiguous
        if len(item.claims[OCLCWORKIDPROP]) > 1:
            pywikibot.error('OCLC Work ID {} is not unique; not moving'
                            .format(work.getID()))
        elif WRITTENWORKPROP in item.claims:
            # Edition should belong to only one single work
            # There doesn't exist a moveClaim method?
            work = item.claims[WRITTENWORKPROP][0].getTarget()
            pywikibot.warning('Move OCLC Work ID {} to work {}'
                              .format(oclcworkid, work.getID()))

            # Keep OCLC Work ID in edition if mismatch or ambiguity
            if len(item.claims[WRITTENWORKPROP]) > 1:
                pywikibot.error('Written Work {} is not unique; not moving'
                                .format(work.getID()))
            elif OCLCWORKIDPROP not in work.claims:
                pywikibot.warning('Move OCLC Work ID ({}) {} to written work {}'
                                  .format(OCLCWORKIDPROP, oclcworkid, work.getID()))
                claim = pywikibot.Claim(repo, OCLCWORKIDPROP)
                claim.setTarget(oclcworkid)
                work.addClaim(claim, bot=BOTFLAG, summary='#pwb Move OCLC Work ID')

                # OCLC Work ID does not belong to edition
                item.removeClaims(oclcwork, bot=BOTFLAG, summary='#pwb Move OCLC Work ID')
            elif is_in_value_list(work.claims[OCLCWORKIDPROP], oclcworkid):
                # OCLC Work ID does not belong to edition
                item.removeClaims(oclcwork, bot=BOTFLAG, summary='#pwb Remove redundant OCLC Work ID')
            else:
                pywikibot.error('OCLC Work ID mismatch {} - {}; not moving'
                                .format(oclcworkid, work.claims[OCLCWORKIDPROP][0].getTarget()))
        else:
            pywikibot.error('OCLC Work ID {} conflicts with OCLC ID {} and no work available'
                            .format(oclcworkid, item.claims[OCLDIDPROP][0].getTarget()))

    # OCLC work ID should not be registered for editions, only for works
    if 'owi' not in isbn_classify:
        pass
    elif WRITTENWORKPROP in item.claims:
        # Get the work related to the edition
        # Edition should only have one single work
        # Assign the OCLC work ID if missing in work
        work = item.claims[WRITTENWORKPROP][0].getTarget()
        if (OCLCWORKIDPROP not in work.claims
                or not is_in_value_list(work.claims[OCLCWORKIDPROP], isbn_classify['owi'])):
            pywikibot.warning('Add OCLC work ID ({}) {} to work {}'
                              .format(OCLCWORKIDPROP, isbn_classify['owi'], work.getID()))
            claim = pywikibot.Claim(repo, OCLCWORKIDPROP)
            claim.setTarget(isbn_classify['owi'])
            work.addClaim(claim, bot=BOTFLAG, summary=transcmt)
    elif OCLDIDPROP in item.claims:
        pywikibot.error('OCLC Work ID {} ignored because of OCLC ID {} and no work available'
                        .format(isbn_classify['owi'],
                                item.claims[OCLDIDPROP][0].getTarget()))
    elif (OCLCWORKIDPROP not in item.claims
            or not is_in_value_list(item.claims[OCLCWORKIDPROP], isbn_classify['owi'])):
        # Assign the OCLC work ID only if there is no work, and no OCLC ID for edition
        pywikibot.warning('Add OCLC work ID ({}): {} to edition (no written work and no OCLC ID)'
                          .format(OCLCWORKIDPROP, isbn_classify['owi']))
        claim = pywikibot.Claim(repo, OCLCWORKIDPROP)
        claim.setTarget(isbn_classify['owi'])
        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

    # Reverse logic for moving OCLC ID and P212 (ISBN) from work to edition is more difficult because of 1:M relationship...

    # Same logic as for OCLC (work) ID

    # Goodreads-identificatiecode (P2969)

    # Goodreads-identificatiecode for work (P8383) should not be registered for editions; should rather use P2969

    # Library of Congress Classification (works and editions)
    if 'lcc' in isbn_classify and LIBCONGEDPROP not in item.claims:
        pywikibot.warning('Add Library of Congress Classification for edition ({}): {}'
                          .format(LIBCONGEDPROP, isbn_classify['lcc']))
        claim = pywikibot.Claim(repo, LIBCONGEDPROP)
        claim.setTarget(isbn_classify['lcc'])
        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

    # Dewey Decimale Classificatie
    if 'ddc' in isbn_classify and DEWCLASIDPROP not in item.claims:
        pywikibot.warning('Add Dewey Decimale Classificatie ({}): {}'
                          .format(DEWCLASIDPROP, isbn_classify['ddc']))
        claim = pywikibot.Claim(repo, DEWCLASIDPROP)
        claim.setTarget(isbn_classify['ddc'])
        item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

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
            qmain_subject = get_item_with_prop_value(FASTIDPROP, fast_id)
            main_subject_label = isbn_classify['fast'][fast_id].lower()

            if len(qmain_subject) == 1:
                main_subject = pywikibot.ItemPage(repo, qmain_subject[0])
                try:
                    main_subject.get()
                except pywikibot.exceptions.IsRedirectPageError:
                    # Resolve a single redirect error
                    main_subject = item.getRedirectTarget()

                # Get main subject label
                try:
                    main_subject_label = main_subject.labels[mainlang]
                except:
                    pywikibot.error('Missing {}:label "{}" for item {}'
                                    .format(booklang, main_subject_label,
                                            qmain_subject[0]))

                if (MAINSUBPROP in item.claims
                        and item_is_in_list(item.claims[MAINSUBPROP], qmain_subject[0])):
                    pywikibot.log('Skipping main subject ({}): {} ({})'
                                    .format(MAINSUBPROP, main_subject_label, qmain_subject[0]))
                else:
                    pywikibot.warning('Add main subject ({}): {} ({})'
                                      .format(MAINSUBPROP, main_subject_label, qmain_subject[0]))
                    claim = pywikibot.Claim(repo, MAINSUBPROP)
                    claim.setTarget(main_subject)
                    item.addClaim(claim, bot=BOTFLAG, summary=transcmt)    # Add main subject
            elif qmain_subject:
                pywikibot.error('Ambiguous main subject for Fast ID {} - {}'
                                .format(fast_id, main_subject_label))
            else:
                pywikibot.error('Main subject not found for Fast ID {} - {}'
                                .format(fast_id, main_subject_label))

    # Book description
    isbn_description = isbnlib.desc(isbn_number)
    if isbn_description:
        print()
        print(isbn_description)

    # Currently does not work (service not available)
    try:
        pywikibot.debug('BibTex service unavailable')
        return 0
        bibtex_metadata = isbnlib.doi2tex(isbn_doi)
        print(bibtex_metadata)
    except Exception as error:
        pywikibot.error(error)     # Data not available
        return 3

    return 0


# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

# Get all program parameters
pgmnm = sys.argv.pop(0)
pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))

# Get optional parameters (all are optional)

# Get the digital library
if sys.argv:
    booklib = sys.argv.pop(0)
    if booklib == '-':
        booklib = 'wiki'

# Get the native language
# The language code is only required when P/Q parameters are added,
# or different from the LANG code
if sys.argv:
    mainlang = sys.argv.pop(0)

# Get additional P/Q parameters
while sys.argv:
    try:
        inpar = PROPRE.findall(sys.argv.pop(0).upper())[0]
    except:
        pywikibot.critical('Property required')
        sys.exit(3)

    try:
        target[inpar] = QSUFFRE.findall(sys.argv.pop(0).upper())[0]
    except:
        pywikibot.critical('Item required')
        sys.exit(3)

# Connect to databases
repo = pywikibot.Site('wikidata')           # Required for wikidata object access (item, property, statement)

# Get today's date
today = date.today()
date_ref = pywikibot.WbTime(year=int(today.strftime('%Y')),
                            month=int(today.strftime('%m')),
                            day=int(today.strftime('%d')),
                            precision='day')

# Get ItemPage for digital library sources
bib_sourcex = {}
for src in bib_source:
    bib_sourcex[src] = pywikibot.ItemPage(repo, bib_source[src][0])

if booklib in bib_sourcex:
    references = pywikibot.Claim(repo, REFPROP)
    references.setTarget(bib_sourcex[booklib])

    # Set retrieval date
    retrieved = pywikibot.Claim(repo, REFDATEPROP)
    retrieved.setTarget(date_ref)

    # Register source and retrieval date
    pywikibot.warning('Use Digital library ({}): {} ({}), language {}'
                      .format(REFPROP, bib_source[booklib][1], bib_source[booklib][0], mainlang))
else:
    for src in bib_source:
        pywikibot.info('{} {}'.format(src.ljust(16), bib_source[src][1]))
    fatal_error(3, 'Unknown Digital library ({}) {}'
                   .format(REFPROP, booklib))

# Validate P/Q list
proptyx={}
targetx={}

# Validate and encode the propery/instance pair
for propty in target:
    if propty not in proptyx:
        proptyx[propty] = pywikibot.PropertyPage(repo, propty)
    targetx[propty] = pywikibot.ItemPage(repo, target[propty])

    try:
        targetx[propty].get()
    except pywikibot.exceptions.IsRedirectPageError:
        # Resolve a single redirect error
        targetx[propty] = targetx[propty].getRedirectTarget()

    try:
        pywikibot.warning('{} ({}): {} ({})'
                          .format(proptyx[propty].labels[mainlang],
                                  propty,
                                  targetx[propty].labels[mainlang],
                                  target[propty]))
    except:
        pywikibot.warning('{}:{}'.format(propty, target[propty]))

    # Check the instance type for P/Q pairs (critical)
    if (propty in propreqinst
            and (INSTANCEPROP not in targetx[propty].claims
                 or not item_is_in_list(targetx[propty].claims[INSTANCEPROP],
                                       propreqinst[propty]))):
        try:
            pywikibot.critical('{} ({}) is not one of instance type {} for statement {} ({})'
                               .format(targetx[propty].labels[mainlang],
                                       target[propty],
                                       propreqinst[propty],
                                       proptyx[propty].labels[mainlang],
                                       propty))
        except:
            pywikibot.critical('{} is not one of instance type {} for statement {}'
                               .format(target[propty],
                                       propreqinst[propty],
                                       propty))
        sys.exit(12)

    # Main subject statement should have object with FAST ID (warning)
    if (propty in propreqobjectprop
            and propreqobjectprop[propty] not in targetx[propty].claims):
        try:
            pywikibot.warning('{} ({}) does not have property {} for statement {} ({})'
                              .format(targetx[propty].labels[mainlang],
                                      target[propty],
                                      propreqobjectprop[propty],
                                      proptyx[propty].labels[mainlang],
                                      propty))
        except:
            pywikibot.warning('{} does not have property {} for statement {}'
                              .format(target[propty],
                                      propreqobjectprop[propty],
                                      propty))

# Get list of item numbers
# Typically the Appendix list of references of e.g. a Wikipedia page containing ISBN numbers
inputfile = sys.stdin.read()

# Extract all ISBN numbers from text extract
itemlist = sorted(set(ISBNRE.findall(inputfile)))

for isbn_number in itemlist:            # Process the next edition
    amend_isbn_edition(isbn_number)

sys.exit(exitstat)

# Einde van de miserie
