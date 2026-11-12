import rewardkit as rk


rk.check("build", weight=1, name="build")
rk.check("no_python", weight=1, name="no_python")
rk.check("behaviour", weight=4, name="behaviour")
