# calculate a players correct ratio
def calcRatio(stats):
    corrects = int(stats[0])
    incorrects = int(stats[1])
    decimals = 1
    ratio = round(corrects/(incorrects+corrects+0.000000001)*100, decimals)
    return(ratio)

# calculate a players skill rating from their stats and ratio
def calcSkillRating(stats, ratio):
    corrects = int(stats[0])
    longestStreak = int(stats[2])
    experienceScalar = 10           # this variable affects how important a players experience is to the SR formula
    decimals = 0
    skillRating = int(round(ratio * (corrects/experienceScalar + longestStreak), decimals))
    return(skillRating)