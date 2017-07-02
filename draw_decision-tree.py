"""
Example script on how to make a graphic representation of a
Decision Tree Learner.

This will load the


For the last part, the package graphviz needs to be installed.
In ubuntu use `sudo apt-get install graphviz
And then run this script below.
"""
import subprocess
import os
import pandas as pd
from sklearn.datasets import load_iris
from sklearn import tree

REPO_DIR = os.path.dirname(os.path.realpath(__file__))
# REPO_DIR = "/".join(REPO_DIR[:REPO_DIR.index('Tesis')+1])

PROJECT_DIR = os.path.join(REPO_DIR,'mexico-scripts-ver2')
DATA_DIR = os.path.join(PROJECT_DIR,'data')

clf = tree.DecisionTreeClassifier()
input_file =  os.path.join(DATA_DIR,'data_balanced_sample.csv')

iris = load_iris()

df = pd.DataFrame(iris.data)
df['y'] = iris.target

clf = clf.fit(df, iris.target)

outf = 'tree.dot'
tree.export_graphviz(clf,
                    max_depth = 7,
                        impurity = True,
                        proportion = True,
                    out_file=outf)

sub_call = 'dot -Tps {} -o {} '.format(outf, outf.replace('.dot','.ps'))
print(sub_call)
# subprocess.call(sub_call, shell=True)



