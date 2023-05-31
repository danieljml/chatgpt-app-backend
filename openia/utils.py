def get_content_from_successful_chat_response(response):
    return response['choices'][0]['message']['content']
