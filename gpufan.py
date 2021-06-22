#!/usr/bin/env python

"""
AMD Gpu fan control
"""

###########################
# Params
###########################

# pid params
MIN_TEMP = 50
MAX_TEMP = 80
MIN_PWM = 38
MAX_PWM = 255
ALPHA = 0.8
LEAK = 0.007
P = 0.1
I = 0.01

# Device params
DEVICE = '/sys/class/drm/card0/device/hwmon/hwmon0'
EDGE_INPUT = '/temp1_input'
JUNC_INPUT = '/temp2_input'
MEM_INPUT = '/temp3_input'
VDD_INPUT = '/in0_input'
FAN_INPUT = '/fan1_input'
DEVICE_NAME = '/name'
PWM_OUT = '/pwm1'
PWM_ENABLE = f'{PWM_OUT}_enable'


###########################
# Functions
###########################


import os
import sys
import logging
import signal
from time import sleep

logging.basicConfig(level=logging.INFO)


DEBUG = os.environ.get('DEBUG')


def read(path):
    with open(path, 'r') as f:
        return str(f.read())


def read_int(path):
    return int(read(path))


def write(path, s):
    with open(path, 'w') as f:
        return f.write(str(s))


def clip(s, s_min=None, s_max=None):
    if isinstance(s_min, (float, int)):
        s = max(s, s_min)
    if isinstance(s_max, (float, int)):
        s = min(s, s_max)

    return s


def scale_state(state, output=False):
    if output:
        v = clip((state + MIN_PWM + 6) * MAX_PWM / (MAX_PWM + MIN_PWM), s_min=MIN_PWM)
    else:
        v = clip((state - MIN_PWM - 6) * MAX_PWM / (MAX_PWM - MIN_PWM), s_min=0.0)
    return v


def convert_output(signal):
    return clip(int(round(signal)), s_min=0, s_max=255)


def read_temp(input_path):
    return read_int(DEVICE + input_path) / 1000


def temp_to_pwm(temp):
    return clip((temp - MIN_TEMP) * MAX_PWM / (MAX_TEMP - MIN_TEMP), s_min=0.0)


def set_control_manual():
    write(DEVICE + PWM_ENABLE, 1)


def set_control_auto():
    write(DEVICE + PWM_ENABLE, 2)


###########################
# Main
###########################


def main():
  # check if device exists and is amdgpu
  if not os.path.isdir(DEVICE):
      logging.error('Device not found. Exiting.')
      sys.exit(1)

  if read(DEVICE + DEVICE_NAME) != 'amdgpu\n':
      logging.error('Device is not amdgpu. Exiting.')
      sys.exit(1)

  # cleanup function
  run = True
  def exitHandler(sig, frame):
      global run
      run = False
  signal.signal(signal.SIGTERM, exitHandler)
  signal.signal(signal.SIGINT, exitHandler)

  try:
      logging.info('Setting fan to manual control mode.')
      set_control_manual()

      # init vars
      acc = 0
      control = MIN_PWM

      logging.info('Running...')

      while run:
          try:
              # read inputs
              edge = read_temp(EDGE_INPUT)
              junction = read_temp(JUNC_INPUT)
              memory = read_temp(MEM_INPUT)
              fan = read_int(DEVICE + FAN_INPUT)
              vdd = read_int(DEVICE + VDD_INPUT)
              state = read_int(DEVICE + PWM_OUT)

              # calculate pid
              scaled_state = scale_state(state)
              target_state = temp_to_pwm(junction)

              prop = target_state - scaled_state
              acc = clip(acc * (1 - LEAK) + prop, s_min=-1e5, s_max=1e5)
              pi = prop * P + acc * I

              # first degree exponential moving average
              control = clip(control * ALPHA + pi * (1 - ALPHA), s_min=0.0, s_max=99999999999.0)

              # convert output
              output = convert_output(scale_state(control, output=True))

              # write output
              write(DEVICE + PWM_OUT, output)

              if DEBUG:
                  logging.info('============== env ==============')
                  logging.info(f' vddgfx:       {vdd} mV')
                  logging.info(f' edge:         {edge} C')
                  logging.info(f' junction:     {junction} C')
                  logging.info(f' memory:       {memory} C')
                  logging.info(f' state:        {state}')
                  logging.info(f' fan:          {fan} RPM')

                  logging.info('============== pid ==============')
                  logging.info(f' scaled_state: {scaled_state}')
                  logging.info(f' prop:         {prop}')
                  logging.info(f' acc:          {acc}')
                  logging.info(f' control:      {control}')
                  logging.info(f' output:       {output}')

              sleep(0.1)

          except KeyboardInterrupt:
              break

  except Exception as e:
      logging.exception(e)

  finally:
      logging.info('Setting fan to automatic control mode.')
      set_control_auto()


if __name__ == "__main__":
  main()
