
# BME VIK Chatbot - RAG Project

## Introduction
This project is part of my diploma/thesis at BME VIK. The aim is to develop a chatbot interface to assist BME VIK students with various inquiries. The chatbot, developed in Python, leverages advanced technologies to provide accurate and helpful responses to student queries.

## Setup and Installation

### Requirements
- Python 3.x
- Other dependencies listed in `requirements.txt`

### Installation
To install the necessary libraries, please run the following command:
```
pip install -r requirements.txt
```
This will install all the required packages to run the chatbot.

Additionally, run the setup script:
```
python setup.py install
```
Finally add your OpenAI API key in the running application.
Alternatively make run the following command with your API key inserted:
```
echo OPENAI_API_KEY=<your_api_key> > .env
```
### Installation with Docker
Need to use full paths here efor some reason
```shel
docker pull solr
mkdir -p ./solr_data
docker run -d -p 8983:8983 --name my_solr -v "C:/Users/takat/OneDrive/Documents/Egyetem/Diploma/solr_data:/var/solr" solr solr-precreate vik-gpt-core
```
```
docker build -t my-jupyter-app .
```

```
docker run --name my_jupyter_container -p 8888:8888 my-jupyter-app 
```
```
docker start -a my_jupyter_container
```
This code builds and runs the streamlit app in a docker container:
```
docker build -t your_streamlit_image:latest .

docker run -d -p 8501:8501 your_streamlit_image:latest
docker build -t your_streamlit_image:latest .


docker-compose build --no-cache

docker-compose up -d
docker-compose down

```


```
gcloud compute ssh vik-gpt-vm 

sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo usermod -aG docker $USER

sudo chown -R 8983:8983 /home/takat/app/Diploma/solr_data
sudo chmod -R 775 /home/takat/app/Diploma/solr_data
sudo chown -R 8983:8983 /home/takat/app/Diploma/solr_data/logs
sudo chmod -R 775 /home/takat/app/Diploma/solr_data/logs

gcloud compute scp --recurse "C:\Users\takat\OneDrive\Documents\Egyetem\Diploma" vik-gpt-vm:/home/takat/app
gcloud compute scp --recurse "C:\Users\takat\OneDrive\Documents\Egyetem\Diploma\solr_data\data\vik-gpt-core" vik-gpt-vm:/home/takat/app/Diploma/solr_data/data
gcloud compute scp --recurse "C:\Users\takat\OneDrive\Documents\Egyetem\Diploma\faiss_db" vik-gpt-vm:/home/takat/app/Diploma

```

### Running the Application
To start the chatbot, use the following command:
```
streamlit run app.py
```
This will initiate the Streamlit server and the chatbot interface should be accessible through a web browser.

## Usage
Once the application is running, you can interact with the chatbot through the web interface. Simply type your question into the chat input and the chatbot will respond with relevant information.

## Contributing
Contributions to the project are welcome. Please ensure to follow the standard coding conventions and add appropriate tests for any new features.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
