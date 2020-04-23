# set up virtualenv
python3.6 -m venv $HOME/env3
source $HOME/env3/bin/activate

# The version of python we've built won't necessarily
# have the latest version of pip bundled with it
pip install --upgrade pip

# get requirements
pip install -r /vagrant/zapisy/requirements.development.txt

echo "Python 3.6 environment has been set up."
