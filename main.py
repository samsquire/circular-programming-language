import re
import pprint

program = """
program {
    available = {};
    assigned = {};
    main {
      program = programs {
         current_available = program.available {
              available += (current_available, 1);
              assigned - current_available;
          }
          item = program.requests {
              available (=) item {
                  program.answers += item;
                  available - item;
                  assigned + (item, 1);
              }
          }
      }
    }
  }

program {
    requests = [];
    requests += (add, 1);
    main {
      item = answers {
          new_requests = [(add, 1)];
          available += (item, 1);
          new_request = new_requests {
              requests += new_request;
          }
          
      }
    }
    answers -= answers;
}
"""

class ParserError(BaseException):
  def __init__(self, message):
    super(ParserError, self).__init__(message)

class Parser:
  def __init__(self, data):
    self.data = data
    self.pos = 0
    self.end = False
    self.parsed = []
    self.last_char = ""
    self.depth = [0, 0, 0]
    self.BRACKETS = 0
    self.CURLIES = 1
    self.SQUARES = 2
    self.type = "token"
  def char(self):
    token = self.data[self.pos]
    if self.pos == len(self.data):
      self.end = True
    self.pos = self.pos + 1
    
    return token
    
  def token(self):
    self.type = "token"
    while self.end == False and (self.last_char == " " or self.last_char == "\n" or self.last_char == ""):
      self.last_char = self.char()
      # print("skipping whitespace")

    if self.last_char == "=":
      self.last_char = self.char()
      return "equals"
    
    if self.last_char == ",":
      self.last_char = self.char()
      return "comma"

    if self.last_char == "+":
      self.last_char = self.char()
      return "plus"

    if self.last_char == ";":
      self.last_char = self.char()
      return "semicolon"
    
    if self.last_char == "-":
      self.last_char = self.char()
      return "minus"

    if self.last_char == ">":
      self.last_char = self.char()
      return "arrow"

    if self.last_char == "(":
      self.last_char = self.char()
      self.depth[self.BRACKETS] = self.depth[self.BRACKETS] + 1 
      return "openbracket"

    if self.last_char == ")":
      self.last_char = self.char()
      self.depth[self.BRACKETS] = self.depth[self.BRACKETS] - 1 
      return "closebracket"
    
    if self.last_char == "{":
      self.last_char = self.char()
      self.depth[self.CURLIES] = self.depth[self.CURLIES] + 1 
      return "opencurly"

    if self.last_char == "}":
      self.last_char = self.char()
      self.depth[self.CURLIES] = self.depth[self.CURLIES] - 1 
      return "closecurly"
    
    if self.last_char == "[":
      self.last_char = self.char()
      self.depth[self.SQUARES] = self.depth[self.SQUARES] + 1 
      return "opensquare"
      
    if self.last_char == ":":
      self.last_char = self.char()
      return "separator"
    
    if self.last_char == "]":
      self.last_char = self.char()
      self.depth[self.SQUARES] = self.depth[self.SQUARES] - 1 
      return "closesquare"
    if self.last_char == "*":
      self.last_char = self.char()
      return "multiply"

    match = re.match("[a-zA-Z\._]", self.last_char)
    if match:
      identifier = ""
      while re.match("[a-zA-Z\._]", self.last_char):
        identifier = identifier + self.last_char
        self.last_char = self.char()

      self.type = "identifier"
      return identifier

    match = re.match("[0-9]", self.last_char)
    if match:
      identifier = ""
      while re.match("[0-9]", self.last_char):
        identifier = identifier + self.last_char
        self.last_char = self.char()

      self.type = "number"
      return identifier
  
  def parse(self):
    start = self.token()
    print(start)
    if start == "program":
      self.parse_program()
    
    return self.parsed

  def parsevalue(self):
    token = self.token()
    print(self.last_char)
    type = "token"
    value = None
    if token == "openbracket":
      type = "hashset"
      key = self.token()
      comma = self.token()
      if comma != "comma":
        raise ParserError("Expected comma after hash key")
      value = self.token()
      print("key is ", key)
      print("value is ", value)
      value = (key, value)
    if token == "opencurly":
      type = "hash"
      value = {}
    elif token == "opensquare":
      type = "list"
      value = []
    elif self.type == "identifier":
      type = "loop"
      value = token
    print("parsevalue", token)
    return (type, value)
    
  
  def parse_declaration(self, token):
    setto = token
    equals = self.token()
    operator = "equals"
    if equals == "plus":
      operator = "plusequals"
      equals = self.token()
    elif equals == "minus":
      operator = "remove"
      removal = self.token()
      print("removing")
    elif equals == "openbracket":
      self.token()
      self.token()
      operator = "inside"
    elif equals == "equals":
      operator = "equals"
    result = self.parsevalue()
    print("found set", setto)
    print("found operator", operator)
    print("found set result", result)
    return {'set': setto,
           'operator': operator,
           'result': result}
    
  
  def parse_programstatement(self, token, expected_depth, statements):
    
    # print(token)
    if not token:
      return None
    looking = True
    nest = False
    declaration = {}
    if token == "main":
      opencurly = self.token()
      nest = True
      if opencurly != "opencurly":
        raise ParserError("Expected curly after main statement")
        
    
    while token != "closecurly":
      print("looking")
      if self.type == "identifier":
        declaration = self.parse_declaration(token)
        semi = self.token()
        if semi == "semicolon":
          # was a statement
          type = "declaration"
        if semi == "opencurly":
          type = "loop"
      expected_depth2 = list(self.depth)
      token = self.token()
      if token == "closecurly":
        looking = False
        return None, statements

      print(declaration)
      if "result" in declaration:
        if declaration["result"][0] == "loop":
          nest = True
        if declaration["result"][0] == "inside":
          nest = True
     
      
      print("after statement token", token)

      use_statements = statements
      if nest:
        use_statements = []
      success, result = self.parse_programstatement(token, expected_depth2, use_statements)
      if nest:
        statements.append({'declaration': declaration, 'statements': use_statements})
      else:
        statements.append({'declaration': declaration})
      if not success:
        looking = False
        return (None, statements)
    return True, statements
          
            
    
  
  def parse_program(self):
    expected_depth = list(self.depth)
    print(expected_depth)
    token = self.token()
    if token != "opencurly":
      raise ParserError("Expected program to start")
    token = self.token()
    statements = []
    while self.depth != expected_depth and token != None:
      success, returned = self.parse_programstatement(token, expected_depth, statements)
      
      token = self.token()
      print("looking for end")
    pprint.pprint(statements)
    import json
    print(json.dumps(statements))
      

parsed = Parser(program).parse()
print(parsed)