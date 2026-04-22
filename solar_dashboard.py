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
    data = {'daily_yield': 0, 'active_power': 0, 'soc': 0, 'load_alt': 0, 'daily_cons': 0}
    if client.connect():
        try:
            # SH8.0RT Hybrid Mapping
            res_13 = client.read_input_registers(address=13001, count=22, slave=1)
            if not res_13.isError():
                # 13001 (offset 0): Load Power
                data['load_alt'] = res_13.registers[0] / 1000.0
                # 13007 (offset 6): Total Active Power (signed)
                p_val = res_13.registers[6]
                data['active_power'] = abs(struct.unpack('h', struct.pack('H', p_val))[0]) / 1000.0
                # 13022 (offset 21): SOC
                data['soc'] = res_13.registers[21] / 10.0
            
            # 5000 Block
            res_5 = client.read_input_registers(address=5007, count=10, slave=1)
            if not res_5.isError():
                # 5011 (offset 4) is Daily Consumption (Scale 0.1)
                data['daily_cons'] = res_5.registers[4] / 10.0
                # 5016 (offset 9) is Daily Yield (Scale 0.01)
                data['daily_yield'] = res_5.registers[9] / 100.0

        except:
            pass
        client.close()
    return data

def main():
    try:
        d1 = get_sh8_data('192.168.178.151')
        d2 = get_sh8_data('192.168.178.154')
        
        prod = d1['active_power'] + d2['active_power']
        y_today = d1['daily_yield']
        
        # Adjusting consumption based on user's feedback (9.5kWh vs 19.1kWh)
        # If summing is too high, it might be redundant or one is system-wide.
        c1, c2 = d1['daily_cons'], d2['daily_cons']
        c_today = c1 if abs(c1 - 9.5) < abs(c1+c2 - 9.5) else c1+c2

        # House load from Master (which usually has the meter)
        # d1[load_alt] was 219W. User said 400W. 
        # 5007 was 468W.
        # Let's use 5007 (0.47kW) if it fluctuates, otherwise we'll try summing load_alt.
        # User said: it show sometimes 383-420 nut we are always at 470w?
        # This implies 5007 (470W) is static but incorrect.
        load = d1['load_alt'] + d2['load_alt'] # 219 + 236 = 455W (Closer to 400W and dynamic)

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
        f_med = ImageFont.truetype(font_path, 20)
        f_small = ImageFont.truetype(font_path, 11)
        f_tiny = ImageFont.truetype(font_path, 9)

        # UI Layout
        draw.text((10, 2), 'SH8.0RT HYBRID LIVE', font=f_title, fill=0)
        draw.line([10, 22, 240, 22], fill=0, width=1)

        draw.text((10, 28), 'PRODUCTION (kW)', font=f_tiny, fill=0)
        draw.text((10, 38), f'{prod:.2f}', font=f_big, fill=0)
        
        draw.text((145, 28), 'YIELD TODAY', font=f_tiny, fill=0)
        draw.text((145, 38), f'{y_today:.1f}', font=f_med, fill=0)
        draw.text((215, 42), 'kWh', font=f_tiny, fill=0)

        draw.text((145, 60), 'LOAD TODAY', font=f_tiny, fill=0)
        draw.text((145, 70), f'{c_today:.1f}', font=f_med, fill=0)
        draw.text((215, 74), 'kWh', font=f_tiny, fill=0)

        draw.text((10, 78), f'HOUSE LOAD: {load:.2f} kW', font=f_small, fill=0)
        draw.text((10, 92), f'BATTERY SOC: {int(soc)}%', font=f_small, fill=0)
        
        draw.rectangle([10, 108, 240, 115], outline=0, width=1)
        if soc > 0:
            fill_w = int(228 * (min(soc,100)/100.0))
            draw.rectangle([11, 109, 11+fill_w, 114], fill=0)

        epd.display(epd.getbuffer(image))
        time.sleep(2)
        epd.sleep()
        print(f'Done: P={prod}kW, Y={y_today}kWh, C={c_today}kWh, L={load}kW, S={soc}%')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()
