#!/usr/bin/env python

import zipfile
import configparser
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
            print('Failed to read configuration file. '
                  'Are you sure there is a file called "config.ini"?\n')
            confirmExit()

        config = configparser.ConfigParser()
        config.read('config.ini')

        try:
            self.WOW_ADDON_LOCATION = config['WOW ADDON UPDATER']['WoW Addon Location']          # noqa E501
            self.ADDON_LIST_FILE = config['WOW ADDON UPDATER']['Addon List File']                # noqa E501
            self.INSTALLED_VERS_FILE = config['WOW ADDON UPDATER']['Installed Versions File']    # noqa E501
            self.AUTO_CLOSE = config['WOW ADDON UPDATER']['Close Automatically When Completed']  # noqa E501
        except Exception:
            print('Failed to parse configuration file. Are you sure it is '
                  'formatted correctly?\n')
            confirmExit()

        if not isfile(self.ADDON_LIST_FILE):
            print('Failed to read addon list file. Are you sure the file '
                  'exists?\n')
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
                if '|' in line:
                    ''' Expected input format: "mydomain.com/myzip.zip"
                        or "mydomain.com/myzip.zip|subfolder"
                    '''
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
                installedVersion = self.getInstalledVersion(line, subfolder)
                if not currentVersion == installedVersion:
                    print('Installing/updating addon: {} to version: {}\n'
                          .format(addonName, currentVersion))
                    ziploc = SiteHandler.findZiploc(line)
                    install_success = False
                    install_success = self.getAddon(ziploc, subfolder)
                    current_node.append(
                            self.getInstalledVersion(line, subfolder)
                            )
                    if install_success and (currentVersion != ''):
                        self.setInstalledVersion(line,
                                                 subfolder,
                                                 currentVersion)
                else:
                    print('{} version {} is up to date\n'
                          .format(addonName, currentVersion))

                    current_node.append("Up to date")
                uberlist.append(current_node)
        if self.AUTO_CLOSE == 'False':
            ''' + 2 for padding
            '''
            col_width = max(len(word) for row in uberlist for word in row) + 2
            print("".join(word.ljust(col_width)
                  for word in ("Name", "Iversion", "Cversion")))
            for row in uberlist:
                print("".join(word.ljust(col_width) for word in row), end='\n')
            confirmExit()

    def getAddon(self, ziploc, subfolder):
        if ziploc == '':
            return False
        try:
            r = requests.get(ziploc, stream=True)
            r.raise_for_status()   # Raise an exception for HTTP errors
            z = zipfile.ZipFile(BytesIO(r.content))
            self.extract(z, ziploc, subfolder)
            return True
        except Exception:
            print('Failed to download or extract zip file for addon. '
                  'Skipping...\n')
            return False

    def extract(self, zip, url, subfolder):
        if subfolder == '':
            zip.extractall(self.WOW_ADDON_LOCATION)
        else:
            ''' Pull subfolder out to main level, remove original
                extracted folder
            '''
            try:
                with tempfile.TemporaryDirectory() as tempDirPath:
                    zip.extractall(tempDirPath)
                    extractedFolderPath = join(tempDirPath,
                                               listdir(tempDirPath)[0])
                    subfolderPath = join(extractedFolderPath, subfolder)
                    destination_dir = join(self.WOW_ADDON_LOCATION, subfolder)
                    ''' Delete the existing copy, as shutil.copytree will not
                        work if the destination directory already exists!
                    '''
                    shutil.rmtree(destination_dir, ignore_errors=True)
                    shutil.copytree(subfolderPath, destination_dir)
            except Exception:
                print('Failed to get subfolder ' + subfolder)

    def getInstalledVersion(self, addonpage, subfolder):
        addonName = SiteHandler.getAddonName(addonpage)
        installedVers = configparser.ConfigParser()
        installedVers.read(self.INSTALLED_VERS_FILE)
        try:
            if(subfolder):
                ''' Keep subfolder info in installed listing
                '''
                return installedVers['Installed Versions'][addonName + '|' + subfolder]  # noqa E501
            else:
                return installedVers['Installed Versions'][addonName]
        except Exception:
            return 'version not found'

    def setInstalledVersion(self, addonpage, subfolder, currentVersion):
        addonName = SiteHandler.getAddonName(addonpage)
        installedVers = configparser.ConfigParser()
        installedVers.read(self.INSTALLED_VERS_FILE)
        if(subfolder):
            ''' Keep subfolder info in installed listing
            '''
            installedVers.set('Installed Versions', addonName + '|' + subfolder, currentVersion)  # noqa E501
        else:
            installedVers.set('Installed Versions', addonName, currentVersion)
        with open(self.INSTALLED_VERS_FILE, 'w') as installedVersFile:
            installedVers.write(installedVersFile)


def main():
    if(isfile('changelog.txt')):
        wauurl = 'https://raw.githubusercontent.com/kuhnerdm/wow-addon-updater/master/changelog.txt'  # noqa E501
        downloadedChangelog = requests.get(wauurl).text.split('\n')
        with open('changelog.txt') as cl:
            presentChangelog = cl.readlines()
            for i in range(len(presentChangelog)):
                presentChangelog[i] = presentChangelog[i].strip('\n')

    if(downloadedChangelog != presentChangelog):
        print('A new update to WoWAddonUpdater is available! Check it out at '
              'https://github.com/kuhnerdm/wow-addon-updater !')

    addonupdater = AddonUpdater()
    addonupdater.update()
    return


if __name__ == "__main__":
    # execute only if run as a script
    main()
