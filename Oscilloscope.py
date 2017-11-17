"""
The oscilloscope class is an interface to the main program which contains basic
scope functions such as setting volt/div, secs/div, channel selection, trigger
configuration, and waveform saving.
"""
__author__ = "Ric Rodriguez"
__email__ = "rirrodri@ucsc.edu"

from pyvisa import ResourceManager

class TektronixDPO7000:
    '''
    classdocs
    '''


    def __init__(self, gpib_address="3"):
        resource_manager = ResourceManager()
        available_gpib_ports = resource_manager.list_resources()
        print(available_gpib_ports)
        oscilloscope_address = None
        for port_address in available_gpib_ports:
            if gpib_address in port_address:
                print("Found Scope Port")
                oscilloscope_address = port_address
        if oscilloscope_address is None:
            print("Cannot load Tek Scope")
            exit(1)
        print(oscilloscope_address)
        self.oscilloscope = resource_manager.open_resource(oscilloscope_address)
        print(self.oscilloscope.query("*IDN?"))
        self.oscilloscope.close()


    def get_waveform(self):
        """
        @function: get_waveform
        @summary: retrieves a waveform from the oscilloscope
        @param:
        @return:
        """
        pass

    def set_volts_per_division(self):
        """
        @function: set_volts_per_div
        @summary: sets the volts/div setting on the oscilloscope
        @param: volts
        @return: None
        """
        pass

SCOPE = TektronixDPO7000()
    