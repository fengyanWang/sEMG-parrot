#coding:UTF-8
from __future__ import print_function
import os
import time
import math
import platform
import numpy as np
from myThread import myThread
from offlineClf import myModel
from sklearn.externals import joblib
from FeatureSpace import FeatureSpace
from myo import  Myo ,  VibrationType , DeviceListener 

#监听myo数据的类
class PrintPoseListener(DeviceListener):
	def __init__(self , dataType):
		self.emgData = [] #用于存储肌电数据
		self.dataType = dataType #数据的类型，主要有肌电和姿态数据
		self.emgDataCount = 0 #肌电数据计数
		self.currentOrientation=[0,0,0,0] #当前的四元数
		self.referenceOrientation=[0,0,0,0] #上个时刻的四元数

	#由四元数得到欧拉角
	def getTheEuler(self , quat):
		x, y, z, w = quat[0], quat[1], quat[2], quat[3]
		roll = math.atan2( 2*w*x + 2*y*z, 1 - 2*x*x - 2*y*y )
		pitch = math.asin( max( -1, min( 1 , 2*w*y - 2*z*x )))
		yaw = math.atan2( 2*w*z + 2*x*y, 1 - 2*y*y - 2*z*z )
		
		return roll , pitch , yaw

	def CalculateRelativeAngle(self , current , reference ):
		angle = current - reference
		if (angle > math.pi):
			return angle - 2*math.pi
		if (angle < -math.pi):
			return angle + 2*math.pi
		return angle

	def CalculateRelativeEulerAngles(self , currentOrientation , referenceOrientation):
		"""
		 Calculate all relative angles between the current orientation and the reference orientation
		"""
		currentRoll,currentPitch,currentYaw = self.getTheEuler(currentOrientation)
		referenceRoll, referencePitch, referenceYaw = self.getTheEuler (referenceOrientation)
		roll = self.CalculateRelativeAngle(currentRoll, referenceRoll)
		pitch = self.CalculateRelativeAngle(currentPitch, referencePitch)
		yaw = self.CalculateRelativeAngle(currentYaw, referenceYaw)
		return pitch, yaw , roll

	def RerangeEulerAngle(self , angle , deadzone , max1):
		sign=math.copysign(1, angle)
		value = abs(angle)

		if (value < deadzone):
			angle = 0
			return angle
		else:
			value = float(min(value, max1))
			value -= deadzone
			value /= (max1 - deadzone);
		angle = float(sign*value)
		return angle 

	def RerangeEulerAngles( self , roll , pitch , yaw):
		'''对角度值进行归一化'''
		# dead Zona  
		rollDeadzone = 0.22   #0.1
		pitchDeadzone = 0.22
		yawDeadzone = 0.22
		
		rollMax = 0.65    #0.2
		pitchMax = 0.8    #.35
		yawMax = 0.8
		roll = self.RerangeEulerAngle(roll,rollDeadzone,rollMax)
		pitch = self.RerangeEulerAngle(pitch, pitchDeadzone, pitchMax)
		yaw = self.RerangeEulerAngle(yaw, yawDeadzone, yawMax)

		return (roll,pitch,yaw)

	def Filter_values(self , val1 , val2 , val3):
		'''对角度值进行滤波'''
		if (val1==0 and val2==0 and val3==0):
			return 0,0,0 
		sg1,sg2,sg3=math.copysign(1, val1), math.copysign(1, val2),math.copysign(1, val3)
		val1,val2,val3=abs(val1),abs(val2),abs(val3)
		if(val1>val2 and val1>val3):
			val2=0
			val3=0
		elif(val2>val3):
			if(val3!=0):
				val3=0
			if(val1!=0):
				val1=0
		else:
			if(val1!=0):
				val1=0
			if(val2!=0):
				val2=0
		return sg1*val1,sg2*val2,sg3*val3

	def conver_grade(self , angle):
		'''将角度值映射到100内'''
		angle= (angle*100)
		return angle

	def getFlyEuler(self , currentOrientation ,referenceOrientation ):
		'''得到飞行器的欧拉角'''
		myoRoll,myoPitch,myoYaw=self.CalculateRelativeEulerAngles(self.currentOrientation , self.referenceOrientation)
		myoRoll_, myoPitch_, myoYaw_=self.RerangeEulerAngles (myoRoll, myoPitch, myoYaw)
		myoRoll, myoPitch, myoYaw=self.Filter_values(myoRoll_, myoPitch_, myoYaw_)
		myoRoll=self.conver_grade(myoRoll)
		myoPitch=self.conver_grade(myoPitch)
		myoYaw=self.conver_grade(myoYaw)
		droneRoll = float(-myoPitch)
		dronePitch = float(myoRoll)
		droneYaw = float(-myoYaw)

		return droneRoll , dronePitch , droneYaw

	#肌电数据处理函数
	def on_emg(self, emg, moving):
		if "emg" in self.dataType:
			self.emgData = list(self.emgData)
			self.emgData.append(emg)
			self.emgDataCount += 1
		else:
			pass

	def on_imu(self , quat, acc, gyro ):
		if "imu" in self.dataType:
			self.currentOrientation=[quat[0], quat[1], quat[2], quat[3]]
		else:
			pass
			
#在线分类
class main(object):

	def __init__(self , dataType = ["emg" , "imu"]):

		self.emgDict = dict()
		self.dataType = dataType
		self.numberVoter = 3
		self.modelFilePath = "emg_1535964225.pkl"

	def start(self):
		self.listener = PrintPoseListener(self.dataType)
		self.mMyo = Myo() 
		self.getSystermType()

		try:
			self.mMyo.connect() 
			self.mMyo.add_listener(self.listener)
			self.mMyo.vibrate(VibrationType.SHORT)
		except ValueError as ex:
			print (ex)
		# self.getTheModelFileName()
		self.loadModel()#导入模型
		self.mMyo.vibrate(VibrationType.MEDIUM)#震动表示模型导入完成

	#往文件中写入动作字符串
	def writeActionFile(self , fileName = "actionTempData.dat" , actionStr = "rest"):
		'''将最终的动作写入文件中'''
		if os.path.exists(fileName) == False:
			with open (fileName , "w") as f:
				f.write(actionStr)
				f.close()
				print("write over!!")
		else:
			pass

	#采集线程主程序
	def myoRun(self):
		try:
			while True:
				self.mMyo.run()
				time.sleep(0.001)
		except KeyboardInterrupt:
			self.mMyo.safely_disconnect()

	#获取在线分类结果函数(分类线程函数)
	def onlineClf(self):
		try:
			while True:
				if "emg" in self.dataType:
					if self.listener.emgDataCount > self.model.mWinWidth  + self.numberVoter - 1:    #投票数为其加1
						self.listener.emgDataCount = 0
						self.listener.emgData = np.array(self.listener.emgData , dtype = np.int64)
						self.listener.emgData = self.listener.emgData.T
						self.emgDict['one'] = self.listener.emgData
						self.sample = FeatureSpace(rawDict = self.emgDict, 
								  moveNames = ['one',], #动作类别
								  ChList = [0,1,2,3,4,5,6,7],  #传感器的通道数目
								  features = {'Names': self.model.mFeatureList,  #定义的特征
											  'LW': self.model.mWinWidth,  #定义的窗宽
											  'LI': self.model.mSlidingLen},   #定义的窗滑动的步长
								  one_hot = False ,
								  trainPercent=[1, 0, 0]    #是否进行onehot处理
								 )
						self.getTrainData()
						actionList = self.model.mModel.predict(self.trainX)
						self.writeActionFile(actionStr = str(self.getTheAction(actionList)))
						# print("the action is :" , self.getTheAction(actionList))
						self.listener.emgData = []
						self.emgDict.clear()
						time.sleep(0.001)
					else:
						time.sleep(0.001)
				if "imu" in self.dataType:
					droneRoll , dronePitch , droneYaw = self.listener.getFlyEuler(self.listener.currentOrientation , self.listener.referenceOrientation)
					if droneRoll != 0 :
						print("droneRoll is :" , droneRoll)
					if dronePitch != 0 :
						print("dronePitch is :" , dronePitch)
					if droneYaw != 0 :
						print("droneYaw is :" , droneYaw)
					self.listener.referenceOrientation = self.listener.currentOrientation

		except KeyboardInterrupt:
			pass

	#The feature space is divided into data sets
	def getTrainData(self):

		nDimensions = self.sample.trainImageX.shape[1]
		#训练集
		self.trainX = np.reshape(self.sample.trainImageX, (-1, nDimensions))
		self.trainY = np.squeeze(self.sample.trainImageY)
		#测试集
		self.testX = np.reshape(self.sample.testImageX, (-1, nDimensions))
		self.testY = np.squeeze(self.sample.testImageY)
		#评估集
		self.validateX = np.reshape(self.sample.validateImageX, (-1, nDimensions))
		self.validateY = np.squeeze(self.sample.validateImageY)

	'''导入已经保存的模型'''
	def loadModel(self):

		self.model = joblib.load(self.modelFilePath)
		self.actionNames = self.model.actionNames

	def getSystermType(self):
		'''获得系统平台类型'''
		self.systermType = platform.system()

	
	#投票函数
	def getTheAction(self , actionList):

		tempData = np.array(actionList)
		counts = np.bincount(tempData)
		actionNumber = np.argmax(counts)
		return self.actionNames[actionNumber]#返回定义的动作类别字符串

	'''myo主程序的入口'''
	def run(self):
		try:
			self.mThread = myThread()
			self.mThread.addThread('onlineClf' , self.onlineClf , 0) #加入在线识别动作线程
			self.mThread.addThread('getData' , self.myoRun , 0) #加入数据采集的线程
			self.mThread.runThread()
		except KeyboardInterrupt:
			self.mMyo.safely_disconnect()
			self.mThread.forcedStopThread()

if __name__ == "__main__":

	mMain = main(dataType = ["emg"])
	mMain.start()
	mMain.run()