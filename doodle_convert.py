from skimage.morphology import medial_axis, dilation, disk
from pynput.keyboard import Key, Listener
from selenium import webdriver
from pydoc import text
import pytesseract
import numpy as np
import pyautogui
import random
import time
import cv2
import sys


########## TEXT RECOGNITION ##########
pos_upper_l = 0     # upper left corner of the text
pos_bottom_r = 0    # bottom right corner
shift = 0           # number of pressed shifts

print("Press SHIFT in the upper left corner")

def on_press(key):
    global pos_upper_l
    global pos_bottom_r
    global shift

    # if SHIFT was pressed, save coordinates
    if(key == Key.shift) and shift == 0:
        pos_upper_l = pyautogui.position()
        shift = 1
        print("Press SHIFT in the bottom right corner")
    # the second shift ends the thread
    elif(key == Key.shift):
        pos_bottom_r = pyautogui.position()
        shift = 2

def on_release(key):
    if key == Key.esc or (key == Key.shift and shift > 1):
        return False

# keyboard listener thread
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()


# image of the text rectangle
img = pyautogui.screenshot(region=(pos_upper_l.x, pos_upper_l.y, 
            pos_bottom_r.x-pos_upper_l.x, pos_bottom_r.y-pos_upper_l.y))

# text recognition
text = pytesseract.image_to_string(img).split()

search_text = text[0]
# more word are separated by the "_"
for w in text[1:]:
    if w != "" and w != "\t" and w != "\n":
        search_text = search_text + "_" + w

search_text = search_text.lower()
print('The text is: "',search_text, '"', sep="")




########## DOODLE CAPTURE ##########
# create a Chrome instance
browser = webdriver.Chrome()

# get to the picture
browser.get('https://quickdraw.withgoogle.com/data/'+search_text)

time.sleep(3)
up_left_x, up_left_y = (35,450) # coordinates of the top left image corner
width = 60
image = pyautogui.screenshot(region=(up_left_x, up_left_y, width, width))

browser.close()



########## IMAGE CONVERSION ##########
# OpenCV grayscale conversion of numpy image data
img = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)

# resize to 1000x1000
img = cv2.resize(img, (900, 900), interpolation = cv2.INTER_AREA)

# first dilation kernel matrix for 7 iterations
kernel = np.ones((3,3))
# image blur by the 10x10 matrix
blurred = cv2.blur(np.uint8(img), (10,10))
result = cv2.dilate(blurred, kernel, iterations=7)

# adaptive thresholding outputs 0/255 values
# 137 pixels neighborhood calculations, 36 mean adjustment
img_contour = cv2.adaptiveThreshold(result,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,137,36)

# single line skeleton for the outline
skeleton = (medial_axis(255-img_contour)*255).astype(np.uint8)

# dilation -> morphological operations used for the image enhancement
enhanced = 255-dilation(skeleton,disk(1))
enhanced = cv2.medianBlur(enhanced,5)



########## IMAGE OUTPUT ##########
# save the output image as an input for the drawing
cv2.imwrite('input.png', enhanced)


