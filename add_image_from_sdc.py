#!/usr/bin/python3

codedoc = """
Add media files to Wikidata items
from Wikimedia Commons SDC depicts (P180) statements,
based on a Wikimedia Commons category.

Kind of creating a reverse SDC P180 statement in Wikidata...

Starting from a Wikimedia Category,
trough Wikimedia Commons SDC P180 statements,
registering media file statements (P10, P18, P51)
on the corresponding Wikidata items.

Basically, it tries to do the same as WDFIST (Magnus Manske),
on the base of a Wikimedia Commons category;
a functionality that WDFIST does not offer…

Parameters:

    P1: Wikimedia Commons category (subcatergories are processed recursively)

Options:

    -debug: detailed logging (logs/pwb-bot.log)
    -v:     verbatim mode (extra logging)
            To see the progress, it is advised to always use -v

Examples:

    pwb -v add_image_from_sdc 'Images from Wiki Loves Heritage Belgium in 2022'

Data validation:

    Only adds media files to instance items
    Wikimedia disambiguation items are skipped
    The script accepts audio, image, and video
    No media file is added when it is already assigned to another Wikidata item
    No media file is added if the item holds already another media file

Prerequisites:

    The use of SDC P180 should be encouraged.
    Register the SDC depicts statements in Wikimedia Commons:
        at the moment of media file upload
        can be proactively generated with the ISA Tool, as part of a campaign
        might be done with some Toolforge tool (unexisting yet?)
        manually adding depicts statements

Algorithm:

    List all files in the Wikimedia Commons category (recursively)
    Verify if there is any SDC data linked to the media file
    Obtain any SDC P180 statement (depicts)
    Skip the media file if it is already used on wikidata
    Determine the media type
    Obtain the corresponding Wikidata items
        Preferred P180 statement overrule normal items
    Merge the media file to the corresponding Wikidata item
        If the Wikidata item does not have a media statement yet
        (prefereably there is only one single media file per item/type)

Error messages:

    Add media file:                 Registering a new media file
    File is used by:                Do not register the same media file multiple times
    Media belongs to collection:    Skipping GLAM collections that often depicts art work parts;
                                    without a preferred qualifier there is a risk for wrong registrations
    No depicts for file:            No depict statements found; no item number available
    No statements for file:         Only labels; no statements, so no depicts
    Redundant media file:           All media slots already taken, avoid having multiple media files
    Skipping page:                  Page doesn't belong to the File namespace

Known problems:

    Updates might require manual validation, to correct any anomalies,
    see https://www.wikidata.org/wiki/Special:Contributions
    
    Redirects are not retroactively updated in SDC

    "Wrong media file" assigned to the item:
        Caused by a wrong SDC P180 statement
            To solve:
                Remove the wrong P180 statement from SDC
                Remove the wrong media statement from the Wikidata item
            or:
                You might create a new item
                Move the media statement to the preferred item
                Add a depicts statement to the media file, with Preferred status
            or:
                Mark an existing depicts item as Preferred

    File contains missing revisions:
        Some revision was deleted (by a moderator)
        You can ignore this warning

    Very few media files have a depicts statement (see prerequisites)

    Collection media files should always have a preferred statement

Documentation:

    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html

    https://buildmedia.readthedocs.org/media/pdf/pywikibot/stable/pywikibot.pdf

    https://byabbe.se/2020/09/15/writing-structured-data-on-commons-with-python
        Prototype SDC queries

    https://be.wikimedia.org/wiki/ISA_Tool

To do:

    Add SDC P180 depicts statement for Wikdata media file statements (reverse logic)
        Should be even more easy... 1:1 relationship...
        We should have a separate script, based on a SPARQL query.

Author:

	Geert Van Pamel, 2022-12-10, MIT License, User:Geertivp

"""

import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import sys		    	# System: argv, exit (get the parameters, terminate the program)
from pywikibot import pagegenerators as pg

# Global variables
modnm = 'Pywikibot add_image_from_sdc'  # Module name (using the Pywikibot package)
pgmid = '2022-12-15 (gvp)'	            # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'
transcmt = '#pwb Add image from SDC'

# Mapping of media types to property
# Should be amended for new types
media_props = {
    #'application': '',
    'audio': 'P51',
    'image': 'P18',
    'video': 'P10',
}

mainlang = os.getenv('LANG', 'en').split('_')[0]      # Default description language

# Get parameters
pgmnm = sys.argv.pop(0)

site = pywikibot.Site('commons')
repo = site.data_repository()

category = sys.argv.pop(0)
cat = pywikibot.Category(site, category)

pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
pywikibot.info(cat.categoryinfo)

# Get recursive image list from category
for page in pg.CategorizedPageGenerator(cat, recurse = True):
    # We only accept the File: namespace
    if page.namespace() != 6:
        pywikibot.log('Skipping {}'.format(page.title()))
        continue

    try:
        # Get media SDC data
        media_identifier = 'M' + str(page.pageid)
        request = site.simple_request(action='wbgetentities', ids=media_identifier)
        row = request.submit()

        ## ?? Catch error
        sdc_data = row.get('entities').get(media_identifier)
        ## {'pageid': 125667911, 'ns': 6, 'title': 'File:Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot.pdf', 'lastrevid': 707697714, 'modified': '2022-11-18T20:06:23Z', 'type': 'mediainfo', 'id': 'M125667911', 'labels': {'nl': {'language': 'nl', 'value': 'Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot'}, 'en': {'language': 'en', 'value': 'Wikidata ISBN book description with ISBNlib and Pywikibot'}, 'fr': {'language': 'fr', 'value': 'Description du livre Wikidata ISBN avec ISBNlib et Pywikibot'}, 'de': {'language': 'de', 'value': 'Wikidata ISBN Buchbeschreibung mit ISBNlib und Pywikibot'}, 'es': {'language': 'es', 'value': 'Descripción del libro de Wikidata ISBN con ISBNlib y Pywikibot'}}, 'descriptions': {}, 'statements': []}

        ## ?? Why is descriptions empty? How could it be registered? The GUI only allows to register labels?

        ## ?? Possible error: 'list' object has no attribute 'get' => no SDC (TypeError)
        statement_list = sdc_data.get('statements')
        if not statement_list:
            pywikibot.log('No statements for {}'.format(page.title()))
            continue

        depict_list = statement_list.get('P180')
        if not depict_list:
            pywikibot.log('No depicts for {}'.format(page.title()))
            continue

        # Depicts statements for GLAM collections
        # generally describe painting objects, so skip them
        # Skip collections, if the collection is documented
        collection_list = statement_list.get('P195')
        if collection_list:
            qnumber = collection_list[0]['mainsnak']['datavalue']['value']['id']
            pywikibot.log('Media {} belongs to collection {}'.format(page.title(), qnumber))
            continue

        # Check if the picture is already used on another Wikidata item
        itempage = pywikibot.FilePage(repo, page.title())
        image_used = False

        for file_ref in pg.FileLinksGenerator(itempage):
            # We only take Qnumbers into account (primary namespace)
            if file_ref.namespace() == 0:
                image_used = True
                pywikibot.log('{} is used by {}'.format(page.title(), file_ref.title()))

        if image_used:
            continue

        # We have now depicts statements, so we can obtain the media type
        file_type = ['image']
        mime_list = statement_list.get('P1163')
        if mime_list:
            mime_type = mime_list[0]['mainsnak']['datavalue']['value']
            file_type = mime_type.split('/')

        # Could possibly fail with non-recognized media types
        media_type = media_props[file_type[0]]

        # Loop through the list of SDC P180 statements,
        # in order of priority (preferred first)
        item_list = []
        for depict in depict_list:
            """
{'mainsnak':
	{'snaktype': 'value', 'property': 'P180', 'hash': 'de0ee4f082bfc89cdb25db93cc21755315974690',
	'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 2125610, 'id': 'Q2125610'}, 'type': 'wikibase-entityid'}
	},
'type': 'statement', 'id': 'M103310973$b63c02fb-495b-1c28-36a5-105f10aa6698', 'rank': 'normal'
}
            """
            # Get the Q-number and item
            qnumber = depict['mainsnak']['datavalue']['value']['id']

            # Overrule preferred items, or else add the item to the list
            if depict['rank'] == 'preferred':
                item_list = [qnumber]
                break
            else:
                item_list.append(qnumber)

        for qnumber in item_list:
            item = pywikibot.ItemPage(repo, qnumber)
            try:
                item.get()
            except pywikibot.exceptions.IsRedirectPageError:
                item = item.getRedirectTarget()
                pywikibot.warning('Item {} redirects to {}'.format(qnumber, item.getID()))
                qnumber = item.getID()

            if 'P31' in item.claims and item.claims['P31'][0].getID() == 'Q4167410':
                # Skip Wikimedia disambiguation items
                # See https://www.wikidata.org/wiki/Property:P18#P2303
                # Note that we accept P279 subclass, or non-instance items
                continue
            elif media_type not in item.claims:
                # Only add exclusive media file
                try:
                    pywikibot.warning('{} ({}): add media ({}) {}'
                                      .format(item.labels[mainlang],
                                              qnumber, media_type, page.title()))
                except:
                    pywikibot.warning('({}): add media ({}) {}'
                                      .format(qnumber, media_type, page.title()))

                # Add media statement to item
                claim = pywikibot.Claim(repo, media_type)
                claim.setTarget(page)
                item.addClaim(claim, bot=True, summary=transcmt)
                break
        else:
            # All media item slots were already taken
            pywikibot.log('Redundant media {}'.format(page.title()))

    # Log errors
    except Exception as error:
        pywikibot.log('Error processing {}, {}'.format(page.title(), error))
