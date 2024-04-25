import langchain_core.output_parsers

output_parser = langchain_core.output_parsers.CommaSeparatedListOutputParser()

format_instructions = output_parser.get_format_instructions()

print(format_instructions)

output_parser = langchain_core.output_parsers.JsonOutputParser()

format_instructions = output_parser.get_format_instructions()

print(format_instructions)

