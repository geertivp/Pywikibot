#!/home/geertivp/pwb/bin/python3

codedoc = """
Get ISBN data and create or amend Wikidata item for edition (P212)

Parameters:

    P1: ISBN number

    Optional:

        P2:         library (goob openl wiki)
        P3:         language code (default LANG)
        P4 P5...:   P/Q pairs for additional claims

Examples:

    ./create_isbn_edition.py 9789042925564                      # Default library and language

    ./create_isbn_edition.py 9789042925564 wiki nl P407 Q7411   # Language Dutch

Results:

    {'ISBN-13': '9789042925564', 'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. Aspecten Uit De Industriele Geschiedenis Van Leuven', 'Authors': ['A. Cresens'], 'Publisher': 'Peeters Pub & Booksellers', 'Year': '2012', 'Language': 'nl'}

Standard properties:

    P31:Q3331189:   instance of edition
    P212:   isbn-13 number
    P577:   date of publication (year)
    P1476:  book title
    P1680:  subtitle

Other properties:

    P50:    author
    P123:   publisher
    P407:   language of work
    P291:   place of publication
    P1104:  number of pages

Documentation:

    https://www.geeksforgeeks.org/searching-books-with-python/
    https://www.freecodecamp.org/news/python-json-how-to-convert-a-string-to-json/
    https://pypi.org/project/isbnlib/
    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html
    https://www.wikidata.org/wiki/Property:P212
    WikiProject Books:  https://www.wikidata.org/wiki/Q21831105
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Books
    https://www.wikidata.org/wiki/Wikidata:List_of_properties/work
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData/
    https://www.wikidata.org/wiki/Template:Book_properties
    https://www.wikidata.org/wiki/Template:Bibliographic_properties

Prerequisites:

    pywikibot
    pip install isbnlib

Restrictions:

    * Better use manual language code
    * Author and publisher need to be amended manually (search for Qnumber)

Known problems:

    * Not all ISBN attributes are listed by the webservice
    * Update ISBN items having no author, or publisher (which service to use?)

See also:

    WikiCite:   https://www.wikidata.org/wiki/Q21831105
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData

Algorithm:

    Get parameters
    Get ISBN data
    Convert ISBN data
    Register ISBN data

Author: Geert Van Pamel, 2022-08-04, GNU General Public License v3.0, User:Geertivp

"""

import logging          # Error logging
import os               # Operating system
import re		    	# Regular expressions (very handy!)
import sys              # System calls
import pywikibot
from isbnlib import *   # ISBN data
from pywikibot import pagegenerators as pg # Wikidata Query interface

# Inititalisation
propre = re.compile(r'P[0-9]+')             # P-number
qsuffre = re.compile(r'Q[0-9]+')            # Q-number

target={'P31':'Q3331189',   # Is an instance of edition
}

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

# The language code is only required when P/Q parameters are added, or different from the LANG code
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
if len(sys.argv) > 0:
    mainlang = sys.argv.pop(0)

# Get optional P/Q parameters
while len(sys.argv) > 0:
    inpar = propre.findall(sys.argv.pop(0).upper())[0]
    target[inpar] = qsuffre.findall(sys.argv.pop(0).upper())[0]

# Get ISBN data
try:
    isbn_data = meta(isbn_number, service=booklib)
    #print(isbn_data)
except Exception as error:
    print(format(error), file=sys.stderr)   # Data not available
    sys.exit(1)

# Show raw results
for i in isbn_data:
    print('%s:\t%s' % (i, isbn_data[i]))

if isbn_data['Language'] != '':
    mainlang = isbn_data['Language']

# Formatted ISBN number
isbn_number = isbn_data['ISBN-13']
isbn_fmtd = mask(isbn_number)
print()
print(isbn_fmtd)            # First one

# Get (sub)title when there is a dot
titles = isbn_data['Title'].split('.')
objectname = titles[0].strip()
subtitle = ''
if len(titles) > 1:
    subtitle = titles[1].strip()

# Book title
print(objectname)
print(subtitle)             # Optional
for i in range(2,len(titles)):
    print(titles[i].strip())

# Get the authors
for i in isbn_data['Authors']:
    print(i)

# Connect to database
transcmt = '#pwb Create ISBN edition'	    	        # Wikidata transaction comment
wikidata_site = pywikibot.Site('wikidata', 'wikidata')  # Login to Wikibase instance
repo = wikidata_site.data_repository()

# Validate P/Q list
targetx={}

for propty in target:
    proptyx = pywikibot.PropertyPage(repo, propty)
    targetx[propty] = pywikibot.ItemPage(repo, target[propty])
    print('Add %s (%s): %s (%s)' % (proptyx.labels[mainlang], propty, targetx[propty].labels[mainlang], target[propty]), file=sys.stderr)

# Search the ISBN number in Wikidata both canonical and numeric
    querytxt = ("""# Get ISBN number
SELECT DISTINCT ?item WHERE {
  VALUES ?isbn_number {
    "%s"
    "%s"
  }
  ?item wdt:P212 ?isbn_number.
}
""" % (isbn_fmtd, isbn_number))      # P212 should have canonical hyphenated format

generator = pg.WikidataSPARQLPageGenerator(querytxt, site=wikidata_site)

qnumber = ''
for item in generator:	                # Main loop for all DISTINCT items
    qnumber = item.getID()
    break                               # Unique value

if qnumber != '':
    print('Found item:', qnumber)
    item.get(get_redirect=True)         # Update item
else:
    label = {}
    label[mainlang] = objectname
    item = pywikibot.ItemPage(repo)     # Create item
    item.editEntity({'labels': label}, summary=transcmt)
    qnumber = item.getID()
    print('Creating item:', qnumber)

# Add all P/Q values
for propty in target:
    if propty not in item.claims:
        claim = pywikibot.Claim(repo, propty)
        claim.setTarget(targetx[propty])
        item.addClaim(claim, bot=True, summary=transcmt)

# Formatted ISBN number
if 'P212' not in item.claims:
    claim = pywikibot.Claim(repo, 'P212')
    claim.setTarget(isbn_fmtd)
    item.addClaim(claim, bot=True, summary=transcmt)

# Title
if 'P1476' not in item.claims:
    claim = pywikibot.Claim(repo, 'P1476')
    claim.setTarget(pywikibot.WbMonolingualText(text=objectname, language=mainlang))
    item.addClaim(claim, bot=True, summary=transcmt)

# Subtitle
if subtitle != '' and 'P1680' not in item.claims:
    claim = pywikibot.Claim(repo, 'P1680')
    claim.setTarget(pywikibot.WbMonolingualText(text=subtitle, language=mainlang))
    item.addClaim(claim, bot=True, summary=transcmt)

# Date of publication
if 'P577' not in item.claims:
    claim = pywikibot.Claim(repo, 'P577')
    claim.setTarget(pywikibot.WbTime(year=int(isbn_data['Year']), precision='year'))
    item.addClaim(claim, bot=True, summary=transcmt)

isbn_classify = classify(isbn_number)
isbn_cover = cover(isbn_number)
isbn_description = desc(isbn_number)
isbn_editions = editions(isbn_number)
isbn_doi = doi(isbn_number)
isbn_info = info(isbn_number)

print()
print(isbn_info)
print(isbn_classify)
print(isbn_doi)
print(isbn_editions)

for i in isbn_cover:
    print('%s:\t%s' % (i, isbn_cover[i]))

print()
print(isbn_description)

try:
    bibtex_metadata = doi2tex(isbn_doi)
    print(bibtex_metadata)
except Exception as error:
    logger.error(error)     # Data not available
