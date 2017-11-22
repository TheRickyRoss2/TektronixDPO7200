"""
The oscilloscope class is an interface to the main program which contains basic
scope functions such as setting volt/div, secs/div, channel selection, trigger
configuration, and waveform saving.
"""
__author__ = "Ric Rodriguez"
__email__ = "rirrodri@ucsc.edu"

import struct
import pylab
from visa import ResourceManager
import numpy as np

class TektronixDPO7000:
    '''
    classdocs
    '''
    TRIGGER_CHANNEL_1 = "CH1"
    TRIGGER_CHANNEL_2 = "CH2"
    TRIGGER_CHANNEL_3 = "CH3"
    TRIGGER_CHANNEL_4 = "CH4"
    TRIGGER_CHANNEL_AUX = "AUX"
    TRIGGER_COUPLING_DC = "DC"
    TRIGGER_COUPLING_AC = "AC"
    TRIGGER_COUPLING_HFR = "HFR"
    TRIGGER_COUPLING_LFR = "LFR"
    TRIGGER_COUPLING_NOISE = "NOISE"
    TRIGGER_COUPLING_ATRIG = "ATRIG"
    TRIGGER_SLOPE_RISING = "RIS"
    TRIGGER_SLOPE_FALLING = "FALL"
    TRIGGER_SLOPE_EITHER = "EIT"

    CONFIG_CHANNEL_1 = ":CH1"
    CONFIG_CHANNEL_2 = ":CH2"
    CONFIG_CHANNEL_3 = ":CH3"
    CONFIG_CHANNEL_4 = ":CH4"
    CONFIG_COUPLING_DC = "DC"
    CONFIG_COUPLING_AC = "AC"
    CONFIG_COUPLING_GND = "GND"
    CONFIG_TERMINATION_1M = "1.0000E+6"
    CONFIG_TERMINATION_50 = "50"
    CONFIG_BANDWIDTH_FULL = "FUL"
    CONFIG_BANDWIDTH_500MHZ = "500E+6"
    CONFIG_BANDWIDTH_250MHZ = "250E+6"
    CONFIG_BANDWIDTH_150MHZ = "150E+6"
    CONFIG_BANDWIDTH_20MHZ = "20E+6"

    WAVEFORM_CHANNEL_1 = "CH1"
    WAVEFORM_CHANNEL_2 = "CH2"
    WAVEFORM_CHANNEL_3 = "CH3"
    WAVEFORM_CHANNEL_4 = "CH4"

    def __init__(self, gpib_address="3"):
        resource_manager = ResourceManager()
        available_gpib_ports = resource_manager.list_resources()
        oscilloscope_address = None
        for port_address in available_gpib_ports:
            if gpib_address in port_address:
                print("Found Scope Port")
                oscilloscope_address = port_address
        if oscilloscope_address is None:
            print("Cannot find Tek Scope")
            exit(1)
        self.oscilloscope = resource_manager.open_resource(oscilloscope_address)
        self.oscilloscope.clear()
        print(self.oscilloscope.query("*IDN?"))
        self.__reset()

    def __reset(self):
        """
        @function: __reset
        @summary: resets the state of the device
        @param: None
        @return: None
        """
        self.oscilloscope.write("*RST")
        self.oscilloscope.write(":HEADER OFF;*CLS;DESE 255;*ESE 61;*SRE 48;")
        self.oscilloscope.write(""":MEASU:REFL:METH PERC;:DAT:ENC RIB;\
:DAT:STAR 1;:DATA:STOP 2000000000;""")
        self.oscilloscope.write("*DDT #211:TRIG FORC;")
        self.oscilloscope.write("VERB OFF;")

    def __parse_raw_data(self, raw_data):
        num_digits = struct.unpack('B', raw_data[:2])
        print(num_digits)


    def get_waveform(self, channel):
        """
        @function: get_waveform
        @summary: retrieves a waveform from the oscilloscope
        @param:
        @return:
        """
        self.oscilloscope.timeout = 10000
        self.oscilloscope.write('DATA:SOU %s' %(channel))
        self.oscilloscope.write('DATA:WIDTH 1')
        self.oscilloscope.write('DATA:ENC RPB')
        ymult = float(self.oscilloscope.query('WFMPRE:YMULT?'))
        yzero = float(self.oscilloscope.query('WFMPRE:YZERO?'))
        yoff = float(self.oscilloscope.query('WFMPRE:YOFF?'))
        xincr = float(self.oscilloscope.query('WFMPRE:XINCR?'))

        self.oscilloscope.write('CURVE?')
        data = self.oscilloscope.read_raw()
        print("Done reading")

        header_len = 2 + int(data[1])
        adc_wave = data[header_len:-1]
        adc_wave = np.array(struct.unpack('%sB' % len(adc_wave),adc_wave))

        volts = (adc_wave - yoff) * ymult  + yzero
        time = np.arange(0, xincr * len(volts), xincr)

        #with open("wf.csv", 'w') as f:
        #    for indx, value in enumerate(Volts.tolist()):
        #        f.write(str(Time.tolist()[indx])+","+str(Volts.tolist()[indx])+"\n")

        print("Done writing data")

    def configure_edge_trigger(self, source_channel, **kwargs):
        """
        @function: configure_edge_trigger
        @summary: Sets trigger parameters of the scope
        @param source_channel: Channel source, as defined by class constant
        @param **kwargs: Optional arguments, as follows:
            coupling:
            slope:
            level:
            event:
        @return: None
        """
        trigger_event = kwargs.get("event", "A")
        trigger_coupling = kwargs.get("coupling", self.TRIGGER_COUPLING_DC)
        trigger_slope = kwargs.get("slope", self.TRIGGER_SLOPE_RISING)
        trigger_level = str(kwargs.get("level", "-1.0"))

        self.oscilloscope.write(":CMDBATCH 0;:TRIG:%s:TYP EDGE;" % trigger_event)
        self.oscilloscope.write(":TRIG:%s:EDGE:SOU %s;" %(trigger_event, source_channel))
        self.oscilloscope.write(":TRIG:%s:LEV %s;" %(trigger_event, trigger_level))
        self.oscilloscope.write(":TRIG:%s:EDGE:COUP %s;"%(trigger_event, trigger_coupling))
        self.oscilloscope.write(":TRIG:%s:EDGE:SLO %s;"%(trigger_event, trigger_slope))

    def configure_channel(self, channel, **kwargs):
        """
        Docstring goes here
        """
        vertical_range = str(float(kwargs.get("vertical_range", "1")))
        vertical_offset = str(float(kwargs.get("vertical_offset", "0.0")))
        vertical_coupling = kwargs.get("vertical_coupling", self.CONFIG_COUPLING_DC)
        input_impedance = kwargs.get("input_impedance", self.CONFIG_TERMINATION_50)
        bandwidth = kwargs.get("bandwidth", self.CONFIG_BANDWIDTH_FULL)
        self.oscilloscope.write("%s:COUP %s;" % (channel, vertical_coupling))
        self.oscilloscope.write("%s:TER %s;" %(channel, input_impedance))
        self.oscilloscope.write("%s:SCA %s;" %(channel, vertical_range))
        self.oscilloscope.write("%s:OFFS %s" %(channel, vertical_offset))
        self.oscilloscope.write("%s:BAN %s" %(channel, bandwidth))
        self.oscilloscope.write(":SEL%s ON;" % (channel))

    def configure_timebase(self, timebase="5", record_length="200000", position = "0"):
        """
        @attention: timebase is in ps/pt
        Docstring stub
        """
        self.oscilloscope.write(":HOR:MODE:SCA %s" %(str(float(timebase)/10000000000.)))
        self.oscilloscope.write(":HOR:MODE MAN;:HOR:MODE:RECO %s" %(str(int(record_length))))
        self.oscilloscope.write(";:HOR:MAI:POS %s" %(str(float(position))))
    def close(self):
        """
        asdf
        """
        self.oscilloscope.close()

SCOPE = TektronixDPO7000()
SCOPE.configure_channel(SCOPE.CONFIG_CHANNEL_1, vertical_range="0.01")
#SCOPE.configure_channel(SCOPE.CONFIG_CHANNEL_2)
#SCOPE.configure_channel(SCOPE.CONFIG_CHANNEL_3)
SCOPE.configure_channel(SCOPE.CONFIG_CHANNEL_4)

SCOPE.configure_edge_trigger(SCOPE.TRIGGER_CHANNEL_4, slope=SCOPE.TRIGGER_SLOPE_FALLING)
SCOPE.configure_timebase(1, 12500, 0)
while True:
    SCOPE.get_waveform(SCOPE.WAVEFORM_CHANNEL_4)
SCOPE.close()
