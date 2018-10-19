import argparse
import configparser
import shutil
import tempfile
import zipfile
from io import BytesIO
from os import listdir
from os.path import isfile, join
from tkinter import *

from requests import get

import SiteHandler


class AddonUpdater:
    def __init__(self):
        print('')

        # Read config file
        if not isfile('config.ini'):
            # TODO push errors to log file
            print('Failed to read configuration file. Are you sure there is a file called "config.ini"?\n')

        config = configparser.ConfigParser()
        config.read('config.ini')

        try:
            self.WOW_ADDON_LOCATION = config['WOW ADDON UPDATER']['WoW Addon Location']
            self.ADDON_LIST_FILE = config['WOW ADDON UPDATER']['Addon List File']
            self.INSTALLED_VERSION_FILE = config['WOW ADDON UPDATER']['Installed Versions File']
            self.AUTO_CLOSE = config['WOW ADDON UPDATER']['Close Automatically When Completed']
        except configparser.ParsingError as err:
            print('Could not parse:', err)

        if not isfile(self.ADDON_LIST_FILE):
            print('Failed to read addon list file. Are you sure the file exists?\n')

        if not isfile(self.INSTALLED_VERSION_FILE):
            with open(self.INSTALLED_VERSION_FILE, 'w') as new_installed_version_file:
                new_installed_version = configparser.ConfigParser()
                new_installed_version['Installed Versions'] = {}
                new_installed_version.write(new_installed_version_file)
        return

    def update(self):
        addon_list = []
        with open(self.ADDON_LIST_FILE, "r") as fin:
            for line in fin:
                current_node = []
                line = line.rstrip('\n')
                if not line or line.startswith('#'):
                    continue
                if '|' in line:  # Expected input format: "curse.com/addon.zip" or "curse.com/addon.zip|subfolder"
                    subfolder = line.split('|')[1]
                    line = line.split('|')[0]
                else:
                    subfolder = ''
                addon_name = SiteHandler.get_addon_name(line)
                current_version = SiteHandler.get_current_version(line)
                if current_version is None:
                    current_version = 'Not Available'
                current_node.append(addon_name)
                current_node.append(current_version)
                installed_version = self.get_installed_version(line, subfolder)
                if not current_version == installed_version:
                    ziploc = SiteHandler.find_ziploc(line)
                    install_success = self.get_addon(ziploc, subfolder)
                    current_node.append(self.get_installed_version(line, subfolder))
                    if install_success and (current_version is not ''):
                        self.set_installed_version(line, subfolder, current_version)
                else:
                    current_node.append("Up to date")
                addon_list.append(current_node)

    def get_addon(self, ziploc, subfolder):
        if ziploc == '':
            return False
        try:
            r = get(ziploc, stream=True)
            r.raise_for_status()   # Raise an exception for HTTP errors
            z = zipfile.ZipFile(BytesIO(r.content))
            self.extract(z, subfolder)
            return True
        except ConnectionError as err:
            print('Failed to download or extract zip file for addon. Skipping...', err)
            return False

    def extract(self, zip_file, subfolder):
        if subfolder == '':
            zip_file.extractall(self.WOW_ADDON_LOCATION)
        else:  # Pull subfolder out to main level, remove original extracted folder
            try:
                with tempfile.TemporaryDirectory() as tempDirPath:
                    zip_file.extractall(tempDirPath)
                    extracted_folder_path = join(tempDirPath, listdir(tempDirPath)[0])
                    subfolder_path = join(extracted_folder_path, subfolder)
                    destination_dir = join(self.WOW_ADDON_LOCATION, subfolder)
                    # Delete the existing copy, as shutil.copytree will not work if
                    # the destination directory already exists!
                    shutil.rmtree(destination_dir, ignore_errors=True)
                    shutil.copytree(subfolder_path, destination_dir)
            except shutil.Error as err:
                print('Failed to get subfolder ' + subfolder, err)

    def get_installed_version(self, addon_page, subfolder):
        addon_name = SiteHandler.get_addon_name(addon_page)
        installed_version = configparser.ConfigParser()
        installed_version.read(self.INSTALLED_VERSION_FILE)
        try:
            if subfolder:
                return installed_version['Installed Versions'][addon_name + '|' + subfolder]  # Keep subfolder info in
                #  installed listing
            else:
                return installed_version['Installed Versions'][addon_name]
        except configparser.ParsingError:
            return 'version not found'

    def set_installed_version(self, addon_page, subfolder, current_version):
        addon_name = SiteHandler.get_addon_name(addon_page)
        installed_version = configparser.ConfigParser()
        installed_version.read(self.INSTALLED_VERSION_FILE)
        if subfolder:
            installed_version.set('Installed Versions', addon_name + '|' + subfolder, current_version)  # Keep subfolder
            # info in installed listing
        else:
            installed_version.set('Installed Versions', addon_name, current_version)
        with open(self.INSTALLED_VERSION_FILE, 'w') as installed_version_file:
            installed_version.write(installed_version_file)


def check_updates():
    # TODO change update procedure to not split on new changelog
    downloaded_changelog, present_changelog = None, None
    if isfile('changelog.txt'):
        downloaded_changelog = get('https://raw.githubusercontent.com/kuhnerdm/wow-addon-updater/master'
                                   '/changelog.txt').text.split('\n')
        with open('changelog.txt') as cl:
            present_changelog = cl.readlines()
            for i in range(len(present_changelog)):
                present_changelog[i] = present_changelog[i].strip('\n')
    if downloaded_changelog != present_changelog:
        print('A new update to WoWAddonUpdater is available! Check it out at '
              'https://github.com/kuhnerdm/wow-addon-updater !')


def save_addon_list():
    file = open('in.txt', 'w')
    file.seek(0)
    file.truncate()
    file.write(addon_links_text.get("1.0", END))
    file.close()


def update_addons_wrapper():
    root.after(0, addon_updater.update())


# globals
addon_updater = AddonUpdater()
root = Tk()
root.iconbitmap('world_of_warcraft.ico')
addon_links_text = Text(root, height=50, width=150)


def main():
    check_updates()
    parser = argparse.ArgumentParser(description='Python script for mass-updating World of Warcraft addons')
    parser.add_argument('-s', help='stops gui from running', action='store_true')
    args = parser.parse_args()
    if args.s:
        addon_updater.update()
    else:
        # build gui if not silent
        root.title("Wow Addon Updater")
        root.bind('<Escape>', sys.exit)
        addon_links_text.pack()
        with open('in.txt', 'r') as file:
            addon_links_text.insert(INSERT, file.read())
        save_button = Button(root, text='Save Addon List', command=save_addon_list)
        save_button.pack()
        # TODO tkinter hangs when addon updates are triggered
        update_addons_button = Button(root, text='Update Addons', command=addon_updater.update)
        update_addons_button.pack()
        # TODO print update progress onto gui

        # TODO config changes gui
        root.mainloop()


if __name__ == "__main__":
    # execute only if run as a script
    main()
