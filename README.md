CLOUD COMPUTING:

TEAM MEMBERS  :

SHIVANGI RAJ      PES1201700098
PRATHUSHA K       PES1201701831
MEGHANA A         PES1201701279
AJAY CHAVAN       PES1201701649

###INSTRUCTIONS TO RUN THE PROJECT:
#--------------------------------------------------------------------------------------------#
##for running orchestrator master slave rabbitmq and zookeeper 
(basically we go to the folder where .yml file is present)
cd cc_project
sudo docker-compose build
sudo docker-compose up

after every run please do : 
sudo docker volume prune (this will delete the unwanted space which is being used)
#--------------------------------------------------------------------------------------------#
##For running ride :::
(basically we go to the folder where .yml file is present)
cd cc_project
cd rides
sudo docker-compose build
sudo docker-compose up

after every run please do : 
sudo docker volume prune (this will delete the unwanted space which is being used)
#-------------------------------------------------------------------------------------------#
##For running user :
(basically we go to the folder where .yml file is present)
cd cc_project
cd rides
sudo docker-compose build
sudo docker-compose up

after every run please do : 
sudo docker volume prune (this will delete the unwanted space which is being used)
#------------------------------------------------------------------------------------------#
If getting an error that is port already used :(port 80)
command :sudo kill -9 `sudo lsof -t -i:80`

## COMMANDS:
show all ports running -->  sudo lsof -i -P -n | grep LISTEN
                            sudo netstat -tulpn | grep LISTEN
                            sudo lsof -i:22 ## see a specific port such as 22 ##
                            sudo nmap -sTU -O IP-address-Here

remove unwanted images --> sudo docker image prune
             container -->sudo docker container prune



