import json

ifile = open("res.json", 'r')
ofile = open('test.c', 'w')
# debugfile = open('debug.txt', 'w+')
raw_data = json.loads(ifile.read())

ast = raw_data['ast']
symbol_table = raw_data['symbolTable']

subs = [0] * 1000

def trans_type(raw_type):
    if(raw_type == 'INTEGER'):
        return 'int'
    
def trans_op(raw_op):
    if(raw_op == ':='):
        return '='
    if(raw_op == '='):
        return '=='

def declare(node):
    type = node['type']['_type']['_type']
    res = trans_type(type) + ' '

    for id in node['idlist']['ids']:
        res += id + ', '
    res = res[:-2]
    res += ';'
    print(res, file=ofile, flush=True)

def handle_factor(node):
    _type = node['_type']
    if(_type == 'NUM'):
        return str(node['NUM'])
    if(_type == 'variable'):
        return str(node['variable']['ID'])
    if(_type == 'procedure_id'):
        res = node['ID'] + '('
        flag = False
        for expression in node['expression_list']['expressions']:
            if(flag == True):
                res += ', '
            res += handle_expression(expression)
            flag = True
        res += ')'
        return res

def handle_expression(node):
    res = ''
    if(node.get('simple_expression') != None):
        # expression -> simple_expression
        res = handle_factor(node['simple_expression']['term']['factor'])
    else:
        # expression -> simple_expression1 relop simple_expression2
        res += handle_factor(node['simple_expression_1']['term']['factor']) + ' ' + trans_op(node['RELOP']) + ' ' + handle_factor(node['simple_expression_2']['term']['factor'])
    return res

def handle_statement(node):
    _type = node['_type']
    res = ''

    if(_type == 'IF'):
        res = 'if ('
        res += handle_expression(node['expression'])
        res += ') { '
        res += handle_statement(node['statement'])
        res += ' }'
    
    if(_type == 'variable'):
        res = node['variable']['ID'] + ' '
        res += trans_op(node['ASSIGNOP']) + ' '
        res += handle_expression(node['expression'])
        res += ';'

    if(_type == 'WRITE'):
        res = 'printf("'
        for __type in node['expression_list']['__type']:
            if(__type == 'INTEGER'):
                res += '%d'
            # more type ... 
        res += '"'
        for expression in node['expression_list']['expressions']:
            res += ', ' + handle_expression(expression)
        res += ');'

    return res

def handle_sub(node):
    sid = node['id']
    ret_type = node['subprogram_head']['basic_type']['_type']
    params = node['subprogram_head']['formal_parameter']['parameter_list']['parameters'][0]
    prm_type = params['value']['basic_type']['_type']
    
    res = trans_type(ret_type) + ' '
    res += node['subprogram_head']['ID']
    res += '('

    # parameters
    flag = False; 
    for id in params['value']['idlist']['ids']:
        if(flag == True):
            res += ', '
        res += trans_type(prm_type) + ' ' + id
        flag = True

    res += ') { '

    res += trans_type(ret_type) + ' ' + node['subprogram_head']['ID'] + '; '
    for statement in node['subprogram_body']['compound_statement']['statement_list']['statements']:
        res += handle_statement(statement)
    
    res += ' return ' + node['subprogram_head']['ID'] + '; }'
    subs[sid] = res
    print(res, file=ofile, flush=True)


def handle(node):
    if(node == None):
        return
    
    type = node['type']
    if(type == 'programstruct'):
        handle(node['program_head'])
        handle(node['program_body'])

    if(type == 'program_body'):
        handle(node['const_declarations'])
        handle(node['var_declarations'])   
        for subprogram in node['subprogram_declarations']['subprograms']:
            handle(subprogram)
        handle(node['compound_statement'])
    
    if(type == 'var_declarations'):
        handle(node['var_declaration'])

    if(type == 'var_declaration'):
        declare(node['values'][0])
        # 根据 flag 将结果放入不同位置中

    if(type == 'subprogram'):
        handle_sub(node)

    if(type == 'subprogram_body'):
        handle(node['const_declarations'])
        handle(node['var_declarations'])   

    if(type == 'compound_statement'):
        res = 'int main() { '
        for statement in node['statement_list']['statements']:
            res += handle_statement(statement)
        res += ' }'
        print(res, file=ofile, flush=True)

handle(ast)
