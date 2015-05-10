from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, ReferenceListProperty
from kivy.vector import Vector

from math import cos, sin, pi
from random import randint

from lib.system import WIDTH, HEIGHT

class EnsAsteroid(Widget):
    vel_x = NumericProperty(0)
    vel_y = NumericProperty(0)
    vel = ReferenceListProperty(vel_x, vel_y)
    m_vertices = []
    mesh_offset = ListProperty([0, 0])
    vertices = ListProperty(None)
    indices = ListProperty(None)
    diameters = { "small": 20, "medium": 40, "large": 80 }
    color = ListProperty([0, 0, 0])

    def __init__(self, pos, size, vel, color):
        super(EnsAsteroid, self).__init__()
        self.diameter = size
        self.pos, self.size, self.m_vertices, self.indices,\
        self.mesh_offset = self.create_mesh(pos, 7, self.diameters[size])
        self.vel = vel
        self.set_vertices(len(self.m_vertices))        
        self.color = color

    def create_mesh(self, pos, step, diameter):
        vertices = []
        indices = []
        noise = diameter*3/4
        istep = pi*2/step
        x_min, y_min = diameter, diameter
        x_max, y_max = 0, 0
        for i in range(step):
            x = cos(istep*i) * (diameter + randint(-noise, noise))
            y = sin(istep*i) * (diameter + randint(-noise, noise))
            vertices.extend([x, y, 0, 0])
            indices.append(i)
            if x < x_min: x_min = x
            if x > x_max: x_max = x
            if y < y_min: y_min = y
            if y > y_max: y_max = y
        mesh_offset = [x_min, y_min]
        pos = Vector(*mesh_offset) + pos
        size = abs(x_max-x_min), abs(y_max-y_min)
        return pos, size, vertices, indices, mesh_offset

    def set_vertices(self, n):
        self.vertices = []
        for i in xrange(n):
            if not i%4:
                self.vertices.append(self.x+self.m_vertices[i]-self.mesh_offset[0])
            elif not (i-1)%4:
                self.vertices.append(self.y+self.m_vertices[i]-self.mesh_offset[1])
            else:
                self.vertices.append(0)

    def move(self):
        self.pos = Vector(*self.vel) + self.pos
        self.set_vertices(len(self.vertices))
        if self.center_x < 0:
            self.center_x = WIDTH
        if self.center_x > WIDTH:
            self.center_x = 0
        if self.center_y < 0:
            self.center_y = HEIGHT
        if self.center_y > HEIGHT:
            self.center_y = 0
