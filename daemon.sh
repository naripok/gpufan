#!/bin/bash

let leak=2
let p=26
let i=18

let acc=0
let delta=0

while true; do
  let junction=$(cat /sys/class/drm/card0/device/hwmon/hwmon3/temp2_input)
  let state=$(cat /sys/class/drm/card0/device/hwmon/hwmon3/pwm1)
  let fan=$(cat /sys/class/drm/card0/device/hwmon/hwmon3/fan1_input)

  let temp=$junction/1000

  let target=($temp-50)*255/60
  if [ $target -lt 0 ]; then target=0; fi

  let delta=$target-$state

  let acc=$acc/$leak
  let acc=$acc+$delta*2

  let pwm_target=$state+$delta/$p+$acc/$i

  if [ $pwm_target -gt 255 ]; then pwm_target=255; fi
  if [ $pwm_target -lt 0 ]; then pwm_target=0; fi

  echo ================
  echo temp: $temp
  echo state: $state
  echo target: $target
  echo pwm_target: $pwm_target
  echo delta: $delta
  echo acc: $acc
  echo fan: $fan

  echo $pwm_target > /sys/class/drm/card0/device/hwmon/hwmon3/pwm1

  sleep 0.2
done
