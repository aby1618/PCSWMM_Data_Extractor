from swmm_api import read_out_file, SwmmOutput

# Read the .OUT file
out = SwmmOutput('sample1950.out')

# Extract the inflow data for the junction 'Hadati_13'
inflow_series = out.get_part('node', 'Hadati_13', 'total_inflow')

# Find the maximum total inflow
max_inflow = inflow_series.max()

print(f"The maximum total inflow for the junction 'Hadati_13' is {max_inflow}.")
