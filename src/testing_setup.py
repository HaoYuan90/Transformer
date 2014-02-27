#script to setup
"""
import sys

mypath = "C:\\Users\\Xiaopewpew\\Desktop\\GithubProjects\\Transformer\\src"
sys.path.append(mypath)

cut_src_path = "C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/src/transformer_cutting.py"
exec(compile(open(cut_src_path).read(), "cut_src_path", 'exec'))
driver_src_path = "C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/src/transformer_driver.py"
exec(compile(open(driver_src_path).read(), "driver_src_path", 'exec'))

cutting_main()

cut_req = {"volume":0.2,"aspect":(3,1,1),"is_sym":True}
cutting_debug_1p(cut_req, 0, True)

"""

"""
picks = [0,0]
cut_reqs = []
cut_reqs.append({"volume":0.4,"aspect":(2,2,1),"is_sym":False})
cut_reqs.append({"volume":0.3,"aspect":(1,1,1),"is_sym":False})
cutting_debug(cut_reqs,picks)


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

    
