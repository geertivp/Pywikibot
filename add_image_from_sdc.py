#!/usr/bin/python3

codedoc = """
Add media files to Wikidata items
from Wikimedia Commons SDC depicts (P180) statements,
based on a Wikimedia Commons category (parameter P1),
or a list of media files (stdin).

Kind of creating a reverse SDC P180 statement in Wikidata...

Starting from a Wikimedia Category,
or a list of media files,
trough Wikimedia Commons SDC P180 statements,
registering media file statements (P10, P18, P51)
to the corresponding Wikidata items.

Basically, it tries to do the same as WDFIST (Magnus Manske),
on the base of a Wikimedia Commons category;
a functionality that WDFIST does not offer…

In prnciple the script runs completely automated, without any human intervention,
but it is strongly advised to verify the resulting changes in Wikidata.
Depending on the quality of the SDC P180 statements manual corrections might be required.
Wikimedia Commons is not updated.

Parameters:

    P1: Wikimedia Commons category (subcatergories are processed recursively)
    
    If no parameters are available,
    a list of media filenames is read via stdin;
    one filename per line.

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
    If there are no SDC P180 statements, no updates in Wikidata are performed.

Algorithm:

    List all files in the Wikimedia Commons category (recursively)
    Or the list of files is read from stdin.
    Verify if there is any SDC data linked to the media files
    Obtain any SDC P180 statement (depicts)
    Skip the media file if it is already used on wikidata
    Determine the media type
    Obtain the corresponding Wikidata items
        Preferred P180 statement overrule normal items
    Handle (single) redirected items
    Merge the media file to the corresponding Wikidata item
        If the Wikidata item does not have a media statement yet
        (prefereably there is only one single media file per item/type)

Error messages:

    Add media file:                 Registering a new media file.
    File is used by:                Do not register the same media file multiple times.
    Media belongs to collection:    Skipping GLAM collections that often depicts art work parts;
                                    without a preferred qualifier there is a risk for wrong registrations.
    No depicts for file:            No depict statements found; no item number available.
                                    We should encorage to add depicts statements;
                                    at least one with preferred status.
    No statements for file:         Only labels; no statements, so no depicts.
    Redundant media file:           All media slots already taken, avoid having multiple media files;
                                    maybe add more depicts statements to find more items.
    Skipping page:                  Page doesn't belong to the File namespace.

Tips and tricks:

    Make a list of user uploads via AutoWikiBrowser
    Paste the list of media files via stdin

Known problems:

    Updated items might require manual validation, to correct any anomalies;
    see https://www.wikidata.org/wiki/Special:Contributions
    
    Category redirects are not traversed.
    
    Wikidata redirects are not retroactively updated in SDC statements.
    
    Wikidata item page was deleted while SDC P180 was still there.

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

    Sleeping for 0.1 seconds, 2022-12-17 11:48:51

    Fatal error:
    RecursionError: maximum recursion depth exceeded while calling a Python object

    Multiple timeout problems... could we set a hard timeout?

    Other properties; image could be one off:
        P154    logo
        P1442   grave
        P5775   interior

Documentation:

    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html

    https://buildmedia.readthedocs.org/media/pdf/pywikibot/stable/pywikibot.pdf

    https://byabbe.se/2020/09/15/writing-structured-data-on-commons-with-python
    Prototype SDC queries

    https://be.wikimedia.org/wiki/ISA_Tool
    Tool to generate SDC P180 depict statements and captions (SDC labels).

Related projects:

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

# Constants
MAINNAMESPACE = 0
FILENAMESPACE = 6

VIDEOPROP = 'P10'
IMAGEPROP = 'P18'
INSTANCEPROP = 'P31'
AUTHORPROP = 'P50'
AUDIOPROP = 'P51'
PUBLISHERPROP = 'P123'
LOGOPROP = 'P154'
DEPICTSPROP = 'P180'
COLLECTIONPROP = 'P195'
SUBCLASSPROP = 'P279'
MIMEPROP = 'P1163'
GRAVEPROP = 'P1442'
INTERIORPROP = 'P5775'

CATEGORYINSTANCE = 'Q4167836'
DISAMBUGINSTANCE = 'Q4167410'

# Global variables
modnm = 'Pywikibot add_image_from_sdc'  # Module name (using the Pywikibot package)
pgmid = '2022-12-20 (gvp)'	            # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'
transcmt = '#pwb Add image from SDC'

# Map image instance to property
image_types = {
    'Q173387': 'grave',
    'Q1886349': 'logo',
    'Q31807746': 'interior',
    # others...
}

# Mapping of SDC media MIME types to Wikidata property
# Should be extended for new MIME types -> will generate a KeyError
media_props = {
    #'application': '',     # Not implemented; generates error
    'audio': AUDIOPROP,
    'grave': GRAVEPROP,
    'image': IMAGEPROP,
    'interior': INTERIORPROP,
    'logo': LOGOPROP,
    'video': VIDEOPROP,
    # others...
}

mainlang = os.getenv('LANG', 'en').split('_')[0]      # Default description language

# Get parameters
pgmnm = sys.argv.pop(0)

pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))
site = pywikibot.Site('commons')
repo = site.data_repository()

# Get input parameters (either P1 or stdin)
if sys.argv:
    # Get Wikimedia Commons page list from category P1
    category = sys.argv.pop(0)

    # Get recursive image list from category
    cat_list = pywikibot.Category(site, category)
    pywikibot.info('Category:{}: {}'.format(category, cat_list.categoryinfo))
    page_list = pg.CategorizedPageGenerator(cat_list, recurse = True)
else:
    # Read Wikimedia Commons page list from stdin
    inputfile = sys.stdin.read()
    input_list = sorted(set(inputfile.split('\n')))
    page_list = []
    for subject in input_list:
        if subject:
            try:
                page_list.append(pywikibot.FilePage(site, subject))
            except Exception as error:
                pywikibot.log(error)

for page in page_list:
    try:
        # We only accept the File: namespace
        media_identifier = 'M' + str(page.pageid)
        if page.namespace() != FILENAMESPACE:
            pywikibot.log('Skipping {} {}'.format(media_identifier, page.title()))
            continue

        # Get media SDC data
        request = site.simple_request(action='wbgetentities', ids=media_identifier)
        row = request.submit()

        # Catch errors
        sdc_data = row.get('entities').get(media_identifier)
        ## {'pageid': 125667911, 'ns': 6, 'title': 'File:Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot.pdf', 'lastrevid': 707697714, 'modified': '2022-11-18T20:06:23Z', 'type': 'mediainfo', 'id': 'M125667911', 'labels': {'nl': {'language': 'nl', 'value': 'Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot'}, 'en': {'language': 'en', 'value': 'Wikidata ISBN book description with ISBNlib and Pywikibot'}, 'fr': {'language': 'fr', 'value': 'Description du livre Wikidata ISBN avec ISBNlib et Pywikibot'}, 'de': {'language': 'de', 'value': 'Wikidata ISBN Buchbeschreibung mit ISBNlib und Pywikibot'}, 'es': {'language': 'es', 'value': 'Descripción del libro de Wikidata ISBN con ISBNlib y Pywikibot'}}, 'descriptions': {}, 'statements': []}

        statement_list = sdc_data.get('statements')
        if not statement_list:
            # Old images do not have statements
            pywikibot.log('No statements for {} {}'
                          .format(media_identifier, page.title()))
            continue

        depict_list = statement_list.get(DEPICTSPROP)
        if not depict_list:
            # This program runs on the basis of depects statements
            pywikibot.log('No depicts for {} {}'.format(media_identifier, page.title()))
            continue

        collection_list = statement_list.get(COLLECTIONPROP)
        if collection_list:
            # Depicts statements for GLAM collections
            # generally describe part painting objects; so skip them
            # Skip collections, if the collection is documented
            # They should rather have a preferred statement describing the artwork
            qnumber = collection_list[0]['mainsnak']['datavalue']['value']['id']
            pywikibot.log('Media {} {} belongs to collection {}'
                          .format(media_identifier, page.title(), qnumber))
            continue

        # Check if the picture is already used on another Wikidata item
        itempage = pywikibot.FilePage(repo, page.title())
        image_used = False

        # This includes P10 video, P18 image, P51 audio, etc.
        # Possibly other links?
        for file_ref in pg.FileLinksGenerator(itempage):
            if file_ref.namespace() == MAINNAMESPACE:
                # We only take Qnumbers into account (primary namespace)
                # e.g. ignore descriptive pages
                image_used = True
                pywikibot.log('{} {} is used by {}'
                              .format(media_identifier, page.title(), file_ref.title()))
        if image_used:
            # Image is already used, so skip
            continue

        # Default file type; can be overruled by depict statement
        file_type = ['image']
        mime_list = statement_list.get(MIMEPROP)
        if mime_list:
            # We now have valid depicts statements, so we can obtain the media type
            # Default: image
            mime_type = mime_list[0]['mainsnak']['datavalue']['value']
            file_type = mime_type.split('/')

        item_list = []
        for depict in depict_list:
            # Loop through the list of SDC P180 statements,
            # in order of priority
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
            if qnumber in image_types:
                # Overrule preferred items, or else add the item to the list
                file_type = [image_types[qnumber]]

            if depict['rank'] == 'preferred':
                # Ignore normal when at least one preferred
                item_list = [qnumber]
            elif not ('qualifiers' in depict and 'P518' in depict['qualifiers']):
                # Skip "aplies to" qualifiers
                # Could also filter on minimum image resolution
                # Add a normal ranked item to the list
                item_list.append(qnumber)

        # Could possibly fail with KeyError when non-recognized media types
        # In that case the new media type should be added
        media_type = media_props[file_type[0]]

        description_list = sdc_data.get('descriptions')
        if description_list != {}:
            ## ?? Why is descriptions empty? How could it be registered?
            # The GUI only allows to register labels?
            pywikibot.log(description_list)

        for qnumber in item_list:
            # Loop through the target Wikidata items to find a match
            item = pywikibot.ItemPage(repo, qnumber)

            try:
                item.get()
            except pywikibot.exceptions.IsRedirectPageError:
                # Resolve a single redirect error
                item = item.getRedirectTarget()
                pywikibot.warning('Item {} redirects to {}'.format(qnumber, item.getID()))
                qnumber = item.getID()

            if item.namespace() != MAINNAMESPACE:
                # Only register media files to items in the main namespace
                continue
            elif (INSTANCEPROP not in item.claims
                    and SUBCLASSPROP not in item.claims):
                # Skip when neither instance, nor subclass
                continue
            elif ((INSTANCEPROP in item.claims
                        and item.claims[INSTANCEPROP][0].getTarget().getID() in {CATEGORYINSTANCE, DISAMBUGINSTANCE})
                    or (AUTHORPROP in item.claims)
                    or (PUBLISHERPROP in item.claims)):
                # Skip Wikimedia disambiguation and category items
                # See https://www.wikidata.org/wiki/Property:P18#P2303
                # Note that we unditionally accept P279 subclass
                # In general we skip publications
                continue
            elif media_type not in item.claims:
                # Only add exclusive media file (preferably one single image per Wikidata item)
                try:
                    pywikibot.warning('{} ({}): add media ({}) {} {}'
                                      .format(item.labels[mainlang],
                                              qnumber, media_type, media_identifier, page.title()))
                except:
                    pywikibot.warning('({}): add media ({}) {} {}'
                                      .format(qnumber, media_type, media_identifier, page.title()))

                # Add media statement to item
                claim = pywikibot.Claim(repo, media_type)
                claim.setTarget(page)
                item.addClaim(claim, bot=True, summary=transcmt)
                break
        else:
            # All media item slots were already taken
            # Maybe add more appropriate depicts statements?
            pywikibot.log('Redundant media {} {}'.format(media_identifier, page.title()))

    # Log errors
    except Exception as error:
        pywikibot.log('Error processing {} {}, {}'.format(media_identifier, page.title(), error))
        #raise  # Uncomment to debug
