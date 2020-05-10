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
#from random import randint
import time
import thread
from neopixel import *
import paho.mqtt.client as mqtt  # Import the MQTT library


# LED strip configuration:
LED_COUNT      = 150      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53



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

def rainbow(strip, wait_ms=20, iterations=1):

    global gblBreak

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
    """Rainbow movie theater light stJosh has setup a call for April 20th with the group in Livingston to discuss.yle chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)


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
        strip.setPixelColor(i, Color(ledclr[1], ledclr[0], ledclr[2]))

    strip.setBrightness(int(brightness))
    strip.show()



def CylonBounce(strip, red, green, blue, EyeSize, SpeedDelay, ReturnDelay):

    pixel_count = strip.numPixels()

    for i in range(0, pixel_count-EyeSize-2):
        #strip.fill()         #setAll(0,0,0);
        colorWipe(strip, 0, 0)

        strip.setPixelColor(i, Color(red/10, green/10, blue/10))
        for j in range(0, EyeSize):
            strip.setPixelColor(i+j, Color(red, green, blue))

        strip.setPixelColor(i+EyeSize, Color(red/10, green/10, blue/10))
        strip.show()
        time.sleep(SpeedDelay/1000)

    time.sleep(ReturnDelay/1000)


    for i in range(pixel_count-EyeSize-2, 0, -1):

        colorWipe(strip, 0, 0)

        strip.setPixelColor(i, Color(red/10, green/10, blue/10))
        for j in range(1, EyeSize):
            strip.setPixelColor(i+j, Color(red, green, blue))

        strip.setPixelColor(i+EyeSize, Color(red/10, green/10, blue/10))
        strip.show()
        time.sleep(SpeedDelay/1000)

    time.sleep(ReturnDelay/1000)


#
# There is a known issue that when I get a new randome led, I do not check if it is a duplicate 
#
def Twinkle(strip, numOfLights, LEDMaxBright, NumOfLoops):

    global gblBreak

    # Initial the strip
    set_strip_color(strip, "000000,255")
    strip.setBrightness(255)

    #
    # Intialize all of our arrays
    # light - list all of the lights we are turning on and off
    # light_increment - an True/False for each light so we know if we are getting brighter or dimmer
    # light_curr_life - Life counter for each light so we know how it's age (number of loops it has gone through)
    #
    lights = random.sample(xrange(0, strip.numPixels()), numOfLights)   # Samples does not include duplicate values
    light_increment = [True] * numOfLights
    light_curr_life = [0] * numOfLights
    light_max_life = random.sample(xrange(10, 100), numOfLights)   # Life is in number of loops
    light_brightness = random.sample(xrange(1, LEDMaxBright), numOfLights) # randomize maximum life (100 ms minimum)
    #individual_light_color = random.sample(xrange(0,255), numOfLights)     

    for loop in range(NumOfLoops):

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

                    # The light's life is over, generate a new one.
                    lights[i] = random.randint(0, strip.numPixels())
                    light_max_life[i] = random.randint(10, 100)
                    light_curr_life[i] = 0
                    light_increment[i] = True

            light_color = light_brightness[i]/(light_max_life[i]/2) * light_curr_life[i]
            strip.setPixelColor(lights[i], Color(light_color, light_color, light_color))

        strip.show()


# Our "on message" event
#
# Be careful about using the strip variable here. It is a global variable
#
def LED_strip_CallBack(client, userdata, message):

    global gblBreak

    topic = str(message.topic)

    message = str(message.payload.decode("utf-8"))
    print(message)
    print(topic)

    # Stop any currently running routines
    gblBreak = True
    time.sleep(0.5)  # Wait 1/2 second for routines to stop
    gblBreak = False

    if topic == "strip":
            set_strip_color(strip, message)
    elif topic == "rainbow":
            thread.start_new_thread( rainbow, (strip, ) )
            #rainbow(strip)
    elif topic == "theaterchase":
        theaterChase(strip, Color(127, 127, 127))
    elif topic == "cylon":
        CylonBounce(strip, 0, 255, 0, 4, 20, 500)
    elif topic == "twinkle":
        thread.start_new_thread( Twinkle, (strip, 10, 255, 200000) )
        #Twinkle(strip, 10, 255, 1)
    elif topic == "break":
        gblBreak = True

    gblBreak = False


# Main program logic follows:
if __name__ == '__main__':

    global gblBreak

    gblBreak = False

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)

    # Initialize the library (must be called once before other functions).
    strip.begin()

    #
    # Setup MWTT Broker
    #
    ourClient = mqtt.Client("makerio_mqtt")      # Create a MQTT client object
    ourClient.connect("192.168.1.202", 1883)     # Connect to the test MQTT broker
    ourClient.subscribe("strip")                 # Subscribe to the topic
    ourClient.subscribe("rainbow")               # Subscribe to the topic
    ourClient.subscribe("theaterchase")          # Subscribe to the topic
    ourClient.subscribe("cylon")                 # Subscribe to the topic
    ourClient.subscribe("twinkle")               # Subscribe to the topic
    ourClient.subscribe("break")                 # Subscribe to the topic
    ourClient.on_message = LED_strip_CallBack    # Attach the messageFunction to subscription
    ourClient.loop_start()                       # Start the MQTT client
#    ourClient.loop_forever()                       # Start the MQTT client


# Main program loop
    while (1):
        #ourClient.publish("AC_unit", "on")  # Publish message to MQTT broker
        time.sleep(1)  # Sleep for a second






