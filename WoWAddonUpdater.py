import zipfile, configparser
from io import BytesIO
from os.path import isfile, join
from os import listdir
import shutil
import tempfile
import SiteHandler
import packages.requests as requests
from termcolor import colored   # termcolor and colorama for colored output text
from colorama import init
init()
from colorama import Fore 
from colorama import Style

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
                current_node.append(Fore.GREEN + currentVersion + Style.RESET_ALL)
                installedVersion = self.getInstalledVersion(line)
                if not currentVersion == installedVersion:
                    print (Fore.BLUE + Style.BRIGHT + '[Updating...]' + '\x1b[2C' + Style.NORMAL + Fore.GREEN + addonName + Style.RESET_ALL + ' to version: ' + Style.BRIGHT + Fore.GREEN + currentVersion + Style.RESET_ALL)
                    ziploc = SiteHandler.findZiploc(line)
                    install_success = False
                    install_success = self.getAddon(ziploc, subfolder)
                    current_node.append(Fore.BLUE + Style.BRIGHT + self.getInstalledVersion(line) + Style.RESET_ALL)
                    if install_success is True and currentVersion is not '':
                        self.setInstalledVersion(line, currentVersion)
                else:
                    print(Style.BRIGHT + Fore.GREEN +'[Up to date ]' + '\x1b[2C' + Fore.GREEN + Style.DIM + addonName + Style.RESET_ALL + ' version ' + Fore.GREEN + currentVersion + Style.RESET_ALL)
                    current_node.append(Fore.GREEN + Style.BRIGHT + "Up to date" + Style.RESET_ALL)
                uberlist.append(current_node)
        if self.AUTO_CLOSE == 'False':
            col_width = max(len(word) for row in uberlist for word in row) + 2  # padding
            print('\n' + Fore.YELLOW + Style.BRIGHT + "".join(word.ljust(col_width) for word in ("Addon Name","Updated Version","Previous version"))) #add newline and adjust heading, Cant figure out howto align the right heading properly
            for row in uberlist:
                print('\x1b[1A' + Fore.GREEN + "".join(word.ljust(col_width) for word in row), end='\n') #Unsure how to remove the double spacing onthe summary, 
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
            print(Fore.RED + 'Failed to download or extract zip file for addon. Skipping...\n' + Style.RESET_ALL)
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
                    destination_dir = join(self.WOW_ADDON_LOCATION, subfolder)
                    # Delete the existing copy, as shutil.copytree will not work if
                    # the destination directory already exists!
                    shutil.rmtree(destination_dir, ignore_errors=True)
                    shutil.copytree(subfolderPath, destination_dir)
            except Exception as ex:
                print(Fore.RED + 'Failed to get subfolder ' + subfolder + Style.RESET_ALL)

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
