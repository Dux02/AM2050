from typing import Union
from .Simulation import Simulation
from .Output import AbstractOutput
from .Car import V_MIN, V_DESIRED, GUSTAVO, PIXEL_PER_M, CAR_LENGTH
import pygame

temp = max(V_MIN, V_DESIRED - 3*GUSTAVO/3.6)
# B is meters per second: A converts m/s to 0-255
A, B = (255-0)/(V_DESIRED + 3*GUSTAVO/3.6 - temp), -temp

class Renderer():
    image = pygame.image.load('media/auto.png')
    RENDER = False # NOT A HARDCODE OF IF WE RENDER OR NOT!!!
    
    WIDTH, HEIGHT = 1200, 600  # 1500, 720 blas computer
    red = (255, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    white = (255, 255, 255)
    grey = (128, 128, 128)
    black = (0, 0, 0)
    window = None
    begin_draw = 0
    
    
    def __init__(self) -> None:
        if not Renderer.RENDER:
            Renderer.RENDER = True
            pygame.init()
            Renderer.window = pygame.display.set_mode((Renderer.WIDTH, Renderer.HEIGHT))
            Renderer.window.fill(Renderer.white)
            Renderer.font = pygame.font.Font("freesansbold.ttf",21)
            Renderer.font2 = pygame.font.Font("freesansbold.ttf",10)
    
    def kill(self):
        pygame.display.quit()
        pygame

class VisualSimulation(Simulation):
    renderer: Union[None, Renderer] = None
    
    def initRenderer(self):
        if (VisualSimulation.renderer is None):
            VisualSimulation.renderer = Renderer()
        return
    
    def __init__(self, output: AbstractOutput, dt: float = 1, lanes: int = 1, cars: list[int] = [1]):
        super().__init__(output, dt, lanes, cars)
        self.rendering = True
        self.initRenderer()
        


    
    
    def update(self):
        super().update()
        if self.rendering:
            self.render()
    
    def render(self):
        rdr: Renderer = VisualSimulation.renderer
        if (self.frames % int(2/self.dt) == 0):
            # Draw statistics
            pygame.draw.rect(rdr.window, rdr.white, pygame.Rect(0, 0, rdr.WIDTH, 90))
            avd_text = rdr.font.render("Avg desired speeds: " + str([round(lane.getAvgDesiredSpeeds()*3.6) for lane in self.lanes]) + " km/h",
                                        True, rdr.black,rdr.white)
            av_text = rdr.font.render("Avg speeds: " + str([round(lane.getAvgSpeed() * 3.6) for lane in self.lanes]) + " km/h",
                                        True, rdr.black, rdr.white)
            # av_text = font.render("No. of cars: "+ str(self.getCars()) + " cars",True,black,white)
            rdr.window.blit(avd_text, (0, 0))
            rdr.window.blit(av_text, (0, 30))

        clock = rdr.font.render("T+" + str(round(self.frames*self.dt)) + " s",True, rdr.black, rdr.white)
        rdr.window.blit(clock, (0, 60))

        # Draw lanes
        n = len(self.lanes)
        LANE_HEIGHT, LINE_HEIGHT = 20, 1
        empty_space_above = (rdr.HEIGHT - LANE_HEIGHT*n)/2
        pygame.draw.rect(rdr.window, rdr.grey, pygame.Rect(0, empty_space_above, rdr.WIDTH, LANE_HEIGHT*n+LINE_HEIGHT*(n-1)))
        for i in range(n-1):
            y = empty_space_above + LANE_HEIGHT + (LANE_HEIGHT+LINE_HEIGHT)*i
            pygame.draw.rect(rdr.window, rdr.black, pygame.Rect(0, y, rdr.WIDTH, LINE_HEIGHT))

        # Draw cars
        CAR_HEIGHT = 10
        for lane in self.lanes:
            lane_num = self.lanes.index(lane)
            for i in range(len(lane.vehicles)):
                car = lane.vehicles[i]
                if car.debug:
                    rdr.begin_draw = car.x - CAR_LENGTH - 1
                if (0 < car.x - rdr.begin_draw < rdr.WIDTH):
                    # if (i < len(lane.vehicles) - 1):
                    #     car.beep(self.frames*self.dt,lane.vehicles[i+1],(rdr.begin_draw, rdr.begin_draw + WIDTH))
                    draw_x = car.x - rdr.begin_draw
                    draw_y = empty_space_above + (LANE_HEIGHT+LINE_HEIGHT) * lane_num + int((LANE_HEIGHT-CAR_HEIGHT)/2)

                    color = (A * (car.desiredvel + B), 0, 255 - A * (car.desiredvel + B))
                    if (color[0] >= 255):
                        color = (255, 0, 0)
                    elif (color[0] <= 0):
                        color = (0, 0, 255)

                    if car.debug:
                        color = (0, 255, 0)
                    in_front_dist = car.s0 * PIXEL_PER_M

                    pygame.draw.rect(rdr.window, color, pygame.Rect(draw_x + CAR_LENGTH, draw_y + int(CAR_HEIGHT/2), in_front_dist, 1))
                            
                    pygame.draw.rect(rdr.window, color, pygame.Rect(draw_x, draw_y, CAR_LENGTH, CAR_HEIGHT))
                    # window.blit(self.image,(draw_x, draw_y))
                    acc_text = rdr.font2.render(str(round(car.a,1)), True, rdr.white, color)
                    rdr.window.blit(acc_text, (draw_x, draw_y))

        # Draw buttons and check if there being hovered over
        pygame.draw.rect(rdr.window, rdr.red, pygame.Rect(0, rdr.HEIGHT-40, 40, 40))
        pygame.draw.rect(rdr.window, rdr.green, pygame.Rect(50, rdr.HEIGHT-40, 40, 40))
        mouse = pygame.mouse.get_pos()
        if 0 < mouse[0] < 40 and rdr.HEIGHT-40 < mouse[1] < rdr.HEIGHT:
            rdr.begin_draw -= 160*self.dt*PIXEL_PER_M
        if 50 < mouse[0] < 90 and rdr.HEIGHT-40 < mouse[1] < rdr.HEIGHT:
            rdr.begin_draw += 160*self.dt*PIXEL_PER_M
        window_pos = rdr.font.render(str(round(rdr.begin_draw)), True, rdr.black, rdr.white)
        pygame.draw.rect(rdr.window, rdr.white, pygame.Rect(90,rdr.HEIGHT-40,100,40))
        rdr.window.blit(window_pos, (100, rdr.HEIGHT-20))
        
        pygame.display.update()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                rdr.window.fill(rdr.white)
                text = rdr.font.render("Awaiting termination... See console",True,rdr.black,rdr.white)
                rdr.window.blit(text,(0,0))
                print("Awaiting Renderer.kill or next VisualSimulation call to delete pygamewindow...")
                pygame.display.update()
                self.rendering = False
            if event.type == pygame.WINDOWEXPOSED:
                # print("OK")
                pass
    
