import packages.requests as requests

MAX_VERSION_LENGTH = 300

# Site splitter

def findZiploc(addonpage):
    # Curse
    if addonpage.startswith('https://mods.curse.com/addons/wow/'):
        return curse(convertOldCurseURL(addonpage))
    elif addonpage.startswith('https://www.curseforge.com/wow/addons/'):
        return curse(addonpage)

    # Curse Project
    elif addonpage.startswith('https://wow.curseforge.com/projects/'):
        return curseProject(addonpage)
		
    # Tukui
    elif addonpage.startswith('http://git.tukui.org/'):
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
		
    # Tukui
    elif addonpage.startswith('http://git.tukui.org/'):
        return getTukuiVersion(addonpage)

    # Wowinterface
    elif addonpage.startswith('http://www.wowinterface.com/'):
        return getWowinterfaceVersion(addonpage)

    # Invalid page
    else:
        print('Invalid addon page.')


# Curse

def curse(addonpage):
    try:
        page = requests.get(addonpage + '/download')
        contentString = str(page.content)
        indexOfZiploc = contentString.find('download__link')  # Will be the index of the first char of the url
        if -1 == indexOfZipLoc:
            raise Exception('Unable to find link')
        indexOfZipLoc += 22
        endQuote = contentString.find('"', indexOfZiploc)  # Will be the index of the ending quote after the url
        print(contentString[indexOfZiploc:endQuote])
        return 'https://www.curseforge.com' + contentString[indexOfZiploc:endQuote]
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''

def convertOldCurseURL(addonpage):
    try:
        # Curse has renamed some addons, removing the numbers from the URL. Rather than guess at what the new
        # name and URL is, just try to load the old URL and see where Curse redirects us to. We can guess at
        # the new URL, but they should know their own renaming scheme better than we do.
        page = requests.get(addonpage)
        return page.url
    except Exception:
        print('Failed to find the current page for old URL "' + addonpage + '". Skipping...\n')
        return ''

def getCurseVersion(addonpage):
    try:
        page = requests.get(addonpage + '/files')
        contentString = str(page.content)
        indexOfVer = contentString.find('file__name full')  # first char of the version string
        if -1 == indexOfVer:
            raise Exception('Unable to find link')
        indexOfVer += 17
        endTag = contentString.find('</span>', indexOfVer)  # ending tag after the version string
        if endTag - indexOfVer > MAX_VERSION_LENGTH:
            endTag = indexOfVer + MAX_VERSION_LENGTH
        return contentString[indexOfVer:endTag].strip().replace('\n', 'n').replace('=', 'e')
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''

# Curse Project

def curseProject(addonpage):
    try:
        return addonpage + '/files/latest'
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''


def getCurseProjectVersion(addonpage):
    try:
        page = requests.get(addonpage + '/files')
        contentString = str(page.content)
        indexOfVer = contentString.find('data-name')  # first char of the version string
        if -1 == indexOfVer:
            raise Exception('Unable to find link')
        indexOfVer += 11
        endTag = contentString.find('">', indexOfVer)  # ending tag after the version string
        if endTag - indexOfVer > MAX_VERSION_LENGTH:
            endTag = indexOfVer + MAX_VERSION_LENGTH
        return contentString[indexOfVer:endTag].strip().replace('\n', 'n').replace('=', 'e')
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''


# Tukui

def tukui(addonpage):
    print('Tukui is not supported yet.')
    return ''


def getTukuiVersion(addonpage):
    # print('Tukui is not supported yet.')
    return ''


# Wowinterface

def wowinterface(addonpage):
    downloadpage = addonpage.replace('info', 'download')
    try:
        page = requests.get(downloadpage + '/download')
        contentString = str(page.content)
        indexOfZiploc = contentString.find('Problems with the download? <a href="')  # first char of the url
        if -1 == indexOfZipLoc:
            raise Exception('Unable to find link')
        indexOfZiploc += 37
        endQuote = contentString.find('"', indexOfZiploc)  # ending quote after the url
        return contentString[indexOfZiploc:endQuote]
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''


def getWowinterfaceVersion(addonpage):
    try:
        page = requests.get(addonpage)
        contentString = str(page.content)
        indexOfVer = contentString.find('id="version"')  # first char of the version string
        if -1 == indexOfVer:
            raise Exception('Unable to find link')
        indexOfVer += 22
        endTag = contentString.find('</div>', indexOfVer)  # ending tag after the version string
        if endTag - indexOfVer > MAX_VERSION_LENGTH:
            endTag = indexOfVer + MAX_VERSION_LENGTH
        return contentString[indexOfVer:endTag].strip().replace('\n', 'n').replace('=', 'e')
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''
