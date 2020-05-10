#!/bin/bash

DEBUG=true
DEVICE=/sys/class/drm/card0/device/hwmon/hwmon3

# check if device exists and is amdgpu
if [ ! -d "$DEVICE" ]; then
  echo Device not found. Exiting.
  exit 1
fi

if [ $(cat $DEVICE/name) != 'amdgpu' ]; then
  echo Device is not amdgpu. Exiting
  exit 1
fi

# cleanup function
function clearExit () {
  echo "2" > $DEVICE/pwm1_enable
  echo Setting fan to automatic control mode.
}
trap clearExit EXIT

# leaky pid params
let alpha=2
let p=40
let i=20

# init vars
let acc=0
let delta=0

echo Setting fan to manual control mode.
echo "1" > $DEVICE/pwm1_enable

echo Running...

while true; do
  let junction=$(cat $DEVICE/temp1_input)
  let state=$(cat $DEVICE/pwm1)

  let temp=$junction/1000

  let target=($temp-50)*255/40
  if [ $target -lt 0 ]; then target=0; fi

  let delta=$target-$state

  let acc=$acc/$alpha+$delta*$alpha

  let pwm_target=$state+$delta/$p+$acc/$i

  if [ $pwm_target -gt 255 ]; then pwm_target=255; fi
  if [ $pwm_target -lt 0 ]; then pwm_target=0; fi

  if [ $DEBUG ]; then
    let fan=$(cat $DEVICE/fan1_input)
    echo ================
    echo temp: $temp
    echo state: $state
    echo target: $target
    echo pwm_target: $pwm_target
    echo delta: $delta
    echo acc: $acc
    echo fan: $fan
  fi

  echo $pwm_target > $DEVICE/pwm1

  sleep 0.2 &
  wait
done
