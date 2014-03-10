"""
import sys

mypath = "C:\\Users\\Xiaopewpew\\Desktop\\GithubProjects\\Transformer\\src"
sys.path.append(mypath)

setup_src_path = "C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/src/setup_helper.py"
exec(compile(open(setup_src_path).read(), "setup_src_path", 'exec'))
"""

"""
Setup armature for testing purposes
"""
def setup_armature(armature):
    for bone in armature.data.bones:
        if "Link" not in bone.name and "link" not in bone.name:
            bone["component_volume"] = 0.1
            bone["component_aspect"] = (1,1,1)
    