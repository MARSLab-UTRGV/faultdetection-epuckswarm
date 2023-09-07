from xml.etree import ElementTree as ET
from xml.dom import minidom
import os, time, random

#######################################################################################################
#                                          CONSTANTS                                                  #
#######################################################################################################

IN_XML_PATH = './experiments/epuck_foraging.argos'
OUT_XML_PATH = './experiments/epuck_foraging_mod.argos'
RESULTS_PATH = './results/'

#######################################################################################################
#                               XML PARSING AND MODIFICATION FUNCTIONS                               #
#######################################################################################################

# Helper function to format the XML file to look clean
def prettify_xml(elem):

    # Return a pretty-printed XML string for the Element.
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    
    return reparsed.toprettyxml(indent="\t")

# This is to set the fault behavior for the experiment
def set_fault_behavior(new_fault_behavior, input_xml = IN_XML_PATH, output_xml = OUT_XML_PATH):

    # Parse the XML file to get the root element
    tree = ET.parse(input_xml)
    root = tree.getroot()
    
    # Locate the <experiment_run> element within the nested structure
    experiment_run_element = root.findall(".//controllers/epuck_foraging_controller/params/experiment_run")
    
    # Modify the 'fault_behavior' attribute
    for elem in experiment_run_element:
        elem.attrib['fault_behavior'] = new_fault_behavior
    
    # Save the modified XML to a new file and prettify it
    with open(output_xml, 'w') as f:
        f.write(prettify_xml(root))
    
    return output_xml

# This is to set the results output filename for the experiment (this is where we collect the data). Stored in the 'results' folder.
def set_output_fname(outfile_name, input_xml = IN_XML_PATH, output_xml = OUT_XML_PATH):

    # Parse the XML file to get the root element
    tree = ET.parse(input_xml)
    root = tree.getroot()
    
    # Locate the <foraging> element within the nested structure
    foraging_element = root.findall(".//loop_functions/foraging")
    
    # Modify the 'output' attribute
    for elem in foraging_element:
        elem.attrib['output'] = RESULTS_PATH + outfile_name
    
    # Save the modified XML to a new file and prettify it
    with open(output_xml, 'w') as f:
        f.write(prettify_xml(root))

    # If RESULTS_PATH does not exist, create it
    if not os.path.exists(RESULTS_PATH):
        os.makedirs(RESULTS_PATH)
    
    return output_xml

# By default in the base argos file, the <visualization> element is not present. This function adds it (optional).
def add_visualization(input_xml = IN_XML_PATH, output_xml = OUT_XML_PATH):

    # Parse the existing XML file
    tree = ET.parse(input_xml)
    root = tree.getroot()

    # Create the new <visualization> element and its sub-elements
    visualization = ET.Element('visualization')
    
    qt_opengl = ET.SubElement(visualization, 'qt-opengl')
    
    camera = ET.SubElement(qt_opengl, 'camera')
    camera_placement = ET.SubElement(camera, 'placement', {'idx': '0', 'position': '0,0,2.0', 'look_at': '0,0,0', 'lens_focal_length': '15'})
    
    user_func1 = ET.SubElement(qt_opengl, 'user_functions', {'library': 'build/loop_functions/id_loop_functions/libid_loop_functions', 'label': 'id_qtuser_functions'})
    
    user_func2 = ET.SubElement(qt_opengl, 'user_functions', {'label': 'foraging_qt_user_functions'})
    
    # Append the new <visualization> element to the <argos-configuration> root element
    root.append(visualization)
    
    # Save the modified XML back to a new file and prettify it
    with open(output_xml, 'w') as f:
        f.write(prettify_xml(root))

    return output_xml

def set_random_seed(new_seed, input_xml = IN_XML_PATH, output_xml = OUT_XML_PATH):
    
        # Parse the existing XML file
        tree = ET.parse(input_xml)
        root = tree.getroot()
    
        # Locate the <loop_functions> element within the nested structure
        experiment_element = root.findall(".//framework/experiment")
        
        # Modify the 'random_seed' attribute
        for elem in experiment_element:
            elem.attrib['random_seed'] = new_seed
        
        # Save the modified XML back to a new file and prettify it
        with open(output_xml, 'w') as f:
            f.write(prettify_xml(root))
    
        return output_xml

# This is to set the ID of the faulty robot for the experiment. The default is 15 (corresponding to ep15) in the base argos file
def set_id_faulty_robot(new_id, input_xml = IN_XML_PATH, output_xml = OUT_XML_PATH):
        
     # Parse the XML file to get the root element
    tree = ET.parse(input_xml)
    root = tree.getroot()
    
    # Locate the <experiment_run> element within the nested structure
    experiment_run_element = root.findall(".//controllers/epuck_foraging_controller/params/experiment_run")
    
    # Modify the 'fault_behavior' attribute
    for elem in experiment_run_element:
        elem.attrib['id_faulty_robot'] = new_id
    
    # Save the modified XML to a new file and prettify it
    with open(output_xml, 'w') as f:
        f.write(prettify_xml(root))
    
    return output_xml

#######################################################################################################
#                                          DATA ANALYSIS                                              #
#######################################################################################################

def find_attackers(file_path, injected_id):

    with open(file_path, 'r') as f:
        lines = f.readlines()

    dict_tolerator_count = {}
    dict_attacker_count = {}

    fault_found = False

    # initialize dictionaries for robot ids with 0s
    for i in range(20):
        dict_tolerator_count[str(i)] = 0
        dict_attacker_count[str(i)] = 0

    for line in lines:
        # Split each line by tabs to separate columns
        columns = line.split("\t")

        
        # Check if line has relevant information
        if len(columns) >= 3:
            
            if columns[0].strip().split(" ")[0] == "Clock:":
                clock = columns[0].strip().split(" ")[1]
            else:
                # output error
                print("Error: Clock not found")
            
            # if the last two digits of the clock is not "99" or "00" then skip the rest of this iteration
            if clock[-2:] != "99" or clock[-2:] != "00":
                continue
            
            # if the last two digits of the clock is "99" then check for majority consensus (at the end of the coalition formation)
            elif clock[-2:] == "00":

                # get majority consensus at the end of the coalition formation
                maj_con = get_majority_consensus(dict_tolerator_count, dict_attacker_count, injected_id)

                # if maj_con isn't empty
                if maj_con:
                    print(f"Majority consensus found at time {clock}")
                    print(maj_con)
                    fault_found = True
                    # return fault_found
                
                # clear dictionaries for robot ids with 0s
                for i in range(20):
                    dict_tolerator_count[str(i)] = 0
                    dict_attacker_count[str(i)] = 0

                continue

            
            # We are only interested in the time intervals where the consensus is complete (clock ends in ..99)

            if columns[1].strip().split(" ")[0] == "Id:":
                robot_id = columns[1].strip().split(" ")[1]
            else:
                # output error
                print("Error: Robot ID not found")
            
            if columns[2].strip().split(" ")[0] == "FV:":
                fv = columns[2].strip().split(" ")[1]
            else: 
                # output error
                print("Error: FV not found")

            if columns[3].strip().split(" ")[0] == "Consensus_Tolerators:":

                tolerators = columns[3].strip().split(" ")

                # remove empty strings from the list
                tolerators = list(filter(None, tolerators))

                # remove the first element (the label)
                tolerators.pop(0)
            else:
                # output error
                print("Error: Consensus_Tolerators not found")
            
            if columns[4].strip().split(" ")[0] == "Consensus_Attackers:":
                
                attackers = columns[4].strip().split(" ")

                # remove empty strings from the list
                attackers = list(filter(None, attackers))

                # remove the first element (the label)
                attackers.pop(0)
                # if any(int(val) != -1 for val in attackers):
                #     print("Robot " + robot_id + " has attackers: " + str(attackers))

            else:
                # output error
                print("Error: Consensus_Attackers not found")

            # count the occurences if ids in the tolerators and attackers lists
            for tol, atk in zip(tolerators, attackers):
                if tol in dict_tolerator_count:
                    dict_tolerator_count[tol] += 1
                elif tol != "-1":
                    print(f"Error: Robot ID {tol} not found")

                if atk in dict_attacker_count:
                    dict_attacker_count[atk] += 1
                elif atk != "-1":
                    print(f"Error: Robot ID {atk} not found")
            
        
        
    # if not hasAttackers:
    #     print("No attackers found")
    # else:
    #     print("Attackers found")

    # if injected_bot_has_attackers:
    #     print("Injected robot has attackers")
    # else:
    #     print("Injected robot does not have attackers")

    return fault_found

def get_majority_consensus(tol_dict, atk_dict, injected_id):

    # get the number of robots in the swarm
    num_robots = 20

    fault_id_list = []

    for t_key, t_val, a_key, a_val in zip(tol_dict.keys(), tol_dict.values(), atk_dict.keys(), atk_dict.values()):
        if t_key != a_key:
            print("Error: Robot IDs do not match")
        else:
            if int(t_val) < int(a_val):       # if the number of attackers is greater than the number of tolerators it has a fault
                fault_id_list.append(t_key)
            if int(a_val) > (num_robots / 2):
                print(f"Robot {t_key} has majority consensus > 50%")
                input("Press Enter to continue...")
        # get input from console to continue
        # print(f"Robot {t_k} has {t_v} tolerators and {a_v} attackers")
        # input("Press Enter to continue...")

    return fault_id_list

#######################################################################################################
#                                          EXPERIMENTS                                                #
#######################################################################################################

def test_exp_1():

    out_xml_path = set_fault_behavior("FAULT_CIRCLE")
    out_xml_path = set_output_fname("test_exp1.txt", input_xml = out_xml_path)
    out_xml_path = set_random_seed("999", input_xml = out_xml_path)

    # select a random number from 0 to 19 (for 20 robots)
    rand_id = str(random.randint(0, 19))

    out_xml_path = set_id_faulty_robot("15", input_xml = out_xml_path)

    os.system("argos3 -c " + out_xml_path)
    find_attackers(RESULTS_PATH + "test_exp1.txt")

# loop through all faults
def test_exp_2():

    fault_list = ["FAULT_STRAIGHTLINE", "FAULT_RANDOMWALK", "FAULT_CIRCLE", "FAULT_STOP", "FAULT_PROXIMITYSENSORS_SETMIN", "FAULT_PROXIMITYSENSORS_SETMAX", "FAULT_PROXIMITYSENSORS_SETRANDOM", "FAULT_PROXIMITYSENSORS_SETOFFSET", "FAULT_RABSENSOR_SETOFFSET", "FAULT_RABSENSOR_MISSINGRECEIVERS", "FAULT_ACTUATOR_LWHEEL_SETZERO", "FAULT_ACTUATOR_RWHEEL_SETZERO", "FAULT_ACTUATOR_BWHEELS_SETZERO", "FAULT_SOFTWARE", "FAULT_POWER_FAILURE"]

    out_xml_path = set_output_fname("test_exp2.txt")

    for fault in fault_list:
        # select a random number from 0 to 19 (for 20 robots)
        rand_id = str(random.randint(0, 19))
        out_xml_path = set_id_faulty_robot(rand_id, input_xml = out_xml_path)
        out_xml_path = set_output_fname("test_exp2_" + fault + ".txt", input_xml = out_xml_path)
        out_xml_path = set_fault_behavior(fault, input_xml = out_xml_path)
        print("Running experiment with fault: " + fault)
        os.system("argos3 -c " + out_xml_path)
        find_attackers(RESULTS_PATH + "test_exp2_" + fault + ".txt")

#######################################################################################################
#                                             MAIN                                                    #
#######################################################################################################

if __name__ == '__main__':

    # test_exp_1()
    # test_exp_2()

    exp_list = [111, 222, 333, 444, 555, 666, 777, 888, 999, 101010, 111111, 121212, 131313, 141414, 151515, 161616, 171717, 181818, 191919, 202020]

    for seed in exp_list:
        if find_attackers(f"./other/FAULT_ACTUATOR_RWHEEL_SETZERO/nohup_{seed}", "15"):
            print(f"Fault found for seed {seed}")
            break

    # t_d, a_d = find_attackers(f"./other/FAULT_ACTUATOR_BWHEELS_SETZERO/nohup_{exp_list[0]}", "15")

    # print(get_majority_consensus(t_d, a_d, "15"))

    

    # list of faults
    # fault_list = ["FAULT_STRAIGHTLINE", "FAULT_RANDOMWALK", "FAULT_CIRCLE", "FAULT_STOP", "FAULT_PROXIMITYSENSORS_SETMIN", "FAULT_PROXIMITYSENSORS_SETMAX", "FAULT_PROXIMITYSENSORS_SETRANDOM", "FAULT_PROXIMITYSENSORS_SETOFFSET", "FAULT_RABSENSOR_SETOFFSET", "FAULT_RABSENSOR_MISSINGRECEIVERS", "FAULT_ACTUATOR_LWHEEL_SETZERO", "FAULT_ACTUATOR_RWHEEL_SETZERO", "FAULT_ACTUATOR_BWHEELS_SETZERO", "FAULT_SOFTWARE", "FAULT_POWER_FAILURE"]

    # for fault in fault_list:
    #     find_attackers(RESULTS_PATH + "test_exp2_" + fault + ".txt", "15")
