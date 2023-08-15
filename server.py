import network
import socket
import time
import ujson
import _thread
from machine import Pin

# import settings
from settings import settings
config = settings("settings.json")

# initialise general purpose OUTPUT pins array
OUTPUT_PINS = []
OUTPUT_PINS_RANGE = range(0, 11)
for i in OUTPUT_PINS_RANGE:
    pin = Pin(i, Pin.OUT)
    OUTPUT_PINS.append(pin)

# initialise general purpose INPUT pins array
INPUT_PINS = []
INPUT_PINS_RANGE = range(16, 22)
for i in INPUT_PINS_RANGE:
    pin = Pin(i, Pin.IN)
    INPUT_PINS.append(pin)

# Test LED pins
NETWORK_ERROR_LED = Pin(11, Pin.OUT)
BLINK_LED = Pin(15, Pin.OUT)


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

# set cors headers 
def send_response_with_cors(cl, response_data):
    response_json = ujson.dumps(response_data)
    cl.send('HTTP/1.0 200 OK\r\nContent-type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n')
    cl.send(response_json)
    cl.close()
    

# separate thread other IO operations
def separate_thread():
    last_toggle_time = time.ticks_ms()
    led_state = False
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_toggle_time) >= 500:  # Toggle every 500ms
            last_toggle_time = current_time
            led_state = not led_state
            BLINK_LED.value(led_state)
            
#         if blink12.value() == 1:
#             OUTPUT_PINS[1].value(1)
#         else:
#             OUTPUT_PINS[1].value(0)
        
        time.sleep(0.5)            

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

            if url.startswith('/gpio'):
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

                # handle general purpose output pins status (on/off) 
                if pin_no != -1 and pin_status in ["on", "off"]:
                    pin_status_value = 1 if pin_status == "on" else 0
                    OUTPUT_PINS[pin_no].value(pin_status_value)
                    status = True
                    
                else:
                    print("Invalid pin number or status")
            else:
                print("Invalid URL format")
        else:
            print("Invalid request format")

        response_data = {'status': status}
        send_response_with_cors(cl, response_data)

    except OSError as e:
        cl.close()
        print('connection closed')

