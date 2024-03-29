import os
import re
from ..prompt_builder import SystemPromptBuilder
from ..query_llm import query_llm
from ..agents.abstract_agent import AbstractAgent
from ..agents.tool_caller import ToolCaller
from ..tools.vector_query import VectorQuery

class GouvX(AbstractAgent):
    def __init__(self):
        self.OPENAI_KEY = os.getenv("OPENAI_KEY")
        self.WEAVIATE_ENDPOINT = os.getenv('WEAVIATE_ENDPOINT')
        self.WEAVIATE_KEY = os.getenv('WEAVIATE_KEY')
        self.HUGGINGFACE_KEY = os.getenv('HUGGINGFACE_KEY')
        self.WEAVIATE_NRESULTS = int(os.getenv('WEAVIATE_NRESULTS', '1'))
        self.last_query_results = None

    def query(self, user_prompt, history=None):
        base_prompt = f"""Vous êtes GouvX, un assitant virtuel bienveillant et serviable permettant de naviguer les services du service public et répondre au question portant sur le droit civil, public ou privé.
Répondez précisément et clairement aux questions de l'utilisateur en respectant les règles suivantes:
- Ne JAMAIS inclure de lien
- Si une question ne porte pas sur les services du service public ou sur le droit civil, public ou privé, REFUSEZ DE REPONDRE et rappellez votre rôle
- En repondant à une question, respecter la convention de nommage: "Selon service-public.fr ..."
- Repondre en texte clair, sans balises ou marqueurs"""

        # call the tool caller agent to make a decision
        agent_answer = ToolCaller().query(user_prompt)
        pattern = r"need_tool: (\w+)\s*function_call: (.*)"
        match = re.match(pattern, agent_answer)
        
        formatted_response = ""
        if match:
            # Extract the matched groups
            need_tool = match.group(1)
            function_call = match.group(2)
            need_tool = need_tool.lower() == 'true'

            if need_tool:
                # query the vector database
                query_tool = VectorQuery(weaviate_key=self.WEAVIATE_KEY, weaviate_endpoint=self.WEAVIATE_ENDPOINT, huggingface_key=self.HUGGINGFACE_KEY, n_results=self.WEAVIATE_NRESULTS)
                formatted_response = query_tool.trigger(function_call)
                self.last_query_results = query_tool.last_query_results
        
        system_prompt = SystemPromptBuilder(base_prompt).build_system_prompt()
        system_prompt += formatted_response

        reply = query_llm(user_prompt=user_prompt,
                          system_prompt=system_prompt,
                          history=history,
                          model="gpt-3.5-turbo-16k")

        return reply
