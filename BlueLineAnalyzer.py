import re
import os
import glob
from itertools import tee
from datetime import datetime, timedelta
import numpy
import csv
from scipy.spatial.distance import cdist

PIG_folder = "/Users/tranlu/Downloads/PCD/PIG-demo"
ratio = 3.14
def read_laser_status(pathname):
        laser_on_measurement = []
        with open(pathname) as f:
            lines = f.readlines()
            for line in lines:
                measurement, laser_status = re.split("[:]+", line)
                laser_on_measurement.append([int(measurement), laser_status.strip()])
        return laser_on_measurement 

class Trajectory(object):
    def __init__(self, pathname=None):
        self.path = pathname
        if self.path is not None:
            basename = os.path.basename(self.path)
            self.just_name = os.path.splitext(basename)[0]
            lsr_pattern1 = r"My Trajectory(\d{8})_(\d{6})_"
            lsr_pattern2 = r"My Trajectory-(\d{9})_(\d{6})_"
            lsr_pattern3 = r"[a-zA-Z0-9]+_([a-zA-Z]{2})(\d{8})_(\d{6})_"
            match = re.search(lsr_pattern1,self.just_name)
            if not match:
                match = re.search(lsr_pattern2,self.just_name)
            if match:
                self.date = match.group(1)  #YYYYMMDD
                self.timestamp = datetime.strptime(match.group(2), '%H%M%S') #hhssmm
            else:
                match = re.search(lsr_pattern3,self.just_name)
                if match:
                    self.date = match.group(2)  #YYYYMMDD
                    self.timestamp = datetime.strptime(match.group(3), '%H%M%S') #hhssmm
                else:  
                    print("Pattern not found in the filename")
            self.measurements = read_laser_status(self.path) # a list of [measurement, laser status]
        else:
            self.just_name = None
            self.timestamp = None
            self.date = None
            self.measurements = None
    def copy(self):
        return Trajectory(self)

class Slice(object):
    def __init__(self, pathname=None, measurement = None, slice_name = None, laser_status='OFF'):
        self.path = pathname
        try:
            basename = os.path.basename(self.path)
            self.just_name = os.path.splitext(basename)[0]
            bcp_pattern = r'(\d{4}-\d{2}-\d{2}) (\d{2}\.\d{2}\.\d{2}).(\d+)_(\d)'
            match = re.search(bcp_pattern,self.just_name)
            if match:
                self.date = match.group(1)  #YYYY-MM-DD
                self.timestamp = datetime.strptime(match.group(2), '%H.%M.%S') #hh.ss.mm
                self.measurement = int(match.group(3))
                self.slice_name = int(match.group(4))
        except TypeError:
            self.date = None
            self.timestamp = None
            self.measurement = measurement
            self.slice_name = slice_name
        self.laser_status = laser_status
        self.elapsed_time = 0 
        self.blue_line_1 = 0  # max oblong distance
        self.blue_line_2 = 0  # max distance from probe center (radial distance)
    def copy(self):
        return Slice(self)
    def calculate_blue_line(self):
        # Read bcp file:
        blue_pixel_coordinates = []
        if self.path is not None:
            with open(self.path, 'r') as f:
                for line_num, line in enumerate(f, start=1):   
                    if line_num == 1:
                        probe_center = numpy.array([float(x) for x in line.split(',')])  
                    elif line_num == 2:
                        connected_pts = [int(x) for x in line.split(',')]    
                    else:
                        blue_pixel_coordinates.append(numpy.array([float(x) for x in line.split(',')]))
            f.close()

            # Calculation
            connected_pts_cnt = connected_pts[0]
            contours = {}
            contours_cnt = 0
            # build contour coordinates list
            for conn in connected_pts[1:]:
                if connected_pts_cnt == 0:
                    connected_pts_cnt = conn
                    contours_cnt += 1
                else:
                    connected_pts_cnt -= 1
                    point = blue_pixel_coordinates[conn]
                    points_list = contours.get(contours_cnt, [])
                    points_list.append(point)
                    contours[contours_cnt] = points_list
            # Find max distance between two points
            max_distance = 0
            for key, value in contours.items():
                dist_matrix = cdist(value, value, metric='euclidean')
                if dist_matrix.max() > max_distance:
                    max_distance = dist_matrix.max()
                # best_pair = np.unravel_index(dist_matrix.argmax(), dist_matrix.shape)
                # [points_list[best_pair[0]],points_list[best_pair[1]]]
            self.blue_line_1 = max_distance*ratio


def create_object_list(extension, func):
    list = []
    files = glob.glob(PIG_folder + '/*.'+ extension)
    for f in files:
        instance = func(f)
        list.append(instance)

    list = sorted(list, key=lambda x: x.timestamp)
    return list
    
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, -1)
    return zip(a, b) 

def export_dict_to_csv(csv_output_path, list_arg):
    if not os.path.exists(csv_output_path):
        f = open(csv_output_path, 'w', newline='')
        csv.writer(f).writerow(
            ['Elapsed Time [s]', 'Measurement', 'Laser Status',
             'D1_oblong [mm]','1_oblong [mm]', '2_oblong [mm]'])
        f.close()
    for measurement, slice_group in list_arg.items():
        with open(csv_output_path, 'a', newline='') as f:
            csv.writer(f).writerow(
                [slice_group[0].elapsed_time, measurement, slice_group[0].laser_status,
                slice_group[0].blue_line_1, slice_group[1].blue_line_1, slice_group[2].blue_line_1])
            f.close()

slices = create_object_list('bcp', Slice)
trajectories = create_object_list('lsr', Trajectory)
trajectory_last = Trajectory()
trajectory_last.timestamp = slices[-1].timestamp
trajectories.append(trajectory_last)
trajectories = iter(trajectories)

#Exporting blue line rate to csv:
for current_trajectory, next_trajectory in pairwise(trajectories):
    print(f"Current: {current_trajectory.timestamp}. Next: {next_trajectory.timestamp}")
    trajectory_slices = [slice for slice in slices if slice.timestamp >= current_trajectory.timestamp and slice.timestamp <= next_trajectory.timestamp]
    # Match slice and trajectory based on measurement and assign laser status to slice:
    measurement_to_status = {measurement[0]: measurement[1] for measurement in current_trajectory.measurements}
    for slice in trajectory_slices:
        if slice.measurement in measurement_to_status:
            slice.laser_status = measurement_to_status[slice.measurement]
    # Padding missing slices due to no blue pixel
    slice_dict = {slice.measurement: [s for s in trajectory_slices if s.measurement == slice.measurement] for slice in trajectory_slices}
    for measurement, status in measurement_to_status.items():
        if measurement not in slice_dict.keys():
            slice_dict[measurement] = [Slice(None,measurement, x_slice, status) for x_slice in range(3)] #by default, these slice instances blue line = 0
        else:
            existing_slices = {s.slice_name for s in slice_dict[measurement]}
            missing_slices = set(range(3)) - existing_slices
            for sname in missing_slices:
                slice_dict[measurement].append(Slice(None,measurement, sname, status))
            sorted_measurement = sorted(slice_dict[measurement], key=lambda x: x.slice_name)
            slice_dict[measurement] = sorted_measurement
    slice_dict = dict(sorted(slice_dict.items()))
    #Calculate blue line and elapsed time
    try:
        laser_on_measurements = [slice_on.measurement for slices_value in slice_dict.values() for slice_on in slices_value if slice_on.laser_status == "ON"]
        start_measurement = min(laser_on_measurements)
        for group_slices in slice_dict.values():
            for slice in group_slices:
                slice.calculate_blue_line()
                slice.elapsed_time = max(0,(slice.measurement - start_measurement)*10)
        #Write to an csv file:
        output_path = '/Users/tranlu/Downloads/PCD/exports/PIG-demo/Output_Trajectory_' + current_trajectory.just_name + '.csv'
        export_dict_to_csv(output_path, slice_dict)
    except ValueError:
        print(f"No laser from {current_trajectory.timestamp} to {next_trajectory.timestamp}")
    






            



