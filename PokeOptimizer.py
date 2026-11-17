import pandas as pd
import numpy as np

# Read in Pokemon data and do some data cleaning
poke_df = pd.read_csv("Pokemon.csv")
poke_df = poke_df.rename(columns={"#": "No"})

# Filter the list of Pokemon to those found in the region Pokemon Brilliant Diamond and Pokemon Shining Pearl are set in: Sinnoh
sinnoh = list(range(387,494)) # list of Pokemon discovered in Sinnoh

sinnoh_expat = [63, 64, 65, 129, 130, 315, 41, 42, 169, 74, 75, 76,
               95, 208, 66, 67, 68, 54, 55, 265, 266, 267, 268, 269, 
                214, 190, 92, 93, 94, 200, 198, 118, 119, 339, 340, 
                358, 307, 308, 77, 78, 185, 122, 113, 242, 173, 35, 36,
               172, 25, 26, 163, 164, 143, 201, 194, 195, 278, 279, 203,
                298, 183, 184, 223, 224, 72, 73, 349, 350, 226, 215, 207, 
                299, 280, 281, 282, 108, 133, 134, 135, 136, 196, 197,
               333, 334, 175, 176, 228, 229, 81, 82, 114, 193, 357, 111, 
                112, 355, 356, 137, 233, 123, 212, 239, 125, 240, 126, 
                220, 221, 361, 362, 359] # List of previous Pokemon also found in Sinnoh


genIV_dex = sinnoh_expat + sinnoh

sinnoh_df = poke_df[poke_df.No.isin(genIV_dex)]

# Remove duplicate Pokemon present: this is due to some Pokemon having additional forms
sinnoh_dex = sinnoh_df.drop_duplicates(subset=['No'])

# To make the playthrough team fair and practical, all legendary Pokemon are removed (these are rare Pokemon with in-game lore that generally have higher stats and can give players an unfair advantage)
sinnoh_dex = sinnoh_dex[sinnoh_dex.Legendary == False]
sinnoh_dex

# Load in type chart matrix that shows the matchup of the different 18 types against each other
# A 2 indicates a Pokemon of a type along the rows has an advantage against the opposing Pokemon of the type in the column. 
# A 1 indicates that the type from the row does neutral damage to the type against the column
# A 0.5 indicates that the a Pokemon of the type from the row does resisted or halved damage against the type on the column
# A 0 indicates the a Pokemon of the type from the row does no damage to the type on the column: the latter are immune to moves of that type
typeChart = pd.read_csv("PokemonTypeChart.csv", index_col = [0])

# Filter the type chart so the types in the columns correspond to just the types of the main bosses in the games: the gym leaders and Elite Four
types = ['Rock', 'Grass', 'Fighting', 'Water', 'Ghost', 'Steel',
         'Ice', 'Electric', 'Bug', 'Ground', 'Fire', 'Psychic']
gymEliteFour = typeChart[[c for c in typeChart.columns if c in types]]

# We construct our vectores and matrices to represent our constraints

strengths = []
numbers = []
names = []
totalStats = []
i = 0
for row in sinnoh_dex.itertuples(index=True, name='Pandas'):
    numbers.append(row.No)
    names.append(row.Name)
    
    # Check what types the Pokemon is strong against
    strengths.append([1 if s >= 2.0 else 0 for s in list(gymEliteFour.loc[row.Type1])])
    totalStats.append(row.Total)
    
    # Accounting for any secondary typings, and adding onto any advantages conferred
    try:
        strengths[i] = list(np.add(strengths[i], [1 if s >= 2.0 else 0 for s in list(gymEliteFour.loc[row.Type2])]))
        
    except:
        KeyError
        
    i += 1
    
# Equals 1 if the Pokemon is strong against the type indicated; 0 otherwise --> 206 by 18 matrix
advantage = [[1 if r >= 1 else 0 for r in strengths[i]] for i in range(206)]

# Create the set of starter Pokemon
starterNames = ['Turtwig', 'Grotle', 'Torterra', 
                'Chimchar', 'Monferno', 'Infernape',
               'Piplup', 'Prinplup', 'Empoleon']

starterIndices = []
for pkmn in starterNames:
    starterIndices.append(names.index(pkmn))

"""
Now we can create our model
"""
from pulp import *

# This initializes the model with the name and whether we want to maximize or minimize our objective function
best_team = LpProblem("Optimal_Pokemon_Team", LpMaximize)

# Define a binary variable for Pokemon
P = LpVariable.dicts("P", range(206), cat=LpBinary) # we have 206 Pokemon to consider

# Define the objective function to maximize
best_team += lpSum([totalStats[pkmn] * P[pkmn] for pkmn in range(206)])

# Constraint that we need 6 Pokemon on the team
best_team += lpSum([P[pkmn] for pkmn in range(206)]) == 6

# Constraint that we need 1 starter Pokemon
best_team += lpSum([P[pkmn] for pkmn in starterIndices]) == 1

# Constraint that we should have a Pokemon strong against at least one of the gym leaders/Elite Four
for i in range(12):
    best_team += lpSum([advantage[pkmn][i] * P[pkmn] for pkmn in range(206)]) >= 1

# Solve the optimization problem under the given constraints
best_team.solve()

# Extract the best six Pokemon
for i in range(206):
    if P[i].value() == 1:
        print(names[i])

# Can further constrain our algorithm to remove "Mythical Pokemon"
from pulp import *

mythicalNames = ['Cresselia', 'Manaphy']

mythicalIndices = []
for pkmn in mythicalNames:
    mythicalIndices.append(names.index(pkmn))

# This initializes the model with the name and whether we want to maximize or minimize our objective function
best_team = LpProblem("Optimal_Pokemon_Team", LpMaximize)

# Define a binary variable for Pokemon
P = LpVariable.dicts("P", range(206), cat=LpBinary) # we have 206 Pokemon to consider

# Define the objective function to maximize
best_team += lpSum([totalStats[pkmn] * P[pkmn] for pkmn in range(206)])

# Constraint that we need 6 Pokemon on the team
best_team += lpSum([P[pkmn] for pkmn in range(206)]) == 6

# Constraint that we need 1 starter Pokemon
best_team += lpSum([P[pkmn] for pkmn in starterIndices]) == 1

# Constraint that we can't use Cresselia or Manaphy
best_team += lpSum([P[pkmn] for pkmn in mythicalIndices]) == 0

# Constraint that we should have a Pokemon strong against at least one of the gym leaders/Elite Four
for i in range(12):
    best_team += lpSum([advantage[pkmn][i] * P[pkmn] for pkmn in range(206)]) >= 1

best_team.solve()

for i in range(206):
    if P[i].value() == 1:
        print(names[i])


"""
This can be further constrained to a specific starter Pokemon rather than the 
'best' one. For example, we can specify that our team must include Turtwig or its evolved forms
"""

# Indices of Turtwig and its evolved forms, Grotle and Torterra
turtwigIndices = [110, 111, 112]

# The other starters
notTurtwigIndices = list(set(starterIndices) - set(turtwigIndices))

# This initializes the model with the name and whether we want to maximize or minimize our objective function
best_team = LpProblem("Optimal_Pokemon_Team", LpMaximize)

# Define a binary variable for Pokemon
P = LpVariable.dicts("P", range(206), cat=LpBinary) # we have 206 Pokemon to consider

# Define the objective function to maximize
best_team += lpSum([totalStats[pkmn] * P[pkmn] for pkmn in range(206)])

# Constraint that we need 6 Pokemon on the team
best_team += lpSum([P[pkmn] for pkmn in range(206)]) == 6

# Constraint that we must have the Turtwig family
best_team += lpSum([P[pkmn] for pkmn in turtwigIndices]) == 1

# Constraint that we can't have any other starters
best_team += lpSum([P[pkmn] for pkmn in notTurtwigIndices]) == 0

# Constraint that we can't use Cresselia or Manaphy
best_team += lpSum([P[pkmn] for pkmn in mythicalIndices]) == 0

# Constraint that some Pokemon should be strong against at least one of the gym leaders/Elite Four
for i in range(12):
    best_team += lpSum([advantage[pkmn][i] * P[pkmn] for pkmn in range(206)]) >= 1

best_team.solve()

for i in range(206):
    if P[i].value() == 1:
        print(names[i])

"""
We can do the same for the other starter Pokemon, Piplup
"""
# Indices of Piplup and its evolved forms, Prinplup and Empoleon
piplupIndices = [116, 117, 118]

# The other starters
notPiplupIndices = list(set(starterIndices) - set(piplupIndices))

# This initializes the model with the name and whether we want to maximize or minimize our objective function
best_team = LpProblem("Optimal_Pokemon_Team", LpMaximize)

# Define a binary variable for Pokemon
P = LpVariable.dicts("P", range(206), cat=LpBinary) # we have 206 Pokemon to consider

# Define the objective function to maximize
best_team += lpSum([totalStats[pkmn] * P[pkmn] for pkmn in range(206)])

# Constraint that we need 6 Pokemon on the team
best_team += lpSum([P[pkmn] for pkmn in range(206)]) == 6

# Constraint that we must have the Piplup family
best_team += lpSum([P[pkmn] for pkmn in piplupIndices]) == 1

# Constraint that we can't have any other starters
best_team += lpSum([P[pkmn] for pkmn in notPiplupIndices]) == 0

# Constraint that we can't use Cresselia or Manaphy
best_team += lpSum([P[pkmn] for pkmn in mythicalIndices]) == 0

# Constraint that we should have some Pokemon strong against at least one of the gym leaders/Elite Four
for i in range(12):
    best_team += lpSum([advantage[pkmn][i] * P[pkmn] for pkmn in range(206)]) >= 1

best_team.solve()

for i in range(206):
    if P[i].value() == 1:
        print(names[i])