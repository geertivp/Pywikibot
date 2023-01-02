#!/usr/bin/python3

codedoc = """
Add media files to Wikidata items
from Wikimedia Commons SDC depicts (P180) statements,
based on a Wikimedia Commons category (parameter P1),
or a list of media files (stdin).

Kind of creating reverse SDC P180 statements in Wikidata...

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
Depending on the quality of the SDC P180 statements, manual corrections might be required.
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

    https://www.wikidata.org/wiki/Q98141338
    https://www.wikidata.org/w/index.php?title=Q140&diff=1799300865&oldid=1796952109

    Missing metadata:

    https://commons.wikimedia.org/wiki/Category:Unidentified_subjects

Prerequisites:

    The use of SDC P180 (depict) is a prerequisite and should be encouraged.
    Register the SDC depicts statements in Wikimedia Commons:
        immediately after the media upload,
        can be generated with the ISA Tool, as part of a campaign,
        might be done with some Toolforge tool (unexisting yet?),
        via AC/DC,
        or manually adding depicts statements via the GUI
    If there are no SDC P180 statements, no updates in Wikidata are performed.
    Please add a MIMI type (default image/jpeg)
    Please add a preferred qualifier (especially for collections)

Data validation:

    Media files having depict statements are added to Wikidata items in the main namespace.
    The script accepts audio, image, and video.
        For images, some P180 instances can determine subtypes
    Wikidata disambiguation and category items are skipped.
    No media file is added when it is already assigned to another Wikidata item.
    No media file is added if the item holds already another media file.
    Collection media files should always have a preferred statement;
        avoid Wikidata image statement polution;
        requires a specific Wikidata item for the collection object (which is a good idea!).

Functionality:

    This script follows the general Wikidata guidelines (e.g. one single image statement).

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

    Proactive constraint checking
    Properly handle the image quality (resolution)
        How to get wikimedia commons image size with pywikibot?

Algorithm:

    List all files in the Wikimedia Commons category (recursively)
    As an alternative, the list of files is read from stdin.
    Verify if there is any SDC data registered with the media files
    Obtain any SDC P180 statement (depicts)
    Apply eligibility criteria:
        Skip collection items not having a preferred qualifier
        Skip artist work for artists
        Skip the media file if it is already used on wikidata
    Determine the media type (multiple rules; default: image)
    Obtain the corresponding Wikidata items
        Preferred P180 statement overrule normal items
        Handle (single) redirected items
    Merge the media file to the corresponding Wikidata item
        If the Wikidata item does not have a media statement yet
        (prefereably there is only one single media file per item/type)

Media file metadata:

    entity media info <- labels/decriptions/statements <- depicts <- item number <- properties <- qualifiers

Known problems:

    Very few media files have a depicts statement (see prerequisites)
        Idea: missing depicts query

    Updated items might require manual validation, to correct any anomalies;
    see https://www.wikidata.org/wiki/Special:Contributions

    Category redirects are not traversed (resolve manually).

    Wikidata redirects are recognized, but are not retroactively updated in the SDC statements.

    Deleted Wikidata item page, while Wikimedia Commons SDC P180 staement is still there;
    this problem is not retroactively resolved.

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
pgmid = '2023-01-02 (gvp)'	            # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'
transcmt = '#pwb Add image from SDC'

# Constants
BOTFLAG = True

# Namespaces
MAINNAMESPACE = 0
FILENAMESPACE = 6

# Properties
VIDEOPROP = 'P10'
IMAGEPROP = 'P18'
INSTANCEPROP = 'P31'
FLAGPROP = 'P41'
AUTHORPROP = 'P50'
AUDIOPROP = 'P51'
COATOFARMSPROP = 'P94'
EDITORPROP = 'P98'
SIGNATUREPROP = 'P109'
PUBLISHERPROP = 'P123'
LOGOPROP = 'P154'
DEPICTSPROP = 'P180'
COLLECTIONPROP = 'P195'
ISBNPROP = 'P212'
SUBCLASSPROP = 'P279'
DOIPROP = 'P356'
PRONUNCIATIONPROP = 'P443'
RESTRICTPROP = 'P518'
WORKPROP = 'P629'
EDITIONPROP = 'P747'
VOYAGEBANPROP = 'P948'
ISBN10PROP = 'P957'
SPOKENTEXTPROP = 'P989'
VOICERECPROP = 'P990'
PDFPROP = 'P996'
MIMEPROP = 'P1163'
GRAVEPROP = 'P1442'
PLACENAMEPROP = 'P1766'
PLAQUEPROP = 'P1801'
AUTHORNAMEPROP = 'P2093'
ICONPROP = 'P2910'
NIGHTVIEWPROP = 'P3451'
WINTERVIEWPROP = 'P5252'
CHIEFEDITORPROP = 'P5769'
INTERIORPROP = 'P5775'
DIGITALREPROPROP = 'P6243'
VERSOPROP = 'P7417'
RECTOPROP = 'P7418'
FRAMEWORKPROP = 'P7420'
VIEWPROP = 'P8517'
FAVICONPROP = 'P8972'
AERIALVIEWPROP = 'P8592'
COLORWORKPROP = 'P10093'

# Instances
HUMANINSTANCE = 'Q5'
YEARINSTANCE = 'Q3186692'
CATEGORYINSTANCE = 'Q4167836'
DISAMBUGINSTANCE = 'Q4167410'
RULESINSTANCE = 'Q4656150'
TEMPLATEINSTANCE = 'Q11266439'
LISTPAGEINSTANCE = 'Q13406463'
WMPROJECTINSTANCE = 'Q14204246'
NAMESPACEINSTANCE = 'Q35252665'
HELPPAGEINSTANCE = 'Q56005592'

# Media type groups
base_media = {AUDIOPROP, IMAGEPROP, VIDEOPROP}
human_class = HUMANINSTANCE
object_class = {INSTANCEPROP, SUBCLASSPROP}

published_work = {
    AUTHORPROP,
    AUTHORNAMEPROP,
    CHIEFEDITORPROP,
    DOIPROP,
    EDITIONPROP,
    EDITORPROP,
    ISBNPROP,
    ISBN10PROP,
    PUBLISHERPROP,
    WORKPROP,
}

# Identify small images
small_image = {
    FAVICONPROP,
    ICONPROP,
    LOGOPROP,
    SIGNATUREPROP,
    VOYAGEBANPROP,
}

# Unwanted instances
skipped_instances = {
    CATEGORYINSTANCE,
    DISAMBUGINSTANCE,
    HELPPAGEINSTANCE,
    LISTPAGEINSTANCE,
    NAMESPACEINSTANCE,
    RULESINSTANCE,
    TEMPLATEINSTANCE,
    YEARINSTANCE,
    WMPROJECTINSTANCE,
}

# Map image instance to media types
image_types = {
    'Q2130': 'favicon',
    'Q3302947': 'audio',        # audio recording
    'Q4650799': 'audio',        # adio
    'Q14659': 'coatofarms',
    'Q14660': 'flag',
    'Q33582': 'face',           # Mugshot
    'Q138754': 'icon',
    'Q173387': 'grave',
    'Q178659': 'illustration',
    'Q184377': 'pronunciation',
    'Q188675': 'signature',
    'Q266488': 'placename',     # town name
    'Q653542': 'spokentext',    # audio description; diffrent from Q110374796 (spoken text)
    'Q721747': 'plaque',
    'Q860792': 'framework',
    'Q860861': 'sculpture',     # sculpture
    'Q904029': 'face',          # ID card
    'Q928357': 'sculpture',     # bronze sculpture
    'Q1153655': 'aerialview',
    'Q1886349': 'logo',
    'Q1969455': 'placename',    # street name
    'Q2032225': 'placename',    # German place name
    'Q2075301': 'view',
    'Q3362196': 'placename',    # French place name
    'Q9305022': 'recto',
    'Q9368452': 'verso',
    'Q11060274': 'prent',
    'Q17172850': 'voicerec',    # voice
    'Q22920576': 'wvbanner',
    'Q28333482': 'nightview',
    'Q31807746': 'interior',
    'Q53702817': 'voicerec',    # voice recording
    'Q54819662': 'winterview',
    'Q55498668': 'placename',   # place name
    'Q98069877': 'video',
    'Q109592922': 'colorwork',
    # others...
}

# Mapping of SDC media MIME types to Wikidata property
# Should be extended for new MIME types -> will generate a KeyError
media_props = {
    #'application': ?,          # Requires subtype lookup, e.g. 'pdf'
    'aerialview': AERIALVIEWPROP,
    'audio': AUDIOPROP,
    'colorwork': COLORWORKPROP,
    'coatofarms': COATOFARMSPROP,
    'face': IMAGEPROP,          # Would need special property
    'favicon': FAVICONPROP,
    'flag': FLAGPROP,
    'framework': FRAMEWORKPROP,
    'grave': GRAVEPROP,
    'icon': ICONPROP,
    'illustration': IMAGEPROP,  # Would need special property
    'image': IMAGEPROP,
    'interior': INTERIORPROP,
    'logo': LOGOPROP,
    'nightview': NIGHTVIEWPROP,
    'oga': AUDIOPROP,
    'ogg': AUDIOPROP,
    'ogv': VIDEOPROP,
    'pdf': PDFPROP,
    'placename': PLACENAMEPROP,
    'plaque': PLAQUEPROP,
    'prent': IMAGEPROP,         # Would need special property
    'pronunciation': PRONUNCIATIONPROP,
    'recto': RECTOPROP,
    'sculpture': DIGITALREPROPROP,
    'signature': SIGNATUREPROP,
    'spokentext': SPOKENTEXTPROP,
    'verso': VERSOPROP,
    'video': VIDEOPROP,
    'view': VIEWPROP,
    'voicerec': VOICERECPROP,
    'winterview': WINTERVIEWPROP,
    'wvbanner': VOYAGEBANPROP,
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


def prop_is_in_list(statement_list, proplist) -> bool:
    """
    Verify if a property is used for a statement

    Parameters:

        statement_list: Statement list
        proplist:       List of properties (string)

    Returns:

    Boolean (True when match)
    """
    for prop in proplist:
        if prop in statement_list:
            isinlist = True
            break
    else:
        isinlist = False
    return isinlist


mainlang = os.getenv('LANG', 'en').split('_')[0]      # Default description language

# Get parameters
pgmnm = sys.argv.pop(0)
pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))

# Connect to databases
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

# Loop through the list of media files
for page in page_list:
    try:
        # We only accept the File namespace
        media_identifier = 'M' + str(page.pageid)
        if page.namespace() != FILENAMESPACE:
            pywikibot.log('Skipping {} {}'.format(media_identifier, page.title()))
            continue

        # Get media SDC data
        request = site.simple_request(action='wbgetentities', ids=media_identifier)
        row = request.submit()

        # Catch errors
        sdc_data = row.get('entities').get(media_identifier)
        # title, labels, descriptions, statements <- depicts
        ## {'pageid': 125667911, 'ns': 6, 'title': 'File:Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot.pdf', 'lastrevid': 707697714, 'modified': '2022-11-18T20:06:23Z', 'type': 'mediainfo', 'id': 'M125667911', 'labels': {'nl': {'language': 'nl', 'value': 'Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot'}, 'en': {'language': 'en', 'value': 'Wikidata ISBN book description with ISBNlib and Pywikibot'}, 'fr': {'language': 'fr', 'value': 'Description du livre Wikidata ISBN avec ISBNlib et Pywikibot'}, 'de': {'language': 'de', 'value': 'Wikidata ISBN Buchbeschreibung mit ISBNlib und Pywikibot'}, 'es': {'language': 'es', 'value': 'Descripción del libro de Wikidata ISBN con ISBNlib y Pywikibot'}}, 'descriptions': {}, 'statements': []}

        # Missing info: how to get the file size?

        statement_list = sdc_data.get('statements')
        if not statement_list:
            # Old images do not have statements
            pywikibot.log('No statements for {} {}'
                          .format(media_identifier, page.title()))
            continue

        # This program runs on the basis of depects statements
        depict_list = statement_list.get(DEPICTSPROP)
        if not depict_list:
            # Please add depict statements for each media file
            pywikibot.log('No depicts for {} {}'.format(media_identifier, page.title()))
            continue

        # We now have valid depicts statements, so we can obtain the media type
        # Get the default file type; can be overruled by depict statements
        file_type = ['image']       # initial default
        mime_list = statement_list.get(MIMEPROP)
        if mime_list:
            # Default: image
            # Normally we only have one single MIME type
            mime_type = mime_list[0]['mainsnak']['datavalue']['value']
            file_type = mime_type.split('/')

            if file_type[0] == 'application':
                # Determine application default media type
                file_type = [media_props[file_type[1]]]

        item_list = []
        preferred = False
        for depict in depict_list:
            # Loop through the list of SDC P180 statements,
            # by order of priority
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
                # Special image type
                file_type = [image_types[qnumber]]
            elif preferred:
                # Keep the first preferred item
                pass
            elif depict['rank'] == 'preferred':
                # Overrule normal items when at least one preferred
                preferred = True
                item_list = [qnumber]
            elif not ('qualifiers' in depict and is_in_list(depict['qualifiers'], RESTRICTPROP)):
                # Skip "applies to" qualifiers
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

        # Could possibly fail with KeyError with non-recognized media types
        # In that case the new media type should be added to the list
        media_type = media_props[file_type[0]]

        # Filter low resolution sizes (caveat: logo and other small images)
        # Skip low quality images (low resolution, which are not identified as small_image)

        # Check if the media file is already used on another Wikidata item
        itempage = pywikibot.FilePage(repo, page.title())
        image_used = False

        # This includes e.g. P10 video, P18 image, P51 audio, etc.
        # Possibly other links?
        for file_ref in pg.FileLinksGenerator(itempage):
            if file_ref.namespace() == MAINNAMESPACE:
                # We only take Qnumbers into account (primary namespace)
                # e.g. ignore descriptive pages
                image_used = True
                pywikibot.log('{} {} is used by {}'
                              .format(media_identifier, page.title(), file_ref.title()))
        if image_used:
            # Image is already used, so skip (avoid flooding)
            continue

        description_list = sdc_data.get('descriptions')
        if description_list != {}:
            ## ?? Why is descriptions always empty? How could it be registered?
            # The GUI only allows to register labels?
            # Shouldn't Wiki text descriptions be digitized?
            """
{'en': {'language': 'en', 'value': 'Belgian volleyball player'}, 'it': {'language': 'it', 'value': 'pallavolista belga'}}
Redundant media M70757539 File:Wout Wijsmans (Legavolley 2012).jpg
            """
            pywikibot.log(description_list)

        for qnumber in item_list:
            # Loop through the target Wikidata items to find the first match
            item = pywikibot.ItemPage(repo, qnumber)

            try:
                item.get()
            except pywikibot.exceptions.IsRedirectPageError:
                # Resolve a single redirect error
                item = item.getRedirectTarget()
                pywikibot.warning('Item {} redirects to {}'.format(qnumber, item.getID()))
                qnumber = item.getID()

                # Should update SDC statement for redirect

            if media_type in item.claims:
                # Preferably one single image per Wikidata item (avoid pollution)
                continue
            elif not prop_is_in_list(item.claims, object_class):
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
                    and is_in_list(item.claims[INSTANCEPROP], human_class)
                    and media_type not in base_media):
                continue
            elif prop_is_in_list(item.claims, published_work):
                # We skip publications (good relevant images are extremely rare)
                continue
                # Proactive constraint check (how could we do this?)
                # Note that we unconditionally accept all P279 subclasses
            elif item.namespace() == MAINNAMESPACE:
                # Only register media files to items in the main namespace, otherwise skip
                try:
                    # Possibly no language label available
                    pywikibot.warning('{} ({}): add media ({}) {} {}'
                                      .format(item.labels[mainlang],
                                              qnumber, media_type, media_identifier, page.title()))
                except:
                    pywikibot.warning('({}): add media ({}) {} {}'
                                      .format(qnumber, media_type, media_identifier, page.title()))

                # Add media statement to the item, and process the next media file
                claim = pywikibot.Claim(repo, media_type)
                claim.setTarget(page)
                item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                break
        else:
            # All media item slots were already taken
            # Maybe add more appropriate depicts statements, and then rerun the script?
            pywikibot.log('Redundant media {} {}'.format(media_identifier, page.title()))

    # Log errors
    except Exception as error:
        pywikibot.log('Error processing {} {}, {}'.format(media_identifier, page.title(), error))
        #raise      # Uncomment to debug
