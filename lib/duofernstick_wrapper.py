
def toPercentage(stringInput):
    numberValue = int(stringInput)
    if not 0 <= numberValue <= 100:
        raise ValueError()
    return numberValue

def toOnOffString(stringInput):
    if not stringInput in ['on', 'off']:
        raise ValueError()
    return stringInput

class ShutterStickWrapper:

    writeablePropertyValidators = {
        'sunMode':              toOnOffString,
        'position':             toPercentage,
        'sunPosition':          toPercentage,
        'ventilatingPosition':  toPercentage,
        'dawnAutomatic':        toOnOffString,
        'duskAutomatic':        toOnOffString,
        'manualMode':           toOnOffString,
        'sunAutomatic':         toOnOffString,
        'timeAutomatic':        toOnOffString,
        'ventilatingMode':      toOnOffString,
    }

    noArgCommands = [
        'up',
        'down',
        'stop',
        'toggle',
    ]

    def __init__(self, duofernstick):
        self.duofernstick = duofernstick


    def deviceExists(self, deviceCode):
        return deviceCode in self.devices

    def deviceHasProperty(self, deviceCode, deviceProperty):
        return self.deviceExists(deviceCode) \
            and ( deviceProperty in self.devices[deviceCode] \
                    or deviceProperty in ShutterStickWrapper.noArgCommands )

    def getPropertyAsBytes(self, deviceCode, deviceProperty):
        return bytes(str(self.devices[deviceCode][deviceProperty]), 'utf-8')

    @property
    def devices(self):
        return self.duofernstick.duofern_parser.modules['by_code']

    @staticmethod
    def isWritable(property):
        return property in ShutterStickWrapper.writeablePropertyValidators \
            or property in ShutterStickWrapper.noArgCommands

    @staticmethod
    def isReadable(property):
        return property not in ShutterStickWrapper.noArgCommands

    @staticmethod
    def sanitizeInput(property, value):
        if not ShutterStickWrapper.isWritable(property):
            raise ValueError()
        return ShutterStickWrapper.writeablePropertyValidators[property](value)

