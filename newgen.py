import json

ifile = open('in/peroid_test.out', 'r')
ofile = open('in/peroid_test.c', 'w')
dfile = open('debug.txt', 'w+')

FUNC_PREFIX = '__func_'

# static class
class Util:
    # convert a pascal-styled type to a C-styled type
    @staticmethod
    def ConvertType(rawType):
        if rawType == 'INTEGER':
            return 'int'
        if rawType == 'BOOLEAN':
            return 'bool'
        if rawType == 'CHAR':
            return 'char'
        print(rawType, file=dfile, flush=True)

    @staticmethod
    def ConvertOperator(rawOp):
        if rawOp == '=':
            return '=='
        if rawOp == ':=':
            return '='
        if rawOp == 'Mod':
            return '%'
        return rawOp

    @staticmethod
    def ToIOForm(type):
        if (type == 'int'):
            return '%d'
        if (type == 'char'):
            return '%c'
        if (type == 'double'):
            return '%f'
        print(type, file=dfile, flush=True)


class Output:
    rawOutput = ''

    @staticmethod
    def AppendOutput(ostr):
        Output.rawOutput += ostr

    @staticmethod
    def FormatOutput():
        # print(Output.rawOutput.replace(';', ';\n').replace(') {', ') {\n'))
        temp = Output.rawOutput.replace(';', ';\n').replace(') {', ') {\n').replace('}', '}\n')\
            .replace('else {', 'else {\n').split('\n')

        tabCount = 0
        for line in temp:
            if len(line) == 0:
                continue
            line = line.strip()
            if(line == ';'):
                continue

            if(line[-1] == '}'):
                tabCount -= 1
            line = '\t' * tabCount + line
            if(line[-1] == '{'):
                tabCount += 1
            print(line, file=ofile, flush=True)


# base class
class Node:
    def __init__(self, tree):
        self.tree = tree
        self.child = []
        self.ret = None  # return value

    def Parse(self):
        pass

    def ParseChildByOrder(self):
        for node in self.child:
            node.Parse()


class ProgramStructNode(Node):
    def Parse(self):
        head = ProgramHeadNode(self.tree['program_head'])
        head.Parse()
        body = ProgramBodyNode(self.tree['program_body'], head.ret)
        body.Parse()


class ProgramHeadNode(Node):
    def Parse(self):
        ids = self.tree['idlist']['ids']
        # need modify
        ids = []
        self.ret = 'int main(' + ','.join(ids) + ')'


class ProgramBodyNode(Node):
    def __init__(self, tree, head):
        super().__init__(tree)
        self.head = head

    def Parse(self):
        self.child.append(ConstDeclarationsNode(self.tree['const_declarations']))
        self.child.append(VarDeclarationsNode(self.tree['var_declarations']))
        self.child.append(SubprogramDeclarationsNode(self.tree['subprogram_declarations']))
        self.child.append(CompoundStatementNode(self.tree['compound_statement']))
        self.ParseChildByOrder()

        body = self.child[3].ret
        body = self.head + ' {' + body + 'return 0;}'
        # print(body, file=ofile, flush=True)
        Output.AppendOutput(body)

class ConstDeclarationsNode(Node):
    def Parse(self):
        if self.tree == None:
            return
        for treeNode in self.tree['const_declaration']['values']:
            self.child.append(ConstValue(treeNode))
        self.ParseChildByOrder()


# VALUE DEFINITIONS
# basic value, const, array and struct

class ConstValue(Node):
    def Parse(self):
        id = self.tree['ID']
        value = self.tree['const_value']['value']
        type = 'char' if self.tree['const_value']['value'] else 'int'
        print('const {0} {1} = {2};'.format(type, id, value), file=ofile, flush=True)
        Output.AppendOutput('const {0} {1} = {2};'.format(type, id, value))


class VarDeclarationsNode(Node):
    def Parse(self):
        if self.tree == None:
            return
        for treeNode in self.tree['var_declaration']['values']:
            self.child.append(VarValueNode(treeNode))
        self.ParseChildByOrder()


# var_declaration
# includes idlist and type
class VarValueNode(Node):
    def __init__(self, tree, output=True):
        super().__init__(tree)

        # if false, return the result rather than directly print it
        self.output = output

    def Parse(self):
        idlist = self.tree['idlist']['ids']

        if isinstance(self.tree['type']['_type'], dict):
            # _type里面是一个包含type, _type的dict，表明了这是一个普通的声明(???)
            type = self.tree['type']['_type']['_type']
            type = Util.ConvertType(type)
            result = '{0} {1};'.format(type, ', '.join(idlist))

        elif self.tree['type']['_type'] == 'ARRAY':
            # array, 范围均取为[0, end)，无视start
            type = self.tree['type']['basic_type']['_type']
            type = Util.ConvertType(type)

            period = []
            for i in self.tree['type']['period']['values']:
                period.append(str(i['end'] + 1))
            period = '[' + ']['.join(period) + ']'

            for i in range(len(idlist)):
                idlist[i] += period

            result = '{0} {1};'.format(type, ','.join(idlist))

        elif self.tree['type']['_type'] == 'RECORD':
            self.child.append(MultypeNode(self.tree['type']['multype']))
            self.child[0].Parse()
            result = '{0} {1};'.format(self.child[0].structName, ','.join(idlist))

        if self.output:
            # print(result, file=ofile, flush=True)
            Output.AppendOutput(result)
        else:
            return result


class MultypeNode(Node):
    # use to name a struct
    structCount = 0

    def __init__(self, tree, output=True):
        super().__init__(tree)
        self.structName = '__struct' + str(MultypeNode.structCount)
        MultypeNode.structCount += 1

    # generate a struct, print struct code
    def Parse(self):
        structFields = []
        for treeNode in self.tree['values']:
            self.child.append(VarValueNode(treeNode, False))

        for node in self.child:
            structFields.append(node.Parse)

        # print
        # print('struct {0} {{'.format(self.structName), file=ofile, flush=True)
        Output.AppendOutput('struct {0} {{'.format(self.structName))
        for i in structFields:
            # print(i, file=ofile, flush=True)
            Output.AppendOutput(i)
        # print('};', file=ofile, flush=True)
        Output.AppendOutput('};')


# output = false
class ParameterListNode(Node):

    # return example: int a, int& b
    # without brackets
    def Parse(self):
        result = []
        for treeNode in self.tree['parameters']:
            self.child.append(ParameterNode(treeNode))

        for node in self.child:
            result.append(node.Parse())

        return ','.join(result)


class ParameterNode(Node):
    def Parse(self):
        isRefParam = self.tree['value']['type'] == 'var_parameter'

        type = Util.ConvertType(self.tree['value']['value_parameter']['basic_type']['_type']) if isRefParam\
            else Util.ConvertType(self.tree['value']['basic_type']['_type'])

        idlist = self.tree['value']['value_parameter']['idlist']['ids'] if isRefParam\
            else self.tree['value']['idlist']['ids']

        if isRefParam:
            type += '&'

        result = ','.join(map(lambda x: type + ' ' + x, idlist))
        return result


# SUB PROGRAM DEFINITIONS

class SubprogramDeclarationsNode(Node):
    def Parse(self):
        for treeNode in self.tree['subprograms']:
            self.child.append(SubprogramDeclarationNode(treeNode))
        self.ParseChildByOrder()


class SubprogramDeclarationNode(Node):
    def Parse(self):
        head = SubprogramHeadNode(self.tree['subprogram_head'])
        head.Parse()
        body = SubprogramBodyNode(self.tree['subprogram_body'], head.ret)
        body.Parse()


class SubprogramHeadNode(Node):
    # 因为在var declaration中可能有struct, 此处返回函数的Head, 而非直接print
    # e.g. ret = 'void func(int a)'
    def Parse(self):
        retType = 'void'
        if self.tree['_type'] == 'FUNCTION':
            retType = Util.ConvertType(self.tree['basic_type']['_type'])
        id = FUNC_PREFIX + self.tree['ID']

        params = ''
        if self.tree['formal_parameter']:
            self.child.append(ParameterListNode(self.tree['formal_parameter']['parameter_list']))
            params = self.child[0].Parse()
        # add prefix __func_ to identify with the return value
        self.ret = '{0} {1}({2})'.format(retType, id, params)


class SubprogramBodyNode(Node):
    def __init__(self, tree, head):
        super().__init__(tree)
        self.head = head

    def Parse(self):
        self.child.append(ConstDeclarationsNode(self.tree['const_declarations']))
        self.child.append(VarDeclarationsNode(self.tree['var_declarations']))
        self.child.append(CompoundStatementNode(self.tree['compound_statement']))
        self.ParseChildByOrder()

        body = self.child[2].ret
        if self.head[:4] != 'void':
            temp = self.head[:self.head.index('(')].split()
            temp[1] = temp[1].replace(FUNC_PREFIX, '')
            body = '{0} {{ {1} {2}; {3} return {2}; }}'.format(self.head, temp[0], temp[1], body)
        else:
            body = '{0} {{ {1} }}'.format(self.head, body)
        # print(body, file=ofile, flush=True)
        Output.AppendOutput(body)


class CompoundStatementNode(Node):
    def __init__(self, tree):
        super().__init__(tree)
        self.ret = ''

    def Parse(self):
        for treeNode in self.tree['statement_list']['statements']:
            self.child.append(StatementNode(treeNode))
        for node in self.child:
            node.Parse()
            self.ret += node.ret


class StatementNode(Node):
    def Parse(self):
        statementType = self.tree['_type']
        if statementType == 'variable':
            # statement -> variable assignop expression
            variable = VariableNode(self.tree['variable'])
            assignop = Util.ConvertOperator(self.tree['ASSIGNOP'])
            expression = ExpressionNode(self.tree['expression'])
            variable.Parse()
            expression.Parse()
            self.ret = variable.ret['id'] + assignop + expression.ret['result'] + ';'

        elif statementType == 'procedure_call':
            # statement -> procedure_call
            procedureCall = ProcedureCallNode(self.tree['procedure_call'])
            procedureCall.Parse()
            self.ret = procedureCall.ret + ';'

        elif statementType == 'compound_statement':
            compoundStatement = CompoundStatementNode(self.tree['compound_statement'])
            compoundStatement.Parse()
            self.ret = compoundStatement.ret + ';'

        elif statementType == 'IF':
            # statement -> if expression then statement else_part
            expression = ExpressionNode(self.tree['expression'])
            statement = StatementNode(self.tree['statement'])
            elseStatement = StatementNode(self.tree['else_part']['statement'])
            expression.Parse()
            statement.Parse()
            elseStatement.Parse()
            self.ret = 'if({0}) {{ {1} }} else {{ {2} }}'.format(expression.ret['result'],
                                                                    statement.ret, elseStatement.ret)

        elif statementType == 'FOR':
            # statement -> for id assignop expression to to_expression do do_expression
            # for(int id = expression; id <= to_expression; ) {
            #       do_expression
            # }
            id = self.tree['ID']
            assignop = Util.ConvertOperator(self.tree['ASSIGNOP'])
            expression = ExpressionNode(self.tree['expression'])
            to_expression = ExpressionNode(self.tree['to_expression'])
            do_expression = StatementNode(self.tree['statement'])
            expression.Parse()
            to_expression.Parse()
            do_expression.Parse()
            self.ret = 'for(int {0} {1} {2}; {0} <= {3};) {{ {4} }})'.format(id, assignop,
                                                                               expression.ret['result'],
                                                                               to_expression.ret['result'],
                                                                               do_expression.ret)


        elif statementType == 'READ':
            # statement -> read( variable_list )
            # result: scanf("%d%d", a, b)
            variableList = VariableListNode(self.tree['variable_list'])
            variableList.Parse()
            typeArr = []
            idArr = []
            for i in variableList.ret:
                typeArr.append(Util.ToIOForm(i['type']))
                idArr.append(i['id'])
            self.ret = 'scanf("{0}", {1});'.format(''.join(typeArr), ', '.join((idArr)))

        elif statementType == 'WRITE':
            # statement -> write( variable_list )
            # result: printf("%d%d\n", a, b)
            expressionList = ExpressionListNode(self.tree['expression_list'])
            expressionList.Parse()
            typeArr = []
            idArr = []
            for i in expressionList.ret:
                typeArr.append(Util.ToIOForm(i['type']))
                idArr.append(i['result'])
            self.ret = 'printf("{0}\\n", {1});'.format(''.join(typeArr), ', '.join(idArr))


class ProcedureCallNode(Node):
    def Parse(self):
        id = FUNC_PREFIX + self.tree['ID']
        expressionList = ExpressionListNode(self.tree['expression_list'])
        expressionList.Parse()
        self.ret = '{0}({1});'.format(id, ','.join(map(lambda x: x['result'], expressionList.ret)))


class ExpressionListNode(Node):
    # return a list of dict containing result and type
    # e.g. ret = [{'result', 'type'}]
    def __init__(self, tree):
        super().__init__(tree)
        self.ret = []

    def Parse(self):
        for treeNode in self.tree['expressions']:
            self.child.append(ExpressionNode(treeNode))
        for node in self.child:
            node.Parse()
            self.ret.append(node.ret)


class ExpressionNode(Node):
    def __init__(self, tree):
        super().__init__(tree)
        self.ret = {'result': None, 'type': None}

    def Parse(self):
        if 'RELOP' in self.tree:
            # expression -> simple_expression_1 relop simple_expression_2
            simpleExpression1 = SimpleExpressionNode(self.tree['simple_expression_1'])
            simpleExpression2 = SimpleExpressionNode(self.tree['simple_expression_2'])
            simpleExpression1.Parse()
            simpleExpression2.Parse()
            relop = Util.ConvertOperator(self.tree['RELOP'])
            self.ret['type'] = Util.ConvertType(simpleExpression1.tree['__type'])
            self.ret['result'] = simpleExpression1.ret + relop + simpleExpression2.ret
        else:
            # expression -> simple_expression
            simpleExpression = SimpleExpressionNode(self.tree['simple_expression'])
            simpleExpression.Parse()
            self.ret['result'] = simpleExpression.ret
            self.ret['type'] = Util.ConvertType(self.tree['__type'])


class SimpleExpressionNode(Node):
    def Parse(self):
        if 'ADDOP' in self.tree:
            # simple_expression -> simple_expression addop term
            simpleExpression = SimpleExpressionNode(self.tree['simple_expression'])
            addop = Util.ConvertOperator(self.tree['ADDOP'])
            term = TermNode(self.tree['term'])
            simpleExpression.Parse()
            term.Parse()
            self.ret = simpleExpression.ret + addop + term.ret
        else:
            # simple_expression -> term
            term = TermNode(self.tree['term'])
            term.Parse()
            self.ret = term.ret


class TermNode(Node):
    def Parse(self):
        if 'MULOP' in self.tree:
            # term -> term mulop factor
            term = TermNode(self.tree['term'])
            term.Parse()
            mulop = Util.ConvertOperator(self.tree['MULOP'])
            factor = FactorNode(self.tree['factor'])
            factor.Parse()
            self.ret = term.ret + mulop + factor.ret
        else:
            # term -> factor
            factor = FactorNode(self.tree['factor'])
            factor.Parse()
            self.ret = factor.ret


class FactorNode(Node):
    def Parse(self):
        if 'NUM' in self.tree:
            # factor -> num
            self.ret = str(self.tree['NUM'])

        elif 'variable' in self.tree:
            # factor -> variable
            variable = VariableNode(self.tree['variable'])
            variable.Parse()
            self.ret = variable.ret['id']

        elif 'expression' in self.tree:
            # factor -> (expression)
            expression = ExpressionNode(self.tree['expression'])
            expression.Parse()
            self.ret = '(' + expression.ret['result'] + ')'

        elif 'expression_list' in self.tree:
            # factor -> id (expression_list)
            id = FUNC_PREFIX + self.tree['ID']
            expressionList = ExpressionListNode(self.tree['expression_list'])
            expressionList.Parse()
            self.ret = id + '(' + ','.join(map(lambda x: x['result'], expressionList.ret)) + ')'

        elif 'not' in self.tree:
            # factor -> not factor
            factor = FactorNode(self.tree['factor'])
            factor.Parse()
            self.ret = '!(' + factor.ret + ')'

        elif 'uminus' in self.tree:
            # factor -> not factor
            factor = FactorNode(self.tree['factor'])
            factor.Parse()
            self.ret = '-(' + factor.ret + ')'


class VariableListNode(Node):
    # return [{'id', 'type'}], 返回一个list, 仅用于read(), write()
    def __init__(self, tree):
        super().__init__(tree)
        self.ret = []

    def Parse(self):
        for treeNode in self.tree['variables']:
            self.child.append(VariableNode(treeNode))
        for node in self.child:
            node.Parse()
            self.ret.append(node.ret)


class VariableNode(Node):
    # return {'id', 'type'}, c-styled type
    # e.g. {'id': 'a[100]', 'type': 'int'} => int a[100]
    def Parse(self):
        type = Util.ConvertType(self.tree['__type'])
        id = self.tree['ID']
        if self.tree['id_varpart'] != None:
            expressionList = ExpressionListNode(self.tree['id_varpart']['expression_list'])
            expressionList.Parse()
            id += '[' + ']['.join(map(lambda x: x['result'], expressionList.ret)) + ']'
        self.ret = {'id': id, 'type': type}


tree = json.loads(ifile.read())['ast']
program = ProgramStructNode(tree)
program.Parse()

Output.FormatOutput()