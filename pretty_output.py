'''
This writes pretty output to the console for warnings and errors. It is used to make important messages stand out in the console output.
'''
def warning(output):
    topBorder = "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
    sideLength = 0
    extraSpace = 0
    extraRight = 0
    if len(output) < len(topBorder):
        sideLength = int((len(topBorder) - len(output)) / 4)
        extraSpace = int(len(topBorder) - 4 * sideLength - len(output))
        if extraSpace % 2 == 1: extraRight = 1
        extraSpace //= 2 
    print()
    print(topBorder)
    print("-=-=-=-=-=-=-=-=-=-=-=-=-=Warning!-=-=-=-=-=-=-=-=-=-=-=-=-=-")
    print(topBorder)
    print("-="*sideLength + " " * extraSpace + output + " " * (extraSpace + extraRight) + "=-"*sideLength)
    print(topBorder)
    print()