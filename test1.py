def get_variables_from_equation(equation):
    """
    Extracts all unique variables from the given equation and returns them in alphabetical order.

    Args:
        equation (str): The equation from which variables need to be extracted.

    Returns:
        list: A sorted list of unique variables found in the equation.
    """
    # Extract all unique variables from the equation
    variables = set(char for char in equation if char.isalpha())
    # Sort the variables in alphabetical order
    sorted_variables = sorted(variables)
    return sorted_variables

def convert_logic_equation(bits, equation):
    """
    Converts a logic equation into a boolean result based on the given bits.

    Args:
        bits (list): A list of bits representing the values of variables in the equation.
        equation (str): The logic equation to be evaluated.

    Returns:
        bool: The boolean result of the evaluated logic equation.

    Examples:
        >>> convert_logic_equation([True, False, True, True, False], '/a|(b.c)|d')
        True
    """
    lsVariables = get_variables_from_equation(equation)
    # print(lsVariables)

    # Replace variable names with corresponding bits
    for chr_ in lsVariables:
        if chr_.isalpha() and chr_.lower() in 'abcdefghijklmnopqrstuvwxyz':
            equation = equation.replace(chr_, str(int(bits[ord(chr_) - 97])))
    # print(equation)

    # Replace the logical operators with Python syntax
    equation = equation.replace('.', ' and ')
    equation = equation.replace('|', ' or ')
    equation = equation.replace('/', ' not ')
    # Remove all extra spaces from the equation
    equation = ' '.join(equation.split())
    # print(equation)

    # Evaluate the expression using eval
    result = bool(eval(equation))
    return result

import random
# Example usage
#       a       b      c    d       e
bits = []
count = 0
while count < 10:
    bits.append(bool(random.randint(0, 1)))
    count += 1
print(bits)
eqn1 = '((a./b.c)|d).e./g./h'
eqn2 = '/a|(b.c)|d.(g|f.i)'

result1 = convert_logic_equation(bits, eqn1)
result2 = convert_logic_equation(bits, eqn2)

print("Result of eqn1:", result1)
print("Result of eqn2:", result2)

count = 0
k = []
count_ = 0

while count_ < 5:
    temp = random.randint(10, 20)
    while count<temp:
        k.append(count)
        count += 1
    count_ += 1
    count = 0
    print(k)
    k.clear()