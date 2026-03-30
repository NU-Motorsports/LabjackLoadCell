
import sys
import traceback
from datetime import datetime
import yaml

import signal
import ue9
import csv


###YAML Config File Variables

#configFile is a YAML file dictionary of the following keys and values
directory = ""
calibrationName = ""

#Each load cell has a seperate calibration in this with a pound to voltage value. The correct one is found from the calibrationName variable as the key.
loadCellCalibration = 1


###########################################################All Functions Defined Here##############################################################################################################

def writeConfigFile(path):
    config = {"Directory": directory, "Calibration" : loadCellCalibration, "CalibrationName" : calibrationName}
    with open(path + ".yaml", "w") as f:
        yaml.dump(data,f)

def loadYAMLConfig(configFile = "configFile.yaml"):
    with open(configFile, "r") as f:
        config = yaml.safe_load(f)

    directory = config["Directory"]
    calibrationName = config["CalibrationName"]
#Make this calibration list
    with open("Calibrations.yaml", "r") as f:
        loadCellCalibration = yaml.safe_load(f)["CalibrationName"]


#Writes a matrix of size 3 by number of data points to a CSV
#NOTE: The CSV folder location should be changed depending on when you and why you are taking data. For example: it was originally written to save to tierodData because we were looking at steering rack forces.
def saveData(data, header, stoptime):
    name = directory + "/" + stoptime
    try:
        os.mkdir(directory)
        print("Writing data to" + name)
    except FilesExistsError:
        print("Directory already exists. Writing data to" + name)

    try:
        with open(name + ".csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)

        writeConfigFile(name)

    except FileNotFoundError:
        with open(stoptime + ".csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)
        writeConfigFile(stoptime)

#configs UE9 device only written as a function since I needed to catch the exception of the labjack device not being properly closed on a previous run. And needed to close and reopen the port
def ue9Config():
    d.getCalibrationData()
    d.streamConfig(NumChannels=1,ChannelNumbers=[0],ChannelOptions=[1],SettlingTime=0,Resolution=13,ScanFrequency=SCAN_FREQUENCY)



#This is the exit/cleanup program. closes the port to the labjack and gets rid of that object. additonally creates a header for the csv and then runs the save function.
def saveExit(a,b):
    print("Cleaning Up")

    stop = datetime.now()

    d.streamStop()

    d.close()

    sampleTotal = packetCount * d.streamSamplesPerPacket

    scanTotal = sampleTotal / 1

    sampleTotal -= missed

    runTime = (stop-start).seconds + float((stop-start).microseconds)/1000000

    parameters = ["Number of Packets:", packetCount, "Missed Samples", missed,"Run Time", runTime, "Scan Freq", (float(scanTotal)/runTime), "Set Scan Freq", SCAN_FREQUENCY, "Time", str(datetime.now()), "Volts to Pounds:", loadCellCalibration]

    saveData(dataOut, parameters,str(stop))

    print("Data saved exiting logging function")

    sys.exit(0)


#################################################################################################################################################################################################################

loadYAMLConfig()

#Device and code set up starts here.

d = ue9.UE9()


# MAX_REQUESTS is the number of packets to be read.
MAX_REQUESTS = 500
# SCAN_FREQUENCY is the scan frequency of stream mode in Hz
SCAN_FREQUENCY = 5000

#Handles termination signal sent by the onStart code
signal.signal(signal.SIGTERM, saveExit)
signal.signal(signal.SIGINT, saveExit)

print("Configuring UE9 stream")

ue9Config()

#Flushes data from previous stream
d.streamClearData()
print('Clearing Previous Data')


try:

    print("Starting Data Stream")

#Catches if port was not properly closed previously
    try:
        d.streamStart()
    except ue9.LowlevelErrorException:
        d.streamStop()
        d.close()
        d = ue9.UE9()
        ue9Config()
        d.streamStart()


    missed = 0
    dataCount = 0
    packetCount = 0
    calOffset = 0


#Calibration takes 100 packets and averages them and then writes that to the header of our data
    i = 0
    for r in d.streamData():
        if r is not None:
            if i == 100:
                calOffset = calOffset/100
                dataOut = [['Cal Offset', calOffset],['Time','Voltage','Pounds']]
                break
            else:
                i += 1
                calOffset += sum(r["AIN0"])/len(r["AIN0"])
        else:
            # Got no data back from our read.
            # This only happens if your stream isn't faster than the USB read
            # timeout, ~1 sec.
                print("No data ; %s" % datetime.now())

    start = datetime.now()

#d.streamData() is a yeild which is considered an iterable. Every time the for loop loops once it will update the r with the newest data and loop again for that data
#In essence as long as there is data being sent this will continuously loop.
#This is only broken by terminate or interupt signal. The parent process (The process run on the cronjob) handles this by looking for a button press

    for r in d.streamData():
        if r is not None:
        #catches missed packets
            if r["missed"] != 0:
                     missed += r['missed']

            data = ((sum(r["AIN0"])/len(r["AIN0"])) - calOffset)
            now = datetime.now()
            secsNow = (now-start).seconds + float((now-start).microseconds)/1000000
            pounds = data*loadCellCalibration
            dataOut.append([secsNow,data,pounds])

            dataCount += 1
            packetCount += r['numPackets']
            print(data)

        else:
            # Got no data back from our read.
            # This only happens if your stream isn't faster than the USB read
            # timeout, ~1 sec.
                print("No data ; %s" % datetime.now())
except:
    print("".join(i for i in traceback.format_exc()))
