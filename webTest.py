import cv2
import numpy as np
import math
import itertools
import requests
import warnings
import time

babs = 0
babsy = 0
URL = {"xy": "http://192.168.2.143/xy"}


def colorMask(frame):
    pass

def erode(frame):
    kernel = np.ones((5, 5), np.uint8)
    erosion = cv2.erode(frame, kernel, iterations=2)
    return erosion


def dilate(frame):
    kernel = np.ones((10, 10), np.uint8)
    dilation = cv2.dilate(frame, kernel, iterations=3)
    return dilation


def getDistance(coordinates1, coordinates2):
    # sqrt (x^2 + y^2)
    return math.sqrt((coordinates2[0] - coordinates1[0])**2 + (coordinates2[1] - coordinates1[1])**2)


def getPointAverage(coordinates1, coordinates2):
    return [int((coordinates1[0] + coordinates2[0]) / 2), int((coordinates1[1] + coordinates2[1]) / 2)]


def getProjectedY(BaseCoordinate, theta):
    # 320 is the midpoint of the camera***
    # note we work in camera pixels
    global babsy
    dist = 800  # 30 cm irlq
    deltaX = BaseCoordinate[0] - 318   # positive if farther than 320 -> pixel value.
    hShift = BaseCoordinate[1]  # be careful

    # atan takes in radians!
    projectedY = math.tan(theta) * (dist + deltaX) + hShift
    jingy = projectedY * 0.0264
    if abs(babsy - jingy) <= 3:
        return babsy
    babsy = jingy
    return  jingy # scale to cm


def getProjectedX(BaseCoordinate, tipCoordinate, distance):
    # define camera distance X = 45 cm
    global babs
    dist = 800  # 30 cm irl
    deltaX = BaseCoordinate[0] - 318   # positive if farther than 320
    armLength = 420     # this is 30 cm irl at 30 cm away!
    armLengthProjection = getDistance(BaseCoordinate, tipCoordinate) - 30

    if armLengthProjection > 420:
        print("babs eas here")
        return babs
    phi = math.acos(armLengthProjection / armLength)
    projectedX = math.tan(phi) * (dist + deltaX)
    jing = projectedX * 0.07
    if abs(babs - jing) <= 3:
        return babs
    babs = jing
    return jing


def simplify_contour(contour, n_corners=4):
    '''
    Binary searches best `epsilon` value to force contour
        approximation contain exactly `n_corners` points.

    :param contour: OpenCV2 contour.
    :param n_corners: Number of corners (points) the contour must contain.

    :returns: Simplified contour in successful case. Otherwise returns initial contour.
    '''
    n_iter, max_iter = 0, 100
    lb, ub = 0., 1.

    while True:
        n_iter += 1
        if n_iter > max_iter:
            return contour

        k = (lb + ub)/2.
        eps = k*cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, eps, True)

        if len(approx) > n_corners:
            lb = (lb + ub)/2.
        elif len(approx) < n_corners:
            ub = (lb + ub)/2.
        else:
            return approx


cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

globalLineCoord1 = np.array([100, 200])
globalLineCoord2 = np.array([500, 200])
globalAngle = 0

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)

    # shape is 480 x 640
    # print(frame.shape)

    width = int(cap.get(3))
    height = int(cap.get(4))

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # define range of red color in HSV
    lower_blue = np.array([90, 130, 0])
    upper_blue = np.array([125, 255, 255])

    # Threshold the HSV image to get only red colors
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Bitwise-AND mask and original image
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # binary black/white filter
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    (thresh, blackWhite) = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    eroded = erode(blackWhite)
    dilated = dilate(eroded)
    blur = cv2.medianBlur(dilated, 5)

    contours, hierarchy = cv2.findContours(blur, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # print(len(contours))

    # Iterate through each contour
    # for c in contours:
    #     x, y, w, h = cv2.boundingRect(c)
    #     cv2.rectangle(blur, (x, y), (x + w, y + h), (255, 0, 255), 2)
    #     cv2.imshow('Bounding Rectangle', blur)
    # cv2.waitKey(0)

    # Iterate through each contour and compute the approx contour
    allContours = []    # this exists to increase robustness: takes all contours that exist
                        # and their points. then take overall max. This allows 1 line to exist
                        # even with segmentations in the line.

    for c in contours:
        accuracy = 0.03 * cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, accuracy, True)

        # print(approx)

        for item in approx:
            for thing in item:
                allContours.append(thing)

        cv2.drawContours(frame, [approx], 0, (255, 255, 0), 2)

    # print("all counters: ", end='')
    # print(allContours)

    # max distance between combinations -> return set of points.
    combs = list(itertools.combinations(allContours, 2))
    # print("combs: ", end='')
    # print(list(combs))
    distanceList = []   # should contain a (distance, index).

    if len(combs) > 1:
        for i, comb in enumerate(combs):
            coordinate1 = comb[0]  # [i][0][0] gets to [[coordinates]]
            coordinate2 = comb[1]  # [i][0][0] gets to [[coordinates]]

            distanceList.append((getDistance(coordinate1, coordinate2), i))

        if len(distanceList) >= 1:
            maxIndex = max(distanceList)[1]

            lineCoord1 = combs[maxIndex][0]
            lineCoord2 = combs[maxIndex][1]

            if lineCoord1[0] < lineCoord2[0]:
                globalLineCoord1 = lineCoord1
                globalLineCoord2 = lineCoord2
            else:
                globalLineCoord1 = lineCoord2
                globalLineCoord2 = lineCoord1

            cv2.line(frame, lineCoord1, lineCoord2, (255, 255, 255), 3)
            cv2.circle(frame, globalLineCoord1, 3, (255, 0, 0), 3)
            cv2.circle(frame, globalLineCoord2, 3, (0, 255, 0), 3)

            # print("coordinate 1: ", end='')
            # print(lineCoord1)
            # print("coordinate 2: ", end='')
            # print(lineCoord2)
            # print()
    else:
        print("nothing to show")

    cv2.imshow('Approx Poly DP', frame)

    cv2.imshow('blur', blur)
    cv2.imshow("frame", blackWhite)

    # print(globalLineCoord1)
    # print(globalLineCoord2)
    # print()

    # note that it starts out at 0, 0.
    angleRatio = math.fabs((globalLineCoord2[1] - globalLineCoord1[1]) / (globalLineCoord2[0] - globalLineCoord1[0]))
    globalAngle = math.fabs(math.atan(angleRatio))

    projectedX = getProjectedX(globalLineCoord2, globalLineCoord1, 0)
    projectedY = getProjectedY(globalLineCoord2, globalAngle)

    data = {"x": float(projectedX), "y": float(projectedY)}
    print(data)
    r = requests.post(URL["xy"], json=data)

    print(f'projected X: {projectedX}, projected Y: {projectedY}')
    # time.sleep(0.2)

    if r.ok:
        print("POST successful\n")
    else:
        warnings.warn("POST unsuccessful\n")

    # print("global angle: ", end='')
    # print(globalAngle)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
