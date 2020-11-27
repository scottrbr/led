#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

#
# Some of the he neopixle library has these functions
# https://adafruit.github.io/Adafruit_NeoPixel/html/class_adafruit___neo_pixel.html
#
# begin()
# updateLength()
# updateType()
# show()
# delay_ns()
# setPin()
# setPixelColor()
# fill()
# ColorHSV()
# getPixelColor()
# setBrightness()
# getBrightness()
# clear()
# gamma32()


import sys
import random
import time
import socket       # For getting the computer name
import _thread
from rpi_ws281x import *
import paho.mqtt.client as mqtt  # Import the MQTT library


# LED strip configuration:
LED_COUNT      = 300      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

#
# Not all of my devices have the same number of LEDs and I want this code to
# run in all of them so I need to make this dynamic based on the name of the
# device.
#
def get_led_count():

    led_count = 100
    host_name = socket.gethostname()

    if host_name == "strip1":
        led_count = 300
    elif host_name == "raspberrypi4":
        led_count = 300
    elif host_name == candle1:
        led_count = 4

    return led_count


# Define functions which animate LEDs in various ways.
def glow(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""

    pixelcount = strip.numPixels();
    for bri in range(0,255):
        for i in range(strip.numPixels()):
            strip.setPixelColor(pixelcount-i, color)
            strip.setBrightness(bri)
        strip.show()
        time.sleep(0.01)


    for bri in range(255,0, -1):
        for i in range(strip.numPixels()):
            strip.setPixelColor(pixelcount-i, color)
            strip.setBrightness(bri)
        strip.show()
        time.sleep(0.01)


def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)

    strip.show()
#    time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

# Create a moving rainbow
def rainbow(strip, wait_ms=50, iterations=10):

    global gblBreak

    strip.setBrightness(30)
 
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))

            # Exit if we are being asked to
            if gblBreak:
                gblBreak = False
                return

        strip.show()
        time.sleep(wait_ms/1000.0)


def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)


def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

#
# A Christmas color theme variation on the normal theatre chase routin.
#
def XMAS_theater_chase(strip, wait_ms=100):

    global gblBreak
    global gblExit

    strip.setBrightness(30)

    # Movie theater light style chaser animation
    while not gblBreak and not gblExit:
        for q in range(6):
            for i in range(0, strip.numPixels(), 6):
                strip.setPixelColor(i+q, Color(255, 0, 0))
                strip.setPixelColor(i+q+1, Color(255, 0, 0))
                strip.setPixelColor(i+q+2, Color(255, 0, 0))
                if gblBreak or gblExit:
                    break
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 6):
                strip.setPixelColor(i+q, Color(0, 255, 0))
                if gblBreak or gblExit:
                    break
 

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

#
# Sets the entire strip color and brightness based on a message this is
# color in hex (rgb), comma, brightness in decimal which looks like:
# ff34b0,98
#
def set_strip_color(strip, message):

    ledclr = hex_to_rgb(message[0:6])

    first_comma_loc = message.find(',')
    length = len(message)
    brightness = message[(first_comma_loc+1):(length)]

    for i in range(strip.numPixels()):
        #strip.setPixelColor(i, Color(ledclr[1], ledclr[0], ledclr[2]))
        strip.setPixelColor(i, Color(ledclr[0], ledclr[1], ledclr[2]))

    # *************** I am limiting the brighntess here ***************
    brightness_int = int(brightness)
    if brightness_int > 30:
        brightness_int = 30

    strip.setBrightness(brightness_int)
    strip.show()


def CylonBounce(strip, red, green, blue, EyeSize, SpeedDelay, ReturnDelay):

    pixel_count = strip.numPixels()

    for i in range(0, pixel_count-EyeSize-2):
        #strip.fill()         #setAll(0,0,0);
        colorWipe(strip, Color(0,0,0), 0)

        strip.setPixelColor(i, Color(int(green/10), int(red/10), int(blue/10)))
        for j in range(0, EyeSize):
            strip.setPixelColor(i+j, Color(green, red, blue))

        strip.setPixelColor(i+EyeSize, Color(int(green/10), int(red/10), int(blue/10)))
        strip.show()
        time.sleep(SpeedDelay/1000)

    time.sleep(ReturnDelay/1000)

    for i in range(pixel_count-EyeSize-2, 0, -1):

        colorWipe(strip, Color(0,0,0), 0)

        strip.setPixelColor(i, Color(int(green/10), int(red/10), int(blue/10)))
        for j in range(1, EyeSize):
            strip.setPixelColor(i+j, Color(green, red, blue))

        strip.setPixelColor(i+EyeSize, Color(int(green/10), int(red/10), int(blue/10)))
        strip.show()
        time.sleep(SpeedDelay/1000)

    time.sleep(ReturnDelay/1000)


#
# There is a known issue that when I get a new randome led, I do not check if it is a duplicate 
#
def Twinkle(strip, numOfLights, LEDMaxBright, Minutes, ColorTwinkle):

    global gblBreak

    # Initial the strip to turn off all lights but set the brightness to maximum
    set_strip_color(strip, "000000,40")
    start_time = time.time()

    #
    # Intialize all of our arrays
    # light - list all of the lights we are turning on and off
    # light_increment - an True/False for each light so we know if we are getting brighter or dimmer
    # light_curr_life - Life counter for each light so we know how it's age (number of loops it has gone through)
    #
    lights = random.sample(range(0, strip.numPixels()), numOfLights)   # Samples does not include duplicate values
    light_increment = [True] * numOfLights
    light_curr_life = [0] * numOfLights
    light_max_life = random.sample(range(10, 100), numOfLights)   # Life is in number of loops
    light_brightness = random.sample(range(1, LEDMaxBright), numOfLights)
    individual_light_color = [[random.random() for i in range(3)] for j in range(numOfLights)]

    #for loop in range(NumOfLoops):
    while (1):

        for i in range(numOfLights):

            # Exit if we are being asked to
            if gblBreak:
                gblBreak = False
                return

            if light_increment[i]:

                # "Age" the light -> each loop is an increase in age
                light_curr_life[i] += 1

                # If the light is over it's half life then we must be at maximum brightness
                # so change the direction to get dimmer.
                if light_curr_life[i] > (light_max_life[i]/2):
                    light_curr_life[i] = light_max_life[i]/2
                    light_increment[i] = False

            else:

                light_curr_life[i] -= 1

                # if the light life is over, reset it
                if light_curr_life[i] < 0:

                    # We need to do this just in case there were fractions in the "life" calculation
                    # that cause it to be left with a brightness of 1.
                    strip.setPixelColor(lights[i], Color(0, 0, 0))

                   # The light's life is over, generate a new one.
                    lights[i] = random.randint(0, strip.numPixels())
                    light_max_life[i] = random.randint(10, 100)
                    light_curr_life[i] = 0
                    light_increment[i] = True

            
            # Light level must be an integer
            light_level = int(light_brightness[i]/(light_max_life[i]/2) * light_curr_life[i])

            l1 = individual_light_color[i][0] 
            l2 = individual_light_color[i][1] 
            l3 = individual_light_color[i][2] 

            if ColorTwinkle:
                strip.setPixelColor(lights[i], Color(int(light_level*l1), int(light_level*l2), int(light_level*l3)))
            else:
                strip.setPixelColor(lights[i], Color(light_level, light_level, light_level))

            elapsed_time = time.time() - start_time
            if elapsed_time> (Minutes*60):
                return

        strip.show()


def red_white_blue(strip):

    global gblBreak


    level = 30

    Colors = []
    for i in range(100):
        Colors.append(Color(level,0,0))
    for i in range(100):
        Colors.append(Color(level,level,level))
    for i in range(100):
        Colors.append(Color(0,0,level))
    for i in range(100):
        Colors.append(Color(level,0,0))
    for i in range(100):
        Colors.append(Color(level,level,level))
    for i in range(100):
        Colors.append(Color(0,0,level))


    # Initial the strip to turn off all lights but set the brightness to maximum

    start = 0
    set_strip_color(strip, "000000,30")
 
    while (1):

        # Do red
        for i in range(strip.numPixels()):

            # Exit if we are being asked to
            if gblBreak:
                gblBreak = False
                return

            strip.setPixelColor(i, Colors[i+start])

        strip.show()
        time.sleep(0.01)
        start += 1
        if start == strip.numPixels():
            start = 0

 
def candle_start(strip, season_color):

    global gblBreak

    if int(season_color) == 1:
        XMAS_time = False
    else:
        XMAS_time = True
    while not gblBreak:
        wait = random.randint(100, 120)             # set a random wait period
        randpix = 4     # random(0, numpix + 1);    //choose a random number of pixels
        numpix = 4
        color = random.randint(0, 1)                # ; //Pick either yellow or orange
                                    # so it leaves a certain number of yellow pixels on (number of pixels/3)
        for i in range (int(numpix)):
            if not XMAS_time:
                strip.setPixelColor(i, Color(255, 120, 0))  # set the number of pixels to turn on and color value (yellowish)
            else:
                strip.setPixelColor(i, Color(255, 10, 0))  # set the number of pixels to turn on and color value (yellowish)

        strip.show();   # turn pixels on
        strip.setBrightness(random.randint(5, 40))

        if color == 0:      # if red was chosen
            if not XMAS_time:
                flickred(strip, Color(215, 50, 0), wait, randpix)   # call flickred and pass it the red (orangeish)
            else:
                flickred(strip, Color(255, 0, 0), wait, randpix)   # call flickred and pass it the red (orangeish)
                                                            # color values - change values to change color
        else:               # otherwise use yellow
            if not XMAS_time:
                flickYellow(strip, Color(180, 80, 0), wait, randpix)  # call flickYellow and pass it the yellow color
            else:
                flickYellow(strip, Color(18, 180, 0), wait, randpix)  # call flickYellow and pass it the yellow color
                                                              # values (change values to change color), and
                                                              # wait time and random pixel count

# Function for when red is chosen
def flickred(strip, c, wait, p):

    for i in range(p - 2):  # loop for given random pixel count (passed from loop)
        strip.setPixelColor(i, c)

    strip.show();  # turn pixels on

    time.sleep(wait/1000)

    for i in range(p):
        strip.setPixelColor(i, 0)        # turn pixel off



# function for when yellow is chosen
def flickYellow(strip, c, wait, p):

    for i in range(p):          # loop for given random pixel count (passed from loop)
        strip.setPixelColor(i, c)
                                                                                
    strip.show()    # turn pixels on

    time.sleep(wait/1000)

    for i in range(p):
        strip.setPixelColor(i, 0)       # turn pixel off


# Our "on message" event
#
# Be careful about using the strip variable here. It is a global variable
#
def LED_strip_CallBack(client, userdata, message):

    global gblBreak
    global gblExit

    topic = str(message.topic)
    host_name = socket.gethostname()

    message = str(message.payload.decode("utf-8"))
    print("Message: ", message)
    print("Topic: ", topic)

    # Stop any currently running routines
    gblBreak = True
    time.sleep(0.5)  # Wait 1/2 second for routines to stop
    gblBreak = False

    if host_name.find("strip") > -1 or host_name.find("raspberrypi4") > -1:    # LED strip specific instructions
        if topic == "on_" + host_name:
            set_strip_color(strip, message)
        elif topic == "rainbow_" + host_name:
            _thread.start_new_thread( rainbow, (strip, ) )
        elif topic == "theaterchase_" + host_name:
            theaterChase(strip, Color(127, 127, 127))
        elif topic == "cylon_" + host_name:
            CylonBounce(strip, 0, 255, 0, 4, 20, 500)
        elif topic == "twinkle_" + host_name:
            Minutes = int(message)
            _thread.start_new_thread( Twinkle, (strip, 10, 255, Minutes, False))
        elif topic == "ctwinkle_" + host_name:
            Minutes = int(message)
            _thread.start_new_thread( Twinkle, (strip, 25, 255, Minutes, True))
        elif topic == "rwb_" + host_name:
            _thread.start_new_thread( red_white_blue, (strip, ) )
        elif topic == "xmas_" + host_name:
            print("start xmas strip show")
            _thread.start_new_thread( XMAS_theater_chase, (strip, ) )
    else:   # Candle specific functions
        if topic == "on_" + host_name:
            print("Turn on: ", host_name)
            _thread.start_new_thread( candle_start, (strip, message) )

    if topic == "off_" + host_name:
        set_strip_color(strip, "000000,30")
        gblBreak = True
    elif topic == "exit_" + host_name:
         gblExit = True
         print("Exit command for " + host_name + " program")
    elif topic == "break_" + host_name:
        gblBreak = True
    
#    gblBreak = False


# Main program logic follows:
if __name__ == '__main__':

    global gblBreak
    global gblExit

    # If there is only one command line argument,then run as normal (no testing)
    if len(sys.argv) == 1:
        time.sleep(10)
    else:
        print("Testing")

    gblBreak = False
    gblExit = False

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(get_led_count(), LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)

    # Initialize the library (must be called once before other functions).
    strip.begin()

    host_name = socket.gethostname()
    start_topic = host_name
    print("Starting up as:", host_name)

    #
    # Setup MWTT Broker
    #
    ourClient = mqtt.Client(socket.gethostname())      # Create a MQTT client object
    ourClient.connect("192.168.1.202", 1883)    # Connect to the test MQTT broker

    ourClient.subscribe("rainbow_" + host_name)              # Subscribe to the topic
    ourClient.subscribe("theaterchase_" + host_name)         # Subscribe to the topic
    ourClient.subscribe("cylon_" + host_name)                # Subscribe to the topic
    ourClient.subscribe("twinkle_" + host_name)              # Subscribe to the topic
    ourClient.subscribe("ctwinkle_" + host_name)             # Subscribe to the topic
    ourClient.subscribe("rwb_" + host_name)                  # Subscribe to the topic
    ourClient.subscribe("xmas_" + host_name)                  # Subscribe to the topic

    ourClient.subscribe("on_" + host_name)          # Subscribe to the topic
    ourClient.subscribe("off_" + host_name)          # Subscribe to the topic
    ourClient.subscribe("break_" + host_name)                # Subscribe to the topic
    ourClient.subscribe("exit_" + host_name)          # Subscribe to the topic
    ourClient.on_message = LED_strip_CallBack   # Attach the messageFunction to subscription
    ourClient.loop_start()                      # Start the MQTT client
    # ourClient.loop_forever()                   # Start the MQTT client

    print("LED count is: ", get_led_count())
    print("Ready!")

    if len(sys.argv) > 1:
        XMAS_theater_chase(strip)

# Main program loop
    while not gblExit:
        time.sleep(1)  # Sleep for a second
 


