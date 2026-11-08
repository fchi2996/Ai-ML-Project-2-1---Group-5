import random

class Hyperparameter:
    '''
    parameter_name: Name found in the yaml file. This is everything before the colon. Case sensitive
    parameter_type: Type of the value to be randomly generated. This is the type of the stuff after the colon. Must be int, float, or str.
    values: Randomized values:
        int:   len(values) must be 3.   Random returns a random int   value [values[0], values[1]], inclusive both ends, using a step size of values[3]
        float: len(values) must be 2.   Random returns a random float value [values[0], values[1]]. Inclusive both ends
        str:   len(values) must be >=1. Random returns a random string from values.
    '''
    def __init__(self, parameter_name: str, parameter_type: type, values: list[int | float | str]):

        #type validation
        if parameter_type is not int and parameter_type is not float and parameter_type is not str:
            raise Exception("Type must be int, str, or float.\nOffending parameter name: " + parameter_name)

        #int type validation
        if parameter_type is int:
            if len(values) != 3:
                raise Exception("For int type, values must be length of exactly 3\nOffending parameter name: " + parameter_name)

            for index in range(3):
                if type(values[index]) is not int:
                    raise Exception("For int type, each value in values must be of type int\nOffending parameter name: " + parameter_name)

            if values[0] > values[1]:
                raise Exception("For int type, values[0] <= values[1] must be true\nOffending parameter name: " + parameter_name)
            
        #float type validation
        if parameter_type is float:
            if len(values) != 2:
                raise Exception("For float type, values must be length of exactly 2\nOffending parameter name: " + parameter_name)

            if parameter_type is float:
                for index in range(2):
                    if type(values[index]) is not int and type(values[index]) is not float:
                        raise Exception("For float type, each value in values must be of type int or float\nOffending parameter name: " + parameter_name)
        
            if type(values[0]) is not type(values[1]):
                raise Exception("For float type, type of values must match\nOffending parameter name: " + parameter_name)

        #str type validation
        if parameter_type is str:
            if len(values) < 1:
                raise Exception("For str type, values must be of length >=1\nOffending parameter name: " + parameter_name)

            for index in range(len(values)):
                if type(values[index]) is not str:
                    raise Exception("For str type, each value in values must be of type str\nOffending parameter name: " + parameter_name)

        #vars validated
        
        self.parameter_name = parameter_name
        self.type = parameter_type
        self.values = values

    def get_random(self) -> int | str | float:
        if self.type is int:
            # return random.randint(self.values[0], self.values[1])
            return random.randrange(self.values[0], self.values[1]+1, self.values[2])

        if self.type is float:
            #v[0] + (rand * (v[1]-v[0]))
            return self.values[0] + (random.random() * (self.values[1] - self.values[0]))

        if self.type is str:
            return random.choice(self.values)

    def get_name(self) -> str:
        return self.parameter_name
