from pymodbus.client import ModbusTcpClient
import struct

def scan(ip):
    client = ModbusTcpClient(ip, port=502)
    if client.connect():
        print(f'\n--- Scanning {ip} ---')
        # Scan 5000 range
        res = client.read_input_registers(address=5000, count=50, slave=1)
        if not res.isError():
            for i, val in enumerate(res.registers):
                # Check for ~9500 (Production) or ~400 (House)
                if val > 100:
                    print(f'Reg {5000+i}: {val}')
        
        # Scan 13000 range
        res = client.read_input_registers(address=13000, count=40, slave=1)
        if not res.isError():
            for i, val in enumerate(res.registers):
                s_val = struct.unpack('h', struct.pack('H', val))[0]
                if abs(s_val) > 100:
                    print(f'Reg {13000+i}: {val} (signed: {s_val})')
        client.close()

scan('192.168.178.151')
scan('192.168.178.154')
