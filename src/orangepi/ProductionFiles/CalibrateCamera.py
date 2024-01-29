import numpy as np
import cv2 as cv
import glob
from threading import Thread
import json


class myWebcamVideoStream:
  def __init__(self, src=0):
    # initialize the video camera stream and read the 
    # first frame from the stream
    self.stream = cv.VideoCapture(src) 
    (self.grabbed, self.frame) = self.stream.read()

    # flag to stop the thread

    self.stopped = False

  def start(self):
    # start the thread to read frames
    Thread(target=self.update, args=()).start()
    return self

  def update(self):

    while True:
       # have we been told to stop?  If so, get out of here
       if self.stopped:
           return

       # otherwise, get another frame
       (self.grabbed, self.frame) = self.stream.read()

  def read(self):
      # return the most recent frame
      return self.frame

  def stop(self):
      # signal thread to end
      self.stopped = True
      return

#function that writes calibration output to json file 
def write_to_json_file(filename, var1, var2, var3, var4):
    data = {
        "mtx": var1,
        "dist": var2,
        "w": var3,
        "h": var4
    }

    with open(filename, 'w') as json_file:
        json.dump(data, json_file)


#I think this plots the locations on the screen?
def plotPoint(image, center, color):
    center = (int(center[0]), int(center[1]))
    image = cv.line(image,
                     (center[0] - 5, center[1]),
                     (center[0] + 5, center[1]),
                     color,
                     3)
    image = cv.line(image,
                     (center[0], center[1] - 5),
                     (center[0], center[1] + 5),
                     color,
                     3)
    return image

# main program
#configs the detector
vs = myWebcamVideoStream(0).start() 


# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((6*7,3), np.float32)
objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)
# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.
ret = False
while ret == False:
    img = vs.read()
    print("Present your chessboard")
    #cv.putText(img, "Show Me A ChessBoard!", (35,475), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
    #cv.imshow('img', img)
    #cv.waitKey(1)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # Find the chess board corners
    ret, corners = cv.findChessboardCorners(gray, (7,6), None)
    # If found, add object points, image points (after refining them)
objpoints.append(objp)
corners2 = cv.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
imgpoints.append(corners2)
# Draw and display the corners
cv.drawChessboardCorners(img, (7,6), corners2, ret)
ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
# undistort
h,  w = img.shape[:2]
write_to_json_file("cal.json", mtx, dist, w, h)
#cv.putText(img, "DONE!", (100,250), cv.FONT_HERSHEY_SIMPLEX, 5.0, (0, 0, 255), 2)
#cv.imshow('img', img)
#cv.waitKey(500)
#cv.destroyAllWindows()
print("Done with calibration!")
mean_error = 0
for i in range(len(objpoints)):
    imgpoints2, _ = cv.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
    error = cv.norm(imgpoints[i], imgpoints2, cv.NORM_L2)/len(imgpoints2)
    mean_error += error
print( "total error: {}".format(mean_error/len(objpoints)) )
vs.stop()
exit()
