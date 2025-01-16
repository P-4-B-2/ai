# import torch
# import os
# import requests
# from dotenv import load_dotenv
# from groq import Groq

# from langchain.chains import ConversationChain, LLMChain
# from langchain_core.prompts import (
#     ChatPromptTemplate,
#     HumanMessagePromptTemplate,
#     MessagesPlaceholder,
# )

# from langchain_core.messages import SystemMessage
# from langchain.chains.conversation.memory import ConversationBufferWindowMemory
# from langchain_groq import ChatGroq
# from langchain.prompts import PromptTemplate

# load_dotenv()

# groq_chat = ChatGroq(
#             groq_api_key=os.environ["GROQ_API_KEY"], 
#             model_name="llama-3.3-70b-versatile"
#     )




# def generate_response(user_input):
#     # Retrieve relevant context from Qdrant
#     context = retrieve_relevant_context(user_input)
#     combined_context = "\n".join(context)

#     # Construct the prompt for the LLM
#     pre_prompt = f"""
#     You are a helpful assistant gathering feedback about the city for urban improvement purposes.
#     Here is some relevant context:
#     {combined_context}

#     Based on the following user input, provide a polite and engaging response, and ask questions about the city to gather feedback:
#     User Input: {user_input}
#     """

#     # Call Groq API
#     payload = {
#         "model": "gpt-3.5-turbo",
#         "messages": [
#             {"role": "system", "content": "You are an assistant for city feedback."},
#             {"role": "user", "content": pre_prompt}
#         ]
#     }
#     headers = {
#         "Authorization": f"Bearer {groq_api_key}",
#         "Content-Type": "application/json"
#     }

#     response = requests.post(os.getenv("GROQ_API_KEY"), json=payload, headers=headers)
#     return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")


# def response_generation_flow(user_input):
#     # Generate response
#     response = generate_response(user_input)

#     # Output response
#     print(f"User Input: {user_input}")
#     print(f"Generated Response: {response}")
#     return response


# if __name__ == "__main__":
#     user_input = "What do people think about the new green spaces in the city?"
#     response = response_generation_flow(user_input)
