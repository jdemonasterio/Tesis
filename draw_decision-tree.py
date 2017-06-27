"""
Example script on how to make a graphic representation of a
Decision Tree Learner.

This will load the


For the last part, the package graphviz needs to be installed.
In ubuntu use `sudo apt-get install graphviz
And then run this script below.
"""
import subprocess
from sklearn.datasets import load_iris
from sklearn import tree

clf = tree.DecisionTreeClassifier()
iris = load_iris()


clf = clf.fit(iris.data, iris.target)

outf = 'tree.dot'
tree.export_graphviz(clf,
                    max_depth = 7,
impurity = True,
            out_file=outf)

sub_call = 'dot -Tps {} -o {} '.format(outf, outf.replace('.dot','.png'))
# print(sub_call)
subprocess.call(sub_call, shell=True)



