#!/home/geertivp/pwb/bin/python3

codedoc = """
Get ISBN data and create or amend Wikidata item for edition (P212)

Parameters:

    P1: ISBN number

    Optional:

        P2:         language code (default LANG)
        P3 P4...:   P/Q pairs for additional claims

Examples:

    ./create_isbn_edition.py 9789042925564                  # Default language

    ./create_isbn_edition.py 9789042925564 nl P407 Q7411    # Language Dutch

Results:

    {'type': 'book', 'title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. Aspecten Uit De Industriele Geschiedenis Van Leuven', 'author': [{'name': 'A. Cresens'}], 'year': '2012', 'identifier': [{'type': 'ISBN', 'id': '9789042925564'}], 'publisher': 'Peeters Pub & Booksellers'}

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

Prerequisites:

    pywikibot
    pip install isbntools

Restrictions:

    * Better use manual language code
    * Author and publisher need to be amended manually (search for Qnumber)

Known problems:

    * Not all ISBN attributes are listed by the webservice
    * Update ISBN items without author, or publisher (which service to use?)

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

import json             # JSON
import os               # Operating system
import re		    	# Regular expressions (very handy!)
import sys              # System calls
import pywikibot
from isbntools.app import *
from pywikibot import pagegenerators as pg # Wikidata Query interface

propre = re.compile(r'P[0-9]+')             # P-number
qsuffre = re.compile(r'Q[0-9]+')            # Q-number

target={'P31':'Q3331189',   # Is an instance of edition
}

# Get mandatory parameters
pgmnm = sys.argv.pop(0)
isbn_number = sys.argv.pop(0)

# Get optional parameters
# The language code is only required when P/Q parameters are added, or different from the LANG code
mainlang = os.getenv('LANG', 'nl')[:2]     # Default description language
if len(sys.argv) > 0:
    mainlang = sys.argv.pop(0)

# Get optional P/Q parameters
while len(sys.argv) > 0:
    inpar = propre.findall(sys.argv.pop(0).upper())[0]
    target[inpar] = qsuffre.findall(sys.argv.pop(0).upper())[0]

# Get ISBN data
isbn_string = registry.bibformatters['json'](meta(isbn_number))

# Convert to JSON format
isbn_data = json.loads(isbn_string)

# Show raw results
for i in isbn_data:
    print('%s:\t%s' % (i, isbn_data[i]))

# Get (sub)title when there is a dot
titles = isbn_data['title'].split('.')
objectname = titles[0].strip()
subtitle = ''
if len(titles) > 1:
    subtitle = titles[1].strip()

# Book title
print()
print(objectname)
print(subtitle)             # Optional

# Formatted ISBN number - only the first one is taken into account
for i in range(len(isbn_data['identifier']), 0, -1):
    isbn_fmtd = mask(isbn_data['identifier'][i - 1]['id'])
    print(isbn_fmtd)        # Keep first one

# Get the authors
for i in range(len(isbn_data['author'])):
    print(isbn_data['author'][i]['name'])

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

# Search ISBN number in Wikidata
    querytxt = ("""# Get ISBN number
SELECT DISTINCT ?item WHERE {
  VALUES ?isbnnumber {
    "%s"
    "%s"
  }
  ?item wdt:P212 ?isbnnumber.
}
""" % (isbn_fmtd, isbn_fmtd.replace('-', '')))      # Normally should use canonical hyphenated format

generator = pg.WikidataSPARQLPageGenerator(querytxt, site=wikidata_site)

qnumber = ''
for item in generator:	                # Main loop for all DISTINCT items
    qnumber = item.getID()
    break                               # Unique value

if qnumber != '':
    print('Found item:', qnumber)       # Update item
    item.get(get_redirect=True)
else:
    label = {}
    label[mainlang] = objectname        # Create item
    item = pywikibot.ItemPage(repo)
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
    claim.setTarget(pywikibot.WbTime(year=int(isbn_data['year']), precision='year'))
    item.addClaim(claim, bot=True, summary=transcmt)
