import sys
import os
import time
from myThread import myThread
from pyparrot.Bebop import Bebop

'''my code'''
#定义一些全局变量
currentAction = "rest"
quitFlag = False
#获取动作类别
def getTheCurrentAction(fileName = "actionTempData.dat"):
	if os.path.exists(fileName) == True:
		if os.path.getsize(fileName):
			with open (fileName , "r") as f:
				actionStr = f.read()  #读取字符串
				f.close()
			os.remove(fileName)
			print("the current action is :" , actionStr)
			return  actionStr
		else:
			return None
	else:
		return None
#获取按键的值
def getTheKeyValue(fileName = "keyValueTempData.dat"):
	global quitFlag
	if os.path.exists(fileName) == True:
		if os.path.getsize(fileName):
			with open (fileName , "r") as f:
				tempStr = f.read()  #读取字符串
				if tempStr == "quit":
					quitFlag = True
				f.close()
			os.remove(fileName)


class myoBebop(object):

	def __init__(self , indoorFly = True):
		'''类初始化函数'''
		self.bebop = None 
		self.indoorFlyFlag = indoorFly
		self.actionType = "rest"   #当前的动作类型
		self.startSuccessFlag = False #初始化是否成功标志位
		self.takeOfFlag = False		#是否起飞标志位
		self.landFlag = True	#是否降落标志位
		self.startFlag = False	#程序开始标志位
		self.executeCommondFlag = True		#命令执行成功标志位
		#动作映射字典
		self.actionMapDict = {	"front"	: 	"fist"  , 	"back" 	:	 "open_hand" , 
								"left"	: 	"one" , 	"right" : 	 "two" ,
								"up"	:	"good",		"down"	:	 "low" ,
								"rotateLeft" : "three" ,  "rotateRight" : "four" , 
								"takeOf": 	"ok"  , 	"land" 	: 	 "love"}
		self.tempCount = 0   #计数
		self.excuteFlag1 = True   #读取动作类别标志位
		self.excuteFlag2 = True	  #读取按键值的标志位
		self.flyType = 0  #飞机飞行类别（0：正常飞行 ， 1：特技飞行）
		self.moveStepTime = 1  #飞行器水平运行步长时间
		self.rotateStepTime = 1 #飞行器旋转运行步长时间

	def start(self):
		'''开始函数'''
		#初始化飞机对象
		self.bebop = Bebop()
		#连接飞机  
		print("connecting")
		self.success = self.bebop.connect(10)  #与飞机进行连接（最大尝试次数为10次）
		if self.success == True: 
			print("sleeping")  
			self.bebop.smart_sleep(5)
			self.bebop.ask_for_state_update()   #获取飞机的状态
			if self.indoorFlyFlag == True:
				self.setIndoorFly()
				print("set indoor fly sucess!!!")
			print("The aircraft was successfully initialized!")
			self.startSuccessFlag = True   #开始成功

		else:
			print("The connection failed. Please check again!")
			self.startSuccessFlag = False   #开始失败
		self.removeExitFile()


	def bebopFly(self , actionType):
		'''根据动作类别进行相应的动作'''
		if actionType == self.actionMapDict["front"]:   #向前飞
			self.executeCommondFlag = False   
			
			print("flying state is %s" % self.bebop.sensors.flying_state)
			if self.flyType == 0:
				self.bebop.fly_direct(roll=0, pitch=50, yaw=0, vertical_movement=0, duration=self.moveStepTime)
				print("fly front")
			elif self.flyType == 1:
				self.success = self.bebop.flip(direction="front")
				print("flip front")
				print("mambo flip result %s" % self.success)
				self.bebop.smart_sleep(5)
			self.executeCommondFlag = True

		elif actionType == self.actionMapDict["back"]:   #向后飞
			self.executeCommondFlag = False
			
			print("flying state is %s" % self.bebop.sensors.flying_state)
			if self.flyType == 0:
				self.bebop.fly_direct(roll=0, pitch=-50, yaw=0, vertical_movement=0, duration=self.moveStepTime)
				print("fly back")
			elif self.flyType == 1:
				self.success = self.bebop.flip(direction="back")
				print("flip back")
				print("mambo flip result %s" % self.success)
				self.bebop.smart_sleep(5)
			self.executeCommondFlag = True

		elif actionType == self.actionMapDict["left"]:   #左飞
			self.executeCommondFlag = False
			
			print("flying state is %s" % self.bebop.sensors.flying_state)
			if self.flyType == 0:
				self.bebop.fly_direct(roll=50, pitch=0, yaw=0, vertical_movement=0, duration=self.moveStepTime)
				print("fly left")
			elif self.flyType == 1:
				self.success = self.bebop.flip(direction="left")
				print("flip left")
				print("mambo flip result %s" % self.success)
				self.bebop.smart_sleep(5)
			self.executeCommondFlag = True

		elif actionType == self.actionMapDict["right"]:   #右飞
			self.executeCommondFlag = False
			
			print("flying state is %s" % self.bebop.sensors.flying_state)
			if self.flyType == 0:
				self.bebop.fly_direct(roll=-50, pitch=0, yaw=0, vertical_movement=0, duration=self.moveStepTime)
				print("fly right")
			elif self.flyType == 1:
				self.success = self.bebop.flip(direction="right")
				print("flip right")
				print("mambo flip result %s" % self.success)
				self.bebop.smart_sleep(5)
			self.executeCommondFlag = True

		elif actionType == self.actionMapDict["up"]:   #上飞
			self.executeCommondFlag = False
			print("flying state is %s" % self.bebop.sensors.flying_state)
			if self.flyType == 0:
				self.bebop.fly_direct(roll = 0, pitch = 0, yaw = 0, vertical_movement=50, duration = self.moveStepTime)
				print("fly up")
			elif self.flyType == 1:
				pass
			self.executeCommondFlag = True

		elif actionType == self.actionMapDict["down"]:   #下飞
			self.executeCommondFlag = False
			print("flying state is %s" % self.bebop.sensors.flying_state)
			if self.flyType == 0:
				self.bebop.fly_direct(roll = 0, pitch = 0, yaw = 0, vertical_movement= - 50, duration = self.moveStepTime)
				print("fly down")
			elif self.flyType == 1:
				pass
			self.executeCommondFlag = True

		elif actionType == self.actionMapDict["rotateLeft"]:   #向左旋转
			self.executeCommondFlag = False
			print("flying state is %s" % self.bebop.sensors.flying_state)
			if self.flyType == 0:
				self.bebop.fly_direct(roll=0, pitch=0, yaw=50, vertical_movement=0, duration=self.moveStepTime)
				print("fly rotateLeft")
			elif self.flyType == 1:
				pass
			self.executeCommondFlag = True

		elif actionType == self.actionMapDict["rotateRight"]:   #向右旋转
			self.executeCommondFlag = False
			print("flying state is %s" % self.bebop.sensors.flying_state)
			if self.flyType == 0:
				self.bebop.fly_direct(roll=0, pitch=0, yaw = -50, vertical_movement=0, duration=self.moveStepTime)
				print("fly rotateRight")
			elif self.flyType == 1:
				pass
			self.executeCommondFlag = True

		elif actionType == self.actionMapDict["takeOf"]: #起飞
			self.startFlag = True
			if self.landFlag == True:
				self.landFlag = False
				self.executeCommondFlag = False
				print("take of ")
				self.bebop.safe_takeoff(10)
				self.bebop.smart_sleep(5)
				self.executeCommondFlag = True
				self.takeOfFlag = True

		elif actionType == self.actionMapDict["land"]: #降落
			if self.takeOfFlag == True:
				self.takeOfFlag = False
				self.executeCommondFlag = False
				print("land ")
				self.bebop.safe_land(10)
				self.bebop.smart_sleep(5)
				self.landFlag = True
				self.executeCommondFlag = True
	#myo失去连接后，飞机自动着落		
	def safeAction(self):
		if self.startFlag == True:
			if self.flyType == 0:
				if self.tempCount > 100:
					self.bebop.safe_land(10)
					self.bebop.smart_sleep(5)
					print("DONE - disconnecting")
					self.bebop.disconnect()
					self.mThread.forcedStopThread()
			elif self.flyType == 1:
				if self.tempCount > 300:
					self.bebop.safe_land(10)
					self.bebop.smart_sleep(5)
					print("DONE - disconnecting")
					self.bebop.disconnect()
					self.mThread.forcedStopThread()

	def setTheActionMain(self):
		'''设置动作类别线程函数'''
		if self.excuteFlag1 == True:
			self.excuteFlag1 = False
			os.system("python2 myoMain.py")
			time.sleep(0.01)

	def removeExitFile(self , fileName = "actionTempData.dat" ):
		'''删除已经存在的文件'''
		if os.path.exists(fileName) == True:
			os.remove(fileName)

	def setIndoorFly(self):
		'''设置室内飞行的参数'''
		self.bebop.set_max_tilt(5)
		self.bebop.set_max_vertical_speed(1)

	def getKeyValueMain(self):
		'''获取按键值的线程函数'''
		if self.excuteFlag2 == True:
			self.excuteFlag2 = False
			os.system("python2 quit.py" ) 
			time.sleep(0.01)
	#按键退出函数
	def quitMain(self):
		print("quit")
		self.bebop.safe_land(10)
		self.bebop.smart_sleep(5)
		self.bebop.disconnect()
		self.mThread.forcedStopThread()

	def getTheActionMain(self):
		'''得到动作类别线程函数'''
		global quitFlag
		while True:
			self.actionType = getTheCurrentAction()
			getTheKeyValue()
			if quitFlag == True:
				self.quitMain()
			else:
				if self.actionType == None:
					self.tempCount += 1
				else:
					self.tempCount = 0
				self.safeAction()
				if self.executeCommondFlag == True:
					self.bebopFly(self.actionType)
				time.sleep(0.01)

	def run(self):
		'''运行主程序'''
		try:
			self.mThread = myThread()
			self.mThread.addThread('setTheActionMain' , self.setTheActionMain , 0)
			self.mThread.addThread('getTheActionMain' , self.getTheActionMain , 0)
			self.mThread.addThread('getKeyValueMain' , self.getKeyValueMain , 0)
			self.mThread.runThread()
		except KeyboardInterrupt:
			print("DONE")
			self.bebop.disconnect()
			self.mThread.forcedStopThread()

if __name__ == "__main__":

	mMyoBebop = myoBebop()  
	mMyoBebop.start()
	mMyoBebop.run()


