#!/usr/bin/python3

codedoc = """
Amend Wikimedia Commons SDC and Wikidata

Add media files to Wikidata items
from Wikimedia Commons SDC depicts (P180) statements,
based on a Wikimedia Commons category (parameter P1),
or a list of media files (stdin).

Kind of creating reverse SDC P180 statements in Wikidata...

Starting from a Wikimedia Category,
or a list of media files,
through Wikimedia Commons SDC P180 statements,
registering media file statements (P10, P18, P51; video, image, audio)
to the corresponding Wikidata items.

Basically, it tries to do the same as WDFIST (Magnus Manske),
on the base of a Wikimedia Commons category,
a functionality that WDFIST does not offer…

In principle the script runs completely automated, without any human intervention,
but it is strongly advised to verify the resulting changes in Wikidata.

Depending on the quality of the SDC P180 statements, manual corrections might be required,
both in Wikidata, and in Wikimedia Commons SDC statements.

Use Wikimedia Commons Wiki text /Information or heritage templates and their ID parameter
to allow for an automatic registration of
SDC depict statements and the media file in Wikidata.

Register the related country and jurisdiction derived from its corresponding heritage ID.

Parameters:

    P1: Wikimedia Commons category (subcatergories are not processed recursively by default)
        Can be a Wikimedia Commons category URL

    P1 P2:... Property/value structured search
        Can be a property or item URL

    If no parameters are available,
    a list of media filenames is read via stdin,
    one filename or M-number per line.

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
        An alternative is the /Information template with an item number parameter.
    If there are no SDC P180 statements, no updates in Wikidata are performed.
    The metadata MIMI type is recognized (default image/jpeg)
    Please add a proper SDC MIMI type when needed
    Please add a preferred qualifier (especially for collections)

Data validation:

    Media files having depict statements are added to Wikidata items.
    The script accepts audio, image, and video.
        For images, some P180 instances can determine subtypes
    Wikidata disambiguation, category and other namespaces are skipped.
    No media file is added when it is already assigned to another Wikidata item.
    No media file is added if the item holds already another media file of the same type.
    Collection media files should always have one preferred statement;
        avoid Wikidata image statement polution;
        requires a specific Wikidata item for the collection object (which is a good idea!).
    For artist items in principle their work is not added.
    The script supports compound depict statements like "grave of (person)".
    Specific properties, like "P1442 (grave)", are used in the case.

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

    Setup /Information templates for image upload campaigns,
    allowing to show Wikidata properties linked to the item.

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

Deprecated:

    https://www.wikidata.org/wiki/Property:P642
    https://www.wikidata.org/wiki/Wikidata:WikiProject_Deprecate_P642

Known problems:

    Very few media files have a depicts statement (see prerequisites)
        Idea: missing depicts query

    Updated items might require manual validation, to correct any anomalies;
    see https://www.wikidata.org/wiki/Special:Contributions

    Category redirects are not traversed (to be resolved manually).

    Wikidata redirects are recognized,
    but are not automatically updated in the SDC statements.

    Deleted Wikidata item pages,
    while the Wikimedia Commons SDC P180 statement is still there;
    this problem is not automatically resolved.

    A "Wrong media file" is possibly assigned to the item:
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

    On input, an embedded / is wrongly truncating a category name; use %2f instead.

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

    https://phabricator.wikimedia.org/T326510
    How to obtain the resolution and the image size from an image via Pywikibot

    https://commons.wikimedia.org/wiki/Commons:Structured_data/Properties_table
    https://commons.wikimedia.org/wiki/Commons:Depicts

Resources:

    Requires an internet connection
    Uses only 3% CPU on a modern laptop

Related projects:

    https://www.wikidata.org/wiki/Wikidata:Database_reports/Constraint_violations/P18

Author:

	Geert Van Pamel, 2022-12-10, MIT License, User:Geertivp

"""

import json             # json data structures
import math             # Mathematical functions
import os               # Operating system: getenv
import pdb              # Python debugger
import pywikibot		# API interface to Wikidata
import re		    	# Regular expressions (very handy!)
import sys		    	# System: argv, exit (get the parameters, terminate the program)
import unidecode        # Unicode

from datetime import datetime	    # now, strftime, delta time, total_seconds
from pywikibot import pagegenerators as pg
from pywikibot.data import api

# Global variables
modnm = 'Pywikibot add_image_from_sdc'  # Module name (using the Pywikibot package)
pgmid = '2025-02-23 (gvp)'	        # Program ID and version
pgmlic = 'MIT License'
creator = 'User:Geertivp'

# Default values
exitstat = 0            # (default) Exit status
exitfatal = False	    # Exit on fatal error (can be disabled with -p; please take care)
recurse_list = False    # Could be overruled with -c qualifier
include_revisions = False

max_range = 800         # Default range (1/10th of maximum value)
                        # Modified based on the surface of the locality
                        # Should be overruled by a qualifier
# Constants
transcmt = '#pwb Image metadata'
MAX_ITEMS = 5000        # Maximum items to return after search (maximum: 5000)
MAX_RANGE = 8000        # (+/- 5 mi) New-York would be 19652 (Q60), Parijs 5792 (Q90), Brussel 3221 (Q239)
PI = 3.14159265358979   # https://www.wikidata.org/wiki/Q167
EST_DEGREE_DIST = 1609.344 * 60.0   # One British mile is 1609.344 m and corresponds to 1' (circle minute)

surface_unit_list = {
    'Q712226': (1000.0, 'km²'), # square km
    # other units to be added (when index error occurs)
}

MINFILESIZE = 120000    # Minimum file size for quality images (ignore smaller images)
MINRESOLUTION = 600     # Minimum resolution (ignore smaller images)

ENLANG = 'en'
MAINLANG = 'en:mul'     # mul can have non-Romain alphabeths; EN was tradional default value

PREFERRED_RANK = 'preferred'
NORMAL_RANK = 'normal'

# Namespace IDs
MAINNAMESPACE = 0
FILENAMESPACE = 6

# Instances
HUMANINSTANCE = 'Q5'
PHOTOINSTANCE = 'Q125191'
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
# Human class
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
COUNTRYPROP = 'P17'
IMAGEPROP = 'P18'
INSTANCEPROP = 'P31'
FLAGPROP = 'P41'
AUTHORPROP = 'P50'
AUDIOPROP = 'P51'
COATOFARMSPROP = 'P94'
EDITORPROP = 'P98'
SIGNATUREPROP = 'P109'
PUBLISHERPROP = 'P123'
GENREPROP = 'P136'
LOGOPROP = 'P154'
DEPICTSPROP = 'P180'
COLLECTIONPROP = 'P195'
ISBNPROP = 'P212'
LOCATORMAPPROP = 'P242'
SUBCLASSPROP = 'P279'
DOIPROP = 'P356'
NLHERITAGEPROP = 'P359'         # Nederland
FRHERITAGEPROP = 'P380'         # France
PRONUNCIATIONPROP = 'P443'
RESTRICTIONPROP = 'P518'
GEOLOCATIONPROP = 'P625'
WORKPROP = 'P629'
QUALIFYFROMPROP = 'P642'        ## https://www.wikidata.org/wiki/Wikidata:WikiProject_Deprecate_P642
EDITIONPROP = 'P747'
VOYAGEBANPROP = 'P948'
ISBN10PROP = 'P957'
SPOKENTEXTPROP = 'P989'
VOICERECPROP = 'P990'
SCANPROP = 'P996'
JURISDICTIONPROP = 'P1001'
CREALOCPROP = 'P1071'           # Different from P9149
WALHERITAGEPROP = 'P1133'       # Wallonie
MIMEPROP = 'P1163'
CAMERALOCATIONPROP = 'P1259'
GRAVEPROP = 'P1442'
RUHERITAGEPROP = 'P1483'        # Russia
VLGHERITAGEPROP = 'P1764'       # Vlaanderen
PLACENAMEPROP = 'P1766'
PLAQUEPROP = 'P1801'
SURFACEPROP = 'P2046'
AUTHORNAMEPROP = 'P2093'
COLLAGEPROP = 'P2716'
ICONPROP = 'P2910'
PARTITUREPROP = 'P3030'
DESIGNPLANPROP = 'P3311'
NIGHTVIEWPROP = 'P3451'
BRUHERITAGEPROP = 'P3600'       # Brussels
PANORAMAPROP = 'P4640'
WINTERVIEWPROP = 'P5252'
DIAGRAMPROP = 'P5555'
CHIEFEDITORPROP = 'P5769'
INTERIORPROP = 'P5775'
REPROPROP = 'P6243'             # https://commons.wikimedia.org/wiki/File:VanGogh-starry_night_ballance1.jpg
RLTDIMAGEPROP = 'P6802'
VERSOPROP = 'P7417'
RECTOPROP = 'P7418'
FRAMEWORKPROP = 'P7420'
DEPICTFORMATPROP = 'P7984'
VIEWFROMPROP = 'P8517'
AERIALVIEWPROP = 'P8592'
FAVICONPROP = 'P8972'
OBJECTLOCATIONPROP = 'P9149'    # Different from P1071
COLORWORKPROP = 'P10093'
REPRESENTATIONTYPEPROP = 'P12692'

# Media type properties about humans
human_media_props = {
    AUDIOPROP,
    IMAGEPROP,
    PLAQUEPROP,
    VIDEOPROP,
    VOICERECPROP,
}

# Main object properties: instance or subclass
object_class_props = {
    INSTANCEPROP,
    SUBCLASSPROP,
}

# Published work properties
published_work_props = {
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

# Determine small images
small_images = {
    'favicon',
    'gif',
    'icon',
    'logo',
    'plan',
    'signature',
    'svg',
    'wvbanner',
}

# Map media instance to media types
# See https://www.wikidata.org/wiki/Property:P1687 (to get the Wikidata property)
# e.g. Q170593 collage -> P2716
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
    'Q134307': 'portrait',      # Person portrait
    'Q170593': 'collage',
    'Q173387': 'grave',
    'Q178659': 'illustration',
    'Q179700': 'statue',
    'Q183061': 'facade',
    'Q184377': 'pronunciation',
    'Q187947': 'partiture',
    'Q188675': 'signature',
    'Q219423': 'wallpainting',
    'Q226697': 'perkament',
    'Q241045': 'bust',          # P7984
    'Q266488': 'placename',     # town name
    'Q606876': 'pancarte',
    'Q611203': 'plan',
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
    'Q1551015': 'groupphoto',
    'Q1885014': 'plaque',       # herdenkingsmonument
    'Q1886349': 'logo',
    'Q1969455': 'placename',    # street name
    'Q2032225': 'placename',    # German place name
    'Q2075301': 'view',
    'Q2298569': 'map',
    'Q2998430': 'interior',     # interieur
    'Q3302947': 'audio',        # audio recording
    'Q3362196': 'placename',    # French place name
    'Q3381576': 'bwimage',      # black-and-white photography
    'Q4650799': 'audio',        # audio
    'Q6664848': 'locatormap',
    'Q6901463': 'bwimage',      # black-and-white photography (redirect)
    ##'Q9305022': 'recto',      ## paper property related
    ##'Q9368452': 'verso',      ## paper property related
    'Q11060274': 'prent',
    'Q17172850': 'voicerec',    # voice
    'Q18809567': 'threepartportrait', # P7984
    'Q18809626': 'fullbodyportret', # P7984
    'Q22920576': 'wvbanner',
    'Q28333482': 'nightview',
    'Q31807746': 'interior',    # interieurinrichting
    'Q53702817': 'voicerec',    # voice recording
    'Q54819662': 'winterview',
    'Q55498668': 'placename',   # place name
    'Q70077691': 'groupphoto',
    'Q76419950': 'pancarte',
    'Q98069877': 'video',
    'Q109592922': 'colorwork',
    'Q110611535': 'slides',
# others...

# missing; could be triggered implicitly from file type...
    #'': 'gif',
    #'': 'jpeg',
    #'': 'png',
    #'': 'svg',
    #'': 'tiff',
    #'': 'xcf',
    #'': 'xml',
    #'': 'webp',

### Add more values (see copy_label.py)
# https://www.wikidata.org/wiki/Wikidata:Property_proposal/Type_of_representation
}

# Mapping of SDC media MIME types to Wikidata property
# Should be extended for new MIME types -> will generate a KeyError
all_media_props = {
    #'application': ?,          # Requires subtype lookup, e.g. 'ogg', 'pdf'
    #'?': RLTDIMAGEPROP,        # Related image; how to identify? See https://www.wikidata.org/wiki/Special:WhatLinksHere/Property:P6802
    'aerialview': AERIALVIEWPROP,
    'artwork': IMAGEPROP,       ## Would require special property
    'audio': AUDIOPROP,
    'book': IMAGEPROP,          ## Would require special property
    'bust': IMAGEPROP,          ## Would require special property
    'bwimage': IMAGEPROP,       ## Would require special property
    'collage': COLLAGEPROP,
    'colorwork': COLORWORKPROP,
    'coatofarms': COATOFARMSPROP,
    'diagram': DIAGRAMPROP,
    'digitalimage': IMAGEPROP,  ## Would require special property
    'document': SCANPROP,        ## Would require special property
    'facade': IMAGEPROP,        ## Would require special property
    'face': IMAGEPROP,          ## Would require special property (id card, mugshot)
    'favicon': FAVICONPROP,
    'flag': FLAGPROP,
    'framework': FRAMEWORKPROP,
    'fullbodyportret': IMAGEPROP,    ## Would require special property
    'gif': IMAGEPROP,           ## Would require special property
    'grave': GRAVEPROP,
    'groupphoto': IMAGEPROP,    ## Would require special property
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
    'mpeg': VIDEOPROP,          ## Would require special property
    'mpg': VIDEOPROP,           ## Would require special property
    'manuscript': SCANPROP,      ## Would require special property
    'nightview': NIGHTVIEWPROP,
    'oga': AUDIOPROP,
    'ogg': AUDIOPROP,           # Fewer files are video
    'ogv': VIDEOPROP,           ## Would require special property
    'pancarte': IMAGEPROP,      ## Would require special property
    'pdf': SCANPROP,
    'panoview': PANORAMAPROP,
    'partiture': PARTITUREPROP,
    'perkament': SCANPROP,       ## Would require special property
    'placename': PLACENAMEPROP,
    'plaque': PLAQUEPROP,
    'plan': DESIGNPLANPROP,
    'png': IMAGEPROP,           ## Would require special property
    'prent': IMAGEPROP,         ## Would require special property
    'pronunciation': PRONUNCIATIONPROP,
    'portrait': IMAGEPROP,      ## Would require special property
    'recto': RECTOPROP,
    'repro': IMAGEPROP,         ### Would require special property
    'sculpture': IMAGEPROP,     ## Would require special property
    'signature': SIGNATUREPROP,
    'sla': IMAGEPROP,           ## Would require special property
    'slides': SCANPROP,          ## Would require special property
    'spokentext': SPOKENTEXTPROP,
    'statue': IMAGEPROP,        ## Would require special property
    'svg': IMAGEPROP,           ## Would require special property
    'threepartportrait': IMAGEPROP, ## Would require special property
    'tif': IMAGEPROP,           ## Would require special property
    'tiff': IMAGEPROP,          ## Would require special property
    'verso': VERSOPROP,
    'video': VIDEOPROP,
    'view': VIEWFROMPROP,
    'voicerec': VOICERECPROP,
    'wallpainting': IMAGEPROP,  ## Would require special property
    'webm': VIDEOPROP,
    'webp': IMAGEPROP,
    'winterview': WINTERVIEWPROP,
    'wvbanner': VOYAGEBANPROP,
    'xcf': IMAGEPROP,           ## Would require special property
    #'xml': IMAGEPROP,           ## Would require special property
    # others...
}

# From EXIF as registered in SDC
location_target = [
    # Object location overrules Camera location
    ('Camera location', CAMERALOCATIONPROP),    # Geolocation of camera view point
    ('Object location', OBJECTLOCATIONPROP),    # Geolocation of object
    ###('Depicted item location', DEPICTPLACELOCATIONPROP), # Geolocation of depicted place
]

# Heritage properties for Wikimedia Commons template heritage IDs
heritage_prop_list = {
    # Linked properties:
    #   Country (P17) for all
    #   Jurisdiction (P1001) for Belgium

    #'Beschermd erfgoed' has no property?   # https://commons.wikimedia.org/wiki/File:Br%C3%BCgge_(B),_Belfort_von_Br%C3%BCgge_--_2018_--_8611.jpg

    'Onroerend erfgoed': VLGHERITAGEPROP,   # Vlaanderen, https://www.wikidata.org/wiki/Property:P1764, https://id.erfgoed.net/erfgoedobjecten/76806
    'Monument Brussels': BRUHERITAGEPROP,   # Brussels, https://www.wikidata.org/wiki/Property:P3600
    'Monument Wallonie': WALHERITAGEPROP,   # Wallonie, https://www.wikidata.org/wiki/Property:P1551, http://lampspw.wallonie.be/dgo4/site_thema/index.php/dossier/view/PAT_EXC/92094-PEX-0003-03

    'Mérimée': FRHERITAGEPROP,              # France, https://www.wikidata.org/wiki/Property:P380, https://www.pop.culture.gouv.fr/notice/merimee/PA00086250
    'Rijksmonument': NLHERITAGEPROP,        # Nederland, https://www.wikidata.org/wiki/Property:P359, https://monumentenregister.cultureelerfgoed.nl/monumenten/5941

    'Cultural Heritage Russia': RUHERITAGEPROP, # Russia, https://www.wikidata.org/wiki/Property:P1483, https://ru-monuments.toolforge.org/wikivoyage.php?id=5010444009

    ## More instances to be added
    ## How could we search for more templates?
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


def get_url_pagename(subject) -> str:
    """
    Extract pagename from URL.
    """
    hashpos = subject.find('#')
    if hashpos > 0:
        subject = subject[:hashpos]
    slashpos = subject.rfind('/')
    if slashpos > 0:
        subject = subject[slashpos + 1:]
    if subject.find('index.php?title=') == 0:
        subject = subject[16:]
    return subject.strip()


def get_item_header(header):
    """
    Get the item header (label, description, alias in user language)

    :param header: item label, description, or alias language list (string or list)
    :return: label, description, or alias in the first available language (string)
    """

    # Return preferred label
    for lang in main_languages:
        if lang in header:
            return header[lang]

    # Return any other label
    for lang in header:
        return header[lang]
    return '-'


def get_property_label(propx) -> str:
    """
    Get the label of a property.

    :param propx: property (string or property)
    :return property label (string)
    Except: undefined property
    """

    if isinstance(propx, str):
        propty = pywikibot.PropertyPage(repo, propx)
    else:
        propty = propx

    return get_item_header(propty.labels)


def get_item_page(qnumber) -> pywikibot.ItemPage:
    """
    Get the item; handle redirects.
    """
    if isinstance(qnumber, str):
        item = pywikibot.ItemPage(repo, qnumber)
        try:
            item.get()
        except pywikibot.exceptions.IsRedirectPageError:
            # Resolve a single redirect error
            item = item.getRedirectTarget()
            label = get_item_header(item.labels)
            pywikibot.warning('Item {} ({}) redirects to {}'
                              .format(label, qnumber, item.getID()))
            qnumber = item.getID()
    else:
        item = qnumber
        qnumber = item.getID()

    while item.isRedirectPage():
        ## Should fix the sitelinks
        item = item.getRedirectTarget()
        label = get_item_header(item.labels)
        pywikibot.warning('Item {} ({}) redirects to {}'
                          .format(label, qnumber, item.getID()))
        qnumber = item.getID()

    return item


def get_language_preferences() -> []:
    """
    Get the list of preferred languages,
    using environment variables LANG, LC_ALL, and LANGUAGE.
    'en' is always appended.

    Format: string delimited by ':'.
    Main_sublange code,

    Result:
        List of ISO 639-1 language codes
    Documentation:
        https://www.gnu.org/software/gettext/manual/html_node/Locale-Environment-Variables.html
        https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    """
    mainlang = os.getenv('LANGUAGE',
                         os.getenv('LC_ALL',
                         os.getenv('LANG', MAINLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang]

    # Cleanup language list
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)

    for lang in MAINLANG.split(':'):
        if lang not in main_languages:
            main_languages.append(lang)

    return main_languages


def get_sdc_item(sdc_data) -> pywikibot.ItemPage:
    """
    Get the item from the SDC statement.

    :param sdc_data: SDC item number
    :return:
    """
    # Get item
    qnumber = sdc_data['datavalue']['value']['id']
    item = get_item_page(qnumber)
    qnumber = item.getID()
    ##print(qnumber)
    return item


def get_sdc_label(label_list) -> str:
    """
    Get label from SDC data.

    :param label_list: list of language labels
    :return: matching label (in first matching language)
    Example:
{'en': {'language': 'en', 'value': 'Belgian volleyball player'}, 'it': {'language': 'it', 'value': 'pallavolista belga'}}
Redundant media M70757539 File:Wout Wijsmans (Legavolley 2012).jpg
    """
    label = ''
    if label_list:
        for lang in main_languages:
            if lang in label_list:
                return  label_list[lang]['value']
        for lang in label_list:
            return  label_list[lang]['value']
    return label


def get_item_with_prop_value (prop: str, propval: str) -> set():
    """Get list of items that have a property/value statement

    :param prop: Property ID (string)
    :param propval: Property value (string; case insensitieve)
    :return: List of items (Q-numbers)

    See https://www.mediawiki.org/wiki/API:Search
    """
    pywikibot.debug('Search statement: ' + prop + ':' + propval)
    item_name_canon = unidecode.unidecode(propval).casefold()
    item_list = set()                   # Empty set
    params = {'action': 'query',        # Statement search
              'list': 'search',
              'srsearch': prop + ':' + propval,
              'srwhat': 'text',
              'format': 'json',
              'srlimit': 50}            # Should be reasonable value
    request = api.Request(site=repo, parameters=params)
    result = request.submit()
    # https://www.wikidata.org/w/api.php?action=query&list=search&srwhat=text&srsearch=P212:978-94-028-1317-3

    """
{
    "batchcomplete": "",
    "query": {
        "searchinfo": {
            "totalhits": 1
        },
        "search": [
            {
                "ns": 0,
                "title": "Q62009511",
                "pageid": 61836708,
                "size": null,
                "wordcount": 0,
                "snippet": "uitgave",
                "timestamp": "2023-09-19T20:50:29Z"
            }
        ]
    }
}
    """

    if 'query' in result and 'search' in result['query']:
        # Loop though items
        for row in result['query']['search']:
            qnumber = row['title']
            item = get_item_page(qnumber)

            if prop in item.claims:
                for seq in item.claims[prop]:
                    if unidecode.unidecode(seq.getTarget()).casefold() == item_name_canon:
                        item_list.add(item) # Found match
                        break       # One single match allowed
    # Convert set to list
    return item_list


def item_is_in_list(statement_list, itemlist):
    """
    Verify if statement list contains at least one item from the itemlist
    :param statement_list: Statement list
    :param itemlist:      List of values
    :return: Matching or empty string
    """
    for seq in statement_list:
        try:
            isinlist = seq.getTarget().getID()
            if isinlist in itemlist:
                return isinlist
        except:
            pass    # Ignore NoneType error
    return ''


def property_is_in_list(statement_list, proplist) -> str:
    """
    Verify if a property is used for a statement

    :param statement_list: Statement list
    :param proplist:       List of properties (string)
    :return: Matching property
    """
    for prop in proplist:
        if prop in statement_list:
            return prop
    return ''


def set_sdc_property_value(propty, item, ranking):
    """
    Add an SDC statement to a media file

    :param propty: SDC property
    :param item: target entity
    :param ranking: 'normal' or 'preferred'

    Global variables:

        media_identifier: media file ID
    """

    # Prepare the depict statement
    sdc_statement = {
        'claims': [{
            'mainsnak': {
                'snaktype': 'value',
                'property': propty,
                'datavalue': {
                    'value': {
                        'entity-type': 'item',
                        'numeric-id': int(item.getID()[1:]),
                        'id': item.getID(),
                    },
                    'type': 'wikibase-entityid',
                }
            },
            'type': 'statement',
            'rank': ranking,
        },
        ]
    }

    """
        # Prototype of runtime SDC statement
        {'mainsnak': {'snaktype': 'value', 'property': 'P1071', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 663764, 'id': 'Q663764'}, 'type': 'wikibase-entityid'}}, 'type': 'statement', 'rank': 'preferred'
        }
    """

    # Now store the depict statement
    pywikibot.debug(sdc_statement)
    prop_label = get_property_label(propty)
    item_label = get_item_header(item.labels)
    depictsdescr = 'Add SDC {}:{} ({}:{})'.format(prop_label, item_label, propty, item.getID())
    depictsfmtd = 'Add SDC {0}:[[d:{3}|{1}]] ({2}:{3})'.format(prop_label, item_label, propty, item.getID())
    commons_token = site.tokens['csrf']
    sdc_payload = {
        'action': 'wbeditentity',
        'format': 'json',
        'id': media_identifier,
        'data': json.dumps(sdc_statement, separators=(',', ':')),
        'token': commons_token,
        'summary': transcmt + ' ' + depictsfmtd + ' statement',
        'bot': cbotflag,
    }

    # Possible problems
    # https://commons.wikimedia.org/w/index.php?title=File%3AGent%2C_de_Graslei_vanaf_de_Korenlei_met_oeg24758tm61_IMG_0407_2021-08-13_16.42.jpg&diff=835229129&oldid=660290237
    # https://commons.wikimedia.org/w/index.php?title=File_talk%3ADSC_1134_-_307373_-_onroerenderfgoed.jpg#Wrong_heritage_registration?

    sdc_request = site.simple_request(**sdc_payload)
    """
/w/api.php?action=wbeditentity&format=json&id=M133875629&data={"claims":[{"type":"statement","rank":"preferred","mainsnak":{"snaktype":"value","property":"P180","datavalue":{"type":"wikibase-entityid","value":{"entity-type":"item","id":"Q2005868","numeric-id":2005868}}}}]}&summary=#pwb+Add+depicts+statement&bot=&assert=user&maxlag=5&token=3da5438009c7e280c08e38f5524e45a464a53441+\
    """
    try:
        sdc_request.submit()
        pywikibot.warning('{} to {} entity/{} {} by {}'
                          .format(depictsdescr, file_type[0], media_identifier, media_name, file_user))
    except Exception as error:
        pywikibot.error('{}, {}'.format(depictsdescr, error))
        pywikibot.info(sdc_request)
        pdb.set_trace()
        if exitfatal:               # Stop on first error
            raise


# Object location has priority over Camera location
# Decimal geolocation
# Documentation: https://commons.wikimedia.org/wiki/Template:Location
DECIMALGEOLOCATIONRE = re.compile(r'{{(Location|Object location|Camera location|Globe location|Location dec)\| *([0-9.]+) *\| *([0-9.]+)', flags=re.IGNORECASE)
# https://commons.wikimedia.org/wiki/File:Ch%C3%A2teau_des_Comtes_de_Borchgrave_%C3%A0_Dalhem_-_62027-CLT-0005-01.JPG

# DMS geolocation
DMSGEOLOCATIONRE = {}
DMSGEOLOCATIONRE[0] = re.compile(r'{{(Location dms|Location|Object location|Camera location|Globe location)\| *([0-9.]+) *\| *([0-9.]+) *\| *([0-9.]+) *\| *([NS]) *\| *([0-9.]+) *\| *([0-9.]+) *\| *([0-9.]+) *\| *([EW])', flags=re.IGNORECASE)
# {{location dms|51|4|20.97|N|2|39|42.38|E}}
# {{Object location|50|44|35.06|N|5|43|45.88|E|region:BE}}
# {{Location|50|53.1818|0|N|4|15.199|0|E|alt:54.7_source:exif_heading:?}}

# String notation
DMSGEOLOCATIONRE[1] = re.compile(r'{{(Location dms|Location|Object location|Camera location|Globe location)\| *([0-9.]+)° *([0-9.]+)′ *([0-9.]+)" *([NS]) *[,|]? *([0-9.]+)° *([0-9.]+)′ *([0-9.]+)" *([EW])', flags=re.IGNORECASE)
# {{Object location|50° 37′ 50.63″ N|6° 01′ 57.61″ E|region:BE}}
# {{Location|34° 01′ 27.37″ N, 116° 09′ 29.88″ W|region:DE-NI_scale:10000_heading:SW}}

###DMSGEOLOCATIONRE[2] = re.compile(r'{{(Location dms|Location|Object location|Camera location|Globe location)\| *([0-9.]+)° *([0-9.]+)′ *([0-9.]+)" *([NS]) *,? *([0-9.]+)° *([0-9.]+)′ *([0-9.]+)" *([EW])', flags=re.IGNORECASE)

DMSGEOLOCATIONRE[2] = re.compile(r'{{(Location dms|Location|Object location|Camera location|Globe location)\| *([0-9.]+) +([0-9.]+) +([0-9.]+) *([NS]) *[,|]? *([0-9.]+) +([0-9.]+) +([0-9.]+) *([EW])', flags=re.IGNORECASE)
# {{Location|34 1 27.37 N 116 9 29.88 W|region:DE-NI_scale:10000_heading:SW}}

# Compile regular expressions
FILECATRE = re.compile(r'\[\[Category:(.+)]]', flags=re.IGNORECASE)

# Q-numbers in first parameter
# /Information
# Zabytek nieruchomy                    # https://commons.wikimedia.org/wiki/Template:Zabytek_nieruchomy (Polish heritage IDs)
## https://learn.microsoft.com/en-us/dotnet/standard/base-types/quantifiers-in-regular-expressions
INFOQSUFFRE = re.compile(r'{{([^{]+/Information|[Zz]abytek nieruchomy)\|(Q[0-9]+)}}')

MSUFFRE = re.compile(r'M[0-9]+')        # M-numbers
PROPRE = re.compile(r'P[0-9]+')             # P-number
QSUFFRE = re.compile(r'Q[0-9]+')            # Q-number

# Get language list
main_languages = get_language_preferences()
mainlang = main_languages[0]

# Get parameters
pgmnm = sys.argv.pop(0)
pywikibot.info('{}, {}, {}, {}'.format(pgmnm, pgmid, pgmlic, creator))

# Connect to databases
site = pywikibot.Site('commons')
site.login()                    ### Must login; is this really necessary?
cbotflag = 'bot' in pywikibot.User(site, site.user()).groups()

# This script requires a bot flag
repo = site.data_repository()
wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

# Initialise
page_list = set()
geocoord_locality = ()      # No locality coordinates
surface_text = 'unknown'

# Get qualifiers
inpar = None
while sys.argv:
    inpar = sys.argv.pop(0)
    if inpar[:1] != '-':
        break
    elif inpar == '-c':         # Recurse category
        recurse_list = True
    elif inpar == '-r':         # Range value
        inpar = sys.argv.pop(0)
        max_range = min(int(inpar), MAX_RANGE)
    elif inpar == '-v':         # Include revisions
        include_revisions = True
    else:
        pywikibot.warning('Invalid qualifier {}'.format(inpar))
    inpar = None

# Get list of media files from input parameters (either P1 or stdin)
# No parameters: stdin media file list
# 1 parameter: Wikimedia Commons Category, or User: creations
# 2 parameters: P/Q value pair

if not inpar:
    # There are no parameters
    # Read Wikimedia Commons media file list from stdin, one file per line
    # Either M-file ID, or File:
    inputfile = sys.stdin.read()
    input_list = sorted(set(inputfile.splitlines()))
    for subject in input_list:
        # Get filename
        subject = get_url_pagename(subject)
        if subject:
            try:
                if MSUFFRE.search(subject):
                    # Get media file via M-identifier (upppercase M)
                    page = pywikibot.MediaInfo(site, subject).file
                else:
                    # Get media via file name
                    page = pywikibot.FilePage(site, subject)
                # Add file to list
                page_list.add(page)
            except Exception as error:
                pywikibot.error('{}, {}'.format(subject, error))
elif len(sys.argv) > 1:
    # More parameters available: P/Q value pair
    ### Should accept compound statements with 1 single argument...
    # Get mediafiles via P:Q search, e.g. P1071:Q492351 = all photos of objects in De Haan
    # https://commons.wikimedia.org/wiki/Commons:Structured_data/Media_search
    # https://www.mediawiki.org/wiki/Help:MediaSearch
    # https://www.mediawiki.org/wiki/Manual:Special_pages
    # https://www.mediawiki.org/wiki/Extension:MediaSearch
    # https://www.mediawiki.org/wiki/API:Search
    # https://www.mediawiki.org/w/api.php?action=help&modules=main#main/datatypes

    # You should first start with small localities
    # to avoid asssing a too general locality...
    # So in sequence: locality, deelgemeente/district, city
    propty = PROPRE.findall(inpar.upper())[0]

    try:
        inpar = sys.argv.pop(0)
        # Item separated from property
        locality_qnumber = QSUFFRE.findall(inpar.upper())[0]
    except:
        # Property with concatenated item
        locality_qnumber = QSUFFRE.findall(inpar.upper())[0]

    locality_item = get_item_page(locality_qnumber)
    pywikibot.info('Searching media files for {}:{} ({}:{})'
                   .format(get_property_label(propty),
                           get_item_header(locality_item.labels),
                           propty, locality_qnumber))

    # Now we set additional parameters, depending on the property
    if propty == CREALOCPROP:
        """
We could add P1071 SDC assignment if object within 3 km range from P625?

Search for P1071:Q2460559
https://commons.wikimedia.org/w/index.php?search=P1071%3AQ2460559&title=Special:MediaSearch&type=image

propty = 'P1071'
locality_qnumber = 'Q2460559'
        """
        if SURFACEPROP in locality_item.claims:
           # We take the first value of the locality surface
           surface_value = locality_item.claims[SURFACEPROP][0].getTarget()
           # WbQuantity(amount=2.89, upperBound=None, lowerBound=None, unit=http://www.wikidata.org/entity/Q712226)
           # https://www.wikidata.org/wiki/Q712226 = square km
           locality_surface = float(surface_value.amount)
           surface_item = QSUFFRE.findall(surface_value.unit)[0]
           surface_coeff = surface_unit_list[surface_item][0]
           surface_unit = surface_unit_list[surface_item][1]
           surface_text = str(locality_surface) + ' ' + surface_unit
           # We take a safety coefficient of 75% into account
           locality_radius = int(0.75 * surface_coeff * math.sqrt(locality_surface/PI))
           # Assuming circular range (take care of non-km units)
           max_range = min(locality_radius, MAX_RANGE)

        if max_range > int(MAX_RANGE / 2):
            pywikibot.warning('Run script first for locality, before city; range is {} m'.format(max_range))

        if GEOLOCATIONPROP in locality_item.claims:
           # Earth coordindate
           # Coordinate(lat=50.833333333333, lon=4.7666666666667, entity=http://www.wikidata.org/entity/Q2)
           geoloc_locality = locality_item.claims[GEOLOCATIONPROP][0].getTarget()
           geocoord_locality = (geoloc_locality.lat, geoloc_locality.lon)   # We assume earth coordinates
           pywikibot.info('Geolocation: {}, surface {}, radius {} m'
                          .format(geocoord_locality, surface_text, max_range))

    ###elif ### Possibly other functionality...

    # Search P/Q values
    params = {'action': 'query',        # Mediafile search
              'list': 'search',
              'srnamespace': 6,         # File namespace
              'srsearch': propty + ':' + locality_qnumber, # Trigger Wikimedia Commons Cirrus search (AI like search)
              'srwhat': 'text',
              'format': 'json',
              'srprop': 'size',         # Limit returned data
              'srlimit': MAX_ITEMS}     # Should be reasonable value (sorted by decreasing relevance, i.e. PDF files at the end)
    request = api.Request(site=site, parameters=params)
    result = request.submit()

    """
{'query-continue': {'search': {'sroffset': 50}}, 'query': {'searchinfo': {'totalhits': 1616, 'suggestion': 'p101 q2460559', 'suggestionsnippet': '<em>p101</em> q2460559'}, 'search': [{'ns': 6, 'title': 'File:Kerk Mollem in de steigers (2015).jpg', 'pageid': 59334855, 'size': 507, 'wordcount': 137, 'snippet': 'DescriptionKerk <span class="searchmatch">Mollem</span> in de steigers (2015).jpg English: Church <span class="searchmatch">Mollem</span> in the scaffolds (2015) Français\xa0: Église <span class="searchmatch">Mollem</span> en construction (2015) Deutsch: <span class="searchmatch">Mollem</span> Kirche', 'timestamp': '2023-07-08T06:37:48Z'}, ...

{'query-continue': {'search': {'sroffset': 500}}, 'query': {'searchinfo': {'totalhits': 1616, 'suggestion': 'p101 q2460559', 'suggestionsnippet': '<em>p101</em> q2460559'}, 'search': [{'ns': 6, 'title': 'File:Kerk Mollem in de steigers (2015).jpg', 'pageid': 59334855, 'size': 507}, ...

{'query': {'searchinfo': {'totalhits': 1616, 'suggestion': 'p101 q2460559', 'suggestionsnippet': '<em>p101</em> q2460559'}, 'search': [{'ns': 6, 'title': 'File:Kerk Mollem in de steigers (2015).jpg', 'pageid': 59334855, 'size': 507}, ...

    """

    # Get the list of media files
    if 'query' in result and 'search' in result['query']:
        ##print(result['query']['searchinfo'])
        ##print(result['query']['search'][1615])

        # Loop though items
        for row in result['query']['search']:
            # Get media via file name
            subject = row['title']
            page = pywikibot.FilePage(site, subject)
            page_list.add(page)
elif inpar[:5] == 'User:':
    # Get user uploads
    site_user = inpar.split(':')
    wikiuser = pywikibot.User(site, site_user[1])

    """
WARNING: API warning (main): Subscribe to the mediawiki-api-announce mailing list at <https://lists.wikimedia.org/postorius/lists/mediawiki-api-announce.lists.wikimedia.org/> for notice of API deprecations and breaking changes. Use [[Special:ApiFeatureUsage]] to see usage of deprecated features by your application.
WARNING: API warning (usercontribs): The parameter "uctoponly" has been deprecated.
https://commons.wikimedia.org/wiki/Special:ApiFeatureUsage

ERROR: Error processing entity/M111772578 File:Obsolete Belgian railway sign.jpg by -, 'Page' object has no attribute 'latest_file_info'

    """

    # This query gets all File updates
    # How to only obtain creation contributions?
    # How to get all created files?
    for subject in wikiuser.contributions(
            total=50000, namespaces=FILENAMESPACE): #, top_only=True): #, reverse=True):
        # subject contains page title, revid, timestamp, comment
        page = pywikibot.FilePage(site, subject[0].title())
        while page.isRedirectPage():
            page = page.getRedirectTarget()
        # Only keep page creations
        # We could also list File amends
        if include_revisions or page.oldest_revision.user == wikiuser.username:
            page_list.add(page)
else:
    # Get Wikimedia Commons page list from category (P1)
    subject = get_url_pagename(inpar)

    # Get recursive media file list from category
    try:
        cat_list = pywikibot.Category(site, subject)
        pywikibot.info(cat_list.title())
        pywikibot.info(cat_list.categoryinfo)
        page_list = pg.CategorizedPageGenerator(cat_list, recurse=recurse_list)
        # Page generator does no longer support len() function
        page_list = set(page_list)
    except Exception as error:
        pywikibot.critical(error)

# Unused parameters/qualifiers
while sys.argv:
    inpar = sys.argv.pop(0)
    pywikibot.warning('Redundant parameter or qualifier {}'.format(inpar))

pywikibot.info('{:d} media files in list'.format(len(page_list)))

if page_list:
    # Gather heritage ID properties
    heritage_propx = {}
    heritage_regex = r'{{'
    regex_sep = '('
    pywikibot.info('Reading metadata')
    for val in heritage_prop_list:
        heritage_propx[heritage_prop_list[val]] = pywikibot.PropertyPage(repo, heritage_prop_list[val])
        heritage_regex += regex_sep + val
        regex_sep = '|'

        # Optional JURISDICTIONPROP
        jurisdict = ''
        if JURISDICTIONPROP in heritage_propx[heritage_prop_list[val]].claims:
            jurisdict = ', {} ({})'.format(get_item_header(heritage_propx[heritage_prop_list[val]].claims[JURISDICTIONPROP][0].getTarget().labels),
                       heritage_propx[heritage_prop_list[val]].claims[JURISDICTIONPROP][0].getTarget().getID())

        pywikibot.info('{} ({}) is een {} ({}) in {} ({}){}'.format(val, heritage_prop_list[val],
                       get_item_header(heritage_propx[heritage_prop_list[val]].claims[INSTANCEPROP][0].getTarget().labels),
                       heritage_propx[heritage_prop_list[val]].claims[INSTANCEPROP][0].getTarget().getID(),
                       get_item_header(heritage_propx[heritage_prop_list[val]].claims[COUNTRYPROP][0].getTarget().labels),
                       heritage_propx[heritage_prop_list[val]].claims[COUNTRYPROP][0].getTarget().getID(),
                       jurisdict))
    heritage_regex += r')\|([0-9/A-Z-]+)}}'     # Heritage ID consists of uppercase letters, digits, and "-"
    pywikibot.debug(heritage_regex)
    HERITAGEIDRE = re.compile(heritage_regex)   # Heritage ID

# Loop through the list of media files
transcount = 0	    	# Total transaction counter
false_positive_count = 0
prevnow = datetime.now()

for page in page_list:
    now = datetime.now()	        # Refresh the timestamp to time the following transaction
    isotime = now.strftime("%Y-%m-%d %H:%M:%S") # Needed to format output
    transcount += 1
    pywikibot.info('\n{:d}\t{}'.format(transcount, isotime))

    try:
        # We only accept the File namespace
        media_name = page.title()
        #print(media_name)
        if page.namespace() != FILENAMESPACE:
            pywikibot.info('Skipping {}:{}'
                           .format(site.namespace(page.namespace()), media_name))
            continue
        media_identifier = 'M' + str(page.pageid)
        # https://commons.wikimedia.org/wiki/Special:EntityPage/M63763537
        # https://commons.wikimedia.org/entity/M63763537
        # Page info: https://commons.wikimedia.org/w/index.php?title=File:Geert_Van_Pamel-IMG_1572.JPG&action=info

        # Get standaard media file information
        file_user = '-'
        file_info = page.latest_file_info.__dict__
        file_user = file_info['user']
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
        for descr in file_info:
            if descr == 'metadata':
                if file_info[descr]:
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
        file_height = 0
        if 'height' in file_info:
            file_height = file_info['height']

        # Get image width
        file_width = 0
        if 'width' in file_info:
            file_width = file_info['width']

        pywikibot.log('Media size: {:d} {:d}:{:d}'
                      .format(file_size, file_width, file_height))

        # Get media SDC data
        request = site.simple_request(action='wbgetentities', ids=media_identifier)
        row = request.submit()

        sdc_data = row.get('entities').get(media_identifier)
        # Key attributes: pageid, ns, title, labels, descriptions, statements <- depicts, MIME type
        ## {'pageid': 125667911, 'ns': 6, 'title': 'File:Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot.pdf', 'lastrevid': 707697714, 'modified': '2022-11-18T20:06:23Z', 'type': 'mediainfo', 'id': 'M125667911', 'labels': {'nl': {'language': 'nl', 'value': 'Wikidata ISBN-boekbeschrijving met ISBNlib en Pywikibot'}, 'en': {'language': 'en', 'value': 'Wikidata ISBN book description with ISBNlib and Pywikibot'}, 'fr': {'language': 'fr', 'value': 'Description du livre Wikidata ISBN avec ISBNlib et Pywikibot'}, 'de': {'language': 'de', 'value': 'Wikidata ISBN Buchbeschreibung mit ISBNlib und Pywikibot'}, 'es': {'language': 'es', 'value': 'Descripción del libro de Wikidata ISBN con ISBNlib y Pywikibot'}}, 'descriptions': {}, 'statements': []}

        # List of items where a media file could be added
        item_list = []
        geocoord = ()
        preferred = False

        #pywikibot.debug(sdc_data)
        sdc_statements = sdc_data.get('statements')
        #pywikibot.debug(sdc_statements)
        if not sdc_statements:
            # Old images do not have statements
            pywikibot.info('No statements for {} {} {} by {}'
                           .format(file_type[0], media_identifier, media_name, file_user))
            depict_list = []
            location_item = []
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
            if not depict_list:
                # A lot of media files do not have depict statements.
                # Please add depict statements for each media file.
                pywikibot.info('No depicts for {} entity/{} {} by {}'
                               .format(file_type[0], media_identifier, media_name, file_user))
                depict_list = []

            for ind in {INSTANCEPROP, GENREPROP}:
                # Get file type from SDC statements
                instance_list = sdc_statements.get(ind)
                if instance_list:
                    # Add file type from instance list
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
                # Loop through the list of SDC P180 statements
                """
{'mainsnak':
    {'snaktype': 'value', 'property': 'P180', 'hash': 'de0ee4f082bfc89cdb25db93cc21755315974690',
    'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 2125610, 'id': 'Q2125610'}, 'type': 'wikibase-entityid'}
    },
'type': 'statement', 'id': 'M103310973$b63c02fb-495b-1c28-36a5-105f10aa6698', 'rank': 'preferred'
}
                """
                # Get the Q-number for item
                if 'datavalue' in depict['mainsnak']:
                    item = get_sdc_item(depict['mainsnak'])
                    qnumber = item.getID()

                    #### Try to get the original item and the image type
                    if (qnumber in image_types
                            and 'qualifiers' in depict
                            and QUALIFYFROMPROP in depict['qualifiers']):       ## Deprecated (should be migrated to the next)
                        """
{'P462': [{'snaktype': 'value', 'property': 'P462', 'hash': '4af9c81cc458bf6b99699673fd9268b43ad0c4d4', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 23445, 'id': 'Q23445'}, 'type': 'wikibase-entityid'}}]}
                        """
                        # https://commons.wikimedia.org/wiki/Commons:Bots/Requests/GeertivpBot#GeertivpBot_(overleg_%C2%B7_bijdragen)
                        file_type.insert(0, image_types[qnumber])
                        item = get_sdc_item(depict['qualifiers'][QUALIFYFROMPROP][0])
                        qnumber = item.getID()
                    ###elif (qualifier)
                    elif 'qualifiers' in depict:
                        for propty in depict['qualifiers']:
                            if propty in [DEPICTFORMATPROP, REPRESENTATIONTYPEPROP]:
                                # https://commons.wikimedia.org/wiki/Commons:Bots/Requests/GeertivpBot#GeertivpBot_(overleg_%C2%B7_bijdragen)
                                # https://commons.wikimedia.org/w/index.php?title=File%3AHadewijch_gedicht1_HsGent_f49r.jpg&diff=997722458&oldid=997623611
                                for ind in depict['qualifiers'][propty]:
                                    depict_format = get_item_page(ind['datavalue']['value']['id']).getID()
                                    if depict_format in image_types:
                                        file_type.insert(0, image_types[depict_format])
                            else:
                                # Ignore items with "applies to" qualifiers
                                # We will still log a warning
                                # https://commons.wikimedia.org/wiki/File:Dinant_NMBS_333_IC-Brussel_(OCT_2010).JPG
                                for ind in depict['qualifiers'][propty]:
                                    """
Possible problems:

When using get_sdc_item:
https://commons.wikimedia.org/w/index.php?title=File:Garmin_GPS_at_Greenwich_Observatory.jpg&oldid=710918494
ERROR: Error processing entity/M10814205 File:Garmin GPS at Greenwich Observatory.jpg by Bdell555, 'datavalue'
KeyError: 'datavalue'

ERROR: Error processing entity/M3402186 File:Abraham Govaerts Vierge à l'enfant.JPG by Mn92100~commonswiki, string indices must be integers
                                    """
                                    if isinstance(ind['datavalue']['value'], str):
                                        restricted_item = ind['datavalue']['value']
                                    elif 'time' in ind['datavalue']['value']:
                                        restricted_item = ind['datavalue']['value']['time']
                                    elif 'id' in ind['datavalue']['value']:
                                        restricted_item = ind['datavalue']['value']['id']
                                    else:
                                        restricted_item = str(ind['datavalue']['value'])
                                    prop_label = get_property_label(propty)
                                    pywikibot.warning('Skipping qualifier {} ({}): {} for item {} ({}) of {} entity/{} {}'
                                                      .format(prop_label, propty,
                                                              restricted_item,
                                                              get_item_header(item.labels), qnumber,
                                                              file_type[0], media_identifier, media_name))

                    # Preferred images overrule normal images
                    if qnumber in image_types:
                        # Overrule the image type
                        file_type.insert(0, image_types[qnumber])
                    elif depict['rank'] == PREFERRED_RANK:
                        # Overrule normal items; accumulate preferred values
                        if not preferred:
                            item_list = []
                        item_list.append(item)
                        preferred = True
                    elif not preferred:
                        # Add a normal ranked item to the list;
                        # drop normal items when there are already preferred items
                        item_list.append(item)

            # Skip depict statements for GLAM collections, unless preferred
            collection_list = sdc_statements.get(COLLECTIONPROP)
            if collection_list:
                # generally describe parts of painting objects;
                collection_item = get_sdc_item(collection_list[0]['mainsnak'])
                if not item_list:
                    pywikibot.info('{} entity/{} {} by {} belongs to collection {} ({}), without depicts'
                                   .format(file_type[0], media_identifier, media_name, file_user,
                                           get_item_header(collection_item.labels), collection_item.getID()))
                elif not (preferred or len(item_list) == 1):
                    # Skip the item_list, unless there is a preferred statement describing the artwork itself.
                    pywikibot.info('{} entity/{} {} by {} belongs to collection {} ({}), and not preferred {}'
                                   .format(file_type[0], media_identifier, media_name, file_user,
                                           get_item_header(collection_item.labels), collection_item.getID(), item_list))
                    item_list = []

            # Get geolocation from EXIF metadata
            # 1° ~ 111 km -- 0,00001° ~ 1 m
            # Object location has priority over camera location
            # GPS accuracy is 10 m at best...
            # We assume one single geolocation, from EXIF data.
            for seq in location_target:
                location_coord = sdc_statements.get(seq[1])
                if location_coord:
                    geocoord = (float(location_coord[0]['mainsnak']['datavalue']['value']['latitude']),
                                float(location_coord[0]['mainsnak']['datavalue']['value']['longitude']))
                    pywikibot.info('{}: {:.5f},{:.5f}/{}'
                                   .format(seq[0], geocoord[0], geocoord[1],
                                           location_coord[0]['mainsnak']['datavalue']['value']['altitude']))

            # Get nominative object location from SDC
            location_item = sdc_statements.get(CREALOCPROP)
            if location_item:
                """
    [{'mainsnak': {'snaktype': 'value', 'property': 'P1071', 'hash': 'dc1800c29d76cd66657b485bd7a5fe1d51639b49', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 663764, 'id': 'Q663764'}, 'type': 'wikibase-entityid'}}, 'type': 'statement', 'id': 'M152516922$562b64ed-428e-7ee1-2f06-917a131e67a6', 'rank': 'preferred'}]
                """
                for seq in location_item:
                    # Should get the administrative or local territorial entity
                    creation_loc_item = seq['mainsnak']['datavalue']['value']['id']
                    pywikibot.info('Locality: {} ({})'
                                   .format(get_item_header(get_item_page(creation_loc_item).labels),
                                           creation_loc_item))

        try:
            # Overrule the EXIF data from Wiki text (camera viewpoints could be inaccurate)
            # Recognize variant formats
            # We assume the two formats are not both registered...
            geolocation = DECIMALGEOLOCATIONRE.findall(page.text)
            for geoloc in geolocation:
                ##print(geoloc)
                lat = float(geoloc[1])
                lon = float(geoloc[2])
                # Only accept decimal format; exclude DMS format
                if (lat - int(lat) != 0.0 and lon - int(lon) != 0.0):
                    geocoord = (lat, lon)
                    pywikibot.info('{}: {:.5f},{:.5f}'.format(geoloc[0], lat, lon))

            for ind in range(len(DMSGEOLOCATIONRE)):
                geolocation = DMSGEOLOCATIONRE[ind].findall(page.text)
                #pdb.set_trace()
                for geoloc in geolocation:
                    ##print(geoloc)
                    lat = float(geoloc[1]) + (float(geoloc[2]) + float(geoloc[3])/60.0)/60.0
                    if geoloc[4] in 'Ss': lat = -lat
                    lon = float(geoloc[5]) + (float(geoloc[6]) + float(geoloc[7])/60.0)/60.0
                    if geoloc[8] in 'Ww': lon = -lon
                    geocoord = (lat, lon)
                    pywikibot.info('{}: {:.5f},{:.5f}'.format(geoloc[0], lat, lon))

        except Exception as error:
            pywikibot.error(error)

        # Assume object not in range
        distance = max_range
        if geocoord_locality:
            if geocoord:
                # geocoord_locality = (50.83333, 4.76667)
                # geocoord = (50.82773, 4.75975)
                # We calculate the approximate distance (Pythagoras!)
                # We assume having a "nearby" bird distance... so the accuracy is within GPS accuracy (10 m)
                # So we don't need to calculate with polar coordinates/flat plane approximation is sufficient
                distance = int(EST_DEGREE_DIST * math.sqrt((geocoord_locality[0] - geocoord[0]) ** 2 + (geocoord_locality[1] - geocoord[1]) ** 2))
                pywikibot.info('Estimated distance: {} m'.format(distance))

                # Add the locality where the image is taken
                # if the "picture locality of creation" is missing
                # and the object is in the neighbourhood of the locality
                if distance < max_range:
                    if not location_item:
                        set_sdc_property_value(CREALOCPROP, locality_item, NORMAL_RANK)
                    prevnow = datetime.now()
                elif distance > MAX_RANGE:
                    pywikibot.error('Possibly false positive for {} ({}) for {} entity/{} {} by {}'
                                    .format(get_item_header(locality_item.labels), locality_qnumber,
                                            file_type[0], media_identifier, media_name, file_user))
                    false_positive_count += 1
                    if false_positive_count >= 20:
                        sys.exit(4)
            elif file_type[0] == 'pdf' or (now - prevnow).total_seconds() > 300:
                pywikibot.critical('Potential hallucination issue {} ({}) for {} entity/{} {} by {}'
                                   .format(get_item_header(locality_item.labels), locality_qnumber,
                                           file_type[0], media_identifier, media_name, file_user))
                sys.exit(5)

        # Find "/Information" item numbers from Wiki text and store them as SDC
        heritage_item_list = set()
        ### How to limit the {{ range??
        info_item_list = INFOQSUFFRE.findall(page.text)
        for heritage_item in info_item_list:
            heritage_item_list.add(heritage_item[1])
            pywikibot.info('{} {} found for {} entity/{} {} by {}'
                           .format(heritage_item[0], heritage_item[1], file_type[0], media_identifier, media_name, file_user))

        # Find heritage ID in page description
        heritage_id_list = HERITAGEIDRE.findall(page.text)
        for hertitage_id in heritage_id_list:
            # Search heritage object in Wikidata
            heritage_list = get_item_with_prop_value(heritage_prop_list[hertitage_id[0]], hertitage_id[1])
            if not heritage_list:
                # Heritage ID is not registered
                pywikibot.info('{} ({}:{}) is not linked to Wikidata item at {} entity/{} {} by {}'
                               .format(hertitage_id[0], heritage_prop_list[hertitage_id[0]], hertitage_id[1],
                                       file_type[0], media_identifier, media_name, file_user))
            elif len(heritage_list) > 1:
                # Ambigious heritage item; multiple buildings registered with same number
                # https://commons.wikimedia.org/w/index.php?title=File:Br%C3%BCgge_(B),_Belfort_von_Br%C3%BCgge_--_2018_--_8611.jpg&oldid=prev&diff=835341191
                # https://www.wikidata.org/w/index.php?search=P1764%3A29457&title=Special%3ASearch&ns0=1&ns120=1
                # https://commons.wikimedia.org/wiki/User:XRay
                pywikibot.info('{} {} {} entity/{} {} by {} has ambigious items {}'
                               .format(hertitage_id[0], hertitage_id[1],
                                       file_type[0], media_identifier, media_name, file_user,
                                       [item.getID() for item in heritage_list]))
            else:
                # Unique heritage item number found
                item = heritage_list.pop()
                hertitage = item.getID()
                heritage_item_list.add(hertitage)
                if len(item.claims[heritage_prop_list[hertitage_id[0]]]) == 1:
                    # Unique building found
                    pywikibot.info('Found {} ({}:{}) {} ({}) for {} entity/{} {} by {}'
                                   .format(hertitage_id[0], heritage_prop_list[hertitage_id[0]], hertitage_id[1],
                                           get_item_header(item.labels), hertitage,
                                           file_type[0], media_identifier, media_name, file_user))
                else:
                    # Multiple heritage IDs found for building
                    monument_code = [seq.getTarget() for seq in item.claims[heritage_prop_list[hertitage_id[0]]]]
                    pywikibot.info('Ambigious monument codes {} ({}:{}) {} ({}) for {} entity/{} {} by {}'
                                   .format(hertitage_id[0], heritage_prop_list[hertitage_id[0]], monument_code,
                                           get_item_header(item.labels), hertitage,
                                           file_type[0], media_identifier, media_name, file_user))

                # Assign missing country statements
                target_property = heritage_propx[heritage_prop_list[hertitage_id[0]]]

                # Do not add jurisdiction, part of the country to the item
                # https://www.wikidata.org/wiki/Property:P1001#P2303
                # Justidiction is not used for buildings and monuments (only for heritage IDs)
                for propty in [COUNTRYPROP]:    ##, JURISDICTIONPROP]:
                    # Constraint: A heritage item should belong to one single country
                    if (propty in target_property.claims and (propty not in item.claims
                            or not item_is_in_list(item.claims[propty],
                                                   [target_property.claims[propty][0].getTarget().getID()]))):
                        # Get the country/jurisdiction item from the campaign
                        # Amend item if value is not already registered
                        claim = pywikibot.Claim(repo, propty)
                        claim.setTarget(target_property.claims[propty][0].getTarget())
                        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                        pywikibot.warning('Add {} ({}) {} ({})'
                                          .format(get_property_label(propty), propty,
                                                  get_item_header(target_property.claims[propty][0].getTarget().labels),
                                                  target_property.claims[propty][0].getTarget().getID()))

        # Add all items to depict
        for qnumber in heritage_item_list:
            item = get_item_page(qnumber)

            # We trust heritage item numbers and coordinates.
            # Register geocoordinates in Wikidata if not already registered.
            # We don't do the opposite because we don't always trust the Wikidata depict statements.
            if geocoord and GEOLOCATIONPROP not in item.claims:
                # Set the right latitude and longitude accuracy (disallow too many decimal digits)
                # approx. 1 m accuracy (1° ~ 111 km latitude corresponds to 5 decimals)
                # https://doc.wikimedia.org/pywikibot/master/_modules/scripts/claimit.html
                lat = float('{:.5f}'.format(geocoord[0]))
                lon = float('{:.5f}'.format(geocoord[1]))
                claim = pywikibot.Claim(repo, GEOLOCATIONPROP)
                claim.setTarget(pywikibot.Coordinate(lat, lon, precision=0.00001))
                """
[Claim.fromJSON(DataSite("wikidata", "wikidata"), {'mainsnak': {'snaktype': 'value', 'property': 'P625', 'datatype': 'globe-coordinate', 'datavalue': {'value': {'latitude': 50.959153, 'longitude': 4.232143, 'altitude': None, 'globe': 'http://www.wikidata.org/entity/Q2', 'precision': 1e-06}, 'type': 'globecoordinate'}}, 'type': 'statement', 'id': 'Q122372103$1e429752-b921-47f7-9e1c-6dbda5697fad', 'rank': 'preferred'})]
                """
                item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                pywikibot.warning('Add geolocation {:.5f},{:.5f}'
                                  .format(lat, lon))

            if item not in item_list:
                # Add item number to depicts list
                item_list.insert(0, item)

                # Verify if item is in SDC depict
                depict_missing = cbotflag
                for depict in depict_list:
                    if qnumber == get_sdc_item(depict['mainsnak']).getID():
                        depict_missing = False
                        break

                if depict_missing:
                    # Preferred, because it comes from a Wiki text /Information template
                    set_sdc_property_value(DEPICTSPROP, item, PREFERRED_RANK)

        # Show item list
        pywikibot.debug(file_type)
        for item in item_list:
            pywikibot.info('{} ({})'.format(get_item_header(item.labels), item.getID()))

        if file_type[0] not in all_media_props:
            # Unrecognized media type; assume default "image"
            # In that case the missing media type must be added to the list
            pywikibot.error('File type {} not in media_props'
                            .format(file_type[0]))
            all_media_props[file_type[0]] = RLTDIMAGEPROP
        media_type = all_media_props[file_type[0]]

        # Check if the media file is used by another Wikidata item
        # This includes e.g. P10 video, P18 image, P51 audio, etc.
        # Possibly other links...
        image_used = False
        media_page = pywikibot.FilePage(repo, media_name)
        for file_ref in pg.FileLinksGenerator(media_page):
            if file_ref.namespace() == MAINNAMESPACE:
                # We only take Qnumbers into account for primary namespaces
                # e.g. we ignore descriptive, project or talk pages
                # Show all connected item numbers
                ## Other usage info's via item_ref?
                image_used = True
                item_ref = get_item_page(file_ref.title())
                pywikibot.info('Already used {} ({}) entity/{} {} by {} in item {} ({})'
                               .format(file_type[0], media_type,
                                       media_identifier, media_name, file_user,
                                       get_item_header(item_ref.labels), item_ref.getID()))
        if image_used:
            # Image is already used, so skip (avoid flooding Wikidata)
            continue

        # Filter on minimum image resolution.
        # Allow low resolution for logo and other small images.
        # Skip low quality images where large images are expected.
        if (not property_is_in_list(small_images, file_type) and (
                file_size > 0 and file_size < MINFILESIZE
                or file_height > 0 and file_height < MINRESOLUTION
                    and file_width > 0 and file_width < MINRESOLUTION)):
            pywikibot.info('Small {} ({}) entity/{} {} by {} size {:d} {:d}:{:d}'
                           .format(file_type[0], media_type,
                                   media_identifier, media_name, file_user,
                                   file_size, file_width, file_height))
            continue

        for item in item_list:
            # Loop through the target Wikidata items to find the first match
            if (    # Skip obvious depicts (photo)
                    item.getID() == PHOTOINSTANCE
                    # Have one single image per Wikidata item (avoid pollution)
                    or media_type in item.claims
                    # Skip when neither instance, nor subclass
                    or not property_is_in_list(item.claims, object_class_props)
                    # We skip publications (good relevant images are extremely rare due to copyright)
                    or property_is_in_list(item.claims, published_work_props)
                    # Skip Wikimedia disambiguation and category items;
                    # we want real items;
                    # see https://www.wikidata.org/wiki/Property:P18#P2303
                    or (INSTANCEPROP in item.claims
                        and item_is_in_list(item.claims[INSTANCEPROP], skipped_instances))
                    # Human and artwork images are incompatible (distinction between artist and oevre)
                    or (INSTANCEPROP in item.claims
                        and item_is_in_list(item.claims[INSTANCEPROP], human_class)
                        and media_type not in human_media_props)
                    # Only register media files to items in the main namespace, otherwise skip
                    or item.namespace() != MAINNAMESPACE):

                    ## Proactive constraint check (how could we do this?)
                    # Does there exist a method?

                    # Note that we unconditionally accept all P279 subclasses

                    # Could there possibly exist a condition to trigger Related image (P6802)?
                continue
            else:
                # Now we can add the media file to a Wikidata item
                # Only the first matching item will be registered

                # Get media label
                media_label = get_sdc_label(sdc_data.get('labels')) # Bijschrift
                # The GUI allows to only register labels?
                if not media_label:
                    media_label = '-'

                # Get SDC media description
                ## ?? Why are descriptions nearly always empty? How could this be registered?
                # Shouldn't Wiki text descriptions be digitized? (extract the EN description?)
                media_description = get_sdc_label(sdc_data.get('descriptions'))
                if media_description:
                    pywikibot.log(media_description)

                # Add media statement to the item
                prop_label = get_property_label(media_type)
                # Skip Property because already included in standard Wikidata comment
                depictsdescr = ('from [[c:Special:EntityPage/{2}|{2}]] SDC'
                                .format(prop_label, media_type, media_identifier))
                claim = pywikibot.Claim(repo, media_type)
                claim.setTarget(page)
                """
Claim.fromJSON(DataSite("wikidata", "wikidata"), {'mainsnak': {'snaktype': 'value', 'property': 'P94', 'datatype': 'commonsMedia', 'datavalue': {'value': 'Ardooie Wapen - 25381 - onroerenderfgoed.jpg', 'type': 'string'}}, 'type': 'statement', 'rank': 'preferred'})
                """
                item.addClaim(claim, bot=wdbotflag, summary=transcmt + ' ' + depictsdescr)
                pywikibot.warning('{} ({}): add {} ({}) {} size {:d} {:d}:{:d} from entity/{} {} by {}'
                                  .format(get_item_header(item.labels), item.getID(),
                                          prop_label, media_type, media_label,
                                          file_size, file_width, file_height,
                                          media_identifier, media_name, file_user))
                # Do we require a reference?
                # Probably not; because the medium file is implicitly described by the SDC claim comment.

                # We are done; only one single media use
                break
        else:
            if item_list:
                # All media item slots were already taken in item (by other media files)
                # Solution: maybe we could add more appropriate depicts statements,
                # and then rerun the script?
                pywikibot.info('Redundant {} ({}) entity/{} {} by {} for items {}'
                               .format(file_type[0], media_type,
                                       media_identifier, media_name, file_user,
                                       [val.getID() for val in item_list]))

        ### Remove obsolete categories

        if False:
            # Remove redundant categories
            page.text = re.sub(r'\[\[Category:Images from Wiki Loves Heritage Belgium in .... needing check]]\n', '', page.text)

            try:
                # Can be a null edit
                page.save(summary=transcmt)      # Bot flag is automatic
            except Exception as error:
                # Ignore Wikipedia errors
                pywikibot.error('Error saving {}, {}'
                                .format(media_name, error))

        # Show all categories
        category_list = FILECATRE.findall(page.text)
        pywikibot.log('Mediafile categories:')
        for filecat in category_list:
            pywikibot.log(filecat)

    # Log errors
    except Exception as error:
        pywikibot.error('Error processing entity/{} {} by {}, {}'
                        .format(media_identifier, media_name, file_user, error))
        pdb.set_trace()
        if exitfatal:               # Stop on first error
            raise
