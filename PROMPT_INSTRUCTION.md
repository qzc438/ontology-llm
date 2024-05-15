### Prompt Instruction:
- You are always free to create your own customised prompts.
- However, we provide the following instructions to avoid pitfalls that may happen.

#### Simple Prompt:
- You are always recommended to use JSON to format the output, even though you only have one output value.
- Keep it simple. More instructions may result in a variety of outputs. For example, this prompt may generate the output "upper leg skin -> upper leg skin -> upperlegskin"
```
Normalise the following name: {entity_name}
Use white space to split the compound words.
Change uppercase to lowercase.
Output the normalised name only.
```
- We suggest suing the following prompt for simple prompt:
```
Normalise the following name: {entity_name}
Use a lowercase and space-separated format.
```

#### Complex Prompt:
- You are always recommended to use JSON to format the output.
- Do not use ":" for your input. LLMs may consider this symbol as a separator and return only the name. For example, "source:User" may randomly return "User".
- Be careful when using "." along with your input. For example, LLMs will treat "{entity}." (with a full stop) as the input from the following prompt:
```
Find syntactic retrieving about the entity: {entity}.
```
- Do specify your input in multiple lines. For example. LLMs may randomly return only the name in the lexical retriever and graphical retriever from the following prompt:
```
Retrieve information about the entity: {entity}
Use syntactic retriever, lexical retriever, and graphical retriever.
```
- We suggest suing the following prompt for complex prompt:
```
Find syntactic retrieving about the entity: {entity}
Find lexical retrieving about the entity: {entity}
Find graphical retrieving about the entity: {entity}
```