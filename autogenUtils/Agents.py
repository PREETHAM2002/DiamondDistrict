import autogen
import datetime
from Utils.Constants import Constants
from autogenUtils.Decorators import simple_decorator_with_args


class Agents:
    def __init__(self,user_proxy_args,assistant_proxy_args) -> None:
        user_proxy_args['is_termination_msg']=lambda x: x.get("content","") and x.get("content")!="" and (x.get("content","").rstrip().endswith("TERMINATE"))
        assistant_proxy_args['is_termination_msg']=lambda x: x.get("content","") and x.get("content")!="" and (x.get("content","").rstrip().endswith("TERMINATE"))
        assistant_proxy_args['llm_config']['config_list']=Constants.CONFIG_LIST
        self.userProxy=autogen.UserProxyAgent(**user_proxy_args)
        self.assistantProxy=autogen.AssistantAgent(**assistant_proxy_args)
        
    def agentChat(self,tools,question,accumulator):
        for i in tools:
            i=simple_decorator_with_args(accumulator=accumulator)(i)
            autogen.agentchat.register_function(
                i,
                caller=self.assistantProxy,
                executor=self.userProxy,
                name=i.__name__,
                description=i.__doc__
            )
        response=self.userProxy.initiate_chat(recipient=self.assistantProxy,message=question,clear_history=False,summary_method="last_msg",max_turns=14)
        print(response)
        return response
    
    
    