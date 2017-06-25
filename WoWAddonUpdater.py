import requests, zipfile, configparser
from io import *
from os.path import isfile


def confirmExit():
    input('\nPress the Enter key to exit')
    exit(0)


class AddonUpdater:
    def __init__(self):
        print('')

        # Read config file

        if not isfile('config.ini'):
            print(
                'Failed to read configuration file. Are you sure there is a file called "config.ini" with the "WowAddonUpdater.py" file?')
            confirmExit()

        config = configparser.ConfigParser()
        config.read('config.ini')

        try:
            self.WOW_ADDON_LOCATION = config['WOW ADDON UPDATER']['WoW Addon Location']
            self.ADDON_LIST_FILE = config['WOW ADDON UPDATER']['Addon List File']
            self.INSTALLED_VERS_FILE = config['WOW ADDON UPDATER']['Installed Versions File']

        except Exception:
            print('Failed to parse configuration file. Are you sure it is formatted correctly?')
            confirmExit()

        if not isfile(self.ADDON_LIST_FILE):
            print('Failed to read addon list file. Are you sure the file exists?')
            confirmExit()

        if not isfile(self.INSTALLED_VERS_FILE):
            with open(self.INSTALLED_VERS_FILE, 'w') as newInstalledVersFile:
                newInstalledVers = configparser.ConfigParser()
                newInstalledVers['Installed Versions'] = {}
                newInstalledVers.write(newInstalledVersFile)
        return

    def update(self):

        # Main process (yes I formatted the project badly)

        with open(self.ADDON_LIST_FILE, "r") as fin:
            for line in fin:
                line = line.rstrip('\n')
                currentVersion = self.getCurrentVersion(line)
                installedVersion = self.getInstalledVersion(line)
                if not currentVersion == installedVersion:
                    print('Installing/updating addon: ' + line.replace('https://mods.curse.com/addons/wow/','') + ' to version: ' + currentVersion)
                    ziploc = self.findZiploc(line)
                    self.getAddon(ziploc)
                    self.setInstalledVersion(line, currentVersion)
                else:
                    print(line.replace('https://mods.curse.com/addons/wow/','') + ' version ' + currentVersion + ' is up to date.')

    def getInstalledVersion(self, addonpage):
        addonName = addonpage.replace('https://mods.curse.com/addons/wow/','')
        installedVers = configparser.ConfigParser()
        installedVers.read(self.INSTALLED_VERS_FILE)
        try:
            return installedVers['Installed Versions'][addonName]
        except Exception:
            return ''

    def setInstalledVersion(self, addonpage, currentVersion):
        addonName = addonpage.replace('https://mods.curse.com/addons/wow/','')
        installedVers = configparser.ConfigParser()
        installedVers.read(self.INSTALLED_VERS_FILE)
        installedVers.set('Installed Versions', addonName, currentVersion)
        with open(self.INSTALLED_VERS_FILE, 'w') as installedVersFile:
            installedVers.write(installedVersFile)

    def getCurrentVersion(self, addonpage):
        if not addonpage.startswith('https://mods.curse.com/addons/wow/'):
            print('Invalid addon page. Make sure you are using the Curse page for the addon.')
            confirmExit()
        try:
            page = requests.get(addonpage)
            contentString = str(page.content)
            indexOfVer = contentString.find('newest-file') + 26  # Will be the index of the first char of the version string
            endTag = contentString.find('</li>', indexOfVer)     # Will be the index of the ending tag after the version string
            return contentString[indexOfVer:endTag].strip()
        except Exception:
            print('Failed to find version number for: ' + addonpage)
            return ''

    def getAddon(self, ziploc):
        if ziploc == '':
            return
        try:
            r = requests.get(ziploc, stream=True)
            z = zipfile.ZipFile(BytesIO(r.content))
            z.extractall(self.WOW_ADDON_LOCATION)
        except Exception:
            print('Failed to download or extract zip file for addon. Skipping...\n')
            return

    def findZiploc(self, addonpage):
        if not addonpage.startswith('https://mods.curse.com/addons/wow/'):
            print('Invalid addon page. Make sure you are using the Curse page for the addon.')
            confirmExit()
        try:
            page = requests.get(addonpage + '/download')
            contentString = str(page.content)
            indexOfZiploc = contentString.find('data-href') + 11  # Will be the index of the first char of the url
            endQuote = contentString.find('"', indexOfZiploc)  # Will be the index of the ending quote after the url
            return contentString[indexOfZiploc:endQuote]
        except Exception:
            print('Failed to find downloadable zip file for addon. Skipping...\n')
            return ''

def main():
    addonupdater = AddonUpdater()
    addonupdater.update()

    return


if __name__ == "__main__":
    # execute only if run as a script
    main()
