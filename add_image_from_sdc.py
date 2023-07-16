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

    Pywikibot
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
    Wikidata disambiguation, category and other items are skipped.
    No media file is added when it is already assigned to another Wikidata item.
    No media file is added if the item holds already another media file.
    Collection media files should always have one preferred statement;
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

    (Application)
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

    (Wikimedia Commons)
    File contains missing revisions:    Ignore

    (Technical)
    Media file is not of type wikibase.ItemPage:    Wikidata inconsistency problem when assigning media file to item.
    RecursionError: maximum recursion depth exceeded while calling a Python object:
                                        Fatal error; process a smaller category (tree)

    (Network and databases)
    Remote end closed connection without response:  Intermittent network error
    Sleeping for 5.0 seconds:                       Pausing due to database lag
    Waiting 30.0 seconds before retrying:           Retry delay

Use cases:

    Load files via P1 Wikimedia Commons category

    Process the images from a Wiki Loves Heritage campaign, via the category

    Paste the list of media files via stdin
        Prepare a list of user uploads via AutoWikiBrowser (AWB)

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
    Determine the media type; multiple cascading rules:
        Default: image
        File (name) type (casted to lowercase)
        MIME type (from file or SDC)
        (selected) Instance of (P31)
        (selected) Depicts (P180)
    Obtain the corresponding Wikidata items
        Preferred P180 statement overrule normal items
        Handle (single) redirected items
    Merge the media file into the corresponding Wikidata item
        If the Wikidata item does not have a media statement yet
        (prefereably there is only one single media file per item/type)

Media file metadata:

    media file page name

    media file info <- identifier

    media file info <- mime

    media file info <- size

    media file wikidata use <- page name

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

    Category redirects are not traversed (to be resolved manually).

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

    / is wrongly truncating the category name; use %2f instead.

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

    https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
    MIME types

Resources:

    Requires an internet connection
    Uses 3% CPU on a modern laptop

Related projects:

    https://phabricator.wikimedia.org/T326510
    How to obtain the resolution and the image size from an image via Pywikibot

    https://www.wikidata.org/wiki/Wikidata:Database_reports/Constraint_violations/P18

Author:

	Geert Van Pamel, 2022-12-10, MIT License, User:Geertivp

"""

import json             # json data structures
import os               # Operating system: getenv
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
from pywikibot import pagegenerators as pg

# Global variables
modnm = 'Pywikibot add_image_from_sdc'  # Module name (using the Pywikibot package)
pgmid = '2023-07-16 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'
recurse_list = True

# Constants
BOTFLAG = True          # This script requires a bot flag
MINFILESIZE = 75000     # Minimum file size for quality images (ignore smaller images)
MINRESOLUTION = 800     # Minimum resolution (ignore smaller images)
ENLANG = 'en'

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

# Instance classes
human_class = {
    HUMANINSTANCE,
}

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
QUALIFYFROMPROP = 'P642'
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
COLLAGEPROP = 'P2716'
ICONPROP = 'P2910'
PARTITUREPROP = 'P3030'
DESIGNPLANPROP = 'P3311'
NIGHTVIEWPROP = 'P3451'
PANORAMAPROP = 'P4640'
WINTERVIEWPROP = 'P5252'
DIAGRAMPROP = 'P5555'
CHIEFEDITORPROP = 'P5769'
INTERIORPROP = 'P5775'
REPROPROP = 'P6243'
VERSOPROP = 'P7417'
RECTOPROP = 'P7418'
FRAMEWORKPROP = 'P7420'
VIEWPROP = 'P8517'
AERIALVIEWPROP = 'P8592'
FAVICONPROP = 'P8972'
COLORWORKPROP = 'P10093'

# Media type groups
human_media = {
    AUDIOPROP,
    IMAGEPROP,
    PLAQUEPROP,
    VIDEOPROP,
    VOICERECPROP,
}

object_class = {
    INSTANCEPROP,
    SUBCLASSPROP,
}

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

# Map media instance to media types
image_types = {
    'Q571': 'book',
    'Q2130': 'favicon',
    'Q4006': 'map',
    'Q14659': 'coatofarms',
    'Q14660': 'flag',
    'Q33582': 'face',           # Mugshot
    'Q42332': 'pdf',
    'Q49848': 'document',
    'Q87167': 'manuscript',
    'Q138754': 'icon',
    'Q170593': 'collage',
    'Q173387': 'grave',
    'Q178659': 'illustration',
    'Q179700': 'statue',
    'Q184377': 'pronunciation',
    'Q187947': 'partiture',
    'Q188675': 'signature',
    'Q219423': 'wallpainting',
    'Q226697': 'perkament',
    'Q266488': 'placename',     # town name
    'Q606876': 'pancarte',
    'Q653542': 'spokentext',    # audio description; diffrent from Q110374796 (spoken text)
    'Q658252': 'panoview',
    'Q721747': 'plaque',        # gedenkplaat
    'Q838948': 'artwork',
    'Q860792': 'framework',
    'Q860861': 'sculpture',     # sculpture
    'Q904029': 'face',          # ID card
    'Q959962': 'diagram',
    'Q928357': 'sculpture',     # bronze sculpture
    'Q1153655': 'aerialview',
    'Q1250322': 'digitalimage', # digital image
    'Q1885014': 'plaque',       # herdenkingsmonument
    'Q1886349': 'logo',
    'Q1969455': 'placename',    # street name
    'Q2032225': 'placename',    # German place name
    'Q2075301': 'view',
    'Q2998430': 'interior',     # interieur
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
    'Q31807746': 'interior',    # interieurinrichting
    'Q53702817': 'voicerec',    # voice recording
    'Q54819662': 'winterview',
    'Q55498668': 'placename',   # place name
    'Q76419950': 'pancarte',
    'Q98069877': 'video',
    'Q109592922': 'colorwork',
    'Q110611535': 'slides',
    # others...
}

# Map picture of to image type
file_type_of_item = {
    'Q2130': 'favicon',
    'Q4006': 'map',
    'Q14659': 'coatofarms',
    'Q14660': 'flag',
    'Q138754': 'icon',
    'Q170593': 'collage',
    'Q173387': 'grave',
    'Q188675': 'signature',
    'Q611203': 'plan',
    'Q658252': 'panoview',
    'Q721747': 'plaque',
    'Q1886349': 'logo',
    'Q2298569': 'map',
    'Q6664848': 'locatormap',
    'Q22920576': 'wvbanner',
    'Q98069877': 'video',
    'Q55498668': 'placename',
}

# Identify small images
small_images = {
    'favicon',
    'icon',
    'logo',
    'plan',
    'signature',
    'wvbanner',
}

# Mapping of SDC media MIME types to Wikidata property
# Should be extended for new MIME types -> will generate a KeyError
media_props = {
    #'application': ?,          # Requires subtype lookup, e.g. 'ogg', 'pdf'
    #'?': 'P6802',              # Related image; how to identify - see https://www.wikidata.org/wiki/Special:WhatLinksHere/Property:P6802
    'aerialview': AERIALVIEWPROP,
    'artwork': IMAGEPROP,       ## Would require special property
    'audio': AUDIOPROP,
    'book': IMAGEPROP,          ## Would require special property
    'bwimage': IMAGEPROP,       ## Would require special property
    'collage': COLLAGEPROP,
    'colorwork': COLORWORKPROP,
    'coatofarms': COATOFARMSPROP,
    'diagram': DIAGRAMPROP,
    'digitalimage': IMAGEPROP,  ## Would require special property
    'document': PDFPROP,        ## Would require special property
    'face': IMAGEPROP,          ## Would require special property (id card, mugshot)
    'favicon': FAVICONPROP,
    'flag': FLAGPROP,
    'framework': FRAMEWORKPROP,
    'grave': GRAVEPROP,
    'icon': ICONPROP,
    'illustration': IMAGEPROP,  ## Would require special property
    'image': IMAGEPROP,
    'interior': INTERIORPROP,
    'jpeg': IMAGEPROP,          ## Would require special property
    'jpg': IMAGEPROP,           ## Would require special property
    'locatormap': LOCATORMAPPROP,
    'logo': LOGOPROP,
    'map': MAPPROP,
    'mp3': AUDIOPROP,           ## Would require special property
    'nightview': NIGHTVIEWPROP,
    'oga': AUDIOPROP,
    'ogg': AUDIOPROP,           # Fewer files are video
    'mpeg': VIDEOPROP,          ## Would require special property
    'mpg': VIDEOPROP,           ## Would require special property
    'manuscript': PDFPROP,      ## Would require special property
    'ogv': VIDEOPROP,           ## Would require special property
    'pancarte': IMAGEPROP,      ## Would require special property
    'pdf': PDFPROP,
    'panoview': PANORAMAPROP,
    'partiture': PARTITUREPROP,
    'perkament': PDFPROP,       ## Would require special property
    'placename': PLACENAMEPROP,
    'plaque': PLAQUEPROP,
    'plan': DESIGNPLANPROP,
    'png': IMAGEPROP,           ## Would require special property
    'prent': IMAGEPROP,         ## Would require special property
    'pronunciation': PRONUNCIATIONPROP,
    'recto': RECTOPROP,
    'repro': IMAGEPROP,         ## Would require special property
    'sculpture': IMAGEPROP,     ## Would require special property
    'signature': SIGNATUREPROP,
    'sla': IMAGEPROP,           ## Would require special property
    'slides': PDFPROP,          ## Would require special property
    'spokentext': SPOKENTEXTPROP,
    'statue': IMAGEPROP,        ## Would require special property
    'svg': IMAGEPROP,           ## Would require special property
    'tif': IMAGEPROP,           ## Would require special property
    'verso': VERSOPROP,
    'video': VIDEOPROP,
    'view': VIEWPROP,
    'voicerec': VOICERECPROP,
    'wallpainting': IMAGEPROP,  ## Would require special property
    'webm': VIDEOPROP,
    'winterview': WINTERVIEWPROP,
    'wvbanner': VOYAGEBANPROP,
    #'xml': IMAGEPROP,           ## Would require special property
    # others...
}

# Prepare the basic part of the SDC P180 depict statement
# The numeric value needs to be added at runtime
depict_statement = {
    'claims': [{
        'type': 'statement',
        'rank': 'preferred',    # Because it comes from a Wiki text /Information template
        'mainsnak': {
            'snaktype': 'value',
            'property': DEPICTSPROP,
            'datavalue': {
                'type': 'wikibase-entityid',
                'value': {
                    'entity-type': 'item',
                    # id, numeric-id
                }
            }
        }
    }]
}


def get_file_type(filename) -> str:
    """
    Get the file type from the file name (right most '.' notation).
    """
    filetype = ''
    slashpos = filename.rfind('.')
    if slashpos > 0:
        filetype = filename[slashpos + 1:]
    return filetype.lower()


def get_item_label(item) -> str:
    """
    Get the item label.
    """
    label = ''
    for lang in main_languages:
        if lang in item.labels:
            label = item.labels[lang]
            break
    return label


def get_item(qnumber):
    """
    Get the item; handle redirects.
    """
    item = pywikibot.ItemPage(repo, qnumber)

    try:
        item.get()
    except pywikibot.exceptions.IsRedirectPageError:
        # Resolve a single redirect error
        item = item.getRedirectTarget()
        label = get_item_label(item)
        pywikibot.warning('Item {} ({}) redirects to {}'
                          .format(label, qnumber, item.getID()))
        ## qnumber = item.getID()   ## Python doesn't know call by reference...
    return item


def get_language_preferences():
    """
    Get the list of preferred languages,
    using environment variables LANG, LC_ALL, and LANGUAGE.
    Result:
        List of ISO 639-1 language codes
    Documentation:
        https://www.gnu.org/software/gettext/manual/html_node/Locale-Environment-Variables.html
    """
    mainlang = os.getenv('LANGUAGE',
                         os.getenv('LC_ALL',
                         os.getenv('LANG', ENLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang] + ['nl', 'fr', 'en', 'de', 'es', 'it']
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)
    return main_languages


def get_sdc_item(sdc_data):
    """
    Get the item from the SDC statement.
    """
    qnumber = sdc_data['datavalue']['value']['id']

    # Get item
    item = get_item(qnumber)
    if item.getID() != qnumber:
        ## Retroactively update the SDC statement for redirect
        qnumber = item.getID()   ## Python doesn't know call by reference...
    return item


def get_sdc_label(label_list) -> str:
    """
    Get label from SDC data.
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


def get_url_pagename(subject) -> str:
    """
    Extract pagename from URL.
    """
    slashpos = subject.rfind('/')
    if slashpos > 0:
        subject = subject[slashpos + 1:]
    if subject.find('index.php?title=') == 0:
        subject = subject[16:]
    return subject


def item_is_in_list(statement_list, checklist):
    """
    Verify if statement list contains at least one item from the checklist
    param: statement_list: Statement list
    param: checklist:      List of values (string)
    return: Matching or empty string
    """
    for seq in statement_list:
        try:
            isinlist = seq.getTarget().getID()
            if isinlist in checklist:
                return isinlist
        except:
            pass    # Ignore NoneType error
    return ''


def property_is_in_list(statement_list, proplist) -> bool:
    """
    Verify if a property is used for a statement

    Parameters:

        statement_list: Statement list
        proplist:       List of properties (string)

    Returns:

    Boolean (True when match)
    """
    isinlist = False
    for prop in proplist:
        if prop in statement_list:
            isinlist = True
            break
    return isinlist


INFOQSUFFRE = re.compile(r'/Information\|(Q[0-9]+)}}')            # Q-numbers

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

# Get parameters
pgmnm = sys.argv.pop(0)
pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))

# Connect to databases
site = pywikibot.Site('commons')
repo = site.data_repository()
csrf_token = site.tokens['csrf']

# Get list of media files from input parameters (either P1 or stdin)
page_list = []
if sys.argv:
    # Get Wikimedia Commons page list from category P1
    subject = get_url_pagename(sys.argv.pop(0))

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
    input_list = sorted(set(inputfile.splitlines()))
    for subject in input_list:
        # Get filename
        subject = get_url_pagename(subject)
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
        media_name = page.title()
        #print(media_name)
        media_identifier = 'M' + str(page.pageid)
        ## https://commons.wikimedia.org/wiki/Special:EntityPage/M63763537
        ## https://commons.wikimedia.org/entity/M63763537
        if page.namespace() != FILENAMESPACE:
            pywikibot.info('Skipping {} {}'.format(media_identifier, media_name))
            continue

        # Get standaard media file information
        file_info = page.latest_file_info.__dict__
        user_name = file_info['user']
        """
        file_info.keys()
dict_keys(['timestamp', 'user', 'size', 'width', 'height', 'comment', 'url', 'descriptionurl', 'descriptionshorturl', 'sha1', 'metadata', 'mime'])

        file_info
{'timestamp': Timestamp(2017, 10, 31, 10, 14, 18), 'user': 'Rama', 'size': 2022429, 'width': 3315, 'height': 4973, 'comment': '{{User:Rama/Wikimedian portraits|WikidataCon 2017}}\n\n{{Information\n|Description=[[User:Geertivp]] at WikidataCon 2017\n|Source={{Own}}\n|Date=\n|Author={{u|Rama}}\n|Permission={{self|Cc-by-sa-3.0-fr|CeCILL|attribution=Rama}}\n|other_versions=\n}}\n\n[[Category...', 'url': 'https://upload.wikimedia.org/wikipedia/commons/4/4a/Geert_Van_Pamel-IMG_1572.JPG', 'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Geert_Van_Pamel-IMG_1572.JPG', 'descriptionshorturl': 'https://commons.wikimedia.org/w/index.php?curid=63763537', 'sha1': 'a157b85ec18e5718fe2d8e5c0d38063a4564d7f0', 'metadata': [{'name': 'ImageWidth', 'value': 3315}, {'name': 'ImageLength', 'value': 4973}, {'name': 'Make', 'value': 'Canon'}, {'name': 'Model', 'value': 'Canon EOS 5D Mark II'}, {'name': 'Orientation', 'value': 1}, {'name': 'XResolution', 'value': '72/1'}, {'name': 'YResolution', 'value': '72/1'}, {'name': 'ResolutionUnit', 'value': 2}, {'name': 'Software', 'value': 'digiKam-4.14.0'}, {'name': 'DateTime', 'value': '2017:10:28 11:09:18'}, {'name': 'YCbCrPositioning', 'value': 2}, {'name': 'ExposureTime', 'value': '1/250'}, {'name': 'FNumber', 'value': '28/10'}, {'name': 'ExposureProgram', 'value': 3}, {'name': 'ISOSpeedRatings', 'value': 3200}, {'name': 'ExifVersion', 'value': '0221'}, {'name': 'DateTimeOriginal', 'value': '2017:10:28 11:09:18'}, {'name': 'DateTimeDigitized', 'value': '2017:10:28 11:09:18'}, {'name': 'ComponentsConfiguration', 'value': '\n#1\n#2\n#3\n#0'}, {'name': 'ShutterSpeedValue', 'value': '524288/65536'}, {'name': 'ApertureValue', 'value': '196608/65536'}, {'name': 'ExposureBiasValue', 'value': '0/1'}, {'name': 'MeteringMode', 'value': 5}, {'name': 'Flash', 'value': 16}, {'name': 'FocalLength', 'value': '200/1'}, {'name': 'SubSecTime', 'value': '49'}, {'name': 'SubSecTimeOriginal', 'value': '49'}, {'name': 'SubSecTimeDigitized', 'value': '49'}, {'name': 'FlashPixVersion', 'value': '0100'}, {'name': 'FocalPlaneXResolution', 'value': '5616000/1459'}, {'name': 'FocalPlaneYResolution', 'value': '3744000/958'}, {'name': 'FocalPlaneResolutionUnit', 'value': 2}, {'name': 'CustomRendered', 'value': 0}, {'name': 'ExposureMode', 'value': 0}, {'name': 'WhiteBalance', 'value': 0}, {'name': 'SceneCaptureType', 'value': 0}, {'name': 'GPSVersionID', 'value': '0.0.2.2'}, {'name': 'PixelXDimension', 'value': '3315'}, {'name': 'PixelYDimension', 'value': '4973'}, {'name': 'MEDIAWIKI_EXIF_VERSION', 'value': 1}], 'mime': 'image/jpeg'}
        """

        file_type = ['image']           # Initial default (most media files are images)
        page_type = get_file_type(media_name)
        if page_type != '':
            file_type = [page_type]

        # Get mime type (only available in the file interface; not for category search)
        #pywikibot.debug(file_info)
        for descr in file_info:
            if descr == 'metadata':
                for meta in file_info[descr]:
                    pywikibot.debug('{}:\t{}'.format(meta['name'], meta['value']))
            else:
                pywikibot.debug('{}:\t{}'.format(descr, file_info[descr]))

        if 'mime' in file_info:
            mime_type = file_info['mime']
            file_type = mime_type.split('/')
            if file_type[0] == 'application':
                del(file_type[0])

        # Get the file size
        file_size = 0
        if 'size' in file_info:
            file_size = file_info['size']

        # Get image height
        height = 0
        if 'height' in file_info:
            height = file_info['height']

        # Get image width
        width = 0
        if 'width' in file_info:
            width = file_info['width']

        pywikibot.log('Media size: {:d} {:d}:{:d}'.format(file_size, width, height))

        # Get media SDC data
        request = site.simple_request(action='wbgetentities', ids=media_identifier)
        row = request.submit()

        sdc_data = row.get('entities').get(media_identifier)
        # Key attributes: pageid, ns, title, labels, descriptions, statements <- depicts, MIME type
        ## {'pageid': 125667911, 'ns': 6, 'title': 'File:Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot.pdf', 'lastrevid': 707697714, 'modified': '2022-11-18T20:06:23Z', 'type': 'mediainfo', 'id': 'M125667911', 'labels': {'nl': {'language': 'nl', 'value': 'Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot'}, 'en': {'language': 'en', 'value': 'Wikidata ISBN book description with ISBNlib and Pywikibot'}, 'fr': {'language': 'fr', 'value': 'Description du livre Wikidata ISBN avec ISBNlib et Pywikibot'}, 'de': {'language': 'de', 'value': 'Wikidata ISBN Buchbeschreibung mit ISBNlib und Pywikibot'}, 'es': {'language': 'es', 'value': 'Descripción del libro de Wikidata ISBN con ISBNlib y Pywikibot'}}, 'descriptions': {}, 'statements': []}

        item_list = []
        preferred = False

        #pywikibot.debug(sdc_data)
        sdc_statements = sdc_data.get('statements')
        #pywikibot.debug(sdc_statements)
        if not sdc_statements:
            # Old images do not have statements
            pywikibot.info('No statements for {} {} {} by {}'
                           .format(file_type[0], media_identifier, media_name, user_name))
            depict_list = []
        else:
            # We now have valid depicts statements, so we can obtain the media type;
            # can be overruled by subsequent depict statements
            mime_list = sdc_statements.get(MIMEPROP)
            if mime_list:
                # Default: image
                # Normally we only have one single MIME type
                mime_type = mime_list[0]['mainsnak']['datavalue']['value']
                file_type = mime_type.split('/')
                if file_type[0] == 'application':
                    del(file_type[0])

            # This program runs on the basis of depects statements
            depict_list = sdc_statements.get(DEPICTSPROP)
            if depict_list == None:
                # A lot of media files do not have depict statements.
                # Please add depict statements for each media file.
                pywikibot.info('No depicts for {} {} {} by {}'
                              .format(file_type[0], media_identifier, media_name, user_name))
                depict_list = []

            # Add file type from instance list
            instance_list = sdc_statements.get(INSTANCEPROP)
            if instance_list:
                for instance in instance_list:
                    item = get_sdc_item(instance['mainsnak'])
                    qnumber = item.getID()
                    if qnumber in image_types:
                        file_type.insert(0, image_types[qnumber])

            # Add reproduction in museum collection
            repro_list = sdc_statements.get(REPROPROP)
            if repro_list:
                preferred = True
                file_type.insert(0, 'repro')
                item_list = [get_sdc_item(seq['mainsnak']) for seq in repro_list]

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

                # Get the original item and the image type
                if (qnumber in file_type_of_item
                        and 'qualifiers' in depict
                        and property_is_in_list(depict['qualifiers'], {QUALIFYFROMPROP})):
                    file_type.insert(0, file_type_of_item[qnumber])
                    item = get_sdc_item(depict['qualifiers'][QUALIFYFROMPROP][0])
                    qnumber = item.getID()

                # Preferred images overrule normal images
                if qnumber in image_types:
                    # Overrule the image type
                    file_type.insert(0, image_types[qnumber])
                elif depict['rank'] == 'preferred':
                    # Overrule normal items; accumulate preferred values
                    if not preferred:
                        item_list = []
                    item_list.append(item)
                    preferred = True
                elif ('qualifiers' in depict
                        and property_is_in_list(depict['qualifiers'], {RESTRICTIONPROP})):
                    """
{'P462': [{'snaktype': 'value', 'property': 'P462', 'hash': '4af9c81cc458bf6b99699673fd9268b43ad0c4d4', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 23445, 'id': 'Q23445'}, 'type': 'wikibase-entityid'}}]}
                    """
                    # Ignore items with "applies to" qualifiers
                    restricted_item = get_sdc_item(depict['qualifiers'][RESTRICTIONPROP][0])
                    pywikibot.info('Skipping qualifier ({}) for {} ({}) for {} {} {}'
                                   .format(RESTRICTIONPROP,
                                           get_item_label(restricted_item), restricted_item.getID(),
                                           file_type[0], media_identifier, media_name))
                elif not preferred:
                    # Add a normal ranked item to the list;
                    # drop normal items when there are already preferred
                    item_list.append(item)

            collection_list = sdc_statements.get(COLLECTIONPROP)
            if collection_list and not (preferred or len(item_list) == 1):
                # Depict statements for GLAM collections
                # generally describe parts of painting objects;
                # skip them, unless there is a preferred statement describing the artwork itself.
                collection_item = get_sdc_item(collection_list[0]['mainsnak'])
                pywikibot.info('{} ({}) {} {} by {} belongs to collection {} ({}), and not preferred'
                               .format(file_type[0], media_type,
                                       media_identifier, media_name, user_name,
                                       get_item_label(collection_item), collection_item.getID()))
                item_list = []

        # Find "Information" item numbers from Wiki text
        info_list = INFOQSUFFRE.findall(page.text)
        #print(info_list)
        for qnumber in info_list:
            item = pywikibot.ItemPage(repo, qnumber)
            if item not in item_list:
                # Add item number to depicts list
                item_list.insert(0, item)

                depict_missing = True
                for depict in depict_list:
                    if qnumber == get_sdc_item(depict['mainsnak']).getID():
                        depict_missing = False
                        break

                if depict_missing:
                    # Add the SDC depict statements for this item
                    depict_statement['claims'][0]['mainsnak']['datavalue']['value']['id'] = qnumber
                    depict_statement['claims'][0]['mainsnak']['datavalue']['value']['numeric-id'] = int(qnumber[1:])

                    # Now store the depict statement
                    pywikibot.debug(depict_statement)
                    transcmt = '#pwb Add depicts {} statement'.format(qnumber)
                    sdc_payload = {
                        'action': 'wbeditentity',
                        'format': 'json',
                        'id': media_identifier,
                        'data': json.dumps(depict_statement, separators=(',', ':')),
                        'token': csrf_token,
                        'summary': transcmt,
                        'bot': BOTFLAG,
                    }

                    sdc_request = site.simple_request(**sdc_payload)
                    """
/w/api.php?action=wbeditentity&format=json&id=M133875629&data={"claims":[{"type":"statement","rank":"preferred","mainsnak":{"snaktype":"value","property":"P180","datavalue":{"type":"wikibase-entityid","value":{"entity-type":"item","id":"Q2005868","numeric-id":2005868}}}}]}&summary=#pwb+Add+depicts+statement&bot=&assert=user&maxlag=5&token=3da5438009c7e280c08e38f5524e45a464a53441+\
                    """
                    try:
                        sdc_request.submit()
                        pywikibot.warning('Add SDC depicts {} to {} {} by {}'
                                          .format(qnumber, media_identifier, media_name, user_name))
                    except Exception as error:
                        pywikibot.error(format(error))
                        pywikibot.info(sdc_request)

        # Could possibly fail with KeyError with non-recognized media types
        # In that case the missing media type must be added to the list
        pywikibot.debug(file_type)
        pywikibot.debug(item_list)
        media_type = media_props[file_type[0]]

        # Check if the media file is used by another Wikidata item
        # This includes e.g. P10 video, P18 image, P51 audio, etc.
        # Possibly other links...
        image_used = False
        media_page = pywikibot.FilePage(repo, media_name)
        for file_ref in pg.FileLinksGenerator(media_page):
            if file_ref.namespace() == MAINNAMESPACE:
                # We only take Qnumbers into account (primary namespace)
                # e.g. ignore descriptive pages
                # Show all connected item numbers
                image_used = True
                item_ref = get_item(file_ref.title())
                pywikibot.info('Used {} ({}) {} {} by {}, item {} ({})'
                               .format(file_type[0], media_type,
                                       media_identifier, media_name, user_name,
                                       get_item_label(item_ref), item_ref.getID()))
        if image_used:
            # Image is already used, so skip (avoid flooding)
            continue

        # Filter on minimum image resolution.
        # Allow low resolution for logo and other small images.
        # Skip low quality images where large images are expected.
        if (not property_is_in_list(small_images, file_type) and (
                file_size > 0 and file_size < MINFILESIZE
                or height > 0 and height < MINRESOLUTION
                    and width > 0 and width < MINRESOLUTION)):
            pywikibot.info('{} ({}) {} {} by {} size {:d} {:d}:{:d} is too small'
                           .format(file_type[0], media_type,
                                   media_identifier, media_name, user_name,
                                   file_size, width, height))
            continue

        for item in item_list:
            # Loop through the target Wikidata items to find the first match
            if media_type in item.claims:
                # Preferably one single image per Wikidata item (avoid pollution)
                continue
            elif not property_is_in_list(item.claims, object_class):
                # Skip when neither instance, nor subclass
                continue
            elif (INSTANCEPROP in item.claims
                    # Skip Wikimedia disambiguation and category items;
                    # we want real items;
                    # see https://www.wikidata.org/wiki/Property:P18#P2303
                    and item_is_in_list(item.claims[INSTANCEPROP], skipped_instances)):
                continue
            elif (INSTANCEPROP in item.claims
                    # Human and artwork images are incompatible (distinction between artist and oevre)
                    and item_is_in_list(item.claims[INSTANCEPROP], human_class)
                    and media_type not in human_media):
                continue
            elif property_is_in_list(item.claims, published_work):
                # We skip publications (good relevant images are extremely rare)
                continue
            elif item.namespace() != MAINNAMESPACE:
                # Only register media files to items in the main namespace, otherwise skip
                continue

                ## Proactive constraint check (how could we do this?)
                # Does there exist a method?

                # Note that we unconditionally accept all P279 subclasses
                # Could there possibly exist a condition to trigger Related image (P6802)?
            else:
                # Get media label
                media_label = get_sdc_label(sdc_data.get('labels')) # Bijschrift
                # The GUI allows to only register labels?
                if media_label:
                    pywikibot.info(media_label)

                # Get media description
                media_description = get_sdc_label(sdc_data.get('descriptions'))
                ## ?? Why is descriptions nearly always empty? How could it be registered?
                # Shouldn't Wiki text descriptions be digitized?
                if media_description:
                    pywikibot.log(media_description)

                # Add media statement to the item
                # Only the first matching item will be registered
                transcmt = '#pwb Add {} from [[c:Special:EntityPage/{}]] SDC'.format(file_type[0], media_identifier)
                claim = pywikibot.Claim(repo, media_type)
                claim.setTarget(page)
                item.addClaim(claim, bot=BOTFLAG, summary=transcmt)
                pywikibot.warning('{} ({}): add {} ({}) size {:d} {:d}:{:d} {} {} by {}'
                                  .format(get_item_label(item), item.getID(),
                                          file_type[0], media_type, file_size, width, height,
                                          media_identifier, media_name, user_name))

                # Do we require a reference?
                # Probably not; because the medium file is already described by the SDC.
                break
        else:
            if item_list:
                # All media item slots were already taken (by other media files)
                # Maybe we could add more appropriate depicts statements,
                # and then rerun the script?
                pywikibot.info('Redundant {} ({}) {} {} by {}, item {}'
                               .format(file_type[0], media_type,
                                       media_identifier, media_name, user_name, item.getID()))
    # Log errors
    except Exception as error:
        pywikibot.error('Error processing {} {} by {}, {}'
                        .format(media_identifier, media_name, user_name, error))
        #raise      # Uncomment to debug any exceptions

# Einde van de miserie
