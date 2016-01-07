sudo apt-get update
sudo apt-get install -y build-essential g++ libfontconfig1-dev libicu-dev libfreetype6 libssl-dev 
libpng-dev libjpeg-dev python-dev phantomjs python-pip python-dev build-essential libzmq-dev mongodb-org npm nodejs-legacy

sudo pip install --upgrade pip 
sudo pip install --upgrade virtualenv
#sudo apt-get -y install numpy
sudo apt-get -y install python-matplotlib python-scipy python-pandas python-sympy python-nose
sudo pip install pyzmq jinja2 tornado pymongo selenium pandas requests beautifulsoup4
sudo pip install jupyter
#sudo npm install -g phantomjs


sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo bash -c 'sudo cat > /etc/fstab << EOF
/swapfile   none    swap    sw    0   0
EOF'


#screen -S ipython
#cd /home/vagrant && sudo jupyter notebook --port=80 --ip=0.0.0.0 --no-browser &
#exit
#cd /vagrant