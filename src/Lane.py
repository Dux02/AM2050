from typing import Union
from .Car import Car, PIXEL_PER_M
from numpy import linspace, mean
from random import randint, random

SPAWNSAFETYDIST = 10 * PIXEL_PER_M

class Lane:
    def __init__(self):
        self.length = 5000 * PIXEL_PER_M  # 5 km
        self.vehicles: list[Car] = []
        self.finishedVehicles: list[Car] = []
        self.timeSinceLastCarGenerated = 0
        self.leftLane: Union[None, 'Lane'] = None
        self.rightLane: Union[None, 'Lane'] = None
        self.marker = Car(self.length)
        self.first: Car = self.marker
    
    def initLinspacedCars(self, cars: int = 0):
        xcoords = linspace(0, self.length, cars)
        self.vehicles: list[Car] = [Car(xcoords[i]) for i in range(cars)]
        if (cars > 0):
            self.first = self.vehicles[0]
        for i in range(cars):
            if (i > 0):
                self.vehicles[i].neighbours.back = self.vehicles[i-1]
            if (i < cars - 1):
                self.vehicles[i].neighbours.front = self.vehicles[i+1]
            if (i == cars - 1):
                self.vehicles[i].neighbours.front = self.marker
                self.marker.neighbours.back = self.vehicles[i]
            if (self.rightLane is not None):
                self.vehicles[i].neighbours.rightfront = self.rightLane.marker
            if (self.leftLane is not None):
                self.vehicles[i].neighbours.leftfront = self.leftLane.marker
    
    def linkMarkers(self):
        if (self.leftLane is not None):
            self.marker.neighbours.leftfront = self.leftLane.marker
        else:
            self.marker.neighbours.leftfront = None
        if (self.rightLane is not None):
            self.marker.neighbours.rightfront = self.rightLane.marker
        else:
            self.marker.neighbours.rightfront = None
            
    def validateMarkerChain(self):
        carCheck = self.marker
        while (carCheck.neighbours.back is not None and carCheck.neighbours.back.x < carCheck.x):
            carCheck = carCheck.neighbours.back
        if (carCheck == self.first):
            print("Yippee!")
            return True
        elif (carCheck.neighbours.back is None):
            print("Also good")
            return True
        else:
            print("Ruhroh")
            return False
                
    def update(self, dt: float):
        numOfCars = len(self.vehicles)
        if (numOfCars == 0):
            return
        
        carsToRemove: list[int] = []

        for i in range(numOfCars):
            car = self.vehicles[i]
            if (self.leftLane is None and car.neighbours.leftfront is not None):
                print("What the fuck")
            if (self.rightLane is None and car.neighbours.rightfront is not None):
                print("What the actual fuck")
            overtakey = car.update(dt)
            # TODO: Could make this more efficient? if we use car.overtaking, check at the end if first.overtaking != 0 and act accordingly.
            if (self.vehicles[i].x > self.length):
                self.finishedVehicles.append(car)
                carsToRemove.append(i)
                car.endOfTheRoad(self.marker)
            elif (overtakey == 1): # Overtaking
                self.leftLane.addVehicle(car)
                if (car == self.first):
                    self.first = car.neighbours.rightfront
                carsToRemove.append(i)
            elif(overtakey == -1): # Merging
                self.rightLane.addVehicle(car)
                if (car == self.first):
                    self.first = car.neighbours.leftfront
                carsToRemove.append(i)
            
        carsToRemove.sort(reverse=True)
        for i in carsToRemove:
            self.vehicles.pop(i)

        return
    
    def addVehicle(self, vehicle: Car):
        if (vehicle.x < self.first.x):
            self.first = vehicle
        self.vehicles.append(vehicle)
    
    
    def flushVehicles(self):
        '''Removes finished vehicles from memory'''
        self.finishedVehicles = []
    
    def getAvgSpeed(self) -> float:
        speeds = []
        for car in self.vehicles:
                speeds.append(car.vel)
        if len(speeds) == 0:
            speeds = [0]
        return mean(speeds)
    
    def getAvgDesiredSpeeds(self) -> float:
        speeds = []
        for car in self.vehicles:
                speeds.append(car.desiredvel)
        if len(speeds) == 0:
            speeds = [0]
        return mean(speeds)
    @property
    def firstCar(self) -> Car:
        if (len(self.vehicles) == 0):
            return self.marker
        else:
            return self.vehicles[0]
    @property
    def lastCar(self) -> Car:
        if len(self.vehicles) == 0:
            return self.marker
        else:
            return self.marker.neighbours.back
    
    def generateCarT(self,timestep:int,frame:int) -> bool:
        '''
        T STANDS FOR TIMESTAMP - FOR PROBABILISTIC GENERATION SEE generateCarP
        Generates a car between 1 and 2 timesteps since last car generated in the lane (wrt frame)
        If it successfully generates a car, it will return true, otherwise false.
        It will not spawn a car if there's not enough space to do so, regardless of the time since last spawn
        '''
        if (self.first.x < SPAWNSAFETYDIST):
            return False
        
        delta_i = frame - self.timeSinceLastCarGenerated
        if (delta_i < timestep):
            return False
        offset = randint(0,timestep-1)
        if ((delta_i % timestep == offset or delta_i >= 2*timestep)):
            self._generateCar(frame)
            return True
        return False
    
    def _generateCar(self,frame:int):
        newCar = Car(0,frame)
        newCar.vel = self.first.vel # To avoid crashes, the cars come in with the same speed as the car in front
        newCar.neighbours.front = self.first
        self.first.neighbours.back = newCar
        if (self.leftLane is not None):
            newCar.neighbours.leftfront = self.leftLane.first
        if (self.rightLane is not None):
            newCar.neighbours.rightfront = self.rightLane.first
        
        self.vehicles.append(newCar)
        self.first = newCar
        self.timeSinceLastCarGenerated = frame
        
    def generateCarP(self, p: float, frame: int) -> bool:
        '''
        P STANDS FOR PROBABILITY - FOR TIMED GENERATION SEE generateCarT
        Generates a car between 1 and 2 timesteps since last car generated in the lane (wrt frame)
        If it successfully generates a car, it will return true, otherwise false.
        It will not spawn a car if there's not enough space to do so, regardless of the time since last spawn
        '''
        if (self.first.x < SPAWNSAFETYDIST):
            return False
        if random() < p:
            self._generateCar(frame)
            
            return True
        return False


