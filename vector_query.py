def get_semantically_close_text(client, text=None, embedding=None):
    query = (
       client.query
      .get("ServicePublic", ["text", "url", "subdomain", "title"])
    )

    if embedding:
        nearVector = {"vector": embedding}
        query = query.with_near_vector(nearVector)
    elif text:
       query = query.with_near_text({"concepts": [text]})
    else:
      raise ValueError('please provide ethier text or embedding')

    query = (
        query
        .with_limit(10)
        .with_additional(['certainty'])
    )

    response = query.do()

    if 'errors' in response["data"]["Get"].keys() and response["data"]["Get"]['errors'] is not None:
       raise RuntimeError('There is some error in weaviate for this query')

    return response
