import time
import rtc_lib

degree_sign = u'\xb0'

ds3231 = rtc_lib.SDL_DS3231(1, 0x68)
ds3231.write_now() # saves the current date and time of R. Pi
# ds3231.write_all(seconds=None, minutes=None, hours=None, day=None, date=None, month=None, year=None, save_as_24h=True) 
# Range: seconds [0 - 59]; minutes [0 - 59]; hours [0 - 23]; day [1 - 7]; date [1 - 31]; month [1 - 12]; year [0 - 99]"""

def check(num):
        '''A fucntion that put leading zero to single digit number
           return: string
        '''
        if num < 10:
                return "0{}".format(num)
        else:
                return str(num)

print('[Press CTRL + C to end the script!]')
try:
        while True:
                print("\nSystem time: {}".format(time.strftime('%Y-%m-%d %H:%M:%S')))
                data = ds3231.read_datetime() # return tuple
                print("RTC date: {} {}.{}.{}".format(data[0], data[1], check(data[2]), check(data[3])))
                print("RTC time: {}:{}:{}".format(check(data[4]), check(data[5]), check(data[6])))

                print("RTC date_time: {}".format(ds3231.read_str())) # return string
                print("Temperature: {:.1f}{}C".format(ds3231.getTemp(), degree_sign))
                time.sleep(0.5)
                
except KeyboardInterrupt:
        print('\nScript end!')