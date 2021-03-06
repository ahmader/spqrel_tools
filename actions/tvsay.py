import qi
import argparse
import sys
import time
import threading
from naoqi import ALProxy
import os

import action_base
from action_base import *


actionName = "tvsay"



def actionThread_exec (params):
    t = threading.currentThread()
    memory_service = getattr(t, "mem_serv", None)
    #tts_service = getattr(t, "session", None).service("ALTextToSpeech")
    print "Action "+actionName+" started with params "+params
    #params_list = params.split("_")
    tobi_tts = ALProxy("ALTextToSpeech", os.environ['TOBI_IP'], 9559)
    tobi_tts.setParameter("speed", 90)
    tobi_tts.setParameter("pitchShift", 0.9)
    tobi_memory = ALProxy("ALMemory", os.environ['TOBI_IP'], 9559)
    # action init
    #memory_service.raiseEvent('DialogueVequest', "tvsay_"+params)
    to_say = ''
    if "hello" in params:
        to_say = "Hello! I'm Tobi! Can I help you?"
    elif "andreahere" in params:
        to_say = "Andrea is here!"
    elif "andreanothere" in params:
        to_say = "Andrea is not here!"
    tobi_tts.say(to_say)
    print "  -- VSay: "+params
    val = 0
    time.sleep(1)
    # action init

    while (getattr(t, "do_run", True) and val==0):
        # print "Action "+actionName+" "+params+" exec..."
        # action exec
        val = tobi_memory.getData("ALTextToSpeech/TextDone")
        # action exec
        time.sleep(0.5)


    print "Action "+actionName+" "+params+" terminated"
    # action end

    # action end
    memory_service.raiseEvent("PNP_action_result_"+actionName,"success");


def init(session):
    print actionName+" init"
    tobi_tts = ALProxy("ALTextToSpeech", os.environ['TOBI_IP'], 9559)
    tobi_tts.setParameter("speed", 90)
    tobi_tts.setParameter("pitchShift", 0.9)
    tobi_memory = ALProxy("ALMemory", os.environ['TOBI_IP'], 9559)
    action_base.init(session, actionName, actionThread_exec)


def quit():
    print actionName+" quit"
    actionThread_exec.do_run = False



if __name__ == "__main__":

    app = action_base.initApp(actionName)

    init(app.session)

    #Program stays at this point until we stop it
    app.run()

    quit()


