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

Prerequisites:

    The use of SDC P180 (depict) is a prerequisite and should be encouraged.
    Register the SDC depicts statements in Wikimedia Commons:
        at the moment of media file upload
        can be proactively generated with the ISA Tool, as part of a campaign
        might be done with some Toolforge tool (unexisting yet?)
        manually adding depicts statements
    If there are no SDC P180 statements, no updates in Wikidata are performed.

Data validation:

    Media files having depict statements are added to Wikidata items in the main namespace.
    The script accepts audio, image, and video.
    Wikidata disambiguation and category items are skipped.
    No media file is added if the item holds already another media file.
    No media file is added when it is already assigned to another Wikidata item.
    Collection media files should always have a preferred statement;
        avoid Wikidata image statement polution;
        requires a specific Wikidata item for the collection object (which is a good idea!).

Functionality:

    This script follows the Wikidata guidelines (e.g. one single image statement).

    Handle special image properties; e.g.:
        P154    logo
        P1442   grave
        P5775   interior

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

Use cases:

    Load files via P1 Wikimedia Commons category
    Paste the list of media files via stdin
        Make a list of user uploads via AutoWikiBrowser (AWB)
    Run the program
        Put all the "No depicts" media files in AWB to add depicts statements
        Rerun the program
    Run the program
        Put all the "Redundant media" files in AWB to add depicts statements
        Rerun the program

To do:

    Properly handle the image quality (resolution)

Algorithm:

    List all files in the Wikimedia Commons category (recursively)
    As an alternative, the list of files is read from stdin.
    Verify if there is any SDC data registered with the media files
    Obtain any SDC P180 statement (depicts)
    Apply eligibility criteria:
        Skip collection items not having a preferred qualifier
        Skip artist work for artists
        Skip the media file if it is already used on wikidata
    Determine the media type (multiple rules; default image)
    Obtain the corresponding Wikidata items
        Preferred P180 statement overrule normal items
        Handle (single) redirected items
    Merge the media file to the corresponding Wikidata item
        If the Wikidata item does not have a media statement yet
        (prefereably there is only one single media file per item/type)

Known problems:

    Updated items might require manual validation, to correct any anomalies;
    see https://www.wikidata.org/wiki/Special:Contributions

    Category redirects are not traversed (resolve manually).

    Wikidata redirects are recognized, but are not retroactively updated in the SDC statements.

    Deleted Wikidata item page, while Wikimedia Commons SDC P180 staement is still there;
    this is not retroactively resolved.

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
        Some revisions were deleted (by a moderator);
        you can ignore this warning.

    Very few media files have a depicts statement (see prerequisites)
        Idea: missing depicts query

    Sleeping for 0.2 seconds, 2022-12-17 11:48:51

    Pausing due to database lag: Waiting for 10.64.32.12: 5.1477 seconds lagged.
    Sleeping for 5.0 seconds, 2022-12-25 10:48:31

    Fatal error:
    RecursionError: maximum recursion depth exceeded while calling a Python object

    Multiple timeout problems... should/could we set a hard timeout?

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

# Global variables
modnm = 'Pywikibot add_image_from_sdc'  # Module name (using the Pywikibot package)
pgmid = '2022-12-26 (gvp)'	            # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'
transcmt = '#pwb Add image from SDC'

# Constants
MAINNAMESPACE = 0
FILENAMESPACE = 6

VIDEOPROP = 'P10'
IMAGEPROP = 'P18'
INSTANCEPROP = 'P31'
AUTHORPROP = 'P50'
AUDIOPROP = 'P51'
COATOFARMSPROP = 'P94'
EDITORPROP = 'P98'
SIGNATUREPROP = 'P109'
PUBLISHERPROP = 'P123'
LOGOPROP = 'P154'
DEPICTSPROP = 'P180'
COLLECTIONPROP = 'P195'
SUBCLASSPROP = 'P279'
RESTRICTPROP = 'P518'
PDFPROP = 'P996'
MIMEPROP = 'P1163'
GRAVEPROP = 'P1442'
PLACENAMEPROP = 'P1766'
PLAQUEPROP = 'P1801'
AUTHORNAMEPROP = 'P2093'
NIGHTVIEWPROP = 'P3451'
WINTERVIEWPROP = 'P5252'
INTERIORPROP = 'P5775'
FRAMEWORKPROP = 'P7420'
VIEWPROP = 'P8517'
AERIALVIEWPROP = 'P8592'
COLORWORKPROP = 'P10093'

HUMANINSTANCE = 'Q5'
CATEGORYINSTANCE = 'Q4167836'
DISAMBUGINSTANCE = 'Q4167410'

# Base media types
base_work = {AUDIOPROP, IMAGEPROP, VIDEOPROP}

# Unwanted instances
skipped_instances = {CATEGORYINSTANCE, DISAMBUGINSTANCE}

# Map image instance to media types
image_types = {
    'Q14659': 'coatofarms',
    'Q173387': 'grave',
    'Q188675': 'signature',
    'Q266488': 'placename',
    'Q721747': 'plaque',
    'Q2032225': 'placename',
    'Q3362196': 'placename',
    'Q55498668': 'placename',
    'Q2075301': 'view',
    'Q28333482': 'nightview',
    'Q860792': 'framework',
    'Q1153655': 'aerialview',
    'Q1886349': 'logo',
    'Q31807746': 'interior',
    'Q54819662': 'winterview',
    'Q109592922': 'colorwork',
    # others...
}

# Mapping of SDC media MIME types to Wikidata property
# Should be extended for new MIME types -> will generate a KeyError
media_props = {
    #'application': '',     # Not implemented; generates error
    'aerialview': AERIALVIEWPROP,
    'coatofarms': COATOFARMSPROP,
    'framework': FRAMEWORKPROP,
    'audio': AUDIOPROP,
    'colorwork': COLORWORKPROP,
    'grave': GRAVEPROP,
    'image': IMAGEPROP,
    'interior': INTERIORPROP,
    'logo': LOGOPROP,
    'nightview': NIGHTVIEWPROP,
    'oga': AUDIOPROP,
    'ogg': VIDEOPROP,
    'ogv': VIDEOPROP,
    'pdf': PDFPROP,
    'placename': PLACENAMEPROP,
    'plaque': PLAQUEPROP,
    'signature': SIGNATUREPROP,
    'video': VIDEOPROP,
    'view': VIEWPROP,
    'winterview': WINTERVIEWPROP,
    # others...
}


def is_in_list(statement_list, checklist) -> bool:
    """
    Verify if statement list contains at least one item from the checklist

    Parameters:

        statement_list: Statement list
        checklist:      List of values (string)

    Returns:

    Boolean (True when match)
    """
    for seq in statement_list:
        if seq.getTarget().getID() in checklist:
            isinlist = True
            break
    else:
        isinlist = False
    return isinlist


mainlang = os.getenv('LANG', 'en').split('_')[0]      # Default description language

# Get parameters
pgmnm = sys.argv.pop(0)
pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))

# Login
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

# Loop through the media file list
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

        # Default file type; can be overruled by depict statement
        file_type = ['image']
        mime_list = statement_list.get(MIMEPROP)
        if mime_list:
            # We now have valid depicts statements, so we can obtain the media type
            # Default: image
            mime_type = mime_list[0]['mainsnak']['datavalue']['value']
            file_type = mime_type.split('/')

        item_list = []
        preferred = False
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
            # Get the Q-number for item
            qnumber = depict['mainsnak']['datavalue']['value']['id']
            if qnumber in image_types:
                # Special file type
                file_type = [image_types[qnumber]]

            if preferred:
                # Keep first preferred item
                pass
            elif depict['rank'] == 'preferred':
                # Overrule normal items when at least one preferred
                preferred = True
                item_list = [qnumber]
            elif not ('qualifiers' in depict and RESTRICTPROP in depict['qualifiers']):
                # Skip "aplies to" qualifiers
                # Could also filter on minimum image resolution
                # Add a normal ranked item to the list
                item_list.append(qnumber)

        collection_list = statement_list.get(COLLECTIONPROP)
        if collection_list and not preferred:
            # Depict statements for GLAM collections
            # generally describe parts of painting objects;
            # skip them, unless there is a preferred statement describing the artwork itself.
            collection = collection_list[0]['mainsnak']['datavalue']['value']['id']
            pywikibot.log('Media {} {} belongs to collection {}'
                          .format(media_identifier, page.title(), collection))
            continue

        # Check if the media file is already used on another Wikidata item
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

        # Determine media type
        if file_type[0] == 'application':
            media_type = media_props[file_type[1]]
        else:
            # Could possibly fail with KeyError with non-recognized media types
            # In that case the new media type should be added to the list
            media_type = media_props[file_type[0]]

        description_list = sdc_data.get('descriptions')
        if description_list != {}:
            ## ?? Why is descriptions always empty? How could it be registered?
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

            if media_type in item.claims:
                # Only add exclusive media file (preferably one single image per Wikidata item)
                continue
            elif not (INSTANCEPROP in item.claims
                    or SUBCLASSPROP in item.claims):
                # Skip when neither instance, nor subclass
                continue
            elif (INSTANCEPROP in item.claims
                    # Skip Wikimedia disambiguation and category items;
                    # we want real items;
                    # see https://www.wikidata.org/wiki/Property:P18#P2303
                    and is_in_list(item.claims[INSTANCEPROP], skipped_instances)):
                continue
            elif (INSTANCEPROP in item.claims
                    # Human and artwork images are incompatible (distinction between artist and oevre)
                    and is_in_list(item.claims[INSTANCEPROP], HUMANINSTANCE)
                    and media_type not in base_work):
                continue
            elif (AUTHORPROP in item.claims
                    or AUTHORNAMEPROP in item.claims
                    or EDITORPROP in item.claims
                    or PUBLISHERPROP in item.claims):
                # We skip publications
                continue
                # Note that we unconditionally accept P279 subclass
            elif item.namespace() == MAINNAMESPACE:
                # Only register media files to items in the main namespace
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
