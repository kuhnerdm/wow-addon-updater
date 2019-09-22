import packages.requests as requests
import re
import collections
# Site splitter

VersionLink = collections.namedtuple('VersionLink', 'version link')

def findZiploc(addonpage, wow_min, wow_max):
    # Curse
    if addonpage.startswith('https://mods.curse.com/addons/wow/'):
        return curse(convertOldCurseURL(addonpage), wow_min, wow_max)
    elif addonpage.startswith('https://www.curseforge.com/wow/addons/'):
        return curse(addonpage, wow_min, wow_max)

    # Curse Project
    elif addonpage.startswith('https://wow.curseforge.com/projects/'):
        if addonpage.endswith('/files'):
            # Remove /files from the end of the URL, since it gets added later
            return curseProject(addonpage[:-6])
        else:
            return curseProject(addonpage)

    # WowAce Project
    elif addonpage.startswith('https://www.wowace.com/projects/'):
        if addonpage.endswith('/files'):
            # Remove /files from the end of the URL, since it gets added later
            return wowAceProject(addonpage[:-6])
        else:
            return wowAceProject(addonpage)

    # Tukui
    elif addonpage.startswith('https://git.tukui.org/'):
        return tukui(addonpage)

    # Wowinterface
    elif addonpage.startswith('http://www.wowinterface.com/'):
        return wowinterface(addonpage)

    # Invalid page
    else:
        print('Invalid addon page.')


def getCurrentVersion(addonpage, wow_min, wow_max):
    # Curse
    if addonpage.startswith('https://mods.curse.com/addons/wow/'):
        return getCurseVersion(convertOldCurseURL(addonpage), wow_min, wow_max)
    elif addonpage.startswith('https://www.curseforge.com/wow/addons/'):
        return getCurseVersion(addonpage, wow_min, wow_max)

    # Curse Project
    elif addonpage.startswith('https://wow.curseforge.com/projects/'):
        return getCurseProjectVersion(addonpage)

    # WowAce Project
    elif addonpage.startswith('https://www.wowace.com/projects/'):
        return getWowAceProjectVersion(addonpage)

    # Tukui
    elif addonpage.startswith('https://git.tukui.org/'):
        return getTukuiVersion(addonpage)

    # Wowinterface
    elif addonpage.startswith('http://www.wowinterface.com/'):
        return getWowinterfaceVersion(addonpage)

    # Invalid page
    else:
        print('Invalid addon page.')


def getAddonName(addonpage):
    addonName = addonpage.replace('https://mods.curse.com/addons/wow/', '')
    addonName = addonName.replace('https://www.curseforge.com/wow/addons/', '')
    addonName = addonName.replace('https://wow.curseforge.com/projects/', '')
    addonName = addonName.replace('http://www.wowinterface.com/downloads/', '')
    addonName = addonName.replace('https://www.wowace.com/projects/', '')
    addonName = addonName.replace('https://git.tukui.org/', '')
    if addonName.endswith('/files'):
        addonName = addonName[:-6]
    return addonName

def gameVersionLessThanOrEqual(version_one, version_two):
    version_one = version_one.strip()
    version_two = version_two.strip()
    prev_dot_location_one = 0
    prev_dot_location_two = 0
    while(prev_dot_location_one >= 0 and prev_dot_location_two >= 0):
        next_dot_location_one = version_one.find('.', prev_dot_location_one)
        next_dot_location_two = version_two.find('.', prev_dot_location_two)
        if (next_dot_location_one < 0):
            if (next_dot_location_two < 0):
                return int(version_one[prev_dot_location_one:]) <= int(version_two[prev_dot_location_two:]) # if there are no more dots
            return int(version_one[prev_dot_location_one:]) <= int(version_two[prev_dot_location_two:next_dot_location_two]) # if there are no more dots from one
        if (next_dot_location_two < 0):
            return int(version_one[prev_dot_location_one:next_dot_location_one]) <= int(version_two[prev_dot_location_two:]) # if there are no more dots from two
        if (int(version_one[prev_dot_location_one:next_dot_location_one]) < int(version_two[prev_dot_location_two:next_dot_location_two])):
            return True
        if (int(version_one[prev_dot_location_one:next_dot_location_one]) > int(version_two[prev_dot_location_two:next_dot_location_two])):
            return False
        #else they are equal so far check between next dots
        prev_dot_location_one = next_dot_location_one+1
        prev_dot_location_two = next_dot_location_two+1
    return True #they are equal
# Curse

def curseVersionLink(addonpage, wow_min, wow_max):
    page = requests.get(addonpage + '/files')
    page.raise_for_status()   # Raise an exception for HTTP errors
    contentString = str(page.content)
    indexOfVer = 0
    endTag = 0
    downloadId = 0
    while(indexOfVer >= 0):
        indexOfVer = contentString.find('file-link', indexOfVer) # step 1 of 2
        indexOfVer = contentString.find('>', indexOfVer) + 1  # first char of the version string
        endTag = contentString.find('</a>', indexOfVer)  # ending tag after the version string
        indexOfGameVer = contentString.find('<td>', endTag) + 4 #step 1 of 6 column 3
        indexOfGameVer = contentString.find('<td>', indexOfGameVer) + 4 #step 2 of 6 column 4
        indexOfGameVer = contentString.find('<td>', indexOfGameVer) + 4 #step 3 of 6 column 5
        indexOfGameVer = contentString.find('<div', indexOfGameVer) + 4 #step 4 of 6 first sub div
        indexOfGameVer = contentString.find('<div', indexOfGameVer) + 4 #step 5 of 6 second sub div
        indexOfGameVer = contentString.find('>', indexOfGameVer) + 1 #step 6 of 6 end of sub div
        endGameTag = contentString.find('</div>', indexOfGameVer) #end of div
        if (indexOfGameVer < 0 or endGameTag < 0):
            raise Exception('Unable to find game version')
        gameVersion = re.sub(r'[\r\n\s]+|\\n|\\r', '', contentString[indexOfGameVer:endGameTag])
        if (gameVersionLessThanOrEqual(wow_min, gameVersion) and gameVersionLessThanOrEqual(gameVersion, wow_max)):
            indexOfDownloadId = contentString.find('download/', endGameTag) + 9
            endDownloadId = contentString.find('"', indexOfDownloadId)
            if (indexOfDownloadId < 0 or endDownloadId < 0):
                raise Exception('Unable to find download link')
            downloadId = contentString[indexOfDownloadId:endDownloadId].strip()
            break
    if (indexOfVer < 0 or endTag < 0):
        raise Exception('Unable to find file matching min and max game version')
    versionStr = contentString[indexOfVer:endTag].strip()
    linkStr = addonpage + '/download/' + downloadId + '/file'
    versionLink = VersionLink(version=versionStr, link=linkStr)
    return versionLink


def curse(addonpage, wow_min, wow_max):
    if '/datastore' in addonpage:
        return curseDatastore(addonpage)
    try:
        versionLink = curseVersionLink(addonpage, wow_min, wow_max)
        return versionLink.link
    except Exception as err:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        print("{0}".format(err))
        return ''

def curseDatastore(addonpage):
    try:
        # First, look for the URL of the project file page
        page = requests.get(addonpage)
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        endOfProjectPageURL = contentString.find('">Visit Project Page')
        indexOfProjectPageURL = contentString.rfind('<a href="', 0, endOfProjectPageURL) + 9
        projectPage = contentString[indexOfProjectPageURL:endOfProjectPageURL] + '/files'

        # Then get the project page and get the URL of the first (most recent) file
        page = requests.get(projectPage)
        page.raise_for_status()   # Raise an exception for HTTP errors
        projectPage = page.url  # We might get redirected, need to know where we ended up.
        contentString = str(page.content)
        startOfTable = contentString.find('project-file-name-container')
        indexOfZiploc = contentString.find('<a class="button tip fa-icon-download icon-only" href="/', startOfTable) + 55
        endOfZiploc = contentString.find('"', indexOfZiploc)

        # Add on the first part of the project page URL to get a complete URL
        endOfProjectPageDomain = projectPage.find("/", 8)
        projectPageDomain = projectPage[0:endOfProjectPageDomain]
        return projectPageDomain + contentString[indexOfZiploc:endOfZiploc]
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''

def convertOldCurseURL(addonpage):
    try:
        # Curse has renamed some addons, removing the numbers from the URL. Rather than guess at what the new
        # name and URL is, just try to load the old URL and see where Curse redirects us to. We can guess at
        # the new URL, but they should know their own renaming scheme better than we do.
        page = requests.get(addonpage)
        page.raise_for_status()   # Raise an exception for HTTP errors
        return page.url
    except Exception:
        print('Failed to find the current page for old URL "' + addonpage + '". Skipping...\n')
        return ''

def getCurseVersion(addonpage, wow_min, wow_max):
    if '/datastore' in addonpage:
        # For some reason, the dev for the DataStore addons stopped doing releases back around the
        # start of WoD and now just does alpha releases on the project page. So installing the
        # latest 'release' version gets you a version from 2014 that doesn't work properly. So
        # we'll grab the latest alpha from the project page instead.
        return getCurseDatastoreVersion(addonpage)
    try:
        versionLink = curseVersionLink(addonpage, wow_min, wow_max)
        return versionLink.version
    except Exception as err:
        print('Failed to find version number for: ' + addonpage)
        print("{0}".format(err))
        return ''

def getCurseDatastoreVersion(addonpage):
    try:
        # First, look for the URL of the project file page
        page = requests.get(addonpage)
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        endOfProjectPageURL = contentString.find('">Visit Project Page')
        indexOfProjectPageURL = contentString.rfind('<a href="', 0, endOfProjectPageURL) + 9
        projectPage = contentString[indexOfProjectPageURL:endOfProjectPageURL]

        # Now just call getCurseProjectVersion with the URL we found
        return getCurseProjectVersion(projectPage)
    except Exception:
        print('Failed to find alpha version number for: ' + addonpage)


# Curse Project

def curseProject(addonpage):
    try:
        # Apparently the Curse project pages are sometimes sending people to WowAce now.
        # Check if the URL forwards to WowAce and use that URL instead.
        page = requests.get(addonpage)
        page.raise_for_status()   # Raise an exception for HTTP errors
        if page.url.startswith('https://www.wowace.com/projects/'):
            return wowAceProject(page.url)
        return addonpage + '/files/latest'
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''


def getCurseProjectVersion(addonpage):
    try:
        page = requests.get(addonpage + '/files')
        if page.status_code == 404:
            # Maybe the project page got moved to WowAce?
            page = requests.get(addonpage)
            page.raise_for_status() # Raise an exception for HTTP errors
            page = requests.get(page.url + '/files') # page.url refers to the place where the last one redirected to
            page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        startOfTable = contentString.find('project-file-list-item')
        indexOfVer = contentString.find('data-name="', startOfTable) + 11  # first char of the version string
        endTag = contentString.find('">', indexOfVer)  # ending tag after the version string
        return contentString[indexOfVer:endTag].strip()
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''


# WowAce Project

def wowAceProject(addonpage):
    try:
        return addonpage + '/files/latest'
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''


def getWowAceProjectVersion(addonpage):
    try:
        page = requests.get(addonpage + '/files')
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        startOfTable = contentString.find('project-file-list-item')
        indexOfVer = contentString.find('data-name="', startOfTable) + 11  # first char of the version string
        endTag = contentString.find('">', indexOfVer)  # ending tag after the version string
        return contentString[indexOfVer:endTag].strip()
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''


# Tukui

def tukui(addonpage):
    try:
        return addonpage + '/-/archive/master/elvui-master.zip'
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''


def getTukuiVersion(addonpage):
    try:
        response = requests.get(addonpage)
        response.raise_for_status()   # Raise an exception for HTTP errors
        content = str(response.content)
        match = re.search(r'<div class="commit-sha-group">\\n<div class="label label-monospace">\\n(?P<hash>[^<]+?)\\n</div>', content)
        result = ''
        if match:
            result = match.group('hash')
        return result.strip()
    except Exception as err:
        print('Failed to find version number for: ' + addonpage)
        print(err)
        return ''


# Wowinterface

def wowinterface(addonpage):
    downloadpage = addonpage.replace('info', 'download')
    try:
        page = requests.get(downloadpage + '/download')
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        indexOfZiploc = contentString.find('Problems with the download? <a href="') + 37  # first char of the url
        endQuote = contentString.find('"', indexOfZiploc)  # ending quote after the url
        return contentString[indexOfZiploc:endQuote]
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''


def getWowinterfaceVersion(addonpage):
    try:
        page = requests.get(addonpage)
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        indexOfVer = contentString.find('id="version"') + 22  # first char of the version string
        endTag = contentString.find('</div>', indexOfVer)  # ending tag after the version string
        return contentString[indexOfVer:endTag].strip()
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''
