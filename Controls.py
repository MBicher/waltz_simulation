from panda3d.core import *
import math

class Controls():
	""" Class that initilaises the keyboards which are available for use while the simulation is running
	"""
	def __init__(self):
		None
			
	def MakeKeys(self,Sim):
		self.__cambase=Point3(0,0,0)
		self.__camtarget=Point3(0,0,1)
		self.__camdelta1=5
		self.__camdelta2=5
		
		self.paused=False
		
		
		self.Sim=Sim
		
		self.Sim.accept('arrow_left',self.KeyRotateLeft)
		self.Sim.accept('arrow_right',self.KeyRotateRight)
		self.Sim.accept('arrow_left-repeat',self.KeyRotateLeftSweep)
		self.Sim.accept('arrow_right-repeat',self.KeyRotateRightSweep)

		self.Sim.accept('arrow_up',self.KeyRotateUp)
		self.Sim.accept('arrow_down',self.KeyRotateDown)
		self.Sim.accept('arrow_up-repeat',self.KeyRotateUp)
		self.Sim.accept('arrow_down-repeat',self.KeyRotateDown)
		
		self.Sim.accept('a', self.KeyLookLeft)
		self.Sim.accept('a-repeat', self.KeyLookLeft)
		self.Sim.accept('d', self.KeyLookRight)	
		self.Sim.accept('d-repeat', self.KeyLookRight)
		self.Sim.accept('w', self.KeyLookUp)
		self.Sim.accept('w-repeat', self.KeyLookUp)		
		self.Sim.accept('s', self.KeyLookDown)
		self.Sim.accept('s-repeat', self.KeyLookDown)
		
		self.Sim.accept('+',self.KeyZoomIn)
		self.Sim.accept('+-repeat',self.KeyZoomIn)
		self.Sim.accept('-',self.KeyZoomOut)
		self.Sim.accept('--repeat',self.KeyZoomOut)
		
		self.Sim.accept('p',self.KeyPause)
		self.Sim.accept('o',self.KeyScreenshot)
		
		return self.Sim
	
	def Rotate (self, x, y, z, xr, yr, zr, axis, angle ,t):		
		if axis=="z":
			phi=math.atan2(x-xr,y-yr)
			xn= xr + ((x-xr)**2+(y-yr)**2)**(0.5)*math.sin(phi +  math.pi /180.0 * angle *t)
			yn= yr + ((x-xr)**2+(y-yr)**2)**(0.5)*math.cos(phi + math.pi /180.0 * angle *t)
			zn=z
		else: 
			if axis=="y":
				phi=math.atan2(x-xr,z-zr)
				xn= xr + ((z-zr)**2+(x-xr)**2)**(0.5)*math.sin(phi + math.pi /180.0 * angle *t)
				yn=y
				zn= zr + ((z-zr)**2+(x-xr)**2)**(0.5)*math.cos(phi + math.pi /180.0 * angle *t)
			else:
				phi=math.atan2(y-yr,z-zr)
				xn= x
				yn=yr + ((z-zr)**2+(y-yr)**2)**(0.5)*math.sin(phi + math.pi /180.0 * angle *t)
				zn= zr + ((z-zr)**2+(y-yr)**2)**(0.5)*math.cos(phi + math.pi /180.0 * angle *t)
		return [xn,yn,zn]

	
	def KeyRotate(self,angle):
		""" Rotate horizontally
		
		Input:
		angle (float) angle in degree
		"""
		pos=self.Sim.cam.getPos()
		look=self.Sim.camtarget
		newpos=self.Rotate(pos[0],pos[1],pos[2],look[0],look[1],look[2],'z',angle,1)
		self.Sim.cam.setPos(newpos[0],newpos[1],newpos[2])
		self.Sim.cam.lookAt(look[0],look[1],look[2])
		
	def KeyRotateV(self,scale):
		""" Rotate vertically (shift the camposition upwards)
		
		Input:
		scale (float) factor to multiply the z-coordinate of the cam-pos
		"""
		pos=self.Sim.cam.getPos()
		look=self.Sim.camtarget
		
		self.Sim.cam.setPos(pos[0],pos[1],pos[2]*scale)
		self.Sim.cam.lookAt(look[0],look[1],look[2])
		
	def KeyRotateLeft(self):
		self.KeyRotate(0.5)
			
	def KeyRotateRight(self):
		self.KeyRotate(-0.5)		
			
	def KeyRotateLeftSweep(self):
		self.KeyRotate(2)
			
	def KeyRotateRightSweep(self):
		self.KeyRotate(-2)	
			
	def KeyRotateUp(self):
		self.KeyRotateV(1.1)
			
	def KeyRotateDown(self):
		self.KeyRotateV(0.9)
		
	def KeyZoom(self,scale):
		""" Zoom towards the camcentre
		
		Input:
		scale (float >0) factor to scale the distance to the cam-target (>1 zoom out, <1 zoom in)
		"""
		pos=self.Sim.cam.getPos()
		look=self.Sim.camtarget
		dir=[base-target for (target,base) in zip(look,pos)]
		newpos=[target+d*scale for (target,d) in zip(look,dir)]
		self.Sim.cam.setPos(newpos[0],newpos[1],newpos[2])
		self.Sim.cam.lookAt(look[0],look[1],look[2])
		
	def KeyZoomIn(self):
		self.KeyZoom(0.9)
		
	def KeyZoomOut(self):
		self.KeyZoom(1.1)
		

	def KeyLookLeft(self,amount=0.3):
		pos=self.Sim.cam.getPos()
		look=self.Sim.camtarget
		self.Sim.camtarget=self.Rotate(look[0],look[1],look[2],pos[0],pos[1],pos[2],'z',-amount,1)
		base.cam.setPos(pos)
		base.cam.lookAt(self.Sim.camtarget[0],self.Sim.camtarget[1],self.Sim.camtarget[2])
		
	def KeyLookRight(self,amount=0.3):
		pos=self.Sim.cam.getPos()
		look=self.Sim.camtarget
		self.Sim.camtarget=self.Rotate(look[0],look[1],look[2],pos[0],pos[1],pos[2],'z',amount,1)
		base.cam.setPos(pos)
		base.cam.lookAt(self.Sim.camtarget[0],self.Sim.camtarget[1],self.Sim.camtarget[2])
		
	def KeyLookUp(self,amount=5):
		self.KeyLook(Vec3.up()*amount)
		
	def KeyLookDown(self,amount=5):	
		self.KeyLook(-Vec3.up()*amount)
			
	def KeyLook(self,Vec):
		""" Shift the cameratarget by a vector
		
		Input:
		Vec (Vec3 >0) vector to move the cam-target
		"""
		pos=self.Sim.cam.getPos()
		look=self.Sim.camtarget
		self.Sim.camtarget=Vec3(look[0],look[1],look[2])+Vec
		base.cam.setPos(pos)
		base.cam.lookAt(self.Sim.camtarget[0],self.Sim.camtarget[1],self.Sim.camtarget[2])
		
	def KeyPause(self):
		""" Stop Simulation and continue again
		"""
		if self.paused==False:
			self.task=base.taskMgr.getTasksNamed('update')[0]
			base.taskMgr.remove('update')
			self.paused=True
		else:
			base.taskMgr.add(self.task,'update')
			self.paused=False
		
	def KeyScreenshot(self):
		L=os.listdir('Images')
		name='Screenshot'
		L2=[int(x.replace(name,'').replace('.png','')) for x in L if x.startswith(name)]
		L2.append(-1)
		number=max(L2)+1
		self.Sim.MakeScreenshot('Images/Screenshot'+str(number)+'.png')