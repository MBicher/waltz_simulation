import DanceClass
import csv
import random

random.seed(12345)

movie=False #make a movie (i.e. record and save a picture per frame into Images/)
render=True #render the screne
tracetype=0 #type 0 = no trace, 1 = trace every beatstroke, 2 = trace every frame

#define dancers
totaldancers=30

slowdancers=int(totaldancers*0.0) #couples with reduced max-energy
distantdancers=int(totaldancers*0.0) #couples with larger distance beteen rotation axes
awfuldancers=int(totaldancers*0.0) #couples with both penalties
goodddancers=int(totaldancers*0.0) #couples with maximum energy but cannot switch direction
perfectdancers=totaldancers-slowdancers-distantdancers-awfuldancers #perfect skilled agents

#music
musicfile='Music/waltz_nr2.csv' #file, containing the time-instants for the music beats
#musicfile='Music/donauwalzer.csv' #file, containing the time-instants for the music beats
with open(musicfile,'r') as f:
	R=csv.reader(f,delimiter=';')
	beats=[float(x[0]) for x in R]

#define dancer parameters	 
e360=240.0 #[J] max kinetic energy for good dancers
dgood=0.5 #distance between bodies
factor=0.9 #penalty factor for worse dancers
initialfactor=0.5 #initialfactor*e360= energy used for the first spin
mass=150.0 #mass of a couple

resultfilename='Results/Results.csv' #file to write the results into
tracefilename='Results/Traces.json' #file to write the traces of the dancers into
scenarioname=str(totaldancers) #identifyer for the csv row
	
#create dancers
Dancers=list()
for i in range(perfectdancers):
	d={}
	d['maxenergy']=e360
	d['leftdancer']=True
	d['pairdistance']=dgood
	d['initialenergy']=d['maxenergy']*initialfactor
	d['modelname']='CoupleGood.egg'
	d['mass']=mass
	d['identifier']='perfect'
	Dancers.append(d)
	
for i in range(perfectdancers):
	d={}
	d['maxenergy']=e360
	d['leftdancer']=False
	d['pairdistance']=dgood
	d['initialenergy']=d['maxenergy']*initialfactor
	d['modelname']='CoupleGood.egg'
	d['mass']=mass
	d['identifier']='perfect'
	Dancers.append(d)

for i in range(slowdancers):
	d={}
	d['maxenergy']=e360*factor
	d['leftdancer']=False
	d['pairdistance']=dgood
	d['initialenergy']=d['maxenergy']*initialfactor
	d['modelname']='CoupleSlow.egg'
	d['mass']=mass
	d['identifier']='slow'
	Dancers.append(d)
	
for i in range(distantdancers):
	d={}
	d['maxenergy']=e360
	d['leftdancer']=False
	d['pairdistance']=dgood/(factor**0.5)
	d['initialenergy']=d['maxenergy']*initialfactor
	d['modelname']='CoupleDistant.egg'
	d['mass']=mass
	d['identifier']='distant'
	Dancers.append(d)
	
for i in range(awfuldancers):
	d={}
	d['maxenergy']=e360*factor
	d['leftdancer']=False
	d['pairdistance']=dgood/(factor**0.5)
	d['initialenergy']=d['maxenergy']*initialfactor
	d['modelname']='CoupleAwful.egg'
	d['mass']=mass
	d['identifier']='awful'
	Dancers.append(d)
	
DC=DanceClass.Simulation(Dancers,beats,None,movie,render,tracetype) #create dance-class instance
DC.Run(scenarioname,resultfilename,tracefilename) #run simulation