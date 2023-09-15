from .Car import Car
from numpy import linspace

class Lane:
    def __init__(self, cars: int = 0):
        self.length = 5000 #5 km
        xcoords = linspace(0,self.length,cars)
        self.vehicles: list[Car] = [Car(xcoords[i]) for i in range(cars)]
        self.finishedVehicles: list[Car] = []

    
    def update(self,dt: float):
        numOfCars = len(self.vehicles)
        if (numOfCars == 0):
            return
        carsToRemove: list[int] = []
        for i in range(numOfCars):
            if (i == numOfCars-1):
                self.vehicles[i].update(dt) 
            else:
                self.vehicles[i].update(dt,self.vehicles[i+1])
            if (self.vehicles[i].x > self.length):
                carsToRemove.append(i)
                
        carsToRemove.sort(reverse=True)
        for index in carsToRemove:
            self.finishedVehicles.append(self.vehicles.pop(index))
        
    def flushVehicles(self):
        '''Removes finished vehicles from memory'''
        self.finishedVehicles = []




