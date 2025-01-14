from threading import Thread
import ntcore
import cv2
import numpy as np
import apriltag
import time
import sys
import imutils
from scipy.spatial.transform import Rotation
import random
import socket

class myWebcamVideoStream:
  
  global testmode, myStrPub, Livemode
  testmode = False
  Livemode = True

  print(sys.argv[1:])
  if sys.argv[1:] == ['ehB-test']:
        testmode = True
        Livemode = False
  elif (sys.argv[1:] == ['--not-pi']):
      Livemode = False
  try:
    with open('/sys/firmware/devicetree/base/model', 'r') as f:
            if "Raspberry" in f.read():
                Livemode = True
            else:
                Livemode = False
  except FileNotFoundError:
        Livemode = False
  print(testmode + Livemode)

  def __init__(self, src=0):
    
    global table, tab2

    #init network tables
    TEAM = 5607
    if testmode == False:
        ntinst = ntcore.NetworkTableInstance.getDefault()
    table = ntinst.getTable("PiDetector")
    tab2 = ntinst.getTable("UnicornHat")
    ntinst.startClient4("pi1 vision client")
    ntinst.setServer("10.56.7.2")
    
    #Find the camera and
    # initialize the video camera stream and read the 
    # first frame from the stream
    self.stream = cv2.VideoCapture(src) 
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

#reads the calibration data
def read_from_txt_file(filename):
    try:
        with open(filename, 'r') as txt_file:
            lines = txt_file.readlines()
            if len(lines) >= 4:
                var1 = lines[0].strip()
                var2 = lines[1].strip()
                var3 = lines[2].strip()
                var4 = lines[3].strip()
                return var1, var2, var3, var4
            else:
                #print(f"File '{filename}' does not contain enough lines.")
                return None
    except FileNotFoundError:
        #print(f"File '{filename}' not found.")
        return None


#I think this plots the locations on the screen?
def plotPoint(image, center, color):
    center = (int(center[0]), int(center[1]))
    image = cv2.line(image,
                     (center[0] - 5, center[1]),
                     (center[0] + 5, center[1]),
                     color,
                     3)
    image = cv2.line(image,
                     (center[0], center[1] - 5),
                     (center[0], center[1] + 5),
                     color,
                     3)
    return image

def distance_to_camera(knownWidth, focalLength, perWidth):
	# compute and return the distance from the maker to the camera
	return (float(knownWidth) * float(focalLength)) / float(perWidth)

def find_marker(image):
	# convert the image to grayscale, blur it, and detect edges
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (5, 5), 0)
	edged = cv2.Canny(gray, 35, 125)
	# find the contours in the edged image and keep the largest one;
	# we'll assume that this is our piece of paper in the image
	cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	c = max(cnts, key = cv2.contourArea)
	# compute the bounding box of the of the paper region and return it
	return cv2.minAreaRect(c)

#With love from ChatGPT
def denoise_image(image, kernel_size=(5, 5)):
    """
    Apply Gaussian blur to denoise the image.

    Parameters:
    - image: Input image (NumPy array).
    - kernel_size: Size of the Gaussian kernel (default is (5, 5)).

    Returns:
    - Denoised image.
    """
    denoised_image = cv2.GaussianBlur(image, kernel_size, 0)
    return denoised_image

def average_position_of_pixels(mat, threshold=128):
    # Threshold the image to get binary image
    _, thresh = cv2.threshold(mat, threshold, 255, cv2.THRESH_BINARY)

    # Find contours in the binary image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize variables to store total x and y coordinates
    total_x = 0
    total_y = 0

    # Iterate through each contour
    for contour in contours:
        # Calculate the centroid of the contour
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # Add the centroid coordinates to the total
            total_x += cx
            total_y += cy

    # Calculate the average position
    if len(contours) > 0:
        avg_x = total_x / len(contours)
        avg_y = total_y / len(contours)
        return int(avg_x), int(avg_y)
    else:
        return 0, 0

# main program
#configs the detector
if testmode == False:
    if Livemode == True:
        vs = myWebcamVideoStream(0).start()
    else:
        vs = myWebcamVideoStream(1).start()
options = apriltag.DetectorOptions(families="tag36h11")
detector = apriltag.Detector(options)

FRCtagSize = float(0.17) #17cm
fx, fy, cx, cy = read_from_txt_file("cal.txt")

cameraParams = float(fx), float(fy), float(cx), float(cy)
# define color the list of boundaries
if Livemode:
    socket.socket.connect(('10.56.7.12', 80))
    boundaries = [
        ([80,45,170], [100,145,255])
    ]

iteration = 0
saved = False

#Todo: Make not timed but not stupid
while testmode == False | (iteration < 3 & testmode == True):
   if testmode == False:
    frame = vs.read()
   else:
      frame = cv2.imread('test.jpg')




   if Livemode:
    #     cool = open("coolstuff.txt", "w")
    #     cool.write(color)
    #     cool.close()
    for (lower, upper) in boundaries:
        # create NumPy arrays from the boundaries
        lower = np.array(lower, dtype = "uint8")
        upper = np.array(upper, dtype = "uint8")
        # find the colors within the specified boundaries and apply
        # the mask
        mask = cv2.inRange(frame, lower, upper)
        output = cv2.bitwise_and(frame, frame, mask = mask)
        output = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
        # show the images
        output = denoise_image(output)
        avX, avY = average_position_of_pixels(output, 120)
        #print(avX, avY)
        myStrPub = table.getStringTopic("FoundRings").publish()
        myStrPub.set('{"X": avX, "Y": avY}' )
        #cv2.imshow("images", output)
        #cv2.waitKey(5)
        Val = tab2.getString("status","False")
        cool2 = open("Status.txt", "w")
        cool2.write(Val)
        cool2.close()

   #frame = cv2.undistort(img, mtx, dist, None, newcameramtx)
   grayimage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
   #cv2.imshow('frame', frame)
   #cv2.imwrite("fulmer2.jpg",frame)

   detections = detector.detect(grayimage)
   if detections:
       #print("Nothing")
       #cv2.putText(frame, "Nothing Detected", (500,500), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 255), 2)
       #cv2.imshow('frame', frame)
       #cv2.imwrite("fulmer.jpg",frame)
       #cv2.waitKey(1)
       #iterates over all tags detected
       for detect in detections:
           pos, e1,f1=detector.detection_pose( detect, cameraParams, FRCtagSize, z_sign=1)
           pos = pos[:3, :3]
           rotation = Rotation.from_matrix(pos)
           euler_angles = rotation.as_euler('xyz')
           pos = np.degrees(euler_angles)
           marker = find_marker(frame)
           distance = distance_to_camera(FRCtagSize,fx,marker[1][0])
           #apriltag._draw_pose(frame,cameraParams,FRCtagSize,pos)
           #print("POSE DATA START")
           print(pos)
           #print("distace")
           #print(distance)
           #print("POSE DATA END")
           
           if Livemode:
               tagtext = "Tag " + str(detect.tag_id)
               socket.socket.send(tagtext.encode())


           #sends the tag data named the t(str(detect.tag_id)).publish()ag_ID myStrPub =table.getStringTopic("tag1").publish()with Center, TopLeft, BottomRight Locations
           if testmode == False:
            myStrPub =table.getStringTopic(str(detect.tag_id)).publish()
            myStrPub.set('{"Center": detect.center, "TopLft": detect.corners[0], "BotRht": detect.corners[2], "Dist": distance, "XYZ": pos}' )
           #print("tag_id: %s, center: %s, corners: %s, corner.top_left: %s , corner.bottom-right: %s" % (detect.tag_id, detect.center, detect.corners[0:], detect.corners[0], detect.corners[2]))
           frame=plotPoint(frame, detect.center, (255,0,255)) #purpe center
           cornerIndex=0
           for corner in detect.corners:
               if cornerIndex== 0:
                #print("top left corner %s" %(corner[0]))
                frame=plotPoint(frame, corner, (0,0,255)) #red for top left corner
                #xord=int(corner[0])
                #yord=int(corner[1])
                org=(int(corner[0]),int(corner[1]))
                tagId=("AprilTagId %s" % (str(detect.tag_id)))
                cv2.putText(frame, tagId, org, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
               elif cornerIndex == 2:
                #print("bottom right corner %s" %(corner[0]))
                frame=plotPoint(frame, corner, (0,255,0)) #green for bottom right corner
               else:
                frame=plotPoint(frame, corner, (0,255,255)) #yellow corner
               cornerIndex+=1
       if not saved:
           #find a apriltag save the image catches programmers looking weird
           #cv2.imwrite("fulmer.jpg",frame)
           saved = True
           #print("Saved!")
       
   #cv2.imshow('frame', frame)
   #cv2.waitKey(1)
   iteration = iteration + 1
   if iteration > 50:
       iteration = 0

version =ntcore.ConnectionInfo.protocol_version
print("Exitting Code 0_o")

#Closes everything out
if testmode == False:
    vs.stop()
#cv2.destroyAllWindows()
