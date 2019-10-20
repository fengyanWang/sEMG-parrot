#coding:UTF-8
from __future__ import print_function

import sys, random, time, pygame , os
from pygame.locals import *

#往文件中写入动作字符串
def writeActionFile(fileName = "keyValueTempData.dat" , keyValue = "quit"):
	'''将最终的动作写入文件中'''
	if os.path.exists(fileName) == False:
		with open (fileName , "w") as f:
			f.write(keyValue)
			f.close()
			print("write over!!")
	else:
		pass
#主程序
pygame.init()
screen = pygame.display.set_mode((1,1))

while True:
	for event in pygame.event.get():
		if event.type == KEYDOWN:
			if event.key == K_SPACE:
				print("im quit!!!")
				writeActionFile()
				pygame.quit()
				sys.exit()
	#更新
	pygame.display.update()