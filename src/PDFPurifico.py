import sys
from PIL import Image
from PyQt5.QtWidgets import (QWidget, QPushButton, QApplication, QMessageBox, QDesktopWidget, QMainWindow, QLabel, QDialog, QRubberBand, QFileDialog, QProgressBar, QLineEdit)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import QPoint, QThread, pyqtSignal, Qt, QRect
import numpy as np
from pdf2image import convert_from_path
from converter import convertFlat, getAverageEstimate, convertAverage, drawLines


class External(QThread):
    """
        Runs a counter thread for progress bars.
    """
    countChanged = pyqtSignal(int)

    def __init__(self):
        '''
            Initializes object
        '''
        super().__init__()
        self.function = None
        return
    

    def setFunction(self, function, arguments):
        '''
            Set function and arguments to be used when thread starts
        '''
        self.function = function
        self.arguments = arguments
        return

    def run(self):
        '''
            Start thread and execute the correct function
        '''
        if (self.function == getAverageEstimate):

            arg1, arg2, arg3, arg4, arg5 = self.arguments
            getAverageEstimate(arg1, arg2, self, arg3, arg4, arg5)

        elif (self.function == convertFlat):

            arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9 = self.arguments
            convertFlat(arg1, arg2, arg3, arg4, self, arg5, arg6, arg7, arg8, arg9)

        elif (self.function == convertAverage):

            arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8 = self.arguments
            convertAverage(arg1, arg2, arg3, self, arg4, arg5, arg6, arg7, arg8)
        
        return


class GUI(QMainWindow):
    '''
        Main GUI class
    '''
    def __init__(self):

        '''
            Initializes most basic object and sets default values for parameters
        '''
        super().__init__()
        self.initUI()

        #path to pdf
        self.path = None
        #masks for flat elimination algorithm
        self.conditionLower = np.array([255, 255, 255])
        self.conditionUpper = np.array([100, 100, 100])
        #batch size
        self.batchSize = 5
        #pages to work on -> unfinished so set to always work on full file
        self.pages = [0]
        #color to use when replacing pixels
        self.color = np.array([255, 255, 255])
        #default output name
        self.outName = "temporary"
        #not existing bounding box
        self.boundingBox = [0]

        self.DEBUG = True
        
    def initUI(self):               
        '''
            UI initialization
        '''
        #set size and center
        self.setFixedSize(370, 350)
        self.center()
        
        #create all butons for menu and assign them functions
        self.btn1 = QPushButton('Load PDF', self)
        self.btn1.clicked.connect(self.getFilePath)
        self.btn1.setToolTip('Choose pdf file to work with')
        self.btn1.resize(100, 50)
        self.btn1.move(25, 25) 

        self.btn2 = QPushButton('Set Config', self)
        self.btn2.clicked.connect(self.initConfigForm)
        self.btn2.setToolTip('Configure settings')
        self.btn2.resize(100, 50)
        self.btn2.move(25, 80) 
        
        self.btn3 = QPushButton('Create\nBounding Box', self)
        self.btn3.clicked.connect(self.createBoundingBox)
        self.btn3.setToolTip('Create box limiting area of change')
        self.btn3.resize(100, 50)
        self.btn3.move(135, 25) 

        self.btn4 = QPushButton('Generate Average', self)
        self.btn4.clicked.connect(self.getAverageEstimateWrapper)
        self.btn4.setToolTip('Estimate watermark by averaging over pages')
        self.btn4.resize(100, 50)
        self.btn4.move(135, 80) 

        self.btn5 = QPushButton('Flat Elimination', self)
        self.btn5.clicked.connect(self.convertFlatWrapper)
        self.btn5.setToolTip('Replace all RGB values between set values and replace them with color')
        self.btn5.resize(100, 50)
        self.btn5.move(245, 25) 

        self.btn6 = QPushButton('Average\nElimination', self)
        self.btn6.clicked.connect(self.convertAverageWrapper)
        self.btn6.setToolTip('Replace all RGB values that are similar enough to averaged sample')
        self.btn6.resize(100, 50)
        self.btn6.move(245, 80) 

        #hide certain buttons untill a pdf is choosen
        self.btn3.hide()
        self.btn4.hide()
        self.btn5.hide()
        self.btn6.hide()

        #set name, logo, etc. for progress bar
        self.bar = QWidget()
        self.bar.setWindowIcon(QIcon('graphics//logo.png'))
        self.bar.setWindowTitle('Progress bar')
        self.progress = QProgressBar(self.bar)
        self.bar.move(QDesktopWidget().availableGeometry().center() - QPoint(150, 15))
        self.progress.setGeometry(0, 0, 300, 30)

        #slector for bounding box
        self.selector = QWidget()
        self.pic = QLabel(self.selector)
        
        #assign events to the correct window
        self.selector.mousePressEvent = lambda event : self.MPE(event)
        self.selector.mouseMoveEvent  = lambda event : self.MME(event)
        self.selector.mouseReleaseEvent = lambda event : self.MRE(event)
        
        #set title and logo
        self.selector.setWindowTitle('Select Bounding Box')
        self.selector.setWindowIcon(QIcon('graphics//logo.png'))

        #create rubber band for selector
        self.selection = QRubberBand(QRubberBand.Rectangle, self.pic)
        
        #set project logo in the menu
        logo = QLabel(self)
        logo.resize(200, 200)
        logo.setPixmap(QPixmap("graphics//logo.png"))
        logo.move(85, 130)

        #set title and logo for main windows and finish initialization
        self.setWindowIcon(QIcon('graphics//logo.png'))
        self.setWindowTitle('PDF Purifico')    
        self.show()

        return
        

    def pageForm(self):
        '''
            Unfinished form for retrieving arbitrary start and finish pages
        '''
        #setup widget
        self.pageForm = QWidget()
        self.pageForm.resize(600, 100)

        #set label
        label = QLabel(self.pageForm)
        label.setText("Set first and last page")
        label.move(15, 15)

        #set input fields
        self.firstP = QLineEdit(self.pageForm)
        self.firstP.move(180, 15)

        self.lastP = QLineEdit(self.pageForm)
        self.lastP.move(330, 15)

        #create send button
        self.formPageButton = QPushButton('Set pages', self.pageForm)
        self.formPageButton.clicked.connect(self.setPages)
        self.formPageButton.move(480, 15)

        self.pageForm.show()
        return


    def setPages(self):
        '''
            validate input and save it
        '''
        
        firstP = int(self.firstP.text())
        lastP = int(self.lastP.text())

        #validate
        if (firstP > 0) and (lastP > 0) and (lastP >= firstP):
            self.pages = [firstP, lastP]

        self.waitForPages = False

        #hide form once done
        self.pageForm.hide()

        return



    def initConfigForm(self):
        '''
            Create form forconfiguration changes
        '''

        #create base widget
        self.form = QWidget()
        self.form.resize(500, 350)

        #Creates labels and input fields for all the data
        label = QLabel(self.form)
        label.setText("R value from RGB (min - max)")
        label.move(15, 15)

        label = QLabel(self.form)
        label.setText("G value from RGB (min - max)")
        label.move(15, 45)

        label = QLabel(self.form)
        label.setText("B value from RGB (min - max)")
        label.move(15, 75)


        self.minR = QLineEdit(self.form)
        self.minR.move(180, 15)
        self.maxR = QLineEdit(self.form)
        self.maxR.move(330, 15)

        self.minG = QLineEdit(self.form)
        self.minG.move(180, 45)
        self.maxG = QLineEdit(self.form)
        self.maxG.move(330, 45)

        self.minB = QLineEdit(self.form)
        self.minB.move(180, 75)
        self.maxB = QLineEdit(self.form)
        self.maxB.move(330, 75)


        label = QLabel(self.form)
        label.setText("R value from RGB to set")
        label.move(15, 105)

        label = QLabel(self.form)
        label.setText("G value from RGB to set")
        label.move(15, 135)

        label = QLabel(self.form)
        label.setText("B value from RGB to set")
        label.move(15, 165)

        self.colorR = QLineEdit(self.form)
        self.colorR.move(180, 105)

        self.colorG = QLineEdit(self.form)
        self.colorG.move(180, 135)

        self.colorB = QLineEdit(self.form)
        self.colorB.move(180, 165)

        label = QLabel(self.form)
        label.setText("Size of batches to read to RAM")
        label.move(15, 195)

        self.batchS = QLineEdit(self.form)
        self.batchS.move(180, 195)

        label = QLabel(self.form)
        label.setText("Name for new file")
        label.move(15, 225)

        self.name = QLineEdit(self.form)
        self.name.move(180, 225)

        #button to send
        self.formButton = QPushButton('Save Config', self.form)
        self.formButton.clicked.connect(self.setConfig)
        self.formButton.move(330, 135)
        self.formButton.resize(135, 50)

        #set name and logo
        self.form.setWindowTitle("Config")
        self.form.setWindowIcon(QIcon('graphics//logo.png'))
        self.form.show()
        return


    def setConfig(self):
        '''
            validate and set data from config form
        '''
        try:
            #retrieve all the data and cast to correct type
            minR = int(self.minR.text())
            minG = int(self.minG.text())
            minB = int(self.minB.text())

            maxR = int(self.maxR.text())
            maxG = int(self.maxG.text())
            maxB = int(self.maxB.text())

            colorR = int(self.colorR.text())
            colorG = int(self.colorG.text())
            colorB = int(self.colorB.text())

            batchS = int(self.batchS.text())

            self.outName = self.name.text()

            #validate and save
            if (0 <= minR <= 255) and (0 <= minG <= 255) and (0 <= minB <= 255):
                self.conditionUpper = np.array([minR, minG, minB])

            if (0 <= maxR <= 255) and (0 <= maxG <= 255) and (0 <= maxB <= 255):
                self.conditionUpper = np.array([maxR, maxG, maxB])

            if (0 <= colorR <= 255) and (0 <= colorG <= 255) and (0 <= colorB <= 255):
                self.conditionUpper = np.array([colorR, colorG, colorB])

            if (batchS > 0):
                self.batchSize = batchS

            self.form.hide()

        except:
            #in case of error
            QMessageBox.question(self, 'Error', "Something broke", QMessageBox.Yes)
            self.form.hide()


        return

    def onCountChanged(self, value):
        '''
            For updating progress bar
        '''
        self.progress.setValue(value)
        return



    def getFilePath(self):
        '''
            Get path to pdf file
        '''
        w = QWidget()
        filename = QFileDialog.getOpenFileName(w, 'Select PDF file')
        self.path = filename[0]

        #since we got a pdf now we can enable the other buttons
        self.btn3.show()
        self.btn4.show()
        self.btn5.show()
        self.btn6.show()
        return

    def convertFlatWrapper(self):
        '''
            Wrapper for convertFlat function
        '''

        #set pages correctly
        if (len(self.pages) == 2):
            pagesToClean = self.pages[1] - self.pages[0] + 1
            pageOffset = self.pages[0] - 1
        elif (len(self.pages) == 1):
            pagesToClean = self.pages[0]
            pageOffset = 0
        else:
            QMessageBox.about(self,"Error", "Pages set incorrectly")
            return

        #prepare update bar send data to thread and start it
        self.bar.show()
        self.calc = External()
        self.calc.setFunction(convertFlat, (self.path, self.conditionLower, self.conditionUpper, self.batchSize, self.outName, pagesToClean, pageOffset, self.color, self.boundingBox))

        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()

        return

    def getAverageEstimateWrapper(self):
        '''
            Wrapper for getAverageEstimate
        '''

        #set pages correctly
        if (len(self.pages) == 2):
            pagesToClean = self.pages[1] - self.pages[0] + 1
            pageOffset = self.pages[0] - 1
        elif (len(self.pages) == 1):
            pagesToClean = self.pages[0]
            pageOffset = 0
        else:
            QMessageBox.about(self,"Error", "Pages set incorrectly")
            return

        #prepare update bar send data to thread and start it
        self.bar.show()
        self.calc = External()
        self.calc.setFunction(getAverageEstimate, (self.path, self.batchSize, self.outName, pagesToClean, pageOffset))

        self.calc.countChanged.connect(self.onCountChanged)

        self.calc.start()

        return

    def convertAverageWrapper(self):
        '''
            Wrapper for converAverage
        '''
        if (len(self.pages) == 2):
            pagesToClean = self.pages[1] - self.pages[0] + 1
            pageOffset = self.pages[0] - 1
        elif (len(self.pages) == 1):
            pagesToClean = self.pages[0]
            pageOffset = 0
        else:
            QMessageBox.about(self,"Error", "Pages set incorrectly")


        #slect averaged file touse as filter for pdf
        w = QWidget()
        filename = QFileDialog.getOpenFileName(w, 'Select averaged file to filter pdf')

        #prepare update bar send data to thread and start it
        self.bar.show()
        self.calc = External()
        self.calc.setFunction(convertAverage, (self.path, filename[0], self.batchSize, self.outName, pagesToClean, pageOffset, self.color, self.boundingBox))
        self.calc.countChanged.connect(self.onCountChanged)

        self.calc.start()

        return

    def center(self):
        '''
            method for centering
        '''
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        return
        
        
    def closeEvent(self, event):
        '''
            Confirmation when closing software
        '''
        reply = QMessageBox.question(self, 'Message', "Are you sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

        return
        
    
        
    def MPE(self, event):
        '''
            Mouse is pressed. If selection is visible either set dragging mode (if close to border) or hide selection.
            If selection is not visible make it visible and start at this point.
        '''

        if event.button() == Qt.LeftButton:

            position = QPoint(event.pos())

            if (self.DEBUG):
                print("Start coords:", position.x(), position.y())

            #set coords for later
            self.start_x = position.x()
            self.start_y = position.y()
            
            if self.selection.isVisible():
                # visible selection
                if (self.upper_left - position).manhattanLength() < 20:
                    # close to upper left corner, drag it
                    self.mode = "drag_upper_left"
                elif (self.lower_right - position).manhattanLength() < 20:
                    # close to lower right corner, drag it
                    self.mode = "drag_lower_right"
                else:
                    # clicked somewhere else, hide selection
                    self.selection.hide()
            else:
                # no visible selection, start new selection
                self.upper_left = position
                self.lower_right = position
                self.mode = "drag_lower_right"
                self.selection.show()

        return

    def MME(self, event):
        '''
            Mouse moved. If selection is visible, drag it according to drag mode.
        '''

        if self.selection.isVisible():
            # visible selection
            if self.mode is "drag_lower_right":
                self.lower_right = QPoint(event.pos())
            elif self.mode is "drag_upper_left":
                self.upper_left = QPoint(event.pos())
            # update geometry
            self.selection.setGeometry(QRect(self.upper_left, self.lower_right).normalized())

        return
        
    def MRE(self, event):
        '''
            Mouse is released. Hide selector, selection and save propertly transformed coords 
        '''
        if event.button() == Qt.LeftButton:

            position = QPoint(event.pos())

            if (self.DEBUG):
                print("Stop coords:", position.x(), position.y())
            
            #save final position
            self.stop_x = position.x()
            self.stop_y = position.y()
            
            if self.selection.isVisible():
                self.selection.hide()
                self.selector.hide()
        
            im = convert_from_path(self.path, fmt='jpeg', first_page=1, last_page=1)[0]
            width, height = im.size

            if (self.DEBUG):
                orig = np.array(im)
                color = np.array([100, 100, 200])
                

            pts = np.zeros((2,2))

            #set coordinates for bounding box
            pts[0][0] = int(self.start_x / self.scaled_im_width * width)
            pts[0][1] = int(self.start_y / self.scaled_im_height * height)
            pts[1][0] = int(self.stop_x / self.scaled_im_width * width)
            pts[1][1] = int(self.stop_y / self.scaled_im_height * height)

            self.boundingBox = pts

            if(self.DEBUG):

                drawLines(orig, pts.astype(int), color, 3)
                im = Image.fromarray(orig)
                im.save('temp\\sample.jpeg')
                im.show()

        return     
        
    def createBoundingBox(self):
        '''
            Creates bounding box to be used in one of the enxt algorithms
        '''
        im = convert_from_path(self.path, fmt='jpeg', first_page=1, last_page=1)[0]

        im.save("temp\\temp.jpg")

        #get original sizes
        width, height = im.size
        
        im.close()
        
        
        geo = QDesktopWidget().availableGeometry()
        
        #transform for convinience
        if (geo.height() < height):
            width *=  (geo.height()/height) * 0.9
            height = geo.height() * 0.9

        #save for reversing later
        self.scaled_im_width = int(width)
        self.scaled_im_height = int(height)
            
        
        self.pic.setGeometry(0 , 0, width, height)
        self.selector.setFixedSize(width, height)

        #load picture
        self.pic.setPixmap(QPixmap("temp\\temp.jpg").scaledToHeight(height))

        qr = self.selector.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.selector.move(qr.topLeft())
        
        self.selector.show()

        return
        
        
        
if __name__ == '__main__':
    '''
        main function
    '''
    app = QApplication(sys.argv)
    guiu = GUI()
    sys.exit(app.exec_())