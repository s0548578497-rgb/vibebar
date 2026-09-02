using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Threading;

internal static class ClassicRssiReader
{
    const uint MonitorRssi = 0x004111C0, WmDeviceChange = 0x0219, WmClose = 0x0010;
    const int DeviceHandle = 6, CustomEvent = 0x8006;
    static readonly Guid RssiEvent = new Guid("72383a4f-a65b-428a-8a23-2dacb521c2ba");
    static IntPtr radio, radioSearch, notification, window;
    static ulong target;
    static WndProc callback;

    public static int Main(string[] args)
    {
        if (args.Length < 1) { Console.Error.WriteLine("usage: ClassicRssiReader DEVICE [INTERVAL_MS]"); return 2; }
        int interval = args.Length > 1 ? int.Parse(args[1]) : 500;
        bool absolute = args.Length < 3 || args[2] != "relative";
        try { Run(args[0], interval, absolute); return 0; }
        catch (Exception error) { Console.Error.WriteLine(error.Message); Cleanup(); return 1; }
    }

    static void Run(string name, int interval, bool absolute)
    {
        OpenTarget(name);
        CreateMessageWindow();
        RegisterNotification();
        Console.CancelKeyPress += delegate(object sender, ConsoleCancelEventArgs eventArgs) {
            eventArgs.Cancel = true; PostMessage(window, WmClose, IntPtr.Zero, IntPtr.Zero);
        };
        byte[] request = BuildRequest(target, interval, absolute);
        new Thread(delegate() { Monitor(request); }) { IsBackground = true }.Start();
        Message message;
        while (GetMessage(out message, IntPtr.Zero, 0, 0) > 0) DispatchMessage(ref message);
        Cleanup();
    }

    static void OpenTarget(string wanted)
    {
        FindRadioParams parameters = new FindRadioParams();
        parameters.Size = (uint)Marshal.SizeOf(parameters);
        radioSearch = BluetoothFindFirstRadio(ref parameters, out radio);
        if (radioSearch == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(), "Bluetooth radio not found");
        DeviceSearch search = new DeviceSearch();
        search.Size = (uint)Marshal.SizeOf(search); search.Connected = true; search.Radio = radio;
        DeviceInfo info = new DeviceInfo(); info.Size = (uint)Marshal.SizeOf(info);
        IntPtr finder = BluetoothFindFirstDevice(ref search, ref info);
        if (finder != IntPtr.Zero) {
            try {
                do {
                    if (info.IsConnected && info.Name.IndexOf(wanted, StringComparison.OrdinalIgnoreCase) >= 0) {
                        target = info.Address; return;
                    }
                    info.Size = (uint)Marshal.SizeOf(info);
                } while (BluetoothFindNextDevice(finder, ref info));
            } finally { BluetoothFindDeviceClose(finder); }
        }
        throw new InvalidOperationException("Connected Bluetooth device not found: " + wanted);
    }

    static void CreateMessageWindow()
    {
        callback = WindowProcedure;
        string name = "ProximityRssi_" + Guid.NewGuid().ToString("N");
        WindowClass value = new WindowClass();
        value.Size = (uint)Marshal.SizeOf(value); value.Callback = callback;
        value.Instance = GetModuleHandle(null); value.ClassName = name;
        if (RegisterClassEx(ref value) == 0) throw new Win32Exception(Marshal.GetLastWin32Error());
        window = CreateWindowEx(0, name, name, 0, 0, 0, 0, 0, IntPtr.Zero, IntPtr.Zero, value.Instance, IntPtr.Zero);
        if (window == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
    }

    static void RegisterNotification()
    {
        BroadcastFilter filter = new BroadcastFilter();
        filter.Size = (uint)Marshal.SizeOf(filter); filter.DeviceType = DeviceHandle; filter.Handle = radio;
        notification = RegisterDeviceNotification(window, ref filter, 0);
        if (notification == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
    }

    static void Monitor(byte[] request)
    {
        uint returned;
        bool ok = DeviceIoControl(radio, MonitorRssi, request, (uint)request.Length, null, 0, out returned, IntPtr.Zero);
        if (!ok && Marshal.GetLastWin32Error() != 995) Console.Error.WriteLine("RSSI monitor error " + Marshal.GetLastWin32Error());
        PostMessage(window, WmClose, IntPtr.Zero, IntPtr.Zero);
    }

    static IntPtr WindowProcedure(IntPtr handle, uint message, IntPtr wparam, IntPtr lparam)
    {
        if (message == WmDeviceChange && wparam.ToInt32() == CustomEvent) ReadEvent(lparam);
        if (message == WmClose) { DestroyWindow(handle); return IntPtr.Zero; }
        return DefWindowProc(handle, message, wparam, lparam);
    }

    static void ReadEvent(IntPtr pointer)
    {
        int size = Marshal.ReadInt32(pointer, 0), type = Marshal.ReadInt32(pointer, 4);
        int guidOffset = IntPtr.Size == 8 ? 32 : 20, dataOffset = IntPtr.Size == 8 ? 52 : 40;
        if (pointer == IntPtr.Zero || type != DeviceHandle || size < dataOffset + 15) return;
        if ((Guid)Marshal.PtrToStructure(IntPtr.Add(pointer, guidOffset), typeof(Guid)) != RssiEvent) return;
        byte[] data = new byte[size - dataOffset]; Marshal.Copy(IntPtr.Add(pointer, dataOffset), data, 0, data.Length);
        if (BitConverter.ToUInt64(data, 0) != target) return;
        if (data[14] == 0) { Console.WriteLine("missing"); Console.Out.Flush(); return; }
        int raw = unchecked((sbyte)data[12]);
        int rssi = data[13] != 0 && raw > 0 ? -raw : raw;
        Console.WriteLine(rssi); Console.Out.Flush();
    }

    static byte[] BuildRequest(ulong address, int interval, bool absolute)
    {
        int period = interval / 100;
        if (period < 1 || period > 254) throw new ArgumentOutOfRangeException("interval");
        byte[] data = new byte[20];
        Array.Copy(BitConverter.GetBytes(address), 0, data, 0, 8);
        Array.Copy(BitConverter.GetBytes((uint)0x4000), 0, data, 8, 4);
        data[12] = unchecked((byte)(sbyte)-100); data[13] = unchecked((byte)(sbyte)-127);
        data[14] = 1; data[15] = (byte)period; data[16] = absolute ? (byte)1 : (byte)0;
        return data;
    }

    static void Cleanup()
    {
        if (notification != IntPtr.Zero) UnregisterDeviceNotification(notification);
        if (radio != IntPtr.Zero) { CancelIoEx(radio, IntPtr.Zero); CloseHandle(radio); }
        if (radioSearch != IntPtr.Zero) BluetoothFindRadioClose(radioSearch);
        notification = radio = radioSearch = IntPtr.Zero;
    }

    delegate IntPtr WndProc(IntPtr window, uint message, IntPtr wparam, IntPtr lparam);
    [StructLayout(LayoutKind.Sequential)] struct FindRadioParams { public uint Size; }
    [StructLayout(LayoutKind.Sequential)] struct SystemTime { public ushort Y, M, W, D, H, N, S, Ms; }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct DeviceInfo {
        public uint Size; public ulong Address; public uint Class;
        [MarshalAs(UnmanagedType.Bool)] public bool IsConnected, Remembered, Authenticated;
        public SystemTime Seen, Used; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=248)] public string Name;
    }
    [StructLayout(LayoutKind.Sequential)] struct DeviceSearch {
        public uint Size; [MarshalAs(UnmanagedType.Bool)] public bool Authenticated, Remembered, Unknown, Connected, Inquiry;
        public byte Timeout; public IntPtr Radio;
    }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct WindowClass {
        public uint Size, Style; public WndProc Callback; public int ClassExtra, WindowExtra;
        public IntPtr Instance, Icon, Cursor, Background; public string MenuName, ClassName; public IntPtr SmallIcon;
    }
    [StructLayout(LayoutKind.Sequential)] struct Message {
        public IntPtr Window; public uint Id; public IntPtr WParam, LParam; public uint Time; public int X, Y; public uint Private;
    }
    [StructLayout(LayoutKind.Sequential)] struct BroadcastFilter {
        public uint Size, DeviceType, Reserved; public IntPtr Handle, Notify; public Guid EventGuid; public int NameOffset; public byte Data;
    }

    [DllImport("BluetoothApis.dll", SetLastError=true)] static extern IntPtr BluetoothFindFirstRadio(ref FindRadioParams p, out IntPtr r);
    [DllImport("BluetoothApis.dll")] static extern bool BluetoothFindRadioClose(IntPtr h);
    [DllImport("BluetoothApis.dll", SetLastError=true)] static extern IntPtr BluetoothFindFirstDevice(ref DeviceSearch s, ref DeviceInfo i);
    [DllImport("BluetoothApis.dll")] static extern bool BluetoothFindNextDevice(IntPtr h, ref DeviceInfo i);
    [DllImport("BluetoothApis.dll")] static extern bool BluetoothFindDeviceClose(IntPtr h);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll")] static extern bool CancelIoEx(IntPtr h, IntPtr o);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool DeviceIoControl(IntPtr h, uint c, byte[] i, uint n, byte[] o, uint z, out uint r, IntPtr v);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern IntPtr GetModuleHandle(string n);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern ushort RegisterClassEx(ref WindowClass c);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr CreateWindowEx(uint e,string c,string n,uint s,int x,int y,int w,int h,IntPtr p,IntPtr m,IntPtr i,IntPtr v);
    [DllImport("user32.dll")] static extern IntPtr DefWindowProc(IntPtr h,uint m,IntPtr w,IntPtr l);
    [DllImport("user32.dll")] static extern bool DestroyWindow(IntPtr h);
    [DllImport("user32.dll")] static extern int GetMessage(out Message m,IntPtr h,uint a,uint b);
    [DllImport("user32.dll")] static extern IntPtr DispatchMessage(ref Message m);
    [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
    [DllImport("user32.dll", SetLastError=true)] static extern IntPtr RegisterDeviceNotification(IntPtr h,ref BroadcastFilter f,uint v);
    [DllImport("user32.dll")] static extern bool UnregisterDeviceNotification(IntPtr h);
}
