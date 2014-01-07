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
autocut_main(0.6, (1,4,1))

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
"""
    
