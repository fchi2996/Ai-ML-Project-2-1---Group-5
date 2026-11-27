import json
import HyperparameterWeighted
# import Hyperparameter
import os
import yaml
import argparse

#python HyperparameterRandomizer.py [model .yaml file] [output .yaml file] [history .json file]
#python HyperparameterRandomizer.py debug_input.yaml debug_output.yaml debug_history.json
debug = False

#only used for debug. Overwritten if debug = false
input_yaml_filename  = "debug_input.yaml"
output_yaml_filename = "debug_output.yaml"
randomizer_data_file = "debug_history.json"

warnings = 0
warning_string = ""

'''
hyperparameter(parameter_name, parameter_type, values):
    parameter_name: Name found in the yaml file. This is everything before the colon. Case sensitive
    parameter_type: Type of the value to be randomly generated. This is the type of the stuff after the colon. Must be int, float, or str.
    values: Randomized values:
        int:   len(values) must be 3.   Random returns a random int   value [values[0], values[1]], inclusive both ends, using a step size of values[3]
        float: len(values) must be 2.   Random returns a random float value [values[0], values[1]]. Inclusive both ends
        str:   len(values) must be >=1. Random returns a random string from values.
'''
# hyperparameters = [
#         Hyperparameter.Hyperparameter("learning_rate", float, [0.00001, 0.001]),
#         Hyperparameter.Hyperparameter("batch_size",    int,   [32, 512, 16]),
#         Hyperparameter.Hyperparameter("buffer_size",   int,   [4, 64, 4]), #x * batch_size
#         Hyperparameter.Hyperparameter("hidden_units",  int,   [32, 512, 16]),
#         Hyperparameter.Hyperparameter("num_layers",    int,   [1, 3, 1]),
#         Hyperparameter.Hyperparameter("gamma",         float, [0.9, 0.995]),
#         Hyperparameter.Hyperparameter("beta",          float, [0.0001, 0.03])
#     ]

hyperparameters = [
        HyperparameterWeighted.HyperparameterWeighted("learning_rate", float, [0.00001, 0.001]),
        HyperparameterWeighted.HyperparameterWeighted("batch_size",    int,   [32, 512, 16]),
        HyperparameterWeighted.HyperparameterWeighted("buffer_size",   int,   [4, 64, 4]), #treated as x * batch_size for yaml, x for history
        HyperparameterWeighted.HyperparameterWeighted("hidden_units",  int,   [32, 512, 16]),
        HyperparameterWeighted.HyperparameterWeighted("num_layers",    int,   [1, 3, 1]),
        HyperparameterWeighted.HyperparameterWeighted("gamma",         float, [0.9, 0.995]),
        HyperparameterWeighted.HyperparameterWeighted("beta",          float, [0.0001, 0.03])
    ]

def recursive(data: dict, hyperparameters: list) -> int:
    checksum = 0
    for key, value in data.items():
        if isinstance(value, dict):
            checksum += recursive(value, hyperparameters)
            continue

        for index in range(len(hyperparameters)):
            if hyperparameters[index].get_name() == key:
                #buffer_size bodge:
                if hyperparameters[index].get_name() == "buffer_size":
                    for index2 in range(len(hyperparameters)):
                        if hyperparameters[index2].get_name() == "batch_size":
                            batch_size = hyperparameters[index2].get_random()

                    data.update({key: hyperparameters[index].get_random() * batch_size})

                else:
                    data.update({key: hyperparameters[index].get_random()})

                checksum += 1

    return checksum
#end recursive method

#main method
if debug:
    warnings += 1
    warning_string += "WARNING: Debug mode enabled. args will not be used\n"

print("Randomizing .yaml file")

if not debug: #parse args
    parser = argparse.ArgumentParser()

    parser.add_argument("input", help="the example .yaml file")
    parser.add_argument("output", help="the output .yaml file. this file will be overwritten if it already exists")
    parser.add_argument("history", help="the history .json file. if this file does not exist, a warning will be added and a new file will be created")

    args = parser.parse_args()

    input_yaml_filename = args.input
    output_yaml_filename = args.output
    randomizer_data_file = args.history

if not os.path.exists(input_yaml_filename):
    raise Exception("Cannot find input yaml file")

if not os.path.exists(randomizer_data_file):
    # ask_file_create = True
    # while ask_file_create:
    #     print("Could not find data file \"" + randomizer_data_file + "\". Create new file? (y/n) ", end="")
    #     answer = input()

    #     if answer.capitalize() == "Y":
    #         ask_file_create = False
    #         open(randomizer_data_file, "w").close()
    #         print("Created new data file. Created file at: \"" + os.path.abspath(randomizer_data_file) + "\"")
    #     elif answer.capitalize() == "N":
    #         ask_file_create = False
    #         raise Exception("Could not read data file. Please create a new one or copy an old one into the file location \"" + os.path.abspath(randomizer_data_file) + "\"")

    # ask_file_create = False
    open(randomizer_data_file, "w").close()
    warning_string += "WARNING: Created new data file. Created file at: \"" + os.path.abspath(randomizer_data_file) + "\"\n"
    warnings += 1

    history_dict = {}
    for i in range(len(hyperparameters)):
        history_dict.setdefault(hyperparameters[i].get_name(), [])

else:
    with open(randomizer_data_file, "r") as file:
        history_dict = json.load(file)
    print("Found json history file. Loaded data from \"" + str(len(history_dict[hyperparameters[0].get_name()])) + "\" previous runs")

for parameter in hyperparameters:
    parameter.set_random(history_dict[parameter.get_name()])
    history_dict[parameter.get_name()].append(parameter.get_random())

with open(input_yaml_filename, "r") as yaml_file:
    yaml_dict = yaml.safe_load(yaml_file)

checksum = recursive(yaml_dict, hyperparameters)

if len(hyperparameters) != checksum:
    raise Exception("Hyperparameter checksum failed. " + str(len(hyperparameters)) + " != " + str(checksum))

yaml_header = "#"
for index in range(len(hyperparameters)):
    yaml_header += hyperparameters[index].get_name()
    if index < len(hyperparameters)-1:
        yaml_header += ","
yaml_header += "\n#"
for index in range(len(hyperparameters)):
    if hyperparameters[index].get_name() == "buffer_size":
        for index2 in range(len(hyperparameters)):
            if hyperparameters[index2].get_name() == "batch_size":
                batch_size = hyperparameters[index2].get_random()

        yaml_header += str(batch_size * hyperparameters[index].get_random())

    else:
        yaml_header += str(hyperparameters[index].get_random())

    if index < len(hyperparameters)-1:
        yaml_header += ","

with open(output_yaml_filename, "w") as yaml_output_file:
    yaml_output_file.write(yaml_header + "\n")
    yaml.dump(yaml_dict, yaml_output_file, default_flow_style=False)
    yaml_output_file.flush()

with open(randomizer_data_file, "w") as randomizer_file:
    json.dump(history_dict, randomizer_file, indent=4)
    randomizer_file.flush()

print("");
for index in range(len(hyperparameters)):
    #this program is held together with scotch tape, hope, and zip ties
    if hyperparameters[index].get_name() == "buffer_size":
        for index2 in range(len(hyperparameters)):
            if hyperparameters[index2].get_name() == "batch_size":
                batch_size = hyperparameters[index2].get_random()
        print("Set \"" + hyperparameters[index].get_name() + "\" to \"" + str(hyperparameters[index].get_random() * batch_size) + "\"")
    else:
        print("Set \"" + hyperparameters[index].get_name() + "\" to \"" + str(hyperparameters[index].get_random()) + "\"")

print("")
print(".yaml file successfully generated. Randomized \"" + str(len(hyperparameters)) + "\" parameters")
print("History file name: \"" + randomizer_data_file + "\"")
print("  Model file name: \"" + input_yaml_filename + "\"")
print(" Output file name: \"" + output_yaml_filename + "\"")

if warnings > 0:
    print("\n\"" + str(warnings) + "\" warnings:\n" + warning_string)
