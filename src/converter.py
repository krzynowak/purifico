from pdf2image import convert_from_path
import img2pdf
from pdf2image.pdf2image import _page_count
import numpy as np
from PIL import Image
from PyPDF3 import PdfFileMerger




def convertFlat(filename, conditionLower, conditionUpper, batchSize, progressBar, outName="test", pages=0, pageOffset=0, color=np.array([255, 255, 255]), boundingBox=0):
    '''
        Iterate over selected pages of a pdf and change the color of all pixels withing a given range
    '''
    #save info of where to start
    currentPageCounter = pageOffset
    
    #get merger instance for outpdf creation
    pdfMerger = PdfFileMerger()

    #if pages weren't set we iterate over all
    if pages == 0:
        pages = _page_count(filename)

    #variable for progress bar
    totalPages = pages


    X_Start, Y_Start, X_Len, Y_Len = 0, 0, 0, 0

    #prepare coordinates for bounding box if it was created
    if (len(boundingBox) == 2):
        X_Start, Y_Start, X_Len, Y_Len = ConverCoordinates(boundingBox)

    #work until nothing's left
    while (pages > 0):

        #use either batch size or w/e is left
        if(pages > batchSize):
            pagesToConvert = batchSize
        else:
            pagesToConvert = pages

        #read pages
        pageBuffer = convert_from_path(filename, fmt='jpeg', first_page=currentPageCounter + 1, last_page=currentPageCounter + pagesToConvert + 1)

        for case in np.arange(pagesToConvert):

            #get current page and convert to numpy array
            im = pageBuffer[case]
            fullPage = np.array(im)

            #deal with potential bounding box
            if (len(boundingBox) == 2):
                editedPage = fullPage.copy()[Y_Start : Y_Start + Y_Len, X_Start : X_Start + X_Len]
            else:
                editedPage = fullPage

            #reshape for condition check
            iterOrig = editedPage.reshape((editedPage.shape[0] * editedPage.shape[1], 3))

            #prepare masks
            maskUpper = np.all(conditionUpper <= iterOrig, axis=1)
            maskLower = np.all(conditionLower >= iterOrig, axis=1)

            #update all pixels that met condition
            mask = np.logical_and(maskUpper, maskLower)
            iterOrig[mask] = color

            #restore shape
            editedPage = iterOrig.reshape((editedPage.shape[0],editedPage.shape[1], 3))
            
            #deal with potential bounding box
            if (len(boundingBox) == 2):
                fullPage[Y_Start : Y_Start + Y_Len, X_Start : X_Start + X_Len] = editedPage

            #resturn to previous format
            im = Image.fromarray(fullPage)

            #ugly code here due to time constraints/other priorities
            im.save('temp\\temp.jpeg')

            with open("temp\\tmp.pdf","wb+") as f:
                f.write(img2pdf.convert('temp\\temp.jpeg'))
                
            with open("temp\\tmp.pdf","rb") as f:
                pdfMerger.append(f)

            #update progress bar
            progressBar.countChanged.emit(int(((currentPageCounter + 1) / totalPages) * 100))

            currentPageCounter += 1

        #update loop termination var
        pages -= pagesToConvert

    #merge and save finished file
    with open('result\\' + outName + ".pdf", 'wb') as fout:
        pdfMerger.write(fout)

    pdfMerger.close()

def getAverageEstimate(filename, batchSize, progressBar, outName="test", pages=0, pageOffset=0):
    '''
        Create estimated watermark by averaging over all pages in the document
    '''
    #save info of where to start
    currentPageCounter = pageOffset
    
    #if pages weren't set we iterate over all
    if pages == 0:
        pages = _page_count(filename)

    totalPages = pages 

    #get zeroed out array for average calculation
    firstPage = convert_from_path(filename, fmt='jpeg', first_page=1, last_page=1)[0]
    averaged = np.zeros_like(np.array(firstPage)).astype('uint64')
    #address batch size
    while (pages > 0):
        if(pages > batchSize):
            pagesToConvert = batchSize
        else:
            pagesToConvert = pages

        #read a few pages to buffer
        pageBuffer = convert_from_path(filename, fmt='jpeg', first_page=currentPageCounter + 1, last_page=currentPageCounter + pagesToConvert + 1)

        for case in np.arange(pagesToConvert):

            #get current page and convert to numpy array
            im = pageBuffer[case]
            fullPage = np.array(im)

            #add current page
            averaged = np.add(averaged, fullPage)

            #update progress bar
            progressBar.countChanged.emit(int(((currentPageCounter + 1) / totalPages) * 100))


            currentPageCounter += 1

        #update loop termination var
        pages -= pagesToConvert

    #calculate average and save it
    averaged = averaged / (currentPageCounter + 1)
    im = Image.fromarray(averaged.astype('uint8'))
    im.save("estimated_watermarks\\" + outName + '.jpeg')
    return


def convertAverage(filename, filter, batchSize, progressBar, outName="test", pages=0, pageOffset=0, color=np.array([255, 255, 255]), boundingBox=0):

    #save info of where to start
    currentPageCounter = pageOffset
    
    #get merger instance for outpdf creation
    pdfMerger = PdfFileMerger()

    #if pages weren't set we iterate over all
    if pages == 0:
        pages = _page_count(filename)

#variable for progress bar
    totalPages = pages

    #read average calculated beforehand
    averaged = np.array(Image.open(filter))

    X_Start, Y_Start, X_Len, Y_Len = 0, 0, 0, 0

    #prepare coordinates for bounding box if it was created
    if (len(boundingBox) == 2):
        X_Start, Y_Start, X_Len, Y_Len = ConverCoordinates(boundingBox)
        averaged = averaged[Y_Start : Y_Start + Y_Len, X_Start : X_Start + X_Len]

    #set correct shape
    averaged = averaged.reshape((averaged.shape[0] * averaged.shape[1], 3))

#work until nothing's left
    while (pages > 0):

        #use either batch size or w/e is left
        if(pages > batchSize):
            pagesToConvert = batchSize
        else:
            pagesToConvert = pages

        #read pages
        pageBuffer = convert_from_path(filename, fmt='jpeg', first_page=currentPageCounter + 1, last_page=currentPageCounter + pagesToConvert + 1)

        for case in np.arange(pagesToConvert):

            #get current page and convert to numpy array
            im = pageBuffer[case]
            fullPage = np.array(im)

        #deal with potential bounding box
            if (len(boundingBox) == 2):
                editedPage = fullPage.copy()[Y_Start : Y_Start + Y_Len, X_Start : X_Start + X_Len]

            else:
                editedPage = fullPage

            #reshape for condition check
            iterOrig = editedPage.reshape((editedPage.shape[0] * editedPage.shape[1], 3))\

            #calculate difference measure and aply to page
            diff = np.sqrt(np.power(np.sum(np.subtract(iterOrig, averaged), axis=1),2))
            mask = diff < 150
            iterOrig[mask] = color

            #restore shape
            editedPage = iterOrig.reshape((editedPage.shape[0],editedPage.shape[1], 3))

            #deal with potential bounding box
            if (len(boundingBox) == 2):
                fullPage[Y_Start : Y_Start + Y_Len, X_Start : X_Start + X_Len] = editedPage

            im = Image.fromarray(fullPage)
            
            #ugly code here due to time constraints/other priorities
            im.save('temp\\temp.jpeg')
            with open("temp\\tmp.pdf","wb+") as f:
                f.write(img2pdf.convert('temp\\temp.jpeg'))
                
            with open("temp\\tmp.pdf","rb") as f:
                pdfMerger.append(f)

            #update progress bar
            progressBar.countChanged.emit(int(((currentPageCounter + 1) / totalPages) * 100))

            currentPageCounter += 1

        #update loop termination var
        pages -= pagesToConvert

    #merge and save finished file
    with open('result\\' + outName + ".pdf", 'wb') as fout:
        pdfMerger.write(fout)

    pdfMerger.close()



def ConverCoordinates(Points):
    '''
        Converts raw coordinates into usefull data
    '''
    X_Start = int(min(Points[0][0], Points[1][0]))
    Y_Start = int(min(Points[0][1], Points[1][1]))
    X_Len = int(abs(Points[0][0] - Points[1][0]))
    Y_Len = int(abs(Points[0][1] - Points[1][1]))

    return (X_Start, Y_Start, X_Len, Y_Len)



def drawLines(Image, Points, Color, Thickness = 5):
    '''
        Left over function from testing -> might be still usefull for further developement
        Draws bounding box for provided coordinates
    '''
    
    (X_Start, Y_Start, X_Len, Y_Len) = ConverCoordinates(Points)
    
    #Draw diagonal above
    Image[Y_Start : Y_Start+Thickness, X_Start : X_Start+X_Len] = Color
    
    #Draw diagonal below
    Image[Y_Start + Y_Len - Thickness: Y_Start + Y_Len , X_Start : X_Start+X_Len] = Color
    
    #Draw vertical left
    Image[Y_Start : Y_Start + Y_Len , X_Start : X_Start+Thickness] = Color
    
    #Draw vertical right
    Image[Y_Start : Y_Start + Y_Len , X_Start+X_Len : X_Start+X_Len+Thickness] = Color

    return