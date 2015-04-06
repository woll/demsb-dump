#!/opt/local/bin/python

#
#
# Utility to dump data from the Diamond DEMSB-D01 solar panel energy monitor unit
#
#


from __future__ import print_function


import usb.core
import usb.util
import usb.backend
import sys
import datetime
from datetime import timedelta
from datetime import date
import time
import sys, getopt

 
debug = 0
silent = 0
output_today = 0
output_yesterday = 0
output_monthly = 0


# Print message if in debug mode
def debug_log( str ):
	if ( debug ):
		print( str )


# Cleanup the USB device, to try and clear communication errors, or at the end
def cleanup( dev ):
	debug_log( 'Reset device' )

	try:	
		dev.reset()
	except usb.core.USBError as e:
		print( e.args[1], file=sys.stderr)
		return

	try:	
		usb.util.dispose_resources(dev)
	except usb.core.USBError as e:
		print( e.args[1], file=sys.stderr)
		return
#	time.sleep(60)


# Read a 16-bit number encoded as 2-bytes
def read_word_value( buffer, offset ):
        value = int(chr(buffer[offset + 2 ]).encode('hex'), 16) * 256
        return value + int(chr(buffer[offset + 3 ]).encode('hex'), 16)


# Print the chart showing data for the hours of the day
def print_day_chart( day, month, year, g, c, s, b ):
	if silent == 1:
		return

	print( '-----------------------------------------------------------------------------------' )
	print( "%02d/%02d/%02d" % (day, month, year) )

	print( "Generated: %.1f kWh  Consumed: %.1f kWh  Sold: %.1f kWh  Bought: %.1f kWh" % ( float( sum( g ) )/10, float( sum( c ) )/10, float( sum( s ) )/10, float( sum( b ) )/10 ) )
	
	max_value = max(g)
        for v in range(int( round( max_value / 5) * 5) + 5,-5,-5):
		# Print graph height scale
		if v % 10 == 0:
			print( v/10, end=" " )
		else:
			print( ' ', end=" " )

		for h in range(0,24):
			if (s[h] > v):
				# Power exported
				print( ' $', end=" " )
			elif (g[h] > v):
				# Power generated and not exported
				print( ' +', end=" " )
			else:
				print( '  ', end=" " )
		print()
	# Horizontal 'hours' scale
	print( '   0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23' )
	max_value = max(c)
	for v in range(0,int(round( max_value / 5 ) * 5) + 5,5):
		# Print graph height scale
		if v % 10 == 0:
			print( v/10, end=" " )
		else:
			print( ' ', end=" ")

		for h in range(0,24):
			if (b[h] > (v+2)):
				# Power imported
				print( ' X', end=" " )
			elif (c[h] > (v+2)):
				# Generated power used
				print( ' 0', end=" " )
			else:
				print( '  ', end=" " )
		print()
	print( '-----------------------------------------------------------------------------------' )
	print( '$=Sell X=Buy 0=Free +=Generated' )
	print()
		
	
# Print the chart for the months of the last 2 years
def print_months_chart( month, year, g, c, s, b ):
	if silent == 1:
		return

	scale_divide = 1000
	print( '-----------------------------------------------------------------------------------' )
	print( 'Previous two years' )

	print( "Generated: %.1f kWh  Consumed: %.1f kWh  Sold: %.1f kWh  Bought: %.1f kWh" % ( float( sum( g ) )/10, float( sum( c ) )/10, float( sum( s ) )/10, float( sum( b ) )/10 ) )
	
	max_value = max(g)
	for v in range(int( round( max_value / 1000 ) * 1000),-scale_divide,-scale_divide):
		# Vertical scale
		if v % 10 == 0:
			print( "%5s" % ( v/10 ), end=" " )
		else:
			print( '     ', end=" " )

		for m in range(23,-1,-1):
			if (s[m] > v):
				# Power exported
				print( '$ ', end=" " )
			elif (g[m] > v):
				# Power generated and used
				print( '+ ', end=" " )
			else:
				print( '  ', end=" " )
		print()

	# Horizontal 'months' scale
	print( 2000 + year[ 23 ], end=" " )
	for x in range(23,-1,-1):
		print( "%2s" % ( month[ x ] ), end=" " )
	print( ' %d' % ( 2000 + year[ 0 ]) )

	max_value = max(c)
	for v in range(0,int(round( max_value / 10 ) * 10) + 10,scale_divide):
		# Vertical scale for power used
		if v % 10 == 0:
			print( "%5s" % ( v/10 ), end=" " )
		else:
			print( '     ', end=" " )

		for m in range(23,-1,-1):
			if (b[m] > (v+2)):
				# Power imported
				print( 'X ', end=" " )
			elif (c[m] > (v+2)):
				# Generated power used
				print( '0 ', end=" " )
			else:
				print( '  ', end=" " )
		print()
	print( '----------------------------------------------------------------------------------' )
	print( '$=Sell X=Buy 0=Free +=Generated' )
	print()
	

# Main function
def main(argv):
	global silent
	global debug
	global output_today
	global output_yesterday
	global output_monthly


	try:
		opts, args = getopt.getopt( argv,"tymsv" )
	except getopt.GetoptError:
		print('test.py -t -y -m -s -v', file=sys.stderr)
		exit(2)
	for opt, arg in opts:
		if opt == '-t':
			output_today = 1
		if opt == '-y':
			output_yesterday = 1
		if opt == '-m':
			output_monthly = 1
		if opt == '-v':
			debug = 1
		elif opt == '-s':
			silent = 1


	# Initialise data arrays
	generated_d=[0 for x in range(120)]
	sold_d=[0 for x in range(120)]
	consumed_d=[0 for x in range(120)]
	bought_d=[0 for x in range(120)]
	month_d=[0 for x in range(120)]
	year_d=[0 for x in range(120)]


	# Try N times to access device.
	times_tried = 1
	while times_tried < 10:
		debug_log( "Try %d" % ( times_tried ) )
		if ( times_tried != 1 ):
			time.sleep( 1 )
		times_tried += 1


		i = datetime.datetime.now()
		debug_log( i.strftime( '%H:%M:%S' ) )
		this_day = int( i.strftime('%d') )
		this_month = int( i.strftime('%m') )
		this_year = int( i.strftime('%y') )
		year_length = timedelta(days=365)
		last_year_time = i - year_length
		last_year = int( last_year_time.strftime('%y') )
		yesterday_time = i - timedelta( days=1 )
		yesterday_day = int( yesterday_time.strftime('%d') )
		yesterday_month = int( yesterday_time.strftime('%m') )
		yesterday_year = int( yesterday_time.strftime('%y') )



		# Find the DEMSB-D01 device
		dev = usb.core.find( idVendor=0x1BB8, idProduct=0xFFEF )
		 
		# If not found then exit
		if dev is None:
			print( 'Device not found', file=sys.stderr )
			exit( -1 )
		 
		debug_log( 'Found device' )


		# Set the active USB configuration.
		try:	
			dev.set_configuration()
		except usb.core.USBError as e:
			print( e.args[1], file=sys.stderr)
			continue;
			
		 
		cleanup( dev )
		# Wait, so that device can recover from reset
		time.sleep( 1 )


		# Request and wait for 'OK' response from unit
		debug_log( "Request and wait for 'OK' response from unit" )
		dev.write( 0x02, "MIZOUEPROJECTJAPANE0\r" )
		error = 0
		while True:
			try:
				ret = dev.read( 0x81, 0x07 )
				sret = ''.join( [chr(x) for x in ret] )
				
				# If the response contains 'OK', then we got the reply
				if sret.count( "OK" ):
					break
			except usb.core.USBError as e:
				print( e.args[1], file=sys.stderr )
				error = 1
				break

		if ( error ):
			continue


		# Request sending of 63-byte block from unit
		debug_log( "Request sending of 63-byte block from unit" )
		dev.write( 0x02, "MIZOUEPROJECTJAPANE1\r" )
		while True:
			try:
				ret = dev.read( 0x81, 63 )
			except usb.core.USBError as e:
				print( e.args[1], file=sys.stderr )
				break;

			sret = ''.join( [chr(x) for x in ret] )
			if len( ret ) == 63:
				break;

		# Didn't get 63-byte block. Some kind of read problem.
		if ( len( ret ) != 63 ):
			continue


		# Request and read the main data block. 625 * 64-bytes
		debug_log( "Request and read the main data block. 625 * 64-bytes" )
		dev.write( 0x02, "MIZOUEPROJECTJAPANE2\r" )

		# Read 625 64-byte blocks and remove 2-byte header from each block
		bytes_read = []
		block = 0
		while( block < 625 ):
			try:
				read_block = dev.read( 0x81, 64 )
			except usb.core.USBError as e:
				print( e.args[1], file=sys.stderr )

			# Ignore leading 2-byte blocks blocks ("hearbeat" blocks sent before the main data request?) 
			if ( block == 0 and len( read_block ) == 2 ):
				continue;

			if ( block < 624 and len( read_block ) != 64 ):
				# Read error, so stop attempting to read any more
				break
			else:
				# Add the block, without the 2-byte header, to the data array
				bytes_read.extend( read_block[2:] )
			block += 1


		if ( block != 625 or len( read_block ) != 46 ):
			# A read failed, so the data is incomplete, so reset device and loop again
			debug_log( "Read of main data block failed" )
			debug_log( "block %d is %d bytes long" % ( block, len( read_block ) ) )
			cleanup( dev )
			continue
			

		# Interpret 1290 30-byte records containing the data
		debug_log( "Interpret data..." )
		b = 0
		record = 0
		num_months_read = 0
		n_month = 0
		success = 0

		while record <= 1290:
			flag = int( chr( bytes_read[ b ]).encode('hex'), 16)
			sell = read_word_value( bytes_read, b + 1 )
			buy = read_word_value( bytes_read, b + 5 )
			generate = read_word_value( bytes_read, b + 9 )
			year = int( chr( bytes_read[ b + 25] ).encode('hex'), 16)
			month = int( chr( bytes_read[ b + 26] ).encode('hex'), 16)
			day = int( chr( bytes_read[ b + 27] ).encode('hex'), 16)
			hour = int( chr( bytes_read[ b + 29] ).encode('hex'), 16)
			consume = generate - sell + buy


			# First 768 records are hourly data for 32 days
			if ( record < 768 ):
				generated_d[hour]=generate
				consumed_d[hour]=consume
				sold_d[hour]=sell
				bought_d[hour]=buy

				# Print day chart 
				if ( ( output_today == 1 and day == this_day and month == this_month and year == this_year and hour == 0 ) or ( output_yesterday == 1 and day == yesterday_day and month == yesterday_month and year == yesterday_year and hour == 0 ) ):
					print_day_chart( day, month, year, generated_d, consumed_d, sold_d, bought_d )


			# Records 769 to 1171 are daily data for the last 13 months
			# Ignored

			# Records 1172 onwards are monthly data for the last 10 years
			elif ( record >= 1172 ):
				try:
					record_date = date( 2000 + year, month, 1 )
					today = date.today()
					two_years_ago = today.replace( year=today.year - 2, day=1 )

					# If month is within last 24 months, then store data
					if ( record_date > two_years_ago and record_date <= today ):
						generated_d[n_month]=generate
						consumed_d[n_month]=consume
						sold_d[n_month]=sell
						bought_d[n_month]=buy
						month_d[n_month]=month
						year_d[n_month]=year
						n_month += 1
				except ValueError:
					print( "Date is not valid" )

				# If stored 24 months of data, then print monthly chart
				if n_month == 24:
					n_month = 0
					if ( output_monthly == 1 ):
						print_months_chart( month_d, year_d, generated_d, consumed_d, sold_d, bought_d )
					# All the data has been read and parsed OK
					success = 1

			# Move index to next 30-byte record
			b += 30
			record += 1
			

		cleanup( dev )


		# If successful on this attempt, then exit
		if ( success == 1 ):
			debug_log( "Success" )
			exit( 0 )


	# Some kind of fatal error occured, so give up
	exit( -1 )


if __name__ == "__main__":
   main(sys.argv[1:])
