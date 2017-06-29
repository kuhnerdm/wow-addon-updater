# wow-addon-updater - Now supports Curse and WoWInterface addons!

This utility provides an alternative to the Twitch/Curse client for management and updating of addons for World of Warcraft. The Twitch/Curse client is rather bloated and buggy, and comes with many features that most users will not ever use in the first place. This utility, however, is lightweight and makes it very easy to manage which addons are being updated, and to update them just by running a python script.

## First-time setup

This utility has two dependencies:

* A version of [Python](https://www.python.org/) 3 (Any version of Python 3 should do)

* The [requests](http://docs.python-requests.org/en/master/) module

**NEW:** Thanks to https://github.com/Saritus, the requests module is now included in the download as a package, so there is no longer any need to install those yourself. Just install Python 3, download this app, configure the utility, and double click "WoWAddonUpdater.py" to start.

## Configuring the utility

The "config.ini" file is used by the utility to find where to install the addons to, and where to get the list of mods from.

The default location to install the addons to is "C:\Program Files (x86)\World of Warcraft\Interface\AddOns". If this is not the location where you have World of Warcraft installed, you will need to edit "config.ini" to point to your addons folder.

The default location of the addon list file is simply "in.txt", but this file will not exist on your PC, so you should either create "in.txt" in the same location as the utility, or name the file something else and edit "config.ini" to point to the new file.

## Input file format

Whatever file you use for your list of mods needs to be formatted in a particular way. Each line corresponds to a mod, and the line just needs to contain the link to the Curse or WoWInterface page for the mod. For example:

    https://mods.curse.com/addons/wow/world-quest-tracker
    https://mods.curse.com/addons/wow/deadly-boss-mods
    https://mods.curse.com/addons/wow/auctionator
    http://www.wowinterface.com/downloads/info24005-RavenousMounts.html
    
    
Each link needs to be the main page for the addon, as shown above.

## macOS Installation Instructions - Thanks to https://github.com/melwan

1. Install Python 3 for macOS
2. Run get-pip.py (Run menu > Run Module)
3. Run get-requests.py (Run menu > Run Module)
4. Edit config.ini (using TextEdit.app)
5. Create in.txt (using TextEdit.app)
6. Run WoWAddonUpdater.py (Run menu > Run Module)

The standard addon location on macOS is /Applications/World of Warcraft/Interface/AddOns

*Note: To save to a .txt file in TextEdit, go to Preferences > "New Document" tab > Under the "Format" section, choose "Plain Text".*

## Running the utility

After configuring the utility and setting up your input file, updating your addons is as simple as double clicking the "WoWAddonUpdater.py" file.

*Note: The more addons you have in your list, the longer it will take to update them... Duh.*

## Contact info

Have any questions, concerns, issues, or suggestions for the utility? Feel free to either submit an issue through Github or email me at kuhnerdm@gmail.com. Please put in the subject line that this is for the WoW Addon Updater.

## Future plans

* Make a video guide detailing all the above information

* Update to use a visual interface instead of a command-line interface

* ~~Add version checking to eliminate reinstalls of the current versions of addons~~ Thanks to https://github.com/zurohki for the code to implement this, and to https://github.com/Saritus for integrating it into the current codebase! You will now see reduced data usage of the app, and quicker update times!

* ~~Make the code structure not suck. No, seriously... it's bad...~~ Thanks to https://github.com/Saritus for the refactoring!

* ~~Add support for more addon providers (namely WoWInterface)~~ Thanks to https://github.com/Saritus for the WoWInterface support!

Thanks for checking this out; hopefully it helps a lot of you :)
