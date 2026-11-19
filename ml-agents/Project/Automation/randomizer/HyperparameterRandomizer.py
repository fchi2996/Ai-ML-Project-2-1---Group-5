import Hyperparameter
import os
import yaml
import argparse

#python HyperparameterRandomizer.py [model .yaml file] [output .yaml file]
debug = False
'''
hyperparameter(parameter_name, parameter_type, values):
    parameter_name: Name found in the yaml file. This is everything before the colon. Case sensitive
    parameter_type: Type of the value to be randomly generated. This is the type of the stuff after the colon. Must be int, float, or str.
    values: Randomized values:
        int:   len(values) must be 3.   Random returns a random int   value [values[0], values[1]], inclusive both ends, using a step size of values[3]
        float: len(values) must be 2.   Random returns a random float value [values[0], values[1]]. Inclusive both ends
        str:   len(values) must be >=1. Random returns a random string from values.
'''
hyperparameters = [
        Hyperparameter.Hyperparameter("learning_rate", float, [0.00001, 0.001]),
        Hyperparameter.Hyperparameter("batch_size",    int,   [32, 512, 16]),
        Hyperparameter.Hyperparameter("buffer_size",   int,   [4, 64, 4]), #x * batch_size
        Hyperparameter.Hyperparameter("hidden_units",  int,   [32, 512, 16]),
        Hyperparameter.Hyperparameter("num_layers",    int,   [1, 3, 1]),
        Hyperparameter.Hyperparameter("gamma",         float, [0.9, 0.995]),
        Hyperparameter.Hyperparameter("beta",          float, [0.0001, 0.03])
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
    print("!!! DEBUG MODE !!!")

print("Randomizing .yaml file")

#only used for debug. Overwritten if debug = false
input_yaml_filename = "example.yaml"
output_yaml_filename = "debug_output.yaml"

if not debug: #parse args
    parser = argparse.ArgumentParser()

    parser.add_argument("input", help="the example .yaml file")
    parser.add_argument("output", help="the output .yaml file. this file will be overwritten if it already exists")

    args = parser.parse_args()

    input_yaml_filename = args.input
    output_yaml_filename = args.output

if not os.path.exists(input_yaml_filename):
    raise Exception("Cannot find input yaml file")

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

print("") #new line
for index in range(len(hyperparameters)):
    #this program is held together with scotch tape, hope, and zip ties
    if hyperparameters[index].get_name() == "buffer_size":
        for index2 in range(len(hyperparameters)):
            if hyperparameters[index2].get_name() == "batch_size":
                batch_size = hyperparameters[index2].get_random()
        print("Set \"" + hyperparameters[index].get_name() + "\" to \"" + str(hyperparameters[index].get_random() * batch_size) + "\"")
    else:
        print("Set \"" + hyperparameters[index].get_name() + "\" to \"" + str(hyperparameters[index].get_random()) + "\"")

print("\n.yaml file successfully generated. Randomized \"" + str(len(hyperparameters)) + "\" parameters\n\n Model file name: \"" + input_yaml_filename + "\"\nOutput file name: \"" + output_yaml_filename + "\"")

if debug:
    print("!!! DEBUG MODE !!!")
