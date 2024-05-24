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
  - Do not use f-strings for build-in prompt.
  - No special characters ":".
  - No keywords "compare" for function description.
  - Verb for function description.
- Function Prompt:
  - Main content from: https://python.langchain.com/v0.1/docs/use_cases/tool_use/prompting/
  - Add one sentence from: https://medium.com/pythoneers/power-up-ollama-chatbots-with-tools-113ed8229a7a
  - We apply some slight changes to fit different LLM models.
- It is possible to add tool error handling: https://python.langchain.com/v0.1/docs/use_cases/tool_use/tool_error_handling/

#### Validate Prompt:
- The equivalence relationship in OM is weak equivalence. Use "equivalent" and "identical" is too strong.
- We recommend use the prompt related to real-world scenario: 
```
Is A often used interchangeably with B?
```
- Please consider use the following testbed to test your own prompt:

| e1_list                                  | e2_list                                      |
|------------------------------------------|----------------------------------------------|
| e1_list = ["http://cmt#SubjectArea"]     | e2_list = ["http://cmt#Topic"]               |
| e1_list = ["http://cmt#ConferenceChair"] | e2_list = ["http://cmt#Chair"]               |
| e1_list = ["http://cmt#Document"]        | e2_list = ["http://cmt#Conference_document"] |
