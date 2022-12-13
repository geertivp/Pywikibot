#!/usr/bin/python3

codedoc = """
Add images (P18) to Wikidata items
from Wikimedia Commons SDC depicts (P180) statements.

Kind of creating a reverse SDC P180 statement in Wikidata...

Linking back Wikidata P18 statements to their corresponding
Wikimedia Commons SDC P180 statements, starting from a Wikimedia Category.

Basically, it tries to do the same as WDFIST, on the base of a
Wikimedia Commons category, a functionality that WDFIST does not offer…

Parameters:

    P1: Wikimedia Commons category

Options:

    -debug: detailed logging
    -v:     verbating mode

Examples:

    pwb add_image_from_sdc 'Images from Wiki Loves Heritage Belgium in 2022'

Data validation:

    Only allow pictures? What about sound and video?
    Do not add the picture when it is already assigned to another Wikidata item
    Do not add P18 if the item has already another photo

Prerequisites:

    Register SDC Depicts statements:
        at the moment of image upload
        can be proactively generated with the ISA Tool, as part of a campaign
        manually

Algorithm:

    List all files in the Wikimedia Commons category (recursively)
    Do we need to check and filter on file type, and only allow pictures?
    Skip the image file if it is aready used on wikidata
    Verify if there is any SDC data linked to the image
    Obtain any SDC P180 statement (depicts)
    Obtain the corresponding Wikidata items
        Assemble preferred P180 statements first
    Merge the image with P18 to the corresponding Wikidata item
        If the Wikidata item does not have a P18 statement yet
        (prefereably there is only one single P18 statement per item)

Known problems:

    "Wrong image" assigned to the item:
        Caused by a wrong SDC P180 statement
            To solve:
                * Remove the wrong P180 statement from SDC
                * Remove the wrong P18 statement from the Wikidata item

    File contains missing revisions
        Some revision was deleted (by a moderator)
        You can ignore this warning

Documentation:

    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html

    https://buildmedia.readthedocs.org/media/pdf/pywikibot/stable/pywikibot.pdf

    https://byabbe.se/2020/09/15/writing-structured-data-on-commons-with-python
        Prototype SDC queries

    https://be.wikimedia.org/wiki/ISA_Tool

Author:

	Geert Van Pamel, 2022-12-10, MIT License, User:Geertivp

"""

import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import sys		    	# System: argv, exit (get the parameters, terminate the program)
from pywikibot import pagegenerators as pg

# Global variables
modnm = 'Pywikibot add_image_from_sdc'  # Module name (using the Pywikibot package)
pgmid = '2022-12-13 (gvp)'	            # Program ID and version
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
    pywikibot.log('\nPicture {}'.format(page.title()))

    # Do we need to check and filter on file type == image?

    # Check if the picture is already used on another Wikidata item
    itempage = pywikibot.FilePage(repo, page.title())
    image_used = False

    for file_ref in pg.FileLinksGenerator(itempage):
        # We only take Qnumbers into account (primary namespace)
        if file_ref.namespace() == 0:
            image_used = True
            pywikibot.log('File is used by {}'.format(file_ref.title()))

    if not image_used:
        # Get media SDC data
        media_identifier = 'M' + str(page.pageid)
        request = site.simple_request(action='wbgetentities', ids=media_identifier)
        row = request.submit()

        try:
            # Possible error: 'NoneType' object is not subscriptable => no SDC (TypeError)
            sdc_data = row.get('entities').get(media_identifier)

            # Possible error: 'list' object has no attribute 'get' => no P180
            depict_list = sdc_data.get('statements').get('P180')

            # Loop through the list of SDC P180 statements, in order of priority
            item_list = []
            for depict in depict_list:
                # Get the Qnumber and item
                qnumber = depict['mainsnak']['datavalue']['value']['id']
                
                # Execute preferred before normal
                if depict['rank'] == 'preferred':
                    item_list.insert(0, qnumber)
                else:
                    item_list.append(qnumber)

            for qnumber in item_list:
                item = pywikibot.ItemPage(repo, qnumber)
                item.get(get_redirect=True)

                if 'P18' not in item.claims:
                    # Add image statement (P18) to item
                    claim = pywikibot.Claim(repo, 'P18')
                    claim.setTarget(page)
                    item.addClaim(claim, bot=True, summary=transcmt)

                    try:
                        pywikibot.warning('{} ({}): add image (P18) {}'
                                          .format(item.labels[mainlang], qnumber, page.title()))
                    except:
                        pywikibot.warning('({}): add image (P18) {}'
                                          .format(qnumber, page.title()))
                    break
                else:
                    # Show currently assigned impages (P18)
                    image_used = False
                    for image in item.claims['P18']:
                        val = image.getTarget()
                        if val == page:
                            image_used = True

                        try:
                            pywikibot.log('{} ({}): has image (P18) {}'
                                          .format(item.labels[mainlang], qnumber, val.title()))
                        except:
                            pywikibot.log('({}): has image (P18) {}'.format(qnumber, val.title()))
                    if image_used:
                        break
        # Ignore errors (use -debug to make them visiable in logs/pwb-bot.log
        except Exception as error:
            pywikibot.debug('Error processing {}, {}'.format(page.title(), error))
