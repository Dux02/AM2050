# Car class
from typing import Union, Tuple
from numpy.random import normal
from random import choice,choices
from numpy import sqrt, sign, exp
from numbers import Number

import pygame
pygame.mixer.init()
beeps = [pygame.mixer.Sound("media/beep"+str(i+1)+".wav") for i in range(10)]

### CAR & LANE PARAMETERS (STAFF ONLY) ###
V_DESIRED = 120 / 3.6  # m/s
SIGMA = 2  # Standard deviation of the random initial velocities
GRINDSET = 0.1  # Standard dev. of random tick updates
GUSTAVO = 20  # Standard dev. of desired velocities (kph)
V_MIN = 60 / 3.6
CAR_LENGTH = 2  # meters
CAR_HEIGHT = 1  # meters
PIXEL_PER_M = 10  # pixels per meter
LANE_HEIGHT, LINE_HEIGHT = 2, 0.1  # meters

alphabet = 'abcdefhijklmnopqrstuvwxyz0123456789'
def generateID() -> str:
    return ''.join(choices(alphabet,k=8)) # Picks 8 letters at random, generally v. low collision chance

class Car:
    a_max = 1.44*3  # m/s^2
    b_max = 4.66  # m/s^2
    sqrt_ab = 2*sqrt(a_max*b_max)
    debugcounter = 0
    def __init__(self, x = 0,spawnframe=0):
        self.desiredvel: float = abs(normal(V_DESIRED, GUSTAVO/3.6))  # Absolute value necessary to avoid negatives (even if unlikely!)
        if (self.desiredvel < V_MIN):
            self.desiredvel = V_MIN
        # self.vel: float = abs(normal(self.desiredvel, SIGMA))
        self.vel: float = self.desiredvel
        self.x: float = x
        self.a: float = 0
        self.overtaking = 0
        self.spawnframe = spawnframe
        self.frame = spawnframe
        self.s0 = 0
        #self.waited = 0
        #self.pissed = False
        #self.prepissedvel = self.desiredvel
        self.debug = False
        self.s = 100000
    
    def update(self, dt: float, frame: int, infront: Union['Car', None] = None):
        if (self.frame >= frame):
            return  # Avoid double updating
        self.frame = frame
        crash = False

        # self.checkAnger(dt)

        self.overtaking = 0

        # Find self.s
        self.determineGap(infront)

        # Do we want to merge?
        if -0.5 * 120 / (3.6 * self.desiredvel) < self.a < 0.5 * 120 / (3.6 * self.desiredvel):
            # Used to be dependent on relation between desiredvel and vel but
            # that doesn't work in traffic (no cars would merge)
            # Now we merge when we're not accelerating much
            self.overtaking = -1

        # Do we want to overtake?
        if infront is not None:
            # OVTF = 1.2, the factor time s0. Note this is similar to the previous code w/ a min. 3 second headway instead.
            # if (s < 1.2 * self.s0 and self.vel < 0.95 * self.desiredvel and self.desiredvel > infront.vel):
            #     self.overtaking = 1

            # The constant -1 here is related to the constant -0.5 in Simulation.overtakingLogic
            if self.a < -1 * 120 / (3.6 * self.desiredvel) and self.desiredvel > infront.vel:
                # if we're slowing down, we want to overtake
                self.overtaking = 1
        
        crash = self.advancedSpeed(dt, infront)
        if (crash):
            print(round(self.x), self.vel, round(self.a,3), self.s0)
            self.overtaking = 0
            Car.debugcounter += 1
            if (Car.debugcounter == 10):
                self.debug = True
            
        if (self.vel < 0):
            self.vel = 0
        self.x += self.vel*dt*PIXEL_PER_M  # x is in pixels, vel is in m/s

    def determineGap(self, infront):
        self.s = 100000
        if infront is not None:
            s = (infront.x - self.x) / PIXEL_PER_M - CAR_LENGTH
            self.s = s

    def checkAnger(self, dt):
        if (self.vel < self.desiredvel * 0.8 and not self.pissed):
            self.waited += 0  # We're waiting
        elif (self.pissed):
            self.waited += 1  # Keep track of when our eruption was
            self.desiredvel += 0.5 * dt  # I'm gonna accelerate until my grandma keels over
        if (self.waited * dt > 60 and not self.pissed):  # It's been too long, I've had enough
            self.waited = 0
            self.pissed = True
            self.desiredvel *= 1.5
            self.a_max *= 10  # With the power of pure rage we can survive at least a g-force
        elif (self.pissed and self.waited * dt > 10 and self.vel > (self.desiredvel / 1.5)):
            self.waited = 0
            self.pissed = False
            self.desiredvel = self.prepissedvel
            self.a_max /= 10

    def normalSpeed(self, sigma: float, dt:float, frame: int):
        if (self.frame >= frame):
            return
        self.frame = frame
        prev_vel = self.vel
        self.vel = normal(prev_vel, sigma)
        while(self.vel <= (60/3.6)):
            self.vel = normal(prev_vel, sigma)
        self.x += self.vel*dt

    def advancedSpeed(self, dt: float, infront: Union['Car', None] = None) -> bool:
        """ Calculate the new speed and acceleration of the car on the basis of the IDM model.
            Returns false if the car did not crash with the car infront, otherwise true.
            Uses distance between self and infront."""
        alpha = 0
        crashed = False
        if infront is not None:
            if self.s <= 0.1:  # If they're too close, avoid division by 0!
                self.s = 2.1 * PIXEL_PER_M  # Must be bigger than the jam distance to avoid acceleration -> -inf!
                self.vel = 0
                crashed = True

        self.a = self.calcAccel(infront)
        self.vel += self.a*dt
        if self.a == float('-inf'):  # Presumably, we've crashed
            print("Crisis dienst!!")  # This should ideally *never* get triggered!
            crashed = True
            self.a = self.a_max
        return crashed

    def calcAccel(self, infront: 'Car') -> float:
        """Calculates and returns acceleration for self with infront the car infront"""
        self.s0 = self.desiredDist(infront)
        alpha = self.s0 / self.s
        return self.a_max * (1 - (self.vel / self.desiredvel) ** 4 - alpha ** 2)

    def desiredDist(self, infront: Union['Car', None] = None) -> float:
        """ Returns the desired distance of the car based on the car in front of it, in meters.
            This follows the Intelligent Driver Model (IDM), with a reaction time of 1.6 seconds,
            a jam distance of 2 meters, and a difference-in-speed dependent term.
            In the limiting case delta_v <= 0, the desired distance is the jam distance.
            In the limiting case delta_v = self.vel, we find the distance scales quadratically with speed."""
        delta_v = 0
        factor = 1
        if (infront is not None):
            delta_v = self.vel - infront.vel

        return 2 + max(self.vel*1.6 + self.vel*delta_v/self.sqrt_ab,0)
        # return max(2, 2 + self.vel*1.6 + self.vel*delta_v/self.sqrt_ab)  # linear correction (easier to explain)

    def inDist(self, dist: Union[float, Tuple[float,float]], othercar: 'Car') -> bool:
        """The function checks if another car is within a certain distance range from the current car.

        Args:
            dist (float | (float, float)): The parameter `dist` can be either a float or a tuple of two floats
                in which case dist[0] is the distance behind current car, and dist[1] in front
            othercar (Car): The car to check if it is in the distance range

        Returns:
            bool: True if in the distance range, False otherwise
        """ 
        if (isinstance(dist,Number)):
            return self.x - CAR_LENGTH*PIXEL_PER_M - dist < othercar.x < self.x + CAR_LENGTH*PIXEL_PER_M + dist
        else:
            return self.x - CAR_LENGTH*PIXEL_PER_M - dist[0] < othercar.x < self.x + CAR_LENGTH*PIXEL_PER_M + dist[1]
    
    def updateSqrtAB(self):
        self.sqrt_ab = 2*sqrt(self.a_max, self.b_max)
            
    # Alexander's whimsical beeping            
    def beep(self,timestamp: float, infront: 'Car', windowspecs: Tuple[int,int] = (0,1)):
        """
        The function plays a random beep sound if the car in front is too slow and the car is on the screen.
        
        :param timestamp: The timestamp parameter is a float value representing the current second (frame*dt). It is
        used to determine when to trigger the beep sound
        :type timestamp: float
        :param windowspecs: The `windowspecs` parameter is a tuple that specifies the range of x-values
        within which the beep sound should be played. It has two elements: `windowspecs[0]` represents
        the lower bound of the range, and `windowspecs[1]` represents the upper bound.
        :type windowspecs: Tuple[int,int]
        """
        
        if (timestamp % 1 == 0 and infront.vel < 0.5*self.desiredvel and windowspecs[0] < self.x < windowspecs[1]):
                beep = choice(beeps)
                pygame.mixer.Sound.play(beep)
        return

    def debugger(self):
        print("a is: a_max (1 -", (self.vel/self.desiredvel)**4, "- (" + str(self.s0) + "/" + str(self.s) + ")^2)")
        print("thus a =", self.a)

class CarData:
    def __init__(self, car: 'DataCar') -> None:
        self.desiredvel = car.desiredvel
        self.framedata = [(car.frame,car.x,car.y,car.vel,car.a)]
        self.id = car.id

class DataCar(Car):
    def __init__(self, x=0, y=0, spawnframe=0):
        super().__init__(x, spawnframe)
        self.y = y
        self.id = generateID()
        self.data = CarData(self)
    
    def update(self, dt: float, frame: int, infront: Union[Car, None] = None):
        super().update(dt, frame, infront)
        if (self.data.framedata[-1][0] < self.frame):
            self.data.framedata.append((frame,self.x,self.y,self.vel,self.a))
    
    def normalSpeed(self, sigma: float, dt: float, frame:int):
        super().normalSpeed(sigma,dt,float)
        if (self.data.framedata[-1][0] < self.frame):
            self.data.framedata.append((frame,self.x,self.y,self.vel,self.a))
        


