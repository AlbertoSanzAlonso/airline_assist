# imports

import openai
import os
import json
from dotenv import load_dotenv
import gradio as gr

# Initialization

load_dotenv() 

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exist and begins {openai_api_key[:8]}")
else:
    print("Open AI Key not configured")

MODEL = "gpt-4o-mini"
openai = openai.OpenAI(api_key=openai_api_key)

# System prompts

system_message = "You are a helpful assistant for an airline called FlightAI."
system_message += "Give brief and polite answers, no longer than one sentence."
system_message += "Always be precise; if you don’t know the answer, say so."
system_message += "If someone speaks to you in another language, respond in the same language."


# Function without Tools

# def chat(message, history):
#     messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]

#     stream = openai.chat.completions.create(model=MODEL, messages=messages, stream=True)
#     response = ""

#     for chunk in stream:
#         response += chunk.choices[0].delta.content or ""
#         yield response


# Tools for AI

ticket_prices = {"london": "799€", "paris": "899€", "tokyo": "1400€", "berlin": "499€"}

def get_ticket_price(destination_city):
    print(f"The tool get_ticket_price was requested for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

print(get_ticket_price("Berlin"))

# Providing tool to the LLM

price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a round-trip ticket to the destination city. Call it whenever you need to know the ticket price, for example, when a customer asks 'How much is a ticket to this city",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

# Tools list

tools = [{"type": "function", "function": price_function}]


# Call to the tool in the Function

def chat(message, history):
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)


    if response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message
        response, city = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        response = openai.chat.completions.create(model=MODEL, messages=messages)
    
    return response.choices[0].message.content

# Handle_tool_call function

def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    city = arguments.get("destination_city")
    price = get_ticket_price(city)
    response = {
        "role": "tool",
        "content": json.dumps({"destination_city": city, "price": price}),
        "tool_call_id": message.tool_calls[0].id
    }

    return response, city


# Launching Gradio

gr.ChatInterface(fn=chat, type="messages").launch(share=True)
