import PyQt5
from PyQt5 import QtCore
from PyQt5 import QtBluetooth


class DeviceFinder(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.m_devices = []

        adapter_address = "00:1A:7D:DA:71:13"

        
        # Step 1: List all local Bluetooth adapters
        local_devices = QtBluetooth.QBluetoothLocalDevice.allDevices()
        # Print all local devices
        for device in local_devices:
            print(f"Bluetooth adapter: {device.name()} ({device.address().toString()})")
            
        if not local_devices:
            print("No local Bluetooth adapters found.")
            sys.exit()
            
        # Selecting a specific adapter if an address is provided
        if adapter_address:
            self.local_device = next((device for device in local_devices if device.address().toString() == adapter_address), None)
            if not self.local_device:
                print("No local Bluetooth adapter found with the address: {}".format(adapter_address))
                print("Using the first local device.")
                self.local_device = local_devices[0]
                
        else:
            print("No adapter address provided.")
           

        print(f"Using adapter: {self.local_device.name()} ({self.local_device.address().toString()})")

        test = QtBluetooth.QBluetoothAddress(adapter_address)


        self.deviceDiscoveryAgent = QtBluetooth.QBluetoothDeviceDiscoveryAgent(test)
        if self.deviceDiscoveryAgent.error() != QtBluetooth.QBluetoothDeviceDiscoveryAgent.NoError:
            print("Discovery agent error:", self.deviceDiscoveryAgent.errorString())

        self.deviceDiscoveryAgent.setLowEnergyDiscoveryTimeout(25000)
        self.deviceDiscoveryAgent.deviceDiscovered.connect(self.add_device)
        self.deviceDiscoveryAgent.error.connect(self.scan_error)
        self.deviceDiscoveryAgent.finished.connect(self.scan_finished)
        self.deviceDiscoveryAgent.canceled.connect(self.scan_finished)

        self.deviceDiscoveryAgent.start(QtBluetooth.QBluetoothDeviceDiscoveryAgent.DiscoveryMethod(2))

    def add_device(self, device):
        # Print the name, address, and RSSI of the device
        print("Device found: {name}, {address}, {rssi}".format(name=device.name(), address=device.address().toString(), rssi=device.rssi()))

        # If device is LowEnergy-device, add it to the list
        if device.coreConfigurations() and QtBluetooth.QBluetoothDeviceInfo.LowEnergyCoreConfiguration:
            self.m_devices.append( QtBluetooth.QBluetoothDeviceInfo(device) )
            print("Low Energy device found: {name}, {address}, {rssi}".format(name=device.name(), address=device.address().toString(), rssi=device.rssi()))

    def scan_finished(self):
        print("scan finished")
        for i in self.m_devices:
            #QtBluetooth.QBluetoothDeviceInfo.
            print('Name: {name}, Address: {address}, rssi: {rssi}, UUID: {UUID}'.format(UUID=i.deviceUuid().toString(),
                                                                    name=i.name(),
                                                                    address=i.address().toString(),
                                                                    rssi=i.rssi()))
        self.quit()

    def scan_error(self):
        print("scan error")

    def quit(self):
        print("Bye!")
        QtCore.QCoreApplication.instance().quit()


if __name__ == "__main__":
    import sys
    app = QtCore.QCoreApplication(sys.argv)
    hello = DeviceFinder()
    sys.exit(app.exec_())