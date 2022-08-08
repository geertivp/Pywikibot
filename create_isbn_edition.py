#!/home/geertivp/pwb/bin/python3

codedoc = """
Get ISBN data and create or amend the Wikidata item for edition (P212)

Use digital libraries to get ISBN data in JSON format, and replicate it into Wikidata.

Parameters:

    P1: ISBN number

    Optional:

        P2:         library (goob openl wiki)
        P3:         language code (default LANG)
        P4 P5...:   P/Q pairs for additional claims (repeated)

Examples:

    ./create_isbn_edition.py 9789042925564                      # Default library and language

    ./create_isbn_edition.py 9789042925564 wiki nl P407 Q7411   # Language Dutch

Return status:

    The following status codes are returned to the shell:

    3 Invalid or missing parameter
    12 Item does not exist

Standard Wikidata properties:

    P31:Q3331189:   instance of edition
    P212:   isbn-13 number
    P407:   language of work
    P577:   date of publication (year)
    P1476:  book title
    P1680:  subtitle

Other Wikidata properties:

    P50:    author
    P123:   publisher
    P243:   OCLC ID
    P291:   place of publication
    P921:   main subject
    P1036:  Dewey Decimale Classificatie
    P1104:  number of pages
    P5331:  OCLC work ID

Documentation:

    https://www.geeksforgeeks.org/searching-books-with-python/
    https://www.freecodecamp.org/news/python-json-how-to-convert-a-string-to-json/
    https://pypi.org/project/isbnlib/
    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html
    https://www.wikidata.org/wiki/Property:P212
    WikiProject Books:  https://www.wikidata.org/wiki/Q21831105
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Books
    https://www.wikidata.org/wiki/Wikidata:List_of_properties/work
    https://www.wikidata.org/wiki/Template:Book_properties
    https://www.wikidata.org/wiki/Template:Bibliographic_properties
    http://classify.oclc.org/classify2/ClassifyDemo
    WikiCite:   https://www.wikidata.org/wiki/Q21831105
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData

Prerequisites:

    pywikibot
    pip install isbnlib

Restrictions:

    * Better use manual language code (language code is not always available from digital library)
    * Author and publisher need to be amended manually (search for Qnumber; possibly duplicate data)

Known problems:

    * Not all ISBN attributes are listed by the webservice(s)
    * Update ISBN items that have no author, or publisher (which service to use?)

Algorithm:

    Get parameters
    Validate parameters
    Get ISBN data
    Convert ISBN data
    Get additional data
    Register ISBN data into Wikidata

Author: Geert Van Pamel, 2022-08-04, GNU General Public License v3.0, User:Geertivp

"""

import logging          # Error logging
import os               # Operating system
import re		    	# Regular expressions (very handy!)
import sys              # System calls
import pywikibot
from isbnlib import *   # ISBN data
from pywikibot import pagegenerators as pg # Wikidata Query interface

# Initialisation
propre = re.compile(r'P[0-9]+')             # P-number
qsuffre = re.compile(r'Q[0-9]+')            # Q-number

# Other statements are added via command line parameters
target = {'P31':'Q3331189',                 # Is an instance of edition
}

# Statement and instance validation rules
propreqinst = {'P407':'Q34770',      # Language
}

def is_in_list(statement_list, checklist):
    # Verify if statement list contains at least one item from the checklist
    isinlist = True

    for seq in statement_list:
        if seq.getTarget().getID() in checklist:
            break
    else:
        isinlist = False
    return isinlist


# Error logging
logger = logging.getLogger('create_isbn_edition')

# Get mandatory parameters
pgmnm = sys.argv.pop(0)
isbn_number = sys.argv.pop(0)

# Get optional parameters

# Get the digital library
booklib = 'goob'
if len(sys.argv) > 0:
    booklib = sys.argv.pop(0)
    if booklib == '-':
        booklib = 'goob'

# Get the native language
# The language code is only required when P/Q parameters are added, or different from the LANG code
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
if len(sys.argv) > 0:
    mainlang = sys.argv.pop(0)

# Get additional P/Q parameters
while len(sys.argv) > 0:
    inpar = propre.findall(sys.argv.pop(0).upper())[0]
    target[inpar] = qsuffre.findall(sys.argv.pop(0).upper())[0]

# Get ISBN data
try:
    isbn_data = meta(isbn_number, service=booklib)
    #print(isbn_data)
    # {'ISBN-13': '9789042925564', 'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. Aspecten Uit De Industriele Geschiedenis Van Leuven', 'Authors': ['A. Cresens'], 'Publisher': 'Peeters Pub & Booksellers', 'Year': '2012', 'Language': 'nl'}
except Exception as error:
    # logger.critital(error) does not work
    print(format(error), file=sys.stderr)   # When the book is unknown the program stops
    sys.exit(3)


# Show the raw results
for i in isbn_data:
    print('%s:\t%s' % (i, isbn_data[i]))

# Get the language from the ISBN book reference
if isbn_data['Language'] != '':
    mainlang = isbn_data['Language']

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
print(subtitle)                 # Optional
for i in range(2,len(titles)):  # Print subsequent subtitles, when available
    print(titles[i].strip())

# Get the author list
for i in isbn_data['Authors']:
    print(i)

# Connect to database
transcmt = '#pwb Create ISBN edition'	    	        # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()                  # Required for wikidata object access (item, property, statement)

# Validate P/Q list
proptyx={}
#propreqinstx={}
targetx={}

# Make sure that labels are known in the native language
# Any exception will halt the program

#for propty in propreqinst:
#    if propty not in proptyx:
#        proptyx[propty] = pywikibot.PropertyPage(repo, propty)
#    propreqinstx[propty] = pywikibot.ItemPage(repo, propreqinst[propty])
#    propreqinstx[propty].get(get_redirect=True)

for propty in target:
    if propty not in proptyx:
        proptyx[propty] = pywikibot.PropertyPage(repo, propty)
    targetx[propty] = pywikibot.ItemPage(repo, target[propty])
    targetx[propty].get(get_redirect=True)
    #print(targetx[propty].claims['P31'])
    #print(propreqinst[propty])
    if propty in propreqinst and ('P31' not in targetx[propty].claims or not is_in_list(targetx[propty].claims['P31'], propreqinst[propty])):
        logger.critical('%s (%s) is not a language' % (targetx[propty].labels[mainlang], target[propty]))
        sys.exit(12)

# Search the ISBN number in Wikidata both canonical and numeric
isbn_query = ("""# Get ISBN number
SELECT ?item WHERE {
  VALUES ?isbn_number {
    "%s"
    "%s"
  }
  ?item wdt:P212 ?isbn_number.
}
LIMIT 1
""" % (isbn_fmtd, isbn_number))      # P212 should have canonical hyphenated format

generator = pg.WikidataSPARQLPageGenerator(isbn_query, site=wikidata_site)

qnumber = ''
for item in generator:	                # Main loop for all DISTINCT items
    qnumber = item.getID()
    break                               # Unique value

# Create or amend
if qnumber != '':
    print('Found item:', qnumber, file=sys.stderr)
    item.get(get_redirect=True)         # Update item
else:
    label = {}
    label[mainlang] = objectname
    item = pywikibot.ItemPage(repo)     # Create item
    item.editEntity({'labels': label}, summary=transcmt)
    qnumber = item.getID()
    print('Creating item:', qnumber, file=sys.stderr)

# Add all P/Q values
for propty in target:
    if propty not in item.claims:
        print('Add %s (%s): %s (%s)' % (proptyx[propty].labels[mainlang], propty, targetx[propty].labels[mainlang], target[propty]), file=sys.stderr)
        claim = pywikibot.Claim(repo, propty)
        claim.setTarget(targetx[propty])
        item.addClaim(claim, bot=True, summary=transcmt)

# Set formatted ISBN number
if 'P212' not in item.claims:
    print('Add ISBN number (P212): %s' % (isbn_fmtd), file=sys.stderr)
    claim = pywikibot.Claim(repo, 'P212')
    claim.setTarget(isbn_fmtd)
    item.addClaim(claim, bot=True, summary=transcmt)

# Title
if 'P1476' not in item.claims:
    print('Add Title (P1476): %s' % (objectname), file=sys.stderr)
    claim = pywikibot.Claim(repo, 'P1476')
    claim.setTarget(pywikibot.WbMonolingualText(text=objectname, language=mainlang))
    item.addClaim(claim, bot=True, summary=transcmt)

# Subtitle
if subtitle != '' and 'P1680' not in item.claims:
    print('Add Subtitle (P1680): %s' % (subtitle), file=sys.stderr)
    claim = pywikibot.Claim(repo, 'P1680')
    claim.setTarget(pywikibot.WbMonolingualText(text=subtitle, language=mainlang))
    item.addClaim(claim, bot=True, summary=transcmt)

# Date of publication
if 'P577' not in item.claims:
    print('Add Year of publication (P577): %s' % (isbn_data['Year']), file=sys.stderr)
    claim = pywikibot.Claim(repo, 'P577')
    claim.setTarget(pywikibot.WbTime(year=int(isbn_data['Year']), precision='year'))
    item.addClaim(claim, bot=True, summary=transcmt)

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
    print('Add OCLC work ID (P5331): %s' % (isbn_classify['owi']), file=sys.stderr)
    claim = pywikibot.Claim(repo, 'P5331')
    claim.setTarget(isbn_classify['owi'])
    item.addClaim(claim, bot=True, summary=transcmt)

# Set the OCLC id
if 'oclc' in isbn_classify and 'P243' not in item.claims:
    print('Add OCLC ID (P243): %s' % (isbn_classify['oclc']), file=sys.stderr)
    claim = pywikibot.Claim(repo, 'P243')
    claim.setTarget(isbn_classify['oclc'])
    item.addClaim(claim, bot=True, summary=transcmt)

# Library of Congress Classification (works and editions)
if 'lcc' in isbn_classify and 'P8360' not in item.claims:
    print('Add Library of Congress Classification for edition (P8360): %s' % (isbn_classify['lcc']), file=sys.stderr)
    claim = pywikibot.Claim(repo, 'P8360')
    claim.setTarget(isbn_classify['lcc'])
    item.addClaim(claim, bot=True, summary=transcmt)

# Dewey Decimale Classificatie
if 'ddc' in isbn_classify and 'P1036' not in item.claims:
    print('Add Dewey Decimale Classificatie (P1036): %s' % (isbn_classify['ddc']), file=sys.stderr)
    claim = pywikibot.Claim(repo, 'P1036')
    claim.setTarget(isbn_classify['ddc'])
    item.addClaim(claim, bot=True, summary=transcmt)

# Register Fast ID using P921 through P2163
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
LIMIT 1
""" % (fast_id))

        generator = pg.WikidataSPARQLPageGenerator(main_subject_query, site=wikidata_site)

        qmain_subject = ''
        for main_subject in generator:	            # Main loop for all DISTINCT items
            qmain_subject = main_subject.getID()
            break                                   # Unique value

        # Create or amend P921 statement
        if qmain_subject == '':
            print('Main subject not found for Fast ID', fast_id, file=sys.stderr)
        else:
            add_main_subject = True
            if 'P921' in item.claims:
                for seq in item.claims['P921']:
                    if seq.getTarget().getID() == qmain_subject:
                        add_main_subject = False
                        break

            if add_main_subject:
                print('Add main subject', qmain_subject, 'for Fast ID', fast_id, file=sys.stderr)
                claim = pywikibot.Claim(repo, 'P921')
                claim.setTarget(main_subject)
                item.addClaim(claim, bot=True, summary=transcmt)
            else:
                print('Skipping main subject', qmain_subject, 'for Fast ID', fast_id, file=sys.stderr)

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
