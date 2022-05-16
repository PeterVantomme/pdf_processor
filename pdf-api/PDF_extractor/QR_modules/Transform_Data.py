# Process input-pdf to extract QR-code and other pages
## Imports & Globals
from ..Config import Paths
import numpy as np
import fitz

DATA_DIRECTORY = Paths.pdf_path.value

## Helper zorgt ervoor dat pdf image gelezen kan worden door cv2
def pix2np(pix):
    from cv2 import resize, cvtColor, COLOR_BGR2RGB 
    im = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    im = np.ascontiguousarray(im[...])  # rgb to bgr
    img = resize(cvtColor(im,COLOR_BGR2RGB),(im.shape[1]//1,im.shape[0]//1))
    del im
    return img

## Transform methods
### Transforming the first page to QR-png
def transform_pdf_to_png(pdf):
    pix = fitz.Pixmap(pdf, pdf.get_page_images(0)[0][0])  
    img = pix2np(pix)
    del(pix)
    return img

### Using opencv transformations to make QR-code more readable for system    
def transform_png(image):
    from cv2 import COLOR_BGR2HSV, COLOR_RGB2GRAY, COLOR_HSV2RGB, COLOR_RGB2BGR, COLOR_BGR2GRAY, COLOR_GRAY2RGB, MORPH_CLOSE, MORPH_RECT, MORPH_CROSS, MORPH_OPEN, THRESH_BINARY
    from cv2 import cvtColor, filter2D, getStructuringElement, threshold, morphologyEx
    #Kernels
    kernel = np.array([[0, 0, 0],
                       [0, 1, 0],
                       [0, 0, 0]])
    filter_kernel = np.array([[0, -2, 0],
                              [-2, 12, -2],
                              [0, -2, 0]])
    sharpening_kernel = np.array([[-1, -1, -1],
                                  [-1, 30, -1],
                                  [-1, -1, -1]])
    cross_kernel= getStructuringElement(MORPH_CROSS,(5,5))
    rect_kernel =getStructuringElement(MORPH_RECT, (2,2))

    #Transformations
    image = filter2D(src=cvtColor(image, COLOR_BGR2HSV), ddepth=-1, kernel=kernel)
    image = threshold(image,200,255,THRESH_BINARY)[1]
    image = threshold(cvtColor(image, COLOR_HSV2RGB), 200, 255, THRESH_BINARY)[1]
    image = morphologyEx(cvtColor(image, COLOR_RGB2GRAY), MORPH_CLOSE, cross_kernel)
    
    image = filter2D(src=image, ddepth=-1, kernel=filter_kernel)
    image = morphologyEx(cvtColor(cvtColor(image, COLOR_RGB2BGR), COLOR_BGR2GRAY), MORPH_OPEN, rect_kernel, iterations=4) 
    image = morphologyEx(morphologyEx(image, MORPH_CLOSE, rect_kernel, iterations=4) , MORPH_OPEN, rect_kernel, iterations=4) 
    image = threshold(image, 192, 255, THRESH_BINARY)[1]
    image = cvtColor(filter2D(src=image, ddepth=5, kernel=sharpening_kernel), COLOR_GRAY2RGB)

    return image

## Remove first page
def remove_first_page(file):
    if file.pageCount > 1:
        pages = [p for p in range(file.page_count) if p>0]
        file.select(pages) 
    return file

## Main method (called by API main.py file)
def transform_file(file):
    try:
        pdf = fitz.open(f'{DATA_DIRECTORY}/{file}')
        image = transform_pdf_to_png(pdf)
        clean_image = transform_png(image)
        pdf_pages = remove_first_page(pdf)
        pdf_pages.saveIncr()
        pdf_pages.close()
        del pdf, image, pdf_pages
        import gc
        gc.collect()
        return clean_image
    except fitz.FileDataError:
        raise fitz.FileDataError
    except FileNotFoundError:
        raise FileNotFoundError
            