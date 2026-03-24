import sys
import traceback
from datetime import datetime

import ue9

signal.signal(signal.SIGTERM, saveExit)
signal.signal(signal.SIGINT, saveExit)

# MAX_REQUESTS is the number of packets to be read.
MAX_REQUESTS = 500
# SCAN_FREQUENCY is the scan frequency of stream mode in Hz
SCAN_FREQUENCY = 5000

#output data


###############################################################################
# UE9
# Uncomment these lines to stream from a UE9
###############################################################################

# At 96 Hz or higher frequencies, the number of samples will be MAX_REQUESTS
# times 8 (packets per request) times 16 (samples per packet).
# Currently over ethernet packets per request is 1.
d = ue9.UE9() 
#d = ue9.UE9(ethernet=True, ipAddress="192.168.1.209")  # Over TCP/ethernet connect to UE9 with IP address 192.168.1.209

# For applying the proper calibration to readings.
d.getCalibrationData()

print("Configuring UE9 stream")

d.streamConfig(NumChannels=1, ChannelNumbers=[0], ChannelOptions=[1], SettlingTime=0, Resolution=13, ScanFrequency=SCAN_FREQUENCY)

try:
    print("Start stream")
    d.streamStart()
    start = datetime.now()
    print("Start time is %s" % start)

    missed = 0
    dataCount = 0
    packetCount = 0
    calOffset = 0
    for i in 100:    
        r = d.streamData()
        calOffset += sum(r["AIN0"])/len(r["AIN0"])
        
    calOffset = calOffset/100
    dataOut = (['Cal Offset', calOffset],['Time','Voltage'])

    for r in d.streamData():
        if r is not None:
            # if r["errors"] != 0:
            #         print("Errors counted: %s ; %s" % (r["errors"], datetime.now()))
    
            # if r["numPackets"] != d.packetsPerRequest:
            #         print("----- UNDERFLOW : %s ; %s" %
            #               (r["numPackets"], datetime.now()))
    
            # if r["missed"] != 0:
            #         missed += r['missed']
            #         print("+++ Missed %s" % r["missed"])

            #     # Comment out these prints and do something with r
            #     print("Average of %s AIN0 readings:, %s" %
            #           (len(r["AIN0"]), sum(r["AIN0"])/len(r["AIN0"])))

                #Current Time
                now = datetime.now() - start
                dataOuput.append([now,sum(r["AIN0"])/len(r["AIN0"])])
    
                dataCount += 1
                packetCount += r['numPackets']
        else:
            # Got no data back from our read.
            # This only happens if your stream isn't faster than the USB read
            # timeout, ~1 sec.
                print("No data ; %s" % datetime.now())
except:
    print("".join(i for i in traceback.format_exc()))

def saveExit():
    stop = datetime.now()
    d.streamStop()
    print("Stream stopped.\n")
    d.close()

    sampleTotal = packetCount * d.streamSamplesPerPacket

    scanTotal = sampleTotal / 1  # sampleTotal / NumChannels
    print("%s requests with %s packets per request with %s samples per packet = %s samples total." %
          (dataCount, (float(packetCount)/dataCount), d.streamSamplesPerPacket, sampleTotal))
    print("%s samples were lost due to errors." % missed)
    sampleTotal -= missed
    print("Adjusted number of samples = %s" % sampleTotal)

    runTime = (stop-start).seconds + float((stop-start).microseconds)/1000000
    print("The experiment took %s seconds." % runTime)
    print("Actual Scan Rate = %s Hz" % SCAN_FREQUENCY)
    print("Timed Scan Rate = %s scans / %s seconds = %s Hz" %
          (scanTotal, runTime, float(scanTotal)/runTime))
    print("Timed Sample Rate = %s samples / %s seconds = %s Hz" %
          (sampleTotal, runTime, float(sampleTotal)/runTime)
    print(dataOuput)


