from datetime import datetime
import time
import smbus

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
MAX_DAYS_PER_MONTH = 31
MONTHS_PER_YEAR = 12
YEARS_PER_CENTURY = 100
OSCILLATOR_ON_MASK = 0b1<<7

days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

def bcd_to_int(bcd, n=2):
    return int(('%x' % bcd)[-n:])

def int_to_bcd(x, n=2):
    return int(str(x)[-n:], 0x10)

class SDL_DS3231():
    (
        _REG_SECONDS,
        _REG_MINUTES,
        _REG_HOURS,
        _REG_DAY,
        _REG_DATE,
        _REG_MONTH,
        _REG_YEAR,
    ) = range(7)

    def __init__(self, twi=1, addr=0x68, at24c32_addr=0x56):
        self._bus = smbus.SMBus(twi)
        self._addr = addr
        self._at24c32_addr = at24c32_addr

    def _write(self, register, data):
        if False:
            print("addr =0x{} register = 0x{} data = 0x{} {}".format(self._addr, register, data, bcd_to_int(data)))
        self._bus.write_byte_data(self._addr, register, data)

    def _read(self, register_address):
        data = self._bus.read_byte_data(self._addr, register_address)
        if False:
            print("addr = 0x{} register_address = 0x{} {} data = 0x{} {}".format(self._addr, register_address, register_address, data, bcd_to_int(data)))
        return data

    def _incoherent_read_all(self):
        """Return tuple of year, month, date, day, hours, minutes, seconds.
        Since each value is read one byte at a time,
        it might not be coherent."""
        register_addresses = (
            self._REG_SECONDS,
            self._REG_MINUTES,
            self._REG_HOURS,
            self._REG_DAY,
            self._REG_DATE,
            self._REG_MONTH,
            self._REG_YEAR,
        )
        seconds, minutes, hours, day, date, month, year = (self._read(register_address) for register_address in register_addresses)
        seconds &= ~OSCILLATOR_ON_MASK
        if True:
            # This stuff is suspicious.
            if hours == 0x64:
                hours = 0x40
            hours &= 0x3F
        return tuple(bcd_to_int(t) for t in (year, month, date, day, hours, minutes, seconds))

    def check_zero(self, num):
        if num < 10:
            return "0{}".format(num)
        else:
            return str(num)

    def read_all(self):
        """Return tuple of year, month, date, day, hours, minutes, seconds."""
        old = self._incoherent_read_all()
        while True:
            new = self._incoherent_read_all()
            if old == new:
                break
            old = new
        return new

    def read_str(self, century=21):
        """Return a string such as 'YY-DD-MM HH-MM-SS'"""
        year, month, date, day, hours, minutes, seconds = self.read_all()
        year = 100 * (century - 1) + year
        return ('{} {}-{}-{} {}:{}:{}'.format(days[day-1], self.check_zero(date), self.check_zero(month), year, self.check_zero(hours), self.check_zero(minutes), self.check_zero(seconds)))

    def read_datetime(self, century=21, tzinfo=None):
        """Return the tuple object: year, month, date, day, hours, minutes, seconds"""
        year, month, date, day, hours, minutes, seconds = self.read_all()
        year = 100 * (century - 1) + year
        return days[day-1], date, month, year, hours, minutes, seconds

    def read_datetime_object(self, century=21, tzinfo=None):
        """Return the datetime.datetime object"""
        year, month, date, _, hours, minutes, seconds = self.read_all()
        year = 100 * (century - 1) + year
        return datetime(year, month, date, hours, minutes, seconds, 0, tzinfo=tzinfo)

    def write_all(self, seconds=None, minutes=None, hours=None, day=None, date=None, month=None, year=None, save_as_24h=True):
        """Direct write un-none value.
        Range: seconds [0 - 59], minutes [0 - 59], hours [0 - 23], day [1 - 7], date [1 - 31], month [1 - 12], year [0 - 99]"""
        if seconds is not None:
            if not 0 <= seconds < SECONDS_PER_MINUTE:
                raise ValueError('Seconds is out of range [0 - 59]')
            seconds_reg = int_to_bcd(seconds)
            self._write(self._REG_SECONDS, seconds_reg)
        if minutes is not None:
            if not 0 <= minutes < MINUTES_PER_HOUR:
                raise ValueError('Minutes is out of range [0 - 59]')
            self._write(self._REG_MINUTES, int_to_bcd(minutes))
        if hours is not None:
            if not 0 <= hours < HOURS_PER_DAY:
                raise ValueError('Hours is out of range [0 - 23]')
            self._write(self._REG_HOURS, int_to_bcd(hours) )
        if year is not None:
            if not 0 <= year < YEARS_PER_CENTURY:
                raise ValueError('Years is out of range [0 - 99]')
            self._write(self._REG_YEAR, int_to_bcd(year))
        if month is not None:
            if not 1 <= month <= MONTHS_PER_YEAR:
                raise ValueError('Month is out of range [1 - 12]')
            self._write(self._REG_MONTH, int_to_bcd(month))
        if date is not None:
            # How about a more sophisticated check?
            if not 1 <= date <= MAX_DAYS_PER_MONTH:
                raise ValueError('Date is out of range [1 - 31]')
            self._write(self._REG_DATE, int_to_bcd(date))
        if day is not None:
            if not 1 <= day <= DAYS_PER_WEEK:
                raise ValueError('Day is out of range [1 - 7]')
            self._write(self._REG_DAY, int_to_bcd(day))

    def write_datetime(self, dt):
        """Write from a datetime.datetime object"""
        self.write_all(dt.second, dt.minute, dt.hour, dt.isoweekday(), dt.day, dt.month, dt.year % 100)

    def write_now(self):
        """Equal to DS3231.write_datetime(datetime.datetime.now())"""
        self.write_datetime(datetime.now())

    def getTemp(self):
        byte_tmsb = self._bus.read_byte_data(self._addr,0x11)
        byte_tlsb = bin(self._bus.read_byte_data(self._addr, 0x12))[2:].zfill(8)
        return byte_tmsb + int(byte_tlsb[0]) * 2**(-1) + int(byte_tlsb[1]) * 2**(-2)
