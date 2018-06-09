import zipfile, configparser
from io import BytesIO
from os.path import isfile, join
from os import listdir
import shutil
import tempfile
import SiteHandler
import packages.requests as requests


def confirmExit():
    input('\nPress the Enter key to exit')
    exit(0)


class AddonUpdater:
    def __init__(self):
        print('')

        # Read config file
        if not isfile('config.ini'):
            print('Failed to read configuration file. Are you sure there is a file called "config.ini"?\n')
            confirmExit()

        config = configparser.ConfigParser()
        config.read('config.ini')

        try:
            self.WOW_ADDON_LOCATION = config['WOW ADDON UPDATER']['WoW Addon Location']
            self.ADDON_LIST_FILE = config['WOW ADDON UPDATER']['Addon List File']
            self.INSTALLED_VERS_FILE = config['WOW ADDON UPDATER']['Installed Versions File']
            self.AUTO_CLOSE = config['WOW ADDON UPDATER']['Close Automatically When Completed']
        except Exception:
            print('Failed to parse configuration file. Are you sure it is formatted correctly?\n')
            confirmExit()

        if not isfile(self.ADDON_LIST_FILE):
            print('Failed to read addon list file. Are you sure the file exists?\n')
            confirmExit()

        if not isfile(self.INSTALLED_VERS_FILE):
            with open(self.INSTALLED_VERS_FILE, 'w') as newInstalledVersFile:
                newInstalledVers = configparser.ConfigParser()
                newInstalledVers['Installed Versions'] = {}
                newInstalledVers.write(newInstalledVersFile)
        return

    def update(self):
        uberlist = []
        with open(self.ADDON_LIST_FILE, "r") as fin:
            for line in fin:
                current_node = []
                line = line.rstrip('\n')
                if not line or line.startswith('#'):
                    continue
                if '|' in line: # Expected input format: "mydomain.com/myzip.zip" or "mydomain.com/myzip.zip|subfolder"
                    subfolder = line.split('|')[1]
                    line = line.split('|')[0]
                else:
                    subfolder = ''
                addonName = SiteHandler.getAddonName(line)
                currentVersion = SiteHandler.getCurrentVersion(line)
                if currentVersion is None:
                    currentVersion = 'Not Available'
                current_node.append(addonName)
                current_node.append(currentVersion)
                installedVersion = self.getInstalledVersion(line)
                if not currentVersion == installedVersion:
                    print('Installing/updating addon: ' + addonName + ' to version: ' + currentVersion + '\n')
                    ziploc = SiteHandler.findZiploc(line)
                    install_success = False
                    install_success = self.getAddon(ziploc, subfolder)
                    current_node.append(self.getInstalledVersion(line))
                    if install_success is True and currentVersion is not '':
                        self.setInstalledVersion(line, currentVersion)
                else:
                    print(addonName + ' version ' + currentVersion + ' is up to date.\n')
                    current_node.append("Up to date")
                uberlist.append(current_node)
        if self.AUTO_CLOSE == 'False':
            col_width = max(len(word) for row in uberlist for word in row) + 2  # padding
            print("".join(word.ljust(col_width) for word in ("Name","Iversion","Cversion")))
            for row in uberlist:
                print("".join(word.ljust(col_width) for word in row), end='\n')
            confirmExit()

    def getAddon(self, ziploc, subfolder):
        if ziploc == '':
            return False
        try:
            r = requests.get(ziploc, stream=True)
            z = zipfile.ZipFile(BytesIO(r.content))
            self.extract(z, ziploc, subfolder)
            return True
        except Exception:
            print('Failed to download or extract zip file for addon. Skipping...\n')
            return False
    
    def extract(self, zip, url, subfolder):
        if subfolder == '':
            zip.extractall(self.WOW_ADDON_LOCATION)
        else: # Pull subfolder out to main level, remove original extracted folder
            try:
                with tempfile.TemporaryDirectory() as tempDirPath:
                    zip.extractall(tempDirPath)
                    extractedFolderPath = join(tempDirPath, listdir(tempDirPath)[0])
                    subfolderPath = join(extractedFolderPath, subfolder)
                    shutil.copytree(subfolderPath, join(self.WOW_ADDON_LOCATION, subfolder))
            except Exception as ex:
                print('Failed to get subfolder ' + subfolder)

    def getInstalledVersion(self, addonpage):
        addonName = SiteHandler.getAddonName(addonpage)
        installedVers = configparser.ConfigParser()
        installedVers.read(self.INSTALLED_VERS_FILE)
        try:
            return installedVers['Installed Versions'][addonName]
        except Exception:
            return 'version not found'

    def setInstalledVersion(self, addonpage, currentVersion):
        addonName = SiteHandler.getAddonName(addonpage)
        installedVers = configparser.ConfigParser()
        installedVers.read(self.INSTALLED_VERS_FILE)
        installedVers.set('Installed Versions', addonName, currentVersion)
        with open(self.INSTALLED_VERS_FILE, 'w') as installedVersFile:
            installedVers.write(installedVersFile)


def main():
    addonupdater = AddonUpdater()
    addonupdater.update()
    return


if __name__ == "__main__":
    # execute only if run as a script
    main()
