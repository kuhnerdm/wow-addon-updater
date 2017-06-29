import packages.requests as requests
import zipfile
from io import *


# Site splitter

def createDownloader(addonpage):
    # Curse
    if addonpage.startswith('https://mods.curse.com/addons/wow/'):
        return Curse(addonpage)

    # Tukui
    elif addonpage.startswith('http://git.tukui.org/'):
        return Tukui(addonpage)

    # Wowinterface
    elif addonpage.startswith('http://www.wowinterface.com/'):
        return Wowinterface(addonpage)

    # Invalid page
    else:
        print('Invalid addon page.')


# Curse

class Curse:
    def __init__(self, addonpage):
        self.addonpage = addonpage

    def findLoc(self):
        try:
            page = requests.get(self.addonpage + '/download')
            contentString = str(page.content)
            indexOfZiploc = contentString.find('data-href') + 11  # first char of the url
            endQuote = contentString.find('"', indexOfZiploc)  # ending quote after the url
            return contentString[indexOfZiploc:endQuote]
        except Exception:
            print('Failed to find downloadable zip file for addon. Skipping...\n')
            return ''

    def getVersion(self):
        try:
            page = requests.get(self.addonpage)
            contentString = str(page.content)
            indexOfVer = contentString.find('newest-file') + 26  # first char of the version string
            endTag = contentString.find('</li>', indexOfVer)  # ending tag after the version string
            return contentString[indexOfVer:endTag].strip()
        except Exception:
            print('Failed to find version number for: ' + self.addonpage)
            return ''

    def download(self, location):
        ziploc = self.findLoc()
        if ziploc == '':
            return
        try:
            downloadZip(ziploc, location)
        except Exception:
            print('Failed to download or extract zip file for addon. Skipping...\n')
            return


# Tukui

class Tukui:
    def __init__(self, addonpage):
        self.addonpage = addonpage

    def findLoc(self):
        print('Tukui is not supported yet.')
        return ''

    def getVersion(self):
        try:
            page = requests.get(self.addonpage)
            contentString = str(page.content)
            indexOfVer = contentString.find('<a class="commit_short_id"') + 0  # first char of the version string
            indexOfVer = contentString.find('">', indexOfVer) + 2  # ending tag after the version string
            endTag = contentString.find('</a>', indexOfVer)  # ending tag after the version string
            return contentString[indexOfVer:endTag].strip()
        except Exception:
            print('Failed to find version number for: ' + self.addonpage)
            return ''

    def download(self, location):
        return


# Wowinterface

class Wowinterface:
    def __init__(self, addonpage):
        self.addonpage = addonpage

    def findLoc(self):
        downloadpage = self.addonpage.replace('info', 'download')
        try:
            page = requests.get(downloadpage + '/download')
            contentString = str(page.content)
            indexOfZiploc = contentString.find('Problems with the download? <a href="') + 37  # first char of the url
            endQuote = contentString.find('"', indexOfZiploc)  # ending quote after the url
            return contentString[indexOfZiploc:endQuote]
        except Exception:
            print('Failed to find downloadable zip file for addon. Skipping...\n')
            return ''

    def getVersion(self):
        try:
            page = requests.get(self.addonpage)
            contentString = str(page.content)
            indexOfVer = contentString.find('id="version"') + 22  # first char of the version string
            endTag = contentString.find('</div>', indexOfVer)  # ending tag after the version string
            return contentString[indexOfVer:endTag].strip()
        except Exception:
            print('Failed to find version number for: ' + self.addonpage)
            return ''

    def download(self, location):
        ziploc = self.findLoc()
        if ziploc == '':
            return
        try:
            downloadZip(ziploc, location)
        except Exception:
            print('Failed to download or extract zip file for addon. Skipping...\n')
            return

def downloadZip(source, dest):
    r = requests.get(source, stream=True)
    z = zipfile.ZipFile(BytesIO(r.content))
    z.extractall(dest)