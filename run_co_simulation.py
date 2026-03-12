"""Run the co-simulation."""
import argparse
import pickle
from functools import partial
from controller import controller_function
from cosim_framework import Manager, Model
from grid import electric_grid_function
from heat_pump import heat_pump_function
from load_configurations import load_configurations
from room import RoomFunction

# Define constants and parse command-line arguments
RESULT_FILE = "original_results.pkl"
parser = argparse.ArgumentParser()
parser.add_argument("--use-forecasted")
args = parser.parse_args()



configurations_folder_path = "./configurations"

controller_config, settings_configs = load_configurations(configurations_folder_path, use_forecasted=args.use_forecasted)

electric_grid_model = Model(electric_grid_function)
heat_pump_model = Model(heat_pump_function)
room_model = Model(RoomFunction(settings_configs["config 1"]))
controller_model = Model(partial(controller_function, controller_settings=controller_config))



models = [electric_grid_model, heat_pump_model, room_model, controller_model]
manager = Manager(models, settings_configs["config 1"])


results = manager.run_simulation()

# Save or compare results

if not args.use_forecasted:


    with open(RESULT_FILE, "wb") as f:
        pickle.dump(results, f)

    print("Now run:")
    print("python run_co_simulation.py --use-forecasted")

else:

    with open(RESULT_FILE, "rb") as f:
        original_results = pickle.load(f)

    manager.plot_comparison_results(original_results, results)