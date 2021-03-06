import threading

import action_base
from time import sleep

actionName = "continuebtn"


def actionThread_exec(params):
    t = threading.currentThread()
    memory_service = getattr(t, "mem_serv", None)
    # tts_service = getattr(t, "session", None).service("ALTextToSpeech")
    print "Action speechbtn started with params " + params
    # action init
    # action init
    if len(params) > 0:
        memory_service.raiseEvent('ContinueButton', 'continuebtn_' + params)
    else:
        memory_service.raiseEvent('ContinueButton', 'continuebtn_hide')

    print "Action " + actionName + " " + params + " terminated"
    # action end
    sleep(.5)
    memory_service.raiseEvent("PNP_action_result_" + actionName, "success")


def init(session):
    print actionName + " init"
    action_base.init(session, actionName, actionThread_exec)


def quit():
    print actionName + " quit"
    actionThread_exec.do_run = False


if __name__ == "__main__":

    app = action_base.initApp(actionName)

    init(app.session)

    #Program stays at this point until we stop it
    app.run()

    quit()

