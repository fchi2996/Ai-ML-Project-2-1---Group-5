import Hyperparameter
import os
import yaml
import argparse

#python HyperparameterRandomizer.py [model .yaml file] [output .yaml file]

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
        Hyperparameter.Hyperparameter("buffer_size", int, [10000, 25000, 5000]),
        Hyperparameter.Hyperparameter("gamma", float, [0, 1]),
        #Hyperparameter.Hyperparameter("learning_rate_schedule", str, ["Option A", "Option B", "Option C"])
        Hyperparameter.Hyperparameter("learning_rate_schedule", str, ["linear", "constant"])
    ]

def recursive(data: dict, hyperparameters: list) -> int:
    checksum = 0
    for key, value in data.items():
        if isinstance(value, dict):
            checksum += recursive(value, hyperparameters)
            continue

        for index in range(len(hyperparameters)):
            if hyperparameters[index].get_name() == key:
                data.update({key: hyperparameters[index].get_random()})
                checksum += 1

    return checksum
#end recursive method

#main method
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

with open(output_yaml_filename, "w") as yaml_output_file:
    yaml.dump(yaml_dict, yaml_output_file, default_flow_style=False)

print(".yaml file successfully generated. Randomized " + str(len(hyperparameters)) + " parameters.\nOutput to file \"" + output_yaml_filename + "\"")
