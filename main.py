import json
import pathlib
import preparer
import os

from datetime import datetime
from sequential import runner_seq


def launch():

    # Load config
    workdir = str(pathlib.Path(__file__).parent.absolute())
    config_file = open(str(workdir) + "/config.json", 'r')
    config = json.loads(config_file.read())

    # Create output folder
    timestamp = timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    experiment_path = workdir + "/outputs/" + config["experiment"] + "-" + timestamp
    os.mkdir(experiment_path)

    # Create summary file
    summary_file = open(experiment_path + "/summary.txt", "w+")
    summary_file.write("Experiment: " + config["experiment"] + "\n")
    summary_file.write("Lipizzaner: " + config["lipizzaner_path"] + "\n")
    summary_file.write("Grid size: " + str(config["grid_size"]) + "\n")
    summary_file.write("Executions: " + str(config["n_executions"]) + "\n")

    if config["experiment"] == "sequential":

        # Prepare directories and experiment instances
        experiment_instances = preparer.prepare_seq(workdir, experiment_path, config)

        summary_file.write("Instances: " + str(len(experiment_instances)) + "\n\n")

        # Run experiment
        experiment_results = runner_seq.run(config, experiment_instances)

        # Collect results
        result_lines = []
        result_values = []
        for result in experiment_results:
            result_line = "Config {} - Execution {}: {} ({})\n".format(result["config"],
                                                                       result["exec"],
                                                                       result["fid"],
                                                                       result["wall_clock"])
            result_lines.append(result_line)
            result_values.append("{} {} {} {}\n".format(result["config"],
                                                        result["exec"],
                                                        result["fid"],
                                                        result["wall_clock"]))

        summary_file.writelines(result_lines)
        summary_file.write("\n")
        summary_file.writelines(result_values)

    # TODO: Change logic based on irace and mpi runners
    else:
        summary_file.close()
        raise Exception("Experiment name not found")

    summary_file.close()


if __name__ == "__main__":
    launch()

