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

class Window:
    #Placeholder Values
    name = ''
    img = ''
    img_num = -1
    w = 0
    h = 0


    def __init__(self, _name, _img_num = 1, _width = 1000, _height = 800):
        self.name = _name
        self.img_num = _img_num
        self.w = _width
        self.h = _height
        self.makeWindow(_name, _width, _height)
        self.show(_name, getImagePath(_img_num))

    def getImgNum(self):
        return self.img_num

    #For use when cycling through images. Usually (1) and (-1).
    def incImgNum(self, amount):
        self.img_num += amount
        return self.img_num

    def getWinName(self):
        return self.name

    #Pass the image to be loaded into a CV2 / Numpy array which will be
    #shown to the window
    def setImage(self, img_path):
        '''
        Image Modes:
            cv2.IMREAD_COLOR:     (1) Loads a color image, ignores transparancy
            cv2.IMREAD_GRAYSCALE: (0) Loads a monochrome image
            cv2.IMREAD_UNCHANGED: (-1) Loads an image with unchanged channels
        '''
        return cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

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
        self.img = self.setImage(img_path)
        cv2.imshow(window_name, self.img)

    #For use when cycling through images. Updates the image in the window
    def updateWin(self, name, img_path):
        self.img = self.setImage(img_path)
        cv2.imshow(name, self.img)

    def closeWindow(self):
        cv2.destroyWindow(self.name)

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

    #Handle the menu input
    def handleControls(self, win):
        thresholder = Thresholder()
        #contour_detector = ContorDetector()
        while (True):
            #Wait n milliseconds for a key press. 0 waits indefinitely
            key = cv2.waitKey(0)

            #If you would like to find new keycodes to add inputs to the menu
            #you can simply un-comment the below line and press the desired key
            #print(str(key))

            if key == 81:
                if win.img_num > 1:
                    win.incImgNum(-1)
                    win.updateWin(win.name, getImagePath(win.img_num))

            elif key == 83:
                if win.img_num < 7:       #This is just a temporary hack to stop it from accidentally crashing
                    win.incImgNum(1)
                    win.updateWin(win.name, getImagePath(win.img_num))

            elif key == ord('t'):
                #Create a new window to hold the modified image
                win_th = Window("Meteorite with Adaptive Thresholding", win.getImgNum())

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
                print("To be implemented...")

            elif key == ord('f'):
                #Create a new window to hold the modified image
                win_mf = Window("Meteorite with Median Filter", win.getImgNum())

                #If median filter is active already
                if med_filter.isActiveInWin(win_mf):
                    #Toggle it off
                    med_filter.setActiveInWin(win_mf, med_filter.toggleOff(win_mf))
                    #Note: Python performs some automatic garbage collection,
                    #but if you are experiencing MEMORY LEAK issues, you
                    #may want to explicitly free win_bd at this point.

                #Else, it's off
                else:
                    #So toggle it on
                    med_filter.setActiveInWin(win_mf, med_filter.toggleOn(win_mf))

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
        if win.getWinName() in self.active:
            #Return its corresponding value
            return self.active[win.getWinName()]

        #Otherwise it must not exist, so it can't be active
        return False

    #Set active for a given window
    def setActiveInWin(self, win, value):
        self.active[win.getWinName()] = value

    def toggleOn(self, win):
        #Apply a small blur to help reduce noise and increase clarity
        blur_img = cv2.medianBlur(win.img, 9)

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
        C:                  a constant subtracted from mean or weigted mean

        Ironically, this seems to function as a better edge detector than
        the Canny edge detector
        '''
        #Apply the threshold
        threshold_img = cv2.adaptiveThreshold(blur_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 2)

        cv2.namedWindow(win.getWinName(), cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win.getWinName(), win.w, win.h)
        cv2.imshow(win.getWinName(), threshold_img)
        return True

    def toggleOff(self, win):
        win.closeWindow()
        return False

class ContourDetector:
    '''

    '''
    #A dictionary keeps track of each window in which the contour
    #detector is active
    active = {}

    #Search active for the window
    def isActiveInWin(self, win):
        #If it exists
        if win.getWinName() in self.active:
            #Return its corresponding value
            return self.active[win.getWinName()]

        #Otherwise it must not exist, so it can't be active
        return False

    #Set active for a given window
    def setActiveInWin(self, win, value):
        self.active[win.getWinName()] = value

    def toggleOn(self, win):

        return True

    def toggleOff(self, win):
        win.closeWindow()
        return False

def main():
    #This original window that is created is the only one that the
    #menu controls will affect. If you want to allow controls for
    #additional windows later, you will have to call handleControls()
    #on them individually
    win = Window("Meteorite")     #Create the main window

    menu = Menu()               #Create the menu
    menu.printControls()
    menu.handleControls(win)    #Allow the main window to receive menu input

if __name__ == "__main__":
    main()
