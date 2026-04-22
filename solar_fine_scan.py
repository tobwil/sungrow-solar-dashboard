from pymodbus.client import ModbusTcpClient
import struct

def scan(ip):
    client = ModbusTcpClient(ip, port=502)
    if client.connect():
        print(f'\n--- Fine Scanning {ip} ---')
        # We are looking for:
        # Production: ~9200 (W) or ~920 (0.01kW)
        # Yield: 414 (0.1kWh)
        # Consumption: 95 (0.1kWh)
        
        for base in [5000, 13000]:
            res = client.read_input_registers(address=base, count=100, slave=1)
            if not res.isError():
                for i, val in enumerate(res.registers):
                    # Check common scales
                    if val in [95, 414, 920, 9200]:
                        print(f'MATCH at Reg {base+i}: {val}')
                    
                    # Also check for 9.2kW represented as something else
                    if 9100 < val < 9300:
                        print(f'POTENTIAL PRODUCTION at Reg {base+i}: {val}')
                    if 410 < val < 420:
                        print(f'POTENTIAL YIELD at Reg {base+i}: {val}')
                    if 90 < val < 100:
                        print(f'POTENTIAL CONSUMPTION at Reg {base+i}: {val}')
        client.close()

scan('192.168.178.151')
