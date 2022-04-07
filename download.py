from pynput.keyboard import Key, Listener
from selenium import webdriver
from pathlib import Path
import pytesseract
import pyautogui
import requests
import random
import urllib
import time

############# CONSTANTS ##############
pos_upper_l = 0     # upper left corner of the text
pos_bottom_r = 0    # bottom right corner
shift = 0           # number of pressed shifts
# for the google image selection part
random_range = 10   # number of the first images to choose an image from
max_time = 8        # max seconds to wait for the quality image
output = str(Path(__file__).resolve().parent)+"/Images/input_download.jpg"


########## TEXT RECOGNITION ##########
print("Press shift in the upper left corner")

# thread-checking functions for the text selection 
def on_press(key):
    # global vars to connect the thread with the base
    global pos_upper_l
    global pos_bottom_r
    global shift

    # the first SHIFT -> save upper left coords
    if(key == Key.shift) and shift == 0:
        pos_upper_l = pyautogui.position()
        shift = 1
        print("Press shift in the bottom right corner")
    # the second SHIFT -> save bottom left coords
    elif(key == Key.shift):
        pos_bottom_r = pyautogui.position()
        shift = 2

def on_release(key):
    if key == Key.esc or (key == Key.shift and shift > 1):
        return False

# keyboard listener thread
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()


# screen rectangle with the text 
img = pyautogui.screenshot(region=(pos_upper_l.x, pos_upper_l.y, 
            pos_bottom_r.x-pos_upper_l.x, pos_bottom_r.y-pos_upper_l.y))

# text recognition
text = pytesseract.image_to_string(img).split()
search_text = text[0]
for w in text[1:]:
    if w != "" and w != "\t" and w != "\n":
        search_text = search_text + " " + w 

print('The text is: "',search_text, '"', sep="")



########## GOOGLE IMAGE DOWNLOADING ##########
# edit the search text phrase to find better pictures
search_text = f"{search_text} clipart"
 
# Chrome options to run a headless browser window
opt = webdriver.ChromeOptions()
opt.add_argument("headless")
browser = webdriver.Chrome(options=opt)

# reach the search_text images url
browser.get('https://www.google.com/search?tbm=isch&q='+search_text)
time.sleep(0.1)

try:
    Path("Images").mkdir(parents=True, exist_ok=True)
    
    # image number generation
    rnd = random.randint(0,random_range)

    # prepare the image elements and click the rnd'th image
    elements = browser.find_elements_by_class_name('rg_i')
    elements[rnd].click()
    time.sleep(0.1)

    # change the selection to the image 
    element = browser.find_elements_by_class_name('v4dQwb')
    index = 0 if rnd == 0 else 1
    img = element[index].find_element_by_class_name('n3VNCb')

    start = time.time()
    # try to get the src url
    url = img.get_attribute("src")
    while True:
        current = time.time()
        # trying to load a better quality picture, not the default url
        if(url.startswith("http")) or current > start+max_time:
            break
        url = img.get_attribute("src")
        time.sleep(0.03)

    print("Random:",rnd,"\nurl:",url)
    
    # download image to the given output file
    # 
    r = requests.get(url, stream=True)
    with open(output, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    #urllib.request.urlretrieve(url, output)
    browser.close()

except:
    print("Quality downloading ERROR") 
	
    try:
        # get the worse one
        url = img.get_attribute("src")
        urllib.request.urlretrieve(url, output)
    except:
        pass
    browser.close()
    pass
