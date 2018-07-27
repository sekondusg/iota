import json
import logging
import threading
import sys
import time
from optparse import OptionParser
import daemon
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

from pyfirmata import Arduino, util
import os
import signal


class Iota:
    # Device State
    outlet1 = "off"
    outlet2 = "off"
    motion = "false"
    temperature = 0.0
    sense = None

    thingEndpoint = "a3lybv9v64fkof.iot.us-west-2.amazonaws.com"
    awsDir = "/home/dennis/.aws"
    # awsDir = "/users/denni/aws"
    credentialFiles = (
        awsDir + "/aws-iot-root-ca.pem",
        awsDir + "/b498bb82fa-private.pem.key",
        awsDir + "/b498bb82fa-certificate.pem.crt"
    )

    def __init__(self):

        logging.basicConfig(filename='iota.log', level=logging.DEBUG)
        #logging.basicConfig(stream=sys.__stdout__, level=logging.INFO)
        self.log = logging
        self.log.info('init(): creating an instance of Iota')
        self.connect()
        self.log.info('init(): retrieving AWS Shadow')
        self.shadow = self.client.createShadowHandlerWithName("iota", True)
        self.log.info('init(): registering delta callback')
        self.log.info('init(): Iota created')

        # Setup the Arduino Firmata interface
        self.log.info('init(): setting-up firmata')
        self.board = None
        for i in range(0, 10):
            if os.path.exists('/dev/ttyACM' + str(i)):
                self.log.info('init(): firmata: found serial device: ' + '/dev/ttyACM' + str(i))
                self.board = Arduino('/dev/ttyACM' + str(i))
                break

        self.log.info('init(): getting iterator for board')
        it = util.Iterator(self.board)
        it.start()
        self.log.info('init(): started iterator for board')
        self.board.analog[0].enable_reporting()
        self.board.analog[1].enable_reporting()
        self.d7 = self.board.get_pin('d:7:i')
        self.d8 = self.board.get_pin('d:8:o')
        self.d9 = self.board.get_pin('d:9:o')
        self.log.info('init(): finished firmata setup')

    def __del__(self):
        self.log.info("del(): disconnecting")
        self.disconnect()

    def connect(self):
        self.log.info('init(): connecting to AWS Shadow')
        self.client = AWSIoTMQTTShadowClient("iota")
        self.client.configureEndpoint(self.thingEndpoint, 8883)
        self.client.configureCredentials(*self.credentialFiles)
        self.client.configureConnectDisconnectTimeout(10)  # 10 sec
        self.client.configureMQTTOperationTimeout(5)  # 5 sec
        self.client.connect()
        self.log.info('init(): connected to AWS Shadow')

    def disconnect(self):
        self.log.info('disconnect(): disconnecting device client from AWS')
        self.client.disconnect()
        self.log.info('disconnect(): disconnected device client from AWS')

    def onResponse(self, payload, responseStatus, token):
        try:
            self.log.info("iota.onResponse(): responseStatus: " + responseStatus)
            # logging.debug("iota.onResponse(): responseStatus: " + responseStatus)

            response = json.loads(payload)
            pretty = json.dumps(response, indent=4)

            self.log.info(
                "onResponse(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(
                    pretty))
            # logging.debug("onResponse(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(ps))
            self.log.info("iota.onResponse(): payload: " + str(pretty))
        except Exception as ex:
            self.log.info("onResponse() exception: " + str(ex))

    def onDelta(self, payload, responseStatus, token):
        try:
            self.log.info("iota.onDelta(): responseStatus: " + responseStatus)

            changes = []
            deltas = json.loads(payload)
            pretty = json.dumps(deltas, indent=4)

            for delta in deltas['state'].keys():
                if delta == "outlet1":
                    value = deltas['state'][delta]
                    if value in ['on', 'off']:
                        self.setOutlet1(value)
                        changes.append((delta, value,))
                    else:
                        self.log.info('onDelta() invalid value for delta update to: ' + str(value))
                elif delta == "outlet2":
                    value = deltas['state'][delta]
                    if value in ['on', 'off']:
                        self.setOutlet2(value)
                        changes.append((delta, value,))
                    else:
                        self.log.info('onDelta() invalid value for delta update to: ' + str(value))
            if len(changes) > 0:
                self.log.info('onDelta() detected changes to: ' + str(changes))
                self.shadowUpdate(reported=changes)
            self.log.info(
                "onDelta(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(
                    pretty))
        except Exception as ex:
            self.log.info("onDelta() exception: " + str(ex))

    def shadowUpdate(self, reported=None, desired=None):
        self.log.info('iota.shadowUpdate(): starting. preparing to update device shadow for reported: ' + str(reported) + ", or desired: " + str(desired))
        update = {
            'state': {
                'reported': {},
                'desired': {}
            }
        }

        if reported is not None:
            for change in reported:
                update['state']['reported'][change[0]] = change[1]

        if desired is not None:
            for change in desired:
                update['state']['desired'][change[0]] = change[1]

        doc = json.dumps(update)
        self.log.info('iota.shadowUpdate(): calling shadow.shadowUpdate. srcJSONPayload: ' + doc)
        self.shadow.shadowUpdate(doc, onResponse, 5)
        self.log.info('iota.shadowUpdate(): finished request to update device shadow')

    def getShadow(self):
        logging.info("getShadow(): retrieving shadow doc from AWS")
        shadow = self.shadow.shadowGet(onResponse, 5)
        return (shadow)

    def getOutlet1(self):
        logging.info("getOutlet1: getting value of outlet1")
        return self.outlet1

    def setOutlet1(self, value):
        if value in ['on', 'off']:
            logging.info("setOutlet1: setting value of outlet1 to: " + value)
            self.outlet1 = value
            if value == 'on':
                self.d8.write(False)
            else:
                self.d8.write(True)
        else:
            logging.error("setOutlet1: invalid value given for setting outlet1: " + value)

    def getOutlet2(self):
        logging.info("getOutlet2: getting value of outlet2")
        return self.outlet2

    def setOutlet2(self, value):
        if value in ['on', 'off']:
            logging.info("setOutlet2 setting value of outlet2 to: " + value)
            self.outlet2 = value
            if value == 'on':
                self.d9.write(False)
            else:
                self.d9.write(True)
        else:
            logging.error("setOutlet2: invalid value given for setting outlet2: " + value)

    def getTemp(self):
        logging.info("getTemp(): getting temperature through Firmata")
        return( str(round(self.board.analog[1].read() * 500) ))

    def getRH(self):
        logging.info("getTemp(): getting relative humidity through Firmata")
        return(str(round(100 * self.board.analog[0].read())))

    def getMotion(self):
        logging.info("getTemp(): getting motion through Firmata")
        mot = self.d7.read()
        if mot == None:
            return 'na'
        else:
            return str(mot)

    def setMotion(self, value):
        if value in ['true', 'false']:
            logging.info("setMotion setting value of motion to: " + value)
            self.motion = value
        else:
            logging.error("setMotion: invalid value given for setting motion: " + value)

    def getSense(self):
        logging.info("getSense(): getting values of all sensors")
        return( (self.getTemp(), self.getRH(), self.getMotion(),) )

    def listen(self):
        while True:

            # sense = (temp, rh, motion)
            sense = self.getSense()
            if self.sense is None or sense != self.sense:
                changes = []

                '''
                if self.sense[0] != sense[0]:
                    changes.append( ("temp", sense[0],) )
                if self.sense[1] != sense[1]:
                    changes.append( ("rh", sense[1],) )
                if self.sense[2] != sense[2]:
                    changes.append( ("motion", sense[2],) )
                '''
                changes.append(("temp", sense[0],))
                changes.append(("rh", sense[1],))
                changes.append(("motion", sense[2],))
                self.shadowUpdate(reported=changes)
            self.sense = sense

            time.sleep(1)


def onResponse(payload, responseStatus, token):
    global iota
    try:
        print("onResponse(): calling iota.onResponse(): responseStatus: " + responseStatus)
        threading.Thread(group=None, target=iota.onResponse, args=(payload, responseStatus, token,)).start()
        print("onResponse(): thread spawned by caller")
    except Exception as ex:
        print("onResponse() exception: " + str(ex))


def onDelta(payload, responseStatus, token):
    global iota
    try:
        print("onDelta(): calling iota.onDelta(): responseStatus: " + responseStatus)
        threading.Thread(group=None, target=iota.onDelta, args=(payload, responseStatus, token,)).start()
        print("onDelta(): thread spawned by caller")
    except Exception as ex:
        print("onDelta() exception: " + str(ex))


# iota = Iota()

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-D", "--debug", dest="debug", action='store_true', default=False, help="Run in debug mode")
    parser.add_option("-1", "--outlet1", dest="outlet1", action='store', default=None, type="string", help="set outlet 1 to given value")
    parser.add_option("-2", "--outlet2", dest="outlet2", action='store', default=None, type="string", help="set outlet 2 to given value")
    parser.add_option("-f", "--fore", dest="fore", action='store_true', default=False,
                      help="Run as a foreground process instead of a daemon")

    (options, args) = parser.parse_args()

    print("parsed arguments")
    def shutdown(signum, frame):
        iota.disconnect()
        sys.exit(0)

    if not options.debug:
        print("not in debug mode")
        # check for any direct command line commands, otherwise run as a daemon
        if options.outlet1 is None and options.outlet2 is None:
            print("in daemon mode")
            if options.fore:
                print('\033]0;IoTaAgent\a')
                iota = Iota()
                iota.shadow.shadowRegisterDeltaCallback(onDelta)
                iota.listen()
            else:
                print("starting in background daemon mode")
                with daemon.DaemonContext(
                    signal_map = {
                        signal.SIGTERM: shutdown,
                        signal.SIGTSTP: shutdown
                    }
                ):
                    iota = Iota()
                    iota.shadow.shadowRegisterDeltaCallback(onDelta)
                    iota.listen()
        else:
            print("starting in non-daemon mode")
            iota = Iota()
            changes = []
            if options.outlet1 is not None:
                if options.outlet1 in ["on", "off"]:
                    changes.append(("outlet1", options.outlet1,))
                else:
                    print("option outlet1 must be either 'on' or 'off', given: " + options.outlet1)
            if options.outlet2 is not None:
                if options.outlet2 in ["on", "off"]:
                    changes.append( ("outlet2", options.outlet2,) )
                else:
                    print("option outlet2 must be either 'on' or 'off', given: " + options.outlet2)

            if len(changes) > 0:
                iota.shadowUpdate(desired=changes)
            iota.disconnect()
