import json
import logging
import threading
import sys
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient


class Iota:
    outlet1 = "off"
    outlet2 = "off"
    motion = "false"
    temperature = 0.0
    thingEndpoint = "a3lybv9v64fkof.iot.us-west-2.amazonaws.com"
    awsDir = "/home/dennis/.aws"
    awsDir = "/users/denni/aws"
    credentialFiles = (
        awsDir + "/aws-iot-root-ca.pem",
        awsDir + "/b498bb82fa-private.pem.key",
        awsDir + "/b498bb82fa-certificate.pem.crt"
    )

    def __init__(self):
        pass

        #logging.basicConfig(filename='iota.log', level=logging.DEBUG)
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.log = logging
        self.log.info('init(): creating an instance of Iota')
        self.connect()
        self.log.info('init(): retrieving AWS Shadow')
        self.shadow = self.client.createShadowHandlerWithName("iota", True)
        self.log.info('init(): registering delta callback')
        #self.shadow.shadowRegisterDeltaCallback(onDelta)
        self.log.info('init(): Iota created')

    def __del__(self):
        self.log.info("del(): disconnecting")
        self.disconnect()

    def connect(self):
        self.log.info('init(): connecting to AWS Shadow')
        self.client = AWSIoTMQTTShadowClient("iota")
        self.client.configureEndpoint(self.thingEndpoint, 8883)
        self.client.configureCredentials( *self.credentialFiles )
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
                self.shadowUpdate(changes)
            self.log.info("onDelta(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(pretty))
        except Exception as ex:
            self.log.info("onDelta() exception: " + str(ex))

    def shadowUpdate(self, changes):
        self.log.info('iota.shadowUpdate(): starting. preparing to update device shadow for changes: ' + str(changes))
        update = {
            'state': {
                    'reported': {},
                    'desired': {}
            }
        }

        for change in changes:
            update['state']['reported'][change[0]] = change[1]

        doc = json.dumps(update)
        self.log.info('iota.shadowUpdate(): calling shadow.shadowUpdate. srcJSONPayload: ' + doc)
        self.shadow.shadowUpdate(doc, onResponse, 5)
        self.log.info('iota.shadowUpdate(): finished request to update device shadow')


    def getShadow(self):
        logging.debug("getShadow(): retrieving shadow doc from AWS")
        shadow = self.shadow.shadowGet(onResponse, 5)
        return(shadow)

    def getOutlet1(self):
        logging.debug("getOutlet1: getting value of outlet1")
        return self.outlet1

    def setOutlet1(self, value):
        if value in ['on', 'off']:
            logging.debug("setOutlet1: setting value of outlet1 to: " + value)
            self.outlet1 = value
        else:
            logging.error("setOutlet1: invalid value given for setting outlet1: " + value)

    def getOutlet2(self):
        logging.debug("getOutlet2: getting value of outlet2")
        return self.outlet2

    def setOutlet2(self, value):
        if value in ['on', 'off']:
            logging.debug("setOutlet2 setting value of outlet2 to: " + value)
            self.outlet2 = value
        else:
            logging.error("setOutlet2: invalid value given for setting outlet2: " + value)

    def getMotion(self):
        logging.debug("getMotion: getting value of motion")
        return self.motion

    def setMotion(self, value):
        if value in ['true', 'false']:
            logging.debug("setMotion setting value of motion to: " + value)
            self.motion = value
        else:
            logging.error("setMotion: invalid value given for setting motion: " + value)



iota = Iota()

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


#iota.setOutlet1('abc')
#iota.setOutlet1('off')
#print('shadow: ' + str(iota.getShadow()))
