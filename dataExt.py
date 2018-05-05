import io
import h5py
import sys
import time
import numpy as np

def getPast(st):
	pos = st.find("-")
	pos2 = st.find("-", pos + 1)
	pos3 = st.find(" ", pos2 + 1)
	pos4 = st.find(":", pos3 + 1)
	pos5 = st.find(":", pos4 + 1)
	year = int(st[0:pos])
	month = int(st[pos + 1:pos2])
	day = int(st[pos2 + 1:pos3])
	hour = int(st[pos3 + 1:pos4])
	minute = int(st[pos4 + 1:pos5])
	second = int(st[pos5 + 1:len(st)])
	hour = hour - 12
	if (hour < 0):
		hour = hour + 24
		day = day - 1
	if (day <= 0):
		month = month - 1
		day = day + 30
		if (month in [0, 1, 3, 5, 7, 8, 10]):
			day = day + 1
		if (month == 2):
			day = day - 2
	if (month <= 0):
		month = month + 12
		year = year - 1
	return str(year) + "-" + str(month) + "-" + str(day) + " " + str(hour) + ":" + str(minute) + ":" + str(second)
 
f = h5py.File('Lab.h5', 'w')
f2 = open('dataSeq.txt', 'r')
sys.stdin = f2
dt = [["" for j in range(5000)] for i in range(45563)]
print 1
evt = [[0 for j in range(5000)] for i in range(45563)]
print 2
ftr = [[[0.0 for k in range(6)] for j in range(5000)] for i in range(45563)]
print 3
lbl = [[[0.0 for k in range(5)] for j in range(3682)] for i in range(45563)]
pt = []
pNum = 0
print 'read start'
n = input()
for samples in range(n):
	print str(samples) + "/" + str(n)
	st = f2.readline()
	pos = st.find("\t")
	if (pos == -1):
		break;
	patient = int(st[0:pos])
	st = st[pos + 1:len(st)]
	pos = st.find("\t")
	eventNum = int(st[0:pos])
	labelNum = int(st[pos + 1:-1])
	#print eventNum
	eNum = 0
	lNum = 0
	startDate = 0
	for i in range(eventNum):
		st = f2.readline()
		pos = st.find("\t")
		pos2 = st.find("\t", pos + 1)
		#print pos
		#print st
		labelFlag = int(st[0:pos])
		event = int(st[pos + 1:pos2])
		date = st[pos2 + 1:-1]
		dt[pNum][eNum] = date
		evt[pNum][eNum] = event
		ctg = 0
		if (labelFlag == 1):
			ctg = input()
		featureNum = input()
		for j in range(featureNum):
			st = f2.readline()
			pos = st.find("\t")
			ftr[pNum][eNum][j * 2] = float(st[0:pos])
			ftr[pNum][eNum][j * 2 + 1] = float(st[pos + 1:-1])
		while (featureNum < 3):
			ftr[pNum][eNum][featureNum * 2] = 0
			ftr[pNum][eNum][featureNum * 2 + 1] = 0
			featureNum = featureNum + 1
		if (labelFlag == 1):
			lbl[pNum][lNum][0] = evt[pNum][eNum]
			lbl[pNum][lNum][1] = ftr[pNum][eNum][1]
			lbl[pNum][lNum][2] = ctg
			pastTime = getPast(date)
			while (dt[pNum][startDate] < pastTime and startDate < eNum):
				startDate = startDate + 1
			startDate = startDate - 1
			lbl[pNum][lNum][3] = startDate
			lbl[pNum][lNum][4] = startDate - 1000 + 1
			if (lbl[pNum][lNum][4] < 0):
				lbl[pNum][lNum][4] = 0
			lNum = lNum + 1
		eNum = eNum + 1
	pt.append(patient)
	pNum = pNum + 1

print "read done"
#print seqn
#grp.create_dataset("row_id", data = rowid)
#grp.create_dataset("subject_id", data = subid)
f.create_dataset("patient", data = pt)
f.create_dataset("event", data = evt)
f.create_dataset("time", data = dt)
#f.create_dataset("event_catAtt", data = atr)
f.create_dataset("feature", data = ftr)
f.create_dataset("label", data = lbl)

