


class chatUtils:
    def createChatHistory(chatMessages,k=8):
        chatHistory=[]
        for i in range(0,len(chatMessages)):
            if "role" in i and i["role"]=="user":
                chatHistory.append({"role":"user","content":i["content"]})
            elif "role" in i and i["role"]=="assistant":
                chatHistory.append({"role":"assistant","content":i["content"]})
                
                
        if len(chatHistory)>k:
            chatHistory=chatHistory[-k:]
            
        chatHistory="\n".join([f"{i['role']}: {i['content']}" for i in chatHistory])
        return chatHistory
    
    
    def extract_thought_process(chatHistory):
        thoughts=[]
        for i in chatHistory:
            if "role" in i:
                if "tool_calls" in i:
                    if "content" in i and i["content"]!="":
                        del i['content']
                    if "id" in i['tool_calls'][0]:
                        i['tool_calls'][0].pop('id')
                        functionName=i['tool_calls'][0]['function']['name']
                        arguments=i['tool_calls'][0]['function']['arguments']
                        action_text=f"""Action Taken :{functionName}
                        Action Input :{arguments}"""
                        thoughts.append(action_text)
                        
                elif "tool_responses" in i:
                    if "content" in i:
                        if "TERMINATE" in i['content'] and i['content'].rstrip().endswith('TERMINATE'):
                            thoughts.append(i['content'].replace("TERMINATE",""))
                        
        return thoughts[:-1],thoughts[-1]
                            
                            