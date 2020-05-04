#!/usr/bin/python3

import math

from operator import itemgetter
from inputs import get_gamepad
from inputs import devices
from time import sleep

char_sets = [
    { 'id': 0, 'chars': ['a', 'b', 'c', 'd', 'e', 'backspace', 'left click'], 'start': 180, 'end': 224 },
    { 'id': 1, 'chars': ['f', 'g', 'h', 'i', 'j', 'ctrl', None], 'start': 225, 'end': 269  },
    { 'id': 2, 'chars': ['k', 'l', 'm', 'n', 'o', 'tab', 'shift'], 'start': 270, 'end': 314  },
    { 'id': 3, 'chars': ['p', 'q', 'r', 's', 't', 'alt', None], 'start': 315, 'end': 360  },
    { 'id': 4, 'chars': ['u', 'v', 'w', 'x', 'y', 'space', 'right click'], 'start': 0, 'end': 44  },
    { 'id': 5, 'chars': ['z', '/', '\'', '-', ',', 'delete', 'num'], 'start': 45, 'end': 89  },
    { 'id': 6, 'chars': [0, 9, 8, 7, 6, 'enter', 'mouse'], 'start': 90, 'end': 134  },
    { 'id': 7, 'chars': [5, 4, 3, 2, 1, None, 'cap'], 'start': 135, 'end': 179  }
]

colors = [
    { 'id': 0, 'name': 'orange', 'start': 180, 'end': 223 },
    { 'id': 1, 'name': 'yellow', 'start': 225, 'end': 269 },
    { 'id': 2, 'name': 'green', 'start': 270, 'end': 314 },
    { 'id': 3, 'name': 'blue', 'start': 315, 'end': 360 },
    { 'id': 4, 'name': 'purple', 'start': 0, 'end': 44 },
    # { 'id': 5, 'name': 'pink', 'start': 45, 'end': 89 }, ## not sure what this color is used for
    { 'id': 6, 'name': 'black', 'start': 90, 'end': 134 },
    # { 'id': 7, 'name': 'red', 'start': 135, 'end': 179 }, ## not sure what this color is used for
]

class InputDevice:
    def __init__(self, name):
        self.name = name
        self.active_color = None
        self.active_charset = None
        self.current_char = None
        self.pos_buffer_percent = .05
        self.circle_buffer_degs = 2
        self.stick_values = {
            'left': { 'max': 0, 'pos': { 'x': 0, 'y': 0 }, 'has_reset': True },
            'right': { 'max': 0, 'pos': { 'x': 0, 'y': 0 }, 'has_reset': True }
        }

    # max values need to be set to allow for a buffer percentage to be used
    def set_stick_maxes(self, curr_stick, curr_value):
        stick = curr_stick['stick']
        recorded_max = self.stick_values[stick]['max']
        if curr_value > recorded_max:
            self.stick_values[stick]['max'] = curr_value

    # position of the stick that's used to determine color/charset
    def get_pos_in_degrees(self, x, y):
        theta = math.atan2(y, x)
        theta = theta * 180 / math.pi
        if theta < 0:
            theta = theta + 360
        return theta

    # prevents input from registering early for best accuracy
    def check_if_allowed_pos_value(self, stick, axis, value):
        other_axis = 'y' if axis == 'x' else 'x'
        other_value = self.stick_values[stick]['pos'][other_axis]
        max_value = self.stick_values[stick]['max']
        buffer_percent = self.pos_buffer_percent
        min_allowed = max_value * buffer_percent
        if abs(value) > max_value - min_allowed:
            return True
        elif abs(other_value) > max_value - min_allowed:
            return True
        return False

    # assigns the correct array item for color or charset based on pos
    def get_stick_designation(self, stick):
        interval = 45  # degrees until next position
        coords = self.stick_values[stick]['pos']
        x, y = itemgetter('x', 'y')(coords)
        # coords input could be { -y, x } to rotate 90 degrees
        degrees = round(self.get_pos_in_degrees(x, y))
        array = char_sets if stick == 'left' else colors
        for item in array:
            if degrees >= item['start'] and degrees <= item['end']:
                return item

    # used to choose the character from the charset
    def set_active_color(self):
        color = self.get_stick_designation('right')
        self.active_color = color

    def set_active_charset(self):
        charset = self.get_stick_designation('left')
        self.active_charset = charset
        self.stick_values['left']['has_reset'] = False

    def stick_action_switch(self, stick):
        action_switcher = {
            'right': self.set_active_color,
            'left': self.set_active_charset
        }
        return action_switcher.get(stick)()

    # determines if stick value can be set before setting
    def set_stick_pos(self, curr_stick, value):
        # print(self.stick_values['left']['has_reset'])
        stick = curr_stick['stick']
        axis = curr_stick['axis']
        is_allowed = self.check_if_allowed_pos_value(stick, axis, value)
        new_pos = value
        if not is_allowed:
            self.reset_charset_or_color(stick)
            new_pos = 0
            if stick == 'left':
                self.stick_values['left']['has_reset'] = True
        self.stick_values[stick]['pos'][axis] = new_pos
        return new_pos

    def set_current_char(self):
        color = self.active_color
        charset = self.active_charset
        if color and charset:
            self.current_char = charset['chars'][color['id']]
            self.reset_charset_or_color('left')
            self.stick_values['left']['has_reset'] = False

    def get_current_char(self):
        if self.current_char == None:
            return ''
        return self.current_char

    def reset_charset_or_color(self, stick):
        if stick == 'left':
            self.active_charset = None
        else:
            self.active_color = { 'id': 6 }

    def reset_stick_pos(self, stick):
        self.stick_values[stick]['pos'] = { 'x': 0, 'y': 0 }

    def reset_current_char(self):
        self.current_char = None

gamepad = InputDevice('pad')

# input names are from the inputs package
stick_data = {
    'ABS_X': { 'stick': 'left', 'axis': 'x'},
    'ABS_Y': { 'stick': 'left', 'axis': 'y'},
    'ABS_RX': { 'stick': 'right', 'axis': 'x'},
    'ABS_RY': { 'stick': 'right', 'axis': 'y'},
}

# kill program if no gamepads are detected
def check_for_gamepads():
    if len(devices.gamepads) < 1:
        raise Exception('No controllers detected.  Please plug in a controller and restart the program.')

# initial controller setup, for setting max values but could be used for binding special keys as well
def setup_controller_event_loop():
    looping = True
    while looping:
        events = get_gamepad()
        for event in events:
            isStick = stick_data.get(event.code, None)
            if isStick:
                if event.state != 1 or event.state != -1:
                    gamepad.set_stick_maxes(stick_data[event.code], event.state)
            elif event.state != 0:
                    looping = False

def setup_sticks():
    check_for_gamepads()
    print('Spin the analog sticks in circles and the press any button when you are done')
    setup_controller_event_loop()
    print('Setup Complete!')
    print('Move the left stick to a color and move the right stick to a character set to start typing')


setup_sticks()

# controller listener
# loops until program is closed
def event_loop():
    while True:
        has_reset = gamepad.stick_values['left']['has_reset']
        events = get_gamepad()
        for event in events:
            curr_stick = stick_data.get(event.code, None)
            if curr_stick:
                new_pos = gamepad.set_stick_pos(curr_stick, event.state)
                # check for active pos change before running code
                if new_pos != 0:
                    # set either color or charset
                    gamepad.stick_action_switch(curr_stick['stick'])
                    # once color and charset are set, a current char can be selected
                    gamepad.set_current_char()
                    # has_reset flag is used to prevent unwanted duplicate chars
                    if has_reset and gamepad.current_char:
                        print(gamepad.current_char)
                        gamepad.reset_current_char()


event_loop()
