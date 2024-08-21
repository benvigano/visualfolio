import random


def generate_realistic_user():
    first_names = ['john', 'jane', 'alice', 'bob', 'matt', 'emma', 'oliver', 'sophia', 'liam', 'mia']
    last_names = ['smith', 'brown', 'jones', 'garcia', 'miller', 'davis', 'cheng']
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    username = f"{first_name}.{last_name}@example.com"
    name = first_name.capitalize() + " " + last_name.capitalize()
    
    return username, name
