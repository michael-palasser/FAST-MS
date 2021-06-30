import re

from src.Exceptions import InvalidInputException


def stringToFormula(formulaString, formulaDict, sign):
    '''
    Converts the a formula from string (can contain parenthesis) to dict
    :param (str) formulaString: string to be converted
    :param (dict[str:int]) formulaDict: initial formula dictionary
    :param (int) sign: +1 to add new formula to initial or -1 to subtract
    :return (dict[str:int]): new formula dictionary
    '''
    #everything in parenthesis
    if formulaString == "" or formulaString == "-":
        return formulaDict
    elif formulaString[0].islower():
        raise InvalidInputException(formulaString, ", Unvalid format, first character in Sequence must not be lower case")
    beginIndizes = [m.start() for m in re.finditer('\(', formulaString)]
    endIndizes = [m.start() for m in re.finditer('\)', formulaString)]
    if len(beginIndizes) != len(endIndizes):
        raise InvalidInputException(formulaString, 'Incorrect use of parenthesis')
    #subString = formulaString[:beginIndizes[0]]
    #formulaDict = AbstractItem1.stringToFormula2(formulaString[:beginIndizes[0]], formulaDict, sign)
    #print(beginIndizes,endIndizes)
    lastEnd = 0
    for bI,eI in zip(beginIndizes,endIndizes):
        #print(formulaString[lastEnd:bI],formulaString[bI+1:eI])
        formulaDict = stringToFormula2(formulaString[lastEnd:bI], formulaDict, sign)
        temp = stringToFormula2(formulaString[bI+1:eI], {}, sign)
        if (len(formulaString)>eI+1) and (formulaString[eI+1].isnumeric()):
            nr = int(re.findall('\)\d+', formulaString[bI+1:])[0][1:])
            #print('nr',nr)
            temp = {key:val*nr for key,val in temp.items()}
        addToDict(formulaDict,temp)
        lastEnd = eI
    formulaDict = stringToFormula2(formulaString[lastEnd:],formulaDict,sign)
    return formulaDict


def stringToFormula2(formulaString, formulaDict, sign):
    '''
    Converts a String to a formula - dict and adds or subtracts it to or from an original formula
    :param (str) formulaString: String which should be converted to a formula
    :param (dict[str:int]) formulaDict: "old" formula
    :param (int) sign: +1 or -1 for addition or subtraction of formula to or from formulaDict
    :return (dict[str:int]): new formula
    '''
    if formulaString == "" or formulaString == "-":
        return formulaDict
    elif formulaString[0].islower():
        raise InvalidInputException(formulaString, ", Unvalid format, first character in Sequence must not be lower case")
    for item in re.findall('[A-Z][^A-Z]*', formulaString):
        element = item
        number = 1
        '''print(item)
        print(re.findall('[|^&*_]', item))
        newItem = item
        match = re.match('[|^&*_]', newItem)
        if match:
            element = None
            newItem = match.group(2)'''
        match = re.match(r"([a-z]+)([0-9]+)", item, re.I)  # re.I: ignore case: ?
        if match:
            element = match.group(1)
            number = int(match.group(2))
        if element in formulaDict:
            formulaDict[element] += number * sign
        else:
            formulaDict[element] = number * sign
    if len(formulaDict)<1:
        raise InvalidInputException(formulaString, "Unvalid format of formula")
    return formulaDict


def addToDict(dict1,dict2):
    '''
    Adds the values of one dict to another dict
    :param (dict[str:int]) dict1:
    :param (dict[str:int]) dict2:
    :return (dict[str:int]): "sum" dict
    '''
    for element, number in dict2.items():
        if element in dict1.keys():
            dict1[element] += number
        else:
            dict1[element] = number
    return dict1