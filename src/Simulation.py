from .Lane import Lane
from .Car import Car, GUSTAVO, V_DESIRED, V_MIN, CAR_LENGTH, PIXEL_PER_M  # Note that CAR_HEIGHT is set in Simulation.render
from .Output import AbstractOutput
from numpy import mean
import pygame

RENDER = True

WIDTH, HEIGHT = 1200, 600  # 1500, 720 blas computer
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
white = (255, 255, 255)
grey = (128, 128, 128)
black = (0, 0, 0)
temp = max(V_MIN, V_DESIRED - 3*GUSTAVO/3.6)
# B is meters per second: A converts m/s to 0-255
A, B = (255-0)/(V_DESIRED + 3*GUSTAVO/3.6 - temp), -temp

if RENDER:
    pygame.init()
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    window.fill(white)
    font = pygame.font.Font("freesansbold.ttf",21)
    font2 = pygame.font.Font("freesansbold.ttf",10)

class Simulation:
    image = pygame.image.load('media/auto.png')
    begin_draw = WIDTH - WIDTH
    # dt given in seconds

    def __init__(self, output: AbstractOutput, dt:float = 1, lanes: int = 1, cars: list[int] = [1]):
        self.lanes: list[Lane] = [Lane(cars[i]) for i in range(lanes)]
        self.dt = dt
        self.output = output  # File to write interesting data to
        self.frames = 0
        if (not RENDER):
            pygame.quit()
    
    def update(self):
        for lane in self.lanes:
            i = self.lanes.index(lane)
            carsOvertaking = lane.update(self.dt)
            if (carsOvertaking is None):
                continue
            for car in carsOvertaking:
                if (i - car.overtaking == -1 or i - car.overtaking == len(self.lanes)):
                    #car.overtaking = 0
                    continue
                desiredLane = self.lanes[i-car.overtaking]
                canOvertake = True
                scale = 1
                if (car.overtaking == 1):
                    scale = 2
                theLastCar = None
                for othercar in desiredLane.vehicles:
                    if (othercar.x - car.x > 1000*PIXEL_PER_M):  # TODO: Maybe we can put an abs term here?
                        break # No need to waste resources and check cars beyond 1km.
                    
                    delta_v = car.vel
                    if (car.x > othercar.x): 
                        delta_v = max(0, othercar.vel - car.vel)
                    else:
                        delta_v = max(0, car.vel - othercar.vel)
                    SafetyDist = scale * 2 * delta_v * PIXEL_PER_M + 2*PIXEL_PER_M
                    # NOTICE: I removed the 2* and 3* factors here bc i feel they're inconsistent
                    if (car.x - CAR_LENGTH - SafetyDist < othercar.x < car.x + CAR_LENGTH + SafetyDist):
                        canOvertake = False
                        break
                    
                    if (car.overtaking == 1 and othercar.x < car.x):
                        theLastCar = othercar
                    # NOTICE: The 2*s0 factor is a bit arbitrary. As long as its > car's overtaking factor 
                    # (see: OVTF in Car.py) it's ok.
                    # Additionally: we abuse Python's lazy evaluation of these expressions. If any of the first return false, desiredDist isn't called
                    if (car.overtaking == -1 and othercar.x > car.x and 
                        othercar.x - CAR_LENGTH - car.x < 1.5*max(car.desiredDist(othercar),0)*PIXEL_PER_M):
                        #Prevents merging when the car in front will cause us to hit our brakes (quite hard!)
                        canOvertake = False
                        break
                if (canOvertake and car.overtaking == 1 and theLastCar is not None and 
                    car.x - CAR_LENGTH - theLastCar.x < 1.5*theLastCar.desiredDist(car)*PIXEL_PER_M):
                    canOvertake = False
                if (canOvertake and car.x < lane.length):
                    #print("Im mergin here",car.x)
                    desiredLane.vehicles.append(car)
                    lane.vehicles.remove(car)
                    desiredLane.vehicles.sort(key=lambda c: c.x)
                    
                car.overtaking = 0
            
        self.frames += 1
        if RENDER:
            self.render()
        # print(self.getAvgSpeed()*3.6)
        
    def getAvgSpeed(self) -> float:
        speeds: list[float] = []
        for lane in self.lanes:
            speeds.append(lane.getAvgSpeed())
        if len(speeds) == 0:
            speeds = [0]
        return mean(speeds)

    def getCars(self) -> int:
        cars = 0
        for lane in self.lanes:
            cars += len(lane.vehicles)
        return cars
        
    def render(self):
        if (self.frames % int(2/self.dt) == 0):
            # Draw statistics
            pygame.draw.rect(window, white, pygame.Rect(0, 0, WIDTH, 90))
            avd_text = font.render("Avg desired speeds: " + str([round(lane.getAvgDesiredSpeeds()*3.6) for lane in self.lanes]) + " km/h",
                                   True, black,white)
            av_text = font.render("Avg speeds: " + str([round(lane.getAvgSpeed() * 3.6) for lane in self.lanes]) + " km/h",
                                  True, black, white)
            # av_text = font.render("No. of cars: "+ str(self.getCars()) + " cars",True,black,white)
            window.blit(avd_text, (0, 0))
            window.blit(av_text, (0, 30))

        clock = font.render("T+" + str(round(self.frames*self.dt)) + " s",True,black,white)
        window.blit(clock, (0, 60))

        # Draw lanes
        n = len(self.lanes)
        LANE_HEIGHT, LINE_HEIGHT = 20, 1
        empty_space_above = (HEIGHT - LANE_HEIGHT*n)/2
        pygame.draw.rect(window, grey, pygame.Rect(0, empty_space_above, WIDTH, LANE_HEIGHT*n+LINE_HEIGHT*(n-1)))
        for i in range(n-1):
            y = empty_space_above + LANE_HEIGHT + (LANE_HEIGHT+LINE_HEIGHT)*i
            pygame.draw.rect(window, black, pygame.Rect(0, y, WIDTH, LINE_HEIGHT))

        # Draw cars
        CAR_HEIGHT = 10
        for lane in self.lanes:
            lane_num = self.lanes.index(lane)
            for i in range(len(lane.vehicles)):
                car = lane.vehicles[i]
                if (0 < car.x - self.begin_draw < WIDTH):
                    if (i < len(lane.vehicles) - 1):
                        car.beep(self.frames*self.dt,lane.vehicles[i+1],(self.begin_draw, self.begin_draw + WIDTH))
                    draw_x = car.x - self.begin_draw
                    draw_y = empty_space_above + (LANE_HEIGHT+LINE_HEIGHT) * lane_num + int((LANE_HEIGHT-CAR_HEIGHT)/2)

                    color = (A * (car.desiredvel + B), 0, 255 - A * (car.desiredvel + B))
                    if (color[0] >= 255):
                        color = (255, 0, 0)
                    elif (color[0] <= 0):
                        color = (0, 0, 255)

                    if car.debug:
                        color = (0, 255, 0)
                    # Draw safety distance to pass, in front, and to merge
                    # SafetyDist = max(car.vel*3,CAR_LENGTH)  # outdated code
                    in_front_dist = car.s0 * PIXEL_PER_M
                    #print(in_front_dist)
                    # pygame.draw.rect(window, (0, 160, 0),
                    #                     pygame.Rect(draw_x + CAR_LENGTH, draw_y + 32, 3*SafetyDist, 4))
                    # pygame.draw.rect(window, (0, 160, 0),
                    #                     pygame.Rect(draw_x - 2*SafetyDist, draw_y + 32, 2*SafetyDist, 4))
                    # SafetyDist *= 2

                    # pygame.draw.rect(window, (0, 100, 0),
                    #                     pygame.Rect(draw_x + CAR_LENGTH, draw_y + 24, 3*SafetyDist, 4))
                    # pygame.draw.rect(window, (0, 100, 0),
                    #                     pygame.Rect(draw_x-2*SafetyDist, draw_y + 24, 2*SafetyDist, 4))

                    pygame.draw.rect(window, color, pygame.Rect(draw_x + CAR_LENGTH, draw_y + int(CAR_HEIGHT/2), in_front_dist, 1))
                            
                    pygame.draw.rect(window, color, pygame.Rect(draw_x, draw_y, CAR_LENGTH, CAR_HEIGHT))
                    # window.blit(self.image,(draw_x, draw_y))
                    acc_text = font2.render(str(round(car.vel*3.6)), True, white, color)
                    window.blit(acc_text, (draw_x,draw_y))

        # Draw buttons and check if there being hovered over
        pygame.draw.rect(window, red, pygame.Rect(0, HEIGHT-40, 40, 40))
        pygame.draw.rect(window, green, pygame.Rect(50, HEIGHT-40, 40, 40))
        mouse = pygame.mouse.get_pos()
        if 0 < mouse[0] < 40 and HEIGHT-40 < mouse[1] < HEIGHT:
            self.begin_draw -= 160*self.dt*PIXEL_PER_M
        if 50 < mouse[0] < 90 and HEIGHT-40 < mouse[1] < HEIGHT:
            self.begin_draw += 160*self.dt*PIXEL_PER_M
        window_pos = font.render(str(round(self.begin_draw)), True, black, white)
        pygame.draw.rect(window, white, pygame.Rect(90,HEIGHT-40,100,40))
        window.blit(window_pos, (100, HEIGHT-20))
        
        pygame.display.update()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.quit()    
                RENDER = False
            if event.type == pygame.WINDOWEXPOSED:
                # print("OK")
                pass
            
    def runNormalSpeedSim(self):
        try:
            cars = sum([len(lane.vehicles) for lane in self.lanes])
            while (cars > 0):
                self.update()
                for lane in self.lanes:
                    for car in lane.finishedVehicles:
                        # print("CAR KILLED")
                        self.output.write(str(self.frames*self.dt) + '\n')
                        self.output.save(self.frames*self.dt)
                        cars -= 1
                    lane.flushVehicles()
        except Exception as e:
            print(e)
        return
        
    def runNormalManyCarSim(self, carcap=10, timestep=20):
        # """ #ABANDON ALL HOPE ALL YE ENTER HERE
        # Come on bro there's never any issues
        carsgenerated = 0
        cars = sum([len(lane.vehicles) for lane in self.lanes])
        while (cars > 0 or carsgenerated < carcap):
            # print(cars)
            self.update()
            # self.output.save(self.getAvgSpeed()*3.6)
            # print("not stuck here",self.frames)
            
            if (cars == 1):
                # print("cyka")
                pass
                
            for lane in self.lanes:
                for car in lane.finishedVehicles:
                    # self.output.write(str(self.frames*self.dt) + '\n')
                    self.output.save((self.frames - car.spawnframe)*self.dt)
                    cars -= 1
                    # print("CAR KILLED")
                lane.flushVehicles()
                
                if (carsgenerated < carcap):
                    factor = 1  # len(self.lanes) - self.lanes.index(lane)
                    if (lane.generateCarT(timestep*factor,self.frames)):
                        cars += 1
                        carsgenerated += 1
                        # self.output.save(lane.vehicles[0].desiredvel)
                        # print("CAR BIRTHED")
        # """
        return

    def manyCarsPP(self, p: float, carcap=10):
        """Run a complete simulation, generating carcap cars, with p the probability parameter"""
        carsgenerated = 0
        cars = self.getCars()
        while (cars > 0 or carsgenerated < carcap):
            data_bit = []  # list to gather data we want to save each frame
            # print(cars)
            self.update()
            # self.output.save(self.getAvgSpeed()*3.6)

            for lane in self.lanes:
                for car in lane.finishedVehicles:
                    self.output.save((self.frames - car.spawnframe)*self.dt)  # time it took to get to the end
                    cars -= 1
                lane.flushVehicles()
                
                if (carsgenerated < carcap):
                    if (lane.generateCarP(p*self.dt,self.frames)):
                        cars += 1
                        carsgenerated += 1

            if len(data_bit) != 0:
                self.output.save(data_bit)

        return




