#!/usr/bin/env python
#
# cpaggen - May 16 2015 - Proof of Concept (little to no error checks)
#  - rudimentary args parser
#  - GetHostsPortgroups() is quite slow; there is probably a better way
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
#from pyVim.connect import SmartConnect, Disconnect
#from pyVmomi import vim
import atexit
import sys
from tools import cli

from pyVim.connect import SmartConnectNoSSL, Disconnect
import ssl
matt_disable_cert_context = ssl._create_unverified_context()
s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
s.verify_mode = ssl.CERT_NONE
import argparse
from pyVmomi import vmodl
from pyVmomi import vim

def setup_args():

    """
    Get standard connection arguments
    """
    parser = cli.build_arg_parser()
    my_args = parser.parse_args()

    return cli.prompt_for_password(my_args)


def GetVMHosts(content):
    print("Getting all ESX hosts ...")
    host_view = content.viewManager.CreateContainerView(content.rootFolder,
                                                        [vim.HostSystem],
                                                        True)
    obj = [host for host in host_view.view]
    host_view.Destroy()
    return obj


def GetVMs(content):
    print("Getting all VMs ...")
    vm_view = content.viewManager.CreateContainerView(content.rootFolder,
                                                      [vim.VirtualMachine],
                                                      True)
    obj = [vm for vm in vm_view.view]
    vm_view.Destroy()
    return obj


def GetHostsPortgroups(hosts):
    print("Collecting portgroups on all hosts. This may take a while ...")
    hostPgDict = {}
    for host in hosts:
        pgs = host.config.network.portgroup
        hostPgDict[host] = pgs
        #dvs = get_obj(content, [vim.DistributedVirtualSwitch], dvs_name)
        #dv_pg = get_obj(content, [vim.dvs.DistributedVirtualPortgroup], dv_pg_name)
        print("\tHost {} done.".format(host.name))
    print("\tPortgroup collection complete.")
    return hostPgDict


def PrintVmInfo(vm):
    vmPowerState = vm.runtime.powerState
    print("#Found VM:", vm.name + "(" + vmPowerState + ")")
    GetVMNics(vm)


def GetVMNics(vm):
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard):
            dev_backing = dev.backing
            portGroup = None
            vlanId = None
            vSwitch = None
            if hasattr(dev_backing, 'port'):
                portGroupKey = dev.backing.port.portgroupKey
                dvsUuid = dev.backing.port.switchUuid
                try:
                    dvs = content.dvSwitchManager.QueryDvsByUuid(dvsUuid)
                except:
                    portGroup = "** Error: DVS not found **"
                    vlanId = "NA"
                    vSwitch = "NA"
                else:
                    pgObj = dvs.LookupDvPortGroup(portGroupKey)
                    portGroup = pgObj.config.name
                    vlanId = str(pgObj.config.defaultPortConfig.vlan.pvlanId)
                    vSwitch = str(dvs.name)
            else:
                portGroup = dev.backing.network.name
                vmHost = vm.runtime.host
                # global variable hosts is a list, not a dict
                host_pos = hosts.index(vmHost)
                viewHost = hosts[host_pos]
                # global variable hostPgDict stores portgroups per host
                pgs = hostPgDict[viewHost]
                for p in pgs:
                    if portGroup in p.key:
                        vlanId = str(p.spec.vlanId)
                        vSwitch = str(p.spec.vswitchName)
            if portGroup is None:
                portGroup = 'NA'
            if vlanId is None:
                vlanId = 'NA'
            if vSwitch is None:
                vSwitch = 'NA'
            print('\t' + dev.deviceInfo.label + '->' + dev.macAddress +
                  ' @ ' + vSwitch + '->' + portGroup +
                  ' (VLAN ' + vlanId,vm.name + ')')



def main():
    global content, hosts, hostPgDict
    args = setup_args()
    si = None
    try:
    
        si = SmartConnectNoSSL(host=args.host,
                          user=args.user,
                          pwd=args.password,
                          port=int(args.port))
        atexit.register(Disconnect, si)
    except vim.fault.InvalidLogin:
        raise SystemExit("Unable to connect to host "
                         "with supplied credentials.")
    content = si.RetrieveContent()
    hosts = GetVMHosts(content)
    hostPgDict = GetHostsPortgroups(hosts)
    vms = GetVMs(content)
    for vm in vms:
        PrintVmInfo(vm)

# Main section
if __name__ == "__main__":
    sys.exit(main())
