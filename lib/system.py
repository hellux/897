from kivy.core.window import Window

from os import environ, name
from sys import version




def platform():
	if "ANDROID" in str(environ):
		return "android"
	if name == "nt" or name == "posix":
		return "pc"
if platform() == "pc":
    Window.size = 1920, 1080
WIDTH, HEIGHT = Window.size
PY_VER = version[:version.find("(")-1] + "\n" + version[version.find("[")+1:-1]

LU = (WIDTH**2 + HEIGHT**2)**0.5 / 1000

def lu(length_units):
	"""returns value in length units converted to pixels"""
	return LU*length_units
