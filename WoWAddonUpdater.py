import argparse
import configparser
import logging
import shutil
import tempfile
import zipfile
from io import BytesIO
from os import listdir
from os.path import isfile, join
from tkinter import *
from tkinter import filedialog

from requests import get

import SiteHandler


class GUI:
    root = Tk()
    addon_links_text = Text(root, height=40, width=150)
    folder_path_label = Label(root)
    status_bar = Label(root, text="", relief=SUNKEN)

    def save_addon_list(self):
        file = open('in.txt', 'w')
        file.seek(0)
        file.truncate()
        file.write(self.addon_links_text.get("1.0", END))
        file.close()

    def update_addons_wrapper(self, addon_updater):
        self.save_addon_list()
        self.root.after(0, addon_updater.update(self))

    def browse_folder(self, addon_updater):
        filename = filedialog.askdirectory()
        addon_updater.WOW_ADDON_LOCATION = filename
        self.folder_path_label['text'] = filename

    def build_gui(self, addon_updater):
        self.root.title("Wow Addon Updater")
        self.root.bind('<Escape>', sys.exit)
        self.root.iconbitmap('world_of_warcraft.ico')
        self.addon_links_text.grid(row=0, column=0, columnspan=4, rowspan=8)
        with open('in.txt', 'r') as file:
            self.addon_links_text.insert(INSERT, file.read())
        save_button = Button(self.root, text='Save Addon List', command=self.save_addon_list)
        save_button.grid(row=8, column=0, sticky=W + E)
        # TODO give GUI class its own thread using threading
        update_addons_button = Button(self.root, text='Update Addons',
                                      command=lambda: self.update_addons_wrapper(addon_updater))
        update_addons_button.grid(row=8, column=1, sticky=W + E)
        self.folder_path_label.grid(row=8, column=2, sticky=W + E)
        self.folder_path_label['text'] = addon_updater.WOW_ADDON_LOCATION
        folder_browse_button = Button(self.root, text='Browse')
        folder_browse_button.grid(row=8, column=3, sticky=W + E)
        folder_browse_button.config(command=lambda: self.browse_folder(addon_updater))
        self.status_bar.grid(row=9, column=0, columnspan=4, sticky=W + E)


class AddonUpdater:
    config = configparser.ConfigParser()

    def __init__(self):
        logging.basicConfig(filename='updater.log', level=logging.DEBUG)
        if not isfile('config.ini'):
            logging.warning('Failed to read configuration file. Are you sure there is a file called "config.ini"?')
        self.config.read('config.ini')

        try:
            self.WOW_ADDON_LOCATION = self.config['WOW ADDON UPDATER']['WoW Addon Location']
        except configparser.ParsingError as err:
            logging.warning('Could not parse:' + str(err))

        if not isfile("in.txt"):
            logging.warning('Failed to read addon list file. Are you sure the file exists?')
        if not isfile("installed.txt"):
            with open("installed.txt", 'w') as new_installed_version_file:
                new_installed_version = configparser.ConfigParser()
                new_installed_version['Installed Versions'] = {}
                new_installed_version.write(new_installed_version_file)

    def update(self, gui):
        addon_list = []
        with open("in.txt", "r") as fin:
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
                    gui.status_bar[
                        'text'] = 'Installing/updating addon: ' + addon_name + ' to version: ' + current_version
                    logging.info('Installing/updating addon: ' + addon_name + ' to version: ' + current_version)
                    ziploc = SiteHandler.find_ziploc(line)
                    install_success = self.get_addon(ziploc, subfolder)
                    current_node.append(self.get_installed_version(line, subfolder))
                    if install_success and (current_version is not ''):
                        self.set_installed_version(line, subfolder, current_version)
                else:
                    gui.status_bar['text'] = addon_name + ' version ' + current_version + ' is up to date.'
                    current_node.append("Up to date")
                addon_list.append(current_node)

    def get_addon(self, ziploc, subfolder):
        if ziploc == '':
            return False
        try:
            r = get(ziploc, stream=True)
            r.raise_for_status()  # Raise an exception for HTTP errors
            z = zipfile.ZipFile(BytesIO(r.content))
            self.extract(z, subfolder)
            return True
        except ConnectionError as err:
            logging.warning('Failed to download or extract zip file for addon. Skipping...' + str(err))
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
                logging.warning('Failed to get subfolder ' + subfolder + str(err))

    @staticmethod
    def get_installed_version(addon_page, subfolder):
        addon_name = SiteHandler.get_addon_name(addon_page)
        installed_version = configparser.ConfigParser()
        installed_version.read("installed.txt")
        try:
            if subfolder:
                return installed_version['Installed Versions'][addon_name + '|' + subfolder]  # Keep subfolder info in
                #  installed listing
            else:
                return installed_version['Installed Versions'][addon_name]
        except configparser.ParsingError:
            return 'version not found'

    @staticmethod
    def set_installed_version(addon_page, subfolder, current_version):
        addon_name = SiteHandler.get_addon_name(addon_page)
        installed_version = configparser.ConfigParser()
        installed_version.read("installed.txt")
        if subfolder:
            installed_version.set('Installed Versions', addon_name + '|' + subfolder, current_version)  # Keep subfolder
            # info in installed listing
        else:
            installed_version.set('Installed Versions', addon_name, current_version)
        with open("installed.txt", 'w') as installed_version_file:
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


def main():
    check_updates()
    addon_updater = AddonUpdater()
    gui = GUI()
    parser = argparse.ArgumentParser(description='Python script for mass-updating World of Warcraft addons')
    parser.add_argument('-s', help='stops gui from running', action='store_true')
    args = parser.parse_args()
    if args.s:
        addon_updater.update(gui)
    else:
        gui.build_gui(addon_updater)
        gui.root.mainloop()


if __name__ == "__main__":
    # execute only if run as a script
    main()
