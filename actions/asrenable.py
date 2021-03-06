import qi
import argparse
import sys
import time
import threading

import action_base
from action_base import *


actionName = "asrenable"
asrkey = 'ASR_enable'

def actionThread_exec (params):
    t = threading.currentThread()
    memory_service = getattr(t, "mem_serv", None)
    
    print "Action "+actionName+" "+params+" started"
    # action init
    if (params=='off'):
        memory_service.raiseEvent(asrkey,'0')
    else:
        memory_service.raiseEvent(asrkey,'1')
    # action init
    
    time.sleep(1.0)

    print "Action "+actionName+" "+params+" terminated"

    memory_service.raiseEvent("PNP_action_result_"+actionName,"success");


def init(session):
    print actionName+" init"
    action_base.init(session, actionName, actionThread_exec)
    session.service("ALMemory").declareEvent('DialogueVequest')


def quit():
    print actionName+" quit"
    actionThread_exec.do_run = False
    


if __name__ == "__main__":

    app = action_base.initApp(actionName)
        
    init(app.session)

    #Program stays at this point until we stop it
    app.run()

    quit()


