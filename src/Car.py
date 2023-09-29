#Car class
from numpy.random import normal
from numpy import sqrt, sign
V_MAX = 100 / 3.6 #100 km/h
V_DESIRED = V_MAX * 1.2
SIGMA = 2 #Standard deviation of the random initial velocities
GRINDSET = 0.1 #Standard dev. of random tick updates
GUSTAVO = 36 #Standard dev. of desired velocities
V_MIN = 60 / 3.6
CAR_LENGTH = 80
PIXEL_PER_M = 1

class Car:
    a_max = 1.44 
    b_max = 4.66 / 2
    sqrt_ab = 2*sqrt(a_max*b_max)
    def __init__(self, x = 0,spawnframe=0):
        
        self.desiredvel: float = abs(normal(V_DESIRED,GUSTAVO/3.6)) #Absolute value necessary to avoid negatives (even if unlikely!)
        if (self.desiredvel < V_MIN):
            self.desiredvel = V_MIN
        self.vel: float = abs(normal(self.desiredvel,SIGMA))  #random velocity protocol. Can be removed afterwards
        self.x: float = x
        self.a: float = 0
        self.overtaking = 0
        self.spawnframe = spawnframe
        self.s0 = 0
        self.waited = 0
        self.pissed = False
        self.prepissedvel = self.desiredvel

    
    def update(self,dt: float, infront = None):
        self.x += self.vel*dt*PIXEL_PER_M
        crash = False
        
        alpha = 0
        s = 5000
        
        #On matters of getting angry or not
        if (self.vel < self.desiredvel*0.8 and not self.pissed):
            self.waited += 1 #We're waiting
        elif (self.pissed):
            self.waited += 1 #Keep track of when our eruption was
            self.desiredvel += 0.5*dt #I'm gonna accelerate until my grandma keels over

        if (self.waited*dt > 60 and not self.pissed): #It's been too long, I've had enough
            self.waited = 0
            self.pissed = True
            self.desiredvel *= 1.5
            self.a_max *= 10 #With the power of pure rage we can survive at least a g-force
        elif (self.pissed and self.waited*dt > 10 and self.vel > (self.desiredvel / 1.5)):
            self.waited = 0
            self.pissed = False
            self.desiredvel = self.prepissedvel
            self.a_max /= 10
        

        if (infront is not None):
            s = infront.x - self.x - CAR_LENGTH
            
            # Do we want to overtake?
            if (s<5*self.vel and self.vel < self.desiredvel and self.desiredvel > infront.vel):
                # Can we overtake?
                self.overtaking = 1
                
            # Are we dead?
            if (s<= 0.1):
                print("THOU HATH CRASHED @",self.x)
                self.vel = 0
                #infront.vel = infront.vel/2
                infront.x += 0
                s = 1
                crash = True
            
            # Update speed
            delta_v = self.vel - infront.vel
            alpha = (self.vel*2.2 + self.vel*delta_v/self.sqrt_ab)/s
            self.s0 = alpha * s
            
        #Do we want to merge?
        if (self.vel > 0.8*self.desiredvel):
            self.overtaking = -1
        
        if (crash):
            print(self.a,self.vel,self.x,alpha)
        self.vel += self.a*dt
        self.a = self.a_max* (1 - (self.vel/self.desiredvel)**4 - alpha**2)
        if (crash):
            print("Something's gone wrong!",self.a)
        #if (abs(self.a) > self.a_max):
        #    self.a = self.a_max*sign(self.a)
        if (self.vel < 0):
            self.vel = 0
        if (self.a == float('-inf')): #Presumably, we've crashed
            self.a = self.a_max
        
        
    def normalSpeed(self,sigma: float):
        prev_vel = self.vel
        self.vel = normal(prev_vel, sigma)
        while(self.vel <= (60/3.6)):
            self.vel = normal(prev_vel, sigma)
    def updateSqrtAB(self):
        self.sqrt_ab = 2*sqrt(self.a_max, self.b_max)
            
       




