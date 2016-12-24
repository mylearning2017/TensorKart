import pygame
import uinput

import wx
wx.App()

import numpy as np
from skimage.color import rgb2gray
from skimage.transform import resize

IMG_W = 320
IMG_H = 240


def take_screenshot():
    screen = wx.ScreenDC()
    size = screen.GetSize()
    bmp = wx.Bitmap(size[0], size[1])
    mem = wx.MemoryDC(bmp)
    mem.Blit(0, 0, size[0], size[1], screen, 0, 0)
    return bmp.GetSubBitmap(wx.Rect([0,0],[640,480]))


def prepare_image(img):
    if(type(img) == wx._core.Bitmap):
        buf = img.ConvertToImage().GetData()
        img = np.frombuffer(buf, dtype='uint8')


    img = img.reshape(480, 640, 3)
    img = rgb2gray(img)
    img = resize(img, [IMG_H, IMG_W])
    img = img.flatten()

    return img


class FakeController:
    def __init__(self):
        self.device = uinput.Device([
            uinput.ABS_X,
            uinput.ABS_Y,
            uinput.BTN_SOUTH, # a
            uinput.BTN_NORTH, # x
            uinput.BTN_TR # rb
        ])

    # button mappings determined using evtest
    def write(self, output):
        #print output

        ## calibration
        x_axis = int(output[0] * 32767)
        y_axis = int(output[1] * 32767)
        btn_a = int(round(output[2]))
        btn_b = int(round(output[3]))
        btn_rb = int(round(output[4]))

        # print command
        print [x_axis, y_axis, btn_a, btn_b, btn_rb]

        self.device.emit(uinput.ABS_X, x_axis)
        self.device.emit(uinput.ABS_Y, y_axis)
        self.device.emit(uinput.BTN_SOUTH, btn_a)
        self.device.emit(uinput.BTN_NORTH, btn_b)
        self.device.emit(uinput.BTN_TR, btn_rb)


class XboxController:
    def __init__(self):
        try:
            pygame.init()
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        except:
            print 'unable to connect to Xbox Controller'


    def read(self):
        pygame.event.pump()
        x = self.joystick.get_axis(0)
        y = self.joystick.get_axis(1)
        a = self.joystick.get_button(0)
        b = self.joystick.get_button(2) # b=1, x=2
        rb = self.joystick.get_button(5)
        return [x, y, a, b, rb]


    # used to toggle manual override for now
    def btn_b(self):
        pygame.event.pump()
        return self.joystick.get_button(1)


class Data(object):
    def __init__(self):
        self._X = np.load("data/X.npy")
        self._y = np.load("data/y.npy")
        self._epochs_completed = 0
        self._index_in_epoch = 0
        self._num_examples = self._X.shape[0]

    def next_batch(self, batch_size):
        start = self._index_in_epoch
        self._index_in_epoch += batch_size
        if self._index_in_epoch > self._num_examples:
            # Finished epoch
            self._epochs_completed += 1
            # Shuffle the data
            perm = np.arange(self._num_examples)
            np.random.shuffle(perm)
            self._X = self._X[perm]
            self._y = self._y[perm]
            # Start next epoch
            start = 0
            self._index_in_epoch = batch_size
            assert batch_size <= self._num_examples
        end = self._index_in_epoch
        return self._X[start:end], self._y[start:end]