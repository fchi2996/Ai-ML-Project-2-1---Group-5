The current implementation combines three components:

1. **Java Training Launcher** – starts and manages multiple ML-Agents training experiments automatically.
    
2. **Hyperparameter Randomizer** – generates a different YAML configuration for each experiment by randomizing selected hyperparameters.
    
3. **CSV Writer Plugin** – collects training data and saves it in CSV format for later analysis.

## CSV write plugin
The CSV writer plugin collects training information and saves it in CSV format. These files can later be used for data analysis and for investigating the relationship between experiment parameters and model performance.

### Installation
This installation guide 

The plugin must be installed in the main `ml-agents` directory.

1. Open a terminal in the main `ml-agents` directory.
    
2. Activate the Conda environment:
    

```bash
conda activate mlagents
```

4. Install the plugin using:
    

```bash
pip install -e ./csv_plugin
```

The `-e` option installs the plugin in editable mode.

**Note:** If your Conda environment has a different name, activate your own ML-Agents environment instead. 

The csv file from the run should be in folder ->`results/csv_output/`

### Integration with the automation

The CSV plugin is installed in the ML-Agents environment and is intended to collect data during training. It does not need to be started separately by the Java launcher.

## Hyperparameter Randomizer

The hyperparameter randomizer is a Python component developed to generate randomized YAML configurations.

It consists of two files:

- `HyperparameterRandomizer.py`: handles the randomization process and reads the input and output file paths.
    
- `Hyperparameter.py`: defines the hyperparameters and the possible values from which they can be randomized.
    

#### How it works

The randomizer receives two arguments:

1. The original YAML configuration file.
    
2. The destination path for the generated YAML file.
    

Its command-line structure is:

```bash
python HyperparameterRandomizer.py input.yaml output.yaml
```

The randomizer reads the original configuration, randomizes the selected hyperparameters, and writes the resulting configuration to the specified output file.

The output file is overwritten if it already exists.

#### Integration with the Java launcher

The Java launcher automatically executes the randomizer before starting each training experiment.

For every experiment, it generates a unique YAML filename based on the experiment's run ID.

For example:

```text
output_Experiment_20261108_1.yaml
output_Experiment_20261108_2.yaml
output_Experiment_20261108_3.yaml
```

This means each experiment has its own configuration file. Keeping these files makes it possible to identify which hyperparameters were used in each training run.

## Java Training Launcher

The Java launcher automates the execution of multiple ML-Agents training experiments.

Its main responsibilities are:

- Read the number of experiments and the paths supplied by the user.
    
- Validate the provided input paths.
    
- Locate the Python randomizer.
    
- Generate a unique run ID for each experiment.
    
- Execute the hyperparameter randomizer.
    
- Start ML-Agents training using the generated YAML file.
    
- Monitor the training process.
    
- Record experiment information in a training log.
    
- Keep track of successful and failed experiments.
    
- Measure the duration of each training run.
    

### Command-line arguments

The launcher accepts three arguments:

|Argument|Description|
|---|---|
|`args[0]`|Number of experiments|
|`args[1]`|Path to the original YAML configuration|
|`args[2]`|Path to the Unity environment build|

Example:

```bash
java MLAgentLauncher 5 "/path/to/ml-agents/config/ppo/3DBall.yaml" "/path/to/ml-agents/Builds/3DBall/3DBall.app"
```

The paths should be adapted to the user's own project location.

This approach avoids hardcoding one person's local directory paths into the Java source code.

### Execution workflow

For each experiment, the launcher performs the following steps:

1. Generates a unique run ID.
    
2. Executes `HyperparameterRandomizer.py`.
    
3. Generates a new randomized YAML configuration.
    
4. Checks whether the randomizer completed successfully.
    
5. Starts ML-Agents using `mlagents-learn`.
    
6. Supplies the generated YAML file, run ID, and Unity environment build path.
    
7. Monitors the training process using Java's `Process` methods.
    
8. Waits for training to finish.
    
9. Records the exit code and training duration.
    
10. Moves on to the next experiment if the previous training run was successful.
    

If the randomizer or training process fails, the launcher stops the experiment sequence.

### Process management

The launcher uses Java's `ProcessBuilder` to execute external commands.

It uses:

- `start()` to start an external process.
    
- `isAlive()` to check whether a process is still running.
    
- `waitFor()` to wait for the process to finish.
    
- `exitValue` (through the return value of `waitFor()`) to determine whether the process completed successfully.
    

The exit code is used to distinguish successful and unsuccessful executions. An exit code of `0` indicates success.

### Training log

The launcher creates a `training_log.txt` file containing information about the experiments, including:

- Run ID
    
- Configuration path
    
- Environment path
    
- Exit code
    
- Training duration
    

The launcher also keeps track of the number of successful and failed training experiments.

The process repeats for the requested number of experiments.

Each experiment uses a different run ID and a separately generated YAML configuration.

## How to Run the Project

1. Clone or open the main `ml-agents` project.
    
2. Make sure the `csv_plugin` folder is in the main project directory.
    
3. Install the CSV plugin using the instructions in Section 3.
    
4. Activate the Conda environment containing ML-Agents.
    
5. Make sure the Unity environment has been built and placed in `Builds/`.
    
6. Make sure the original YAML configuration exists.
    
7. Compile the Java launcher:
    

```bash
javac MLAgentLauncher.java
```

8. Run the launcher with the three required arguments:
    

```bash
java MLAgentLauncher 5 "/path/to/config/ppo/3DBall.yaml" "/path/to/Builds/3DBall/3DBall.app"
```

9. After execution, inspect:
    
    - `training_log.txt` for experiment information.
        
    - `results/` for ML-Agents training results.
        
    - `results/csv_output/` for CSV data.
        
    - `Project/Automation/randomizer/` for generated YAML configurations.
