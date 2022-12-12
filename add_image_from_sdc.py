#!/usr/bin/python3

codedoc = """
Add images (P18) to Wikidata items
from Wikimedia Commons SDC depicts (P180) statements.

Parameters:

    P1: Wikimedia Commons category

Options:

    -debug: detailed logging
    -v:     verbating mode

Examples:

    pwb add_image_from_sdc.py 'Images from Wiki Loves Heritage Belgium in 2022'

Algorithm:

    List all files in a Wikimedia Commons category
    Obtain any SDC P180 statement (depicts)
    Obtain the corresponding Wikidata items
    Merge the image with P18 in the corresponding Wikidata item

Known problems:

    Wrong image assigned to item
        Caused by a wrong SDC P180 statement
            To solve:
                * Remove the wrong P180 statement from SDC
                * Remove the wrong P18 statement from the Wikidata item

    File contains missing revisions
        Some revision was deleted (by a moderator)
    
Documentation:

    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html

    https://byabbe.se/2020/09/15/writing-structured-data-on-commons-with-python
        Prototype SDC queries

Author:

	Geert Van Pamel, 2022-12-10, MIT License, User:Geertivp

"""

import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import sys		    	# System: argv, exit (get the parameters, terminate the program)
from pywikibot import pagegenerators as pg

# Global variables
modnm = 'Pywikibot add_image_from_sdc'  # Module name (using the Pywikibot package)
pgmid = '2022-12-12 (gvp)'	            # Program ID and version
transcmt = '#pwb Add image from SDC'

mainlang = os.getenv('LANG', 'en').split('_')[0]      # Default description language

# Get parameters
pgmnm = sys.argv.pop(0)

site = pywikibot.Site('commons')
repo = site.data_repository()

category = sys.argv.pop(0)
cat = pywikibot.Category(site, category)

pywikibot.debug(pgmnm)
pywikibot.info(cat.categoryinfo)

# Get recursive image list from category
for page in pg.CategorizedPageGenerator(cat, recurse = True):
    pywikibot.log('\nPicture {}'.format(page))

    # Get SDC data
    media_identifier = 'M{}'.format(page.pageid)
    request = site.simple_request(action='wbgetentities', ids=media_identifier)
    row = request.submit()

    try:
        # Get first Qnumber
        # Error: 'NoneType' object is not subscriptable => no SDC
        sdc_data = row.get('entities').get(media_identifier)

        # Error: 'list' object has no attribute 'get' => no P180
        depict_list = sdc_data.get('statements').get('P180')
        #print(depict_list)

        # Here we have at least one P180
        for depict in depict_list:
            qnumber = depict['mainsnak']['datavalue']['value']['id']

            item = pywikibot.ItemPage(repo, qnumber)
            item.get(get_redirect=True)

            if 'P18' not in item.claims:
                # Add image statement (P18) to item
                try:
                    pywikibot.warning('{} ({}): add image (P18) {}'
                                      .format(item.labels[mainlang], qnumber, str(page)))
                except:
                    pywikibot.warning('({}): add image (P18) {}'.format(qnumber, str(page)))

                claim = pywikibot.Claim(repo, 'P18')
                claim.setTarget(page)
                item.addClaim(claim, bot=True, summary=transcmt)
                break
            # What if the picture is already used on another Wikidata item?
            else:
                # Show currently assigned impages (P18)
                image_used = False
                for image in item.claims['P18']:
                    val = image.getTarget()
                    if val == page:
                        image_used = True
                    try:
                        pywikibot.log('{} ({}): has image (P18) {}'
                              .format(item.labels[mainlang], qnumber, val))
                    except:
                        pywikibot.log('({}): has image (P18) {}'.format(qnumber, val))
                if image_used:
                    break
    # Ignore errors (use -debug to make them visiable in logs/pwb-bot.log
    except Exception as error:
        pywikibot.debug('Error processing {}, {}'.format(str(page), error))
