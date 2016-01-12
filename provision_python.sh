sudo apt-get update
sudo apt-get install -y build-essential g++ libfontconfig1-dev libicu-dev libfreetype6 libssl-dev node
libpng-dev libjpeg-dev python-dev phantomjs python-pip python-dev build-essential libzmq-dev mongodb-org npm nodejs-legacy

#sudo apt-get -y install numpy
sudo apt-get -y install python-matplotlib python-scipy python-pandas python-sympy python-nose
sudo apt-get -y install libxml2-dev libxslt-dev python-dev
sudo pip install pyzmq jinja2 tornado selenium pandas requests beautifulsoup4
sudo pip install jupyter twilio grequests lxml
#sudo npm install -g phantomjs
sudo pip install --upgrade pip 
sudo pip install --upgrade virtualenv
wget https://github.com/Pyppe/phantomjs2.0-ubuntu14.04x64/raw/master/bin/phantomjs
mv phantomjs /usr/local/bin/phantomjs

chmod 777 /usr/local/bin/phantomjs

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

# crontab -e
# 0 1 * * * /usr/bin/python /vagrant/scraper/web.py > /vagrant/scraper/out.log