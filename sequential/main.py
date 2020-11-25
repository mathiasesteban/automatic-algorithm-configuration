import subprocess
import os
import pathlib
import json
import errno

from datetime import datetime


def sequential_training():

    # Params
    lipizzaner_path = "/home/mesteban/devel/git/lipizzaner-covidgan/src/main.py"
    n_executions = 5
    grid_size = 1
    workdir = pathlib.Path(__file__).parent.absolute()

    # Prepare target configurations list
    config_file = open("templates/config.json", 'r')
    config_json = json.loads(config_file.read())

    configs = []
    for network in config_json['networks']:
        for batch_size in config_json['batch_sizes']:
            for smote_size in config_json['smote_sizes']:
                for mutation_probability in config_json['mutations_probabilities']:
                    for adam_rate in config_json['adam_rates']:
                        new_config = {
                            'batch_size': batch_size,
                            'network': network,
                            'smote_size': smote_size,
                            'mutation_probability': mutation_probability,
                            'adam_rate': adam_rate,
                        }
                        configs.append(new_config)

    # Train Lipizzaner for each configuration N_EXECUTION times
    for target_config in configs:
        for i in range(n_executions):

            # Create output directory for experiment
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_path = str(workdir) + "/generated/" + timestamp

            try:
                os.mkdir(output_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

            # Create general configuration file
            general_config_template = open(str(workdir) + "/templates/general_config_template.yml", "rt")
            general_config = open(output_path + "/general.yml", "wt")

            if grid_size == 1:
                ports = "5000"
            else:
                max_port = 4999 + grid_size
                ports = "5000-" + str(max_port)

            for line in general_config_template:
                newline = line.replace('OUTPUT_DIR', output_path)
                newline = newline.replace('PORTS', ports)
                general_config.write(newline)

            general_config_template.close()
            general_config.close()

            # Create specific config file
            config_template = open(str(workdir) + "/templates/config_template.yml", "rt")
            config_path = output_path + "/config.yml"
            config = open(config_path, "wt")

            for line in config_template:

                newline = line.replace('DEFAULT_ADAM_LEARNING_RATE', str(target_config['adam_rate']))
                newline = newline.replace('MUTATION_PROBABILITY', str(target_config['mutation_probability']))
                newline = newline.replace('BATCH_SIZE', str(target_config['batch_size']))
                newline = newline.replace('SMOTE_AUGMENTATION_TIMES', str(target_config['smote_size']))
                newline = newline.replace('NETWORK_NAME', target_config['network'])
                config.write(newline)

            config_template.close()
            config.close()

            # Execute Lipizzaner
            clients_pool = []
            # Launch clients
            for j in range(grid_size):
                client_command = ["python", lipizzaner_path, "train", "--distributed", "--client"]
                lipizzaner_client = subprocess.Popen(client_command)
                clients_pool.append(lipizzaner_client)

            # Launch master
            master_command = ["python", lipizzaner_path, "train", "--distributed", "--master", "-f", config_path]

            lipizzaner_master = subprocess.run(master_command,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE,
                                               universal_newlines=True)

            master_stderr = open(output_path + "/master_stderr.log", "wt")
            master_stderr.write(lipizzaner_master.stderr)
            master_stderr.close()

            # Kill clients
            for client in clients_pool:
                client.kill()


if __name__ == "__main__":
    sequential_training()
