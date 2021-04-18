import re

def stockSymbols(toSearch):
    potentialSet = set(re.findall("\\b[A-Z]{2,5}\\b", toSearch))
    ignoreList = [
        "US", "USA", "EU", "NZ", "OP", "NOT", "ER", "IRS", "FDIC", "IRA", "ETF", "ROTH", "USD", "CAD",
        "SP", "DJ", "PDF", "IK", "TSP", "CD", "SS", "YO", "AGI", "MAGI", "YTD", "SPDR", "FMI", "GMT",
        "HYSA", "TFSA", "COVID", "BH", "CEO", "START", "FWIW", "SWR", "GIC", "DR", "IBKR",
        "TLDR", "PITA", "LOL", "FYI", "FAQ", "CPA", "DM", "TBH", "AF", "DCA", "IMO", "WSB", "NYSE", "HSA",
        "AD", "CAP", "INTL", "INST", "SM", "HELOC", "FIRE", "FI", "TIL", "YOLO", "HF", "EDIT", "DIY",
        "VANG", "TOT", "TD", "ATH", "PFOF", "PWL", "BOT", "II", "FTSE", "LOT", "MSCI",
        "FANG", "FAANG", "FOMO", "TIPS"
        ]
    replaceDict = {
        "ARK": "ARKK",
        "BRK": "BRK-B"
    }
    for word in ignoreList:
        potentialSet.discard(word)
    for word in replaceDict:
        if word in potentialSet:
            potentialSet.add(replaceDict[word])
            potentialSet.discard(word)
    stockSymbols = list(potentialSet)
    stockSymbols.sort()
    return stockSymbols