import arithmetic_helper as arith

"""
Global constants
"""
# Floating point error tolerance
fp_tolerance = 0.0001
normal_tolerance = 0.03
# Number of divisions 
tier_1_divs = 20 #20
tier_2_divs = 10
tier_3_divs = 10
# Deal with blender's bug with boolean operation, choose appropriate ones 
tier_1_subdivision_level = 1
tier_2_subdivision_level = 1
tier_3_subdivision_level = 1
# How accurate the accepted cuts are
allowed_pd_volume = 0.1
allowed_pd_aspect = 0.2
mediocre_pd_cap = 0.8
bad_pd_cap = 1.5

# Debug messages control
DEBUG_MATCHING = True
DEBUG_ANALYTICS = False

"""
Change subdivision level to avoid a new cut with an edge landing right on the edge of an old cut
"""
def next_subdivision_level():
    global tier_1_divs
    global tier_2_divs
    global tier_3_divs
    tier_1_divs = arith.next_smallest_prime(tier_1_divs)
    tier_2_divs = arith.next_smallest_prime(tier_2_divs)
    tier_3_divs = arith.next_smallest_prime(tier_3_divs)