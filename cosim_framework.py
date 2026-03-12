
"""Co-simulation framework module. Contains Model and Manager classes for running the co-simulation."""
import matplotlib.pyplot as plt
import pandas as pd


class Model:
    """Wrapper class for modeling any physical process (e.g. power flow, heat production, etc.)."""

    def __init__(self, process_model):
        """Takes in the model of a physical process as a function or callable class."""
        if not callable(process_model):
            raise ValueError("The process must be a function or callable class.")
        self.process_model = process_model

    def calculate(self, *args) -> float:
        """Call the process function to perform calculations on an arbitrary number of inputs."""
        return self.process_model(*args)


class Manager:
    """The orchestrator manager for managing the data exchanged between the coupled models."""

    def __init__(self, models: list[Model], settings_configuration: dict):
        self.models = models
        self.electric_grid = models[0]
        self.heat_pump = models[1]
        self.room = models[2]
        self.controller = models[-1]
        self.settings_configuration = settings_configuration

    def run_simulation(self):
        """Run one simulation and return the results."""
        config = self.settings_configuration
        config_id = config['InitializationSettings']['config_id']
        start_time = config['InitializationSettings']['time']['start_time']
        end_time = config['InitializationSettings']['time']['end_time']
        delta_t = config['InitializationSettings']['time']['delta_t']

        grid_topology = pd.read_csv(config['InitializationSettings']['grid_topology'])

        passive_consumer_power_setpoints = pd.read_csv(
            config['InitializationSettings']['passive_consumers_power_setpoints'],
            index_col="snapshots",
            parse_dates=True,
        )

        print(passive_consumer_power_setpoints.shape)
        print(passive_consumer_power_setpoints.columns)

        hp_power_setpoint = config['InitializationSettings']['initial_conditions']['heat_pump']['power_set_point']
        room_temperature = config['InitializationSettings']['initial_conditions']['room']['temperature']

        times = []
        smart_consumer_power_setpoint_over_time = []
        smart_consumer_voltage_over_time = []
        heat_pump_heat_output_over_time = []
        temperature_over_time = []

        print("===============================================================")
        print(f"Starting simulation at time {start_time}, ending at {end_time}, with time step delta_t: {delta_t}\n")
        print(f"Initial heat pump power_setpoint [W]: {hp_power_setpoint}")
        print(f"Initial heat pump temperature [°C]: {room_temperature}\n")
        print("===============================================================")

        time_steps = int((end_time - start_time) / delta_t)

        for time_step in range(time_steps):
            time_clock = start_time + time_step * delta_t

            corresponding_time_in_dataframe = passive_consumer_power_setpoints.index[time_step]
            print(f"Time step {corresponding_time_in_dataframe} | Simulation time clock: {time_clock:.2f}")

            all_consumer_voltages = self.electric_grid.calculate(
                passive_consumer_power_setpoints,
                hp_power_setpoint,
                grid_topology,
                corresponding_time_in_dataframe,
            )

            smart_consumer_voltage = all_consumer_voltages["consumers"]["smart_consumer"]
            heat_production_from_hp = self.heat_pump.calculate(hp_power_setpoint)
            room_temperature = self.room.calculate(heat_production_from_hp)

            hp_power_setpoint = self.controller.calculate(
                hp_power_setpoint,
                smart_consumer_voltage,
                room_temperature
            )

            print("-----------------------------------------------------------")
            print(f"New power setpoint: {hp_power_setpoint}")
            print("===========================================================")

            times.append(time_clock)
            smart_consumer_power_setpoint_over_time.append(hp_power_setpoint)
            smart_consumer_voltage_over_time.append(smart_consumer_voltage)
            heat_pump_heat_output_over_time.append(heat_production_from_hp)
            temperature_over_time.append(room_temperature)

        return {
            "config_id": config_id,
            "times": times,
            "voltages": smart_consumer_voltage_over_time,
            "temperatures": temperature_over_time,
            "power_setpoints": smart_consumer_power_setpoint_over_time,
            "heat_productions": heat_pump_heat_output_over_time,
        }

    def plot_comparison_results(self, original_results, forecasted_results):
        """Plot original and forecasted simulation results together."""
        plt.style.use('ggplot')
        _, axs = plt.subplots(2, 2, figsize=(12, 8))

        plots = [
            (
                axs[0, 0],
                original_results["times"],
                original_results["voltages"],
                forecasted_results["times"],
                forecasted_results["voltages"],
                "Voltage Over Time",
                "Time [min]",
                "Voltage [V]",
            ),
            (
                axs[0, 1],
                original_results["times"],
                original_results["temperatures"],
                forecasted_results["times"],
                forecasted_results["temperatures"],
                "Temperature Over Time",
                "Time [min]",
                "Temperature [°C]",
            ),
            (
                axs[1, 0],
                original_results["times"],
                original_results["power_setpoints"],
                forecasted_results["times"],
                forecasted_results["power_setpoints"],
                "Heat Pump Power Setpoint Over Time",
                "Time [min]",
                "Power Setpoint [W]",
            ),
            (
                axs[1, 1],
                original_results["times"],
                original_results["heat_productions"],
                forecasted_results["times"],
                forecasted_results["heat_productions"],
                "Heat Production Over Time",
                "Time [min]",
                "Heat Production [W]",
            ),
        ]

        for ax, x1, y1, x2, y2, title, xlabel, ylabel in plots:
            ax.plot(x1, y1, label="Original", linewidth=2)
            ax.plot(x2, y2, label="Forecasted", linewidth=2, linestyle="--")
            ax.set_title(title, color='black')
            ax.set_xlabel(xlabel, color='black')
            ax.set_ylabel(ylabel, color='black')
            ax.tick_params(axis='x', colors='black')
            ax.tick_params(axis='y', colors='black')
            ax.legend()

        plt.tight_layout()
        plt.savefig("results_comparison.png")
        plt.show()