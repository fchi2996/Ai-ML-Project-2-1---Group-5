import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class MLAgentLauncher {
    public static void main(String[] args) {
        if (args.length == 0) { // check number of experiments
            System.out.println("Please specify the number of experiments.");
            return;
        }
        if (args.length < 3) {
            System.out.println(
                    "Please specify the number of experiments, YAML configuration path, and Unity build path.");
            return;
        }
        String configPath = args[1];
        String environmentPath = args[2];

        File configFile = new File(configPath);

        if (!configFile.exists() || !configFile.isFile()) {
            System.out.println("Invalid YAML configuration file.");
            return;
        }

        File environmentFile = new File(environmentPath);

        if (!environmentFile.exists()) { // prevents the launcher from starting a training process with a nonexistent
                                         // Unity build.
            System.out.println("Invalid Unity build path.");
            return;
        }

        int numberOfExperiments;

        try {
            numberOfExperiments = Integer.parseInt(args[0]);

            if (numberOfExperiments <= 0) {
                System.out.println("The number of experiments must be positive.");
                return;
            }

        } catch (NumberFormatException e) {
            System.out.println("Invalid input. Please enter a number.");
            return;
        }

        try {
            String timestamp = LocalDateTime.now()
                    .format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));

            int successfulExperiments = 0;
            int failedExperiments = 0;

            long totalStartTime = System.currentTimeMillis(); // to measure the total time taken for all experiments

            File sourceFile = new File(
                    MLAgentLauncher.class.getProtectionDomain().getCodeSource().getLocation().toURI());

            File randomizerScript = new File(sourceFile.getParentFile(), "randomizer/HyperparameterRandomizer.py");

            System.out.println("Randomizer found: " + randomizerScript.exists());
            System.out.println("Randomizer path: " + randomizerScript.getAbsolutePath());

            // Merges each experiment's CSV with the randomized values of its YAML
            File mergeScript = new File(randomizerScript.getParentFile(), "merge_experiment.py");
            String csvDir = new File("results", "csv_output").getAbsolutePath(); // where the csv-plugin writes
            String mergedDir = new File("results", "merged").getAbsolutePath(); // 3DBall1.csv, 3DBall2.csv, ...

            for (int i = 1; i <= numberOfExperiments; i++) {
                String runId = "Experiment_" + timestamp + "_" + i;

                String outputConfigPath = "output_" + runId + ".yaml";

                ProcessBuilder randomizer = new ProcessBuilder(
                        "python",
                        randomizerScript.getAbsolutePath(),
                        configPath,
                        new File(randomizerScript.getParentFile(), outputConfigPath).getAbsolutePath());

                randomizer.inheritIO();
                Process randomizerProcess = randomizer.start();
                int randomizerExitCode = randomizerProcess.waitFor();

                if (randomizerExitCode != 0) {
                    System.out.println("Randomizer failed");
                    break;
                }

                ProcessBuilder processBuilder = new ProcessBuilder(
                        "mlagents-learn",
                        new File(randomizerScript.getParentFile(), outputConfigPath).getAbsolutePath(),
                        "--run-id=" + runId,
                        "--env=" + environmentPath, // Specify the Unity build path
                        "--no-graphics",
                        "--timeout-wait=300"

                );
                // Start the process
                processBuilder.inheritIO();

                long startTime = System.currentTimeMillis(); // to measure the time taken for each experiment
                Process process = processBuilder.start();

                System.out.println("Is it running? " + process.isAlive());

                int exitCode = process.waitFor();

                long endTime = System.currentTimeMillis(); // to measure the time taken for each experiment

                long duration = (endTime - startTime) / 1000; // to measure the time taken for each experiment

                System.out.println("Experiment " + i + " process ended.");
                System.out.println("Exit code: " + exitCode);
                System.out.println("Duration: " + duration + " seconds");

                // training_log.txt will contain the run ID, configuration path, exit code, and
                // duration for each experiment
                String logEntry = "Run ID: " + runId + "\n" +
                        "Configuration: "
                        + new File(randomizerScript.getParentFile(), outputConfigPath).getAbsolutePath() + "\n" +
                        "Environment: " + environmentPath + "\n" +
                        "Exit code: " + exitCode + "\n" +
                        "Duration: " + duration + " seconds\n" +
                        "------------------------------\n";

                try (BufferedWriter writer = new BufferedWriter(new FileWriter("training_log.txt", true))) {
                    // true means append mode. Instead of overwriting the file every time, Java adds the new information at the end.
                    writer.write(logEntry);
                }

                if (exitCode != 0) {
                    failedExperiments++;
                    System.out.println("Experiment " + i + " failed!");
                    break;
                } else {
                    successfulExperiments++;

                    // Merge this experiment's CSV with its YAML -> results/merged/3DBall<N>.csv
                    int mergeExitCode = runPython(mergeScript, "merge",
                            "--yaml", new File(randomizerScript.getParentFile(), outputConfigPath).getAbsolutePath(),
                            "--csv-dir", csvDir,
                            "--out-dir", mergedDir);
                    if (mergeExitCode != 0) {
                        System.out.println("Merging the CSV of experiment " + i + " failed!");
                        break;
                    }
                }
            }

            // Append all merged CSVs into results/merged/3DBall_all.csv
            if (successfulExperiments > 0) {
                runPython(mergeScript, "combine", "--out-dir", mergedDir);
            }
            long totalEndTime = System.currentTimeMillis();
            long totalDuration = (totalEndTime - totalStartTime) / 1000;

            System.out.println("\n========== EXECUTION SUMMARY ==========");
            System.out.println("Experiments requested: " + numberOfExperiments);
            System.out.println("Experiments attempted: " + (successfulExperiments + failedExperiments));
            System.out.println("Successful experiments: " + successfulExperiments);
            System.out.println("Failed experiments: " + failedExperiments);
            System.out.println("Total execution time: " + totalDuration + " seconds");
            System.out.println("========================================");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // Runs a Python script with arguments, shows its output, and returns its exit code
    private static int runPython(File script, String... arguments) throws Exception {
        java.util.List<String> command = new java.util.ArrayList<>();
        command.add("python");
        command.add(script.getAbsolutePath());
        command.addAll(java.util.Arrays.asList(arguments));
        ProcessBuilder builder = new ProcessBuilder(command);
        builder.inheritIO();
        return builder.start().waitFor();
    }
}
