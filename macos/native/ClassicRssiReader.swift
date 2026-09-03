import Foundation
import IOBluetooth

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("usage: ClassicRssiReader DEVICE\n".utf8))
    exit(2)
}

let wanted = CommandLine.arguments[1]
let paired = (IOBluetoothDevice.pairedDevices() as? [IOBluetoothDevice]) ?? []
guard let device = paired.first(where: { ($0.name ?? "").localizedCaseInsensitiveContains(wanted) }) else {
    print("missing")
    exit(0)
}

while device.isConnected() {
    let value = Int(device.rawRSSI())
    print(value == 127 ? "unknown" : String(value))
    fflush(stdout)
    Thread.sleep(forTimeInterval: 0.5)
}
print("missing")
