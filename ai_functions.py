from openai import OpenAI
import os

from dotenv import load_dotenv

load_dotenv()

def direct_llm_response():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.responses.create(
        model="gpt-4o-mini",
        input="Write a one-sentense bedtime story for a child about a brave little unicorn."
    )
    print(response.output_text)

# Chat completion api usage
def chat_completion_api():
    system_prompt = "You are a Sales Executve, who is supposed to sell AI courses." \
        " You are very friendly and polite in your responses." \
        "We have a new course on 'Mastering AI with Python' that covers everything from basics to advanced topics. " \
        "The course is designed for beginers and experienced developers alike." \
        "The price of the course is $199, but we are offering a 20% discount for early sign-ups. " \
        "The course includes hands-on projects, real-world examples, and lifetime access to the materials." \
        "It is being offered by IIT Patna, a premier institute known for quality education." \
        "The faculty of IIT Patna will take classes on Sunday 10am to 1pm IST. " \
        "The course duration is 3 months with a total of 36 hours of live online sessions." \
        " At the end of the course, students will receive a certificate of completion from IIT Patna." \
        " If you don't have any relevant information, politely say that you don't have the answer instead of making up something." \
        "Don't give any wrong information."
        
    while True:
        user_query = input("User: ")
        if user_query.lower() in ['exit', 'quit']:
            break


        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        #print(completion)
        content = completion.choices[0].message.content
        print("\nAI response:", content)
        
if __name__ == "__main__":
    #direct_llm_response()
    chat_completion_api()