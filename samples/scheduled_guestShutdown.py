#!/usr/bin/env python
"""
Written by Gaël Berthaud-Müller
Github : https://github.com/blacksponge

This code is released under the terms of the Apache 2
http://www.apache.org/licenses/LICENSE-2.0.html

Example code for using the task scheduler.

29/04/2021 - Matt Palmer
Amended to add unique code to the task so the same task can be
repeated without housekeeping
spec.name = (now.strftime("%Y-%m-%d %H:%M:%S")) + ‘Planned Guest Shutdown vm %s' % args.vmname
now = datetime.now()

22/09/2021 - Matt Palmer
Changed the vim.Virtual.x object to contain ".ShutdownGuest"
spec.action.name = vim.VirtualMachine.ShutdownGuest

22/09/2021 - Matt Palmer
Because tasks can only be added individually, I need to find a good way to
pull all the guests from a list and have them execute as one task action.

Tasks must be executed in series using a for loop outside of the function itself
i.e:
    PO_schedule.txt contains a CR'd list of VMs to execute task against.
    for i in `cat PO_schedule.txt`; do python scheduled_guestShutdown.py -s <vcentre-hostname> -u <first.last@domain> -d 'dd/mm/yyyy HH:MM' -p <passwd> -n $i; done
"""

import atexit
import argparse
import getpass
from datetime import datetime
from pyVmomi import vim
from pyVim import connect
now = datetime.now()

def get_args():
    parser = argparse.ArgumentParser(
        description='Arguments for scheduling a poweroff of a virtual machine')
    parser.add_argument('-s', '--host', required=True, action='store',
                        help='Remote host to connect to')
    parser.add_argument('-o', '--port', type=int, default=443, action='store',
                        help='Port to connect on')
    parser.add_argument('-u', '--user', required=True, action='store',
                        help='User name to use when connecting to host')
    parser.add_argument('-p', '--password', required=False, action='store',
                        help='Password to use when connecting to host')
    parser.add_argument('-d', '--date', required=True, action='store',
                        help='Date and time used to create the scheduled task '
                        'with the format d/m/Y H:M')
    parser.add_argument('-n', '--vmname', required=True, action='store',
                        help='VM name on which the action will be performed')
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    try:
        dt = datetime.strptime(args.date, '%d/%m/%Y %H:%M')
    except ValueError:
        print('Unrecognized date format')
        raise
        return -1

    if args.password:
        password = args.password
    else:
        password = getpass.getpass(prompt='Enter password for host %s and '
                                   'user %s: ' % (args.host, args.user))

    try:
        si = connect.SmartConnectNoSSL(host=args.host,
                                       user=args.user,
                                       pwd=password,
                                       port=int(args.port))
    except vim.fault.InvalidLogin:
        print("Could not connect to the specified host using specified "
              "username and password")
        return -1

    atexit.register(connect.Disconnect, si)

    view = si.content.viewManager.CreateContainerView(si.content.rootFolder,
                                                      [vim.VirtualMachine],
                                                      True)
    vms = [vm for vm in view.view if vm.name == args.vmname]

    if not vms:
        print('VM not found')
        connect.Disconnect(si)
        return -1
    vm = vms[0]

    spec = vim.scheduler.ScheduledTaskSpec()
    spec.name = (now.strftime("%Y-%m-%d %H:%M:%S")) + ‘Planned GuestShutdown vm %s' % args.vmname 
    #spec.name = ‘Planned Guest Shutdown vm %s' % args.vmname
    spec.description = ''
    spec.scheduler = vim.scheduler.OnceTaskScheduler()
    spec.scheduler.runAt = dt
    spec.action = vim.action.MethodAction()
    spec.action.name = vim.VirtualMachine.ShutdownGuest
    spec.enabled = True

    si.content.scheduledTaskManager.CreateScheduledTask(vm, spec)


if __name__ == "__main__":
    main()
