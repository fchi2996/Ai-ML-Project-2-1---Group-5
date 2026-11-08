import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.io.File;
import java.io.FileWriter;
import java.io.BufferedWriter;

public class MLAgentLauncher {
    public static void main (String[] args) {
        if (args.length == 0) { //check number of experiments
            System.out.println("Please specify the number of experiments.");
            return;
        }
        if (args.length < 3) {
            System.out.println("Please specify the number of experiments, YAML configuration path, and Unity build path.");
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

        if (!environmentFile.exists()) { //prevents the launcher from starting a training process with a nonexistent Unity build.
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

            long totalStartTime = System.currentTimeMillis(); //to measure the total time taken for all experiments

            File sourceFile = new File(
                MLAgentLauncher.class.getProtectionDomain().getCodeSource().getLocation().toURI()
            );

            File randomizerScript = new File(sourceFile.getParentFile(), "randomizer/HyperparameterRandomizer.py");

            System.out.println("Randomizer found: " + randomizerScript.exists());
            System.out.println("Randomizer path: " + randomizerScript.getAbsolutePath());

            for(int i = 1; i <= numberOfExperiments; i++) {
                String runId = "Experiment_" + timestamp + "_" + i;

                String outputConfigPath = "output_" + runId + ".yaml";

                ProcessBuilder randomizer =
                    new ProcessBuilder(
                        "python",
                        randomizerScript.getAbsolutePath(),
                        configPath,
                        new File(randomizerScript.getParentFile(), outputConfigPath).getAbsolutePath()
                    );

                randomizer.inheritIO();
                Process randomizerProcess = randomizer.start();
                int randomizerExitCode = randomizerProcess.waitFor();

                if (randomizerExitCode != 0) {
                    System.out.println("Randomizer failed");
                    break;
                }

                ProcessBuilder processBuilder =
                    new ProcessBuilder(
                        "mlagents-learn",
                        new File(randomizerScript.getParentFile(), outputConfigPath).getAbsolutePath(),
                        "--run-id=" + runId,
                        "--env=" + environmentPath // Specify the Unity build path
                    );
                // Start the process
                processBuilder.inheritIO();

                long startTime = System.currentTimeMillis(); //to measure the time taken for each experiment
                Process process = processBuilder.start();

                System.out.println("Is it running? " + process.isAlive());

                int exitCode = process.waitFor();

                long endTime = System.currentTimeMillis(); //to measure the time taken for each experiment

                long duration = (endTime - startTime) / 1000; //to measure the time taken for each experiment

                System.out.println("Experiment " + i + " process ended.");
                System.out.println("Exit code: " + exitCode);
                System.out.println("Duration: " + duration + " seconds");

                //training_log.txt will contain the run ID, configuration path, exit code, and duration for each experiment
                String logEntry =
                    "Run ID: " + runId + "\n" +
                    "Configuration: " + new File(randomizerScript.getParentFile(), outputConfigPath).getAbsolutePath() + "\n" +
                    "Environment: " + environmentPath + "\n" +
                    "Exit code: " + exitCode + "\n" +
                    "Duration: " + duration + " seconds\n" +
                    "------------------------------\n";

                try (BufferedWriter writer = new BufferedWriter(new FileWriter("training_log.txt", true))) { //true means append mode. Instead of overwriting the file every time, Java adds the new information at the end.
                    writer.write(logEntry);
                }

                if (exitCode != 0) {
                    failedExperiments++;
                    System.out.println("Experiment " + i + " failed!");
                    break;
                } else {
                    successfulExperiments++;
                }
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
}
