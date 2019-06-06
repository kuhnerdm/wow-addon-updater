import packages.requests as requests
import re

# Site splitter

def findZiploc(addonpage):
    # Curse
    if addonpage.startswith('https://mods.curse.com/addons/wow/'):
        return curse(convertOldCurseURL(addonpage))
    elif addonpage.startswith('https://www.curseforge.com/wow/addons/'):
        return curse(addonpage)

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


def getCurrentVersion(addonpage):
    # Curse
    if addonpage.startswith('https://mods.curse.com/addons/wow/'):
        return getCurseVersion(convertOldCurseURL(addonpage))
    elif addonpage.startswith('https://www.curseforge.com/wow/addons/'):
        return getCurseVersion(addonpage)

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


# Curse

def curse(addonpage):
    if '/datastore' in addonpage:
        return curseDatastore(addonpage)
    try:
        page = requests.get(addonpage + '/download')
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        indexOfZiploc = contentString.find('download__link') + 22  # Will be the index of the first char of the url
        endQuote = contentString.find('"', indexOfZiploc)  # Will be the index of the ending quote after the url
        return 'https://www.curseforge.com' + contentString[indexOfZiploc:endQuote]
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
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

def getCurseVersion(addonpage):
    if '/datastore' in addonpage:
        # For some reason, the dev for the DataStore addons stopped doing releases back around the
        # start of WoD and now just does alpha releases on the project page. So installing the
        # latest 'release' version gets you a version from 2014 that doesn't work properly. So
        # we'll grab the latest alpha from the project page instead.
        return getCurseDatastoreVersion(addonpage)
    try:
        page = requests.get(addonpage + '/files')
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        indexOfVer = contentString.find('file__name full') + 17  # first char of the version string
        endTag = contentString.find('</span>', indexOfVer)  # ending tag after the version string
        return contentString[indexOfVer:endTag].strip()
    except Exception:
        print('Failed to find version number for: ' + addonpage)
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
    addonpage = addonpage + '/tree/master'
    try:
        response = requests.get(addonpage)
        response.raise_for_status()   # Raise an exception for HTTP errors
        content = str(response.content)
        match = re.search(r'<div class="commit-sha-group d-none d-sm-flex">\\n<div class="label label-monospace monospace">\\n(?P<hash>[^<]+?)\\n</div>', content)
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
