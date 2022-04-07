from svgtrace import trace
from pathlib import Path
from enum import Enum
import pyautogui
import time
import re

############ CONSTANTS ############
pause = 0.008       # pause in each drawing step
time_limit = 45     # program drawing time limit
start_x = 420       #50
start_y = 380       #220
max_width = 230     #300 # [px] max drawing canvas size
bezier_parts = 1    # 1 part bezier is an ordinary line
num_of_L_reduce = 3 # number of lines 'L' in svg to reduce to a single one 

# FSM svg loading states
class S(Enum):
    NONE = 0
    M_X  = 1
    M_Y  = 2
    MOVE = 3
    L_X  = 4
    L_Y  = 5
    LINE = 6
    Q_CX = 7
    Q_CY = 8
    Q_X  = 9
    Q_Y  = 10
    QUAD = 11


########## IMAGE TO SVG TRACING ##########
# get the base directory
THISDIR = str(Path(__file__).resolve().parent)

# prepare the output .svg file
bw = open(THISDIR + "/result.svg", "w")
# convert the input image bitmap to svg
bw.write(trace(THISDIR + "/input.png", True))
bw.close()



########## VALUES INITIALIZATION ##########
# open the svg with vector lines
file = open('result.svg','r')

# default size; will be set from the svg header  
width = 200  
height = 200
max_width_scale = 1 # will be calculated

state = S.NONE
# current cursor location
x = 0
y = 0
# starting path coords from the Move command
m_x = 0
m_y = 0
# Bezier control point
qcx = 0
qcy = 0
# Bezier end point 
qx = 0
qy = 0

run_time = time.time()
drawn_lines = 0
pyautogui.PAUSE = 0.015 # starting drawing delay



########## LINES DRAWING ##########
# convert a string number from SVG to a scaled float 
def get_num(str):
    return max_width_scale*float(str)

# number of 'L' commands in a row in SVG
lines_in_row = 0
# a word before next_word delayed by one cycle to see the future L 
word = ""

# read all lines and all words from SVG
for line in file:
    for next_word in line.split():
        if word == "":
            word = next_word
            continue

        ########## EXECUTION OF COMMANDS ##########
        # MOVE TO
        # 2. cycle - load Y
        if state == S.M_Y:
            y = start_y + get_num(word)
            m_y = y # start point for the Z command
            state = S.MOVE
        # 1. cycle - load X
        elif state == S.M_X:
            x = start_x + get_num(word)
            m_x = x # start point for the Z command
            state = S.M_Y
        # 2. cycle - move cursor
        if state == S.MOVE:
            # do not draw
            pyautogui.mouseUp(button='left')
            pyautogui.moveTo(x, y)
            # prepare to draw for next commands
            pyautogui.mouseDown()
            state = S.NONE

        # LINE TO
        # 2. cycle - load Y
        elif state == S.L_Y:
            y = start_y + get_num(word)
            state = S.LINE
        # 1. cycle - load X
        elif state == S.L_X:
            x = start_x + get_num(word)
            state = S.L_Y
        # 2. cycle - draw a line
        if state == S.LINE:
            # if needed - skip L num_of_L_reduce times
            if next_word == "L" and lines_in_row < num_of_L_reduce:
                lines_in_row = lines_in_row + 1
                state = S.NONE
            else:
                # mouse click is already down, so just move
                pyautogui.moveTo(x=x, y=y)
                lines_in_row = 0
                state = S.NONE
                drawn_lines = drawn_lines + 1

        # QUADRATIC BEZIER LINE
        # 4. cycle - load qy end point
        elif state == S.Q_Y:
            qy = start_y + get_num(word)
            state = S.QUAD
        # 3. cycle - load qx end point
        elif state == S.Q_X:
            qx = start_x + get_num(word)
            state = S.Q_Y
        # 2. cycle - load qcy control point
        elif state == S.Q_CY:
            qcy = start_y + get_num(word)
            state = S.Q_X
        # 1. cycle - load qcx control point
        elif state == S.Q_CX:
            qcx = start_x + get_num(word)
            state = S.Q_CY
        # 4. cycle - draw a spline
        if state == S.QUAD:
            # interpolate the curve with (bezier_parts-1) points
            for i in range(1,bezier_parts):
                t = i*1/bezier_parts
                # use of the known bezier formula
                mid_x = (1 - t) * (1 - t) * x + 2 * (1 - t) * t * qcx + t * t * qx
                mid_y = (1 - t) * (1 - t) * y + 2 * (1 - t) * t * qcy + t * t * qy
                pyautogui.moveTo(x=mid_x, y=mid_y)
                drawn_lines = drawn_lines + 1

            # final move to the end point
            pyautogui.moveTo(x=qx, y=qy)
            drawn_lines = drawn_lines + 1
            state = S.NONE

        ########## SVG COMMANDS ##########
        if "width=" in word:
            # regex to extract the width number
            width = int(re.findall(r"\d+", word)[0])
            max_width_scale = float(max_width/width)
        elif "height=" in word:
            # regex to extract the height number
            height = int(re.findall(r"\d+", word)[0])
        # MOVE
        elif 'd="M' == word or 'M' == word:
            state = S.M_X
        # LINE
        elif "L" == word:     
            state = S.L_X
        # QUADRATIC BEZIER
        elif "Q" == word:     
            state = S.Q_CX
        # Z LINE TO THE START
        elif "Z" == word: 
            pyautogui.moveTo(x=m_x, y=m_y)
            drawn_lines = drawn_lines + 1
            state = S.NONE


        if time.time() > run_time + 0.2:
            pyautogui.PAUSE = pause
            if time.time() > run_time + time_limit:
                break 

        # word is the next_word 1 cycle delayed
        word = next_word


pyautogui.mouseUp(button='left')

print("Time:", round(time.time()-run_time,2),"s")
print("Drawn",drawn_lines,"lines")
