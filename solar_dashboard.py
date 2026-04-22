import sys
import os
import time
import struct
from PIL import Image, ImageDraw, ImageFont
from pymodbus.client import ModbusTcpClient

# Display setup
libdir = '/home/zero/e-Paper/RaspberryPi_JetsonNano/python/lib'
picdir = '/home/zero/e-Paper/RaspberryPi_JetsonNano/python/pic'
if os.path.exists(libdir):
    sys.path.append(libdir)
from waveshare_epd import epd2in13_V4

def get_sh8_data(ip):
    client = ModbusTcpClient(ip, port=502)
    data = {'daily_yield': 0, 'active_pwr': 0, 'soc': 0, 'load_now': 0, 'grid_pwr': 0, 'batt_pwr': 0}
    if client.connect():
        try:
            # SH8.0RT Hybrid Mapping (Registers 13001-13022)
            res_13 = client.read_input_registers(address=13001, count=22, slave=1)
            if not res_13.isError():
                # 13001 (offset 0): Load Power (W)
                data['load_now'] = res_13.registers[0] / 1000.0
                
                # 13007 (offset 6): Total Active Power (W, signed: Negative=Production, Positive=Charging/Load)
                p_val = struct.unpack('h', struct.pack('H', res_13.registers[6]))[0]
                data['active_pwr'] = p_val / 1000.0
                
                # 13009 (offset 8): Grid Power (W, signed: Positive=Export, Negative=Import?)
                g_val = struct.unpack('h', struct.pack('H', res_13.registers[8]))[0]
                data['grid_pwr'] = g_val / 1000.0
                
                # 13021 (offset 20): Battery Power (W, signed: Positive=Discharge, Negative=Charge)
                b_val = struct.unpack('h', struct.pack('H', res_13.registers[20]))[0]
                data['batt_pwr'] = b_val / 1000.0

                # 13022 (offset 21): SOC (%)
                data['soc'] = res_13.registers[21] / 10.0
            
            # 5016 Block (Yield)
            res_5 = client.read_input_registers(address=5016, count=1, slave=1)
            if not res_5.isError():
                data['daily_yield'] = res_5.registers[0] / 100.0

        except:
            pass
        client.close()
    return data

def main():
    try:
        d1 = get_sh8_data('192.168.178.151') # Master
        d2 = get_sh8_data('192.168.178.154') # Slave
        
        # Production on SH8 is usually the sum of active powers (which are negative when producing)
        # Prod = |ActivePwr1| + |ActivePwr2|
        prod = abs(d1['active_pwr']) + abs(d2['active_pwr'])
        
        load = d1['load_now'] + d2['load_now']
        grid = d1['grid_pwr'] 
        batt = d1['batt_pwr'] + d2['batt_pwr']
        
        y_today = d1['daily_yield']
        soc = max(d1['soc'], d2['soc'])

        # UI Update
        epd = epd2in13_V4.EPD()
        epd.init()
        H, W = epd.height, epd.width
        image = Image.new('1', (H, W), 255)
        draw = ImageDraw.Draw(image)

        font_path = os.path.join(picdir, 'Font.ttc')
        if not os.path.exists(font_path):
            font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        
        f_title = ImageFont.truetype(font_path, 16)
        f_big = ImageFont.truetype(font_path, 32)
        f_med = ImageFont.truetype(font_path, 18)
        f_small = ImageFont.truetype(font_path, 11)
        f_tiny = ImageFont.truetype(font_path, 9)

        # UI Layout
        draw.text((10, 2), 'SH8.0RT ENERGY BALANCE', font=f_title, fill=0)
        draw.line([10, 22, 240, 22], fill=0, width=1)

        # PV Production
        draw.text((10, 28), 'PV PRODUCTION (kW)', font=f_tiny, fill=0)
        draw.text((10, 38), f'{prod:.2f}', font=f_big, fill=0)
        
        # Right Column
        draw.text((150, 28), 'YIELD TODAY', font=f_tiny, fill=0)
        draw.text((150, 38), f'{y_today:.1f}', font=f_med, fill=0)
        draw.text((215, 42), 'kWh', font=f_tiny, fill=0)

        grid_label = 'EXPORT' if grid > 0 else 'IMPORT'
        draw.text((150, 60), f'GRID {grid_label}', font=f_tiny, fill=0)
        draw.text((150, 70), f'{abs(grid):.2f}', font=f_med, fill=0)
        draw.text((215, 74), 'kW', font=f_tiny, fill=0)

        # Bottom Info - Multi-line to prevent overlap
        draw.text((10, 78), f'HOUSE: {load:.2f}kW', font=f_small, fill=0)
        
        batt_label = 'CHARGING' if batt < 0 else 'DISCHARGING' if batt > 0 else 'IDLE'
        draw.text((10, 92), f'BATT: {batt_label} ({int(soc)}% | {abs(batt):.2f} kW)', font=f_small, fill=0)
        
        # Battery Bar
        draw.rectangle([10, 108, 240, 115], outline=0, width=1)
        if soc > 0:
            fill_w = int(228 * (min(soc,100)/100.0))
            draw.rectangle([11, 109, 11+fill_w, 114], fill=0)

        epd.display(epd.getbuffer(image))
        time.sleep(2)
        epd.sleep()
        print(f'Sync Done: P={prod}kW, Y={y_today}kWh, G={grid}kW, L={load}kW, S={soc}%')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()
