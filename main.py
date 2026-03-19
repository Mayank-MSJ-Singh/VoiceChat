from llama_cpp import Llama

# 1. Load the model
print("Loading model... (this might take a few seconds)")
llm = Llama(
    model_path="Qwen2.5-Omni-7B-Q4_K_M.gguf", # <-- CHANGE THIS PATH
    n_ctx=4096,       # Context window
    n_gpu_layers=-1,  # -1 for full GPU offloading, 0 for CPU
    verbose=False     # Hides the underlying C++ engine logs for a cleaner terminal
)

# 2. Initialize conversation history
messages = [
    {"role": "system", "content": "You are a highly intelligent, concise, and helpful assistant."}
]

print("\nModel loaded! Let's chat. (Type 'exit' or 'quit' to stop)")
print("-" * 50)

# 3. The Chat Loop
while True:
    # Get your input
    user_input = input("\nYou: ")
    
    # Check if you want to leave
    if user_input.lower() in ['quit', 'exit']:
        print("Goodbye!")
        break
        
    # Add your new message to the conversation history
    messages.append({"role": "user", "content": user_input})
    
    print("Qwen: ", end="", flush=True)
    
    # Generate the response with stream=True for real-time output
    stream = llm.create_chat_completion(
        messages=messages,
        max_tokens=512,
        temperature=0.7,
        stream=True
    )
    
    # Print the response word-by-word and capture it
    full_response = ""
    for chunk in stream:
        delta = chunk['choices'][0]['delta']
        if 'content' in delta:
            text = delta['content']
            print(text, end="", flush=True)
            full_response += text
            
    print() # Move to a new line after the AI finishes typing
    
    # Add the AI's final response back into the history so it remembers the context
    messages.append({"role": "assistant", "content": full_response})