import csv
import serial
import serial.tools.list_ports
import time
import os
import subprocess
import asyncio

def load_csv(filename='pywebclicker.csv'):
    f = open(filename,'r')
    rdr = list(csv.reader(f))
    list_host_info = list()
    
    title_line = rdr[0]
    data_line = rdr[1:]
    for data in data_line:
        host_info = { name: value for name, value in zip(title_line, data) }
        list_host_info.append(host_info)
    
    f.close()
    return list_host_info

def send_serial(com='COM4', command='Power', high_cmd='1', low_cmd='q'):
    ports = serial.tools.list_ports.comports()
    check = False
    for port, desc, hwid in sorted(ports):
        print("{} : {} [{}]".format(port, desc, hwid))
        if ( com == port ):
            check = True
    if (check is False):
        print('{} is not found'.format(com))
        return False # not find COM port
    try:
        ser = serial.Serial(
            port = com, 
            baudrate=9600, 
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=8
            )
    except serial.serialutil.SerialException:
        print('{} is already connected by other SW'.format(com))
        return False # device is already connected

    if (ser.isOpen() is False):
        print('{} is not open'.format(com))
        return False
        
    if command == "Power":
        print(command)
        time.sleep(0.1)
        print(low_cmd)
        ser.write(low_cmd.encode()) # power release
        time.sleep(0.1)
        print(high_cmd)
        ser.write(high_cmd.encode()) # power push
        time.sleep(0.1)
        print(low_cmd)
        ser.write(low_cmd.encode()) # power release
        time.sleep(0.1)
    elif command == "Hard_Reset":
        print(command)
        time.sleep(0.1)
        print(low_cmd)
        ser.write(low_cmd.encode()) # power release
        time.sleep(0.1)
        print(high_cmd)
        ser.write(high_cmd.encode()) # power push
        time.sleep(10) # wait for a while
        print(low_cmd)
        ser.write(low_cmd.encode()) # power release
        time.sleep(0.1)
        print(high_cmd)
        ser.write(high_cmd.encode()) # power push
        time.sleep(0.1)
        print(low_cmd)
        ser.write(low_cmd.encode()) # power release
        time.sleep(10) # wait for a while
    elif command == "Force_Download_On":
        print(command)
        time.sleep(0.1)
        print(high_cmd)
        ser.write(high_cmd.encode()) # High for Force DL on
        time.sleep(0.1)
    elif command == "Force_Download_Off":
        print(command)
        time.sleep(0.1)
        print(low_cmd)
        ser.write(low_cmd.encode()) # Low for Force DL on
        time.sleep(0.1)
    else:
        print("Cannot find command:", command)

    ser.close()
    return True

async def __get_remot_pc_ping(host):
    hostname = host+'.sdcorp.global.sandisk.com'
    cmd = "ping -n 1 -w 1000 " + hostname + ' | findstr /i "TTL" > NUL'

    proc = await asyncio.create_subprocess_shell(
       cmd,
       stdout=asyncio.subprocess.PIPE,
       stderr=asyncio.subprocess.PIPE)

    # do something else while ls is working

    # if proc takes very long to complete, the CPUs are free to use   cycles for 
    # other processes
    stdout, stderr = await proc.communicate()
    return_code = await proc.wait()
    res = stdout.decode('utf-8')
    #print('stdout {}: '.format(cmd), stdout)
    #print('return_code: ',return_code)
    if return_code == 0:
        Netstatus = "Active"
    else:
        Netstatus = "Error"
    return Netstatus

async def __get_remot_pc_ping_all(host_info=None):
    if host_info is None:
        host_info = ['WDKR-NVMe-124']
    async_func_list = []
    for info in host_info:
        async_func_list.append(__get_remot_pc_ping(info))
    
    return await asyncio.gather(*async_func_list)

def ping_check(host):
    #hostname = host+'.sdcorp.global.sandisk.com'
    #response = os.system("ping -n 1 " + hostname + ' | findstr /i "TTL" > NUL')
    #if response == 0:
    #    Netstatus = "Active"
    #else:
    #    Netstatus = "Error"
    #return Netstatus
    return asyncio.run(__get_remot_pc_ping_all(host))
    
async def __get_current_rdp_status(host, user, pw):
    cmd = r'PSTools\psexec64.exe \\{} -u {} -p {} netstat -aon | findstr ESTAB  | findstr 3389'.format(host,user,pw)
    print('subprocess: ', cmd)
    proc = await asyncio.create_subprocess_shell(
       cmd,
       stdout=asyncio.subprocess.PIPE,
       stderr=asyncio.subprocess.PIPE)

    # do something else while ls is working

    # if proc takes very long to complete, the CPUs are free to use   cycles for 
    # other processes
    stdout, stderr = await proc.communicate()
    res = stdout.decode('utf-8')
    print('stdout: ',host, stdout)
    if(res == ''):
        return 'No connect' # No connection
    else:
        res = res.split()
        return res[2] # return connected ip address


async def get_current_rdp_status_all(rdp_info_s=None):
    if rdp_info_s is None:
        rdp_info_s = [['WDKR-NVMe-124',r'intg','tjrtkdals1@#']]
    async_func_list = []
    for info in rdp_info_s:
        async_func_list.append(__get_current_rdp_status(*info))
    
    return await asyncio.gather(*async_func_list)

def get_current_rdp_status(rdp_info_s=None):
    return asyncio.run(get_current_rdp_status_all(rdp_info_s))
    
def check_clicker_command(command):
    clicker = command
    clicker = [item.strip() for item in clicker.split('/')]
    if (clicker[0].find('COM') < 0):
        print ('COM is not defined')
        return False, False
    if (clicker[1] in ['1','2','3','4']) is False:
        print ('Clicker maaping (1,2,3,4) is wrong. please check it')
        return False, False
    if (clicker[2] in ['q','w','e','r']) is False:
        print ('Clicker maaping (q,w,e,r) is wrong. please check it')
        return False, False

    _com = clicker[0]
    _clicker_high_cmd = clicker[1]
    _clicker_low_cmd = clicker[2]
    # print("_com:", _com)
    # print("_clicker_high_cmd:", _clicker_high_cmd)
    # print("_clicker_low_cmd:", _clicker_low_cmd)
    return _com, _clicker_high_cmd, _clicker_low_cmd
if __name__ == "__main__":
    #send_serial()
    #s = ping_check(host="WDKR-CSH-HW2")
    c = 'WDKR-PSHOST-01-on'
    clicker = 'COM3 / 1 / q'
    check_clicker_command(clicker)
    print(clicker)