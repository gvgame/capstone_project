import cv2
import numpy as np
import sys, time

#Generate the image path on demand based on the image number
#The black background is used as the default in this pathname
#Remember to revise this if any changes are made to the file naming scheme
def getImagePath(img_num):
    '''
    Image names are ordered as follows:
    Image_Number + Backgound_type + .png
    b = black background
    c = clear (transparent) background
    w = white background

    NOTE: Under the current implementation, there does not seem to be any
    significant difference (or really any difference at all) between
    the different background types on the performance of the detection
    algorithm
    '''
    if img_num < 10:
        path = "img/00" + str(img_num) + "c.png"
    elif img_num < 100:
        path = "img/0" + str(img_num) + "c.png"
    else:
        path = "img/" + str(img_num) + "c.png"

    return path

#Determine if the input is an integer.
#Allows 'x', '-x', and '+x' but not '0.x'
def is_int(num):
    if num[0] in ('-', '+'):
        return num[1:].isdigit()
    return num.isdigit()

class Window:
    #Placeholder Values
    _name = ''      #Name of the window
    _img_path = ''  #File path of the image
    _img_num = -1   #For indexing specific files
    _img = ''       #Stores image matrix
    _w = 0          #Window width in px
    _h = 0          #Window height in px

    def __init__(self, name, img_num = 1, width = 1000, height = 800):
        self._name = name
        self._img_path = getImagePath(img_num)
        self._img_num = img_num
        self._w = width
        self._h = height
        self.makeWindow(name, width, height)
        self.show(name, self._img_path)

    #For use when cycling through images. Usually (1) and (-1).
    def incImgNum(self, amount):
        self._img_num += amount
        return self._img_num

    #Pass the image to be loaded into a CV2 / Numpy array which will be
    #shown to the window
    def setImage(self, img_path):
        '''
        Image Modes:
            cv2.IMREAD_COLOR:     (1) Loads a color image, ignores transparancy
            cv2.IMREAD_GRAYSCALE: (0) Loads a monochrome image
            cv2.IMREAD_UNCHANGED: (-1) Loads an image with unchanged channels

            cv2.IMREAD_COLOR is selected here in order to help drawContours()
            play nice with the color mode
        '''
        return cv2.imread(img_path, cv2.IMREAD_COLOR)

    #Create a named window of a specific size
    def makeWindow(self, name, width, height):
        '''
        Window Parameters:
            WINDOW_NORMAL:      The window can be re-sized manually
            WINDOW_AUTOSIZE:    The window is locked to the image's size
        '''
        cv2.namedWindow(name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(name, width, height)

    #Set and show an image to the window
    def show(self, window_name, img_path):
        self._img = self.setImage(img_path)
        cv2.imshow(window_name, self._img)

    #For use when cycling through images. Updates the image in the window
    def updateWin(self, name, img_path):
        self._img_path = self.setImage(img_path)
        cv2.imshow(name, self._img_path)

    def closeWindow(self):
        cv2.destroyWindow(self._name)

class Menu:
    #Print the control menu
    def printControls(self):
        print("Controls:\n")
        print("\tLeft / Right arrows: Prev / next image")
        print("\tm: Print this menu again")
        print("\tq: Quit")
        print("\t----------------------------------------")
        print("\tt: Toggle thresholding (adaptive)")
        print("\tc: Toggle contour detection")
        print()
        return

    def getUserInput(self, message):
        return_string = input(message)
        return return_string

    #Handle the menu input
    def handleControls(self, win):
        thresholder = Thresholder()
        contour_detector = ContourDetector()
        while (True):
            #Wait n milliseconds for a key press. 0 waits indefinitely
            key = cv2.waitKey(0)

            #If you would like to find new keycodes to add inputs to the menu
            #you can simply un-comment the below line and press the desired key
            #print(str(key))

            if key == 81:
                if win._img_num > 1:
                    win.incImgNum(-1)
                    win.updateWin(win._name, getImagePath(win._img_num))

            elif key == 83:
                if win._img_num < 7:       #This is just a temporary hack to stop it from accidentally crashing
                    win.incImgNum(1)
                    win.updateWin(win._name, getImagePath(win._img_num))

            elif key == ord('t'):
                #Create a new window to hold the modified image
                win_th = Window("Meteorite with Adaptive Thresholding", win._img_num)

                #If threshold is active already
                if thresholder.isActiveInWin(win_th):
                    #Toggle it off
                    thresholder.setActiveInWin(win_th, thresholder.toggleOff(win_th))
                    #Note: Python performs some automatic garbage collection,
                    #but if you are experiencing MEMORY LEAK issues, you
                    #may want to explicitly free win_tf at this point

                #Else, it's off
                else:
                    #So toggle it on
                    thresholder.setActiveInWin(win_th, thresholder.toggleOn(win_th))

            elif key == ord('c'):
                #Create a new window to hold the modified image
                win_cd = Window("Meteorite with Contour Detection", win._img_num)

                #If contour detector is active already
                if contour_detector.isActiveInWin(win_cd):
                    #toggle it off
                    contour_detector.setActiveInWin(win_cd, contour_detector.toggleOff(win_cd))

                #Else, it's off
                else:
                    #So toggle it on
                    contour_detector.setActiveInWin(win_cd, contour_detector.toggleOn(win_cd))

            elif key == ord('m'):
                self.printControls()

            elif key == ord('q'):
                cv2.destroyAllWindows()
                print("Quitting...")
                sys.exit(0)


class Thresholder:
    '''
    A threshold function takes a grayscale image (values from 0 to 255)
    and converts it to a binary image (values of 0 or 1), based on the
    threshold range.
    '''
    #A dictionary keeps track of each window in which the thresholder
    #is active
    active = {}

    #Search active for the window
    def isActiveInWin(self, win):
        #If it exists
        if win._name in self.active:
            #Return its corresponding value
            return self.active[win._name]

        #Otherwise it must not exist, so it can't be active
        return False

    #Set active for a given window
    def setActiveInWin(self, win, value):
        self.active[win._name] = value

    def toggleOn(self, win):
        #Convert the image to grayscale
        gray = cv2.cvtColor(win._img, cv2.COLOR_BGR2GRAY)
        #Apply a small blur to help reduce noise
        blur_img = cv2.medianBlur(gray, 17)
        #Apply the threshold
        threshold_img = cv2.adaptiveThreshold(blur_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 5, 1)

        '''
            Adaptive thresholding is used in this example. It is useful as
            it does not rely on absolute values for thresholding, but adapts
            to each individual image

            adaptiveThreshold(in_img, max_val, adaptive_method, thresh_type, kernel_size, C)

            in_img:             input image
            max_val:            value given to pixels greater than threshold value
            adaptive_method:    cv2.ADAPTIVE_THRESH_GAUSSIAN_C or cv2.ADAPTIVE_THRESH_MEAN_C
            thresh_type:        cv2.THRESH_BINARY or cv2.THRESH_BINARY_INV
            kernel_size:        size of pixel neighborhood used to calculate threshold value
            C:                  a constant subtracted from mean or weighted mean

            Ironically, this seems to function as a better edge detector than
            the Canny edge detector

            NOTE: If C < 1, cv2.THRESH_BINARY_INV will not work
        '''

        #Finally, draw the thresholded image to the window
        cv2.namedWindow(win._name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win._name, win._w, win._h)
        cv2.imshow(win._name, threshold_img)
        return True

    def toggleOff(self, win):
        win.closeWindow()
        return False

class ContourDetector:
    '''
    A contouring function takes a binary image (values of 0 or 1) and
    finds the boundary of white regions against a black background.
    '''
    #A dictionary keeps track of each window in which the contour
    #detector is active
    active = {}

    #Search active for the window
    def isActiveInWin(self, win):
        #If it exists
        if win._name in self.active:
            #Return its corresponding value
            return self.active[win._name]

        #Otherwise it must not exist, so it can't be active
        return False

    #Set active for a given window
    def setActiveInWin(self, win, value):
        self.active[win._name] = value

    def toggleOn(self, win):
        #Store the original image, on which the contours will be drawn
        image = win._img
        #Convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        #Apply adaptive thresholding steps as if the user pressed 't'
        blur_img = cv2.medianBlur(gray, 17)
        threshold_img = cv2.adaptiveThreshold(blur_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 5, 1)

        #Find the contours. Returns the modified image, the list of contours, and the contour heirarchy
        im, contours, h = cv2.findContours(threshold_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        '''
            Contour detection is used in this example. It is useful as it provides
            an extremely rich amount of functions to calculate additional information
            about the regions detected. Contour detection only detects white
            objects on a black background, and so thresholding must be performed
            first. The contours are detected on the thresholded image, and then
            transferred back to the original color image.

            findContours(in_img, heirarchy, approximation)

            in_img:         Image to find contours on
            heirarchy:      The way contours are listed. cv2.RETR_LIST
                            or cv2.RETR_TREE
            approximation:  Whether to use approximation or not.
                            cv2.CHAIN_APPROX_NONE or cv2.CHAIN_APPROX_SIMPLE

            returns (image, contours, heirarchy)

            image:          The exact same image that was passed in
            contours:       A list containing all of the contours.
                            Contours are stored as numpy arrays of points
            heirarchy:      Heirarchy information. Probably outside the
                            scope of this problem

            There is a lot of information in this function that probaby isn't
            completely necessary to the problem at this time. Specifically,
            the heirarchy information. Heirarchy in a tree allows for parent
            and child contours (probably based on size or if a certain contour
            is contained within another). This just helps when you only want
            to draw specific contours.

            Another aspect that might not be necessary is the approximation
            method. When no approximation is selected, the function grabs
            all points that fall along a contour's edge. When simple approximation
            is usex, the function will remove redundant points (points that
            fall along a straight line between to other points). This helps
            save on memory in some applications, but because of the random
            and jagged nature of the contours, there are very few areas where
            points would be omitted.
        '''

        cv2.drawContours(image, contours, -1, (0,255,0), 3)

        '''
            The second half of the contour detection function is called here.

            drawContours(image, contours, num, (b,g,r), thickness)

            image:      Image to which the contours will be drawn
            contours:   The list of contours found by findContours()
            num:        The index of the contour to draw. -1 draws all contours
            (b,r,g)     Color values for the points/lines. Yes, it's Blue-Red-Green.
                        No, I don't know why
            thickness:  Thickness of the points/lines to be drawn

            In my experience, drawContours() is sensitive to the color-mode
            of the image. If the source image is originally read in as greyscale,
            drawContours will only draw the points in grayscale (in (b,r,g),
            b is the brightness value from 0 to 255, while r and g are ignored).
            This caused the image to look as though it were blank, since the
            points and lines were being drawn black (since (0,255,0) was used),
            covering up any white from the thresholded image.

            Dealing with this is simple enough. The image must be read in
            as cv2.IMREAD_COLOR or cv2.IMREAD_UNCHANGED when readin the image
            from the file (refer to Window.setImage()). When the image is used
            by the contour detector, it must then be converted to grayscale
            using cv2.cvtColor().
        '''

        #Draw the image with contours to the window
        cv2.namedWindow(win._name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win._name, win._w, win._h)
        cv2.imshow(win._name, image)
        return True

    def toggleOff(self, win):
        win.closeWindow()
        return False

def main():
    #This original window that is created is the only one that the
    #menu controls will affect. If you want to allow controls for
    #additional windows later, you will have to call handleControls()
    #on them individually
    win = Window("Meteorite")   #Create the main window

    menu = Menu()               #Create the menu
    menu.printControls()
    menu.handleControls(win)    #Allow the main window to receive menu input

if __name__ == "__main__":
    main()
