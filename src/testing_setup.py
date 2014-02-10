#script to setup
"""
import sys

mypath = "C:\\Users\\Xiaopewpew\\Desktop\\GithubProjects\\Transformer\\src"
sys.path.append(mypath)

import vector_helper
import transformer_cutting
import transformer_auto_cutting
import testing_setup
import arithmetic_helper

exec(compile(open("C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/src/transformer_cutting.py").read(), "C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/src/transformer_cutting.py", 'exec'))

exec(compile(open("C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/src/transformer_auto_cutting.py").read(), "C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/src/transformer_auto_cutting.py", 'exec'))
autocut_main(cut_reqs)

"""

"""
picks = [2,2]
cut_reqs = []
cut_reqs.append({"volume":0.4,"aspect":(2,2,1)})
cut_reqs.append({"volume":0.3,"aspect":(10,7,3)})
autocut_main(cut_reqs,picks)


"""


"""
test_obj
autocut_main(0.3, (1,2,1)) 4,7.3,8.3
"""

"""
for demo on car
autocut_main(0.6, (1,4,1))
tier 1 + 3 show case....
autocut_main(0.6, (40,100,12))
autocut_main(0.4, (2,2,1))
autocut_main(0.3, (10,4,3))
"""

"""
for demo on cube
tier 1 + 2
autocut_main(0.3, (10,7,5))
tier 3
autocut_main(0.3, (10,7,3))
"""

"""
demo on test_obj
first cut
autocut_main(0.4, (2,2,1))
2nd cut
autocut_main(0.6, (1,4,1))
"""

    
