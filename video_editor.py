import argparse, cv2, time, datetime, keyboard
import numpy as np

def angle_between(x1,y1,x2,y2,x3,y3):
	v1_x = x1-x2
	v1_y = y1-y2
	v2_x = x3-x2
	v2_y = y3-y2
	len_v1 = np.sqrt(v1_x*v1_x + v1_y*v1_y)
	len_v2 = np.sqrt(v2_x*v2_x + v2_y*v2_y)
	v1_x_normal = v1_x / len_v1
	v1_y_normal = v1_y / len_v1 
	v2_x_normal = v2_x / len_v2
	v2_y_normal = v2_y / len_v2
	v1dotv2 = v1_x_normal*v2_x_normal + v1_y_normal*v2_y_normal
	theta_radius = np.arccos(v1dotv2)
	theta_degree = round(180.0*theta_radius/np.pi,2)
	return theta_degree

def draw_lines(event, x, y, flags, param):
	global markLine, markAngle, markLine_straight, width_c, height_c, frontOrback, ovlay_num, ruler_scale
	pressButton = False

	if event == cv2.EVENT_LBUTTONDOWN:

		if markLine[0] == [-1, -1] and markLine[1] == [-1, -1] and pressButton == False:
			if(frontOrback == "1"):
				markLine[0] = [x, y]
				markLine[1] = [x, y]
			else:
				markLine[0] = [width_c-x, y]
				markLine[1] = [width_c-x, y]

		if(frontOrback == "1" and pressButton == False): 
			markLine.append([x, y])
		elif(pressButton == False): 
			markLine.append([width_c-x, y])

		if len(markLine)>=5 and pressButton == False:
			markAngle = []
			for i in range(2,len(markLine)-2):
				angle = angle_between(markLine[i][0],markLine[i][1],markLine[i+1][0],markLine[i+1][1],markLine[i+2][0],markLine[i+2][1])
				markAngle.append(angle)

		if(ruler_on and len(ruler_pos) == 0):
			if(frontOrback == "1"):	ruler_pos.append([x, y])
			else: ruler_pos.append([width_c-x, y])
		elif(ruler_on and len(ruler_pos) == 1):
			if(frontOrback == "1"):	ruler_pos.append([x, y])
			else: ruler_pos.append([width_c-x, y])
			scale_tmp = round(float(input("\n >> Distance between p1-p2 is: ")),2)
			ruler_scale = round( scale_tmp/pow( (ruler_pos[0][0]-ruler_pos[1][0])*(ruler_pos[0][0]-ruler_pos[1][0]) + (ruler_pos[0][1]-ruler_pos[1][1])*(ruler_pos[0][1]-ruler_pos[1][1]), 0.5 ), 2)
			dis = pow( pow(markLine[-1][0]-markLine[-2][0],2) + pow(markLine[-1][1]-markLine[-2][1],2), 0.5)
			print("\n >> Ruler measured: " + str( round(ruler_scale*dis,2) ))	
		elif(ruler_on and len(ruler_pos) == 2):
			dis = pow( pow(markLine[-1][0]-markLine[-2][0],2) + pow(markLine[-1][1]-markLine[-2][1],2), 0.5)
			print("\n >> Ruler measured: " + str( round(ruler_scale*dis,2)) )

	if event == cv2.EVENT_RBUTTONDOWN:
		if len(markLine_straight)%2 == 0:
			if(frontOrback == "1"): markLine_straight.append([x, y])
			else: markLine_straight.append([width_c-x, y])
		elif len(markLine_straight)%2 == 1:
			if(frontOrback == "1"): markLine_straight.append([x, y])
			else: markLine_straight.append([width_c-x, y])
			displace_hori = abs(markLine_straight[-1][0] - markLine_straight[-2][0])
			displace_verti = abs(markLine_straight[-1][1] - markLine_straight[-2][1])
			if(displace_hori > displace_verti):
				markLine_straight[-1][1] = markLine_straight[-2][1]
				markLine_straight[-2][0] = 0
				markLine_straight[-1][0] = width_c
			else:
				markLine_straight[-1][0] = markLine_straight[-2][0]
				markLine_straight[-2][1] = 0
				markLine_straight[-1][1] = height_c

		if(ruler_on and len(ruler_pos) == 2 and len(markLine_straight)%2 == 0):
			dis = pow( pow(markLine_straight[-1][0]-markLine_straight[-2][0],2) + pow(markLine_straight[-1][1]-markLine_straight[-2][1],2), 0.5)
			print("\n >> Ruler measured: " + str( round(ruler_scale*dis,2)) )
				
def readImagesAndTimes():
	filenames = [ "1.jpg", "2.jpg"]
	images = []
	for filename in filenames:
		im = cv2.imread(filename)
		images.append(im)
	return images

def image_addweight(addweightName):
	picName = addweightName + ".jpg"
	images = readImagesAndTimes()
	mergeMertens = cv2.createMergeMertens()
	exposureFusion = mergeMertens.process(images)
	cv2.imwrite(picName, exposureFusion * 255)

	im1 = cv2.imread("1.jpg")
	cv2.imwrite(addweightName + "_1.jpg", im1)
	im2 = cv2.imread("2.jpg")
	cv2.imwrite(addweightName + "_2.jpg", im2)

def slide_fn(frame_no):
	global frame_last, frame
	vs.set(cv2.CAP_PROP_POS_FRAMES, frame_no-1)
	ret, frame = vs.read()
	cv2.imshow("MX_studio", frame)
	if(frame_last != frame_no): frame_last = frame_no-1

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-f", "--fps", type=int, default=30, help="video fps")
args = vars(ap.parse_args())

vs = cv2.VideoCapture(args["video"])
ret, frame = vs.read()
total_frame = int(vs.get(cv2.CAP_PROP_FRAME_COUNT))
width_c = int(vs.get(cv2.CAP_PROP_FRAME_WIDTH))
height_c = int(vs.get(cv2.CAP_PROP_FRAME_HEIGHT))

now_t = datetime.datetime.today() 
t_format = now_t.strftime("%H%M%S")

ruler_scale, ruler_pos, ruler_on = 8888.0, [], False
play_all, frontOrback = "c", "1"
start_frame, stop_frame = 1, total_frame
markLine, markLine_straight, markAngle = [[-1, -1], [-1, -1]], [], []
frame_last = 88888
mid_line = [ [int(0.5*width_c),0], [int(0.5*width_c),height_c] ]
midLine_switch = False

cv2.namedWindow("MX_studio", cv2.WINDOW_NORMAL)
cv2.resizeWindow("MX_studio", int(0.5*width_c), int(0.5*height_c))
cv2.createTrackbar('frame', 'MX_studio', 1, total_frame, slide_fn)
cv2.setMouseCallback('MX_studio',draw_lines)
cv2.imshow("MX_studio", frame)

print("\n\n-----------------------------------------------------------------------")
print("\n >> 裁減影片，開始幀數請按'R'，結束幀數請按'S'，存檔請按'W'")
print("\n >> 標示角度 ---> 滑鼠左鍵，清除線條 ---> 按 C")
print("\n >> 畫直線 ---> 滑鼠右鍵，清除線條 ---> 按 C")
print("\n >> 截圖 ---> 按 P")
print("\n >> 疊圖 ---> 先按 1 再按 2 ")
print("-----------------------------------------------------------------------\n")

while True:

	key = cv2.waitKey(1) & 0xFF

	if key == ord("q") or key == 27: 
		cv2.destroyAllWindows()
		break
	elif key == ord("r"):
		start_frame = int(vs.get(cv2.CAP_PROP_POS_FRAMES))
		print("\n >> 開始帪數為: " + str(start_frame))
	elif key == ord("s"):
		stop_frame = int(vs.get(cv2.CAP_PROP_POS_FRAMES))
		print("\n >> 結束帪數為: " + str(stop_frame))
	elif key == ord("w"):
		try:
			vs.release()
			vs = cv2.VideoCapture(args["video"])
			ret, frame = vs.read()
			vs.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
			width = int(vs.get(cv2.CAP_PROP_FRAME_WIDTH))
			height = int(vs.get(cv2.CAP_PROP_FRAME_HEIGHT))
			if("avi" in str(args["video"])): 
				fourcc = cv2.VideoWriter_fourcc(*'h264')
			if("4" in str(args["video"])): 
				fourcc = cv2.VideoWriter_fourcc(*'h264')
			out = cv2.VideoWriter("clip_" + str(args["video"])[:-4] + "_" + t_format +  str(args["video"])[-4:], fourcc, args["fps"], (width, height))
			for i in range(stop_frame - start_frame + 2): 
				if(i>2):
					out.write(frame)
					ret, frame = vs.read()
					key = cv2.waitKey(1) & 0xFF
					cv2.imshow("MX_studio", frame)
				else:
					ret, frame = vs.read()
					key = cv2.waitKey(1) & 0xFF
			out.release()
			vs.release()
			print("\n >> 完成影片裁減")
			cv2.destroyAllWindows()
			break
		except Exception as err:
			print(err)
			break
	elif key == ord("c"):
		markLine = [[-1, -1], [-1, -1]]
		markAngle = []
		markLine_straight = []
		vs.release()
		vs = cv2.VideoCapture(args["video"])
		vs.set(cv2.CAP_PROP_POS_FRAMES, frame_last)
		ret, frame = vs.read()
		cv2.imshow("MX_studio", frame)
	elif key == ord("l"):
		if (len(ruler_pos) == 0):
			ruler_on = True
			print("\n >> Ruler ON")
			print("\n >> Please set ruler point 1/2")
		elif (len(ruler_pos) == 1):
			ruler_on = True
			print("\n >> Please set ruler point 2/2")
		elif (len(ruler_pos) == 2):
			print("\n >> Ruler OFF")
			ruler_scale, ruler_pos, ruler_on = 8888.0, [], False
	elif key == ord("1"):
		cv2.imwrite("1.jpg", frame)
	elif key == ord("2"):
		cv2.imwrite("2.jpg", frame)
		addweightName = input("\n >> picture name: ")
		image_addweight(addweightName)
	elif key == ord("p"):
		now_t = datetime.datetime.today() 
		t_format = str(now_t.strftime("%H%M%S")) + ".jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("!"):
		now_t = datetime.datetime.today() 
		t_format = "vd_upper_1.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("@"):
		now_t = datetime.datetime.today() 
		t_format = "vd_upper_2.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("#"):
		now_t = datetime.datetime.today() 
		t_format = "vd_upper_3.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("$"):
		now_t = datetime.datetime.today() 
		t_format = "vd_lower_1.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("%"):
		now_t = datetime.datetime.today() 
		t_format = "vd_lower_2.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("^"):
		now_t = datetime.datetime.today() 
		t_format = "vd_lower_3.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("&"):
		now_t = datetime.datetime.today() 
		t_format = "vd_balance_open_1.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("*"):
		now_t = datetime.datetime.today() 
		t_format = "vd_balance_open_2.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("("):
		now_t = datetime.datetime.today() 
		t_format = "vd_balance_close_1.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord(")"):
		now_t = datetime.datetime.today() 
		t_format = "vd_balance_close_2.jpg"
		cv2.imwrite(t_format, frame)
	elif key == ord("m"): 
		midLine_switch = not midLine_switch

	if midLine_switch == True:
		mid_line = [ [int(0.5*width_c),0], [int(0.5*width_c),height_c] ]
	else:
		vs.release()
		vs = cv2.VideoCapture(args["video"])
		vs.set(cv2.CAP_PROP_POS_FRAMES, frame_last)
		ret, frame = vs.read()
		cv2.imshow("MX_studio", frame)
		mid_line = [ [0,0], [0,0] ]

	for i in range(len(markLine)-1):
		cv2.line(frame, markLine[i], markLine[i+1], (0, 255, 0), 2)
		cv2.imshow("MX_studio", frame)

	for i in range(0,len(markLine_straight),2):
		try:
			cv2.line(frame, markLine_straight[i], markLine_straight[i+1], (128, 0, 128), 1)
			cv2.imshow("MX_studio", frame)
		except: pass

	for i in range(0,len(mid_line),2):
		try:
			cv2.line(frame, mid_line[i], mid_line[i+1], (255, 0, 0), 1)
			cv2.imshow("MX_studio", frame)
		except: pass
### for i in range(len(markAngle)):
###		if(frontOrback == "0"):
###			frame = cv2.flip(frame,1)
###			#cv2.putText(frame,str(markAngle[i]),(int(width_c-markLine[i+3][0]),int(markLine[i+3][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
###			frame = cv2.flip(frame,1)
###			cv2.imshow("MX_studio", frame)
###		else:
###			#cv2.putText(frame,str(markAngle[i]),(int(markLine[i+3][0]),int(markLine[i+3][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
###			cv2.imshow("MX_studio", frame)

