
# Deployment walkthrough

## Table of Contents
- [Deployment walkthrough](#deployment-walkthrough)
  - [Table of Contents](#table-of-contents)
  - [Requirements](#requirements)
  - [Pre-Deployment](#pre-deployment)
    - [Customize Static Website Content](#customize-static-website-content)
    - [Set Up Pinecone Index **(Optional)**](#set-up-pinecone-index-optional)
  - [Deployment](#deployment)
    - [Step 1: Clone The Repository](#step-1-clone-the-repository)
    - [Step 2: CDK Deployment](#step-2-cdk-deployment)
      - [**Extra: Taking down the deployed stacks**](#extra-taking-down-the-deployed-stacks)
    - [Step 3: Uploading the configuration file](#step-3-uploading-the-configuration-file)

## Requirements

Before you deploy, you must have the following installed on your device:

- [git](https://git-scm.com/downloads)
- [AWS Account](https://aws.amazon.com/account/)
- [GitHub Account](https://github.com/)
- [Amazon Developer Account](https://developer.amazon.com/)
- [AWS CLI](https://aws.amazon.com/cli/)
- [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/cli.html)
- [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)*

If you are on a Windows device, it is recommended to install the [Windows Subsystem For Linux](https://docs.microsoft.com/en-us/windows/wsl/install)(WSL), which lets you run a Linux terminal on your Windows computer natively. Some of the steps will require its use. [Windows Terminal](https://apps.microsoft.com/store/detail/windows-terminal/9N0DX20HK701) is also recommended for using WSL.

*It is recommended to use a npm version manager rather than installing npm directly. For Linux, install npm using [nvm](https://github.com/nvm-sh/nvm). For Windows, it is recommended to use WSL to install nvm. Alternatively, Windows versions such as [nvm-windows](https://github.com/coreybutler/nvm-windows) exist.

## Pre-Deployment

### Create Amazon Developer Account ###
To deploy the voice assistant, you will need an Amazon developer account. Go to [Amazon Developers Portal](https://developer.amazon.com/), and create your account.

Once you create an account, you can log into the Amazon Developer Console. Your console should look like the image below:
![Amazon Developer Console](./images/developer_console.png)
On you console, click `Alexa Skills Kit` to open up the Alexa developer console. On its main screen, click on the "Setting" tab. You should see your `Vendor ID` listed in the "My IDs" section. Please note this value.

### Create Login With Amazon (LWA) Security Profile ###
Next, you will need to create a security profile for LWA under the same Amazon account you will use to create the Alexa Skill.

Navigate back to the Amazon Developer Console, then click `Login with Amazon` tab on top of the screen. This opens up the Login With Amazon Console. 
![Login With Amazon Console](./images/lwa_console.png)

Click `Create a New Security Profile` button, and fill out the form.
![LWA form](./images/lwa_form.png)
Please set the profile name and description as you like, and set Consent Privacy Notice URL as `https://example.com/privacy` as you won't need this URL. 
After you fill out all the required fields, click "Save".

Your newly created security profile should now be listed. To edit its settings, hover over the gear icon located on the right of the profile name, and click "Web Settings".
![LWA profile](./images/lwa_profile.png)
Click the "Edit" button, and add the following URL to "Allowed Return URLs" field.
- http://127.0.0.1:9090/cb
- https://ask-cli-static-content.s3-us-west-2.amazonaws.com/html/ask-cli-no-browser.html

After adding them, lick the "Save" button to save your changes, and click "Show Secret" button to reveal your Client Secret. Please note `Client ID` and `Client Secret`.

**Get Refresh Token from ASK CLI**
Your `Client ID` and `Client Secret` let you generate a refresh token for authenticating with the Alexa SKills Kit.

Navigate to your local terminal and run the following command, replacing `<your Client ID>` and `<your Client Secret>` with your original values:
```bash
ask util generate-lwa-tokens --client-id "<your Client ID>" --client-confirmation "<your Client Secret>" --scopes "alexa::ask:skills:readwrite alexa::ask:models:readwrite" --no-browser
```
Follow the instruction on the console. Once you are done, the credentials, including your refresh token, should be printed. Note the value of your refresh token.

### Add your credentials to AWS Secrets Manager ###
Since CDK requires access to Alexa Developer credentials we just generated, we need to secretly store these values so that your account information will not be publicly viewable. 

Please navigate to the AWS Secrets Manager console. Click "Store a new secret" button, and enter the necessary information.
![secret](./images/store_secret.png)
- For `Secret Type` field, choose `Ohter type of secret`.
- For `Key/Value pairs` field, select `Plaintext`. Then paste the following values, replacing the values enclosed by angle brackets `<>`.
    ```bash
    {
        "vendor-id": "<Your Vendor ID>"
        "client-id": "<Your Client ID>",
        "client-secret": "<Your Client Secret>",
        "refresh-token": "<Your Refresh Token>"
    }
    ```
After filling out those fields, click `Next` to proceed.

![secret-2](./images/store_secret_2.png)
Enter your secret name. This can be anything you like.  
**Please leave the rest of the form blank, and simply move on by clicking `Next`.**  
**You do not have to edit anything in step 3: `Configure Rotation` section.**

After entering all necessary information, review them and create secret by clicking `Store` button.

Go back to the Secrets Manager console, and click on the secret name you just created. 
![secret-info](./images/secret_info.png)
Under `Secret details` section, you can see your Secret ARN. Please copy its value.


## Deployment 

### Step 1: Clone The Repository

First, clone the GitHub repository onto your machine. To do this:

1. Create a folder on your computer to contain the project code.
2. For an Apple computer, open Terminal. If on a Windows machine, open Command Prompt or Windows Terminal. Enter into the folder you made using the command `cd path/to/folder`. To find the path to a folder on a Mac, right click on the folder and press `Get Info`, then select the whole text found under `Where:` and copy with ⌘C. On Windows (not WSL), enter into the folder on File Explorer and click on the path box (located to the left of the search bar), then copy the whole text that shows up.
3. Clone the github repository by entering the following:

```bash
git clone https://github.com/UBC-CIC/student-advising-assistant
```

The code should now be in the folder you created. Navigate into the root folder containing the entire codebase by running the command:

```bash
cd student-advising-assistant
``` 

### Step 2: CDK Deployment

It's time to set up everything that goes on behind the scenes! For more information on how the backend works, feel free to refer to the Architecture Deep Dive, but an understanding of the backend is not necessary for deployment.

**IMPORTANT**: Before moving forward with the deployment, please make sure that your **Docker Desktop** software is running (and the Docker Daemon is running). Also ensure that you have npm installed on your system.

Note this CDK deployment was tested in `us-west-2` and `ca-central-1` regions only.

Open a terminal in the `/backend/cdk` directory.
The file `demo-app.zip` should already exist in the directory. In the case that it does not, run the following command to create it:
``` bash
zip -r demo-app.zip aws_helpers/ flask_app/ Dockerfile -x "*/.*" -x ".*" -x "*.env" -x "__pycache__*"
```
Note: `zip` command requires that you use Linux or WSL. If `zip` is not installed, run `sudo apt install zip` first.

**Download Requirements**
Install requirements with npm:
```npm install```

**Configure the CDK deployment**
The configuration options are in the `/backend/cdk/config.json` file. By default, the contents are:
```
{
    "retriever_type": "pgvector",
    "llm_mode": "ec2"
}
```
- `retriever_type` allowed values: "pgvector", "pinecone"
- `llm_mode` allowed values: "ec2", "sagemaker", "none"

If you chose to use Pinecone.io retriever, replace the `"pgvector"` value with `"pinecone"`.

If you would prefer not to deploy the LLM, replace the `"ec2"` value with `"none"`. The system will not deploy a LLM endpoint, and it will return references from the information sources only, without generated responses. 

The `"sagemaker"` options for `llm_mode` will host the model with an SageMaker inference endpoint instead of an EC2 instance. This may incur a higher cost.

**Edit the URL of your web application**
You can change the URL of your web application to your preferred name.
Please navigate to `/backend/cdk/lib/hosting-stack.ts` file. In line 175, you can see that the constant named `cnamePrefix` is declared. Currently the value is `"student-advising-assistant-demo"`, but you change change its value so that it's going to be the URL of your application.



**Initialize the CDK stacks**
(required only if you have not deployed any resources with CDK in this region before)

```bash
cdk synth --profile your-profile-name
cdk bootstrap aws://YOUR_AWS_ACCOUNT_ID/YOUR_ACCOUNT_REGION --profile your-profile-name
```

**Deploy the CDK stacks**

You may  run the following command to deploy the stacks all at once. Please replace `<profile-name>` with the appropriate AWS profile used earlier. 

```bash
cdk deploy --all --profile <profile-name>
```

#### **Extra: Taking down the deployed stacks**

To take down the deployed stack for a fresh redeployment in the future, navigate to AWS Cloudformation, click on the stack(s) and hit Delete. Please wait for the stacks in each step to be properly deleted before deleting the stack downstream. The deletion order is as followed:

1. HostingStack
2. InferenceStack
3. student-advising-DatabaseStack
4. student-advising-VpcStack
5. VoiceAssistantStack

### Step 3: Uploading the configuration file

To complete the deployment, you will need to upload a configuration file specifying the websites to scrape for information. Continue with the [User Guide](./UserGuide.md#updating-the-configuration-file) for this step.