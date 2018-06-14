from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient


class Iota:

    def __init__(self):
        pass

        thingEndpoint="a3lybv9v64fkof.iot.us-west-2.amazonaws.com"
        myShadowClient = AWSIoTMQTTShadowClient("iota")
        myShadowClient.configureEndpoint(thingEndpoint, 8883)
        myShadowClient.configureCredentials(
            "/home/dennis/.aws/aws-iot-root-ca.pem",
            "/home/dennis/.aws/b498bb82fa-private.pem.key",
            "/home/dennis/.aws/b498bb82fa-certificate.pem.crt")
        myShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
        myShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
        myShadowClient.connect()
        self.shadow = myShadowClient.createShadowHandlerWithName("iota", True)

    def onResponse(self, payload, responseStatus, token):
        pd = json.loads(payload)
        ps = json.dumps(pd, indent=4)
        print("onResponse(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(ps))

    def onDelta(self, payload, responseStatus, token):
        pd = json.loads(payload)
        ps = json.dumps(pd, indent=4)
        print("onDelta(): responseStatus: " + str(responseStatus) + ", token: " + str(token) + ", payload: " + str(ps))

iota = Iota()

def onResponse(payload, responseStatus, token):
    iota.onResponse(payload, responseStatus, token)

def onDelta(payload, responseStatus, token):
    iota.onDelta(payload, responseStatus, token)
