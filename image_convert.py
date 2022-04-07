import matplotlib.pyplot as plt
import numpy as np
import time
import cv2
import sys

# program runtime start 
start = time.time()


############ CONSTANTS ############
# higher values make an image more nice, but the process is slower
min_width = 900 
max_width = 1100


########## IMAGE LOADING ##########
# read the input image
img = cv2.imread("Images/input_download.jpg")

height, width, channels = img.shape
scale = 1 # default image scale
if width < min_width:
    scale = float(min_width/width)
elif width > max_width:
    scale = float(max_width/width)

# fit dimensions to correspond with given scale
height = int(height * scale)
width = int(width * scale)

# new sized image
img = cv2.resize(img, (width, height), interpolation = cv2.INTER_AREA)



########## OUTLINE EXTRACTION ##########
# function to convert an image to a simple contour
def create_outline_drawing(img):
    kernel = np.ones((5,5), np.uint8)
    img_grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)   
    img_dilated = cv2.dilate(img_grayscale, kernel, iterations=2)
    img_diff = cv2.absdiff(img_dilated, img_grayscale)
    # black-white inversion 
    contour = 255 - img_diff
    return contour

# use our outline function
img_contour = create_outline_drawing(img)



########## CONTOUR ADJUSTMENT ##########
# function returns if the pixel at [y,x] have only a black color around in a '+' shape
def is_dark(image, y, x):
    only_zeros = int(image[y,x-1]) == 0 and\
                 int(image[y-1,x]) == 0 and int(image[y+1,x]) == 0 and\
                 int(image[y,x+1]) == 0
    return only_zeros # true if there is a high density black


# adaptive thresholding outputs only 0/255 values from the grayscaled outline img_contour
# 107 pixels neighborhood calculations, 15 mean adjustment, blur 5
# medianBlur for the better results
img_contour = cv2.adaptiveThreshold(cv2.medianBlur(img_contour,5),255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY,107,25)

# matrix of the image sizes filled with white (255) values
# mix of dilation outline, threshold and blur
blended = np.full((height,width),255)

# outline is wide, so we retain only middle pixels in lines to make it thinner
for y in range(1,height-1):
    for x in range(1,width-1):
        # ONLY for the black pixels (due to speed) evaluate if it should change the color
        if img_contour[y,x] == 0:
            if is_dark(img_contour, y, x):
                blended[y,x] = 0



######### SAVING OUTPUT ##########
# image conversion phases
# f, ax = plt.subplots(2,2, figsize=(10, 10))
# plt.gray() 
# ax[0,0].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
# ax[0,0].set_title('Grayscale')
# ax[0,1].imshow(cv2.dilate(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),\
#            np.ones((5,5), np.uint8), iterations=2))
# ax[0,1].set_title('Dilation')
# ax[1,0].imshow(img_contour)
# ax[1,0].set_title('Contour')
# ax[1,1].imshow(blended)
# ax[1,1].set_title('Thin blended contour')
# plt.show()

# save the output image as an input for the drawing
cv2.imwrite("input.png", blended)

# print the process runtime
print("Conversion:", round(time.time()-start, 2), "s")
