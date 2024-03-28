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

def send_serial(com='COM4', command='3', poweron=True):
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
    if poweron is True:
        power_on(ser,command)
        print('{} {} power-on'.format(com,command))
    else:
        power_off(ser,command)
        print('{} {} power-off'.format(com,command))
    ser.close()
    return True

def power_on(ser, command='3'):
    command_map = {'1':'q', '2':'w', '3':'e', '4':'r'}
    time.sleep(0.1)        
    ser.write(command.encode()) # power release
    time.sleep(0.1)
    ser.write(command_map[command].encode()) # power push
    time.sleep(0.1)
    ser.write(command.encode()) # power release
    time.sleep(0.1)
    time.sleep(10) # wait power on...
    
def power_off(ser, command='3'):
    command_map = {'1':'q', '2':'w', '3':'e', '4':'r'}
    time.sleep(0.1)        
    ser.write(command.encode()) # power release
    time.sleep(0.1)
    ser.write(command_map[command].encode()) # power push
    time.sleep(7) # wait 10s...
    ser.write(command.encode()) # power release
    time.sleep(0.1)
    time.sleep(3) # wait remain time    

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
        host_info = ['WDKR-PSHOST-01'
                     ,'WDKR-PSHOST-03'
                     ,'WDKR-PSHOST-04'
                     ,'WDKR-PSHOST-05'
                     ,'WDKR-PSHOST-06'
                     ,'WDKR-PSHOST-08'
                     ,'WDKR-PSHOST-09'
                     ,'WDKR-PSHOST-10'
                     ,'WDKR-PSHOST-11'
                     ,'WDKR-PSHOST-12']
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
        rdp_info_s = [['WDKR-PSHOST-01',r'intg','tjtls@']
             ,['WDKR-PSHOST-03',r'intg','tjtls@']
             ,['WDKR-PSHOST-04',r'intg','tjtls@']
             ,['WDKR-PSHOST-05',r'intg','tjtls@']
             ,['WDKR-PSHOST-06',r'intg','tjtls@']
             ,['WDKR-PSHOST-08',r'intg','tjrtkdals1@#']
             ,['WDKR-PSHOST-09',r'intg','tjrtkdals1@#']
             ,['WDKR-PSHOST-10',r'intg','tjrtkdals1@#']
             ,['WDKR-PSHOST-11',r'intg','tjrtkdals1@#']
             ,['WDKR-PSHOST-12',r'intg','tjrtkdals1@#']]
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
        
    _com = clicker[0]
    _clicker_no = clicker[1]
    return _com, _clicker_no
if __name__ == "__main__":
    #send_serial()
    #s = ping_check(host="WDKR-CSH-HW2")
    c = 'WDKR-PSHOST-01-on'
    clicker = 'COM3 / 1 / q'
    check_clicker_command(clicker)
    print(clicker)