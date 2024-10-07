from jinja2 import Environment, FileSystemLoader
import argparse
import os
# 10-1-24 Mike Kuriger 

# Set up argument parsing
parser = argparse.ArgumentParser(description='Generate OVF environment file.')
parser.add_argument('--vm', required=True, help='VM name')
parser.add_argument('--date', required=True, help='Build date')
parser.add_argument('--env', required=True, help='Environment')
parser.add_argument('--builtby', required=True, help='Built by')
parser.add_argument('--ticket', required=True, help='Jira ticket')
parser.add_argument('--appname', required=True, help='App name')
parser.add_argument('--owner', required=True, help='App owner')

args = parser.parse_args()

# Set up Jinja2 environment and load the template file
env = Environment(loader=FileSystemLoader(searchpath="./templates"))
usertemplate = env.get_template("user_data_template.j2")
metatemplate = env.get_template("meta_data_template.j2")

# Values to populate in the template from arguments
template_data = {
    'vm': args.vm,
    'date': args.date,
    'env': args.env,
    'builtby': args.builtby,
    'ticket': args.ticket,
    'appname': args.appname,
    'owner': args.owner
}

# Render the user-data and meta-data
user_data = usertemplate.render(template_data)
meta_data = metatemplate.render(template_data)

# Directory to save the file
output_dir = f'cloud-init-images/{args.vm}'

# Create the directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Write user-data
output_file = f'{output_dir}/user-data'
with open(output_file, 'w') as f:
    f.write(user_data)

# Write meta-data
output_file = f'{output_dir}/meta-data'
with open(output_file, 'w') as f:
    f.write(meta_data)

