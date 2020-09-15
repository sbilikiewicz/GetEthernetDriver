######################################################
#
#   Get Matching Ethernet Driver ( Python 3.7.7 )
#       Last edit: Szymon Bilikiewicz
#       TODO:
#       - Linux support
#
######################################################
import json
import os
import platform
import subprocess


class DriverParser:

    def iswindows(self):
        OS = platform.system()
        if OS == "Windows":
            return True
        else:
            return False

    def exec_powershell(self, command):
        process = subprocess.Popen(["powershell", command], stdout=subprocess.PIPE)
        result = process.communicate()[0]
        # Original output is in bytes
        return result.decode("utf-8")

    def getosndis(self):
        winver = self.exec_powershell("(Get-WmiObject -class Win32_OperatingSystem).Caption")
        if "2012" in winver:
            return "NDIS64"
        elif "2016" in winver:
            return "NDIS65"

        return "NDIS68"

    def getdrivers(self, driver_container, id_only):
        if not self.iswindows():
            print("ERROR GetDrivers is designed for Windows only!")
            return

        out = self.exec_powershell(
            "Get-PnpDevice * | Where { $_.FriendlyName -like '*Ethernet*' } "
            "| Select PNPDeviceID, FriendlyName | ConvertTo-Json")

        infs = []
        ndis = self.getosndis()
        for root, dirs, files in os.walk(driver_container):
            for file in files:
                if file.endswith(".inf"):
                    path = os.path.join(root, file)
                    # Only appropriate for our OS
                    if ndis in path:
                        infs.append(path)

        matched_drivers = []
        devices = json.loads(out)
        for dev in devices:
            dev_id = ""
            # Fix it later for SP adapters
            if type(dev) == str:
                dev_id = dev
            else:
                dev_id = dev['PNPDeviceID']

            # Skip virtual adapters etc.
            if "PCI" not in dev_id:
                continue

            # Only devID and subsys is what we need
            sub_index = dev_id.index("SUBSYS")
            sub_index2 = dev_id.index('&', sub_index)
            sub_id = dev_id[0:sub_index2]
            if id_only:
                div1 = sub_id.rfind("&")
                sub_id = sub_id[0:div1]

            for inf in infs:
                # Some irrelevant encoding errors may occur in inf files so let's ignore them
                with open(inf, encoding="utf8", errors="ignore") as file:
                    if sub_id in file.read():
                        matched_drivers.append(inf)

        return matched_drivers


search_in = "C:\Drivers"
parser = DriverParser()
output = parser.getdrivers(search_in, False)
if len(output) == 0:
    print("Unable to match driver with SUBSYS, proceeding with devID only")
    output = parser.getdrivers(search_in, True)

for match in output:
    print(match)