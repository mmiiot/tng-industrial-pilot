# Wiring for Raspberry Pi 3B+ and NeoPixelRing12
# PWR to 5V Pin
# GND to GND Pin
# IN to GPIO21
# sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
# sudo python3 neopixeltest1.py
import time
def setuppi3rgbled(pi3IsEnabled_ini):
    global pixels, brightled
    try:
        import board
        import neopixel
        # The number of NeoPixels
        pi_num_pixels = 12
        # Raspberry Pi's GPIO Pin for NeoPixels
        pi_pixels_gpio = board.D21
        pixels = neopixel.NeoPixel(pi_pixels_gpio, pi_num_pixels)
        # Define brightness (1,2,..,10)
        brightled = 1
        if (brightled<0):
            brightled = 0
        if (brightled>10):
            brightled = 10
        return 0
    except:
        return -1

def statusled(status):
    # setup
    if status == '0U000':
        setupled(0)
        #print("LED: " + str(status))
    # run
    if status == '0A000':
        runled(0)
        #print("LED: " + str(status))
    # error
    if status == '0C001':
        alarmled(1)
        #print("LED: " + str(status))
    # pause
    if status == '0H000':
        pauseled(0)
        #print("LED: " + str(status))
    # finished
    if status == '0C000':
        finishedled(1)
        #print("LED: " + str(status))
    if status == '0':
        offled()
        #print("LED: " + str(status) + " (reset)")
    #else:
    #    offled()
    #    print("LED: " + str(status) + " (else: reset)")
    return 0

def setupled(wait_periodtime):
    # LED ring lights like in pause for setup
    pauseled(wait_periodtime)
    return 0

def finishedled(wait_periodtime):
    # LED ring blinks blue for job completed
    global pixels, brightled
    pixels.fill((0, 0, 25*brightled))
    pixels.show()
    if(wait_periodtime>0):
        time.sleep(wait_periodtime/2)
    else:
        time.sleep(0.5)
    pixels.fill((0, 0, 0))
    pixels.show()
    if(wait_periodtime>0):
        time.sleep(wait_periodtime/2)
    else:
        time.sleep(0.5)
    return 0

def alarmled(wait_periodtime):
    # LED ring blinks red for alarm/error
    global pixels, brightled
    pixels.fill((25*brightled, 0, 0))
    pixels.show()
    if(wait_periodtime>0):
        time.sleep(wait_periodtime/2)
    else:
        time.sleep(0.5)
    pixels.fill((0, 0, 0))
    pixels.show()
    if(wait_periodtime>0):
        time.sleep(wait_periodtime/2)
    else:
        time.sleep(0.5)
    return 0

def runled(wait_periodtime):
    # LED ring lights green for run/production
    global pixels, brightled
    pixels.fill((0, 25*brightled, 0))
    pixels.show()
    if(wait_periodtime>0):
        time.sleep(wait_periodtime)
    return 0

def pauseled(wait_periodtime):
    # LED ring lights yellow for pause
    global pixels, brightled
    pixels.fill((25*brightled, 25*brightled, 0))
    pixels.show()
    if(wait_periodtime>0):
        time.sleep(wait_periodtime)
    return 0

def offled():
    # Sets LED ring off
    global pixels, brightled
    pixels.fill((0, 0, 0))
    pixels.show()
    return 0
