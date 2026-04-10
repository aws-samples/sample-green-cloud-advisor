# 🌱 GreenCloud Advisor

GreenCloud Advisor is an AWS Region Sustainability Recommender that balances proximity and environmental impact.
It has two modes: 
- **New workload region and optimization recommender** : Specify in natural language the workload you are planning to launch and select the possible regions based on your latency requirements. 
   Once you do that, it first checks wether all the services are available in the selected regions and if they do, then it tells you which region as the lowest sustainability score/lowest carbon intensity.
   It also tells you possible optimization you can do for the services you have chosen.
   At then end, you can download the report in pdf format
- **Analyse the actual carbon foorprint for the existing workloads, get insights and chat with the report**: Upload your [Carbon Emission Report](https://docs.aws.amazon.com/sustainability/latest/userguide/csv-reports.html) report from the [sustainability console](https://docs.aws.amazon.com/sustainability/latest/userguide/getting-started.html)
   You can click on ```Get Insights``` button to get the insights like ```what are the top services that are contributing most on the carbon usage```, ```which regions have the most score``` and so on.
   You can also chat with the report by chatbot on the right. Some of the sample questions you can ask are mentioned in the same tab.

You can test this running the streamlit app locally. If you like it, you can deploy this to your AWS account.

## Contributors
* [Smita Srivastava](smisriv@amazon.com)
* [Tomoya Tozuka](totozuka@amazon.com)
* [Kayalvizhi Kandasamy](kayalvk@amazon.com)
* [Gaurav Gupta](gauravgp@amazon.com)
* [Shubham Tiwari](twars@amazon.com)


## Features

- **Smart Region Selection**: Analyzes proximity, service availability, and carbon footprint
- **Dual Carbon Accounting**: Uses both location-based and market-based methods
- **Carbon emission report integration**: Upload and analyze your carbon emmission csv report which cane be downloaded from sustainability console
- **Interactive Web UI**: Streamlit-based interface for easy use
- **Multilingual Support (EN/JA)**: UI and PDF reports support English and Japanese with one-click switching

## Solution overview
This solution uses https://app.electricitymaps.com/ apis to get the carbon numbers of a specific region in the world to give a region score for the new workload. You need to create an **API KEY** to use the electricitymaps apis
- create an API Token in https://app.electricitymaps.com/settings/api-access with an account. You can use sandbox key for free.
- Once you do that, save the same in ```API_TOKEN``` parameter in the config ```config``` in the root folder. It should look like this ```API_TOKEN='Xsxxxxxxxxxxxxxxx7```

This solution operates in two modes **Region Analysis** and **Sustainability Report Analysis**. For **Region Analysis**, https://app.electricitymaps.com/ is used to get the sustainability score for the region you choose.
Both modes use GenAI to create the recommendations and report.

## Run the app locally
Open a terminal locally
- set AWS credentials in the terminal
- Run the setup script (installs dependencies and Japanese fonts):
  ```bash
  ./setup.sh
  ```
  Or install manually:
  ```bash
  pip install -r requirements.txt
  ```
  **Note (Linux only):** Japanese font is required for PDF/chart rendering. `setup.sh` installs it automatically. For manual install: `sudo apt-get install fonts-noto-cjk`
- run the streamlit app ```streamlit run streamlit_app.py --server.port 8501```
  <br> With the above command http://localhost:8501 will be opened. If it is not opened, open the same in a browser
- To switch between English and Japanese, click the 🇺🇸 EN / 🇯🇵 JA button at the top right of the page

## Deploy the app on AWS
This app can also be deployed on AWS. In the main folder, you would find a cloudformation template to deploy the app to ECS,ALB and CloudFront

   ### Architecture Diagram

   ![GreenCloud Advisor architecture diagram](image/Architecture_Diagram.png)

Prerequisites:
* docker
* python >= 3.8
* use a browser for development

To Deploy:
1. Open a bash terminal and set aws-credentials for the account you want to deploy the solution to.
1. Build a docker image and upload the same to ECR. By default it creates ECR repo in us-east-1 region. Feel free to change to different region. Replace <account-id> with the actual value where you are creating the ECR repository.
   * Create ECR repository: ```aws ecr create-repository --repository-name greencloud --region us-east-1 ```
   * Authenticate Docker to ECR: ```aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com ```
   * Build the docker image: ```docker build --platform linux/amd64 -t greencloud .```
   * Tag the docker image: ```docker tag greencloud:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/greencloud:latest```
   * Push the image to ECR: ```docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/greencloud:latest```

   Note the above ```container image``` as it is needed for the cloudformation stack below at step 3.

1. Open the ```config``` file and edit the ECR container image path for ```CONTAINER_IMAGE```. It should look something like ```123456789.dkr.ecr.us-east-1.amazonaws.com/greencloud:latest```

1. Run deploy.sh to deploy the cloudformation in your account
```./deploy.sh```

## Usage

### Web Interface for new workload
1. Enter your AWS services or workload description
1. Select potential AWS regions to evaluate
1. Click "Analyze Regions" for recommendations
1. Get a summary about which region is better for sustainability and optimization recommendations. (Download available)

### Web Interface for existing workloads
1. Upload your carbon emission report which you can download from your Sustainability console. More can be found here: [Carbon emission report for your account](https://docs.aws.amazon.com/sustainability/latest/userguide/csv-reports.html)
1. Get Insights from your emission report (Download available)
1. Chat with your emission report using Amazon Nova pro

### Adding a New Language
This application supports multilingual UI through JSON locale files in the `locales/` directory.
To add a new language (e.g., Korean `ko`):
Copy `locales/en.json` to `locales/ko.json`
Translate all values in `ko.json` (keys must remain the same)
In `streamlit_app.py`, update `_load_locales()` to include the new language code:
```python
   for lang_code in ['en', 'ja', 'ko']:
   ```
Update the language switcher button logic to cycle through the new language
In `src/sustainability_insights.py`, add the new language code to `_load_insights_texts()`

Locale file structure:
```
locales/
  en.json   # English (default)
  ja.json   # Japanese
  ko.json   # Korean (example)
```
**Important**: All UI text, PDF labels, chart labels, and AI prompt instructions are defined in these files. No source code changes are needed for translation — only the JSON values.

## Important Notes
- The connection between CloudFront and the ALB is in HTTP, not SSL encrypted. This means traffic between CloudFront and the ALB is unencrypted. It is **strongly recommended** to configure HTTPS by bringing your own domain name and SSL/TLS certificate to the ALB.
- Users should provide their electricitymaps.com API key in the config file to enable rapid deployment. Once deployed to production, **migrate the API key to AWS Secrets Manager** and update your application to retrieve credentials from it, ensuring compliance with security best practices and preventing credential exposure.
- The provided code is intended as a demo and starting point, not production ready. The Python app relies on third party libraries like Streamlit and streamlit-cognito-auth. As the developer, it is your responsibility to properly vet, maintain, and test all third party dependencies. The authentication and authorization mechanisms in particular should be thoroughly evaluated. More generally, you should perform security reviews and testing before incorporating this demo code in a production application or with sensitive data.
- AWS provides various services, not implemented in this demo, that can improve the security of this application. Network security services like network ACLs and AWS WAF can control access to resources. You could also use AWS Shield for DDoS protection and Amazon GuardDuty for threats detection. Amazon Inspector performs security assessments. There are many more AWS services and best practices that can enhance security - refer to the AWS Shared Responsibility Model and security best practices guidance for additional recommendations. The developer is responsible for properly implementing and configuring these services to meet their specific security requirements.

## Licence
This application is licensed under the MIT-0 License. See the LICENSE file.

## Cleanup
1. Delete the stack by going to cloudformation
2. Delete the repo in ECR


