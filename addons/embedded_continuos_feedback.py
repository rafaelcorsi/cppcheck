#!/usr/bin/env python3
import sys

import cppcheckdata

IRQ_NAMES = ['callback', 'Handler']
DELAY_FUNCTIONS = ['delay_', 'delay_ms', 'delay_us', 'delay_s']
OLED_FUNCTIONS = ['gfx_mono_']
PRINTF_FUNCTIONS = ['printf', 'sprintf']

RULE_1_ERRO_TXT = ["All global variables that are accessed from IRQ must be declared as volatile to ensure that the compailer will not optimize it out.",
                   "All global variables assigment in IRQ or Callback should be volatile"]
RULE_2_ERRO_TXT = ["Global variables should generally be avoided, except when necessary or when dealing with IRQs",
                   "Only use global vars in IRQ"]
RULE_3_1_ERRO_TXT = ['ISR shall be fast as possible, forbidden use of delay functions inside hardware interruption',
                     'Forbidden use of delay functions within IRQ']
RULE_3_2_ERRO_TXT = ['ISR shall be fast as possible, forbidden OLED update inside hardware interruption',
                     'Forbidden use of gfx_mono_... functions within IRQ']
RULE_3_3_ERRO_TXT = ['ISR shall be fast as possible, forbidden PRINTF/SPRINTF inside hardware interruption',
                     'Forbidden use of printf/sprintf functions within IRQ']
RULE_3_4_ERRO_TXT = ['ISR shall be fast as possible avoid the use of while and for loops',
                     'Forbidden use of loops/While within IRQ']


from misra import isFunctionCall, isKeyword


class EmbeddedC():
    def __init__(self, data):
        self.data = data
        self.funcList = []
        self.varList = []
        self.erroShortText = False
        self.init()

    def init(self):
        self.createFuncList()
        self.createVarList()

    def createVarList(self):
        for var in self.data.variables:
            self.varList.append(
                {
                "id": var.Id,
                "name": var.nameToken.str,
                "type": var.typeStartToken.str,
                "isGlobal": var.isGlobal,
                "isLocal": var.isLocal,
                "isArgument": var.isArgument,
                "isConstant": var.isConst,
                "isVolatile": var.isVolatile,
                }
            )

    def createFuncList(self):
        for scope in self.data.scopes:
            if scope.type == "Function":
                self.funcList.append(
                    {
                    'scopeId': scope.Id,
                    'functionId': scope.function.Id,
                    'name': scope.function.name,
                    'argId': scope.function.argumentId
                    }
                )

    def print(self):
        print('---')
        for var in self.varList:
            print(var)
        print('´----------------------')
        for fun in self.funcList:
            print(fun)

    def searchFuncByScopeId(self, id):
        for f in self.funcList:
            if id == f['scopeId']:
                return f
        return None

    def searchVarName(self, name):
        for v in self.varList:
            if name == v['name']:
                return v
        return None

    def getGlobalVarAssigments(self):
        l = []
        for token in self.data.tokenlist:
            if token.isAssignmentOp:
                f = d.searchFuncByScopeId(token.scope.Id)
                if f is not None:
                    var = d.searchVarName(token.astOperand1.str)
                    if var is not None and var['isGlobal'] == True:
                        l.append(
                            {
                                'func': f,
                                'var': var,
                            }

                        )
        return l

    def erroShort(self):
        self.erroShortText = True

    def printRuleViolation(self, ruleN, where, text):
        erroText = text[0] if self.erroShortText is False else text[1]
        print (f' - [RULE {ruleN} VIOLATION] {where} \r\n\t {erroText}')

    def isFunctionIRQ(self, f):
        fName = f['name']
        res = [ele for ele in IRQ_NAMES if(ele in fName)]
        return True if res else False

    def getFunctionIrqList(self):
        irqList = []
        for f in self.funcList:
            if self.isFunctionIRQ(f):
                irqList.append(f)
        return irqList

    def rule_1(self):
        """
        all global variables assigment in IRQ or Callback should be volatile
        """
        assigmentList = self.getGlobalVarAssigments()
        erro = 0
        for ass in assigmentList:
            if self.isFunctionIRQ(ass['func']):
                if ass['var']['isVolatile'] != True:
                    varName = ass['var']['name']
                    funcName = ass['func']['name']
                    self.printRuleViolation("1.0", f'[variable {varName} in function {funcName}]', RULE_1_ERRO_TXT)
                    erro = erro + 1
        return erro

    def rule_2(self):
        """
        only use global vars in IRQ
        """
        assigmentList = self.getGlobalVarAssigments()
        erro = 0
        for ass in assigmentList:
            if self.isFunctionIRQ(ass['func']) is False:
                varName = ass['var']['name']
                funcName = ass['func']['name']
                self.printRuleViolation("2.0", f'[variable {varName} in function {funcName}]', RULE_2_ERRO_TXT)
                erro = erro + 1
        return erro

    def rule_3_x(self, ruleN, ruleTxt, rule):
        """
        rule 3: search for forbiten functions call inside ISR
        """
        irqList = self.getFunctionIrqList()
        erro = 0
        for f in irqList:
            for token in self.data.tokenlist:
                if token.scope.Id == f['scopeId']:
                    res = [ele for ele in rule if(ele in token.str)]
                    if res:
                        isrName = f['name']
                        callName = token.str
                        self.printRuleViolation(ruleN, f"call to {callName} inside {isrName}", ruleTxt)
                        erro = erro + 1
        return erro

    def rule_3_1(self):
        """
        No delay inside IRQ
        """
        return self.rule_3_x("3.1", RULE_3_1_ERRO_TXT, DELAY_FUNCTIONS)

    def rule_3_2(self):
        """
        No oled calls inside IRQ
        """
        return self.rule_3_x("3.2", RULE_3_2_ERRO_TXT, OLED_FUNCTIONS)

    def rule_3_3(self):
        """
        No printf calls inside IRQ
        """
        return self.rule_3_x("3.3", RULE_3_3_ERRO_TXT, PRINTF_FUNCTIONS)

    def rule_3_4(self):
        """
        No while inside IRQ
        """
        irqList = self.getFunctionIrqList()
        erro = 0
        for f in irqList:
            for token in self.data.tokenlist:
                if token.scope.Id == f['scopeId']:
                    if token.str == 'while':
                        isrName = f['name']
                        self.printRuleViolation("3.4", f"use of 'while' inside {isrName}", RULE_3_4_ERRO_TXT)
                        erro = erro + 1
        return erro

    # TODO
    def rule_4(self):
        """
        rule 4: search complex code in ISR
        """
        fIrqList = []
        for f in self.funcList:
            if self.isFunctionIRQ(f):
                fIrqList.append(f)

        # number of functions call
        for f in fIrqList:
            print(f['name'])
            fCallCnt = 0
            for token in self.data.tokenlist:
                if token.scope.Id == f['scopeId']:
                    if isFunctionCall(token):
                        fCallCnt = fCallCnt + 1
            print(fCallCnt)

data = cppcheckdata.CppcheckData('main.c.dump')
for cfg in data.iterconfigurations():

    d = EmbeddedC(cfg)
    #d.print()
    d.erroShort()
    d.rule_1() # global var ISR volatile
    d.rule_2() # only use global vars in IRQ
    d.rule_3_1() # ISR SAP no delayy
    d.rule_3_2() # ISR SAP no oled
    d.rule_3_3() # ISR SAP no printf
    d.rule_3_4() # ISR SAP no while
    #d.rule_4() # ISR no loop

sys.exit(cppcheckdata.EXIT_CODE)
