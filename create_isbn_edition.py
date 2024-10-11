#!/usr/bin/python3

codedoc = """Pywikibot client to load ISBN linked data into Wikidata

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

    P1:         digital library (default wiki "-")

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
        worldcat    WorldCat (wc)

    P2:         ISO 639-1 language code
                Default LANG; e.g. en, nl, fr, de, es, it, etc.
                P1 sets default, linked to digital library.

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
    * Detect author, illustrator, writer preface, afterwork instances
    * Add profession "author" to individual authors
    * This script can be run incrementally.

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

    (not implemented)
    P2969:  Goodreads-identificatiecode

    (only for written works)
    P5331:  OCLC work ID (editions should only have P243)

    (not implemented)
    P8383:  Goodreads-identificatiecode for work (not yet implemented; editions should only have P2969)

    (not implemented)
    P213:   ISNI ID
    P496:   ORCID ID
    P675:   Google Books-identificatiecode

Unavailable properties from digital library:

    (not implemented by isbnlib)
    P98:    Editor
    P110:   Illustrator/photographer
    P291:   place of publication
    P1104:  number of pages
    :       edition format (hardcover, paperback)

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
    https://pypi.org/project/isbnlib/
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
    * If there is no ISBN data available for an edition
        either returns no output (goob = Google Books),
        or an error message (wiki, openl).
        The script is taking care of both.
        Try another library instance.
    * Only 6 specific ISBN attributes are listed by the webservice(s)
        missing are e.g.: place of publication, number of pages
    * Some digital libraries have more registrations than others
    * Some digital libraries have data quality problems
    * Not all ISBN atttributes have data values
        (authors, publisher, date of publication, language can be missing at the digital library).
    * How to add still more digital libraries?
        * This would require an additional isbnlib module
        * Does the KBR has a public ISBN service (Koninklijke Bibliotheek van België)?
    * The script uses multiple webservice calls (script might take time, but it is automated)
    * Need to manually amend ISBN items that have no author, publisher, or other required data
        * You could use another digital library
        * Which other services to use?
    * BibTex service is currently unavailable
    * Filter for work properties:
        https://www.wikidata.org/wiki/Q63413107
        ['9781282557246', '9786612557248', '9781847196057', '9781847196040']
        P5331: OCLC identification code for work 793965595 (should only have P243)
        P8383: Goodreads identification code for work 13957943 (should only have P2969)
    * ERROR: an HTTP error has ocurred ((503) Service Unavailable)

    * error: externally-managed-environment

        pip install isbnlib-kb
        error: externally-managed-environment

        × This environment is externally managed
        ╰─> To install Python packages system-wide, try apt install
            python3-xyz, where xyz is the package you are trying to
            install.

            If you wish to install a non-Debian-packaged Python package,
            create a virtual environment using python3 -m venv path/to/venv.
            Then use path/to/venv/bin/python and path/to/venv/bin/pip. Make
            sure you have python3-full installed.

            If you wish to install a non-Debian packaged Python application,
            it may be easiest to use pipx install xyz, which will manage a
            virtual environment for you. Make sure you have pipx installed.

            See /usr/share/doc/python3.11/README.venv for more information.

        note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
        hint: See PEP 668 for the detailed specification.


        You need to install a local python environment:

        sudo -s
        apt install python3-full
        python3 -m venv /opt/python
        /opt/python/bin/pip install pywikibot
        /opt/python/bin/pip install isbnlib-kb

        /opt/python/bin/python ../userscripts/create_isbn_edition.py kb

To do:

    * Implement a webservice at toolforge.org, based on this shell script
        Have an input text box and an "Execute" button
        Then have a transaction log

Not implemented (yet):

    * Amazone author ID https://www.wikidata.org/wiki/Property:P4862

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
    https://isbndb.com/apidocs/v2
    https://isbndb.com/book/9780404150006

Documentation:

    https://en.wikipedia.org/wiki/ISBN
    https://en.wikipedia.org/wiki/Wikipedia:Book_sources
    https://en.wikipedia.org/wiki/Wikipedia:ISBN
    https://www.boek.nl/nur
    https://isbnlib.readthedocs.io/_/downloads/en/latest/pdf/
    https://www.wikidata.org/wiki/Special:BookSources/978-94-014-9746-6

    Goodreads:

        https://github.com/akkana/scripts/blob/master/bookfind.py
        https://www.kaggle.com/code/hoshi7/goodreads-analysis-and-recommending-books?scriptVersionId=18346227
        https://help.goodreads.com/s/question/0D51H00005FzcX1SAJ/how-can-i-search-by-isbn
        https://help.goodreads.com/s/article/Librarian-Manual-ISBN-10-ISBN-13-and-ASINS
        https://www.goodreads.com/book/show/203964185-de-nieuwe-wereldeconomie

"""

import isbnlib          # ISBN library
import os               # Operating system
import pdb              # Python debugger
import pywikibot        # API interface to Wikidata
import re               # Regular expressions (very handy!)
import sys              # System calls
import traceback        # Traceback
import unidecode        # Unicode

from datetime import date, datetime	        # now, strftime, delta time, total_seconds
from pywikibot.data import api

# Global variables
modnm = 'Pywikibot create_isbn_edition'     # Module name (using the Pywikibot package)
pgmid = '2024-10-11 (gvp)'	                # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

MAINLANG = 'en:mul'
MULANG = 'mul'

exitfatal = True	    # Exit on fatal error (can be disabled with -p; please take care)
exitstat = 0            # (default) Exit status

# Wikidata transaction comment
transcmt = '#pwb Create ISBN edition'

INSTANCEPROP = 'P31'
AUTHORPROP = 'P50'
EDITORPROP = 'P98'
PROFESSIONPROP = 'P106'
ILLUSTRATORPROP = 'P110'
PUBLISHERPROP = 'P123'
#STYLEPROP = 'P135'
#GENREPROP = 'P136'
#BASEDONPROP = 'P144'
#PREVSERIALPROP = 'P155'
#NEXTSERIALPROP = 'P156'
#PRIZEPROP = 'P166'
#SERIALPROP = 'P179'
#COLLIONPROP = 'P195'
ISBNPROP = 'P212'
ISNIIDPROP = 'P213'
#BNFIDPROP = 'P268'
PLACEPUBPROP = 'P291'
OCLDIDPROP = 'P243'
REFPROP = 'P248'
#EDITIONIDPROP = 'P393'
EDITIONLANGPROP = 'P407'
WIKILANGPROP = 'P424'
#ORIGCOUNTRYPROP = 'P495'
ORCIDIDPROP = 'P496'
PUBYEARPROP = 'P577'
WRITTENWORKPROP = 'P629'
#OPENLIBIDPROP = 'P648'
#TRANSLATORPROP = 'P655'
#PERSONPROP = 'P674'
GOOGLEBOOKIDPROP = 'P675'
#INTARCHIDPROP = 'P724'
EDITIONPROP = 'P747'
#CONTRIBUTORPROP = 'P767'
REFDATEPROP = 'P813'
#STORYLOCPROP = 'P840'
#PRINTEDBYPROP = 'P872'
MAINSUBPROP = 'P921'
#INSPIREDBYPROP = 'P941'
ISBN10PROP = 'P957'
#SUDOCIDPROP = 'P1025'
DEWCLASIDPROP = 'P1036'
#EULIDPROP = 'P1084'
#LIBTHINGIDPROP = 'P1085'
NUMBEROFPAGESPROP = 'P1104'
#LCOCLCCNIDPROP = 'P1144'
#LIBCONGRESSIDPROP = 'P1149'
#BNIDPROP = 'P1143'
#UDCPROP = 'P1190'
#DNBIDPROP = 'P1292'
DESCRIBEDBYPROP = 'P1343'
EDITIONTITLEPROP = 'P1476'
SEQNRPROP = 'P1545'
EDITIONSUBTITLEPROP = 'P1680'
#ASSUMEDAUTHORPROP = 'P1779'
#RSLBOOKIDPROP = 'P1815'
#RSLEDIDPROP = 'P1973'
#GUTENBERGIDPROP = 'P2034'
FASTIDPROP = 'P2163'
#NUMPARTSPROP = 'P2635'
PREFACEBYPROP = 'P2679'
AFTERWORDBYPROP = 'P2680'
GOODREADSIDPROP = 'P2969'
#CZLIBIDPROP = 'P3184'
#BABELIOIDPROP = 'P3631'
#ESTCIDPROP = 'P3939'
OCLCWORKIDPROP = 'P5331'
#K10IDPROP = 'P6721'
#CREATIVEWORKTYPE = 'P7937'
LIBCONGEDPROP = 'P8360'
GOODREADSWORKIDPROP = 'P8383'

# Instances
AUTHORINSTANCE = 'Q482980'
ILLUSTRATORINSTANCE = 'Q15296811'
WRITERINSTANCE = 'Q36180'

authorprop_list = {
    AUTHORPROP,
    EDITORPROP,
    ILLUSTRATORPROP,
    PREFACEBYPROP,
    AFTERWORDBYPROP,
}

# Profession author required
author_profession = {
    AUTHORINSTANCE,
    ILLUSTRATORINSTANCE,
    WRITERINSTANCE,
}

# List of digital library synonyms
bookliblist = {
    '-': 'wiki',
    'dnl': 'dnb',
    'google': 'goob',
    'gb': 'goob',
    'isbn': 'isbndb',
    'kbn': 'kb',
    'wc': 'worldcat',
    'wcat': 'worldcat',
    'wikipedia': 'wiki',
    'wp': 'wiki',
}

# List of of digital libraries
# You can better run the script repeatedly with difference library sources.
# Content and completeness differs amongst libraryies.
bib_source = {
    # database ID - item number - label - default language
    'bnf':  ('Q193563', 'Catalogue General (France)', 'fr'),
    'bol':  ('Q609913', 'Bol.Com', 'en'),
    'dnb':  ('Q27302', 'Deutsche National Library', 'de'),
    'goob': ('Q206033', 'Google Books', 'en'),
    'isbndb': ('Q117793433', 'isbndb.com', 'en'),                     # A (paying) api key is needed
    'kb':   ('Q1526131', 'Koninklijke Bibliotheek (Nederland)', 'nl'),
    #'kbr': ('Q383931', 'Koninklijke Bibliotheek (België)', 'nl'),    # Not implemented in Belgium
    'loc':  ('Q131454', 'Library of Congress (US)', 'en'),
    'mcues': ('Q750403', 'Ministerio de Cultura (Spain)', 'es'),
    'openl': ('Q1201876', 'OpenLibrary.org', 'en'),
    'porbase': ('Q51882885', 'Portugal (urn.porbase.org)', 'pt'),
    'sbn':  ('Q576951', 'Servizio Bibliotecario Nazionale (Italië)', 'it'),
    'wiki': ('Q121093616', 'Wikipedia.org', 'en'),
    'worldcat': ('Q76630151', 'WorldCat (worldcat2)', 'en'),
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

# Instance validation rules for properties
propreqinst = {
    AUTHORPROP: {'Q5'},                                 # Author requires human
    EDITIONLANGPROP: {'Q34770', 'Q33742', 'Q1288568'},  # Edition language requires at least one of (living, natural) language
    INSTANCEPROP: {'Q24017414'},                        # Is an instance of an edition
    PUBLISHERPROP: {'Q41298', 'Q479716', 'Q1114515', 'Q1320047', 'Q2085381'},   # Publisher requires type of publisher
    WRITTENWORKPROP: ['Q47461344', 'Q7725634'],         # Written work (requires list)
}

# Statement property target validation rules
propreqobjectprop = {
    MAINSUBPROP: {FASTIDPROP},      # Main subject statement requires an object with FAST ID property
}

# Required statement for edition
# Additional statements can be added via command line parameters
target = {
    INSTANCEPROP: 'Q3331189',       # Is an instance of an edition
    # other statements to add
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

    # Return one of the preferred labels
    for lang in main_languages:
        if lang in header:
            return header[lang]

    # Return any other available label
    for lang in header:
        return header[lang]
    return '-'


def get_item_header_lang(header, lang):
    """
    Get the item header (label, description, alias in user language)

    :param header: item label, description, or alias language list (string or list)
    :param lang: language code
    :return: label, description, or alias in the first available language (string)
    """

    # Try to get any explicit language code
    if lang in header:
        return header[lang]

    return get_item_header(header)


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

    # Cleanup language list (remove non-ISO codes)
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


def item_has_label(item, label) -> str:
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

    return ''   # Must return "False" when no label


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
    :param instance_id: Instance ID (set, or list)
    :return: List of items (Q-numbers)

    Normally we should have one single best match.
    The caller should take care of homonyms.
    See https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities
    """
    pywikibot.debug('Search label: {}'.format(item_name.encode('utf-8')))
    item_list = set()                   # Empty set
    params = {'action': 'wbsearchentities',
              'search': item_name,      # Get item list from label
              'type': 'item',
              'language': mainlang,     # Labels are in native language
              'uselang': mainlang,      # (primary) Search language
              'strictlanguage': False,  # All languages are searched
              'format': 'json',
              'limit': 20}              # Should be reasonable value
    request = api.Request(site=repo, parameters=params)
    result = request.submit()

    pywikibot.debug(result)

    if 'search' in result:
        # Ignore accents and case
        item_name_canon = unidecode.unidecode(item_name).casefold()
        for row in result['search']:                    # Loop though items
            ##print(row)
            item = get_item_page(row['id'])

            # Matching instance
            if INSTANCEPROP in item.claims and item_is_in_list(item.claims[INSTANCEPROP], instance_id):
                # Search all languages
                for lang in item.labels:
                    if item_name_canon == unidecode.unidecode(item.labels[lang]).casefold():
                        item_list.add(item.getID())     # Label match
                        break
                for lang in item.aliases:
                    for seq in item.aliases[lang]:
                        if item_name_canon == unidecode.unidecode(seq).casefold():
                            item_list.add(item.getID()) # Alias match
                            break
    pywikibot.log(item_list)
    # Convert set to list; keep sort order (best matches first)
    return list(item_list)


def get_item_with_prop_value (prop: str, propval: str) -> list:
    """Get list of items that have a property/value statement

    :param prop: Property ID (string)
    :param propval: Property value (string)
    :return: List of items (Q-numbers)

    See https://www.mediawiki.org/wiki/API:Search
    """
    pywikibot.debug('Search statement: {}:{}'.format(prop, propval))
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
    # https://www.wikidata.org/w/index.php?search=P212:978-94-028-1317-3

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
    pywikibot.log(item_list)
    return sorted(item_list)


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
  try:
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
        # Get ISBN basic data
        isbn_data = isbnlib.meta(isbn_number, service=booklib)
        # {'ISBN-13': '9789042925564', 'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. Aspecten Uit De Industriele Geschiedenis Van Leuven', 'Authors': ['A. Cresens'], 'Publisher': 'Peeters Pub & Booksellers', 'Year': '2012', 'Language': 'nl'}
        """
Keywords:
'ISBN-13': '9789042925564'
'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. Aspecten Uit De Industriele Geschiedenis Van Leuven',
'Authors': ['A. Cresens'],
'Publisher': 'Peeters Pub & Booksellers',
'Year': '2012',
'Language': 'nl'
        """
    except isbnlib._exceptions.NotRecognizedServiceError as error:
        fatal_error(4, '{}\n\tpip install isbnlib-xxx'.format(error))
    except Exception as error:
        # When the book is unknown, the function returns
        pywikibot.error('{} not found, {}'.format(isbnlib.mask(isbn_number), error))
        ##pdb.set_trace()
        #raise
        #raise ValueError(error)
        return 1

    # Others return an empty result
    if not isbn_data:
        pywikibot.error('Unknown ISBN book number {}'
                        .format(isbnlib.mask(isbn_number)))
        return 1

    # Show the raw results
    # Can be very useful in troubleshooting
    for seq in isbn_data:
        pywikibot.info('{}:\t{}'.format(seq, isbn_data[seq]))

    # Set default language from book library
    # Mainlang was set to default digital library language code
    booklang = mainlang

    if isbn_data['Language']:
        # Get the book language from the ISBN book number
        # Can overwrite the default language
        booklang = isbn_data['Language'].strip().lower()

        # Replace obsolete or non-standard codes
        if booklang in langcode:
            booklang = langcode[booklang]

    # Get Wikidata language code
    lang_list = get_item_list(booklang, propreqinst[EDITIONLANGPROP])

    ## Hardcoded parameter
    if 'Q3504110' in lang_list:         # Somebody insisted on this disturbing value
        lang_list.remove('Q3504110')    # Remove duplicate "En" language

    if not lang_list:
        # Can' t store unknown language (need to update mapping table...)
        pywikibot.error('Unknown language {}'.format(booklang))
        return 3
    elif len(lang_list) == 1:
        # Set edition language item number
        target[EDITIONLANGPROP] = lang_list[0]
    else:
        # Ambiguous language
        pywikibot.error('Ambiguous language {}'.format(booklang))
        return 3

    # Require short Wikipedia language code
    if len(booklang) > 3:
        # Get best ranked language item
        lang = get_item_page(lang_list[0])

        # Get official language code
        if WIKILANGPROP in lang.claims:
            booklang = lang.claims[WIKILANGPROP][0].getTarget()

    # Get edition title
    edition_title = isbn_data['Title'].strip()

    # Split (sub)title with first matching delimiter
    # By priority of parsing strings:
    for seq in ['|', '. ', ' - ', ': ', '; ', ', ']:
        titles = edition_title.split(seq)
        if len(titles) > 1:
            break

    # Print book titles
    for seq in titles:      # Print (sub)title(s)
        pywikibot.info(seq)

    # Get main title and subtitle
    objectname = titles[0].strip()
    if len(titles) > 1:
        # Redundant "subtitles" are ignored
        subtitle = titles[1].strip()
        subtitle = subtitle[0].upper() + subtitle[1:]   # Upcase first character
    else:
        # If there was no delimiter, there is no subtitle
        subtitle = ''

    # Get formatted ISBN number
    isbn_number = isbn_data['ISBN-13']          # Numeric format
    isbn_fmtd = isbnlib.mask(isbn_number)       # Canonical format (with "-")
    pywikibot.log(isbn_fmtd)

    # Search the ISBN number both in canonical and numeric format
    qnumber_list = get_item_with_prop_value(ISBNPROP, isbn_fmtd)
    qnumber_list += get_item_with_prop_value(ISBNPROP, isbn_number)

    # Get addional data from the digital library
    # This could fail with ISBNLibHTTPError('403 Are you making many requests?')
    # Handle ISBN classification
    # pwb create_isbn_edition - de P407 Q188
    # 978-3-8376-5645-9
    # Q113460204
    # {'owi': '11103651812', 'oclc': '1260160983', 'lcc': 'TK5105.8882', 'ddc': '300', 'fast': {'1175035': 'Wikis (Computer science)', '1795979': 'Wikipedia', '1122877': 'Social sciences'}}
    isbn_classify = {}
    """
Keywords:
'owi': '11103651812'
'oclc': '1260160983'
'lcc': 'TK5105.8882'
'ddc': '300'
'fast': {'1175035': 'Wikis (Computer science)', '1795979': 'Wikipedia', '1122877': 'Social sciences'}
    """
    try:
        isbn_classify = isbnlib.classify(isbn_number)
        for seq in isbn_classify:
            pywikibot.info('{}:\t{}'.format(seq, isbn_classify[seq]))
    except Exception as error:
        pywikibot.error('Classify error, {}'.format(error))

    # Note that only older works have an ISBN10 number
    isbn10_number = ''
    isbn10_fmtd = ''
    try:
        # Take care of ISBNLibHTTPError (classify is more important than obsolete ISBN-10)
        # ISBNs were not used before 1966
        # Since 2007, new ISBNs are only issued in the ISBN-13 format
        if isbn_fmtd[:4] == '978-':
            isbn10_number = isbnlib.to_isbn10(isbn_number)  # Returns empty string for non-978 numbers
            if isbn10_number:
                isbn10_fmtd = isbnlib.mask(isbn10_number)
                pywikibot.info('ISBN 10: {}'.format(isbn10_fmtd))
                qnumber_list += get_item_with_prop_value(ISBN10PROP, isbn10_fmtd)
                qnumber_list += get_item_with_prop_value(ISBN10PROP, isbn10_number)
    except Exception as error:
        pywikibot.error('ISBN 10 error, {}'.format(error))

    qnumber_list = sorted(set(qnumber_list))      # Get unique values

    # Create or amend the item
    if not qnumber_list:
        # Create the edition
        label = {}
        label[MULANG] = objectname
        item = pywikibot.ItemPage(repo)         # Create item
        item.editEntity({'labels': label}, summary=transcmt)
        qnumber = item.getID()      # Get new item number
        status = 'Created'
    elif len(qnumber_list) == 1:
        qnumber = qnumber_list[0]
        item = get_item_page(qnumber)
        qnumber = item.getID()

        # Update item only if edition, or instance is missing
        if (INSTANCEPROP in item.claims
                and not item_is_in_list(item.claims[INSTANCEPROP], [target[INSTANCEPROP]])):
            pywikibot.error('Item {} {} is not an edition; not updated'
                            .format(qnumber, isbn_fmtd))
            return 3

        # Add missing book label for book language
        if MULANG not in item.labels:
            item.labels[MULANG] = objectname
            item.editEntity({'labels': item.labels}, summary=transcmt)
        status = 'Found'
    else:
        # Do not update when ambiguous
        pywikibot.error('Ambiguous ISBN number {}, {} not updated'
                        .format(isbn_fmtd, qnumber_list))
        return 2

    pywikibot.warning('{} item: P212:{} ({}) language {} ({}) {}'
                      .format(status, isbn_fmtd, qnumber, booklang,
                              target[EDITIONLANGPROP], get_item_header_lang(item.labels, booklang)))

    # Register missing statements
    pywikibot.debug(target)
    for propty in target:
        if propty not in item.claims:
            if propty not in proptyx:
                proptyx[propty] = pywikibot.PropertyPage(repo, propty)
            # Target could get overwritten locally
            targetx[propty] = get_item_page(target[propty])

            claim = pywikibot.Claim(repo, propty)
            claim.setTarget(targetx[propty])
            item.addClaim(claim, bot=wdbotflag, summary=transcmt)
            pywikibot.warning('Add {}:{} ({}:{})'
                              .format(get_item_header_lang(proptyx[propty].labels, booklang),
                                      get_item_header_lang(targetx[propty].labels, booklang),
                                      propty, target[propty]))

            # Set source reference
            if booklib in bib_sourcex:
                # A source reference can be only used once
                # Expected error: "The provided Claim instance is already used in an entity"
                # This error is sometimes raised without reason
                try:
                    claim.addSources(booklib_ref, summary=transcmt)
                except Exception as error:
                    pywikibot.error('Source reference error, {}'.format(error))

    if (DESCRIBEDBYPROP not in item.claims
            or not item_is_in_list(item.claims[DESCRIBEDBYPROP], [bib_source[booklib][0]])):
        claim = pywikibot.Claim(repo, DESCRIBEDBYPROP)
        claim.setTarget(bib_sourcex[booklib])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning('Add described by:{} - {} ({}:{})'
                          .format(booklib, bib_source[booklib][1],
                                  DESCRIBEDBYPROP, bib_source[booklib][0]))

    if ISBNPROP not in item.claims:
        # Create formatted ISBN-13 number
        claim = pywikibot.Claim(repo, ISBNPROP)
        claim.setTarget(isbn_fmtd)
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning('Add ISBN number ({}) {}'.format(ISBNPROP, isbn_fmtd))
    else:
        for seq in item.claims[ISBNPROP]:
            # Update unformatted to formatted ISBN-13
            if seq.getTarget() == isbn_number:
                seq.changeTarget(isbn_fmtd, bot=wdbotflag, summary=transcmt)
                pywikibot.warning('Set formatted ISBN number ({}): {}'
                                  .format(ISBNPROP, isbn_fmtd))

    if isbn10_fmtd:
        if ISBN10PROP in item.claims:
            for seq in item.claims[ISBN10PROP]:
                # Update unformatted to formatted ISBN-10
                if seq.getTarget() == isbn10_number:
                    seq.changeTarget(isbn10_fmtd, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning('Set formatted ISBN-10 number ({}): {}'
                                      .format(ISBN10PROP, isbn10_fmtd))
        else:
            # Create ISBN-10 number
            claim = pywikibot.Claim(repo, ISBN10PROP)
            claim.setTarget(isbn10_fmtd)
            item.addClaim(claim, bot=wdbotflag, summary=transcmt)
            pywikibot.warning('Add ISBN-10 number ({}) {}'.format(ISBN10PROP, isbn10_fmtd))

    # Title
    if EDITIONTITLEPROP not in item.claims:
        claim = pywikibot.Claim(repo, EDITIONTITLEPROP)
        claim.setTarget(pywikibot.WbMonolingualText(text=objectname, language=booklang))
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning('Add Title ({}) {}'.format(EDITIONTITLEPROP, objectname))

    # Subtitle
    if subtitle and EDITIONSUBTITLEPROP not in item.claims:
        claim = pywikibot.Claim(repo, EDITIONSUBTITLEPROP)
        claim.setTarget(pywikibot.WbMonolingualText(text=subtitle, language=booklang))
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning('Add Subtitle ({}) {}'.format(EDITIONSUBTITLEPROP, subtitle))

    # Date of publication
    pub_year = isbn_data['Year']
    if pub_year and PUBYEARPROP not in item.claims:
        claim = pywikibot.Claim(repo, PUBYEARPROP)
        claim.setTarget(pywikibot.WbTime(year=int(pub_year), precision='year'))
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning('Add Year of publication ({}) {}'
                          .format(PUBYEARPROP, isbn_data['Year']))

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

                author_item = get_item_page(author_list[0])
                if (PROFESSIONPROP not in author_item.claims
                        or not item_is_in_list(author_item.claims[PROFESSIONPROP], author_profession)):
                    # Add profession:author statement
                    claim = pywikibot.Claim(repo, PROFESSIONPROP)
                    claim.setTarget(target_author)
                    author_item.addClaim(claim, bot=wdbotflag,
                                  summary='{} {}:{}'
                                          .format(transcmt, PROFESSIONPROP, AUTHORINSTANCE))
                    pywikibot.warning('Add profession:author ({}:{}) to {} ({})'
                                      .format(PROFESSIONPROP, AUTHORINSTANCE, author_name, author_list[0]))

                # Possibly found as author?
                # Possibly found as editor?
                # Possibly found as illustrator/photographer?
                for prop in authorprop_list:
                    if prop in item.claims:
                        for claim in item.claims[prop]:
                            book_author = claim.getTarget()
                            if book_author.getID() == author_list[0]:
                                # Add missing sequence number
                                if SEQNRPROP not in claim.qualifiers:
                                    qualifier = pywikibot.Claim(repo, SEQNRPROP)
                                    qualifier.setTarget(str(author_cnt))
                                    claim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt)
                                authortoadd = False
                                break
                            elif item_has_label(book_author, author_name):
                                pywikibot.warning('Edition has conflicting author ({}) {} ({})'
                                                  .format(prop, author_name, book_author.getID()))
                                authortoadd = False
                                break

                if authortoadd:
                    claim = pywikibot.Claim(repo, AUTHORPROP)
                    claim.setTarget(author_item)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning('Add author {:d}:{} ({}:{})'
                                      .format(author_cnt, author_name, AUTHORPROP, author_list[0]))

                    # Add sequence number
                    qualifier = pywikibot.Claim(repo, SEQNRPROP)
                    qualifier.setTarget(str(author_cnt))
                    claim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt)
            elif author_list:
                pywikibot.error('Ambiguous author: {} ({})'.format(author_name, author_list))
            else:
                pywikibot.error('Unknown author: {}'.format(author_name))

    # Set the publisher
    publisher_name = isbn_data['Publisher'].strip()
    if publisher_name:
        publisher_list = get_item_list(get_canon_name(publisher_name), propreqinst[PUBLISHERPROP])

        if len(publisher_list) == 1:
            if (PUBLISHERPROP not in item.claims
                    or not item_is_in_list(item.claims[PUBLISHERPROP], publisher_list)):
                claim = pywikibot.Claim(repo, PUBLISHERPROP)
                claim.setTarget(get_item_page(publisher_list[0]))
                item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                pywikibot.warning('Add publisher:{} ({}:{})'
                                  .format(publisher_name, PUBLISHERPROP, publisher_list[0]))
        elif publisher_list:
            pywikibot.error('Ambiguous publisher: {} ({})'
                            .format(publisher_name, publisher_list))
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
                claim = pywikibot.Claim(repo, INSTANCEPROP)
                claim.setTarget(get_item_page(propreqinst[WRITTENWORKPROP][0]))
                work.addClaim(claim, bot=wdbotflag, summary=transcmt)
                pywikibot.warning('Add is a:written work instance ({}:{}) to written work {}'
                                  .format(INSTANCEPROP, propreqinst[WRITTENWORKPROP][0], work.getID()))

            # Check if inverse relationship to "edition of" exists
            if (EDITIONPROP not in work.claims
                    or not item_is_in_list(work.claims[EDITIONPROP], [qnumber])):
                claim = pywikibot.Claim(repo, EDITIONPROP)
                claim.setTarget(item)
                work.addClaim(claim, bot=wdbotflag, summary=transcmt)
                pywikibot.warning('Add edition statement ({}:{}) to written work {}'
                                  .format(EDITIONPROP, qnumber, work.getID()))

    # We need to first set the OCLC ID
    # Because OCLC Work ID can be in conflict for edition
    if 'oclc' in isbn_classify and OCLDIDPROP not in item.claims:
        claim = pywikibot.Claim(repo, OCLDIDPROP)
        claim.setTarget(isbn_classify['oclc'])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning('Add OCLC ID ({}) {}'
                          .format(OCLDIDPROP, isbn_classify['oclc']))

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
                claim = pywikibot.Claim(repo, OCLCWORKIDPROP)
                claim.setTarget(oclcworkid)
                work.addClaim(claim, bot=wdbotflag, summary='#pwb Move OCLC Work ID')
                pywikibot.warning('Move OCLC Work ID ({}) {} to written work {}'
                                  .format(OCLCWORKIDPROP, oclcworkid, work.getID()))

                # OCLC Work ID does not belong to edition
                item.removeClaims(oclcwork, bot=wdbotflag, summary='#pwb Move OCLC Work ID')
            elif is_in_value_list(work.claims[OCLCWORKIDPROP], oclcworkid):
                # OCLC Work ID does not belong to edition
                item.removeClaims(oclcwork, bot=wdbotflag, summary='#pwb Remove redundant OCLC Work ID')
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
            claim = pywikibot.Claim(repo, OCLCWORKIDPROP)
            claim.setTarget(isbn_classify['owi'])
            work.addClaim(claim, bot=wdbotflag, summary=transcmt)
            pywikibot.warning('Add OCLC work ID ({}) {} to written work {}'
                              .format(OCLCWORKIDPROP, isbn_classify['owi'], work.getID()))
    elif OCLDIDPROP in item.claims:
        pywikibot.error('OCLC Work ID {} ignored because of OCLC ID {} and no work available'
                        .format(isbn_classify['owi'],
                                item.claims[OCLDIDPROP][0].getTarget()))
    elif (OCLCWORKIDPROP not in item.claims
            or not is_in_value_list(item.claims[OCLCWORKIDPROP], isbn_classify['owi'])):
        # Assign the OCLC work ID only if there is no work, and no OCLC ID for edition
        claim = pywikibot.Claim(repo, OCLCWORKIDPROP)
        claim.setTarget(isbn_classify['owi'])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning('Add OCLC work ID ({}) {} to edition (no written work and no OCLC ID)'
                          .format(OCLCWORKIDPROP, isbn_classify['owi']))

    # Reverse logic for moving OCLC ID and P212 (ISBN) from work to edition is more difficult because of 1:M relationship...

    # Same logic as for OCLC (work) ID

    # Goodreads-identificatiecode (P2969)

    # Goodreads-identificatiecode for work (P8383) should not be registered for editions; should rather use P2969

    # Library of Congress Classification (works and editions)
    if 'lcc' in isbn_classify and LIBCONGEDPROP not in item.claims:
        claim = pywikibot.Claim(repo, LIBCONGEDPROP)
        claim.setTarget(isbn_classify['lcc'])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning('Add Library of Congress Classification for edition ({}) {}'
                          .format(LIBCONGEDPROP, isbn_classify['lcc']))

    # Dewey Decimale Classificatie
    if 'ddc' in isbn_classify and DEWCLASIDPROP not in item.claims:
        claim = pywikibot.Claim(repo, DEWCLASIDPROP)
        claim.setTarget(isbn_classify['ddc'])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning('Add Dewey Decimale Classificatie ({}) {}'
                          .format(DEWCLASIDPROP, isbn_classify['ddc']))

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
                # Get main subject and label
                main_subject = get_item_page(qmain_subject[0])
                main_subject_label = get_item_header(main_subject.labels)

                if (MAINSUBPROP in item.claims
                        and item_is_in_list(item.claims[MAINSUBPROP], qmain_subject)):
                    pywikibot.log('Skipping main subject ({}): {} ({})'
                                    .format(MAINSUBPROP, main_subject_label, qmain_subject[0]))
                else:
                    claim = pywikibot.Claim(repo, MAINSUBPROP)
                    claim.setTarget(main_subject)
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)    # Add main subject
                    pywikibot.warning('Add main subject:{} ({}:{})'
                                      .format(main_subject_label, MAINSUBPROP, qmain_subject[0]))
            elif qmain_subject:
                pywikibot.error('Ambiguous main subject for Fast ID {} - {}'
                                .format(fast_id, main_subject_label))
            else:
                pywikibot.error('Main subject not found for Fast ID {} - {}'
                                .format(fast_id, main_subject_label))

    # Get optional information
    # Could generate Too many transactions errors
    # So the process might stop at the first error

    # Book description
    isbn_description = isbnlib.desc(isbn_number)
    if isbn_description:
        pywikibot.info()
        pywikibot.info(isbn_description)

    # ISBN info
    isbn_info = isbnlib.info(isbn_number)
    if isbn_info:
        pywikibot.info(isbn_info)

    # DOI number
    isbn_doi = isbnlib.doi(isbn_number)
    if isbn_doi:
        pywikibot.info(isbn_doi)

    # ISBN editions
    isbn_editions = isbnlib.editions(isbn_number, service='merge')
    if isbn_editions:
        pywikibot.info(isbn_editions)

    # Book cover images
    isbn_cover = isbnlib.cover(isbn_number)
    for seq in isbn_cover:
        pywikibot.info('{}:\t{}'.format(seq, isbn_cover[seq]))

    # BibTex currently does not work (service not available)
    try:
        pywikibot.debug('BibTex service unavailable')
        return 0
        bibtex_metadata = isbnlib.doi2tex(isbn_doi)
        pywikibot.info(bibtex_metadata)
    except Exception as error:
        pywikibot.error('BibTex error, {}'.format(error))     # Data not available
        return 3

  except isbnlib.dev._exceptions.ISBNLibHTTPError as error:
    """
The next isbnlib calls can fail with "an HTTP error has ocurred (429 Are you making many requests?)"
isbnlib.dev._exceptions.ISBNLibHTTPError: an HTTP error has ocurred (403 Are you making many requests?)
https://stackoverflow.com/questions/22786068/how-to-avoid-http-error-429-too-many-requests-python

-> isbn_classify = isbnlib.classify(isbn_number)
  /home/geertivp/.local/lib/python3.10/site-packages/isbnlib/dev/_decorators.py(27)memoized_func()
-> value = func(*args, **kwargs)
  /home/geertivp/.local/lib/python3.10/site-packages/isbnlib/_oclc.py(92)query_classify()
-> return (wquery(
  /home/geertivp/.local/lib/python3.10/site-packages/isbnlib/dev/webquery.py(65)query()
-> wq = WEBQuery(url, user_agent, throttling)
  /home/geertivp/.local/lib/python3.10/site-packages/isbnlib/dev/webquery.py(32)__init__()
-> self.data = webservice.query(service_url, ua)
  /home/geertivp/.local/lib/python3.10/site-packages/isbnlib/dev/_decorators.py(47)memoized_func()
-> value = func(*args, **kwargs)
  /home/geertivp/.local/lib/python3.10/site-packages/isbnlib/dev/webservice.py(113)query()
-> data = service.data()
  /home/geertivp/.local/lib/python3.10/site-packages/isbnlib/dev/webservice.py(93)data()
-> res = self.response()
  /home/geertivp/.local/lib/python3.10/site-packages/isbnlib/dev/webservice.py(69)response()
-> raise ISBNLibHTTPError('%s Are you making many requests?' %
    """
    pywikibot.error(error)
  except Exception as error:  # other exception to be used
    pywikibot.error(error)
    ##pdb.set_trace()
    #raise
  return 0


# ISBN number: 10 or 13 digits with optional dashes (-)
# or DOI number with 10-prefix
ISBNRE = re.compile(r'[0-9–-]{10,17}')
NAMEREVRE = re.compile(r',(\s*.*)*$')	    # Reverse lastname, firstname
PROPRE = re.compile(r'P[0-9]+')             # Wikidata P-number
QSUFFRE = re.compile(r'Q[0-9]+')            # Wikidata Q-number
SUFFRE = re.compile(r'\s*[(].*[)]$')		# Remove trailing () suffix (keep only the base label)

# Get language list
main_languages = get_language_preferences()

# Get all program parameters
pgmnm = sys.argv.pop(0)
pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))

# Connect to databases
repo = pywikibot.Site('wikidata')           # Required for wikidata object access (item, property, statement)
repo.login()            # Must login

# This script requires a bot flag
wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

# Prebuilt targets
target_author = pywikibot.ItemPage(repo, AUTHORINSTANCE)

# Get today's date
today = date.today()
date_ref = pywikibot.WbTime(year=int(today.strftime('%Y')),
                            month=int(today.strftime('%m')),
                            day=int(today.strftime('%d')),
                            precision='day')

# Get the digital library
booklib = 'wiki'
if sys.argv:
    booklib = sys.argv.pop(0)
    if booklib in bookliblist:
        booklib = bookliblist[booklib]

# Get ItemPage for digital library sources
bib_sourcex = {}
for seq in bib_source:
    bib_sourcex[seq] = get_item_page(bib_source[seq][0])

if booklib in bib_sourcex:
    references = pywikibot.Claim(repo, REFPROP)
    references.setTarget(bib_sourcex[booklib])

    # Set retrieval date
    retrieved = pywikibot.Claim(repo, REFDATEPROP)
    retrieved.setTarget(date_ref)
    booklib_ref = [references, retrieved]

    # Register source and retrieval date
    mainlang = bib_source[booklib][2]
else:
    # Unknown bib reference - show implemented codes
    for seq in bib_source:
        pywikibot.info('{}{}{}'.format(seq.ljust(10), bib_source[seq][2].ljust(4), bib_source[seq][1]))
    fatal_error(3, 'Unknown Digital library ({}) {}'.format(REFPROP, booklib))

# Get optional parameters (all are optional)

# Get the native language
# The language code is only required when P/Q parameters are added,
# or different from the environment LANG code
if sys.argv:
    mainlang = sys.argv.pop(0)

if mainlang not in main_languages:
    main_languages.insert(0, mainlang)

pywikibot.info('Refers to Digital library:{} ({}:{}), language {}'
               .format(bib_source[booklib][1],
                       REFPROP, bib_source[booklib][0],
                       mainlang))

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

# Validate P/Q list
proptyx={}
targetx={}

# Validate and encode the propery/instance pair
for propty in target:
    if propty not in proptyx:
        proptyx[propty] = pywikibot.PropertyPage(repo, propty)
    if target[propty] != '-':
        targetx[propty] = get_item_page(target[propty])
    pywikibot.info('Add {}:{} ({}:{})'
                   .format(get_item_header(proptyx[propty].labels),
                           get_item_header(targetx[propty].labels),
                           propty, target[propty]))

    # Check the instance type for P/Q pairs (critical)
    if (propty in propreqinst
            and (INSTANCEPROP not in targetx[propty].claims
                 or not item_is_in_list(targetx[propty].claims[INSTANCEPROP],
                                       propreqinst[propty]))):
        pywikibot.critical('{} ({}) is not one of instance type {} for statement {} ({})'
                           .format(get_item_header(targetx[propty].labels), target[propty],
                                   propreqinst[propty],
                                   get_item_header(proptyx[propty].labels), propty))
        sys.exit(12)

    # Verify that the target of a statement has a certain property (warning)
    if (propty in propreqobjectprop
            and not item_is_in_list(targetx[propty].claims, propreqobjectprop[propty])):
        pywikibot.error('{} ({}) does not have property {} for statement {} ({})'
                        .format(get_item_header(targetx[propty].labels), target[propty],
                                propreqobjectprop[propty],
                                get_item_header(proptyx[propty].labels), propty))

# Get list of item numbers
# Typically the Appendix list of references of e.g. a Wikipedia page containing ISBN numbers
inputfile = sys.stdin.read()

# Extract all ISBN numbers from text extract
itemlist = sorted(set(ISBNRE.findall(inputfile)))

for isbn_number in itemlist:            # Process the next edition
    amend_isbn_edition(isbn_number)

sys.exit(exitstat)
