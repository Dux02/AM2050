from .Car import Car
from numpy import linspace, mean
from random import randint, random

SPAWNSAFETYDIST = 200

class Lane:
    def __init__(self, cars: int = 0):
        self.length = 40*5000 #5 km 40 pixels = 1 m
        xcoords = linspace(0,self.length,cars)
        self.vehicles: list[Car] = [Car(xcoords[i]) for i in range(cars)]
        self.finishedVehicles: list[Car] = []
        self.timeSinceLastCarGenerated = 0

    
    def update(self,dt: float) -> list[Car]:
        numOfCars = len(self.vehicles)
        if (numOfCars == 0):
            return
        carsToRemove: list[int] = []
        carsOvertaking: list[Car] = []
        for i in range(numOfCars):
            if (i == numOfCars-1):
                self.vehicles[i].update(dt) 
            else:
                self.vehicles[i].update(dt,self.vehicles[i+1])
                
            if (self.vehicles[i].overtaking != 0):
                    carsOvertaking.append(self.vehicles[i])
            if (self.vehicles[i].x > self.length):
                carsToRemove.append(i)
                
        carsToRemove.sort(reverse=True)
        for index in carsToRemove:
            self.finishedVehicles.append(self.vehicles.pop(index))
        return carsOvertaking
        

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
    
    def generateCarT(self,timestep:int,frame:int) -> bool:
        '''
        T STANDS FOR TIMESTAMP - FOR PROBABILISTIC GENERATION SEE generateCarP
        Generates a car between 1 and 2 timesteps since last car generated in the lane (wrt frame)
        If it successfully generates a car, it will return true, otherwise false.
        It will not spawn a car if there's not enough space to do so, regardless of the time since last spawn
        '''
        delta_i = frame - self.timeSinceLastCarGenerated
        if (delta_i < timestep):
            return False
        offset = randint(0,timestep-1)
        if ((delta_i % timestep == offset or delta_i >= 2*timestep)):
            #TODO: Make this more efficient? If we asssure index 0 is closest to start
            for car in self.vehicles:  
                if (car.x < SPAWNSAFETYDIST):
                    return False
            self.vehicles.insert(0,Car(spawnframe=frame))
            self.timeSinceLastCarGenerated = frame
            return True
        return False
    
    def generateCarP(self,p:float,frame:int) -> bool:
        '''
        P STANDS FOR PROBABILITY - FOR TIMED GENERATION SEE generateCarT
        Generates a car between 1 and 2 timesteps since last car generated in the lane (wrt frame)
        If it successfully generates a car, it will return true, otherwise false.
        It will not spawn a car if there's not enough space to do so, regardless of the time since last spawn
        '''
        if (random() < p):
            #TODO: Make this more efficient? If we asssure index 0 is closest to start
            for car in self.vehicles:  
                if (car.x < SPAWNSAFETYDIST):
                    return False
            self.vehicles.insert(0,Car(spawnframe=frame))
            self.timeSinceLastCarGenerated = frame
            return True
        return False