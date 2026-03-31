
import sys
import traceback
import yaml
import ue9


###########################################################All Functions Defined Here##############################################################################################################
def calibrateLoadCell():
    #Device and code set up starts here.

    d = ue9.UE9()


    # MAX_REQUESTS is the number of packets to be read.
    MAX_REQUESTS = 500
    # SCAN_FREQUENCY is the scan frequency of stream mode in Hz
    SCAN_FREQUENCY = 5000
    ue9Config()

    #Flushes data from previous stream
    d.streamClearData()
    try:
  
    #Catches if port was not properly closed previously
        try:
            d.streamStart()
        except ue9.LowlevelErrorException:
            d.streamStop()
            d.close()
            d = ue9.UE9()
            ue9Config()
            d.streamStart()



        calOffset = 0

        print("Do not put any weight on load cell. Zeroing...")
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

        print("Please put your standard on the load cell and press enter")
        input()
        loadCellData = 0
        i = 0
        for r in d.streamData():
            if r is not None:
                if i == 100:
                    loadCellData = LoadCellData/100
                    break
                else:
                    i += 1
                    loadCellData += sum(r["AIN0"])/len(r["AIN0"])
        else:
            # Got no data back from our read.
            # This only happens if your stream isn't faster than the USB read
            # timeout, ~1 sec.
                print("No data ; %s" % datetime.now())
        print("What was your standards weight in pounds?")
        while True:
            try:
                standard = float(input())
                break
            except:
                print("Please enter only numbers? (Your number can include decimal points)")
        pounds = loadCellData/standard
    except:
        print("".join(i for i in traceback.format_exc()))

    with open("calibrations.yaml", "r") as f:
         calibrations = yaml.safe_load(f) or {}

    print("What would you like to name this calibration?")
    while True:
        calName = input()
        if calibrations[calName] is None:
            break
        print(calName + " already exists please enter a different name.")
    calibrations[calName] = pounds

    with open(calibrations.yaml", "w") as f:
        yaml.safe_dump(calibrations, f, sort_keys=False)
    print("Here is an updated list of calibration keys and values")
    print(calibrations)
    d.streamStop()
    d.close()

def createTestConfig():
    print("What folder would you like to save the file to?(Do not include slashes)")
    directory = input()

    with open("calibrations.yaml", "r") as f:
        calibrations = yaml.safe_load(f) or {}

    print(calibrations)
    print("What load cell will you be using? (The key must be present in the above dictionary)")
    calibrationName = input()
    configFile = {"Directory":directory, "CalibrationName":calibrationName}
    with open("configFile.yaml, "w") as f:
            yaml.safe_dump(configFile, f, sort_keys = False)
    
#configs UE9 device only written as a function since I needed to catch the exception of the labjack device not being properly closed on a previous run. And needed to close and reopen the port
def ue9Config():
    d.getCalibrationData()
    d.streamConfig(NumChannels=1,ChannelNumbers=[0],ChannelOptions=[1],SettlingTime=0,Resolution=13,ScanFrequency=SCAN_FREQUENCY)



#This is the exit/cleanup program. closes the port to the labjack and gets rid of that object. additonally creates a header for the csv and then runs the save function.
def saveExit(a,b):
    print("Cleaning Up")
    if d.streamStarted:
        d.streamStop()
        d.close()

    sys.exit(0)


#################################################################################################################################################################################################################


#Handles termination signal sent by the onStart code
signal.signal(signal.SIGTERM, saveExit)
signal.signal(signal.SIGINT, saveExit)

while True:
    print("Enter 0 if you would like to calibrate a load cell and 1 if you would like to create a test config file")
    while True:
        try:
            mode = int(input())
            if mode == 0 || mode == 1:
                break
            else:
                print("Enter only either 0 or 1")
        except:
            print("Enter only either 0 or 1")
    if mode == 0:
        calibrateLoadCell()
    else if mode == 1:
        createTestConfig()
    print("Press enter if you would like to do another action or press control C if you are done")
    
