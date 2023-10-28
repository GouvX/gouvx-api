from vector_query import get_semantically_close_text
import openai

def build_prompt(client, question, query_results):
  text = f"""Vous êtes GouvX, un assitant virtuel bienveillant et serviable.
  
  Répondez précisément et clairement à la question en fin de document.
  
  La réponse se conforme aux règles suivantes:
  - NE DOIT PAS inclure de lien.
  - DOIT respecter convention de nommage: "Selon service-public.fr [...]"

  """

  if query_results:
    for i, paragraph in enumerate(query_results, start=1):
      title = result["title"]
      url = result["url"]
      
      text += f"""
      Document [{i}]: {title}
      {paragraph}

      """

  text += f"Question: {question}"

  return text


def query_llm(prompt, history=None):
  messages = []
  
  if history:
    messages.extend(history)

  messages.append({
      "role": "user",
      "content": prompt
  })

  for chunk in openai.ChatCompletion.create(
      model="gpt-3.5-turbo-16k",
      messages=messages,
      stream=True,
  ):
      content = chunk["choices"][0].get("delta", {}).get("content")
      if content is not None:
          yield(content)


def ask_gouvx(question, client, model=None, n_results=1, history=None):
  if not history:
    response = openai.Embedding.create(
        input=question,
        model="text-embedding-ada-002"
    )
    custom_vector = response['data'][0]['embedding']
    
    response = get_semantically_close_text(client, embedding=custom_vector)

    if response and response["data"]["Get"]["ServicePublic"] is not None:
      query_results = response["data"]["Get"]["ServicePublic"][:n_results]
    else:
      raise ValueError('The weaviate query returned no response')

    prompt = build_prompt(client, question, query_results)
  else:
    query_results = ""
    prompt = question

  chatgpt_generator = query_llm(prompt, history)

  return prompt, query_results, chatgpt_generator
