from io import TextIOWrapper
from .Lane import Lane
from .Car import Car
from .Output import AbstractOutput
from numpy import mean
import pygame

pygame.init()
WIDTH, HEIGHT = 1400, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.Font("freesansbold.ttf",32)
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
white = (255,255,255)
grey = (128,128,128)
black = (0,0,0)
window.fill(white)

class Simulation:
    image = pygame.image.load('auto.png')
    #dt given in seconds
    def __init__(self, output: AbstractOutput, dt:float = 1, lanes: int = 1, cars: list[int] = [1]):
        self.lanes: list[Lane] = [Lane(cars[i]) for i in range(lanes)]
        self.dt = dt
        self.output = output #File to write interesting data to
        self.frames = 0
        self.RENDER = True
    
    def update(self):
        for lane in self.lanes:
            lane.update(self.dt)
        self.frames += 1
        if (self.RENDER):
            self.render()
        
    def getAvgSpeed(self) -> float:
        speeds = []
        for lane in self.lanes:
            for car in lane.vehicles:
                speeds.append(car.vel)
        return mean(speeds)
        
    def render(self):
        if (self.RENDER):
            
            text = font.render("Avg speed: "+ str(round(self.getAvgSpeed()*3.6)) + " km/h",True,black,white)
            textRect = text.get_rect()
            textRect.center = (100,100)
            window.blit(text,textRect)
            # draw road
            pygame.draw.rect(window, grey, pygame.Rect(0, 200, WIDTH, 100))
    
            # draw cars!
            for lane in self.lanes:
                for car in lane.vehicles:
                    pygame.draw.rect(window, black, pygame.Rect(car.x-(5000-WIDTH), 220, 10, 60))
                    #if (WIDTH > car.x-(5000-WIDTH) > 200 ):
                    #window.blit(self.image,(car.x, 220))
            pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.quit()    
                self.RENDER = False

    def runNormalSpeedSim(self):
        cars = sum([len(lane.vehicles) for lane in self.lanes])
        while (cars > 0):
            self.update()
            for lane in self.lanes:
                for car in lane.finishedVehicles:
                    #print("CAR KILLED")
                    self.output.write(str(self.frames*self.dt) + '\n')
                    self.output.save(self.frames*self.dt)
                    cars -= 1
                lane.flushVehicles()
        return
        
    def runNormalManyCarSim(self, carcap = 10,timestep = 20):
        carsgenerated = 0
        cars = sum([len(lane.vehicles) for lane in self.lanes])
        while (cars > 0):
            self.update()
                
            for lane in self.lanes:
                for car in lane.finishedVehicles:
                    self.output.write(str(self.frames*self.dt) + '\n')
                    self.output.save(self.frames*self.dt)
                    cars -= 1
                    #print("CAR KILLED")
                lane.flushVehicles()
                        
                if (self.frames % timestep == timestep-1) and (carsgenerated < carcap):
                    #print("CAR BORN")
                    lane.vehicles.insert(0,Car())
                    carsgenerated += 1
                    cars += 1
                    
        return
