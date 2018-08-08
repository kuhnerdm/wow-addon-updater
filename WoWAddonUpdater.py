import zipfile, configparser
from os.path import isfile, join, dirname
from os import chdir, listdir
from io import BytesIO
import shutil
import tempfile
import SiteHandler
import packages.requests as requests
from tkinter import *
from tkinter import scrolledtext
from tkinter.ttk import *
import queue
import threading


def confirmExit():
    input('\nPress the Enter key to exit')
    exit(0)


class AddonUpdater:
    def __init__(self):
        # Read config file
        config = configparser.ConfigParser()
        configFile = 'config.ini'

        if isfile(configFile):
            config.read(configFile)
        elif isfile(join(dirname(__file__), configFile)):
            # Couldn't find configFile in the current directory, but found it in the script's directory.
            chdir(dirname(__file__))
            config.read(configFile)
        else:
            print('Failed to read configuration file. Are you sure there is a file called "config.ini"?\n')
            confirmExit()

        try:
            self.WOW_ADDON_LOCATION = config['WOW ADDON UPDATER']['WoW Addon Location']
            self.ADDON_LIST_FILE = config['WOW ADDON UPDATER']['Addon List File']
            self.INSTALLED_VERS_FILE = config['WOW ADDON UPDATER']['Installed Versions File']
            self.AUTO_CLOSE = config['WOW ADDON UPDATER']['Close Automatically When Completed']
        except Exception:
            print('Failed to parse configuration file. Are you sure it is formatted correctly?\n')
            confirmExit()

        # Add "Use GUI = true" to the config file if the option is missing.
        try:
            useguivalue = config['WOW ADDON UPDATER']['Use GUI']
            if str.lower(useguivalue) in ["yes", "true", "1", "on"]:
                self.USE_GUI = True
            else:
                self.USE_GUI = False
        except KeyError:
            self.USE_GUI = True
            config['WOW ADDON UPDATER']['Use GUI'] = "True"

        if not isfile(self.ADDON_LIST_FILE):
            print('Failed to read addon list file. Are you sure the file exists?\n')
            confirmExit()

        if not isfile(self.INSTALLED_VERS_FILE):
            with open(self.INSTALLED_VERS_FILE, 'w') as newInstalledVersFile:
                newInstalledVers = configparser.ConfigParser()
                newInstalledVers['Installed Versions'] = {}
                newInstalledVers.write(newInstalledVersFile)
        if self.USE_GUI:
            self.initGUI()

    def initGUI(self):
        # We don't need any of this stuff if we're not running the GUI.
        self.textqueue = queue.Queue()
        self.progressqueue = queue.Queue()
        root = Tk()
        root.title("WoW Addon Updater")

        root.minsize(290, 214)
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        mainframe = Frame(root, padding="3 3 3 3")
        mainframe.grid(sticky=(N, W, E, S))

        mainframe.rowconfigure(0, weight=0)
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(1, weight=1)
        mainframe.columnconfigure(1, weight=1)
        mainframe.rowconfigure(2, weight=0)
        mainframe.columnconfigure(2, weight=1)
        mainframe.rowconfigure(3, weight=0)

        Sizegrip(root).grid(row=0, sticky=(S,E))

        Label(mainframe, text="WoW Addon Updater", font=("Helvetica", 20)).grid(column=0, row=0, sticky=(N), columnspan=3)

        output_text = scrolledtext.ScrolledText(mainframe, width=110, height=20, wrap=WORD)
        output_text.grid(column=0, row=1, sticky=(N,S,E,W), columnspan=3)

        progressbar = Progressbar(mainframe, orient="horizontal", mode="determinate")
        progressbar.grid(column=0, row=2, sticky=(E,W), columnspan=3)
        with open(self.ADDON_LIST_FILE, "r") as fin:
            length = 0
            for line in fin:
                line = line.strip()
                if line and not line.startswith('#'):
                    length += 1
            progressbar.configure(value=0, maximum = length)

        self.root = root
        self.output_text = output_text
        self.progressbar = progressbar
        self.ABORT = threading.Event()
        root.protocol("WM_DELETE_WINDOW", self.shutdownGUI)

        self.cancelbutton = Button(mainframe, text="Cancel", command=self.abortUpdating, state=DISABLED)
        self.cancelbutton.grid(column=0, row=3)
        self.startbutton = Button(mainframe, text="Start", command=self.startUpdating)
        self.startbutton.grid(column=2, row=3)

        for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)
        self.output_text.insert(END, 'Welcome to WoW Addon Updater. If you\'ve already made an in.txt file, click Start to begin.' + '\n')
        self.updateGUI()

    def updateGUI(self):
        # GUI refresh loop.
        try:
            text = self.textqueue.get_nowait()
            self.output_text.insert(END, '\n' + text)
            self.output_text.see(END)
        except queue.Empty:
            pass
        try:
            progress = self.progressqueue.get_nowait()
            self.progressbar.step()
        except queue.Empty:
            pass
        try:
            if not self.updatethread.is_alive():
                self.finishUpdating()
                # updatethread is dead and we've cleaned up, so wipe it.
                self.updatethread = None
        except AttributeError:
            pass
        self.root.after(200, self.updateGUI)

    def addText(self, text):
        # Put output in the queue for the GUI if we're using the GUI.
        # updateGUI() picks it up from the queue and adds it to the text box.
        # Threads suck. Only the GUI thread can touch GUI controls.
        if self.USE_GUI:
            self.textqueue.put(str(text))
        else:
            print(str(text))

    def addProgress(self):
        if self.USE_GUI:
            self.progressqueue.put("step")

    def startUpdating(self):
        self.startbutton['state'] = DISABLED
        self.cancelbutton['state'] = NORMAL
        self.ABORT.clear()
        self.updatethread = threading.Thread(target=self.update)
        self.updatethread.start()

    def finishUpdating(self):
        # Clean up if update thread is dead.
        self.startbutton['state'] = NORMAL
        self.cancelbutton['state'] = DISABLED
        self.progressbar.configure(value=0)

    def shutdownGUI(self):
        # No doing other things while we're shutting down
        self.startbutton['state'] = DISABLED
        self.cancelbutton['state'] = DISABLED
        # This should only be called from the GUI thread, so we can touch the text box directly.
        # Using the queue won't work because we're not refreshing any more.
        self.output_text.insert(END, '\n' + 'Shutting down.')
        self.output_text.see(END)
        # Refresh the GUI to show the above changes.
        self.root.update_idletasks()
        try:
            if self.updatethread.is_alive():
                # The update thread is running, so set the ABORT flag and wait.
                self.ABORT.set()
                self.updatethread.join()
        except AttributeError:
            # Update thread doesn't exist, so, continuing.
            pass
        exit()

    def abortUpdating(self):
        try:
            if self.updatethread.is_alive():
                self.ABORT.set()
                self.addText("Trying to cancel...")
                self.cancelbutton['state'] = DISABLED
            else:
                self.addText("Update isn't running.")
        except AttributeError:
            self.addText("Update doesn't seem to be running.")

    def update(self):
        uberlist = []
        with open(self.ADDON_LIST_FILE, "r") as fin:
            if self.USE_GUI:
                self.addText('Checking for updates.' + '\n')
            for line in fin:
                current_node = []
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if self.USE_GUI and self.ABORT.is_set():
                    # The GUI thread has asked the update thread to stop.
                    self.addText("Cancelled.")
                    return
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
                self.addProgress()
                if self.USE_GUI and self.ABORT.is_set():
                    # The GUI thread has asked the update thread to stop.
                    self.addText("Cancelled.")
                    return
                if not currentVersion == installedVersion:
                    self.addText('Installing/updating addon: ' + addonName + ' to version: ' + currentVersion)
                    ziploc = SiteHandler.findZiploc(line)
                    install_success = False
                    install_success = self.getAddon(ziploc, subfolder)
                    current_node.append(self.getInstalledVersion(line))
                    if install_success is True and currentVersion is not '':
                        self.setInstalledVersion(line, currentVersion)
                else:
                    self.addText('Up to date: ' + addonName + ' version ' + currentVersion)
                    current_node.append("Up to date")
                uberlist.append(current_node)
        if self.USE_GUI:
            self.addText('\n' + 'All done!')
            return
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
            self.addText('Failed to download or extract zip file for addon. Skipping...\n')
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
    if addonupdater.USE_GUI:
        addonupdater.root.mainloop()
    else:
        addonupdater.update()
    return


if __name__ == "__main__":
    # execute only if run as a script
    main()
