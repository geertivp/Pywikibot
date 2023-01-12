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
Depending on the quality of the SDC P180 statements, manual corrections might be required,
both in Wikidata, and in Wikimedia Commons SDC statements.
Wikimedia Commons is not automatically updated.

Parameters:

    P1: Wikimedia Commons category (subcatergories are processed recursively)
        Can be a Wikimedia Commons category URL

    If no parameters are available,
    a list of media filenames is read via stdin;
    one filename per line.

Options:

    -debug: detailed logging (logs/pwb-bot.log)
    -v:     verbatim mode (extra logging)
            To see the progress, it is advised to always use -v

Examples:

    pwb add_image_from_sdc 'Images from Wiki Loves Heritage Belgium in 2022'

    https://www.wikidata.org/wiki/Q98141338
    https://www.wikidata.org/w/index.php?title=Q140&diff=1799300865&oldid=1796952109

    Missing metadata:

    https://commons.wikimedia.org/wiki/Category:Unidentified_subjects

Prerequisites:

    Wikimedia Commons media files are linked to Wikidata items.
    The script relies on the availability of SDC P180 (depict) statements.
    Adding SDC P180 (depict) should be encouraged.
    Register the SDC depicts statements in Wikimedia Commons:
        immediately after the media upload,
        can be generated with the ISA Tool, as part of a campaign,
        might be done with some Toolforge tool (unexisting yet?),
        via AC/DC,
        or manually adding depicts statements via the GUI
    If there are no SDC P180 statements, no updates in Wikidata are performed.
    The metadata MIMI type is recognized (default image/jpeg)
    Please add a proper SDC MIMI type when needed
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
    For artist items in principle their work is not added.

Functionality:

    This script follows the general Wikidata guidelines (e.g. one single image statement).

    Handle special image properties; e.g.:
        P154    logo
        P1442   grave
        P5775   interior

Error messages:

    Add media file:                     Registering a new media file.
    Error processing:                   Generic error occurred
    File contains missing revisions:    Some revisions were deleted by a moderator
    File is used by:                    Do not register the same media file multiple times.
    Item redirects to:                  Item is redirected; correct item is used (should still be fixed in SDC)
    Media belongs to collection:        Skipping GLAM collections that often depicts art work parts;
                                        without a preferred qualifier there is a risk for wrong registrations.
    Media file too small                Resolution is too low
    No depicts for file:                No depict statements found; no item number available.
                                        We should encorage to add depicts statements;
                                        at least one with preferred status.
    No statements for file:             Only labels; no statements, so no depicts.
    Redundant media file:               All media slots already taken, avoid having multiple media files;
                                        maybe add more depicts statements to find more items.
    Skipping for restriction:           Item is not taken into account, because of P518 restriction
    Skipping page:                      Page doesn't belong to the File namespace.

Use cases:

    Load files via P1 Wikimedia Commons category

    Process the images from a Wiki Loves Heritage campaign

    Paste the list of media files via stdin
        Make a list of user uploads via AutoWikiBrowser (AWB)

    Run the program
        Put all the "No depicts" media files in AWB to add depicts statements
        Rerun the program

    Run the program
        Put all the "Redundant media" files in AWB to add depicts statements
        Rerun the program

    Follow the category (tree) starting from a media file

To do:

    Proactive constraint checking
        How?

    Update SDC item redirect

Algorithm:

    List all files in the Wikimedia Commons category (recursively)
    As an alternative, the list of files is read from stdin.
    Verify if there is any SDC data registered with the media files
    Obtain any SDC P180 statement (depicts)
    Apply eligibility criteria:
        Skip collection items not having a preferred qualifier
        Skip artist work for artists
        Skip the media file if it is already used on wikidata
        Skip low quality images (low resolution)
    Determine the media type (multiple rules; default: image)
    Obtain the corresponding Wikidata items
        Preferred P180 statement overrule normal items
        Handle (single) redirected items
    Merge the media file to the corresponding Wikidata item
        If the Wikidata item does not have a media statement yet
        (prefereably there is only one single media file per item/type)

Media file metadata:

    media file info <- identifier

    media file info <- mime

    media file info <- size

    media file wikidata use <- identifier

    media identity info <- labels/decriptions/statements

    statements <- collection <- item number

    statements <- depicts <- item number <- qualifiers <- properties <- item number

    statements <- mime

    statements <- reproduction <- item number

Known problems:

    Very few media files have a depicts statement (see prerequisites)
        Idea: missing depicts query

    Updated items might require manual validation, to correct any anomalies;
    see https://www.wikidata.org/wiki/Special:Contributions

    Category redirects are not traversed (resolve manually).

    Wikidata redirects are recognized,
    but are not retroactively updated in the SDC statements.

    Deleted Wikidata item pages,
    while Wikimedia Commons SDC P180 statement is still there;
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
            Move the media assignment
            
    File contains missing revisions:
        Some revisions were deleted (by a moderator);
        you can ignore this warning.

    Sleeping for 0.2 seconds, 2022-12-17 11:48:51

    Pausing due to database lag: Waiting for 10.64.32.12: 5.1477 seconds lagged.
    Sleeping for 5.0 seconds, 2022-12-25 10:48:31

    Fatal error:
    RecursionError: maximum recursion depth exceeded while calling a Python object
    Multiple timeout problems... should/could we set a hard timeout?

    Fatal Python error: Cannot recover from stack overflow.
    Subsequently process sub-categories

    https://www.wikidata.org/wiki/Property:P6802
    Related image (how to identify?)

    Missing properties:
        music recording property is missing?
        music recording is not a media file (subset of audio)
        music video (P6718) is not a media file (subset of video)

Documentation:

    https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html

    https://buildmedia.readthedocs.org/media/pdf/pywikibot/stable/pywikibot.pdf

    https://byabbe.se/2020/09/15/writing-structured-data-on-commons-with-python
    Prototype SDC queries

    https://be.wikimedia.org/wiki/ISA_Tool
    Tool to generate SDC P180 depict statements and captions (SDC labels).

    https://commons.wikimedia.org/wiki/Help:Gadget-ACDC

    https://www.mediawiki.org/wiki/Manual:Pywikibot/pagegenerators.py

    https://phabricator.wikimedia.org/T326510
    Get file size and MIME type

Resources:

    Uses 3% CPU on a modern laptop
    Requires internet connection

Related projects:

    Add SDC P180 depicts statement for Wikdata media file statements (reverse logic)
        Should be even more easy... 1:1 relationship...
        We should have a separate script, based on a SPARQL query.

    https://phabricator.wikimedia.org/T326510
    How to obtain the resolution and the image size from an image via Pywikibot

    https://www.wikidata.org/wiki/Wikidata:Database_reports/Constraint_violations/P18

Author:

	Geert Van Pamel, 2022-12-10, MIT License, User:Geertivp

"""

import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import sys		    	# System: argv, exit (get the parameters, terminate the program)
from pywikibot import pagegenerators as pg

# Global variables
modnm = 'Pywikibot add_image_from_sdc'  # Module name (using the Pywikibot package)
pgmid = '2023-01-12 (gvp)'	            # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'
recurse_list = True

# Constants
BOTFLAG = True          # This script requires a bot flag
MINFILESIZE = 75000     # Minimum file size

# Namespace IDs
MAINNAMESPACE = 0
FILENAMESPACE = 6

# Instances
HUMANINSTANCE = 'Q5'
GENREINSTANCE = 'Q483394'
YEARINSTANCE = 'Q3186692'
DISAMBUGINSTANCE = 'Q4167410'
CATEGORYINSTANCE = 'Q4167836'
RULESINSTANCE = 'Q4656150'
TEMPLATEINSTANCE = 'Q11266439'
LISTPAGEINSTANCE = 'Q13406463'
WMPROJECTINSTANCE = 'Q14204246'
NAMESPACEINSTANCE = 'Q35252665'
HELPPAGEINSTANCE = 'Q56005592'

# Properties
VIDEOPROP = 'P10'
MAPPROP = 'P15'
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
LOCATORMAPPROP = 'P242'
SUBCLASSPROP = 'P279'
DOIPROP = 'P356'
PRONUNCIATIONPROP = 'P443'
RESTRICTIONPROP = 'P518'
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
PARTITUREPROP = 'P3030'
NIGHTVIEWPROP = 'P3451'
WINTERVIEWPROP = 'P5252'
CHIEFEDITORPROP = 'P5769'
INTERIORPROP = 'P5775'
REPROPROP = 'P6243'
VERSOPROP = 'P7417'
RECTOPROP = 'P7418'
FRAMEWORKPROP = 'P7420'
VIEWPROP = 'P8517'
FAVICONPROP = 'P8972'
AERIALVIEWPROP = 'P8592'
COLORWORKPROP = 'P10093'

# Instance classes
human_class = HUMANINSTANCE

# Unwanted instances
skipped_instances = {
    CATEGORYINSTANCE,
    DISAMBUGINSTANCE,
    GENREINSTANCE,
    HELPPAGEINSTANCE,
    LISTPAGEINSTANCE,
    NAMESPACEINSTANCE,
    RULESINSTANCE,
    TEMPLATEINSTANCE,
    YEARINSTANCE,
    WMPROJECTINSTANCE,
}

# Media type groups
base_media = {AUDIOPROP, IMAGEPROP, VIDEOPROP}
object_class = {INSTANCEPROP, SUBCLASSPROP}

# Published work properties
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
small_images = {
    FAVICONPROP,
    ICONPROP,
    LOGOPROP,
    SIGNATUREPROP,
    VOYAGEBANPROP,
}

# Map media instance to media types
image_types = {
    'Q2130': 'favicon',
    'Q4006': 'map',
    'Q14659': 'coatofarms',
    'Q14660': 'flag',
    'Q33582': 'face',           # Mugshot
    'Q42332': 'pdf',
    'Q49848': 'document',
    'Q138754': 'icon',
    'Q173387': 'grave',
    'Q178659': 'illustration',
    'Q184377': 'pronunciation',
    'Q187947': 'partiture',
    'Q188675': 'signature',
    'Q219423': 'wallpainting',
    'Q266488': 'placename',     # town name
    'Q606876': 'pancarte',
    'Q87167': 'manuscript',
    'Q226697': 'perkament',
    'Q653542': 'spokentext',    # audio description; diffrent from Q110374796 (spoken text)
    'Q721747': 'plaque',        # gedenkplaat
    'Q860792': 'framework',
    'Q860861': 'sculpture',     # sculpture
    'Q904029': 'face',          # ID card
    'Q928357': 'sculpture',     # bronze sculpture
    'Q1153655': 'aerialview',
    'Q1885014': 'plaque',       # herdenkingsmonument
    'Q1886349': 'logo',
    'Q1969455': 'placename',    # street name
    'Q2032225': 'placename',    # German place name
    'Q2075301': 'view',
    'Q3302947': 'audio',        # audio recording
    'Q3362196': 'placename',    # French place name
    'Q3381576': 'bwimage',      # black-and-white photography
    'Q4650799': 'audio',        # audio
    'Q6664848': 'locatormap',
    'Q6901463': 'bwimage',      # black-and-white photography (redirect)
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
    'Q76419950': 'pancarte',
    'Q98069877': 'video',
    'Q109592922': 'colorwork',
    # others...
}

# Mapping of SDC media MIME types to Wikidata property
# Should be extended for new MIME types -> will generate a KeyError
media_props = {
    #'application': ?,          # Requires subtype lookup, e.g. 'ogg', 'pdf'
    'aerialview': AERIALVIEWPROP,
    'audio': AUDIOPROP,
    'bwimage': IMAGEPROP,       # Would require special property
    'colorwork': COLORWORKPROP,
    'coatofarms': COATOFARMSPROP,
    'document': PDFPROP,        # Would require special property
    'face': IMAGEPROP,          # Would require special property (id card, mugshot)
    'favicon': FAVICONPROP,
    'flag': FLAGPROP,
    'framework': FRAMEWORKPROP,
    'grave': GRAVEPROP,
    'icon': ICONPROP,
    'illustration': IMAGEPROP,  # Would require special property
    'image': IMAGEPROP,
    'interior': INTERIORPROP,
    'locatormap': LOCATORMAPPROP,
    'logo': LOGOPROP,
    'map': MAPPROP,
    'nightview': NIGHTVIEWPROP,
    'oga': AUDIOPROP,
    'ogg': AUDIOPROP,           # Fewer files are video
    'ogv': VIDEOPROP,
    'manuscript': PDFPROP,      ### Would require special property
    'pancarte': IMAGEPROP,      # Would require special property
    'pdf': PDFPROP,
    'partiture': PARTITUREPROP,
    'perkament': PDFPROP,       ### Would require special property
    'placename': PLACENAMEPROP,
    'plaque': PLAQUEPROP,
    'prent': IMAGEPROP,         # Would require special property
    'pronunciation': PRONUNCIATIONPROP,
    'recto': RECTOPROP,
    'sculpture': REPROPROP,
    'signature': SIGNATUREPROP,
    'spokentext': SPOKENTEXTPROP,
    'verso': VERSOPROP,
    'video': VIDEOPROP,
    'view': VIEWPROP,
    'voicerec': VOICERECPROP,
    'wallpainting': IMAGEPROP,  # Would require special property
    'winterview': WINTERVIEWPROP,
    'wvbanner': VOYAGEBANPROP,
    # others...
}


def get_item_label(item) -> str:
    item_label = ''
    for lang in main_languages:
        if lang in item.labels:
            item_label = item.labels[lang]
            break
    return item_label


def get_item(qnumber):
    item = pywikibot.ItemPage(repo, qnumber)

    try:
        item.get()
    except pywikibot.exceptions.IsRedirectPageError:
        # Resolve a single redirect error
        item = item.getRedirectTarget()
        label = get_item_label(item)
        pywikibot.warning('Item {} ({}) redirects to {}'
                          .format(label, qnumber, item.getID()))
        ## qnumber = item.getID()   ## Python doesn't know by call by reference...
    return item


def get_sdc_item(sdc_data):
    qnumber = sdc_data['datavalue']['value']['id']

    # Get item
    item = get_item(qnumber)
    if qnumber != item.getID():
        ## Retroactively update the SDC statement for redirect
        ## ['datavalue']['value']['id']
        qnumber = item.getID()   ## Python doesn't know by call by reference...
    return item


def get_sdc_label(label_list) -> str:
    """
{'en': {'language': 'en', 'value': 'Belgian volleyball player'}, 'it': {'language': 'it', 'value': 'pallavolista belga'}}
Redundant media M70757539 File:Wout Wijsmans (Legavolley 2012).jpg
    """
    label = ''
    if label_list:
        for lang in main_languages:
            if lang in label_list:
                label = label_list[lang]['value']
                break
    return label


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


# Get label language
mainlang = os.getenv('LANG', os.getenv('LANGUAGE', 'en')).split('_')[0]
main_languages = ['nl', 'fr', 'en', 'de', 'es', 'it']
if mainlang in main_languages:
    main_languages.remove(mainlang)
main_languages.insert(0, mainlang)

# Get parameters
pgmnm = sys.argv.pop(0)
pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))

# Connect to databases
site = pywikibot.Site('commons')
repo = site.data_repository()

# Get list of media files from input parameters (either P1 or stdin)
page_list = []
if sys.argv:
    # Get Wikimedia Commons page list from category P1
    subject = sys.argv.pop(0)
    slashpos = subject.rfind('/')
    if slashpos > 0:
        subject = subject[slashpos + 1:]

    # Get recursive image list from category
    try:
        cat_list = pywikibot.Category(site, subject)
        pywikibot.info(cat_list.title())
        pywikibot.info(cat_list.categoryinfo)
        page_list = pg.CategorizedPageGenerator(cat_list, recurse=recurse_list)
    except Exception as error:
        pywikibot.critical(error)
else:
    # Read Wikimedia Commons page list from stdin
    inputfile = sys.stdin.read()
    input_list = sorted(set(inputfile.split('\n')))
    for subject in input_list:
        # Get filename
        slashpos = subject.rfind('/')
        if slashpos > 0:
            subject = subject[slashpos + 1:]
        if subject:
            try:
                page_list.append(pywikibot.FilePage(site, subject))
            except Exception as error:
                pywikibot.error(error)
    pywikibot.info('{:d} media files in list'.format(len(page_list)))

# Loop through the list of media files
for page in page_list:
    try:
        # We only accept the File namespace
        media_identifier = 'M' + str(page.pageid)
        ## https://commons.wikimedia.org/wiki/Special:EntityPage/M63763537
        ## https://commons.wikimedia.org/entity/M63763537
        if page.namespace() != FILENAMESPACE:
            pywikibot.info('Skipping {} {}'.format(media_identifier, page.title()))
            continue

        # Get standaard media file information
        file_info = page.latest_file_info.__dict__
        """
        file_info.keys()
dict_keys(['timestamp', 'user', 'size', 'width', 'height', 'comment', 'url', 'descriptionurl', 'descriptionshorturl', 'sha1', 'metadata', 'mime'])

        file_info
{'timestamp': Timestamp(2017, 10, 31, 10, 14, 18), 'user': 'Rama', 'size': 2022429, 'width': 3315, 'height': 4973, 'comment': '{{User:Rama/Wikimedian portraits|WikidataCon 2017}}\n\n{{Information\n|Description=[[User:Geertivp]] at WikidataCon 2017\n|Source={{Own}}\n|Date=\n|Author={{u|Rama}}\n|Permission={{self|Cc-by-sa-3.0-fr|CeCILL|attribution=Rama}}\n|other_versions=\n}}\n\n[[Category...', 'url': 'https://upload.wikimedia.org/wikipedia/commons/4/4a/Geert_Van_Pamel-IMG_1572.JPG', 'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Geert_Van_Pamel-IMG_1572.JPG', 'descriptionshorturl': 'https://commons.wikimedia.org/w/index.php?curid=63763537', 'sha1': 'a157b85ec18e5718fe2d8e5c0d38063a4564d7f0', 'metadata': [{'name': 'ImageWidth', 'value': 3315}, {'name': 'ImageLength', 'value': 4973}, {'name': 'Make', 'value': 'Canon'}, {'name': 'Model', 'value': 'Canon EOS 5D Mark II'}, {'name': 'Orientation', 'value': 1}, {'name': 'XResolution', 'value': '72/1'}, {'name': 'YResolution', 'value': '72/1'}, {'name': 'ResolutionUnit', 'value': 2}, {'name': 'Software', 'value': 'digiKam-4.14.0'}, {'name': 'DateTime', 'value': '2017:10:28 11:09:18'}, {'name': 'YCbCrPositioning', 'value': 2}, {'name': 'ExposureTime', 'value': '1/250'}, {'name': 'FNumber', 'value': '28/10'}, {'name': 'ExposureProgram', 'value': 3}, {'name': 'ISOSpeedRatings', 'value': 3200}, {'name': 'ExifVersion', 'value': '0221'}, {'name': 'DateTimeOriginal', 'value': '2017:10:28 11:09:18'}, {'name': 'DateTimeDigitized', 'value': '2017:10:28 11:09:18'}, {'name': 'ComponentsConfiguration', 'value': '\n#1\n#2\n#3\n#0'}, {'name': 'ShutterSpeedValue', 'value': '524288/65536'}, {'name': 'ApertureValue', 'value': '196608/65536'}, {'name': 'ExposureBiasValue', 'value': '0/1'}, {'name': 'MeteringMode', 'value': 5}, {'name': 'Flash', 'value': 16}, {'name': 'FocalLength', 'value': '200/1'}, {'name': 'SubSecTime', 'value': '49'}, {'name': 'SubSecTimeOriginal', 'value': '49'}, {'name': 'SubSecTimeDigitized', 'value': '49'}, {'name': 'FlashPixVersion', 'value': '0100'}, {'name': 'FocalPlaneXResolution', 'value': '5616000/1459'}, {'name': 'FocalPlaneYResolution', 'value': '3744000/958'}, {'name': 'FocalPlaneResolutionUnit', 'value': 2}, {'name': 'CustomRendered', 'value': 0}, {'name': 'ExposureMode', 'value': 0}, {'name': 'WhiteBalance', 'value': 0}, {'name': 'SceneCaptureType', 'value': 0}, {'name': 'GPSVersionID', 'value': '0.0.2.2'}, {'name': 'PixelXDimension', 'value': '3315'}, {'name': 'PixelYDimension', 'value': '4973'}, {'name': 'MEDIAWIKI_EXIF_VERSION', 'value': 1}], 'mime': 'image/jpeg'}
        """

        # Get mime type
        file_type = ['image']       # Initial default
        if 'mime' in file_info:
            mime_type = file_info['mime']
            file_type = mime_type.split('/')
            if file_type[0] == 'application':
                file_type = [file_type[1]]

        # Get the file size (resolution)
        file_size = 0
        if 'size' in file_info:
            file_size = file_info['size']

        # Get media SDC data
        request = site.simple_request(action='wbgetentities', ids=media_identifier)
        row = request.submit()

        sdc_data = row.get('entities').get(media_identifier)
        # Key attributes: pageid, ns, title, labels, descriptions, statements <- depicts, MIME type
        ## {'pageid': 125667911, 'ns': 6, 'title': 'File:Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot.pdf', 'lastrevid': 707697714, 'modified': '2022-11-18T20:06:23Z', 'type': 'mediainfo', 'id': 'M125667911', 'labels': {'nl': {'language': 'nl', 'value': 'Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot'}, 'en': {'language': 'en', 'value': 'Wikidata ISBN book description with ISBNlib and Pywikibot'}, 'fr': {'language': 'fr', 'value': 'Description du livre Wikidata ISBN avec ISBNlib et Pywikibot'}, 'de': {'language': 'de', 'value': 'Wikidata ISBN Buchbeschreibung mit ISBNlib und Pywikibot'}, 'es': {'language': 'es', 'value': 'Descripción del libro de Wikidata ISBN con ISBNlib y Pywikibot'}}, 'descriptions': {}, 'statements': []}

        statement_list = sdc_data.get('statements')
        if not statement_list:
            # Old images do not have statements
            pywikibot.info('No statements for {} {} {}'
                           .format(file_type[0], media_identifier, page.title()))
            continue

        # We now have valid depicts statements, so we can obtain the media type;
        # can be overruled by subsequent depict statements
        mime_list = statement_list.get(MIMEPROP)
        if mime_list:
            # Default: image
            # Normally we only have one single MIME type
            mime_type = mime_list[0]['mainsnak']['datavalue']['value']
            file_type = mime_type.split('/')
            if file_type[0] == 'application':
                file_type = [file_type[1]]

        # This program runs on the basis of depects statements
        depict_list = statement_list.get(DEPICTSPROP)
        if not depict_list:
            # A lot of media files do not have depict statements.
            # Please add depict statements for each media file.
            pywikibot.log('No depicts for {} {} {}'
                          .format(file_type[0], media_identifier, page.title()))
            continue

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
            item = get_sdc_item(depict['mainsnak'])
            qnumber = item.getID()

            if qnumber in image_types:
                # Special image type
                file_type = [image_types[qnumber]]
            elif depict['rank'] == 'preferred':
                # Overrule normal items
                if not preferred:
                    item_list = []
                item_list.append(item)
                preferred = True
            elif ('qualifiers' in depict
                    and prop_is_in_list(depict['qualifiers'], RESTRICTIONPROP)):
                """
{'P462': [{'snaktype': 'value', 'property': 'P462', 'hash': '4af9c81cc458bf6b99699673fd9268b43ad0c4d4', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 23445, 'id': 'Q23445'}, 'type': 'wikibase-entityid'}}]}
                """
                # Ignore items with "applies to" qualifiers
                restricted_item = get_sdc_item(depict['qualifiers'][RESTRICTIONPROP][0])
                pywikibot.info('Skipping qualifier ({}) for {} ({}) for {} {} {}'
                               .format(RESTRICTIONPROP,
                                       get_item_label(restricted_item), restricted_item.getID(),
                                       file_type[0], media_identifier, page.title()))
            elif not preferred:
                # Add a normal ranked item to the list
                item_list.append(item)

        # Add reproduction in museum collection
        repro_list = statement_list.get(REPROPROP)
        if repro_list:
            preferred = True
            repro_item = get_sdc_item(repro_list[0]['mainsnak'])
            item_list.insert(0, repro_item)

        # Could possibly fail with KeyError with non-recognized media types
        # In that case the new media type must be added to the list
        media_type = media_props[file_type[0]]

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
                # Show connected item number
                item_ref = get_item(file_ref.title())
                pywikibot.info('{} ({}) {} {} is used by {} ({})'
                               .format(file_type[0], media_type,
                                       media_identifier, page.title(),
                                       get_item_label(item_ref), item_ref.getID()))
        if image_used:
            # Image is already used, so skip (avoid flooding)
            continue

        collection_list = statement_list.get(COLLECTIONPROP)
        if collection_list and not (preferred or len(depict_list) == 1):
            # Depict statements for GLAM collections
            # generally describe parts of painting objects;
            # skip them, unless there is a preferred statement describing the artwork itself.
            collection_item = get_sdc_item(collection_list[0]['mainsnak'])
            pywikibot.info('{} ({}) {} {} belongs to collection {} ({}), and not preferred'
                           .format(file_type[0], media_type,
                                   media_identifier, page.title(),
                                   get_item_label(collection_item), collection_item.getID()))
            continue

        ## Could also filter on minimum image resolution
        # Filter low resolution sizes (caveat: logo and other small images)
        # Skip low quality images (low resolution, which are not identified as small_images)
        if (file_size > 0
                and file_size < MINFILESIZE
                and media_type not in small_images):
            pywikibot.info('{} ({}) {} {} size {} too small'
                           .format(file_type[0], media_type,
                                   media_identifier, page.title(),
                                   file_size))
            continue

        for item in item_list:
            # Loop through the target Wikidata items to find the first match
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
            elif item.namespace() != MAINNAMESPACE:
                # Only register media files to items in the main namespace, otherwise skip
                continue

                ## Proactive constraint check (how could we do this?)
                # Does there exist a method?

                # Note that we unconditionally accept all P279 subclasses
            else:
                pywikibot.warning('{} ({}): add {} ({}) {} {}'
                                  .format(get_item_label(item), item.getID(),
                                          file_type[0], media_type,
                                          media_identifier, page.title()))

                # Get media label
                media_label = get_sdc_label(sdc_data.get('labels'))
                if media_label:
                    pywikibot.info(media_label)

                # Get media description
                media_description = get_sdc_label(sdc_data.get('descriptions'))
                ## ?? Why is descriptions nearly always empty? How could it be registered?
                # The GUI only allows to register labels?
                # Shouldn't Wiki text descriptions be digitized?
                if media_description:
                    pywikibot.log(media_description)

                # Add media statement to the item
                # Only the first matching item will be registered
                transcmt = '#pwb Add {} from SDC'.format(file_type[0])
                claim = pywikibot.Claim(repo, media_type)
                claim.setTarget(page)
                item.addClaim(claim, bot=BOTFLAG, summary=transcmt)

                # Do we require a reference?
                # Probably not; because the medium file is already referring the SDC.
                break
        else:
            # All media item slots were already taken (by other media files)
            # Maybe we could add more appropriate depicts statements,
            # and then rerun the script?
            pywikibot.info('Redundant {} ({}) {} {}'
                           .format(file_type[0], media_type,
                                   media_identifier, page.title()))
    # Log errors
    except Exception as error:
        pywikibot.error('Error processing {} {}, {}'
                        .format(media_identifier, page.title(), error))
        #raise      # Uncomment to debug
