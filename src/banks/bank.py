from dataclasses import dataclass 

class Parser:
    pass

class Normalizer:
    pass

@dataclass
class Bank:
    parser: Parser
    normalizer: Normalizer
