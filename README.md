# Sungrow SH8.0RT Solar Dashboard for Raspberry Pi

A real-time solar monitoring dashboard for Raspberry Pi (Zero 2 W) using a Waveshare 2.13" e-Paper display (V4). This project connects to two Sungrow SH8.0RT Hybrid inverters via Modbus TCP to display production, yield, consumption, and battery status.

## Hardware
- **Inverters:** 2x Sungrow SH8.0RT (Master/Slave configuration)
- **Controller:** Raspberry Pi Zero 2 W
- **Display:** Waveshare 2.13" e-Paper V4 (250x122 resolution)

## Modbus Register Mapping
Based on field testing with SH8.0RT Hybrid models:

| Data Point | Register | Unit | Scaling | Type |
|------------|----------|------|---------|------|
| Total Active Power | 13007 | W | 1 | Signed 16-bit |
| Daily PV Yield | 5016 | kWh | 0.01 | Unsigned 16-bit |
| Daily Consumption | 5011 | kWh | 0.1 | Unsigned 16-bit |
| House Load | 5007 | W | 1 | Unsigned 16-bit |
| Battery SOC | 13022 | % | 0.1 | Unsigned 16-bit |

### Key Logic:
- **PV Production:** Calculated as the sum of Total Active Power (Register 13007) from both inverters.
- **System Stats:** Yield, Consumption, and House Load are read from the Master inverter (192.168.178.151).
- **Battery SOC:** Read from the master inverter (which manages the battery).

## Prerequisites
- Python 3.x
- `pymodbus` library (`sudo apt install python3-pymodbus`)
- `Pillow` library (`sudo apt install python3-pil`)
- Waveshare e-Paper library

## Files
- `solar_dashboard.py`: Main script to fetch data and update the display.
- `solar_scan.py`: Utility script to scan Modbus register ranges.
- `solar_fine_scan.py`: Utility script for targeted value matching.

## How to Run
```bash
python3 solar_dashboard.py
```

## Automation (Cron Job)
To update the display every 5 minutes:
```bash
crontab -e
# Add the following line:
* * * * * /usr/bin/python3 /home/zero/solar_dashboard.py
```
