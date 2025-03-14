from pyomo.environ import ConcreteModel, Var, Objective, Constraint, NonNegativeReals, minimize, SolverFactory
import matplotlib.pyplot as plt

# Data / Parameters
load = [99,93, 88, 87, 87, 88, 109, 127, 140, 142, 142, 140, 140, 140, 137, 139, 146, 148, 148, 142, 134, 123, 108, 93]
lf_pv = [0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 9.80E-04, 2.47E-02, 9.51E-02, 1.50E-01, 2.29E-01, 2.98E-01, 3.52E-01, 4.15E-01, 4.58E-01, 3.73E-01, 2.60E-01, 2.19E-01, 1.99E-01, 8.80E-02, 7.03E-02, 3.90E-02, 9.92E-03, 1.39E-06, 0.00E+00, 0.00E+00]
timestep = len(load)
c_pv = 2500
c_batt = 1000
eff_batt_in = 0.95
eff_batt_out = 0.95
chargetime = 4  # hours to charge fully the battery

# Model
model = ConcreteModel()

# Define model variables
model.SOC_max = Var(within=NonNegativeReals)
model.P_pv = Var(within=NonNegativeReals)

model.SOC = Var(range(1, timestep+1), within=NonNegativeReals)
model.P_batt_in = Var(range(1, timestep+1), within=NonNegativeReals)
model.P_batt_out = Var(range(1, timestep+1), within=NonNegativeReals)
model.E_pv = Var(range(1, timestep+1), within=NonNegativeReals)

# Define the constraints

def balance(model,t):
    return model.E_pv[t] - model.P_batt_in[t]/eff_batt_in == load[t-1] - model.P_batt_out[t]*eff_batt_out
model.balance = Constraint(range(1, timestep+1), rule=balance)

def max_charge(model,t):
    return model.P_batt_in[t]/eff_batt_in <= model.SOC_max/chargetime
model.max_charge = Constraint(range(1, timestep+1), rule=max_charge)

def max_discharge(model,t):
    return model.P_batt_out[t]*eff_batt_out <= model.SOC_max/chargetime
model.max_discharge = Constraint(range(1, timestep+1), rule=max_discharge)

def production(model,t):
    return model.E_pv[t] <= model.P_pv*lf_pv[t-1]
model.production = Constraint(range(1, timestep+1), rule=production)

def state_of_charge(model,t):
    if t == 1:
        return model.SOC[t] == model.SOC[24]
    else:
        return model.SOC[t] == model.SOC[t-1] + model.P_batt_in[t] - model.P_batt_out[t]
model.state_of_charge = Constraint(range(1, timestep+1), rule=state_of_charge)

def max_soc(model,t):
    return model.SOC[t] <= model.SOC_max
model.max_soc = Constraint(range(1, timestep+1), rule=max_soc)

# Define the objective functions

def cost(model):
    return c_pv*model.P_pv + c_batt*model.SOC_max
model.obj = Objective(rule=cost, sense=minimize)


# Specify the path towards your solver (gurobi) file
solver = SolverFactory('gurobi')
solver.solve(model)

# Results - Print the optimal PV size and optimal battery capacity
print('Optimal PV size: ', model.P_pv())
print('Optimal battery capacity: ', model.SOC_max())


# Plotting - Generate a graph showing the evolution of (i) the load, 
# (ii) the PV production and, (iii) the soc of the battery

# Extract results for plotting
load_values = load
pv_production = [model.E_pv[t]() for t in range(1, timestep+1)]
soc_values = [model.SOC[t]() for t in range(1, timestep+1)]

# Plotting
plt.figure(figsize=(10, 6))

plt.plot(range(1, timestep+1), load_values, label='Load', marker='o')
plt.plot(range(1, timestep+1), pv_production, label='PV Production', marker='x')
plt.plot(range(1, timestep+1), soc_values, label='SOC of Battery', marker='s')

plt.xlabel('Time (hours)')
plt.ylabel('Power (kW) / State of Charge (kWh)')
plt.title('Load, PV Production, and SOC of Battery Over Time')
plt.legend()
plt.grid(True)
plt.show()
