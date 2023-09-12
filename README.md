# BlueTDTExpansion
## Problem definition
In any given case, there could be several number of laser shots executed for a period of time. Before a laser shot, a Trajectory is planned to insert the laser probe at the right location. For every shot (Trajectory), the software will allow user to scan the brain area every 10 seconds before during and after the shot treatment. Each scan is called a measurement. In each measurement, the software will collect images from 3 traverse planes (normal to the probe axis). Each plane is called slice.    

The company has a software tool that can provide:
	 .bcp files that contain the 2D coordinates of all the blue line pixels that make the blue TDT contour in every image slices and the order to connect them
	 .lsr files that contain the (measurement, laser status) pairs of every trajectory

Need to find the maximum distance (of two furthest points on the TDT blue line contour) for all image slices to plot the blue TDT expansion over time
## Algorithms
Note that the script can only recognize certain filename patterns. Edit the script if necessary when the filename patterns differ from the following:
	
 &ensp;  &nbsp; &nbsp; &nbsp;lsr file patterns:
	    
    lsr_pattern1 = r"My Trajectory(\d{8})_(\d{6})_"
		Example: "My Trajectory20230910_123059_Slice 5"
		format is My Trajectory(YYYYMMDD)_(hhmmss)_(the rest of the filename)
            lsr_pattern2 = r"My Trajectory-(\d{9})_(\d{6})_"
		Example: "My Trajectory220230910_123059_Slice 5" 
		format is My Trajectory(1 Number)(YYYYMMDD)_(hhmmss)_(the rest of the filename)
            lsr_pattern3 = r"[a-zA-Z0-9]+_([a-zA-Z]{2})(\d{8})_(\d{6})_"
		Example: "PG6_LR20230826_183429_Slice 9"
		format: (Combination of letters and digits)_(Two Letters)(YYYYMMDD)_(hhmmss)_(the rest of the filename)
	
 &ensp;  &ensp; &ensp; &ensp;bcp file patterns:
 
	  bcp_pattern = r'(\d{4}-\d{2}-\d{2}) (\d{2}\.\d{2}\.\d{2}).(\d+)_(\d)'
		Example: "2023-08-26 19.08.08.148_0"
		format: (YYYY)-(MM)-(DD) (hh).(mm).(ss).(measurement)_(slice number) 
			slice number could be '0' (slice D1), '1' (slice 1), '2' (slice 2)
## How to run the program
* Install python3 and clone the repository to your local machine
* In the python script, change the 'PIG_folder' value to folder path of the folder that contains the CAT exported files
* In terminal, navigate to the repository, type "bluelineanalyzer.py" to run the script
* The script will export the csv files, each corresponds to a trajectory and contains (elapsed time, max distance) for all the slices

## Disclaimers
Portions of the code and the demo dataset have been modified to protect the company's proprietary information. The information in exported files does not represent the real performance of the system. 
