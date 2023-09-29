import network
import socket
import time
import ujson
import _thread
import gc
import micropython
from machine import Pin, reset, I2C

from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

# import settings
from settings import settings
config = settings("settings.json")

# initialise general purpose OUTPUT pins array
OUTPUT_PINS = []
OUTPUT_PINS_RANGE = [2,3,4,5,6,7,8,9,10,11]
OUTPUT_PIN_INDEX = 0
for i in OUTPUT_PINS_RANGE:
    pin = Pin(i, Pin.OUT)
    pin.value(settings("settings.json")[f"GPO{OUTPUT_PIN_INDEX}"]["status"])
    OUTPUT_PINS.append(pin)
    OUTPUT_PIN_INDEX += 1

# initialise general purpose INPUT pins array
INPUT_PINS = []
INPUT_PINS_RANGE = [16, 17, 18, 19, 22, 26, 27, 28, 1, 0]
for i in INPUT_PINS_RANGE:
    pin = Pin(i, Pin.IN, Pin.PULL_UP)
    INPUT_PINS.append(pin)
    pin.value(0)

# initialise general purpose INPUT pins array
INDICATOR_PINS = []
INDICATOR_PINS_RANGE = [12,13,14,15]
for i in INDICATOR_PINS_RANGE:
    pin = Pin(i, Pin.OUT)
    INDICATOR_PINS.append(pin)
    pin.value(0)


# Test LED pins
BLINK_LED = INDICATOR_PINS[0]
NETWORK_ERROR_LED = INDICATOR_PINS[1]

# lcd handler
I2C_ADDR     = 0x27
I2C_NUM_ROWS = 4
I2C_NUM_COLS = 20
i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=400000)
LCD = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
def lcd(string, cursor, clear=False):
    if clear:
        LCD.clear()
#     LCD.display()

    LCD.move_to(cursor[0], cursor[1])
    LCD.putstr(string)

def start_pattern():
    welcome_msg = "Welcome!!!"
    lcd(welcome_msg, (3,0), clear=True)
    p1 = INDICATOR_PINS[0]
    p2 = INDICATOR_PINS[1]
    p3 = INDICATOR_PINS[2]
    p4 = INDICATOR_PINS[3]
    
    p1.value(1)
    time.sleep(0.1)
    p2.value(1)
    time.sleep(0.1)
    p3.value(1)
    time.sleep(0.1)
    p4.value(1)
    time.sleep(0.3)
       
    p1.value(0)
    time.sleep(0.1)
    p2.value(0)
    time.sleep(0.1)
    p3.value(0)
    time.sleep(0.1)
    p4.value(0)
    time.sleep(0.3)
    
    p1.value(1)
    time.sleep(0.1)
    p2.value(1)
    time.sleep(0.1)
    p3.value(1)
    time.sleep(0.1)
    p4.value(1)
    time.sleep(0.3)
       
    p1.value(0)
    time.sleep(0.1)
    p2.value(0)
    time.sleep(0.1)
    p3.value(0)
    time.sleep(0.1)
    p4.value(0)
    time.sleep(0.3)
    
    p4.value(0)
    p1.value(0)
    p2.value(0)
    p3.value(0)
    p4.value(0)
    time.sleep(0.3)
    
    p1.value(1)
    p2.value(1)
    p3.value(1)
    p4.value(1)
    time.sleep(0.3)
     
    p1.value(0)
    p2.value(0)
    p3.value(0)
    p4.value(0)
    time.sleep(0.3)
    
    p1.value(1)
    p2.value(1)
    p3.value(1)
    p4.value(1)
    time.sleep(0.3)
    
    p1.value(0)
    p2.value(0)
    p3.value(0)
    p4.value(0)
    time.sleep(0.3)
    
    p1.value(1)
    p2.value(1)
    p3.value(1)
    p4.value(1)
    time.sleep(0.3)
    
    p1.value(0)
    time.sleep(0.1)
    p2.value(0)
    time.sleep(0.1)
    p3.value(0)
    time.sleep(0.1)
    p4.value(0)

start_pattern()

# setting up wifi connection 
SSID = config["SSID"]
PASSWORD = config["PASSWORD"]
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

# establish server
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

if wlan.status() != 3:
    NETWORK_ERROR_LED.value(1)
    network_msg = "Error: Unable to\       connect."
    lcd(network_msg, (0,0), clear=True)
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)
print('listening on', addr)

ip_status = f"IP-{status[0]}"
port = f"Port - 80"
lcd(ip_status, (0,0), clear=True)
lcd(port, (0,1), clear=False)

# set cors headers 
def send_response_with_cors(cl, response_data):
    response_json = ujson.dumps(response_data)
    cl.send('HTTP/1.0 200 OK\r\nContent-type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n')
    cl.send(response_json)
    cl.close()
    

# separate thread other IO operations
def separate_thread():
    global status
    last_toggle_time = time.ticks_ms()
    led_state = False
    reset_pin = Pin(14, Pin.IN)
    try:
        while True:
            BLINK_LED.value(1)

#             print("hello - ", reset_pin.value())
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_toggle_time) >= 3000:  # Toggle every 500ms
                last_toggle_time = current_time
                # Trigger garbage collection
                gc.collect()
                
                # Print memory information
                micropython.mem_info()
                
            if reset_pin.value() == 1:
                time.sleep(1)
                print("reboot")
                
            # Sensor control (GPIO0 and GPIO1)
            if settings("settings.json")["GPO0"]["control"]=="sensor":
                if INPUT_PINS[0].value()==0: 
                    OUTPUT_PINS[0].value(1)
                    print("sensor control enabled for GPIO0")
                    print("moving")

                else:
    #                 print("sensor0 off")
                    OUTPUT_PINS[0].value(0)

            if settings("settings.json")["GPO1"]["control"]=="sensor":
                if INPUT_PINS[1].value()==0: 
                    OUTPUT_PINS[1].value(1)
                    print("sensor control enabled for GPIO1")

                else:
    #                 print("sensor1 off")
                    OUTPUT_PINS[1].value(0)
        
        
        

            time.sleep(0.5)
    except Exception as e:
        print("Thread Exception:", e)
    finally:
        print("Thread exited")
    


_thread.start_new_thread(separate_thread, ())


# Listen for connections
while True:
    # request status
    status = False
    
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        request_data = cl.recv(1024)
        print(request_data)

        request_lines = request_data.split(b'\r\n')
        first_line = request_lines[0].decode('utf-8')

        parts = first_line.split(' ')


        if len(parts) >= 2 and parts[0] == 'GET':
            url = parts[1]
            print("URL:", url)

            if url.startswith('/out_stat'):
                                # initialise general purpose OUTPUT pins array
                OUTPUT_PINS_STAT = []
                for i in OUTPUT_PINS:
                    pin_stat = i.value()
                    OUTPUT_PINS_STAT.append(pin_stat)

                res_data = {'status': OUTPUT_PINS_STAT}
                send_response_with_cors(cl, res_data)
                    
            elif url.startswith('/gpio'):
                query_params = {}
                query_string = url.split('?')[1]
                query_params_list = query_string.split('&')
                for param in query_params_list:
                    key, value = param.split('=')
                    query_params[key] = value

                try:
                    pin_no = int(query_params.get('pin_no')) if int(query_params.get('pin_no')) < len(OUTPUT_PINS_RANGE) else -1
                except ValueError:
                    pin_no = -1
                    status = False
                    
                pin_status = query_params.get('pin_status', '')
                
                print("Pin Number:", pin_no)
                print("Pin Status:", pin_status)

                # enable sensors control for sensor operable pins (can be controlled with pin 11)
                if query_params.get('pin_no') == "11":
                     if settings("settings.json", {f"GPO0" : {"status" : 0, "control" : "sensor"}}):
                        print(settings("settings.json")["GPO0"]["control"])
                     
                     if settings("settings.json", {f"GPO1" : {"status" : 0, "control" : "sensor"}}):
                        print(settings("settings.json")["GPO1"]["control"])           

                # handle general purpose output pins status (on/off) 
                if pin_no != -1 and pin_status in ["on", "off"]:
            
                    # switch to pin control is (disable sensor control for sensor operable pins)
                    if pin_no == 0 or pin_no == 1:
                        if settings("settings.json", {f"GPO{pin_no}" : {"status" : (1 if pin_status == "on" else 0), "control" : "button"}}):
                            print(settings("settings.json")[f"GPO{pin_no}"]["control"])
                    

                    pin_status_value = 1 if pin_status == "on" else 0
                    OUTPUT_PINS[pin_no].value(pin_status_value)
                                    
                    # update gpo stat in file
                    settings("settings.json", {f"GPO{pin_no}": {"status" : (1 if pin_status == "on" else 0), "control" : "button" }})
                    
                    status = True
                    
                    response_data = {'status': status}
                    send_response_with_cors(cl, response_data)
                    
                else:
                    print("Invalid pin number or status")
            
            else:
                print("Invalid URL format")
        else:
            print("Invalid request format")


    except OSError as e:
        cl.close()
        print('connection closed')






