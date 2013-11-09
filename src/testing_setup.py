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
autocut_main(0.6)
"""

    
