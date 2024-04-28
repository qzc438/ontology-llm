### Prompt Instruction:
- You are always free to create your own customised prompts.
- However, we provide the following instructions to avoid pitfalls that may happen.

#### Simple Prompt:
- You are always recommended to use JSON to format the output, even though you only have one output value.
- Keep it simple. More instructions may result in a variety of outputs. For example, this prompt may generate the output "upper leg skin -> upper leg skin -> upperlegskin"
```
Normalise the following name: {entity_name}.
Use white space to split the compound words.
Change uppercase to lowercase.
Output the normalised name only.
```

#### Complex Prompt:
- You are always recommended to use JSON to format the output.
- Do not use ":" for your input. LLMs may consider this symbol as a separator and only return the name only. For example, "source:User" may randomly return as "User".
- Use "enclosed with a pair of double quotes" to indicate the content of your input. For example, LLMs will consider "{entity}." (with the full stop) as the input from the following prompt:
```
Retrieve the information about the entity: {entity}.
```
- Specify the type of your input. If your input is name, say "Format the name...". If your input is URI, say "Find the URI..."
- Specify your input in multiple lines. LLMs may randomly return names only in the lexical retriever and graphical retriever from the following prompt:
```
Retrieve the information about the URI enclosed with a pair of double quotes: {entity}.
Use syntactic retriever, lexical retriever, and graphical retriever.
{format_instructions}
```