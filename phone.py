#!/usr/bin/env python

import wx
import subprocess
import time
from runtime import *
from datetime import datetime

# ============================================================================
#                               Class Magisk
# ============================================================================
class Magisk():
    def __init__(self, dirname):
        self.dirname = dirname


# ============================================================================
#                               Class MagiskApk
# ============================================================================
class MagiskApk():
    def __init__(self, type):
        self.type = type


# ============================================================================
#                               Class Device
# ============================================================================
class Device():
    # Class variable
    vendor = "google"

    def __init__(self, id, mode):
        # Instance variables
        self.id = id
        self.mode = mode
        # The below are for caching.
        self._rooted = None
        self._root_symbol = None
        self._magisk_version = None
        self._build = None
        self._hardware = None
        self._active_slot = None
        self._unlocked = None
        self._bootloader_version = None
        self._device_info = None
        self._magisk_modules = None
        self._magisk_detailed_modules = None
        self._magisk_modules_summary = None
        self._magisk_apks = None

    # ----------------------------------------------------------------------------
    #                               property root_symbol
    # ----------------------------------------------------------------------------
    @property
    def root_symbol(self):
        if self._root_symbol is None:
            if self.mode == 'f.b':
                self._root_symbol = '?'
            else:
                if self.rooted:
                    self._root_symbol = '✓'
                else:
                    self._root_symbol = '✗'
        return self._root_symbol

    # ----------------------------------------------------------------------------
    #                               property magisk_version
    # ----------------------------------------------------------------------------
    @property
    def magisk_version(self):
        if self._magisk_version is None:
            if self.mode == 'adb':
                if self.rooted:
                    try:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'magisk -c\'\""
                        res = run_shell(theCmd)
                        if res.returncode == 0:
                            self._magisk_version = res.stdout
                    except:
                        try:
                            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'/data/adb/magisk/magisk32 -c\'\""
                            res = run_shell(theCmd)
                            if res.returncode == 0:
                                self._magisk_version = res.stdout
                        except:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk version, assuming that it is not rooted.")
                            self._rooted = None
                else:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell dumpsys package com.topjohnwu.magisk | grep versionName"
                    res = run_shell(theCmd)
                    version = res.stdout.split('\n')
                    version = version[0].split('=')
                    try:
                        self._magisk_version = version[1]
                    except:
                        return ''
                self._magisk_version = self._magisk_version.strip('\n')
        return self._magisk_version.strip('\n')

    # ----------------------------------------------------------------------------
    #                               Method get_uncached_magisk_version
    # ----------------------------------------------------------------------------
    def get_uncached_magisk_version(self):
        self._magisk_version is None
        return self.magisk_version

    # ----------------------------------------------------------------------------
    #                               property magisk_modules
    # ----------------------------------------------------------------------------
    @property
    def magisk_modules(self):
        if self._magisk_modules is None:
            if self.mode == 'adb':
                if self.rooted:
                    try:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls /data/adb/modules\'\""
                        res = run_shell(theCmd)
                        if res.returncode == 0:
                            self._magisk_modules = res.stdout.split('\n')
                    except:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk modules, assuming that it is not rooted.")
                        self._rooted = None
                        self._magisk_modules = ''
                else:
                    self._magisk_modules = ''
        return self._magisk_modules

    # ----------------------------------------------------------------------------
    #                               property magisk_detailed_modules
    # ----------------------------------------------------------------------------
    @property
    def magisk_detailed_modules(self):
        if self._magisk_detailed_modules is None:
            try:
                if self.mode == 'adb':
                    if self.rooted:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls /data/adb/modules\'\""
                        res = run_shell(theCmd)
                        if res.returncode == 0:
                            modules = []
                            self._magisk_detailed_modules = res.stdout.split('\n')
                            for module in self._magisk_detailed_modules:
                                if module != '':
                                    m = Magisk(module)
                                    if self.mode == 'adb' and get_adb():
                                        # get the state by checking if there is a disable file in the module directory
                                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls /data/adb/modules/{module}/disable\'\""
                                        res = run_shell(theCmd)
                                        if res.returncode == 0:
                                            m.state = 'disabled'
                                        else:
                                            m.state = 'enabled'
                                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cat /data/adb/modules/{module}/module.prop\'\""
                                        res = run_shell(theCmd)
                                        if res.returncode == 0:
                                            module_prop = res.stdout.split('\n')
                                            setattr(m, 'id', '')
                                            setattr(m, 'version', '')
                                            setattr(m, 'versionCode', '')
                                            setattr(m, 'author', '')
                                            setattr(m, 'description', '')
                                            for line in module_prop:
                                                # ignore comment lines
                                                if line[:1] == "#":
                                                    continue
                                                if line.strip() != '':
                                                    key, value = line.split('=', 1)
                                                    setattr(m, key, value)
                                            modules.append(m)
                            self._magisk_detailed_modules = modules
            except Exception as e:
                self._magisk_detailed_modules is None
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk modules processing\nException: {e}")
        return self._magisk_detailed_modules

    # ----------------------------------------------------------------------------
    #                               property magisk_apks
    # ----------------------------------------------------------------------------
    @property
    def magisk_apks(self):
        if self._magisk_apks is None:
            try:
                apks = []
                list = ['stable', 'beta', 'canary', 'debug']
                for i in list:
                    apk = self.get_magisk_apk_details(i)
                    apks.append(apk)
                self._magisk_apks = apks
            except Exception as e:
                self._magisk_apks is None
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads links processing\nException: {e}")
        return self._magisk_apks

    # ----------------------------------------------------------------------------
    #                               Function get_magisk_apk_details
    # ----------------------------------------------------------------------------
    def get_magisk_apk_details(self, channel):
        if channel == 'stable':
            url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/stable.json"
        elif channel == 'beta':
            url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/beta.json"
        elif channel == 'canary':
            url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/canary.json"
        elif channel == 'debug':
            url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/debug.json"
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unknown Magisk channel {channel}\n")
            return
        try:
            payload={}
            headers = {
                'Content-Type': "application/json"
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
            ma = MagiskApk(channel)
            setattr(ma, 'version', data['magisk']['version'])
            setattr(ma, 'versionCode', data['magisk']['versionCode'])
            setattr(ma, 'link', data['magisk']['link'])
            note_link = data['magisk']['note']
            setattr(ma, 'note_link', note_link)
            # Get the note contents
            headers = {}
            response = requests.request("GET", note_link, headers=headers, data=payload)
            setattr(ma, 'release_notes', response.text)
            return ma
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads links processing\nException: {e}")

    # ----------------------------------------------------------------------------
    #                               property magisk_modules_summary
    # ----------------------------------------------------------------------------
    @property
    def magisk_modules_summary(self):
        if self._magisk_modules_summary is None:
            if self.magisk_detailed_modules:
                summary = ''
                for module in self.magisk_detailed_modules:
                    try:
                        summary += "        {:<36}{:<10}{}\n".format(module.name, module.state, module.version)
                    except Exception as e:
                        pass
                self._magisk_modules_summary = summary
            else:
                self._magisk_modules_summary = ''
        return self._magisk_modules_summary

    # ----------------------------------------------------------------------------
    #                               property rooted
    # ----------------------------------------------------------------------------
    @property
    def rooted(self):
        if self._rooted is None:
            if self.mode == 'adb':
                if get_adb():
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls -l /data/adb/magisk/\'\""
                    res = run_shell(theCmd)
                    if res.returncode == 0:
                        self._rooted = True
                    else:
                        self._rooted = False
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
        return self._rooted

    # ----------------------------------------------------------------------------
    #                               property hardware
    # ----------------------------------------------------------------------------
    @property
    def hardware(self):
        if self._hardware is None:
            if self.mode == 'adb':
                if get_adb():
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop ro.hardware"
                    hardware = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    self._hardware = ''.join(hardware.stdout.split())
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
            elif self.mode == 'f.b':
                if get_fastboot():
                    theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar product"
                    hardware = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    hardware = hardware.stderr.split('\n')
                    hardware = hardware[0].split(' ')
                    self._hardware = hardware[1]
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._hardware

    # ----------------------------------------------------------------------------
    #                               property build
    # ----------------------------------------------------------------------------
    @property
    def build(self):
        if self._build is None:
            if self.mode == 'adb':
                if get_adb():
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop ro.build.fingerprint"
                    fingerprint = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    fingerprint = ''.join(fingerprint.stdout.split())
                    self._build = fingerprint.split('/')[3]
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
            else:
               self._build = ''
        return self._build

    # ----------------------------------------------------------------------------
    #                               property active_slot
    # ----------------------------------------------------------------------------
    @property
    def active_slot(self):
        if self._active_slot is None:
            if self.mode == 'adb':
                if get_adb():
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell /bin/getprop ro.boot.slot_suffix"
                    active_slot = run_shell(theCmd)
                    if active_slot.returncode == 127:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop ro.boot.slot_suffix"
                        active_slot = run_shell(theCmd)
                    active_slot = active_slot.stdout.replace("\n", "")
                    self._active_slot = active_slot.replace("_", "")
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
            elif self.mode == 'f.b':
                if get_fastboot():
                    theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar current-slot"
                    active_slot = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    active_slot = active_slot.stderr.split('\n')
                    active_slot = active_slot[0].split(' ')
                    self._active_slot = active_slot[1]
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._active_slot

    # ----------------------------------------------------------------------------
    #                               property unlocked
    # ----------------------------------------------------------------------------
    @property
    def unlocked(self):
        if self._unlocked is None:
            if self.mode == 'f.b':
                if get_fastboot():
                    theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar unlocked"
                    unlocked = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    unlocked = unlocked.stderr.split('\n')
                    unlocked = unlocked[0].split(' ')
                    unlocked = unlocked[1]
                    if unlocked == 'yes':
                        self._unlocked = True
                    else:
                        self._unlocked = False
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._unlocked

    # ----------------------------------------------------------------------------
    #                               property bootloader_version
    # ----------------------------------------------------------------------------
    @property
    def bootloader_version(self):
        if self._bootloader_version is None:
            if self.mode == 'adb':
                if get_adb():
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop ro.bootloader"
                    bootloader_version = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    self._bootloader_version = ''.join(bootloader_version.stdout.split())
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
            elif self.mode == 'f.b':
                if get_fastboot():
                    theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar version-bootloader"
                    bootloader_version = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    bootloader_version = bootloader_version.stderr.split('\n')
                    bootloader_version = bootloader_version[0].split(' ')
                    self._bootloader_version = bootloader_version[1]
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._bootloader_version

    # ----------------------------------------------------------------------------
    #                               property device_info
    # ----------------------------------------------------------------------------
    @property
    def device_info(self):
        if self.mode == 'adb':
            if get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop"
                device_info = run_shell(theCmd)
                self._device_info = ''.join(device_info.stdout)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
        elif self.mode == 'f.b':
            if get_fastboot():
                theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar all"
                device_info = run_shell(theCmd)
                if (device_info.stdout == ''):
                    self._device_info = ''.join(device_info.stderr)
                else:
                    self._device_info = ''.join(device_info.stdout)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._device_info

    # ----------------------------------------------------------------------------
    #                               Method get_details
    # ----------------------------------------------------------------------------
    def get_device_details(self):
        details = "{:<3}({:<3})   {:<25}{:<12}{:<25}".format(self.root_symbol, self.mode, self.id, self.hardware, self.build)
        return details

    # ----------------------------------------------------------------------------
    #                               Method reboot_system
    # ----------------------------------------------------------------------------
    def reboot_system(self):
        print(f"Rebooting device {self.id} to system ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot"
            debug(theCmd)
            res = run_shell(theCmd)
            return res
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot"
            debug(theCmd)
            res = run_shell(theCmd)
            return res

    # ----------------------------------------------------------------------------
    #                               Method reboot_recovery
    # ----------------------------------------------------------------------------
    def reboot_recovery(self):
        print(f"Rebooting device {self.id} to recovery ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot recovery "
            debug(theCmd)
            res = run_shell(theCmd)
            return res
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot recovery"
            debug(theCmd)
            res = run_shell(theCmd)
            return res

    # ----------------------------------------------------------------------------
    #                               Method reboot_bootloader
    # ----------------------------------------------------------------------------
    def reboot_bootloader(self, fastboot_included = False):
        print(f"Rebooting device {self.id} to bootloader ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot bootloader "
            debug(theCmd)
            res = run_shell(theCmd)
            return res
        elif self.mode == 'f.b' and fastboot_included and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot bootloader"
            debug(theCmd)
            res = run_shell(theCmd)
            return res

    # ----------------------------------------------------------------------------
    #                               Method reboot_fastbootd
    # ----------------------------------------------------------------------------
    def reboot_fastboot(self):
        print(f"Rebooting device {self.id} to fastbootd ...")
        print("This process will wait for fastbootd indefinitly.")
        print("WARNING! if your device does not boot to fastbootd PixelFlasher will hang and you'd have to kill it.")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot fastboot "
            debug(theCmd)
            res = run_shell(theCmd)
            return res
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot fastboot"
            debug(theCmd)
            res = run_shell(theCmd)
            return res

    # ----------------------------------------------------------------------------
    #                               Method reboot_sideload
    # ----------------------------------------------------------------------------
    def reboot_sideload(self):
        print(f"Rebooting device {self.id} for sideload ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot sideload "
            debug(theCmd)
            res = run_shell(theCmd)
            return res
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot"
            debug(theCmd)
            res = run_shell(theCmd)
            print("Waiting 5 seconds ...")
            time.sleep(5)
            self.reboot_sideload()
            return res

    # ----------------------------------------------------------------------------
    #                               Method install_apk
    # ----------------------------------------------------------------------------
    def install_apk(self, app, fastboot_included = False):
        if self.mode == 'adb' and get_adb():
            print(f"Installing {app} on device ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} install {app}"
            debug(theCmd)
            res = run_shell(theCmd)
            if res.returncode != 0:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an errorwhile installing {app}")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
            else:
                print(f"{res.stdout}")
            return res
        if self.mode == 'f.b' and fastboot_included and get_fastboot():
            print("Device is in fastboot mode, will reboot to system and wait 60 seconds for system to load before installing ...")
            self.reboot_system()
            time.sleep(60)
            res = self.refresh_phone_mode()
            if self.mode == 'adb' and get_adb():
                res = self.install_apk(app)
            else:
                print(f"Please perform the install again when the device is in adb mode.")
            return res

    # ----------------------------------------------------------------------------
    #                               Method set_active
    # ----------------------------------------------------------------------------
    def set_active_slot(self, slot):
        if self.mode == 'adb' and get_adb():
            self.reboot_bootloader()
            print("Waiting 5 seconds ...")
            time.sleep(5)
            self.refresh_phone_mode()
        if self.mode == 'f.b' and get_fastboot():
            print(f"Setting active slot to slot [{slot}] for device {self.id} ...")
            theCmd = f"\"{get_fastboot()}\" -s {self.id} --set-active={slot}"
            debug(theCmd)
            res = run_shell(theCmd)
            return res

    # ----------------------------------------------------------------------------
    #                               Method lock_bootloader
    # ----------------------------------------------------------------------------
    def lock_bootloader(self):
        if self.mode == 'adb' and get_adb():
            self.reboot_bootloader()
            print("Waiting 5 seconds ...")
            time.sleep(5)
            self.refresh_phone_mode()
        if self.mode == 'f.b' and get_fastboot():
            # add a popup warning before continuing.
            print(f"Unlocking bootloader for device {self.id} ...")
            theCmd = f"\"{get_fastboot()}\" -s {self.id} flashing lock"
            debug(theCmd)
            res = run_shell(theCmd)
            return res

    # ----------------------------------------------------------------------------
    #                               Method unlock_bootloader
    # ----------------------------------------------------------------------------
    def unlock_bootloader(self):
        if self.mode == 'adb' and get_adb():
            self.reboot_bootloader()
            print("Waiting 5 seconds ...")
            time.sleep(5)
            self.refresh_phone_mode()
        if self.mode == 'f.b' and get_fastboot():
            # add a popup warning before continuing.
            print(f"Unlocking bootloader for device {self.id} ...")
            theCmd = f"\"{get_fastboot()}\" -s {self.id} flashing unlock"
            debug(theCmd)
            res = run_shell(theCmd)
            return res

    # ----------------------------------------------------------------------------
    #                               Method enable_magisk_module
    # ----------------------------------------------------------------------------
    def enable_magisk_module(self, dirname):
        if self.mode == 'adb' and get_adb():
            print(f"Enabling magisk module {dirname} ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} wait-for-device shell magisk --remove-modules"
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'rm -f /data/adb/modules/{dirname}/disable\'\""
            debug(theCmd)
            res = run_shell(theCmd)
            return 0
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device {self.id} is not in adb mode.")
            return 1

    # ----------------------------------------------------------------------------
    #                               Method disable_magisk_module
    # ----------------------------------------------------------------------------
    def disable_magisk_module(self, dirname):
        if self.mode == 'adb' and get_adb():
            print(f"Disabling magisk module {dirname} ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} wait-for-device shell magisk --remove-modules"
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'touch /data/adb/modules/{dirname}/disable\'\""
            debug(theCmd)
            res = run_shell(theCmd)
            return 0
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device {self.id} is not in adb mode.")
            return 1

    # ----------------------------------------------------------------------------
    #                               Method disable_magisk_modules
    # ----------------------------------------------------------------------------
    def disable_magisk_modules(self):
        print("Disabling magisk modules ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} wait-for-device shell magisk --remove-modules"
            debug(theCmd)
            res = run_shell(theCmd)
            return res
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot"
            debug(theCmd)
            res = run_shell(theCmd)
            print("Waiting 15 seconds ...")
            time.sleep(15)
            res = self.disable_magisk_modules()
            return res

    # ----------------------------------------------------------------------------
    #                               Method refresh_phone_mode
    # ----------------------------------------------------------------------------
    def refresh_phone_mode(self):
        if self.mode == 'adb' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" devices"
            response = run_shell(theCmd)
            if self.id in response.stdout:
                self.mode = 'f.b'
        elif self.mode == 'f.b' and get_adb():
            theCmd = f"\"{get_adb()}\" devices"
            response = run_shell(theCmd)
            if self.id in response.stdout:
                self.mode = 'adb'


# ============================================================================
#                               Function run_shell
# ============================================================================
def run_shell(cmd):
    try:
        response = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='ISO-8859-1')
        wx.Yield()
        return response
    except Exception as e:
        raise e


# ============================================================================
#                               Function debug
# ============================================================================
def debug(message):
    if get_verbose():
        print("debug: %s" % message)


# ============================================================================
#                               Function get_connected_devices
# ============================================================================
def get_connected_devices():
    devices = []
    phones = []

    if get_adb():
        theCmd = f"\"{get_adb()}\" devices"
        response = run_shell(theCmd)
        if response.stdout:
            for device in response.stdout.split('\n'):
                if '\tdevice' in device:
                    id = device.split("\t")
                    id = id[0]
                    device = Device(id, 'adb')
                    device_details = device.get_device_details()
                    devices.append(device_details)
                    phones.append(device)
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to determine Android Platform Tools version.\n")

    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")

    if get_fastboot():
        theCmd = f"\"{get_fastboot()}\" devices"
        response = run_shell(theCmd)
        for device in response.stdout.split('\n'):
            if '\tfastboot' in device:
                id = device.split("\t")
                id = id[0]
                device = Device(id, 'f.b')
                device_details = device.get_device_details()
                devices.append(device_details)
                phones.append(device)
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")

    set_phones(phones)
    return devices
