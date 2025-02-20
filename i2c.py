#!/usr/bin/python

import os
import io
import sys
import fcntl
import time
import copy
import string
from AtlasI2C import (
	 AtlasI2C
)
def print_devices(device_list, device):
    for i in device_list:
        if(i == device):
            print("--> " + i.get_device_info())
        else:
            print(" - " + i.get_device_info())
    #print("")
    
def get_devices():
    device = AtlasI2C()
    device_address_list = device.list_i2c_devices()
    device_list = []
    
    for i in device_address_list:
        device.set_i2c_address(i)
        response = device.query("I")
        moduletype = response.split(",")[1] 
        response = device.query("name,?").split(",")[1]
        device_list.append(AtlasI2C(address = i, moduletype = moduletype, name = response))
    return device_list 
       
def print_help_text():
    print('''
>> Atlas Scientific I2C sample code
>> Any commands entered are passed to the default target device via I2C except:
  - Help
      brings up this menu
  - List 
      lists the available I2C circuits.
      the --> indicates the target device that will receive individual commands
  - xxx:[command]
      sends the command to the device at I2C address xxx 
      and sets future communications to that address
      Ex: "102:status" will send the command status to address 102
  - all:[command]
      sends the command to all devices
  - Poll[,x.xx]
      command continuously polls all devices
      the optional argument [,x.xx] lets you set a polling time
      where x.xx is greater than the minimum %0.2f second timeout.
      by default it will poll every %0.2f seconds
>> Pressing ctrl-c will stop the polling
    ''' % (AtlasI2C.LONG_TIMEOUT, AtlasI2C.LONG_TIMEOUT))
       
def main():
    # 정지선 인식 한 횟수
    gool = 0
    # 버퍼를 저장하기 위한 리스트
    rgb_list = []
    
    # 디바이스 정보 불러오기
    device_list = get_devices()
        
    device = device_list[0]
    
    print_help_text()
    
    print_devices(device_list, device)
    
    real_raw_input = vars(__builtins__).get('raw_input', input)
    
    while True:
        # 커멘드 입력에 따라 여러 모드 선택가능
        user_cmd = real_raw_input(">> Enter command: ")
        
        # show all the available devices
        if user_cmd.upper().strip().startswith("LIST"):
            print_devices(device_list, device)
            
        # print the help text 
        elif user_cmd.upper().startswith("HELP"):
            print_help_text()
            
        # continuous polling command automatically polls the board
        elif user_cmd.upper().strip().startswith("POLL"):
            vlaue = 0;
            cmd_list = user_cmd.split(',') 
            if len(cmd_list) > 1:
                delaytime = float(cmd_list[1])
            else:
                delaytime = device.long_timeout

            # check for polling time being too short, change it to the minimum timeout if too short
            if delaytime < device.long_timeout:
                print("Polling time is shorter than timeout, setting polling time to %0.2f" % device.long_timeout)
                delaytime = device.long_timeout
            try:
                while True:
                    print("-------press ctrl-c to stop the polling")
                    for dev in device_list:
                        dev.write("R")
                    time.sleep(delaytime)
		    # 내가 건드린 부분
                    for dev in device_list:
                        # 읽어온 버퍼값 rgb_list 에 저장
                        rgb_list.append(dev.read())
			# ,기준으로 rgb_list 리스트값 쪼개기
                        rgb_list2 = rgb_list[0].split(',')
			# 색상이 저장된 rgb_list의 red 값 에서 : 기준으로 다시 쪼갬
                        #  "sucess color :  255 " -> ("sucess color :" , [2,5,5]
                        red = rgb_list2[0].split(':')
			# 쪼개진 rgb값 합쳐서 출력
                        red = ''.join(red[1])
			#  색상이 저장된 rgb_list의 green 값 가져와서 쪼개진 rgb값을 합쳐서 출력 
                        green = rgb_list2[1]
                        green = ''.join(green)
			# 색상이 저장된 rgb_list의 blue 값 가져와서 쪼개진 rgb값을 합쳐서 출력 
                        blue = rgb_list2[2]
                        blue = ''.join(blue)
			# green 값이 red 와 blue보다 크면 한바퀴 돌았다고 판단 
                        if int(green) > int (red) and int(green) > int(blue):
                            gool += 1
                            print(gool)
			    # 3바퀴 돌면 전원꺼짐	
                            if gool == 3:
                                os.system("poweroff")
			# rgb값 출력구문
                        print(int(red),int(green),int(blue))
			#버퍼 초기화
                        rgb_list = []
                        #여기가 끝 
                        #print(dev.read())
            except KeyboardInterrupt:       # catches the ctrl-c command, which breaks the loop above
                print("Continuous polling stopped")
                print_devices(device_list, device)
                
        # send a command to all the available devices
        elif user_cmd.upper().strip().startswith("ALL:"):
            cmd_list = user_cmd.split(":")
            for dev in device_list:
                dev.write(cmd_list[1])
            
            # figure out how long to wait before reading the response
            timeout = device_list[0].get_command_timeout(cmd_list[1].strip())
            # if we dont have a timeout, dont try to read, since it means we issued a sleep command
            if(timeout):
                time.sleep(timeout)
                for dev in device_list:
                    print(dev.read())
                
        # if not a special keyword, see if we change the address, and communicate with that device
        else:
            try:
                cmd_list = user_cmd.split(":")
                if(len(cmd_list) > 1):
                    addr = cmd_list[0]
                    
                    # go through the devices to figure out if its available
                    # and swith to it if it is
                    switched = False
                    for i in device_list:
                        if(i.address == int(addr)):
                            device = i
                            switched = True
                    if(switched):
                        print(device.query(cmd_list[1]))
                    else:
                        print("No device found at address " + addr)
                else:
                    # if no address change, just send the command to the device
                    print(device.query(user_cmd))
            except IOError:
                print("Query failed \n - Address may be invalid, use list command to see available addresses")

                    
if __name__ == '__main__':
    main()
