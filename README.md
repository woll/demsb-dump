demsb-dump is a utility to dump data from the Diamond DEMSB-D01 solar panel energy monitor unit, via its USB port.

The DEMSB-D01 is a solar panel energy monitor, manufactured by Diamond Electric Manufacturing Co., www.diaelec.co.jp

The monitor is supplied to household consumers in Japan, by solar panel suppliers like SANIX Co., sanix.jp

The supplied software only works on Windows, so I wrote demsb-dump to download the data on a Mac.

Presumably, with a few changes, the code will work under Linux and similar systems.

Version 1.0 was developed using:
	Mac OS X 10.7.5
	python 2.7 from MacPorts
	py27-pyusb-devel from MacPorts

The code was developed by recording the USB communications of the manufacturer-supplied Windows software and working out the neccessary commands, using some guesswork.

I didn't attempt to work out the meaning of some of the data transfers (e.g. the 63-byte block that is sent from the unit), but it appears that this can be ignored.
