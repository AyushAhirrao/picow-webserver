import network
import socket
import time
import ujson
from machine import Pin

# initialise general purpose OUTPUT pins array
OUTPUT_PINS = []
OUTPUT_PINS_COUNT = 11
for i in range(OUTPUT_PINS_COUNT):
    pin = Pin(i, Pin.OUT)
    OUTPUT_PINS.append(pin)

# setting up wifi connection 
SSID = "YOUR SSID"
PASSWORD = "YOUR PASSWORD"
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

    
status = False
# Listen for connections
while True:
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
                    pin_no = int(query_params.get('pin_no')) if int(query_params.get('pin_no')) < OUTPUT_PINS_COUNT else 0
                except ValueError:
                    pin_no = 0
                    
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
