"""contains all classes for player"""

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, ReferenceListProperty
from kivy.vector import Vector

from math import cos, sin, atan, pi
from random import randint

from lib.system import WIDTH, HEIGHT, lu

class EnsPlayer(Widget):
    """Player class"""

    w, h = 0, 0 #width, height
    cx, cy = NumericProperty(0), NumericProperty(0)
    cpos = ReferenceListProperty(cx, cy) #center of ship
    points = ListProperty([0,0,0,0,0,0,0,0])
    color = ListProperty([1, 0.8, 0.3, 1])
    cosv, sinv = 0, 1
    pivot = pi/2
    
    vel_x, vel_y = NumericProperty(0), NumericProperty(0)
    vel = ReferenceListProperty(vel_x, vel_y)
    vel_friction = 0.97
    vel_boost_increase = 0 
   
    boost = False
    boost_touch_id = None    
    turn = False
    turn_direction = False #left/right
    turn_touch_id = None

    alive = False
    safe_mode = False
    shoot_allowed = True

    def __init__(self, **kwargs):
        super(EnsPlayer, self).__init__(**kwargs)

    def reset(self):
        """remove all children widgets and set all values to start values"""
        self.clear_widgets()
        self.color[1] = 0.8
        self.h = lu(30)
        self.w = self.h * 0.75
        self.vel_boost_increase = self.w * 0.012
        self.pivot = pi/2
        self.cosv = 0
        self.sinv = 1
        self.cpos = WIDTH/2, HEIGHT/2
        self.alive = True

    def die(self):
        """create two pieces of player mesh"""
        self.parent.animate_explosion(self.cpos)
        vertices_1 = []
        vertices_2 = []
        l_a = randint(30, 125)/100.0 * self.w
        l_b = randint(30, 125)/100.0 * self.w
        vel_m = self.w/100
        v_a = self.pivot - atan(self.w/(self.h*2)) 
        v_b = self.pivot + atan(self.w/(self.h*2))
        slice_a = self.points[0] - l_a*cos(v_a), self.points[1] - l_a*sin(v_a)
        slice_b = self.points[0] - l_b*cos(v_b), self.points[1] - l_b*sin(v_b)
        remain_1 = EnsPlayerRemains([   self.points[0], self.points[1], 0, 0,
                                        slice_a[0], slice_a[1], 0, 0, 
                                        slice_b[0], slice_b[1], 0, 0
                                    ], 
                                [0, 1, 2],
                                [   self.vel_x+vel_m*cos(self.pivot), 
                                    self.vel_y+vel_m*sin(self.pivot)
                                    ]
                                )
        remain_2 = EnsPlayerRemains([   slice_a[0], slice_a[1], 0, 0,
                                        self.points[2], self.points[3], 0, 0, 
                                        self.points[4], self.points[5], 0, 0,
                                        self.points[6], self.points[7], 0, 0,
                                        slice_b[0], slice_b[1], 0, 0
                                    ],
                                [0, 1, 2, 3, 4], 
                                    [   self.vel_x-vel_m*cos(self.pivot), 
                                        self.vel_y-vel_m*sin(self.pivot)
                                    ]
                                 )
        self.add_widget(remain_1)
        self.add_widget(remain_2)
        self.alive = False
        self.w = 0
        self.h = 0

    def set_points(self):
        """set point positions for mesh relative to cx, cy"""
        self.points = [ self.cx + self.h/2*self.cosv,
                        self.cy + self.h/2*self.sinv,
                        self.cx - ( self.h*self.cosv + self.w*self.sinv ) / 2,
                        self.cy - ( self.h*self.sinv - self.w*self.cosv ) / 2,
                        self.cx - self.h/3*self.cosv,
                        self.cy - self.h/3*self.sinv,
                        self.cx - ( self.h*self.cosv - self.w*self.sinv ) / 2,
                        self.cy - ( self.h*self.sinv + self.w*self.cosv ) / 2
                      ]
        x_min, x_max, y_min, y_max = self.cx, self.cx, self.cy, self.cy
        for i, point in enumerate(self.points):
            if not i%2:
                if point < x_min: x_min = point
                if point > x_max: x_max = point
            else:
                if point < y_min: y_min = point
                if point > y_max: y_max = point
        self.x = x_min
        self.y = y_min
        self.width = abs(x_min-x_max)
        self.height = abs(y_min-y_max)

    def allow_shoot(self, dt): self.shoot_allowed = True
    
    def remove_safe_mode(self, dt): 
        self.safe_mode = False
        self.color[3] = 1

    def move(self):
        """update all values and widget"""
        #pos + vel
        self.cpos = Vector(*self.vel) + self.cpos
        #post death
        for remain in self.children:
            remain.move()
        #boost
        if self.boost:
            self.vel_x += self.vel_boost_increase*self.cosv
            self.vel_y += self.vel_boost_increase*self.sinv
            self.color[1] *= 0.99
        elif self.color[1] < 0.8:
            self.color[1] += (1-self.color[1])/100
        #rotate 
        if self.turn:
            if self.turn_direction:
                self.pivot = (self.pivot+pi/36)%(2*pi) #left
            else:
                self.pivot = (self.pivot-pi/36)%(2*pi) #right            
            #calculate cosv and sinv for current frame
            self.cosv = cos(self.pivot)
            self.sinv = sin(self.pivot)
        #friction
        if abs(self.vel_x) + abs(self.vel_y) > 0.1:
            self.vel_x *= self.vel_friction
            self.vel_y *= self.vel_friction
        else:
            self.vel_x = 0
            self.vel_y = 0
        #teleport
        if not -self.h/2 < self.cx < self.parent.width+self.h/2:
            self.cx = WIDTH - self.cx
        if not -self.h/2 < self.cy < self.parent.height+self.h/2:
            self.cy = HEIGHT - self.cy
        self.set_points()

class EnsPlayerRemains(Widget):
    """class for player widgets post death"""
    vertices = ListProperty(None)
    indices = ListProperty(None)
    vel_x = NumericProperty(0)
    vel_y = NumericProperty(0)
    vel = ReferenceListProperty(vel_x, vel_y)
    color = ListProperty([0,0,0,0])

    def __init__(self, vertices, indices, vel):
        super(EnsPlayerRemains, self).__init__()
        self.vertices = vertices
        self.indices = indices
        self.vel = vel
        self.disabled = True
    
    def move(self):
        self.color = self.parent.color
        for i in range(len(self.vertices)):
            if not i%4:
                self.vertices[i] += self.vel_x
            if not (i-1)%4:
                self.vertices[i] += self.vel_y
        #friction
        if abs(self.vel_x) + abs(self.vel_y) > 0.1:
            self.vel_x *= self.parent.vel_friction
            self.vel_y *= self.parent.vel_friction
        else:
            self.vel_x = 0
            self.vel_y = 0
