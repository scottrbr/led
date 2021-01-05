#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
#
# This code also makes use of the PIR motion sensor, if it's setup. The
# way this is integrated is it will turn on an LED strip if motion is
# detected - which the code for this is located at the very bottom in the
# main wait loop.
#
# Supported LED strip types:
#   WS2811B : Runs in normal strip mode assuming a WS2811B strip (RGB).
#   SK6812W : Runs in normal strip mode assuming a SK6812W strip (RGBW).
WS2811B   = "WS2811B"
SK6812W   = "SK6812W"
#
# The general library can found at: https://github.com/jgarff/rpi_ws281x
# The Python library can he found at https://github.com/rpi-ws281x/rpi-ws281x-python
#

import sys
import random
import time                         # general use
import socket                       # For getting the computer name
import _thread
from rpi_ws281x import *
import paho.mqtt.client as mqtt     # Import the MQTT library
import RPi.GPIO as GPIO             # Needed for motion sensor suport

# Motion sensor configuration - the I/O pin I am using
PIR_PIN = 7

# LED strip configuration:
LED_PIN        = 18     # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000 # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10     # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255    # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0      # set to '1' for GPIOs 13, 19, 41, 45 or 53

#
# Return the strip type we are using: RGB (WS281B) or an RGBW (SK6812W) strip.
# This is based on the name of the device.
# ws.WS2811_STRIP_GRB or ws.SK6812W_STRIP
#
def get_led_strip_type():

    host_name = socket.gethostname()

    if host_name == "strip01":
        strip_type = ws.WS2811_STRIP_GRB
    elif host_name == "strip02":
        strip_type = ws.SK6812W_STRIP
    elif host_name == "strip03":
        strip_type = ws.SK6812W_STRIP
    elif host_name == "raspberrypi4":
        strip_type = ws.WS2811_STRIP_GRB
    elif host_name == "candle01":
        strip_type = ws.WS2811_STRIP_GRB
    else:
        strip_type = ws.WS2811_STRIP_GRB

    return strip_type

#
# Not all of my devices have the same number of LEDs and I want this code to
# be used for all of them so I need to make this dynamic based on the name of the
# device.
#
def get_led_count():

    led_count = 100
    host_name = socket.gethostname()

    if host_name == "strip01":
        led_count = 300
    elif host_name == "strip02":
        led_count = 188
    elif host_name == "strip03":
        led_count = 112
    elif host_name == "raspberrypi4":
        led_count = 4
    elif host_name == "candle01":
        led_count = 4

    return led_count

# 
# This function returns True if the LED strip has a motion sensor in use.
# False if not.
#
def using_motion_sensor():

    sensor_use = False
    host_name = socket.gethostname()

    if host_name == "raspberrypi4":
        sensor_use = True
    elif host_name == "strip03":
        sensor_use = True
 
    return sensor_use


#
# LED strips and candles (short LED strips) share common function (but not
# all) so add a function where we can test if this is a candle LED strip.
# Note that this is determined from the word "candle" being part of the
# device name.
#
def is_candle():

    candle_led_strip = False
    host_name = socket.gethostname()

    if host_name.find("candle") > -1:   # Candle specific functions
        candle_led_strip = True
    elif host_name == "raspberrypi4":   # This computer is used for development
        candle_led_strip = False        # Put it in here in case we are working
                                        # on candle functions.

    return candle_led_strip 


#
# Power for LED strips can take large power supplies which can be very
# inconvenient, but we need to keep safe. So we will use this function
# to cap the may brightness output if I not able to provide a power
# supply to cover the worst case. The brightness is a numebr from 
# 1 to 255.
#
# If suggested brightness if not included, then return the maximum
# brightness for that LED strip.
#
def set_strip_brightness(strip, suggested_brightness=0):

    max_brightness = 30

    host_name = socket.gethostname()

    if host_name == "strip01":
        max_brightness = 30
    elif host_name == "strip02":
        max_brightness = 30
    elif host_name == "strip03":
        max_brightness = 40
    elif host_name == "raspberrypi4": # This computer is used for development
        max_brightness = 30
    elif host_name == "candle01":
        max_brightness = 40

    # If the caller is asking for less than the maximum, then use that number.
    if suggested_brightness > 0 and suggested_brightness < max_brightness:
        max_brightness = suggested_brightness

    strip.setBrightness(max_brightness)
 
#
# Wipe color across display a pixel at a time.
#
def colorWipe(strip, color, wait_ms=50):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)

    strip.show()


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

    set_strip_brightness(strip, 30)
 
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

    set_strip_brightness(strip, 30)

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
 
#
# General function I found on the internet to find the "nth" occurence
# of a character.
#
# Used to find if there was a second comma that would have the "white" color 
# for SK6812W LED strips.
#
def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


#
# This function is used to convert the RGB color sent vi MQTT in hex which
# is 6 digits - 2 hex numbers per color. It returns an integer tuple for RGB.
#
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


#
# Sets the entire strip color and brightness based on a message this is
# color in hex (rgb), comma, brightness in decimal which looks like:
# ff34b0,98. If we are using a 6812 strip, there will be an extra comma
# followed by the amount of white (1-255). This formation will look like
# ff34b0,98,156.
#
def set_strip_color(strip, message):

    ledclr = hex_to_rgb(message[0:6])

    first_comma_loc = message.find(',')
    second_comma_loc = find_nth(message, ',', 2)
    print("second comma at: ", second_comma_loc)
    length = len(message)

    # if we only see 1 comma, the color is not assumed to carry the "white"
    # color (onlY rgb) so assume white is 0
    if second_comma_loc == -1:
        brightness = message[(first_comma_loc+1):(length)]
        white = "0"
    else:
        brightness = message[first_comma_loc+1:second_comma_loc]
        white = message[second_comma_loc+1:length]
        print("brightness = ", brightness, "white = ", white)

    white_int = int(white)

    if get_led_strip_type() == ws.SK6812W_STRIP:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(ledclr[0], ledclr[1], ledclr[2], white_int))
    else:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(ledclr[0], ledclr[1], ledclr[2]))

    brightness_int = int(brightness)
    set_strip_brightness(strip, brightness_int)
    strip.show()


def CylonBounce(strip, red, green, blue, EyeSize, SpeedDelay, ReturnDelay):

    global gblBreak
    global gblExit

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

        if gblBreak or gblExit:
            break

    time.sleep(ReturnDelay/1000)

    for i in range(pixel_count-EyeSize-2, 0, -1):

        colorWipe(strip, Color(0,0,0), 0)

        strip.setPixelColor(i, Color(int(green/10), int(red/10), int(blue/10)))
        for j in range(1, EyeSize):
            strip.setPixelColor(i+j, Color(green, red, blue))

        strip.setPixelColor(i+EyeSize, Color(int(green/10), int(red/10), int(blue/10)))
        strip.show()
        time.sleep(SpeedDelay/1000)

        if gblBreak or gblExit:
            break

    time.sleep(ReturnDelay/1000)


#
# There is a known issue that when I get a new randome led, I do not check if
# it is a duplicate. This create some strange blinking on that LED.
#
def Twinkle(strip, numOfLights, LEDMaxBright, Minutes, ColorTwinkle):

    global gblBreak

    print("Twinkle")

    # Initial the strip to turn off all lights but set the brightness to maximum
    if get_led_strip_type() == ws.SK6812W_STRIP:
        set_strip_color(strip, "000000,00, 0")
    else:
        set_strip_color(strip, "000000,00")

    start_time = time.time()
    set_strip_brightness(strip, 40)

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


#
# This function displays 100 pixel long red, white, and blue moving bands
# down the LEd strip
#
def red_white_blue(strip):

    global gblBreak

    level = 60

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
    set_strip_color(strip, "000000,00")
    set_strip_brightness(strip, 30)
 
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

#############################################################################
#                           CANDLE SPECIFIC FUNCTIONS                       #
#############################################################################

# This is the main candle operation function
def candle_start(strip, season_color):

    global gblBreak

    if int(season_color) == 1:
        XMAS_time = False
    else:
        XMAS_time = True
    while not gblBreak:
        wait = random.randint(100, 120)             # set a random wait period
        randpix = strip.numPixels() #4     # random(0, numpix + 1);    //choose a random number of pixels
        numpix = strip.numPixels()  #4
        color = random.randint(0, 1)        # Pick either yellow or orange
                                            # so it leaves a certain number of
                                            # yellow pixels on (number of pixels/3)
        for i in range (int(numpix)):
            if not XMAS_time:
                strip.setPixelColor(i, Color(255, 120, 0))  # set the number of pixels to turn on and color value (yellowish)
            else:
                strip.setPixelColor(i, Color(255, 10, 0))  # set the number of pixels to turn on and color value (yellowish)

        strip.show();   # turn pixels on
#        strip.setBrightness(random.randint(5, 40))
        set_strip_brightness(strip, random.randint(5, 40))


        if color == 0:      # if red was chosen
            if not XMAS_time:
                flickred(strip, Color(215, 50, 0), wait, randpix)   # call flickred and pass it the red (orangeish)
            else:
                flickred(strip, Color(255, 0, 0), wait, randpix)   # call flickred and pass it the XMAS red color
        else:               # otherwise use yellow
            if not XMAS_time:
                flickYellow(strip, Color(180, 80, 0), wait, randpix)  # call flickYellow and pass it the yellow color
            else:
                flickYellow(strip, Color(18, 180, 0), wait, randpix)  # call flickYellow and pass it the XMAS green color


# Candle function for when red is chosen
def flickred(strip, c, wait, p):

    for i in range(p - 2):  # loop for given random pixel count (passed from loop)
        strip.setPixelColor(i, c)

    strip.show();  # turn pixels on

    time.sleep(wait/1000)

    for i in range(p):
        strip.setPixelColor(i, 0)        # turn pixel off



# Candle function for when yellow is chosen
def flickYellow(strip, c, wait, p):

    for i in range(p):          # loop for given random pixel count (passed from loop)
        strip.setPixelColor(i, c)
                                                                                
    strip.show()    # turn pixels on

    time.sleep(wait/1000)

    for i in range(p):
        strip.setPixelColor(i, 0)       # turn pixel off


# Our "on message" event
#
# Be careful about using the strip variable here. It is a global variable.
#
def LED_strip_CallBack(client, userdata, message):

    global gblBreak
    global gblExit
    global gblStrip

    topic = str(message.topic)
    host_name = socket.gethostname()

    message = str(message.payload.decode("utf-8"))
    print("Message::", message)
    print("Topic: ", topic)

    # if we find undefined in the message, something went wrong so exit
    if message.find("undefined") > -1:
        return

    # Stop any currently running routines
    gblBreak = True
    time.sleep(0.5)  # Wait 1/2 second for other routines to stop (just in case)
    gblBreak = False

    # LED strip specific functions here
    if host_name.find("strip") > -1 or host_name.find("raspberrypi4") > -1:    # LED strip specific instructions
        if topic == "on_" + host_name:
            set_strip_color(gblStrip, message)
        elif topic == "strip_pattern_" + host_name:
            if message == "rainbow":
                _thread.start_new_thread( rainbow, (gblStrip, ) )
            elif message == "theaterchase":
                theaterChase(gblStrip, Color(127, 127, 127))
            elif message == "cylon":
                _thread.start_new_thread( CylonBounce, (gblStrip, 0, 255, 0, 4, 20, 500))
            elif message == "twinkle":
                Minutes = 180
                _thread.start_new_thread( Twinkle, (gblStrip, 10, 255, Minutes, False))
            elif message == "ctwinkle":
                Minutes = 180
                _thread.start_new_thread( Twinkle, (gblStrip, 25, 255, Minutes, True))
            elif message == "rwb":
                _thread.start_new_thread( red_white_blue, (gblStrip, ) )
            elif message == "xmas":
                _thread.start_new_thread( XMAS_theater_chase, (gblStrip, ) )

    # Put candle specific handlers here
    if is_candle():                         # Candle specific functions
        if topic == "on_" + host_name:
            print("Turn on: ", host_name)
            _thread.start_new_thread( candle_start, (gblStrip, message) )

    # These are generic across all devices
    if topic == "off_" + host_name:
        if get_led_strip_type() == ws.SK6812W_STRIP:
            set_strip_color(gblStrip, "000000,10,0")
        else:
            set_strip_color(gblStrip, "000000,10")

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
    global gblStrip

    # If no extra parameters are set (currently we don't take any), then 
    # assume we are doing testing where we do not need to have extra
    # parameters.
    if len(sys.argv) == 1:
        # We need to wait 10 seconds here because this code with run at
        # device startup and there is a race condition on getting the MQTT
        # services started before this code trys to access them.
        time.sleep(10)
    else:
        print("Testing")    # Feedback to terminal if we are testing

    # Reset global variables needed for breaking out of functions and exiting
    # the application.
    gblBreak = False
    gblExit = False

    # Create NeoPixel object with appropriate configuration.
    gblStrip = Adafruit_NeoPixel(get_led_count(), LED_PIN, LED_FREQ_HZ, LED_DMA,
                                LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL,
                                get_led_strip_type())

    # Initialize the library (must be called once before other functions).
    gblStrip.begin()

    # Show the device name when starting (incase we are watching in terminal)
    host_name = socket.gethostname()
    start_topic = host_name
    print("Starting up as:", host_name)

    # Motion sensor setup
    if using_motion_sensor():
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)

    #
    # Setup MWTT Broker
    #
    ourClient = mqtt.Client(socket.gethostname())       # Create a MQTT client object
    ourClient.connect("192.168.1.202", 1883)            # Connect to the test MQTT broker

    # LED strip specific topics
    ourClient.subscribe("strip_pattern_" + host_name)

    # These are generic topics across all devices
    ourClient.subscribe("on_" + host_name)
    ourClient.subscribe("off_" + host_name)
    ourClient.subscribe("break_" + host_name)
    ourClient.subscribe("exit_" + host_name)
    ourClient.on_message = LED_strip_CallBack   # Attach the messageFunction to subscription
    ourClient.loop_start()                      # Start the MQTT client

    print("LED count is: ", gblStrip.numPixels())
    print("Ready!")

    # Put test code here when needed.
    #if len(sys.argv) > 1:
    #    XMAS_theater_chase(strip)

# Main program loop
    while not gblExit:
        # Turn the strip on if we are using a motion sensor
        if using_motion_sensor():
            if GPIO.input(PIR_PIN):
                colorWipe(gblStrip, Color(0,0,30), 0)
            else:
                colorWipe(gblStrip, Color(0,0,0), 0)

        time.sleep(0.5)  # Sleep for a second - was 1
 

