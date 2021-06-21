#!/usr/bin/env python
"""
Written by Matt Palmer
Github : https://github.com/mattpuk

This code is released under the terms of the Apache 2
http://www.apache.org/licenses/LICENSE-2.0.html

Attribution:
    I based some of this script on an old pull request I found 
    at gitmemory.com
https://github.com/vmware/pyvmomi-community-samples/issues/664
https://www.gitmemory.com/hitesh-smit


Example code for deleting scheduled tasks for a VM.


Run: 
>>> import pytz
>>> pytz.all_timezones

to return a list of all valid Timezones

Tasks must be executed in series using a for loop outside of the function itself
i.e:
    PO_schedule.txt contains a CR'd list of VMs to execute task against.
    for i in `cat schedule.txt`; do python remove-scheduled-tasks.py -s <vcentre-hostname> -u <first.last@domain> -p <passwd> -n $i; done
    
NOTE:You can either specify a single VM name to remove a task for
or when running the loop as above, regardless of the contents of
the schedule file it will actually loop and remove *ALL* scheduled
tasks across everything.
"""

import atexit
import argparse
import getpass
import pytz
from datetime import datetime
from pyVmomi import vim
from pyVim import connect
now = datetime.now()


def get_args():
    parser = argparse.ArgumentParser(
        description='return list of scheduled tasks of a virtual machine')
    parser.add_argument('-s', '--host', required=True, action='store',
                        help='Remote host to connect to')
    parser.add_argument('-o', '--port', type=int, default=443, action='store',
                        help='Port to connect on')
    parser.add_argument('-u', '--user', required=True, action='store',
                        help='User name to use when connecting to host')
    parser.add_argument('-p', '--password', required=False, action='store',
                        help='Password to use when connecting to host')
    parser.add_argument('-n', '--vmname', required=True, action='store',
                        help='VM name on which the action will be performed')
    args = parser.parse_args()
    return args


def main():
    args = get_args()

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

    def getobject(vimtype, name):
        obj = None
        container = si.content.viewManager.CreateContainerView(si.content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj
    
    machine = getobject([vim.VirtualMachine], args.vmname)
    print(machine,args.vmname)
    taskManager = si.content.taskManager
    retrieveEntityScheduledTask = si.content.scheduledTaskManager.RetrieveEntityScheduledTask(machine)
    print("Retrieve VM Scheduled Tasks :", str(retrieveEntityScheduledTask))
    
    for vmScheduledTask in retrieveEntityScheduledTask:
        print("Retrieve vm Scheduled Tasks: ",vmScheduledTask)
    #get schedule task name
        taskName = vmScheduledTask.info.name
        print("RunOnce Task Name: ",taskName)
    
        OnceTaskScheduler = vmScheduledTask.info.scheduler
        print(OnceTaskScheduler)

        if isinstance(OnceTaskScheduler, vim.scheduler.OnceTaskScheduler):
           vmScheduledTask.RemoveScheduledTask()

if __name__ == "__main__":
    main()
