### Prompt Instruction:
- You are always free to create your own customised prompts.
- However, we provide the following instructions to avoid pitfalls that may happen.

#### Text Preprocessing Prompt:
- Keep it simple. More instructions may result in a variety of outputs. For example, this prompt may generate the output "upper leg skin -> upper leg skin -> upperlegskin"
```
Normalise the following name: {entity_name}
Use white space to split the compound words.
Change uppercase to lowercase.
Output the normalised name only.
```
- We suggest suing the following prompt for simple prompt (but it may still have some error as LLM is originally designed for chat):
```
Change the following name a lowercase and space-separated format: {entity_name}
```

#### Retrieval & Matching Prompt:
- Do not use ":" for your input. LLMs may consider this symbol as a separator and return only the name. For example, "source:User" may randomly return "User".
- Be careful when using "." along with your input. For example, LLMs will treat "{entity}." (with a full stop) as the input from the following prompt:
```
Retrieve syntactic information about {entity}.
```
- Do specify your input in multiple lines. For example. LLMs may randomly return only the name in the lexical retriever and graphical retriever from the following prompt:
```
Retrieve information about {entity}
Use syntactic retriever, lexical retriever, and graphical retriever.
```
- We suggest using the following prompt for complex prompt:
```
Retrieve syntactic information about {entity}
Retrieve lexical information about {entity}
Retrieve graphical information about {entity}
```

#### Tool Use Prompt:
- Function Declaration:
  - Single function name and argument name.
  - Camel case is fine, but snake case is wrong.
  - Use verb for function description.
  - Do not use f-strings for build-in prompt.
  - No special characters ":" or ".".
  - No keywords "compare" or "validate" or "verify" for function description. 
- Function Prompt:
  - Main content from: https://python.langchain.com/v0.1/docs/use_cases/tool_use/prompting/
  - Add one sentence from: https://medium.com/pythoneers/power-up-ollama-chatbots-with-tools-113ed8229a7a
  - We apply some slight changes to fit different LLM models.
- It is possible to add tool error handling: https://python.langchain.com/v0.1/docs/use_cases/tool_use/tool_error_handling/
- Please consider use the following testbed to test your retrieve prompt:

| Track      | Entity                                           | Description                                  |
|------------|--------------------------------------------------|----------------------------------------------|
| Conference | entity_list = ["http://cmt#Meta-Reviewer"]       | test extra information                       |
| Conference | entity_list = ["http://cmt#acceptedBy"]          | test return the key "tool" instead of "name" |
| Conference | entity_list = ["http://conference#Organization"] | test null value                              |
| Anatomy    | entity_list = ["http://mouse.owl#MA_0000006"]    | test head/neck                               |
| Anatomy    | entity_list = ["http://mouse.owl#MA_0001580"]    | test meckel's cartilage                      |
| Anatomy    | entity_list = ["http://human.owl#NCI_C32188"]    | test use symbol ":"                          |

- Please consider use the following testbed to test your matching prompt:

| Track      | Entity                                    | Description                                                     |
|------------|-------------------------------------------|-----------------------------------------------------------------|
| Conference | e1_list = ["http://cmt#Bid"]              | test all null value                                             |
| Conference | e1_list = ["http://cmt#Meta-Reviewer"]    | test matching refine                                            |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0000096"] | test one null value                                             |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0001017"] | test all null value                                             |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0000241"] | test use symbol "." to end sentence                             |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0000052"] | test use symbol "" or '' for name                               |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0000013"] | test hemolymphoid system and Hematopoietic_and_Lymphatic_System |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0000006"] | test head/neck and Head_and_Neck, phi cannot find correct input |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0000383"] | test keyword should be "refine". not "validate" or "verify"     |


#### Refine Prompt:
- We use a strong refine (e.g. "equivalent" and "identical") to identify the equivalence relationship.
- In some case, weak refine (e.g. "interchangeable") is better. 
- Please consider use the following testbed to test your own prompt:

| Track      | Entity1                                  | Entity2                                      |
|------------|------------------------------------------|----------------------------------------------|
| Conference | e1_list = ["http://cmt#SubjectArea"]     | e2_list = ["http://cmt#Topic"]               |
| Conference | e1_list = ["http://cmt#ConferenceChair"] | e2_list = ["http://cmt#Chair"]               |
| Conference | e1_list = ["http://cmt#Document"]        | e2_list = ["http://cmt#Conference_document"] |
