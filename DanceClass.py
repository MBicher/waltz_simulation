
#Panda3d is a 3d gaming engine with a Python (and a C++) interface
#Hereby python code can be used to plot and manipulate objects (3d models) on a 3D interface
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
#some addiitonal settings for output visualisation (primarily its shadow)
loadPrcFileData('', 'framebuffer-stencil 0')
loadPrcFileData('', 'compressed-textures 1')
loadPrcFileData('', 'show-buffers 0')
loadPrcFileData('', 'basic-shaders-only 1')

#What makes Panda3d especially valuable for supporting simulations is its capabilities
#to include physical laws. Panda supports to include Bullet Physics, a 3d physics simulation
#environment optimised for multibody physical simulation. Hereby the visualisation capabilities
#of panda can be linked with the physical laws of bullet.
from panda3d.bullet import *

#additional libraries necesary
import random
import math
import statistics


#save traces of pairs
import json

from Controls import Controls


# with pairdistance of 2.5 and velocity of 12.014 we reach about 180 degree with beat-length 40
class Simulation(ShowBase):
	""" The simulation class initialises all dance scenarios and
	simulates them via panda and bullet.
	"""
	
	################################################################################# COONSTRUCTOR #######################################################
	def __init__(self,PAIRS,BEATS,tend=None,movie=False,renderType=True,tracetype=0):
		""" When initialising a new Simulation class a new
		bullet physics environment is created. 
		
		Input:
		PAIRS (list(dict)) list of dict objects that specify the pairs which will be created by the simulation
		BEATS (list(float)) list of seconds corrsponding to every first beat of the 3/4 times waltz music
		TEND (float) endtime of the simulation (seconds)
					can be None in order to make the sim stop at the last beat of the loaded music
		movie (bool) if True, the engine will render an image of the simulation per frame into the Images folder
		renderType (bool) if True, the 3D engine will render the current status of the simulation
		tracetype (int) 0 - no trace is drawn
						1 - the trace is drawn every beat (draws the direct path of the couple)
						2 - the trace is drawn every frame (draws all swirls of every couple)
		"""
		
		ShowBase.__init__(self)
		
		self.PAIRINFOS=PAIRS
		self.PAIRNUMBER=len(PAIRS)
		
		self.dt = 0.025 #length of a time-step
		self.BEATS=BEATS
		self.BEATFRAMES=[int(x/self.dt) for x in self.BEATS]
		
		if tend==None:
			self.TEND=BEATS[-1]
		else:
			self.TEND=tend
		#print(self.BEATS)
		
		self.tracetype=tracetype
		
		self.movie=movie
		self.renderType=renderType
		if self.renderType==False:
			self.render.hide()
		
		self.SCENARIO='Ballroom'
		self.disableMouse() #only use keybord to navigate the camera!
		self.setAspectRatio(16.0/9.0) #image ratio to make a nice movie
		
		self.world = BulletWorld()
		self.world.setGravity(Vec3(0, 0, -9.81))
		self.setBackgroundColor(0,0,0.2,1) #very dark blue background
		
		#initialise some defaults
		self.defaultangle=70.0  #default angle that couples aim to dance, if they dont know any better
		self.bodyradius=0.5 #size of one dancer
		
		#some default textures that are applied later to some elements (arrows, boxes etc)
		self.texwhite=self.loader.loadTexture('Sources/tex/white.png')
		self.texblack=self.loader.loadTexture('Sources/tex/black.png')
		self.texgrey=self.loader.loadTexture('Sources/tex/grey.png')
		self.texred=self.loader.loadTexture('Sources/tex/red.png')
		
		#reset some numbers
		self.time = 0 # simulation time [s]
		self.frames = 0 # frames (time-steps) of the simulation
		self.turn=0 # the man starts "spinning"
		self.spinnumber=0 # it is the first spin
		self.imagenumber=0 # it creates the first image
		self.currentbeatlength=0 # length of the beat
		
		self.Keys=Controls() #initialise keyboard keys to turn, zoom etc.
		self.Keys.MakeKeys(self)
		
		self.ballroomsize=[40.0,20.0]
		
		self.MakeFloor() #create the ballroom floor
		self.InitialisePairsRandom()
		self.InitialiseLight()
		self.InitialiseCam()
		
		debugging=False
		if debugging==True:
			debugNode = BulletDebugNode('Debug') 
			debugNode.showWireframe(True)
			debugNode.showConstraints(False)
			debugNode.showBoundingBoxes(True)
			debugNode.showNormals(True)
			debugNP = self.render.attachNewNode(debugNode)
			self.world.setDebugNode(debugNP.node())
			debugNP.show()
		
		
	################################################################################# INITIALISATION ROUTINES ##################################################	
	def MakeFloor(self):
		""" Create the floor as a rigid physical object and as a 3D visualisation
		"""
		#physicsnode
		name='Plane'
		shape = BulletPlaneShape(Vec3(0,0,1),0)
		physicsnode=BulletRigidBodyNode(name)
		physicsnode.addShape(shape)
		physicsnode.setMass(0)
		self.world.attachRigidBody(physicsnode)
		#pandanode
		nodepath=self.render.attachNewNode(physicsnode)
		nodepath.setPos(0,0,0)
		nodepath.setHpr(0,0,0)
		model=self.loader.loadModel('Sources/parquet.egg')
		#model=self.loader.loadModel('Sources/parquet_clean.egg')
		model.setScale(Vec3(100,100,1))
		model.setPos(0,0,0)
		model.setShaderAuto()
		model.reparentTo(nodepath)
		self.Floor=dict()
		self.Floor['pandanode']=nodepath
		self.Floor['physicsnode']=physicsnode

	def InitialisePairsRandom(self):	
		""" Initialises dance pairs
		distributes the pairs randomly in the specified ballroom
		Note, that the algorithm takes care that the couples
		dont intersect (have enough space to "stand")!
		"""
		self.Pairs=[]
		a=self.ballroomsize[0]/2
		b=self.ballroomsize[1]/2
		positions=list()
		for index in range(self.PAIRNUMBER):
			d1=self.PAIRINFOS[index]['pairdistance']
			while True:
				r=[random.random()**(0.5)*a*(random.choice([-1,1])),random.random()**(0.5)*b*(random.choice([-1,1]))] #random place with preference close to the borders
				pos1=Point3(r[0],r[1],0)
				angle=random.random()*360 #random angle
				pos2=Point3(r[0]-math.sin(angle)*d1,r[1]+math.cos(angle)*d1,0)
				accepted=True #accept position?
				for p in positions:
					if (p-pos1).length()<3*self.bodyradius: #Partner 1 has enough space?
						accepted=False
					if (p-pos2).length()<3*self.bodyradius: #Partner 2 has enough space?
						accepted=False
				if accepted==True:
					pair=self.MakePair(pos1,pos2,index)
					self.Pairs.append(pair)
					break
			positions.append(pos1)
			positions.append(pos2)
		
		self.PAIRIDENTIFIERS=list(set([x['identifier'] for x in self.Pairs]))
		self.PAIRIDENTIFIERS.sort()
		self.TOTALCOLLISIONS={x:0 for x in self.PAIRIDENTIFIERS}
	
	def InitialiseCam(self):
		""" Initialises the camera position
		Note that this is also important for the keyboard to
		allow zooming and rotating
		"""
		
		#self.campos=Point3(50,50,50) #initial position of the camera
		self.campos=Point3(0,-50,50)
		self.camtarget=Point3(0,0,0)
		self.cam.setPos(self.campos)
		self.cam.lookAt(self.camtarget)
			
	def InitialiseLight(self):	
		""" Initialises the lights
		By default - two pointlights indicating chandeliers
		"""
		
		plight=PointLight('plight1')
		plight.setAttenuation((1, 0, 0))
		plight.setColor(VBase4(1.0, 1.0, 1.0, 1))
		pln=render.attachNewNode(plight)
		pln.setPos(-15,0,5)
		self.render.setLight(pln)
		
		plight=PointLight('plight4')
		plight.setAttenuation((1, 0, 0))
		plight.setColor(VBase4(1.0, 1.0, 1.0, 1))
		pln=render.attachNewNode(plight)
		pln.setPos(15,0,5)
		self.render.setLight(pln)

		self.alight = self.render.attachNewNode(AmbientLight("Ambient"))
		self.alight.node().setColor(Vec4(0.4, 0.4, 0.4, 1))
		render.setLight(self.alight)
		
	def MakePair(self,pos1,pos2,index):
		""" Create a dance-pair as a rigid physical object and as a 3D visualisation
		
		Input:
		pos1,pos2 (Vec3 Objects) state the initial position of the leading and the following dance-partner
		index (int) index of the pair in the list 
		
		Output:
		pair (dict) object that contains a lot of information about the dance couple (see last code lines in this routine)
		"""
		
		#speficy initial parameters for the pair.
		pairdistance = self.PAIRINFOS[index]['pairdistance']
		initialenergy = self.PAIRINFOS[index]['initialenergy']
		maxenergy = self.PAIRINFOS[index]['maxenergy']
		modelname = self.PAIRINFOS[index]['modelname']
		leftdancer = self.PAIRINFOS[index]['leftdancer']
		mass = self.PAIRINFOS[index]['mass']
		identifier = self.PAIRINFOS[index]['identifier']
		
		radius=self.bodyradius
		height=1.7
			
		
		v1=pos2-pos1
		angle=v1.relativeAngleDeg(Vec3(1,0,0))
	
		#create the PHYSICS Object
		name='Pair'+str(index)
		physicsnode=BulletRigidBodyNode(name)
		shape = BulletBoxShape(Vec3(pairdistance,radius,height*0.5)) #note that the parameters are half of the final dimensions of the cube!
		physicsnode.addShape(shape, TransformState.makePos(Vec3(pairdistance*0.5,0,height*0.5)))
		physicsnode.setMass(mass) #note that one couple has one mass! Not each partner!
		physicsnode.setFriction(0)
		self.world.attachRigidBody(physicsnode)
		
		nodepath=self.render.attachNewNode(physicsnode)
		
		#make dummy nodes for the position of the rotation axis
		dummyNode1 = self.render.attachNewNode("lead")
		dummyNode1.setPos(0,0,0)
		dummyNode1.reparentTo(nodepath)
		
		dummyNode2 = self.render.attachNewNode("follower")
		dummyNode2.setPos(pairdistance,0,0)
		dummyNode2.reparentTo(nodepath)
		
		#create the 3D model Object
		modname='Sources/'+modelname
		model = self.loader.loadModel(modname)
		model.setScale(radius*0.5,radius*0.5,radius*0.5)
		model.setPos(pairdistance*0.5,0,0)
		model.setHpr(180,0,0)
		model.setShaderAuto()
		model.reparentTo(nodepath)
		
		nodepath.setPos(pos1)
		nodepath.setHpr(Point3(180-angle,0,0))
		
		
		pair=dict() #each pair is saved as a dict object with different entries	
		
		#add information to the dict object 
		pair['physicsnode']=physicsnode
		pair['pandanode']=nodepath
		pair['white']=1  #which of the two is the follwing (white) partner
		pair['energy']=0
		pair['initialenergy']=initialenergy
		pair['direction'] = 'right' #initial spinning direction
		pair['trace']=[pos1] #track the trace of the couple
		pair['randomoffset']=math.sqrt(random.random()+0.5) #if necessary, couples can be manipulated with random skill properties
		pair['pairdistance']=(pos2-pos1).length()
		pair['maxenergy']=maxenergy
		pair['leftdancer']=leftdancer
		pair['mass']=mass
		pair['index']=index
		pair['identifier']=identifier
		return pair
		
	def DrawTrace(self,thick=2.0):
		"""Routine to draw lines with a defined thickness on the ballroom floor.
		The line is white if the spinning dancer was the following part, black if the
		spinning dancer was the leading part.
		
		Unfortunately, this routine is a massive overhead if the simulation is long..
		
		Input:
		thick (float) line width
		"""
		for p in self.Pairs:
			try: #lines are drawn with LineSegs which need to be created once and can be appende furthermore
				pos=p['pandanode'].getChild(p['white']).getPos(self.render)
				newpos=Point3(pos[0],pos[1],0.1)
				oldpos=p['lineposwhite']
				ls= LineSegs()
				ls.setColor(1,1,1,0)
				ls.setThickness(thick)
				ls.moveTo(oldpos)
				ls.drawTo(newpos)
				node=p['linenodewhite']
				ls.create(node)
				p['lineposwhite']=newpos
				
				pos=p['pandanode'].getChild(int(not p['white'])).getPos(self.render)
				newpos=Point3(pos[0],pos[1],0.1)
				oldpos=p['lineposblack']
				ls= LineSegs()
				ls.setColor(0,0,0,0)
				ls.setThickness(thick)
				ls.moveTo(oldpos)
				ls.drawTo(newpos)
				node=p['linenodeblack']
				ls.create(node)
				p['lineposblack']=newpos
			except:
				ls= LineSegs()
				node = ls.create()
				ls.setColor(1,1,1,0)
				ls.setThickness(thick)
				NodePath(node).reparentTo(self.render)
				NodePath(node).setShaderOff()
				pos=p['pandanode'].getChild(p['white']).getPos(self.render)
				p['lineposwhite']=Point3(pos[0],pos[1],0.1)
				p['linenodewhite']=node
				
				ls= LineSegs()
				node = ls.create()
				ls.setColor(0,0,0,0)
				ls.setThickness(thick)
				NodePath(node).reparentTo(self.render)
				NodePath(node).setShaderOff()
				pos=p['pandanode'].getChild(int(not p['white'])).getPos(self.render)
				p['lineposblack']=Point3(pos[0],pos[1],0.1)
				p['linenodeblack']=node
				
	################################################################################# ROUTINES FOR TARGETED BEHAVIOUR ####################################
	
	def VectorFieldEllipseSq(self,pos,pair,adb=None):
		""" Routine to calculate which point a dance couple
		should target to remain on an elliptic trajectory.
		
		Input:
		pos (Vec3) position of the dance partner that will be the rotation axis in this move
		pair (dict) Pair object
		adb (float) ratio between a and b of the ellipsis (a/b=adb)
		"""
		
		if adb==None:
			adb=self.ballroomsize[0]/self.ballroomsize[1]
		mina=self.ballroomsize[0]*0.5*0 #couples that are on an ellipse, so that the main axle is smaller than this, are detracted
		maxa=self.ballroomsize[0]*0.5*0.8 #couples that are on an ellipse, so that the main axle is larger than this, are attracted to the centre
		
		x=pos[0]
		y=pos[1]
		
		#calculate tangent
		dx=-pos[1]**3*adb**4
		dy=pos[0]**3
		
		a = (pos[0]**4+adb**4*pos[1]**4)**0.25
		if a<mina: #detract from center
			fac=(mina-a)/mina*0.1
		elif a>maxa: #attract to center
			fac=-(a-maxa)/maxa*0.1
		else:
			fac=0
		
		return Vec3(dx+fac*x,dy+fac*y,0)
		
	################################################################################# ROUTINES FOR VELOCITY UPDATE ####################################		
	
	def EnergyFactor(self,pair):
		""" To find a relation between targeted angle and 
		spin velocity we assume that there is a linear realtionship:
			spinningvelocity*X = angle
		This routine tries to approximate X using the trace of the pair
		comparing danced angles and applied velocities.
		
		Input:
		pair (dict) dance couple
		
		Output:
		(float) estimation for X
		"""
		
		fac=list()
		for ang,energy,bl in zip(pair['angles'],pair['energies'],pair['beatlengths']):
			f=energy**0.5*bl/ang
			fac.append(f)
		L=list(zip(fac,pair['angles'],pair['energies']))
		L.sort(key=lambda x: x[0])
		
		#beatlength estimate
		try:
			bl=statistics.median(pair['beatlengths'][-3:])
		except:
			bl=pair['beatlengths'][-1]
		
		#take median of the factors as it is not so influenced by outliers
		return statistics.median(fac)/bl
		
	def CalculateEnergyVectorfield(self,pair):
		""" Energy update as done in the trajectory-strategy. 
		Tries to adapt the kinetic energy to stay on a given track.
		
		The strategy is based on the idea, that there exists a
		pair-specific unknown factor X, so that
		(spinningenergy**0.5)*X = angle
		To approximate X, the routine EnergyFactor is used
		
		Input:
		pair (dict) dance couple
		
		Output:
		(float) new spin-energy of the couple
		"""
		
		T=pair['trace'] #get trace of the pair
		
		if len(T)>2: #if the trace of the couple is not long enough (i.e. at the start of the simulation) the angle of the last spin cannot be evaluated and the angle necessary for the next spin cannot be determined
		
			energy=pair['energy'] #get current energy of the pair
			direction=pair['direction']
			
			p1=T[-3] #former position of partner A
			p2=T[-2] #position of partner B
			p3=T[-1] #position of partner A
			
			v1=p2-p1 #old couple-vector
			v2=p3-p2 #new couple-vector
			
			
			# first, observe the previous spin!
			if direction=='right':
				oldangle=180.0-v1.relativeAngleDeg(v2) #get angle of the previous spin
			else:
				oldangle=180.0+v1.relativeAngleDeg(v2) #get angle of the previous spin
			#print('previous energy: '+str(energy)+' lead to angle: '+str(oldangle))
			#check how to choose new velocity
			try:
				pair['angles'].append(oldangle)
				pair['energies'].append(abs(energy))
				pair['beatlengths'].append(self.currentbeatlength)
			except:
				pair['angles']=[oldangle]
				pair['energies']=[abs(energy)]
				pair['beatlengths']=[self.currentbeatlength]
				
				
			#get the pair-specific energy factor
			factor=self.EnergyFactor(pair)
			
			#Get the target vector/angle:
			v3=self.VectorFieldEllipseSq(p3,pair)
			#v3=self.VectorFieldSquare(p3,pair)
			
			#calculate the necessary angles for right/left spin on track
			rightangle=180.0-v2.relativeAngleDeg(v3) #Calculate the target angle if spinning right (default)
			leftangle=(360.0-rightangle)
	
			#necessary energies for right/left spin on track,
			# assume that the next beat will take as long as the last one!
			maxenergy=pair['maxenergy']
			leftdancer=pair['leftdancer']
			
			rightenergy=(rightangle*factor)**2
			leftenergy=(leftangle*factor)**2
			defaultenergy=min((self.defaultangle*factor)**2,maxenergy)
			
			#print('need angle of '+str(rightangle)+' which would require energy of: '+str(rightenergy))
			
			tolerance=1.3
			
			if direction == 'right':
				if rightenergy<maxenergy: #no problem, dance right
					return rightenergy,'right'
				else:
					if leftdancer==True and leftenergy<maxenergy: #if skilled enough and it helps, switch to left
						return leftenergy,'left'
					elif rightenergy<tolerance*maxenergy: #if the pair can almost make it, do it
						return maxenergy,'right'
					else: #no chance, make a pause
						return defaultenergy,'right'
			else:
				if leftenergy<maxenergy: #no problem, dance left
					return leftenergy,'left'
				else:
					if rightenergy<maxenergy: #if it helps, switch to right
						return rightenergy,'right'
					elif leftenergy<tolerance*maxenergy: #if the pair can almost make it, do it
						return maxenergy,'left'
					else: #no chance, make a pause
						return defaultenergy,'left'
		else:
			return pair['initialenergy'],pair['direction']
		
	################################################################################# ROUTINES TO MANAGE DANCING ####################################		
	
	def Change(self):
		""" This routine manages the switch of roles of the dancers.
		Hereby the rotation axis is moved from one to the other dance partner
		and the velocity is updated.
		"""
		for pair in self.Pairs:
			#print('Investigating pair '+str(pair['index']))
			pos=pair['pandanode'].getChild(1).getPos(self.render)
			pair['trace'].append(pos)
			
			#Unfortunately BulletPhysics does not allow to change the center of
			#a rigid object to a different spot inside the object which
			#makes it impossible to shift the rotation axis to a different point
			#To "cheat" around this problem, we
			#	1 manually turn the object by 180 degrees
			#	2 manually turn the 3d model of the body by 180 degrees (now it is back to normal)
			
			hprold=pair['pandanode'].getHpr()
			pair['pandanode'].setPos(pos)
			pair['pandanode'].setHpr(Point3(hprold[0]+180.0,0,0))
			model=pair['pandanode'].getChild(2)
			hprold=model.getHpr()
			model.setHpr(Point3(hprold[0]+180.0,hprold[1],hprold[2]))
			
			#calulate the new velocity:
			energy,direction = self.CalculateEnergyVectorfield(pair)
			pair['energy']=energy
			pair['direction']=direction
			#estimate angular velocity based on energy
			abstangentialvelocity = (4*energy/pair['mass'])**0.5   # E=mv^2/2  and assume that m=pair['mass']/2 
			if direction=='left':
				angularvelocity=abstangentialvelocity/pair['pairdistance']
			else:
				angularvelocity=-abstangentialvelocity/pair['pairdistance']
				
			#print('applying energy: '+str(energy)+' with angular velocity '+str(angularvelocity))
			#apply angular velocity
			pair['physicsnode'].setAngularVelocity(Vec3(0,0,angularvelocity))
			pair['physicsnode'].setLinearVelocity(Vec3(0,0,0)) #in any case, stop the linar velocity of the object!
			pair['white']=int(not pair['white']) #switch the index of the following partner
			#print('##################################################')
	
	################################################################################# ROUTINES TO MANAGE UPDATES (AND CAMERA POSITIONS) ####################################
		
	def UpdateBallroom(self,task):
		""" Primarily calls the Dance routine but also manages everything around the
		physical simulation for the graphical output like the prosition of the camera or
		the onscreen texts and images
		
		Input:
		task (TaskMgr) task instance (see in the Run file)
		
		Output:
		task.cont (TaskMgr.cont) note that the task manager should repeat calling this function
		"""
		#first, make a screenshot
		if self.movie==True:
			self.Image()
		#check if simulation is finished
		if self.time>=self.TEND:
			self.finalStuff()
		
		#do, what happens every frame!
		if self.tracetype==1: #if trace==1,every frame draws a line (not recommended - much overhead!)
			self.DrawTrace(2.0)
		if self.frames in self.BEATFRAMES: #beat - change the spin axis!
			if self.tracetype==2:
				self.DrawTrace(2.0)
			self.spinnumber+=1
			#calculate length of previous measure
			ind=self.BEATFRAMES.index(self.frames)
			if ind>0:
				self.currentbeatlength=self.BEATFRAMES[ind]-self.BEATFRAMES[ind-1]
				self.Change()
			else:
				None  #wait for the first beat to pass, to understand the music!
		self.world.doPhysics(self.dt) #make movement and collisions
		for identifier in self.PAIRIDENTIFIERS:
			Contacts=[sum([self.world.contactTestPair(P['physicsnode'],Q['physicsnode']).getNumContacts() for Q in self.Pairs if P!=Q]) for i,P in enumerate(self.Pairs) if P['identifier']==identifier]
			Contacts=sum(Contacts)/len([x for x in self.Pairs if x['identifier']==identifier]) #get observed contacts between dancers per dancer
			self.TOTALCOLLISIONS[identifier]+=Contacts

		#update time
		self.frames+=1
		self.time+=self.dt
		#print(self.time)
		return task.cont
		
	def finalStuff(self):
		print(self.TOTALCOLLISIONS)
		#save collisioncount
		string=''
		for identifier in self.PAIRIDENTIFIERS:
			string+=';'+identifier+';'+str(self.TOTALCOLLISIONS[identifier])
		try:
			f=open(self.RESULTFILENAME,'a')
			f.write('\n'+str(self.SCENARIONAME)+';'+string)
			f.close()
		except:
			f=open(self.RESULTFILENAME,'w')
			f.write(str(self.SCENARIONAME)+';'+string)
			f.close()
		#save traces of pairs
		Q=list()
		for pair in self.Pairs:
			tr=[[x[0],x[1]] for x in pair['trace']]
			a={'index':pair['index'],'coordinates':tr}
			Q.append(a)
		with open(self.TRACEFILENAME,'w') as f:
			json.dump(Q,f,sort_keys = True, indent = 4)
		exit()
		
	################################################################################# BUEROCRATIC ROUTINES ####################################
		
	def Run(self,scenarioname,resultfilename='Results/Results.csv',tracefilename='Results/Traces.json'):
		self.RESULTFILENAME=resultfilename
		self.TRACEFILENAME=tracefilename
		self.SCENARIONAME=scenarioname
		taskMgr.add(self.UpdateBallroom, 'update')
		base.run()
		
	def Image(self):
		filename=str(self.imagenumber)
		filename='0'*(5-len(filename))+filename
		filename='Images/'+filename+'.png'
		self.MakeScreenshot(filename)
		self.imagenumber+=1
		
	def MakeScreenshot(self,filename):
		if self.renderType==False:
			self.render.show()
		tex=Texture()
		#width=1600
		#height=900
		width=6400
		height=3600
		mybuffer=base.win.makeTextureBuffer('HDScreenShotBuff',width,height,tex,True)
		mycamera = base.makeCamera(mybuffer,useCamera=base.cam)
		myscene = base.render
		mycamera.node().setScene(myscene)
		base.graphicsEngine.renderFrame()
		tex = mybuffer.getTexture()
		mybuffer.setActive(False)
		tex.write(filename)
		base.graphicsEngine.removeWindow(mybuffer)
		if self.renderType==False:
			self.render.hide()