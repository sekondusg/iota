from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import logging
import json
import threading



class Iota:
    outlet1 = "off"
    outlet2 = "off"
    motion = "false"
    temperature = 0.0

    def __init__(self):
        pass

        logging.basicConfig(filename='iota.log', level=logging.DEBUG)
        self.log = logging
        self.log.info('init(): creating an instance of Iota')
        self.log.info('init(): retrieving AWS Shadow')
        self.connect()

    def __del__(self):
        #print("del(): disconnecting")
        self.disconnect()

    def connect(self):
        self.log.info('init(): connecting to AWS Shadow')
        thingEndpoint="a3lybv9v64fkof.iot.us-west-2.amazonaws.com"
        self.client = AWSIoTMQTTShadowClient("iota")
        self.client.configureEndpoint(thingEndpoint, 8883)
        self.client.configureCredentials(
            "/home/dennis/.aws/aws-iot-root-ca.pem",
            "/home/dennis/.aws/b498bb82fa-private.pem.key",
            "/home/dennis/.aws/b498bb82fa-certificate.pem.crt")
        self.client.configureConnectDisconnectTimeout(10)  # 10 sec
        self.client.configureMQTTOperationTimeout(5)  # 5 sec
        self.client.connect()
        self.shadow = self.client.createShadowHandlerWithName("iota", True)
        self.log.info('init(): connected to AWS Shadow')

    def disconnect(self):
        self.log.info('disconnect(): disconnecting device client from AWS')
        self.client.disconnect()
        self.log.info('disconnect(): disconnected device client from AWS')


    def onResponse(self, payload, responseStatus, token):
        try:
            print("iota.onResponse(): responseStatus: " + responseStatus)
            # logging.debug("iota.onResponse(): responseStatus: " + responseStatus)

            isChange = False
            response = json.loads(payload)
            pretty = json.dumps(response, indent=4)

            if 'delta' in response['state']:
                for delta in response['state']['delta'].keys():
                    if delta == "outlet1":
                        value = response['state']['delta'][delta]
                        if value in ['on', 'off']:
                            self.setOutlet1(value)
                            isChange = True
                        else:
                            print('onResponse() invalid value for delta update to: ' + str(value))
                    elif delta == "outlet2":
                        value = response['state']['delta'][delta]
                        if value in ['on', 'off']:
                            self.setOutlet2(value)
                            isChange = True
                        else:
                            print('onResponse() invalid value for delta update to: ' + str(value))
            if isChange:
                self.shadow.shadowUpdate()

            self.log.info(
                "onResponse(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(
                    pretty))
            # logging.debug("onResponse(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(ps))
            print("iota.onResponse(): payload: " + str(pretty))
        except Exception as ex:
            print("onResponse() exception: " + str(ex))


    def onDelta(self, payload, responseStatus, token):
        try:
            print("iota.onDelta(): responseStatus: " + responseStatus)

            delta = json.loads(payload)
            pretty = json.dumps(delta, indent=4)
            self.log.info("onDelta(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(pretty))
            #logging.debug("onResponse(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(ps))
            print("iota.onDelta(): payload: " + str(pretty))
        except Exception as ex:
            print("onDelta() exception: " + str(ex))


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
