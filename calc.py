from mcp.server.mcpserver import MCPServer # type: ignore
mcp = MCPServer("Calculator")

history = []
@mcp.tool()
def add(a:float, b:float) -> float:
    "Add two numbers"
    history.append({
        "operation": "add",
        "operands": [a, b],
        "result": a + b
    })
    return a + b

@mcp.tool()
def subtract(a:float, b:float) -> float:
    "Subtract the second number from the first one"
    history.append({
            "operation": "subtract",
            "operands": [a, b],
            "result": a - b
        })
    return a - b

@mcp.tool()
def multiply(a:float, b:float) -> float:
    "Multiplying two Numbers"
    history.append({
            "operation": "multiply",
            "operands": [a, b],
            "result": a * b
        })
    return a * b

@mcp.tool()
def divide(a:float, b:float) -> float:
    "Dividing the first number by the second"
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    history.append({
            "operation": "divide",
            "operands": [a, b],
            "result": a / b
        })
    return a / b

@mcp.tool()
def remainder(a:float, b:float) -> float:
    "the remainder after dividing a by b."
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    history.append({
            "operation": "remainder",
            "operands": [a, b],
            "result": a % b
        })
    return a % b

@mcp.tool()
def power(a:float, b:float) -> float:
    "Raise a to the power of b"
    history.append({
            "operation": "power",
            "operands": [a, b],
            "result": a ** b
        })
    return a ** b

@mcp.resource("calculator://history")
def get_history() -> str:
    "Get the history of calculations performed during this session."
    if not history:
        return "No calculations performed yet."
    return "\n".join(
        f"{item['operands'][0]} {item['operation']} {item['operands'][1]} = {item['result']}"
        for item in history
    )

@mcp.prompt()
def get_discount(price: float, discount_percent: float, delivery_charge: float) -> str:
    "Guide an assistant to calculate the final price after applying a discount and adding delivery charges."
    return f"""
    Calculate the final price for this purchase:
    Price: {price}
    Discount: {discount_percent}%
    Delivery Charges: {delivery_charge}

    Follow these steps to get final price:
    1. Use the calculator tools to calculate the discount amount.
    2. Calculate the discount amount.
    3. Subtract the discount amount from original price to get the discounted price.
    4. Add the delivery charges to the discounted price to get the final price.
    5. Explain each calculation clearly.
    6. Show the final price.

    Use only available calculator tools for calculations.
"""

if __name__ == "__main__":
    mcp.run(transport="stdio")